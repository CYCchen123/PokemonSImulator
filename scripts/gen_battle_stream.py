#!/usr/bin/env python3
"""
Generate battle events in event_new.jsonl format.
Supports local file output and Kafka cluster mode.

Usage:
    python scripts/gen_battle_stream.py [--interval 2.0] [--turns 5 15] [--kafka broker:9092]
"""
import json, random, os, sys, time, argparse, sqlite3, uuid
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
BATTLE_LOGS = PROJECT / "battle_logs"
try:
    BATTLE_LOGS.mkdir(parents=True, exist_ok=True)
except PermissionError:
    BATTLE_LOGS = Path.home() / "battle_logs"
    BATTLE_LOGS.mkdir(parents=True, exist_ok=True)
DB_PATH = PROJECT / "data" / "pokemon.db"
# Fallback: look for pokemon.db in home dir or data subdir
if not DB_PATH.exists():
    for alt in [Path.home() / "pokemon.db", Path.home() / "data" / "pokemon.db"]:
        if alt.exists():
            DB_PATH = alt
            break

# ── Load game data ─────────────────────────
def _load_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    species = {}
    for r in conn.execute("SELECT id, base_hp, name FROM species WHERE base_hp > 0").fetchall():
        species[r["id"]] = {"base_hp": max(100, r["base_hp"]), "name": r["name"]}

    # Abilities
    for sid in species:
        row = conn.execute(
            "SELECT ability_id FROM species_abilities WHERE species_id=? LIMIT 1", (sid,)
        ).fetchone()
        species[sid]["ability_id"] = row[0] if row else 65

    # Moves — load from learnsets
    move_map = {}
    for r in conn.execute("SELECT species_id, move_id FROM learnsets").fetchall():
        sid_key = r["species_id"]
        mid_val = r["move_id"]
        if sid_key not in move_map:
            move_map[sid_key] = []
        move_map[sid_key].append(mid_val)

    ALL_MOVES = [33,34,36,38,53,59,63,85,89,94,10,52,98,22,75,76,79,163,37,58,126,14,24,97,87,
                 55,56,57,115,7,44,19,17,82,73,77,74,70,42,228,188,245,404,520,239,345,398,348,202]
    for sid in species:
        moves = move_map.get(sid, [])
        species[sid]["moves"] = random.sample(moves, min(4, len(moves))) if len(moves) >= 4 \
            else random.sample(ALL_MOVES, min(4, len(ALL_MOVES)))
    conn.close()
    return species

_GAME_DATA = _load_db()
SPECIES_IDS = [sid for sid in _GAME_DATA if _GAME_DATA[sid].get("moves")]
ITEMS = [2,3,6,10,11,14,23,31,188,221,234,240,275,287]
PLAYERS = ["Ash", "Serena", "Leon", "Cynthia"]
PAGES = ["/", "/matchmaking", "/teams", "/stats", "/history", "/data"]
ELEMENTS = ["btn_battle", "btn_team", "btn_stats", "btn_matchmaking", "btn_leave"]
MOVE_NAMES = ["Tackle","Thunderbolt","Flamethrower","Protect","Hydro Pump","Earthquake",
              "Ice Beam","Psychic","Shadow Ball","Dragon Claw","Swords Dance","Recover"]
ABILITIES = ["Drought","Intimidate","Levitate","Swift Swim","Chlorophyll","Mold Breaker"]


def pick_pokemon():
    sid = random.choice(SPECIES_IDS)
    data = _GAME_DATA[sid]
    return {
        "speciesID": sid,
        "moves": random.sample(data["moves"], min(4, len(data["moves"]))),
        "item": random.choice(ITEMS),
        "ability": data.get("ability_id", 65),
        "nature": random.randint(0, 24),
        "level": 50,
    }


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())


# ── Event generators ─────────────────────────

def gen_session(player_id, session_id):
    return {
        "event": "session_start",
        "data": {"player_id": player_id},
        "session_id": session_id,
        "player_id": player_id,
        "timestamp": now_iso()
    }

def gen_page_view(player_id, session_id, page):
    return {
        "event": "page_view",
        "data": {"page": page},
        "session_id": session_id,
        "player_id": player_id,
        "timestamp": now_iso()
    }

def gen_battle_init(battle_id, player_id, session_id, side, opponent_type, team):
    other = "b" if side == "a" else "a"
    return {
        "event": "battle_init",
        "data": {
            "battle_id": battle_id,
            "side": side,
            "opponent_type": opponent_type,
            f"side_{side}": team,
            f"side_{other}": [pick_pokemon() for _ in range(3)],
        },
        "session_id": session_id,
        "player_id": player_id,
        "timestamp": now_iso()
    }

def gen_turn_executed(battle_id, turn, player_id, session_id, side_a_move, side_b_move):
    return {
        "event": "turn_executed",
        "data": {
            "battle_id": battle_id,
            "turn": turn,
            "side_a": {"type": "attack", "move_id": side_a_move, "move_name": random.choice(MOVE_NAMES), "switch_to": None},
            "side_b": {"type": "attack", "move_id": side_b_move, "move_name": random.choice(MOVE_NAMES), "switch_to": None},
        },
        "session_id": session_id,
        "player_id": player_id,
        "timestamp": now_iso()
    }

