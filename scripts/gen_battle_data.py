#!/usr/bin/env python3
"""
Generate synthetic battle log data for testing the analytics pipeline.
Creates realistic battle_logs/<id>/output/*.json files without running the engine.

Usage:
    python3 scripts/gen_battle_data.py [--battles N] [--turns MIN MAX] [--clear]

The live watcher will auto-detect new files and import them into SQLite.
"""
import json, random, os, argparse
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
BATTLE_LOGS = PROJECT / "battle_logs"

# ── Pokemon pools with varied species ──────────────────────────
# Each entry: (species_id, ability_id, [move_ids], base_hp)
POKEMON_DB = [
    # Starters
    (3, 65, [22, 33, 73, 77], 200),    # Venusaur
    (6, 66, [53, 163, 44, 7], 190),     # Charizard
    (9, 67, [57, 55, 110, 61], 195),    # Blastoise
    (154, 65, [75, 76, 79, 74], 210),   # Meganium
    (157, 66, [53, 89, 63, 115], 190),  # Typhlosion
    (160, 67, [55, 56, 57, 59], 200),   # Feraligatr
    (254, 65, [75, 348, 202, 79], 180), # Sceptile
    (257, 66, [53, 89, 24, 63], 195),   # Blaziken
    (260, 67, [55, 89, 56, 59], 210),   # Swampert
    (389, 65, [75, 89, 76, 402], 220),  # Torterra
    (392, 66, [53, 89, 63, 136], 190),  # Infernape
    (395, 67, [55, 56, 57, 59], 210),   # Empoleon
    # Legendaries
    (144, 46, [58, 59, 63, 115], 200),  # Articuno
    (145, 46, [85, 87, 24, 63], 200),   # Zapdos
    (146, 46, [53, 59, 63, 126], 200),  # Moltres
    (150, 46, [94, 59, 63, 115], 220),  # Mewtwo
    (249, 46, [59, 58, 94, 115], 230),  # Lugia
    (250, 46, [53, 76, 58, 115], 230),  # Ho-Oh
    (382, 2, [55, 56, 59, 126], 210),   # Kyogre
    (383, 70, [53, 89, 76, 126], 210),  # Groudon
    (384, 76, [53, 59, 63, 126], 220),  # Rayquaza
    # Popular competitive
    (25, 9, [85, 97, 87, 24], 120),     # Pikachu
    (94, 20, [94, 85, 89, 92], 170),    # Gengar
    (130, 22, [55, 56, 57, 59], 220),   # Gyarados
    (131, 11, [55, 56, 59, 58], 240),   # Lapras
    (143, 47, [34, 59, 63, 76], 260),   # Snorlax
    (149, 136, [63, 59, 53, 56], 200),  # Dragonite
    (248, 45, [89, 59, 63, 53], 230),   # Tyranitar
    (373, 22, [53, 59, 63, 89], 220),   # Salamence
    (376, 25, [34, 89, 63, 94], 195),   # Metagross
    (445, 8, [89, 63, 53, 59], 230),    # Garchomp
    (448, 9, [53, 89, 63, 94], 180),    # Lucario
    (658, 92, [55, 56, 57, 59], 170),   # Greninja
    (888, 234, [53, 34, 63, 59], 200),  # Zacian
    (889, 234, [53, 34, 63, 59], 230),  # Zamazenta
]

ITEMS = [0, 0, 0, 2, 2, 3, 3, 6, 6, 10, 11, 14, 23, 31, 999]
NATURES = list(range(25))

# HP evolution per turn: pokemon lose HP gradually then sometimes faint
# Key: battle turns create varied HP curves


def build_pokemon(species_id, ability_id, moves, base_hp, slot, turn_hp_pct=None):
    """Build a pokemon state dict for a given turn."""
    hp_pct = turn_hp_pct if turn_hp_pct is not None else 100.0
    hp = int(base_hp * hp_pct / 100)
    return {
        "speciesId": species_id,
        "abilityId": ability_id,
        "itemId": random.choice(ITEMS),
        "hp": hp,
        "maxHp": base_hp,
        "fainted": hp_pct is not None and hp_pct <= 0,
        "moves": [{"id": m, "maxPp": random.choice([10, 15, 20, 25, 30]),
                    "pp": random.choice([5, 10, 15, 20, 25, 30]),
                    "slot": i} for i, m in enumerate(moves)],
        "slot": slot,
        "types": [random.randint(0, 17)],
        "statStages": [0, 0, 0, 0, 0, 0, 0],
        "inBattleStatus": [],
        "evs": {"hp": 0, "attack": 0, "defense": 0, "specialAttack": 252, "specialDefense": 0, "speed": 252},
        "ivs": {"hp": 31, "attack": 31, "defense": 31, "specialAttack": 31, "specialDefense": 31, "speed": 31},
        "level": 50,
        "nature": random.choice(NATURES),
    }


def make_battle_team(pool, team_size=3):
    """Pick team_size unique pokemon from the pool."""
    chosen = random.sample(pool, min(team_size, len(pool)))
    return [c[:4] for c in chosen]  # (species_id, ability_id, moves, base_hp)


