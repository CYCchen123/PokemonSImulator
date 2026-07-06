import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODE = os.environ.get("POKEMON_MODE", "local")

LOCAL_DB_OUTPUT = PROJECT_ROOT / "data" / "output.db"
LOCAL_DB_RECENT = PROJECT_ROOT / "data" / "output_recent.db"
LOCAL_DB_POKEMON = PROJECT_ROOT / "data" / "pokemon.db"

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "100.107.105.99:9092")

ENABLE_WATCHER = (MODE == "local") or (os.environ.get("POKEMON_MASTER", "").lower() == "true")
def is_cluster(): return MODE == "cluster"
