"""
Parse battle_logs/output/*.json into structured Spark DataFrames.

Each output file is one turn of a battle. The parser:
1. Extracts battle_id and turn from the filename
2. Flattens sides[] -> pokemons[] into per-pokemon-per-turn rows
3. Flattens events[] into per-event rows
4. Computes derived columns (hp_pct, fainted count per side, is_winner)
"""

import json
import os
from typing import Tuple, List, Dict, Any

from pyspark.sql import SparkSession, DataFrame, Row


def _load_output_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_pokemon_rows(battle_id: str, turn: int, data: dict) -> List[Dict[str, Any]]:
    """Flatten battle.sides[].pokemons[] into a list of flat dicts."""
    rows = []
    battle = data.get("battle", data)
    sides = battle.get("sides", [])

    for side_idx, side in enumerate(sides):
        for poke_idx, pokemon in enumerate(side.get("pokemons", [])):
            hp = pokemon.get("hp", 0)
            max_hp = pokemon.get("maxHp", 1)
            moves = pokemon.get("moves", [])
            rows.append({
                "battle_id": str(battle_id),
                "turn": turn,
                "side_index": side_idx,
                "pokemon_index": poke_idx,
                "species_id": pokemon.get("speciesId", 0),
                "hp": hp,
                "max_hp": max_hp,
                "hp_pct": round(hp / max(max_hp, 1) * 100, 1),
                "fainted": pokemon.get("fainted", False),
                "ability_id": pokemon.get("abilityId", 0),
                "item_id": pokemon.get("itemId", 0),
                "types": pokemon.get("types", []),
                "move_ids": [m.get("id", 0) for m in moves],
                "move_pps": [m.get("pp", 0) for m in moves],
                "stat_stages": pokemon.get("statStages", [0] * 7),
                "status_count": len(pokemon.get("inBattleStatus", [])),
                "slot": pokemon.get("slot", 0),
            })
    return rows


def _extract_event_rows(battle_id: str, turn: int, data: dict) -> List[Dict[str, Any]]:
    """Flatten events[] into a list of flat dicts."""
    rows = []
    events = data.get("events", [])

    for evt in events:
        details = evt.get("details", {})
        poke_ref = details.get("pokemon_ref", {})
        # Determine event type from description keywords
        desc = evt.get("description", "")
        event_type = _classify_event(desc, details)

        rows.append({
            "battle_id": str(battle_id),
            "turn": turn,
            "timeline_index": evt.get("timeline_index", 0),
            "turn_index": evt.get("turn_index", 0),
            "event_type": event_type,
            "description": desc,
            "side_index": details.get("side_index", poke_ref.get("side_index", -1)),
            "pokemon_index": poke_ref.get("pokemon_index", -1),
            "pokemon_name": details.get("pokemon", ""),
            "reason": details.get("reason", ""),
        })
    return rows


def _classify_event(description: str, details: dict) -> str:
    """Classify an event based on its description and details."""
    reason = details.get("reason", "")
    desc_lower = description.lower()

    if "上场" in description or reason in ("initial_send_out", "send_out"):
        return "switch_in"
    if "换下" in description or "下场" in description or reason == "switch_out":
        return "switch_out"
    if "使用了" in description:
        return "move_used"
    if "伤害" in description or "damage" in desc_lower:
        return "damage"
    if "恢复" in description or "heal" in desc_lower:
        return "heal"
    if "倒下了" in description or "faint" in desc_lower:
        return "faint"
    if "特性" in description or "ability" in desc_lower:
        return "ability_trigger"
    if "道具" in description or "item" in desc_lower:
        return "item_trigger"
    if "状态" in description or "status" in desc_lower:
        return "status_apply"
    if "能力" in description or "stat" in desc_lower:
        return "stat_change"
    if "天气" in description or "weather" in desc_lower:
        return "weather"
    return "other"


def parse_output_files(spark: SparkSession, output_dir: str) -> Tuple[DataFrame, DataFrame]:
    """
    Parse all output_*.json files.

    Returns:
        (battle_state_df, event_df) -- two DataFrames
    """
    import glob

    files = sorted(glob.glob(os.path.join(output_dir, "output_*.json")))
    if not files:
        # Try recursive: battle_logs/<id>/output/output_*.json
        files = sorted(glob.glob(os.path.join(output_dir, "**", "output_*.json"), recursive=True))
    if not files:
        raise FileNotFoundError(f"No output_*.json files found in {output_dir}")

    print(f"Parsing {len(files)} output files...")

    all_pokemon_rows = []
    all_event_rows = []

    for fpath in files:
        from common.io_utils import extract_battle_id, extract_turn

        battle_id = extract_battle_id(fpath)
        turn = extract_turn(fpath)
        data = _load_output_json(fpath)

        all_pokemon_rows.extend(_extract_pokemon_rows(battle_id, turn, data))
        all_event_rows.extend(_extract_event_rows(battle_id, turn, data))

    # Create DataFrames using schemas
    from common.schemas import BATTLE_STATE_SCHEMA, EVENT_SCHEMA

    battle_df = spark.createDataFrame(
        spark.sparkContext.parallelize(all_pokemon_rows),
        schema=BATTLE_STATE_SCHEMA,
    )

    event_df = spark.createDataFrame(
        spark.sparkContext.parallelize(all_event_rows),
        schema=EVENT_SCHEMA,
    )

    print(f"  Battle state: {battle_df.count()} rows "
          f"({len(files)} turns x ~2 sides x ~4-5 pokemon)")
    print(f"  Events:       {event_df.count()} rows")

    return battle_df, event_df


def compute_side_stats(battle_df: DataFrame) -> DataFrame:
    """Aggregate per-side stats per turn: alive count, KO count, avg HP."""
    from pyspark.sql.functions import col, sum, count, avg, when

    stats = battle_df.groupBy("battle_id", "turn", "side_index").agg(
        count("*").alias("total_pokemon"),
        sum(when(col("fainted") == True, 1).otherwise(0)).alias("ko_count"),      # noqa: E712
        sum(when(col("fainted") == False, 1).otherwise(0)).alias("alive_count"),  # noqa: E712
        avg("hp_pct").alias("avg_hp_pct"),
    )
    return stats


def determine_winner(battle_df: DataFrame) -> DataFrame:
    """
    Determine the winning side for each battle.
    Side with more alive pokemon at the last turn wins.
    """
    from pyspark.sql.functions import col, max as spark_max, first

    # Get last turn per battle
    last_turn = battle_df.groupBy("battle_id").agg(
        spark_max("turn").alias("last_turn")
    )

    last_state = battle_df.join(
        last_turn,
        (battle_df.battle_id == last_turn.battle_id) &
        (battle_df.turn == last_turn.last_turn)
    ).select(battle_df["*"])

    # Count alive per side at last turn
    alive = last_state.groupBy("battle_id", "side_index").agg(
        sum(when(col("fainted") == False, 1).otherwise(0)).alias("alive_count")  # noqa: E712
    )

    return alive
