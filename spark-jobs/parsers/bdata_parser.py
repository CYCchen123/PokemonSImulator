"""
Parse BData/*.json (Smogon-style metagame statistics) into a DataFrame.

BData JSON structure:
{
  "info": {"metagame": "gen91v1", "cutoff": 0, "number of battles": 41162},
  "data": {
    "PokemonName": {
      "Raw count": 10829,
      "Viability Ceiling": [748, 79, 76, 64],
      "Abilities": {"infiltrator": 5310, ...},
      "Items": {"choiceband": 4871, ...},
      "Spreads": {"Jolly:0/252/4/0/0/252": 3353, ...},
      "Moves": {"dragondarts": 5000, ...},
      "Teammates": {"Volcanion": 2390, ...},
      "Checks and Counters": {"Darkrai": [25.0, 0.08, 0.054], ...},
      "usage": 0.08776
    }
  }
}
"""

import json
import os
from typing import List, Dict, Any

from pyspark.sql import SparkSession, DataFrame


def _top_key(d: dict) -> str:
    """Return the key with the highest value, or empty string."""
    if not d:
        return ""
    return max(d, key=lambda k: d[k])


def _top_key_pct(d: dict, total: int) -> float:
    """Return the fraction of the top key's value vs total (100-based)."""
    if not d or total <= 0:
        return 0.0
    top_val = max(d.values())
    return round(top_val / total * 100, 2)


def _parse_one_bdata_file(fpath: str) -> List[Dict[str, Any]]:
    """Parse one BData JSON file into a list of per-species rows."""
    with open(fpath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    from common.io_utils import extract_bdata_info

    period, cutoff = extract_bdata_info(fpath)
    info = raw.get("info", {})
    metagame = info.get("metagame", "unknown")
    num_battles = info.get("number of battles", 0)
    data = raw.get("data", {})

    rows = []
    for species_name, stats in data.items():
        raw_count = stats.get("Raw count", 0)
        usage = stats.get("usage", 0.0)
        viability = stats.get("Viability Ceiling", [0, 0, 0, 0])

        abilities = stats.get("Abilities", {})
        items = stats.get("Items", {})
        spreads = stats.get("Spreads", {})
        moves = stats.get("Moves", {})
        teammates = stats.get("Teammates", {})

        rows.append({
            "period": period,
            "cutoff": cutoff,
            "metagame": metagame,
            "num_battles": num_battles,
            "species_name": species_name,
            "raw_count": raw_count,
            "usage_pct": round(usage * 100, 4) if usage else 0.0,
            "viability_0": float(viability[0]) if len(viability) > 0 else 0.0,
            "viability_1": float(viability[1]) if len(viability) > 1 else 0.0,
            "viability_2": float(viability[2]) if len(viability) > 2 else 0.0,
            "viability_3": float(viability[3]) if len(viability) > 3 else 0.0,
            "top_ability": _top_key(abilities),
            "top_ability_pct": _top_key_pct(abilities, raw_count),
            "top_item": _top_key(items),
            "top_item_pct": _top_key_pct(items, raw_count),
            "top_spread": _top_key(spreads),
            "top_spread_pct": _top_key_pct(spreads, raw_count),
            "top_move": _top_key(moves),
            "top_move_pct": _top_key_pct(moves, raw_count),
            "top_teammate": _top_key(teammates),
            "top_teammate_pct": _top_key_pct(teammates, raw_count),
        })

    return rows


def parse_bdata_files(spark: SparkSession, bdata_dir: str) -> DataFrame:
    """Parse all BData JSON files into a single DataFrame."""
    import glob

    files = sorted(glob.glob(os.path.join(bdata_dir, "*.json")))
    if not files:
        raise FileNotFoundError(f"No BData files found in {bdata_dir}")

    print(f"Parsing {len(files)} BData metagame files...")

    all_rows = []
    for fpath in files:
        all_rows.extend(_parse_one_bdata_file(fpath))

    from common.schemas import BDATA_SCHEMA

    df = spark.createDataFrame(
        spark.sparkContext.parallelize(all_rows),
        schema=BDATA_SCHEMA,
    )

    # Summary
    species_count = df.select("species_name").distinct().count()
    periods = df.select("period").distinct().count()
    print(f"  BData: {df.count()} rows, {species_count} unique species, "
          f"{periods} periods")
    return df
