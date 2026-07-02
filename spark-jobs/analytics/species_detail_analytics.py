"""
Per-species detail analytics: for each Pokemon species, compute
ranked move usage, item usage, and ability usage.

These feed the frontend drill-down feature: click a species in the
usage ranking → see what moves/items/abilities it commonly uses.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, count, desc, rank, explode,
)
from pyspark.sql.window import Window


def analyze_species_detail(battle_df: DataFrame, output_dir: str,
                           lookup) -> dict:
    """Compute per-species move/item/ability rankings and write CSV."""
    from common.io_utils import write_output_csv

    print("\n=== Species Detail Analytics ===")

    # ── 1. Per-species move usage (explode move_ids, dedupe per battle) ──
    move_exploded = battle_df.select(
        "battle_id", "species_id",
        explode("move_ids").alias("move_id")
    ).dropDuplicates(["battle_id", "species_id", "move_id"])
    species_moves = move_exploded.groupBy("species_id", "move_id").agg(
        count("*").alias("usage_count")
    )
    # Rank within each species: order by usage_count desc, then move_id asc for tie-breaking
    move_window = Window.partitionBy("species_id").orderBy(
        desc("usage_count"), col("move_id")
    )
    species_moves_ranked = species_moves.withColumn(
        "rank", rank().over(move_window)
    )

    print("  Species-move pairs (top 10):")
    species_moves_ranked.orderBy("species_id", "rank").show(10, truncate=False)

    write_output_csv(species_moves_ranked, "meta_species_moves", output_dir)

    # ── 2. Per-species item usage (dedupe per battle) ────────────
    items_deduped = battle_df.select("battle_id", "species_id", "item_id") \
        .dropDuplicates(["battle_id", "species_id"])
    species_items = items_deduped.groupBy("species_id", "item_id").agg(
        count("*").alias("usage_count")
    ).filter(col("item_id") > 0)

    item_window = Window.partitionBy("species_id").orderBy(
        desc("usage_count"), col("item_id")
    )
    species_items_ranked = species_items.withColumn(
        "rank", rank().over(item_window)
    )

    write_output_csv(species_items_ranked, "meta_species_items", output_dir)

    # ── 3. Per-species ability usage (dedupe per battle) ─────────
    abilities_deduped = battle_df.select("battle_id", "species_id", "ability_id") \
        .dropDuplicates(["battle_id", "species_id"])
    species_abilities = abilities_deduped.groupBy("species_id", "ability_id").agg(
        count("*").alias("usage_count")
    ).filter(col("ability_id") > 0)

    ability_window = Window.partitionBy("species_id").orderBy(
        desc("usage_count"), col("ability_id")
    )
    species_abilities_ranked = species_abilities.withColumn(
        "rank", rank().over(ability_window)
    )

    write_output_csv(species_abilities_ranked, "meta_species_abilities", output_dir)

    # ── 4. Summary ────────────────────────────────────────────────
    species_count = species_moves_ranked.select("species_id").distinct().count()
    summary = {
        "species_with_details": species_count,
        "species_moves_rows": species_moves_ranked.count(),
        "species_items_rows": species_items_ranked.count(),
        "species_abilities_rows": species_abilities_ranked.count(),
    }
    print(f"  {species_count} species with per-species detail data")
    return summary
