#!/usr/bin/env python3
"""
每秒生成一场对战数据，模拟实时对战流。
Ctrl+C 停止。

Usage:
    python3 scripts/gen_battle_stream.py [--interval 1.0] [--turns 10 20]
"""

import json, random, os, sys, time, argparse, sqlite3
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
BATTLE_LOGS = PROJECT / "battle_logs"
DB_PATH = PROJECT / "data" / "pokemon.db"

# ── Load real game data from DB ─────────────────────────
def _load_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    # Load all species with their possible abilities and learnable moves
    species = {}
    for r in conn.execute("SELECT id, base_hp FROM species WHERE base_hp > 0").fetchall():
        species[r["id"]] = {"base_hp": max(100, r["base_hp"])}
    # Load species abilities (use first available)
    for r in conn.execute("SELECT species_id, ability_id FROM species_abilities GROUP BY species_id").fetchall():
        if r["species_id"] in species:
            species[r["species_id"]]["ability_id"] = r["ability_id"]
    # Load learnsets: get all move IDs per species (lazy-loaded per species)
    # Store just the list of species_ids that have moves
    species_with_moves = set()
    for r in conn.execute("SELECT DISTINCT species_id FROM learnsets").fetchall():
        species_with_moves.add(r["species_id"])
    conn.close()

    # For each species, load moves lazily or use random fallback
    ALL_MOVES = [33,34,36,38,53,59,63,85,89,94,10,52,98,22,75,76,79,163,37,38,58,126,14,24,97,87,
                 55,56,57,115,7,44,19,17,82,73,77,74,70,42,228,188,245,404,520,239,345,398,348,202]
    for sid in species:
        species[sid]["moves"] = random.sample(ALL_MOVES, min(4, len(ALL_MOVES)))
    return species

_GAME_DATA = _load_db()
SPECIES_IDS = [sid for sid in _GAME_DATA if _GAME_DATA[sid].get("moves")]
ITEMS = [0,0,0,0,2,2,3,3,6,6,10,11,14,23,31,999]

def pick_random_pokemon():
    """Pick a random species with random moves and ability from real game data."""
    sid = random.choice(SPECIES_IDS)
    data = _GAME_DATA[sid]
    hp = data.get("base_hp", 200)
    ability = data.get("ability_id", 65)
    moves = random.sample(data["moves"], min(4, len(data["moves"])))
    return (sid, ability, moves, hp)

def make_pokemon(sid, ab, moves, hp, slot, hp_pct=None):
    pct = hp_pct if hp_pct is not None else 100.0
    return {
        "speciesId": sid, "abilityId": ab,
        "itemId": random.choice(ITEMS),
        "hp": int(hp * pct / 100), "maxHp": hp,
        "fainted": pct <= 0,
        "moves": [{"id": m, "maxPp": 20, "pp": 15, "slot": i} for i, m in enumerate(moves)],
        "slot": slot, "types": [random.randint(0, 17)],
        "statStages": [0]*7, "inBattleStatus": [],
        "evs": {"hp":0,"attack":0,"defense":0,"specialAttack":252,"specialDefense":0,"speed":252},
        "ivs": {"hp":31,"attack":31,"defense":31,"specialAttack":31,"specialDefense":31,"speed":31},
        "level": 50, "nature": random.randint(0, 24),
    }

def gen_battle(battle_id, turns):
    """Generate one battle atomically — write to tmp dir, then rename."""
    battle_dir = BATTLE_LOGS / str(battle_id)
    tmp_dir = BATTLE_LOGS / f".tmp_{battle_id}"
    if tmp_dir.exists():
        import shutil
        shutil.rmtree(tmp_dir)
    out = tmp_dir / "output"
    out.mkdir(parents=True, exist_ok=True)

    pa = [pick_random_pokemon() for _ in range(3)]
    pb = [pick_random_pokemon() for _ in range(3)]

    # Turn 0
    (out / "output_0.json").write_text(json.dumps({
        "turn": 0, "descriptions": [],
        "battle": {"field": {"type":0,"duration":0}, "weather": {"type":0,"duration":0},
            "sides": [
                {"side":0,"active":0,"count":3,"name":"A","sideEffects":{},
                 "pokemons": [make_pokemon(*pa[i], slot=i) for i in range(3)]},
                {"side":1,"active":0,"count":3,"name":"B","sideEffects":{},
                 "pokemons": [make_pokemon(*pb[i], slot=i) for i in range(3)]},
            ]},
        "events": [{"timeline_index":0,"turn_index":0,"description":"Battle start.",
                     "details":{"event_type":"battle_start"}}],
    }, ensure_ascii=False))

    hp_tracker = {}  # (side, slot) -> hp_pct

    for turn in range(1, turns + 1):
        sides_out = []
        for si, team in enumerate([pa, pb]):
            pokes = []
            for slot, t in enumerate(team):
                key = (si, slot)
                if key not in hp_tracker: hp_tracker[key] = 100.0
                loss = random.uniform(0, 35)
                new_hp = max(0, hp_tracker[key] - loss)
                if 0 < new_hp < 25 and random.random() < 0.2: new_hp = 0
                hp_tracker[key] = new_hp
                pokes.append(make_pokemon(*t, slot=slot, hp_pct=new_hp))
            sides_out.append({"side": si, "active": 0, "count": 3,
                              "name": "A" if si == 0 else "B", "pokemons": pokes, "sideEffects": {}})

        events = [{"timeline_index": turn*2, "turn_index": turn,
                    "description": f"Turn {turn} attack.",
                    "details": {"event_type": "damage", "damage": random.randint(5, 60)}}]

        (out / f"output_{turn}.json").write_text(json.dumps({
            "turn": turn, "descriptions": [],
            "battle": {"field": {"type":0,"duration":0}, "weather": {"type":0,"duration":0},
                       "sides": sides_out},
            "events": events,
        }, ensure_ascii=False))

    # Atomic rename — watcher sees complete battle all at once
    if battle_dir.exists():
        import shutil
        shutil.rmtree(battle_dir)
    tmp_dir.rename(battle_dir)


def main():
    parser = argparse.ArgumentParser(description="Stream battle data every N seconds")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--turns", type=int, nargs=2, default=[10, 20])
    parser.add_argument("--start-id", type=int, default=100)
    args = parser.parse_args()

    bid = args.start_id
    print(f"Streaming battles every {args.interval}s (turns {args.turns[0]}-{args.turns[1]}). Ctrl+C to stop.")
    print(f"Starting from ID {bid}")

    try:
        while True:
            turns = random.randint(*args.turns)
            t0 = time.time()
            gen_battle(bid, turns)
            elapsed = time.time() - t0
            print(f"  #{bid} | {turns}t | {elapsed*1000:.0f}ms")
            bid += 1
            sleep_time = args.interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    except KeyboardInterrupt:
        print(f"\nStopped. Generated {bid - args.start_id} battles.")


if __name__ == "__main__":
    main()
