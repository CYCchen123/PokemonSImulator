"""
Type matchup analysis: compute team type distribution and
generate a type-effectiveness heatmap from observed battle data.

Uses species lookup to map species_id -> type1/type2, then
aggregates type frequencies across teams and battles.
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    col, count, sum as spark_sum, when, explode, array,
    round as spark_round, desc
)


def analyze_type_matchups(battle_df: DataFrame, output_dir: str, lookup) -> dict:
    """Type distribution and matchup analysis."""
    from common.io_utils import write_output_csv

    print("\n=== Type Matchup Analysis ===")

    species_map = lookup.species_map.value
    type_names = lookup.type_names.value

    # ── 1. Build type frequency across all pokemon appearances ────
    # Collect species_id -> count from the DataFrame
    species_counts = battle_df.groupBy("species_id").agg(
        count("*").alias("appearances")
    ).collect()

    # Map to type occurrences
    type_counts = {}
    for row in species_counts:
        sid = row["species_id"]
        apps = row["appearances"]
        info = species_map.get(sid, {})
        t1 = info.get("type1", 0)
        t2 = info.get("type2", 0)
        type_counts[t1] = type_counts.get(t1, 0) + apps
        if t2 and t2 != t1:
            type_counts[t2] = type_counts.get(t2, 0) + apps

    print("  Type distribution (across all pokemon appearances):")
    for tid in sorted(type_counts, key=type_counts.get, reverse=True):
        tname = type_names.get(tid, f"Type#{tid}")
        print(f"    {tname:12s}: {type_counts[tid]:,}")

    # ── 2. Team type diversity ───────────────────────────────────
    # Per battle, count unique types per side
    type_per_battle = battle_df.select(
        "battle_id", "side_index", "species_id"
    ).distinct()

    # Collect to driver (reasonable for single battle)
    rows = type_per_battle.collect()
    from collections import defaultdict
    team_types = defaultdict(set)
    for r in rows:
        key = (r["battle_id"], r["side_index"])
        info = species_map.get(r["species_id"], {})
        t1 = info.get("type1", 0)
        t2 = info.get("type2", 0)
        team_types[key].add(t1)
        if t2:
            team_types[key].add(t2)

    type_counts_per_team = [len(v) for v in team_types.values()]
    avg_types = sum(type_counts_per_team) / max(len(type_counts_per_team), 1)

    print(f"\n  Avg unique types per team: {avg_types:.1f} "
          f"(across {len(team_types)} teams)")

    # ── 3. Write type distribution CSV ───────────────────────────
    type_rows = []
    for tid, count_val in sorted(type_counts.items(), key=lambda x: -x[1]):
        type_rows.append({
            "type_id": tid,
            "type_name": type_names.get(tid, f"Type#{tid}"),
            "appearances": count_val,
        })

    type_df = battle_df.sql_ctx.createDataFrame(type_rows)
    write_output_csv(type_df, "type_distribution", output_dir)

    # ── Summary ──────────────────────────────────────────────────
    summary = {
        "most_common_type": type_names.get(
            max(type_counts, key=type_counts.get), "?"
        ) if type_counts else "N/A",
        "avg_unique_types_per_team": round(avg_types, 1),
        "type_dist_output": f"{output_dir}/type_distribution.csv",
    }
    return summary
