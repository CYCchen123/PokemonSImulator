"""
PySpark Batch: Consume frontend events from Kafka, analyze, write to static DBs.

Maps event types to existing table schemas:
  session_start / matchmaking_join → pokemon.db / users
  team_save                       → pokemon.db / user_teams
  battle_start / battle_end       → output.db / battles
  turn_action / damage_dealt      → output.db / battle_turns
  faint / switch_in               → output.db / battle_pokemon_states

Usage (on VM cluster):
  spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \\
      analytics_events.py [--broker 100.107.105.99:9092] [--pokemon-db /path/to/pokemon.db] [--output-db /path/to/output.db]
"""
import json, argparse, sqlite3, sys
from pathlib import Path
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, window, count, sum as spark_sum, lit, expr
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, BooleanType, MapType
)
from pyspark.sql import Row


# No strict schema — parse JSON string in writer


def write_users(df_rows, db_path: str):
    """Insert/update users table in pokemon.db."""
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, created_at TEXT)")
    for row in df_rows:
        username = row.get("player_id", "") or ""
        ts = row.get("timestamp", "") or datetime.utcnow().isoformat()
        if username:
            conn.execute(
                "INSERT OR IGNORE INTO users (username, created_at) VALUES (?, ?)",
                (username, ts)
            )
    conn.commit()
    conn.close()
    return len(df_rows)


def write_user_teams(df_rows, db_path: str):
    """Insert team saves into user_teams table."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT, team_name TEXT, team_json TEXT,
            created_at TEXT, updated_at TEXT
        )
    """)
    count = 0
    for row in df_rows:
        username = row.get("player_id", "")
        team_name = row.get("team_name", "")
        team_json = json.dumps(row, ensure_ascii=False)
        ts = row.get("timestamp", datetime.utcnow().isoformat())
        if username and team_name:
            conn.execute(
                "INSERT OR REPLACE INTO user_teams (username, team_name, team_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (username, team_name, team_json, ts, ts)
            )
            count += 1
    conn.commit()
    conn.close()
    return count


def write_battle_events(df_rows, db_path: str):
    """Write battle_start/battle_end into a battles summary."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS battles (
            battle_id TEXT PRIMARY KEY,
            side TEXT,
            player_id TEXT,
            session_id TEXT,
            event_type TEXT,
            result TEXT,
            team_size INTEGER,
            timestamp TEXT
        )
    """)
    count = 0
    for row in df_rows:
        battle_id = row.get("battle_id", "")
        if battle_id:
            event_type = row.get("event", "")
            conn.execute(
                "INSERT OR REPLACE INTO battles (battle_id, side, player_id, session_id, event_type, result, team_size, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (battle_id, row.get("side", ""), row.get("player_id", ""),
                 row.get("session_id", ""), event_type,
                 row.get("result", ""), row.get("team_size", 0),
                 row.get("timestamp", ""))
            )
            count += 1
    conn.commit()
    conn.close()
    return count


def write_battle_states(df_rows, db_path: str):
    """Write faint/switch_in events into battle_pokemon_states."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS battle_pokemon_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            battle_id TEXT NOT NULL, turn INTEGER DEFAULT 0,
            side_index INTEGER DEFAULT 0, pokemon_index INTEGER DEFAULT 0,
            species_id INTEGER DEFAULT 0, hp INTEGER DEFAULT 0, max_hp INTEGER DEFAULT 0,
            hp_pct REAL DEFAULT 0.0, fainted INTEGER DEFAULT 0,
            ability_id INTEGER DEFAULT 0, item_id INTEGER DEFAULT 0,
            move_ids TEXT DEFAULT '[]', slot INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    count = 0
    for row in df_rows:
        battle_id = row.get("battle_id", "")
        species_id = int(row.get("pokemon", 0) or 0)
        if battle_id and species_id:
            turn = int(row.get("turn", 0) or 0)
            side_char = row.get("side", "a")
            side_index = 0 if side_char == "a" else 1
            fainted_val = 1 if row.get("event", "") == "faint" else 0
            conn.execute(
                """INSERT OR IGNORE INTO battle_pokemon_states
                   (battle_id, turn, side_index, pokemon_index, species_id, fainted, created_at)
                   VALUES (?, ?, ?, 0, ?, ?, datetime('now'))""",
                (battle_id, turn, side_index, species_id, fainted_val)
            )
            count += 1
    conn.commit()
    conn.close()
    return count


def write_battle_init_teams(df_rows, db_path: str):
    """Write battle_init events: extract full team (species, moves, items, abilities)."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS battle_pokemon_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            battle_id TEXT NOT NULL, turn INTEGER DEFAULT 0,
            side_index INTEGER DEFAULT 0, pokemon_index INTEGER DEFAULT 0,
            species_id INTEGER DEFAULT 0, hp INTEGER DEFAULT 0, max_hp INTEGER DEFAULT 100,
            hp_pct REAL DEFAULT 100.0, fainted INTEGER DEFAULT 0,
            ability_id INTEGER DEFAULT 0, item_id INTEGER DEFAULT 0,
            move_ids TEXT DEFAULT '[]', slot INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    count = 0
    for row in df_rows:
        d = row.get("data", {})
        bid = d.get("battle_id", "")
        if not bid:
            continue
        for side_key in ("a", "b"):
            side_index = 0 if side_key == "a" else 1
            team = d.get(f"side_{side_key}", [])
            for slot, mon in enumerate(team):
                species_id = mon.get("speciesID", 0) if isinstance(mon, dict) else 0
                if not species_id:
                    continue
                ability_id = mon.get("ability", 0) if isinstance(mon, dict) else 0
                item_id = mon.get("item", 0) if isinstance(mon, dict) else 0
                moves = json.dumps(mon.get("moves", [])) if isinstance(mon, dict) else "[]"
                conn.execute(
                    "INSERT OR IGNORE INTO battle_pokemon_states (battle_id, turn, side_index, pokemon_index, species_id, hp, max_hp, hp_pct, fainted, ability_id, item_id, move_ids, slot) VALUES (?,0,?,?,?,100,100,100.0,0,?,?,?,?)",
                    (bid, side_index, slot, species_id, ability_id, item_id, moves, slot))
                count += 1
    conn.commit()
    conn.close()
    return count


