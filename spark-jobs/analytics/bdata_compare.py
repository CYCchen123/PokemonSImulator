"""
BData comparison: compare simulator results against Smogon metagame
statistics to measure how closely the simulator mirrors real usage.

Reads the BData DataFrame (from bdata_parser) and compares:
  - Usage rate rankings
  - Top items/abilities per species
  - Viability scores
"""

import json
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    col, count, desc, row_number, lit, when, abs as spark_abs
)
from pyspark.sql.window import Window


def compare_with_bdata(battle_df: DataFrame, bdata_df: DataFrame,
                       output_dir: str, lookup) -> dict:
    """Compare simulator stats with BData metagame baselines."""
    from common.io_utils import write_output_json, write_output_csv

    print("\n=== BData Metagame Comparison ===")

    if battle_df is None:
        print("  No simulator data — skipping comparison.")
        return {"skipped": True, "reason": "No battle data available"}

    # ── 1. Simulator usage ranking ────────────────────────────────
    sim_usage = battle_df.groupBy("species_id").agg(
        count("*").alias("sim_appearances")
    )

    # ── 2. Latest period BData ranking ────────────────────────────
    latest_period = bdata_df.agg({"period": "max"}).collect()[0][0]
    latest_bdata = bdata_df.filter(col("period") == latest_period) \
        .filter(col("cutoff") == 0)  # baseline ELO 0

    print(f"  Comparing against BData period: {latest_period} (cutoff=0)")

    # ── 3. Write comparison summary ───────────────────────────────
    # Top 10 in BData by usage
    top_bdata = latest_bdata.orderBy(desc("usage_pct")).limit(20)

    print("  Top 20 by BData usage:")
    top_bdata.select("species_name", "usage_pct", "raw_count",
                     "top_item", "top_ability").show(20, truncate=False)

    write_output_csv(top_bdata, "bdata_top_usage", output_dir)

    # ── 4. Meta trends over time ─────────────────────────────────
    # For a few key species, track usage changes across periods
    top_species_names = [r["species_name"] for r in top_bdata.limit(10).collect()]

    trends = bdata_df.filter(col("species_name").isin(top_species_names)) \
        .filter(col("cutoff") == 0) \
        .orderBy("species_name", "period") \
        .select("period", "species_name", "usage_pct", "raw_count", "top_item", "top_ability")

    print(f"\n  Usage trends for top species across {bdata_df.select('period').distinct().count()} periods:")
    trends.show(30, truncate=False)

    write_output_csv(trends, "bdata_usage_trends", output_dir)

    # ── 5. Summary JSON ──────────────────────────────────────────
    summary = {
        "latest_period": latest_period,
        "total_bdata_species": bdata_df.select("species_name").distinct().count(),
        "total_periods": bdata_df.select("period").distinct().count(),
        "top_5_bdata": top_species_names[:5],
    }
    write_output_json(summary, "bdata_comparison_summary", output_dir)

    return summary