def generate_battle_json(battle_id, side_a_pool, side_b_pool, num_turns):
    """Generate all output JSON files for a complete battle."""
    import shutil
    output_dir = BATTLE_LOGS / str(battle_id) / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    team_a = make_battle_team(side_a_pool)
    team_b = make_battle_team(side_b_pool)

    # Turn 0: all pokemon at full HP (initial state)
    sides = [
        {"side": 0, "active": 0, "count": len(team_a),
         "name": "Side A",
         "pokemons": [build_pokemon(*t, slot=i) for i, t in enumerate(team_a)],
         "sideEffects": {}},
        {"side": 1, "active": 0, "count": len(team_b),
         "name": "Side B",
         "pokemons": [build_pokemon(*t, slot=i) for i, t in enumerate(team_b)],
         "sideEffects": {}},
    ]

    state = {
        "descriptions": [],
        "turn": 0,
        "battle": {
            "field": {"duration": 0, "type": 0},
            "weather": {"duration": 0, "type": 0},
            "sides": sides,
        },
        "events": [{"timeline_index": 0, "turn_index": 0,
                     "description": "Battle start.",
                     "details": {"event_type": "battle_start"}}],
    }

    with open(output_dir / "output_0.json", "w") as f:
        json.dump(state, f, ensure_ascii=False)

    # Turns 1..N: simulate HP changes
    # Each pokemon starts at 100% and randomly loses HP each turn
    hp_tracker = {}  # (side, slot) -> current hp_pct

    for turn in range(1, num_turns + 1):
        sides_out = []
        for side_idx, team in enumerate([team_a, team_b]):
            pokemons = []
            for slot, t in enumerate(team):
                key = (side_idx, slot)
                if key not in hp_tracker:
                    hp_tracker[key] = 100.0

                # Random HP change: lose 0-40% HP, 10% chance to faint
                loss = random.uniform(0, 40) if hp_tracker[key] > 0 else 0
                new_hp = max(0, hp_tracker[key] - loss)
                # Slight chance to faint if HP is low
                if new_hp > 0 and new_hp < 30 and random.random() < 0.15:
                    new_hp = 0
                hp_tracker[key] = new_hp

                poke = build_pokemon(*t, slot=slot, turn_hp_pct=new_hp)
                pokemons.append(poke)

            sides_out.append({
                "side": side_idx,
                "active": 0,
                "count": len(team),
                "name": f"Side {'A' if side_idx == 0 else 'B'}",
                "pokemons": pokemons,
                "sideEffects": {},
            })

        # Generate events
        events = []
        for side_idx in range(2):
            attacker_slot = random.randint(0, len([team_a, team_b][side_idx]) - 1)
            defender_slot = random.randint(0, len([team_a, team_b][1 - side_idx]) - 1)
            events.append({
                "timeline_index": turn * 2,
                "turn_index": turn,
                "description": f"Side {'A' if side_idx == 0 else 'B'} pokemon uses attack.",
                "details": {
                    "event_type": "damage",
                    "side_index": side_idx,
                    "pokemon_index": attacker_slot,
                    "target_side": 1 - side_idx,
                    "target_pokemon": defender_slot,
                    "damage": random.randint(10, 80),
                },
            })

        state = {
            "descriptions": [],
            "turn": turn,
            "battle": {
                "field": {"duration": 0, "type": 0},
                "weather": {"duration": 0, "type": 0},
                "sides": sides_out,
            },
            "events": events,
        }

        with open(output_dir / f"output_{turn}.json", "w") as f:
            json.dump(state, f, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic battle data")
    parser.add_argument("--battles", type=int, default=10, help="Number of battles")
    parser.add_argument("--turns", type=int, nargs=2, default=[12, 25],
                        help="Min and max turns per battle")
    parser.add_argument("--clear", action="store_true", help="Clear existing battle data")
    parser.add_argument("--start-id", type=int, default=20, help="Starting battle ID")
    args = parser.parse_args()

    if args.clear:
        import shutil
        for d in BATTLE_LOGS.iterdir():
            if d.is_dir() and d.name.isdigit():
                shutil.rmtree(d)
        print("Cleared existing battle data.")

    pool_size = min(6, len(POKEMON_DB) // 2)
    start_id = args.start_id

    for i in range(args.battles):
        battle_id = start_id + i
        pool_a = random.sample(POKEMON_DB, pool_size)
        pool_b = random.sample(POKEMON_DB, pool_size)
        turns = random.randint(args.turns[0], args.turns[1])

        print(f"Battle {battle_id}: {turns} turns, "
              f"A=[{','.join(str(p[0]) for p in pool_a[:3])}] vs "
              f"B=[{','.join(str(p[0]) for p in pool_b[:3])}]")

        generate_battle_json(battle_id, pool_a, pool_b, turns)

    total_files = sum(1 for _ in BATTLE_LOGS.rglob("output_*.json"))
    print(f"\nDone! {args.battles} battles, {total_files} total output files.")
    print(f"Live watcher will auto-import into SQLite within {5}s.")


if __name__ == "__main__":
    main()