def gen_turn_damage(battle_id, turn, target_side, target_species, move, damage, fainted, player_id, session_id):
    return {
        "event": "turn_damage",
        "data": {
            "battle_id": battle_id, "turn": turn,
            "target_side": target_side, "target_species": target_species,
            "move": move, "damage": damage, "fainted": fainted,
        },
        "session_id": session_id, "player_id": player_id, "timestamp": now_iso()
    }

def gen_turn_faint(battle_id, turn, species, side, player_id, session_id):
    return {
        "event": "turn_faint",
        "data": {"battle_id": battle_id, "turn": turn, "species": species, "side": side},
        "session_id": session_id, "player_id": player_id, "timestamp": now_iso()
    }

def gen_turn_switch(battle_id, turn, species, side, reason, player_id, session_id):
    return {
        "event": "turn_switch",
        "data": {"battle_id": battle_id, "turn": turn, "species": species, "side": side, "reason": reason},
        "session_id": session_id, "player_id": player_id, "timestamp": now_iso()
    }

def gen_turn_heal(battle_id, turn, target_side, target_species, heal, player_id, session_id):
    return {
        "event": "turn_heal",
        "data": {"battle_id": battle_id, "turn": turn, "target_side": target_side, "target_species": target_species, "heal": heal},
        "session_id": session_id, "player_id": player_id, "timestamp": now_iso()
    }

def gen_turn_ability(battle_id, turn, species, side, ability, player_id, session_id):
    return {
        "event": "turn_ability",
        "data": {"battle_id": battle_id, "turn": turn, "species": species, "side": side, "ability": ability},
        "session_id": session_id, "player_id": player_id, "timestamp": now_iso()
    }

def gen_battle_result(battle_id, side, result, winner, turns, own_rem, opp_rem, player_id, session_id):
    return {
        "event": "battle_result",
        "data": {
            "battle_id": battle_id, "side": side, "result": result,
            "winner": winner, "turns": turns,
            "own_remaining": own_rem, "opp_remaining": opp_rem,
        },
        "session_id": session_id, "player_id": player_id, "timestamp": now_iso()
    }


# ── Battle simulation ─────────────────────────

def gen_battle_events(battle_id, turns, player_a, player_b, session_a, session_b):
    """Generate a full battle as a list of event dicts."""
    events = []

    # Build teams
    team_a = [pick_pokemon() for _ in range(3)]
    team_b = [pick_pokemon() for _ in range(3)]

    # battle_init from both sides' perspective
    events.append(gen_battle_init(battle_id, player_a, session_a, "a", "human", team_a))
    events.append(gen_battle_init(battle_id, player_b, session_b, "b", "human", team_b))

    hp_pct = {"a": {0:100.0,1:100.0,2:100.0}, "b": {0:100.0,1:100.0,2:100.0}}
    faint_counts = {"a": 0, "b": 0}

    for turn in range(1, turns + 1):
        # Choose moves
        a_move = random.choice(team_a[min(turn-1, 2)]["moves"])
        b_move = random.choice(team_b[min(turn-1, 2)]["moves"])
        events.append(gen_turn_executed(battle_id, turn, player_a, session_a, a_move, b_move))

        # Damage to side B (from A)
        dmg_b = random.randint(10, 60)
        target_slot_b = min(turn - 1, 2)
        target_b = team_b[target_slot_b]["speciesID"]
        prev_b = hp_pct["b"][target_slot_b]
        new_b = max(0.0, prev_b - dmg_b / 1.5)
        hp_pct["b"][target_slot_b] = new_b
        fainted_b = new_b <= 0 or (new_b < 20 and random.random() < 0.15)
        if fainted_b:
            hp_pct["b"][target_slot_b] = 0.0
            faint_counts["b"] += 1
        events.append(gen_turn_damage(
            battle_id, turn, "b", target_b,
            random.choice(MOVE_NAMES), dmg_b, fainted_b,
            player_a, session_a
        ))
        if fainted_b:
            events.append(gen_turn_faint(battle_id, turn, target_b, "b", player_a, session_a))
            # Switch in new mon
            if faint_counts["b"] < 3 and target_slot_b + 1 < 3:
                new_species = team_b[target_slot_b + 1]["speciesID"]
                hp_pct["b"][target_slot_b + 1] = 100.0
                events.append(gen_turn_switch(battle_id, turn + 1, new_species, "b", "faint", player_a, session_a))

        # Damage to side A (from B)
        dmg_a = random.randint(10, 50)
        target_slot_a = min(turn - 1, 2)
        target_a = team_a[target_slot_a]["speciesID"]
        prev_a = hp_pct["a"][target_slot_a]
        new_a = max(0.0, prev_a - dmg_a / 1.5)
        hp_pct["a"][target_slot_a] = new_a
        fainted_a = new_a <= 0 or (new_a < 20 and random.random() < 0.15)
        if fainted_a:
            hp_pct["a"][target_slot_a] = 0.0
            faint_counts["a"] += 1
        events.append(gen_turn_damage(
            battle_id, turn, "a", target_a,
            random.choice(MOVE_NAMES), dmg_a, fainted_a,
            player_b, session_b
        ))
        if fainted_a:
            events.append(gen_turn_faint(battle_id, turn, target_a, "a", player_b, session_b))
            if faint_counts["a"] < 3 and target_slot_a + 1 < 3:
                new_species = team_a[target_slot_a + 1]["speciesID"]
                hp_pct["a"][target_slot_a + 1] = 100.0
                events.append(gen_turn_switch(battle_id, turn + 1, new_species, "a", "faint", player_b, session_b))

        # Occasional heal
        if random.random() < 0.2:
            heal_side = random.choice(["a", "b"])
            heal_slot = random.randint(0, 2)
            team = team_a if heal_side == "a" else team_b
            species = team[heal_slot]["speciesID"]
            heal_amt = random.randint(30, 60)
            hp = hp_pct[heal_side]
            hp[heal_slot] = min(100.0, hp.get(heal_slot, 100.0) + heal_amt / 1.5)
            events.append(gen_turn_heal(
                battle_id, turn, heal_side, species, heal_amt,
                player_a if heal_side == "a" else player_b,
                session_a if heal_side == "a" else session_b
            ))

        # Occasional ability trigger
        if random.random() < 0.15:
            ab_side = random.choice(["a", "b"])
            ab_team = team_a if ab_side == "a" else team_b
            ab_slot = random.randint(0, 2)
            events.append(gen_turn_ability(
                battle_id, turn, ab_team[ab_slot]["speciesID"],
                ab_side, random.choice(ABILITIES),
                player_a if ab_side == "a" else player_b,
                session_a if ab_side == "a" else session_b
            ))

    # battle_result
    alive_a = 3 - faint_counts["a"]
    alive_b = 3 - faint_counts["b"]
    if alive_a > alive_b:
        winner = "a"
    elif alive_b > alive_a:
        winner = "b"
    else:
        winner = random.choice(["a", "b"])

    a_result = "win" if winner == "a" else "loss"
    b_result = "win" if winner == "b" else "loss"

    events.append(gen_battle_result(battle_id, "a", a_result, winner, turns, alive_a, alive_b, player_a, session_a))
    events.append(gen_battle_result(battle_id, "b", b_result, winner, turns, alive_b, alive_a, player_b, session_b))

    return events


