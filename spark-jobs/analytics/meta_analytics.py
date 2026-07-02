"""
Meta analytics: cross-battle statistics — usage rates, win rates,
optimal items/abilities/moves.

These are the "Smogon-style" stats computed from the simulator's
own battle data.
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, when,
    round as spark_round, desc, row_number, lit
)
from pyspark.sql.window import Window


def analyze_meta(battle_df: DataFrame, event_df: DataFrame,
                 output_dir: str, lookup) -> dict:
    """Cross-battle meta statistics."""
    from common.io_utils import write_output_csv

    print("\n=== Meta Analytics ===")

    # ── 1. Species usage ranking ─────────────────────────────────
    # Deduplicate by (battle_id, species_id) — one appearance per battle per species
    species_per_battle = battle_df.select("battle_id", "species_id", "hp_pct", "fainted") \
        .dropDuplicates(["battle_id", "species_id"])
    usage = species_per_battle.groupBy("species_id").agg(
        count("*").alias("appearances"),
        spark_round(avg("hp_pct"), 1).alias("avg_hp_pct"),
        spark_sum(when(col("fainted") == True, 1).otherwise(0)).alias("times_koed"),  # noqa: E712
    ).withColumn(
        "ko_rate", spark_round(col("times_koed") / col("appearances") * 100, 1)
    ).orderBy(desc("appearances"))

    print("  Species usage (top 15):")
    usage.show(15, truncate=False)

    write_output_csv(usage, "meta_species_usage", output_dir)

    # ── 2. Item ranking ──────────────────────────────────────────
    items_per_battle = battle_df.select("battle_id", "species_id", "item_id", "hp_pct") \
        .dropDuplicates(["battle_id", "species_id"])
    items = items_per_battle.groupBy("item_id").agg(
        count("*").alias("uses"),
        spark_round(avg("hp_pct"), 1).alias("avg_hp"),
    ).filter(col("item_id") > 0).orderBy(desc("uses"))

    write_output_csv(items, "meta_item_usage", output_dir)

    # ── 3. Ability ranking ───────────────────────────────────────
    abilities_per_battle = battle_df.select("battle_id", "species_id", "ability_id") \
        .dropDuplicates(["battle_id", "species_id"])
    abilities = abilities_per_battle.groupBy("ability_id").agg(
        count("*").alias("uses"),
    ).filter(col("ability_id") > 0).orderBy(desc("uses"))

    write_output_csv(abilities, "meta_ability_usage", output_dir)

    # ── 4. Move usage (explode move_ids, dedupe per battle/species) ──
    from pyspark.sql.functions import explode
    move_exploded = battle_df.select(
        "battle_id", "species_id",
        explode("move_ids").alias("move_id")
    ).dropDuplicates(["battle_id", "species_id", "move_id"])
    move_usage = move_exploded.groupBy("move_id").agg(
        count("*").alias("times_seen")
    ).orderBy(desc("times_seen"))

    print("  Move usage (top 10):")
    move_usage.show(10, truncate=False)

    write_output_csv(move_usage, "meta_move_usage", output_dir)

    # ── 5. Summary ──────────────────────────────────────────────
    top_species = usage.first()
    summary = {
        "total_species_seen": usage.count(),
        "top_species_id": top_species["species_id"] if top_species else 0,
        "top_species_appearances": top_species["appearances"] if top_species else 0,
    }
    return summary
