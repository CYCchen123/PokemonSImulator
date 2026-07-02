"""
Parse battle_logs/input/*.json into a DataFrame of turn actions.

Input format per file:
  {"type": "pass"}
  {"type": "attack", "move_index": 0, "side": "a"}
  {"type": "switch", "switch_index": 2, "side": "b"}
"""

import json
import os
from typing import List, Dict, Any

from pyspark.sql import SparkSession, DataFrame


def parse_input_files(spark: SparkSession, input_dir: str) -> DataFrame:
    """
    Parse all *_input_*.json files.

    Returns a DataFrame with schema matching ACTION_SCHEMA.
    """
    import glob

    files = sorted(glob.glob(os.path.join(input_dir, "*_input_*.json")))
    if not files:
        raise FileNotFoundError(f"No *_input_*.json files found in {input_dir}")

    print(f"Parsing {len(files)} input action files...")

    rows = []
    for fpath in files:
        from common.io_utils import extract_battle_id, extract_turn

        battle_id = extract_battle_id(fpath)
        turn = extract_turn(fpath)

        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        action_type = data.get("type", "unknown")
        side = data.get("side", "unknown")
        move_index = data.get("move_index", -1)
        switch_index = data.get("switch_index", -1)

        rows.append({
            "battle_id": str(battle_id),
            "turn": turn,
            "side": str(side),
            "action_type": action_type,
            "move_index": move_index if move_index is not None else -1,
            "switch_index": switch_index if switch_index is not None else -1,
        })

    from common.schemas import ACTION_SCHEMA

    action_df = spark.createDataFrame(
        spark.sparkContext.parallelize(rows),
        schema=ACTION_SCHEMA,
    )

    # Summary
    type_counts = action_df.groupBy("action_type").count().collect()
    summary = ", ".join(f"{r['action_type']}={r['count']}" for r in type_counts)
    print(f"  Actions: {action_df.count()} rows ({summary})")

    return action_df
