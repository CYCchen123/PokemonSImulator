"""
Event timeline analytics: damage distribution, status application rates,
ability/item trigger patterns from the event log.
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, when,
    round as spark_round, desc
)


def analyze_events(event_df: DataFrame, output_dir: str, lookup) -> dict:
    """Event timeline analytics."""
    from common.io_utils import write_output_csv

    print("\n=== Event Timeline Analytics ===")

    # ── 1. Event type distribution ───────────────────────────────
    event_dist = event_df.groupBy("event_type").agg(
        count("*").alias("count")
    ).withColumn(
        "pct", spark_round(col("count") / event_df.count() * 100, 2)
    ).orderBy(desc("count"))

    print("  Event type distribution:")
    event_dist.show(20, truncate=False)

    write_output_csv(event_dist, "event_type_dist", output_dir)

    # ── 2. Events per turn (pacing) ──────────────────────────────
    events_per_turn = event_df.groupBy("battle_id", "turn").agg(
        count("*").alias("event_count")
    ).groupBy("battle_id").agg(
        spark_round(avg("event_count"), 1).alias("avg_events_per_turn"),
        spark_sum("event_count").alias("total_events")
    )

    write_output_csv(events_per_turn, "event_pacing", output_dir)

    # ── 3. Damage / heal events (count and pattern) ──────────────
    dmg_heal = event_df.filter(
        col("event_type").isin("damage", "heal", "faint")
    ).groupBy("event_type").agg(
        count("*").alias("count"),
    ).orderBy(desc("count"))

    print("  Damage/Heal/Faint events:")
    dmg_heal.show(10, truncate=False)

    write_output_csv(dmg_heal, "event_damage_heal", output_dir)

    # ── 4. Ability triggers ──────────────────────────────────────
    abilities = event_df.filter(
        col("event_type") == "ability_trigger"
    ).groupBy("pokemon_name").agg(
        count("*").alias("trigger_count")
    ).orderBy(desc("trigger_count"))

    if abilities.count() > 0:
        print("  Top ability-triggering pokemon:")
        abilities.show(10, truncate=False)

    # ── 5. Status application ───────────────────────────────────
    statuses = event_df.filter(
        col("event_type") == "status_apply"
    ).groupBy("reason").agg(
        count("*").alias("count")
    ).orderBy(desc("count"))

    print("  Status application reasons:")
    statuses.show(10, truncate=False)

    write_output_csv(statuses, "event_status", output_dir)

    # ── Summary ──────────────────────────────────────────────────
    total_events = event_df.count()
    move_used_count = event_df.filter(col("event_type") == "move_used").count()

    summary = {
        "total_events": total_events,
        "move_used_events": move_used_count,
        "move_used_pct": round(move_used_count / max(total_events, 1) * 100, 1),
        "unique_event_types": event_dist.count(),
    }
    return summary
