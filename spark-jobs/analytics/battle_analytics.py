"""
Battle-level analytics: HP curves, KO timing, switch patterns.

Analyses a single battle (or set of battles) at the per-turn level
to understand pacing, survivability, and momentum.
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    col, avg, min as spark_min, max as spark_max, count, sum as spark_sum,
    when, round as spark_round, row_number, lag, desc, first
)
from pyspark.sql.window import Window


def analyze_battle_flow(battle_df: DataFrame, event_df: DataFrame,
                        output_dir: str, lookup) -> dict:
    """
    Battle flow analytics:
      - HP remaining per turn per side
      - First KO turn
      - Switch frequency
      - Pokemon survival rates

    Returns a summary dict.
    """
    from common.io_utils import write_output_csv

    print("\n=== Battle Flow Analytics ===")

    # ── 1. HP curve: avg HP per side per turn ────────────────────
    hp_curve = battle_df.groupBy("battle_id", "turn", "side_index").agg(
        spark_round(avg("hp_pct"), 1).alias("avg_hp_pct"),
        spark_sum(when(col("fainted") == True, 1).otherwise(0)).alias("ko_count"),      # noqa: E712
        spark_sum(when(col("fainted") == False, 1).otherwise(0)).alias("alive_count"),   # noqa: E712
    ).orderBy("battle_id", "turn", "side_index")

    write_output_csv(hp_curve, "battle_hp_curve", output_dir)

    # ── 1b. Per-pokemon HP trace (individual Pokemon curves) ────────
    pokemon_hp = battle_df.select(
        "battle_id", "turn", "side_index", "pokemon_index",
        "species_id", "hp", "max_hp", "hp_pct", "fainted"
    ).orderBy("battle_id", "turn", "side_index", "pokemon_index")
    write_output_csv(pokemon_hp, "battle_pokemon_hp", output_dir)
    print(f"  Pokemon HP trace: {pokemon_hp.count()} rows")

    # ── 2. First KO turn per battle ──────────────────────────────
    kos = battle_df.filter(col("fainted") == True) \
        .groupBy("battle_id").agg(spark_min("turn").alias("first_ko_turn"))

    print("  First KO turn per battle:")
    kos.show(5, truncate=False)

    # ── 3. Switch frequency (from events) ────────────────────────
    switches = event_df.filter(
        col("event_type").isin("switch_in", "switch_out")
    ).groupBy("battle_id", "turn").agg(
        count("*").alias("switch_count")
    ).groupBy("battle_id").agg(
        spark_round(avg("switch_count"), 1).alias("avg_switches_per_turn"),
        spark_max("switch_count").alias("max_switches_per_turn"),
    )

    print("  Switch frequency:")
    switches.show(5, truncate=False)

    write_output_csv(switches, "battle_switches", output_dir)

    # ── 4. Pokemon survival ─────────────────────────────────────
    # Species that survive to end (last turn) vs species that faint
    last_turn_df = battle_df.groupBy("battle_id").agg(
        spark_max("turn").alias("last_turn")
    )
    last_state = battle_df.join(
        last_turn_df,
        (battle_df.battle_id == last_turn_df.battle_id) &
        (battle_df.turn == last_turn_df.last_turn)
    )

    survival = battle_df.groupBy("species_id").agg(
        count("*").alias("total_appearances"),
        spark_sum(when(col("fainted") == True, 1).otherwise(0)).alias("total_kos"),  # noqa: E712
    ).withColumn(
        "ko_rate", spark_round(col("total_kos") / col("total_appearances") * 100, 1)
    ).orderBy(desc("total_appearances"))

    print("  Pokemon survival (top 10 most seen):")
    survival.show(10, truncate=False)

    write_output_csv(survival, "battle_survival", output_dir)

    # ── 5. Summary ──────────────────────────────────────────────
    total_turns = battle_df.select("turn").distinct().count()
    total_battles = battle_df.select("battle_id").distinct().count()
    first_ko_avg = kos.agg(avg("first_ko_turn")).collect()[0][0]

    summary = {
        "total_battles": total_battles,
        "total_turns": total_turns,
        "avg_first_ko_turn": round(first_ko_avg, 1) if first_ko_avg else 0,
        "hp_curve_output": f"{output_dir}/battle_hp_curve.csv",
        "switches_output": f"{output_dir}/battle_switches.csv",
        "survival_output": f"{output_dir}/battle_survival.csv",
    }
    return summary
