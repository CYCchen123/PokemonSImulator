#!/usr/bin/env python3
"""
Convert frontend events (battle events) into battle_pokemon_states rows.
Reads events JSONL, extracts species appearances, KOs, damage into output.db.

Usage:
    python scripts/events_to_db.py events_2026-07-06.jsonl
"""
import json, sqlite3, sys
from pathlib import Path
from collections import defaultdict

PROJECT = Path(__file__).resolve().parent.parent
OUTPUT_DB = PROJECT / "data" / "output.db"
POKEMON_DB = PROJECT / "data" / "pokemon.db"


def ensure_schema(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS battle_pokemon_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            battle_id TEXT NOT NULL,
            turn INTEGER NOT NULL DEFAULT 0,
            side_index INTEGER NOT NULL DEFAULT 0,
            pokemon_index INTEGER NOT NULL DEFAULT 0,
            species_id INTEGER NOT NULL DEFAULT 0,
            hp INTEGER NOT NULL DEFAULT 0,
            max_hp INTEGER NOT NULL DEFAULT 100,
            hp_pct REAL NOT NULL DEFAULT 100.0,
            fainted INTEGER NOT NULL DEFAULT 0,
            ability_id INTEGER NOT NULL DEFAULT 0,
            item_id INTEGER NOT NULL DEFAULT 0,
            move_ids TEXT NOT NULL DEFAULT '[]',
            slot INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _imported_files (
            filepath TEXT PRIMARY KEY,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def import_events(filepath: str) -> int:
    """Parse events JSONL and insert battle_pokemon_states rows."""
    with open(filepath, "r", encoding="utf-8") as f:
        events = [json.loads(l) for l in f if l.strip()]

    # Group events by battle_id
    battles = defaultdict(lambda: {"species": set(), "faints": set(), "sides": {},
                                    "appearances": {}, "player_id": "", "session_id": ""})
    battle_events = [e for e in events if e["event"] in
                     ("battle_start", "battle_end", "turn_action", "damage_dealt",
                      "faint", "switch_in")]

    for e in battle_events:
        evt = e["event"]
        d = e.get("data", {})
        bid = d.get("battle_id", e.get("session_id", "unknown"))
        b = battles[bid]
        b["player_id"] = e.get("player_id", "")
        b["session_id"] = e.get("session_id", "")

        if evt == "battle_start":
            side_char = d.get("side", "a")
            b["sides"][side_char] = {"team_size": d.get("team_size", 0)}
            b["battle_id"] = bid

        elif evt == "switch_in":
            species_id = d.get("pokemon", 0)
            side = d.get("side", "a")
            turn = d.get("turn", 0)
            if species_id:
                key = f"{side}_{species_id}"
                b["species"].add((side, species_id))
                b["appearances"][key] = b["appearances"].get(key, 0) + 1

        elif evt == "faint":
            species_id = d.get("pokemon", 0)
            side = d.get("side", "b")  # target side
            turn = d.get("turn", 0)
            if species_id:
                b["species"].add((side, species_id))
                b["faints"].add((side, species_id))

        elif evt == "damage_dealt":
            side = d.get("target_side", "b")
            # track that damage happened to estimate HP loss
            pass

    # Flatten battles into rows
    conn = sqlite3.connect(str(OUTPUT_DB))
    ensure_schema(conn)

    total = 0
    for bid, b in battles.items():
        if b.get("battle_id"):
            bid = b["battle_id"]
        for (side, species_id) in b["species"]:
            side_index = 0 if side == "a" else 1
            fainted = 1 if (side, species_id) in b["faints"] else 0
            hp_pct = 0.0 if fainted else 70.0  # default 70% for survivors
            hp = int(hp_pct)
            appearances = b["appearances"].get(f"{side}_{species_id}", 1)
            for slot in range(appearances):
                cur = conn.execute("""
                    INSERT OR IGNORE INTO battle_pokemon_states
                        (battle_id, turn, side_index, pokemon_index, species_id,
                         hp, max_hp, hp_pct, fainted, ability_id, item_id, move_ids, slot)
                    VALUES (?, 0, ?, ?, ?, ?, 100, ?, ?, 0, 0, '[]', ?)
                """, (str(bid), side_index, slot, species_id, hp, hp_pct, fainted, slot))
                if cur.rowcount and cur.rowcount > 0:
                    total += 1

    conn.commit()
    conn.close()
    return total


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {__file__} <events.jsonl>")
        sys.exit(1)

    n = import_events(sys.argv[1])
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        event_count = sum(1 for _ in f if _.strip())
    print(f"Imported {n} rows from {event_count} events")
