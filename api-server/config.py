"""
PokemonSimulator API Server Configuration (Person A)

所有环境变量集中管理，支持 Docker 和物理机部署。
大数据组件（Kafka/HDFS/Spark/Redis）地址指向外部物理机集群。
"""
import os

# ============================================================
# Server
# ============================================================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# ============================================================
# Kafka (外部物理机集群, Person C)
# ============================================================
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "100.107.105.99:9092,<node2-ip>:9092,<node3-ip>:9092")

KAFKA_TOPIC_REQUESTS = os.getenv("KAFKA_TOPIC_REQUESTS", "battle.requests")
KAFKA_TOPIC_RESULTS = os.getenv("KAFKA_TOPIC_RESULTS", "battle.results")
KAFKA_TOPIC_EVENTS = os.getenv("KAFKA_TOPIC_EVENTS", "battle.events")
KAFKA_TOPIC_ANALYTICS = os.getenv("KAFKA_TOPIC_ANALYTICS", "battle.analytics")

KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "api-server-group")

# ============================================================
# PostgreSQL (Docker, Node3)
# ============================================================
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "pokemon")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "pokemon123")
POSTGRES_DB = os.getenv("POSTGRES_DB", "pokemon_simulator")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# ============================================================
# HDFS (WebHDFS, 外部物理机集群, Person B)
# ============================================================
HDFS_NAMENODE = os.getenv("HDFS_NAMENODE", "100.107.105.99")
HDFS_PORT = int(os.getenv("HDFS_PORT", "9870"))
HDFS_USER = os.getenv("HDFS_USER", "root")
HDFS_BASE_PATH = os.getenv("HDFS_BASE_PATH", "/user/pokemon")

# ============================================================
# Redis (外部物理机集群, Person C)
# ============================================================
REDIS_URL = os.getenv("REDIS_URL", "redis://100.107.105.99:6379/0")
REDIS_SENTINEL = os.getenv("REDIS_SENTINEL", "")  # Sentinel 地址，可选

# ============================================================
# Spark Master (外部物理机集群, Person B)
# ============================================================
SPARK_MASTER_URL = os.getenv("SPARK_MASTER_URL", "spark://100.107.105.99:7077")
SPARK_REST_URL = os.getenv("SPARK_REST_URL", "http://100.107.105.99:6066")

# ============================================================
# C++ Battle Engine
# ============================================================
ENGINE_BINARY = os.getenv("ENGINE_BINARY", "./build/PokemonSimulator")
ENGINE_CACHE_DIR = os.getenv("ENGINE_CACHE_DIR", "/tmp/pokemon-engine")
ENGINE_TIMEOUT = int(os.getenv("ENGINE_TIMEOUT", "30"))  # seconds per turn
