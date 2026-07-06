#!/usr/bin/env python3
"""
Convert event_new.jsonl (Gen9 simulator events) into battle_pokemon_states rows.

New event types:
  battle_init     → full team (species, moves, item, ability)
  turn_damage     → damage dealt
  turn_faint      → KO tracking
  turn_switch     → species appearances
  turn_heal       → heal info
  turn_ability    → ability trigger
  battle_result   → battle outcome
"""
import json, sqlite3, sys
from pathlib import Path
from collections import defaultdict

PROJECT = Path(__file__).resolve().parent.parent
OUTPUT_DB = PROJECT / "data" / "output.db"


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
    with open(filepath, "r", encoding="utf-8") as f:
        events = [json.loads(l) for l in f if l.strip()]

    # Track per-battle state
    battles = {}  # battle_id → {teams, damage, faints, hp_tracker}

    for e in events:
        evt = e["event"]
        d = e.get("data", {})

        # ── battle_init: capture full team info ──
        if evt == "battle_init":
            bid = d.get("battle_id", "")
            if not bid:
                continue
            side_a = d.get("side_a", [])
            side_b = d.get("side_b", [])
            battles[bid] = {
                "teams": {"a": side_a, "b": side_b},
                "hp": {"a": {}, "b": {}},        # slot → current hp_pct
                "faints": set(),
                "faint_side": {},
            }
            # Init HP tracker
            for side_key, team in [("a", side_a), ("b", side_b)]:
                for slot, mon in enumerate(team):
                    # estimate max HP from species base
                    sid = mon.get("speciesID", 0)
                    hp_pct = 100.0
                    battles[bid]["hp"][side_key][slot] = hp_pct

        # ── turn_damage: track HP loss ──
        elif evt == "turn_damage":
            bid = d.get("battle_id", "")
            if bid not in battles:
                continue
            target_side = d.get("target_side", "b")
            species = d.get("target_species", 0)
            damage = d.get("damage", 0)
            # Find which slot this species is in
            team = battles[bid]["teams"].get(target_side, [])
            for slot, mon in enumerate(team):
                if mon.get("speciesID") == species:
                    hp = battles[bid]["hp"][target_side]
                    prev = hp.get(slot, 100.0)
                    # estimate HP% reduction (rough: ~150 total HP per mon)
                    pct_loss = min(prev, damage / 150.0 * 100)
                    hp[slot] = max(0.0, prev - pct_loss)
                    if d.get("fainted"):
                        battles[bid]["faints"].add((target_side, species))
                        battles[bid]["faint_side"][(target_side, species)] = d.get("turn", 0)
                        hp[slot] = 0.0
                    break

        # ── turn_faint: mark KO ──
        elif evt == "turn_faint":
            bid = d.get("battle_id", "")
            side = d.get("side", "")
            species = d.get("species", 0)
            if bid in battles:
                battles[bid]["faints"].add((side, species))
                # Mark HP as 0
                team = battles[bid]["teams"].get(side, [])
                for slot, mon in enumerate(team):
                    if mon.get("speciesID") == species:
                        battles[bid]["hp"][side][slot] = 0.0
                        break

        # ── turn_switch: track appearances ──
        elif evt == "turn_switch":
            bid = d.get("battle_id", "")
            side = d.get("side", "")
            species = d.get("species", 0)
            if bid in battles:
                team = battles[bid]["teams"].get(side, [])
                for slot, mon in enumerate(team):
                    if mon.get("speciesID") == species:
                        battles[bid]["hp"][side][slot] = 100.0  # reset HP on switch in
                        break

        # ── turn_heal: restore HP ──
        elif evt == "turn_heal":
            bid = d.get("battle_id", "")
            side = d.get("target_side", "")
            species = d.get("target_species", 0)
            heal = d.get("heal", 0)
            if bid in battles:
                team = battles[bid]["teams"].get(side, [])
                for slot, mon in enumerate(team):
                    if mon.get("speciesID") == species:
                        hp = battles[bid]["hp"][side]
                        prev = hp.get(slot, 100.0)
                        pct_heal = heal / 150.0 * 100
                        hp[slot] = min(100.0, prev + pct_heal)
                        break

    # ── Flatten into battle_pokemon_states rows ──
    conn = sqlite3.connect(str(OUTPUT_DB))
    ensure_schema(conn)
    total = 0

    for bid, b in battles.items():
        for side_key in ("a", "b"):
            side_index = 0 if side_key == "a" else 1
            team = b["teams"].get(side_key, [])
            hp_tracker = b["hp"].get(side_key, {})
            for slot, mon in enumerate(team):
                species_id = mon.get("speciesID", 0)
                if not species_id:
                    continue
                ability_id = mon.get("ability", 0)
                item_id = mon.get("item", 0)
                move_ids = json.dumps(mon.get("moves", []))
                hp_pct = round(hp_tracker.get(slot, 100.0), 1)
                hp_val = int(hp_pct)
                fainted = 1 if (side_key, species_id) in b["faints"] else 0

                cur = conn.execute("""
                    INSERT OR IGNORE INTO battle_pokemon_states
                        (battle_id, turn, side_index, pokemon_index, species_id,
                         hp, max_hp, hp_pct, fainted, ability_id, item_id, move_ids, slot)
                    VALUES (?, 0, ?, ?, ?, ?, 100, ?, ?, ?, ?, ?, ?)
                """, (str(bid), side_index, slot, species_id,
                      hp_val, hp_pct, fainted, ability_id, item_id, move_ids, slot))
                if cur.rowcount and cur.rowcount > 0:
                    total += 1

    conn.commit()
    conn.close()
    return total


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {__file__} <event_new.jsonl>")
        sys.exit(1)

    n = import_events(sys.argv[1])
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        event_count = sum(1 for _ in f if _.strip())
    print(f"Imported {n} rows ({len([e for l in open(sys.argv[1],encoding='utf-8') if (e:=json.loads(l.strip())).get('event','')=='battle_init'])} battles) from {event_count} events")
