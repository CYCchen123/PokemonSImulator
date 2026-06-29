"""
Bridge Service: Kafka <-> C++ Battle Engine

Consumes battle.requests from Kafka, calls the C++ PokemonSimulator
binary via subprocess, produces results to battle.results and
battle.events topics.

This runs as a background process alongside the API server.
"""
import json
import os
import logging
import subprocess
import tempfile
import time
from pathlib import Path
from kafka import KafkaConsumer, KafkaProducer

from config import (
    KAFKA_BROKER, KAFKA_TOPIC_REQUESTS, KAFKA_TOPIC_RESULTS,
    KAFKA_TOPIC_EVENTS, ENGINE_BINARY, ENGINE_CACHE_DIR,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [bridge] %(levelname)s: %(message)s'
)
logger = logging.getLogger("bridge-service")

# ============================================================
# Battle session management
# ============================================================
# In-memory store of active battle sessions.
# Key: battle_id, Value: dict with session state
_active_battles: dict = {}


class BattleSession:
    """Manages a single battle via C++ engine subprocess calls."""

    def __init__(self, battle_id: str, init_json: dict):
        self.battle_id = battle_id
        self.init_json = init_json
        self.turn_number = 0
        self.work_dir = Path(ENGINE_CACHE_DIR) / battle_id
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Write init files
        side_a = init_json.get("side_a", {})
        side_b = init_json.get("side_b", {})
        seed = init_json.get("seed", 0)

        with open(self.work_dir / "cache/input/side_a.json", "w") as f:
            json.dump(side_a, f)
        with open(self.work_dir / "cache/input/side_b.json", "w") as f:
            json.dump(side_b, f)

        # Create init_request.json for batch mode
        init_request = {
            "side_a": side_a,
            "side_b": side_b,
            "seed": seed,
        }
        (self.work_dir / "cache/input").mkdir(parents=True, exist_ok=True)
        with open(self.work_dir / "cache/input/init_request.json", "w") as f:
            json.dump(init_request, f)

        logger.info(f"Session created for {battle_id} at {self.work_dir}")

    def process_turn(self, actions: list[dict]) -> dict | None:
        """Process a turn with the given actions. Returns the result JSON."""
        self.turn_number += 1
        turn = self.turn_number

        # Write turn input files (1_input_N.json, 2_input_N.json)
        input_dir = self.work_dir / "cache/input"
        input_dir.mkdir(parents=True, exist_ok=True)

        for action in actions:
            side = action.get("side", "").lower()
            side_prefix = "1" if side in ("a", "side_a") else "2"
            turn_file = input_dir / f"{side_prefix}_input_{turn}.json"
            with open(turn_file, "w") as f:
                json.dump(action, f)

        # Call C++ engine
        try:
            cmd = [
                ENGINE_BINARY,
                "--run-cache-input",
            ]
            result = subprocess.run(
                cmd,
                cwd=str(self.work_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.error(f"Engine error for {self.battle_id}: {result.stderr[:500]}")
                return {"ok": False, "error": result.stderr[:500]}

            # Read output
            output_dir = self.work_dir / "cache/output"
            output_files = sorted(output_dir.glob(f"output_{turn}.json"))
            if not output_files:
                # Try without turn number
                output_files = sorted(output_dir.glob("output_*.json"))

            if output_files:
                with open(output_files[-1]) as f:
                    return json.load(f)
            else:
                # Parse stdout directly
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    logger.error(f"No output file found and stdout is not JSON")
                    return {"ok": False, "error": "No output from engine"}

        except subprocess.TimeoutExpired:
            logger.error(f"Engine timeout for {self.battle_id}")
            return {"ok": False, "error": "Engine timeout"}
        except Exception as e:
            logger.error(f"Engine exception for {self.battle_id}: {e}")
            return {"ok": False, "error": str(e)}

    def cleanup(self):
        """Remove temporary files."""
        import shutil
        try:
            if self.work_dir.exists():
                shutil.rmtree(self.work_dir)
            logger.info(f"Cleaned up session for {self.battle_id}")
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")


# ============================================================
# Kafka Bridge Loop
# ============================================================

def run_bridge():
    """Main bridge loop: consume battle requests, call engine, produce results."""

    # Producer for results and events
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None,
        acks='all',
    )

    # Consumer for requests
    consumer = KafkaConsumer(
        KAFKA_TOPIC_REQUESTS,
        bootstrap_servers=KAFKA_BROKER,
        group_id="battle-engine-bridge",
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        key_deserializer=lambda k: k.decode('utf-8') if k else None,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
    )

    logger.info(f"Bridge service started, consuming from {KAFKA_TOPIC_REQUESTS}")

    for message in consumer:
        try:
            data = message.value
            battle_id = data.get("battle_id", "")
            req_type = data.get("type", "")
            payload = data.get("payload", {})

            logger.info(f"Processing {req_type} for {battle_id}")

            if req_type == "create":
                # Create new battle session
                session = BattleSession(battle_id, payload)
                _active_battles[battle_id] = session

                # Process turn 0 (initial send out)
                # For create, we just send the init confirmation
                result = {
                    "battle_id": battle_id,
                    "turn": 0,
                    "ok": True,
                    "state": {
                        "sides": [
                            {"name": payload.get("side_a", {}).get("name", "Side A"),
                             "pokemons": payload.get("side_a", {}).get("pokemon", [])},
                            {"name": payload.get("side_b", {}).get("name", "Side B"),
                             "pokemons": payload.get("side_b", {}).get("pokemon", [])},
                        ]
                    },
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                producer.send(KAFKA_TOPIC_RESULTS, key=battle_id, value=result)

            elif req_type == "turn":
                session = _active_battles.get(battle_id)
                if not session:
                    # Reconstruct session from stored init data
                    logger.warning(f"No active session for {battle_id}, skipping")
                    continue

                actions = payload.get("actions", [])
                turn_result = session.process_turn(actions)

                if turn_result and turn_result.get("ok"):
                    # Extract events
                    events = turn_result.get("events", [])
                    descriptions = turn_result.get("descriptions", [])

                    # Send result
                    result_msg = {
                        "battle_id": battle_id,
                        "turn": session.turn_number,
                        "ok": True,
                        "state": turn_result,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                    producer.send(KAFKA_TOPIC_RESULTS, key=battle_id, value=result_msg)

                    # Send individual events
                    for i, event in enumerate(events):
                        event_msg = {
                            "battle_id": battle_id,
                            "turn": session.turn_number,
                            "timeline_index": i,
                            "event_type": event.get("event_type", "unknown"),
                            "description": event.get("description", descriptions[i] if i < len(descriptions) else ""),
                            "details": event.get("details", {}),
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        }
                        producer.send(KAFKA_TOPIC_EVENTS, key=battle_id, value=event_msg)

                    producer.flush(timeout=5)

                    # Check if battle is over
                    battle_state = turn_result.get("battle", turn_result)
                    sides = battle_state.get("sides", [])
                    for side in sides:
                        pokemons = side.get("pokemons", [])
                        if pokemons and all(p.get("fainted", False) for p in pokemons):
                            # Game over
                            game_over_msg = {
                                "battle_id": battle_id,
                                "turn": session.turn_number,
                                "ok": True,
                                "game_over": True,
                                "winner": "Side B" if side.get("side") == 0 or "Side A" in side.get("name", "") else "Side A",
                                "state": turn_result,
                                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            }
                            producer.send(KAFKA_TOPIC_RESULTS, key=battle_id, value=game_over_msg)
                            producer.flush(timeout=5)
                            session.cleanup()
                            del _active_battles[battle_id]
                            logger.info(f"Battle {battle_id} ended")
                            break
                else:
                    # Error response
                    error_msg = {
                        "battle_id": battle_id,
                        "turn": session.turn_number,
                        "ok": False,
                        "error": turn_result.get("error", "Unknown error") if turn_result else "No result",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                    producer.send(KAFKA_TOPIC_RESULTS, key=battle_id, value=error_msg)

        except Exception as e:
            logger.error(f"Bridge error: {e}", exc_info=True)


if __name__ == "__main__":
    logger.info("PokemonSimulator Bridge Service starting...")
    logger.info(f"Engine binary: {ENGINE_BINARY}")
    logger.info(f"Kafka broker: {KAFKA_BROKER}")
    logger.info(f"Cache directory: {ENGINE_CACHE_DIR}")

    # Ensure cache directory exists
    Path(ENGINE_CACHE_DIR).mkdir(parents=True, exist_ok=True)

    run_bridge()