def write_battle_results(df_rows, db_path: str):
    """Write battle_result events into battles table."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS battles (
            battle_id TEXT, side TEXT, player_id TEXT, session_id TEXT,
            event_type TEXT, result TEXT, winner TEXT, turns INTEGER,
            own_remaining INTEGER, opp_remaining INTEGER, timestamp TEXT
        )
    """)
    count = 0
    for row in df_rows:
        d = row.get("data", {})
        bid = d.get("battle_id", "")
        winner = d.get("winner", "")
        if bid:
            conn.execute(
                "INSERT INTO battles VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (bid, d.get("side",""), row.get("player_id",""), row.get("session_id",""),
                 "battle_result", d.get("result",""), winner,
                 d.get("turns",0), d.get("own_remaining",0), d.get("opp_remaining",0),
                 row.get("timestamp","")))
            count += 1
            # Mark losing side as fainted
            if winner in ("a", "b"):
                loser_idx = 1 if winner == "a" else 0
                conn.execute(
                    "UPDATE battle_pokemon_states SET fainted=1, hp_pct=0.0 WHERE battle_id=? AND side_index=?",
                    (bid, loser_idx))
    conn.commit()
    conn.close()
    return count


EVENT_WRITERS = {
    ("session_start", "users"):        write_users,
    ("team_save", "user_teams"):       write_user_teams,
    ("battle_init", "battle_states"):  write_battle_init_teams,
    ("battle_result", "battles"):      write_battle_results,
}


def _parse_rows(df):
    """Convert Spark rows (json_str) to Python dicts."""
    import json
    result = []
    for r in df.collect():
        try:
            result.append(json.loads(r.json_str))
        except:
            pass
    return result


def process_batch(df, epoch_id, pokemon_db: str, output_db: str):
    """Process one microbatch."""
    rows = _parse_rows(df)
    if not rows:
        return
    print(f"\n=== Batch {epoch_id}: {len(rows)} events ===")
    for (event_type, target), writer in EVENT_WRITERS.items():
        subset = [r for r in rows if r.get("event") == event_type]
        if subset:
            db = pokemon_db if target in ("users", "user_teams") else output_db
            n = writer(subset, db)
            print(f"  {event_type} → {target}: {n} rows")
    from collections import Counter
    print(f"  Distribution: {dict(Counter(r.get('event','?') for r in rows))}")


def main():
    parser = argparse.ArgumentParser(description="PySpark frontend event processor")
    parser.add_argument("--broker", default="100.107.105.99:9092")
    parser.add_argument("--topic", default="battle.logs")
    parser.add_argument("--pokemon-db", default="/home/hadoop/pokemon.db")
    parser.add_argument("--output-db", default="/home/hadoop/output.db")
    parser.add_argument("--batch", action="store_true", help="Batch mode: read all, not streaming")
    args = parser.parse_args()

    spark = SparkSession.builder \
        .appName("PokemonSimulator-EventAnalytics") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()

    kafka_opts = {"kafka.bootstrap.servers": args.broker, "subscribe": args.topic}
    if args.batch:
        df = spark.read.format("kafka").options(**kafka_opts) \
            .option("startingOffsets", "earliest").option("endingOffsets", "latest") \
            .load().selectExpr("CAST(value AS STRING) as json_str")
    else:
        df = spark.readStream.format("kafka").options(**kafka_opts) \
            .option("startingOffsets", "latest").load() \
            .selectExpr("CAST(value AS STRING) as json_str")

    print(f"Broker: {args.broker}, Topic: {args.topic}")
    print(f"Pokemon DB: {args.pokemon_db}, Output DB: {args.output_db}")
    print(f"Mode: {'batch' if args.batch else 'streaming'}")

    if args.batch:
        rows = _parse_rows(df)
        print(f"Fetched {len(rows)} events")
        for (event_type, target), writer in EVENT_WRITERS.items():
            subset = [r for r in rows if r.get("event") == event_type]
            if subset:
                db = args.pokemon_db if target in ("users", "user_teams") else args.output_db
                n = writer(subset, db)
                print(f"  {event_type} → {target}: {n} rows")
        from collections import Counter
        print(f"Distribution: {dict(Counter(r.get('event','?') for r in rows))}")
        print("Done.")
    else:
        streaming_query = df.writeStream \
            .foreachBatch(lambda df, eid: process_batch(df, eid, args.pokemon_db, args.output_db)) \
            .outputMode("append") \
            .start()
        streaming_query.awaitTermination()


if __name__ == "__main__":
    main()
