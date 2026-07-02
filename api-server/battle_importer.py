"""
Battle log importer: scan battle_logs/ for output JSON files,
parse Pokemon state data, and upsert into SQLite.

Usage:
    from battle_importer import import_new_battles
    count = import_new_battles()  # returns number of new rows
"""

import json
import os
import sqlite3
import glob
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATTLE_LOGS = PROJECT_ROOT / "battle_logs"
DB_PATH = PROJECT_ROOT / "data" / "output.db"
RECENT_DB_PATH = PROJECT_ROOT / "data" / "output_recent.db"


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _find_output_files() -> List[str]:
    """Find all output JSON files, returning absolute paths."""
    files = []
    for pat in ["output/output_*.json", "*/output/output_*.json"]:
        for f in BATTLE_LOGS.glob(pat):
            files.append(str(f))
    return sorted(files)


def _extract_battle_id(filepath: str) -> str:
    """Extract battle_id from file path.
    battle_logs/output/output_0.json → "1" (default)
    battle_logs/5/output/output_0.json → "5"
    """
    parts = Path(filepath).parts
    # Check if parent dir is named like "output" under a battle id dir
    if len(parts) >= 2 and parts[-2] == "output":
        grandparent = parts[-3] if len(parts) >= 3 else "1"
        if grandparent not in ("battle_logs", "."):
            return grandparent
    return "1"


def _parse_pokemon_states(filepath: str) -> Tuple[str, list]:
    """Parse one output JSON, return (battle_id, list of row dicts)."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    battle_id = _extract_battle_id(filepath)
    turn = data.get("turn", 0)
    rows = []

    sides = data.get("battle", {}).get("sides", [])
    for side in sides:
        side_index = side.get("side", 0)
        pokemons = side.get("pokemons", [])
        for pi, p in enumerate(pokemons):
            if p.get("speciesId", 0) == 0:
                continue  # empty slot
            rows.append({
                "battle_id": battle_id,
                "turn": turn,
                "side_index": side_index,
                "pokemon_index": pi,
                "species_id": p.get("speciesId", 0),
                "hp": p.get("hp", 0),
                "max_hp": p.get("maxHp", 0),
                "hp_pct": round(p.get("hp", 0) / max(p.get("maxHp", 1), 1) * 100, 1),
                "fainted": 1 if p.get("fainted", False) else 0,
                "ability_id": p.get("abilityId", 0),
                "item_id": p.get("itemId", 0),
                "move_ids": json.dumps([m.get("id", 0) for m in p.get("moves", [])]),
                "slot": p.get("slot", 0),
            })

    return battle_id, rows


def _insert_rows(conn, rows):
    """Insert parsed rows into a DB connection."""
    inserted = 0
    for row in rows:
        cur = conn.execute("""
            INSERT OR IGNORE INTO battle_pokemon_states
                (battle_id, turn, side_index, pokemon_index,
                 species_id, hp, max_hp, hp_pct, fainted,
                 ability_id, item_id, move_ids, slot)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["battle_id"], row["turn"], row["side_index"],
            row["pokemon_index"], row["species_id"],
            row["hp"], row["max_hp"], row["hp_pct"], row["fainted"],
            row["ability_id"], row["item_id"], row["move_ids"],
            row["slot"],
        ))
        if cur.rowcount and cur.rowcount > 0:
            inserted += 1
    return inserted


def import_new_battles(db_path: str = None) -> int:
    """Scan for new output files and import into BOTH historical + recent DBs.
    Returns the number of new rows inserted into historical DB.
    """
    hist_conn = sqlite3.connect(str(DB_PATH))
    recent_conn = sqlite3.connect(str(RECENT_DB_PATH))

    # Purge old data from recent DB (older than 1 hour)
    recent_conn.execute(
        "DELETE FROM battle_pokemon_states WHERE created_at < datetime('now', '-1 hour')"
    )
    recent_conn.commit()

    all_files = _find_output_files()
    total_inserted = 0

    for filepath in all_files:
        # Check BOTH DBs — import if either is missing this file
        hist_done = hist_conn.execute(
            "SELECT 1 FROM _imported_files WHERE filepath = ?", (filepath,)
        ).fetchone()
        recent_done = recent_conn.execute(
            "SELECT 1 FROM _imported_files WHERE filepath = ?", (filepath,)
        ).fetchone()
        if hist_done and recent_done:
            continue

        try:
            battle_id, rows = _parse_pokemon_states(filepath)
        except Exception as e:
            print(f"  [WARN] Failed to parse {filepath}: {e}")
            continue

        if not rows:
            if not hist_done:
                hist_conn.execute("INSERT OR IGNORE INTO _imported_files(filepath) VALUES (?)", (filepath,))
                hist_conn.commit()
            if not recent_done:
                recent_conn.execute("INSERT OR IGNORE INTO _imported_files(filepath) VALUES (?)", (filepath,))
                recent_conn.commit()
            continue

        # Insert into whichever DB is missing this file
        inserted = 0
        if not hist_done:
            inserted = _insert_rows(hist_conn, rows)
            hist_conn.execute("INSERT OR IGNORE INTO _imported_files(filepath) VALUES (?)", (filepath,))
            hist_conn.commit()
        if not recent_done:
            _insert_rows(recent_conn, rows)
            recent_conn.execute("INSERT OR IGNORE INTO _imported_files(filepath) VALUES (?)", (filepath,))
            recent_conn.commit()

        if inserted > 0:
            print(f"  [import] {filepath}: {inserted} rows (battle {battle_id}, turn {rows[0]['turn'] if rows else '?'})")
        total_inserted += inserted

    hist_conn.close()
    recent_conn.close()
    return total_inserted


if __name__ == "__main__":
    count = import_new_battles()
    print(f"Done: {count} new rows imported.")
