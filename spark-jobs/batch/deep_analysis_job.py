"""
PokemonSimulator Deep Analysis Job — Main Entry Point.

Orchestrates the full Spark analytics pipeline:
  1. Parse battle_logs output (battle state per turn)
  2. Parse battle_logs input  (turn actions)
  3. Optionally parse BData metagame statistics
  4. Run analytics modules: battle, meta, event, type, bdata_compare
  5. Write results to output_dir

Usage:
  source venv/bin/activate
  python spark-jobs/batch/deep_analysis_job.py --all

  # Individual modules:
  python spark-jobs/batch/deep_analysis_job.py --battle --meta
  python spark-jobs/batch/deep_analysis_job.py --all --compare-bdata
"""

import os
import sys
import argparse
import time

# Ensure project root + spark-jobs are on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "spark-jobs"))


def get_spark_session(local: bool = True) -> "SparkSession":
    """Create a SparkSession configured for local or cluster mode."""
    from pyspark.sql import SparkSession

    builder = SparkSession.builder \
        .appName("PokemonSimulator-DeepAnalytics") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")

    if local:
        builder = builder \
            .master("local[*]") \
            .config("spark.driver.memory", "2g") \
            .config("spark.sql.shuffle.partitions", "4")

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def main():
    parser = argparse.ArgumentParser(
        description="PokemonSimulator Deep Analytics (Spark)"
    )
    parser.add_argument("--local", action="store_true", default=True,
                        help="Run Spark in local mode (default)")
    parser.add_argument("--all", action="store_true",
                        help="Run all analytics modules")
    parser.add_argument("--battle", action="store_true",
                        help="Run battle flow analytics")
    parser.add_argument("--meta", action="store_true",
                        help="Run meta/usage analytics")
    parser.add_argument("--events", action="store_true",
                        help="Run event timeline analytics")
    parser.add_argument("--types", action="store_true",
                        help="Run type matchup analysis")
    parser.add_argument("--compare-bdata", action="store_true",
                        help="Run BData metagame comparison")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory (default: logs/analytics/)")
    parser.add_argument("--battle-dir", default=None,
                        help="Battle logs directory (default: battle_logs/)")
    parser.add_argument("--bdata-dir", default=None,
                        help="BData directory (default: BData/)")

    args = parser.parse_args()

    # If no module selected, default to --all
    if not any([args.all, args.battle, args.meta, args.events,
                args.types, args.compare_bdata]):
        args.all = True

    # ── Paths ────────────────────────────────────────────────────
    output_dir = args.output_dir or os.path.join(PROJECT_ROOT, "logs", "analytics")
    battle_dir = args.battle_dir or os.path.join(PROJECT_ROOT, "battle_logs")
    bdata_dir = args.bdata_dir or os.path.join(PROJECT_ROOT, "BData")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("  PokemonSimulator Deep Analytics")
    print(f"  Project:  {PROJECT_ROOT}")
    print(f"  Output:   {output_dir}")
    print(f"  Battles:  {battle_dir}")
    print(f"  BData:    {bdata_dir}")
    print("=" * 60)

    # ── Spark Session ────────────────────────────────────────────
    spark = get_spark_session(local=args.local)

    try:
        # ── Load lookup tables (broadcast) ───────────────────────
        from common.lookup_loader import LookupTables
        lookup = LookupTables(spark, PROJECT_ROOT)

        # ── Parse battle output ──────────────────────────────────
        output_path = os.path.join(battle_dir, "output")
        input_path = os.path.join(battle_dir, "input")

        # Check flat path first, then recursive
        has_output = os.path.isdir(output_path) and os.listdir(output_path)
        if not has_output:
            # Check for <battle_dir>/<id>/output/ structure
            import glob
            has_output = len(glob.glob(os.path.join(battle_dir, "**", "output_*.json"), recursive=True)) > 0

        if has_output:
            from parsers.output_parser import parse_output_files
            battle_df, event_df = parse_output_files(spark, battle_dir)
        else:
            print("No output files found — skipping battle parsing.")
            battle_df, event_df = None, None

        # ── Parse battle input ───────────────────────────────────
        has_input = os.path.isdir(input_path) and os.listdir(input_path)
        if not has_input:
            import glob
            has_input = len(glob.glob(os.path.join(battle_dir, "**", "*_input_*.json"), recursive=True)) > 0

        if has_input:
            from parsers.input_parser import parse_input_files
            action_df = parse_input_files(spark, input_path if os.path.isdir(input_path) else battle_dir)
        else:
            print("No input files found — skipping action parsing.")
            action_df = None

        # ── Parse BData ──────────────────────────────────────────
        bdata_df = None
        if args.compare_bdata or args.all:
            if os.path.isdir(bdata_dir) and os.listdir(bdata_dir):
                from parsers.bdata_parser import parse_bdata_files
                bdata_df = parse_bdata_files(spark, bdata_dir)
            else:
                print("No BData files found — skipping BData parsing.")

        if battle_df is None and bdata_df is None:
            print("ERROR: No data to analyze. Check battle_logs/ and BData/ directories.")
            sys.exit(1)

        # ── Run analytics ────────────────────────────────────────
        all_summaries = {}
        t0 = time.time()

        if battle_df is not None:
            if args.all or args.battle:
                from analytics.battle_analytics import analyze_battle_flow
                all_summaries["battle"] = analyze_battle_flow(
                    battle_df, event_df, output_dir, lookup)

            if args.all or args.meta:
                from analytics.meta_analytics import analyze_meta
                all_summaries["meta"] = analyze_meta(
                    battle_df, event_df, output_dir, lookup)

                from analytics.species_detail_analytics import analyze_species_detail
                all_summaries["species_detail"] = analyze_species_detail(
                    battle_df, output_dir, lookup)

            if args.all or args.events:
                from analytics.event_analytics import analyze_events
                all_summaries["events"] = analyze_events(
                    event_df, output_dir, lookup)

            if args.all or args.types:
                from analytics.type_matchup import analyze_type_matchups
                all_summaries["types"] = analyze_type_matchups(
                    battle_df, output_dir, lookup)

        if bdata_df is not None and (args.all or args.compare_bdata):
            from analytics.bdata_compare import compare_with_bdata
            all_summaries["bdata"] = compare_with_bdata(
                battle_df, bdata_df, output_dir, lookup)

        elapsed = time.time() - t0

        # ── Final summary ────────────────────────────────────────
        from common.io_utils import write_output_json
        write_output_json({
            "elapsed_seconds": round(elapsed, 1),
            "modules": list(all_summaries.keys()),
            "summaries": all_summaries,
        }, "analysis_summary", output_dir)

        print(f"\n{'=' * 60}")
        print(f"  Analysis complete in {elapsed:.1f}s")
        print(f"  Modules run: {list(all_summaries.keys())}")
        print(f"  Output: {output_dir}/")
        print(f"{'=' * 60}")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
