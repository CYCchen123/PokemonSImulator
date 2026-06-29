"""
Kafka producer and consumer for PokemonSimulator.
"""
import json
import logging
import threading
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from config import (
    KAFKA_BROKER, KAFKA_TOPIC_REQUESTS, KAFKA_TOPIC_RESULTS,
    KAFKA_TOPIC_EVENTS, KAFKA_CONSUMER_GROUP
)

logger = logging.getLogger(__name__)

# ============================================================
# Producer (send battle requests)
# ============================================================

_producer: KafkaProducer | None = None


def get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=1,
        )
        logger.info(f"Kafka producer connected to {KAFKA_BROKER}")
    return _producer


def send_battle_request(battle_id: str, request_type: str, payload: dict) -> bool:
    """Send a battle request to Kafka. Returns True on success."""
    try:
        producer = get_producer()
        message = {
            "battle_id": battle_id,
            "type": request_type,
            "payload": payload,
        }
        future = producer.send(
            KAFKA_TOPIC_REQUESTS,
            key=battle_id,
            value=message,
        )
        future.get(timeout=10)
        logger.info(f"Sent battle.{request_type} for {battle_id}")
        return True
    except KafkaError as e:
        logger.error(f"Failed to send battle request: {e}")
        return False


def send_battle_event(battle_id: str, events: list[dict]) -> bool:
    """Send battle events to Kafka."""
    try:
        producer = get_producer()
        for event in events:
            producer.send(
                KAFKA_TOPIC_EVENTS,
                key=battle_id,
                value=event,
            )
        producer.flush(timeout=5)
        return True
    except KafkaError as e:
        logger.error(f"Failed to send battle events: {e}")
        return False


# ============================================================
# Consumer (receive battle results)
# ============================================================

_results_handlers: list[callable] = []


def on_battle_result(handler: callable):
    """Register a callback for battle results.
    handler(battle_id, result_data) -> None
    """
    _results_handlers.append(handler)


def _consume_results():
    """Background thread: consume battle.results and invoke handlers."""
    consumer = KafkaConsumer(
        KAFKA_TOPIC_RESULTS,
        bootstrap_servers=KAFKA_BROKER,
        group_id=KAFKA_CONSUMER_GROUP,
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        key_deserializer=lambda k: k.decode('utf-8') if k else None,
        auto_offset_reset='latest',
        enable_auto_commit=True,
    )
    logger.info(f"Kafka consumer started on {KAFKA_TOPIC_RESULTS}")

    for message in consumer:
        try:
            data = message.value
            battle_id = data.get("battle_id", "")
            for handler in _results_handlers:
                try:
                    handler(battle_id, data)
                except Exception as e:
                    logger.error(f"Handler error for {battle_id}: {e}")
        except Exception as e:
            logger.error(f"Consumer error: {e}")


def start_consumer():
    """Start the Kafka consumer in a background thread."""
    thread = threading.Thread(target=_consume_results, daemon=True, name="kafka-consumer")
    thread.start()
    logger.info("Kafka consumer thread started")
