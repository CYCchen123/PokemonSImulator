#!/usr/bin/env python3
"""
Read frontend events JSONL, clean/normalize, send to Kafka.

Usage:
    python scripts/events_to_kafka.py events_2026-07-06.jsonl [--broker 100.107.105.99:9092]
"""
import json, sys, argparse
from pathlib import Path
from datetime import datetime

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "api-server"))


def clean_event(raw: dict) -> dict | None:
    """Normalize an event record. Returns None if invalid."""
    event_type = raw.get("event", "").strip()
    if not event_type:
        return None

    cleaned = {
        "event": event_type,
        "session_id": raw.get("session_id", ""),
        "player_id": raw.get("player_id", ""),
        "timestamp": raw.get("timestamp", ""),
        "data": raw.get("data", {}),
    }

    # ── Per-type validation ──
    if event_type == "session_start":
        cleaned["data"]["player_id"] = cleaned["data"].get("player_id", cleaned["player_id"])

    elif event_type == "page_view":
        if "page" not in cleaned["data"]:
            return None

    elif event_type == "team_save":
        cleaned["data"].setdefault("team_name", "")
        cleaned["data"].setdefault("pokemon_count", 0)

    elif event_type == "matchmaking_join":
        cleaned["data"].setdefault("opponent_type", "bot")

    elif event_type in ("battle_start", "battle_end"):
        cleaned["data"].setdefault("battle_id", "")
        cleaned["data"].setdefault("side", "")
        if event_type == "battle_start":
            cleaned["data"].setdefault("team_size", 0)
        else:
            cleaned["data"].setdefault("result", "unknown")

    elif event_type == "turn_action":
        cleaned["data"].setdefault("battle_id", "")
        cleaned["data"].setdefault("turn", 0)
        if "action" not in cleaned["data"]:
            cleaned["data"]["action"] = {}

    elif event_type == "damage_dealt":
        cleaned["data"].setdefault("battle_id", "")
        cleaned["data"].setdefault("turn", 0)
        cleaned["data"].setdefault("damage", 0)
        cleaned["data"].setdefault("fainted", False)

    elif event_type == "faint":
        cleaned["data"].setdefault("battle_id", "")
        cleaned["data"].setdefault("turn", 0)
        cleaned["data"].setdefault("pokemon", 0)
        cleaned["data"].setdefault("side", "")

    elif event_type == "switch_in":
        cleaned["data"].setdefault("battle_id", "")
        cleaned["data"].setdefault("turn", 0)
        cleaned["data"].setdefault("pokemon", 0)
        cleaned["data"].setdefault("side", "")
        cleaned["data"].setdefault("reason", "manual")

    return cleaned


def produce(filepath: str, broker: str, topic: str = "battle.events", delay: float = 0.1):
    """Read JSONL, clean, and send to Kafka."""
    try:
        from kafka import KafkaProducer
    except ImportError:
        print("kafka-python not installed. Run: pip install kafka-python")
        sys.exit(1)

    producer = KafkaProducer(
        bootstrap_servers=broker,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    total, sent, skipped = 0, 0, 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        total += 1
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"  [SKIP] line {total}: bad JSON ({e})")
            skipped += 1
            continue

        cleaned = clean_event(raw)
        if cleaned is None:
            print(f"  [SKIP] line {total}: invalid event")
            skipped += 1
            continue

        # Key by session_id for partitioning
        key = cleaned["session_id"] or cleaned["player_id"] or ""
        producer.send(topic, key=key, value=cleaned)
        sent += 1

        if delay > 0:
            import time
            time.sleep(delay)

    producer.flush()
    producer.close()
    print(f"\nDone: {total} lines → {sent} sent, {skipped} skipped → topic '{topic}' @ {broker}")


def main():
    parser = argparse.ArgumentParser(description="Send cleaned frontend events to Kafka")
    parser.add_argument("input", help="Path to JSONL file")
    parser.add_argument("--broker", default="100.107.105.99:9092", help="Kafka bootstrap server")
    parser.add_argument("--topic", default="battle.events", help="Kafka topic")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between messages (seconds)")
    parser.add_argument("--dry-run", action="store_true", help="Print cleaned events without sending")
    args = parser.parse_args()

    if args.dry_run:
        with open(args.input, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if not line.strip():
                    continue
                raw = json.loads(line)
                cleaned = clean_event(raw)
                print(f"[{i}] {json.dumps(cleaned, ensure_ascii=False)}")
        return

    produce(args.input, args.broker, args.topic, args.delay)


if __name__ == "__main__":
    main()
