"""
Load game-data lookup tables (species, moves, abilities, items)
as Spark broadcast variables for efficient joins across analytics.

Reads from the project's data/*.json files and the SQLite database
as a fallback.
"""

import json
from typing import Dict, Optional

from pyspark.sql import SparkSession


def _read_json(path: str) -> list:
    """Read a JSON file (array or object). Returns a list of dicts."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Normalise to list
    if isinstance(data, dict):
        # Check for wrapped format: {"species": [...], "moves": [...], ...}
        for key in ("species", "moves", "abilities", "items"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return [data]
    if isinstance(data, list):
        return data
    return []


class LookupTables:
    """Container for broadcast lookup variables used by analytics."""

    def __init__(self, spark: SparkSession, project_root: str):
        import os

        data_dir = os.path.join(project_root, "data")

        # ── Species: id -> {name, type1, type2, baseStats} ─────────
        species_list = _read_json(os.path.join(data_dir, "species.json"))
        species_map = {}
        for s in species_list:
            sid = s.get("id")
            if sid is None:
                continue
            species_map[sid] = {
                "name": s.get("name", f"#{sid}"),
                "type1": s.get("type1", 0),
                "type2": s.get("type2", 0),
                "base_hp": (s.get("baseStats", [0] * 6) + [0] * 6)[0],
                "base_atk": (s.get("baseStats", [0] * 6) + [0] * 6)[1],
                "base_def": (s.get("baseStats", [0] * 6) + [0] * 6)[2],
                "base_spa": (s.get("baseStats", [0] * 6) + [0] * 6)[3],
                "base_spd": (s.get("baseStats", [0] * 6) + [0] * 6)[4],
                "base_spe": (s.get("baseStats", [0] * 6) + [0] * 6)[5],
            }
        self.species_map = spark.sparkContext.broadcast(species_map)

        # ── Moves: id -> {name, type, category, power, accuracy, pp} ─
        moves_list = _read_json(os.path.join(data_dir, "moves.json"))
        moves_map = {}
        for m in moves_list:
            mid = m.get("id")
            if mid is None:
                continue
            moves_map[mid] = {
                "name": m.get("name", m.get("apiName", f"#{mid}")),
                "type": m.get("type", 0),
                "category": m.get("category", "status"),
                "power": m.get("power", 0) or 0,
                "accuracy": m.get("accuracy", 0) or 0,
                "pp": m.get("pp", 0) or 0,
                "priority": m.get("priority", 0) or 0,
            }
        self.moves_map = spark.sparkContext.broadcast(moves_map)

        # ── Abilities: id -> name ──────────────────────────────────
        abilities_list = _read_json(os.path.join(data_dir, "abilities.json"))
        abilities_map = {}
        for a in abilities_list:
            aid = a.get("id")
            if aid is None:
                continue
            abilities_map[aid] = a.get("name", a.get("apiName", f"#{aid}"))
        self.abilities_map = spark.sparkContext.broadcast(abilities_map)

        # ── Items: id -> name ──────────────────────────────────────
        items_list = _read_json(os.path.join(data_dir, "items.json"))
        items_map = {}
        for i in items_list:
            iid = i.get("id")
            if iid is None:
                continue
            items_map[iid] = i.get("name", f"#{iid}")
        self.items_map = spark.sparkContext.broadcast(items_map)

        # ── Type names (18 types) ──────────────────────────────────
        self.type_names = spark.sparkContext.broadcast({
            0: "Normal", 1: "Fire", 2: "Water", 3: "Electric",
            4: "Grass", 5: "Ice", 6: "Fighting", 7: "Poison",
            8: "Ground", 9: "Flying", 10: "Psychic", 11: "Bug",
            12: "Rock", 13: "Ghost", 14: "Dragon", 15: "Dark",
            16: "Steel", 17: "Fairy",
        })

        print(f"Lookup tables loaded: {len(species_map)} species, "
              f"{len(moves_map)} moves, {len(abilities_map)} abilities, "
              f"{len(items_map)} items")

    def species_name(self, sid: int) -> str:
        m = self.species_map.value.get(sid, {})
        return m.get("name", f"#{sid}")

    def move_name(self, mid: int) -> str:
        m = self.moves_map.value.get(mid, {})
        return m.get("name", f"#{mid}")

    def ability_name(self, aid: int) -> str:
        return self.abilities_map.value.get(aid, f"#{aid}")

    def item_name(self, iid: int) -> str:
        return self.items_map.value.get(iid, f"#{iid}")

    def type_name(self, tid: int) -> str:
        return self.type_names.value.get(tid, f"Type#{tid}")