# ── Main loop ─────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate battle events (event_new format)")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--turns", type=int, nargs=2, default=[5, 15])
    parser.add_argument("--start-id", type=int, default=100)
    parser.add_argument("--kafka", type=str, default="",
                        help="Kafka broker (e.g. 100.107.105.99:9092) — enables cluster mode")
    parser.add_argument("--topic", type=str, default="battle.logs")
    args = parser.parse_args()

    kafka_producer = None
    if args.kafka:
        try:
            from kafka import KafkaProducer
            kafka_producer = KafkaProducer(
                bootstrap_servers=args.kafka,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
            print(f"[Kafka] {args.kafka} topic={args.topic}")
        except ImportError:
            print("kafka-python not installed. Use file mode instead.")
            args.kafka = ""

    # Generate sessions
    sessions = {p: f"{uuid.uuid4().hex[:4]}" for p in PLAYERS}
    session_events = []
    for p in PLAYERS:
        session_events.append(gen_session(p, sessions[p]))
        for page in PAGES:
            session_events.append(gen_page_view(p, sessions[p], page))

    # Send session events first
    for e in session_events:
        if kafka_producer:
            kafka_producer.send(args.topic, key=e["session_id"], value=e)
        else:
            pass  # session events only to Kafka

    bid = args.start_id
    cycle = 0
    print(f"Generating battles every {args.interval}s ({args.turns[0]}-{args.turns[1]} turns). Ctrl+C to stop.")

    try:
        while True:
            turns = random.randint(*args.turns)
            t0 = time.time()
            battle_id = f"battle_{uuid.uuid4().hex[:4]}"

            pa = random.choice(PLAYERS)
            pb = random.choice([p for p in PLAYERS if p != pa])

            events = gen_battle_events(battle_id, turns, pa, pb, sessions[pa], sessions[pb])
            cycle += 1

            for e in events:
                if kafka_producer:
                    kafka_producer.send(args.topic, key=e["session_id"], value=e)
                else:
                    # Local: append to daily JSONL file
                    log_file = BATTLE_LOGS / f"events_{time.strftime('%Y-%m-%d')}.jsonl"
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(e, ensure_ascii=False) + "\n")

            if kafka_producer:
                kafka_producer.flush()

            elapsed = time.time() - t0
            print(f"  #{bid} | {turns}t | {len(events)} events | {elapsed*1000:.0f}ms")
            bid += 1

            sleep_time = args.interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    except KeyboardInterrupt:
        n = bid - args.start_id
        print(f"\nDone. {n} battles, {n * 30}+ events generated.")
        if kafka_producer:
            kafka_producer.close()


if __name__ == "__main__":
    main()
