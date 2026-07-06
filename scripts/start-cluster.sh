#!/bin/bash
# ===========================================
#  PokemonSimulator — VM Cluster Startup
#  Run on one VM node (e.g. cyc or myz)
# ===========================================

set -e

# ── Config ──
KAFKA_BROKER="100.107.105.99:9092"
SPARK_HOME="${SPARK_HOME:-/opt/bigdata/spark}"
SPARK_MASTER="${SPARK_MASTER:-spark://cyc:7077}"   # adjust to your master
API_DIR="${API_DIR:-$HOME/api-server}"
POKEMON_DB="${POKEMON_DB:-$HOME/pokemon.db}"
OUTPUT_DB="${OUTPUT_DB:-$HOME/output.db}"
API_PORT="${API_PORT:-8000}"

echo "========================================"
echo "  PokemonSimulator Cluster Startup"
echo "========================================"
echo "  Kafka   → $KAFKA_BROKER"
echo "  Spark   → $SPARK_HOME ($SPARK_MASTER)"
echo "  DB      → $POKEMON_DB / $OUTPUT_DB"
echo "  API     → 0.0.0.0:$API_PORT"
echo "========================================"

# ── 1. Check requirements ──
for req in python3 java nc; do
  command -v $req >/dev/null 2>&1 || { echo "[FAIL] $req not found"; exit 1; }
done

# ── 2. Verify Kafka reachable ──
echo "[1/3] Checking Kafka..."
if nc -z -w3 $(echo $KAFKA_BROKER | sed 's/:/ /') 2>/dev/null; then
  echo "       Kafka OK ($KAFKA_BROKER)"
else
  echo "       [WARN] Kafka unreachable, retrying..."
fi

# ── 3. Start Spark streaming consumer (background) ──
echo "[2/3] Starting Spark streaming..."
SPARK_JOB="$HOME/analytics_events.py"
if [ -f "$SPARK_JOB" ]; then
  POKEMON_MODE=cluster nohup \
    $SPARK_HOME/bin/spark-submit \
      --master $SPARK_MASTER \
      --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
      $SPARK_JOB \
      --broker $KAFKA_BROKER \
      --pokemon-db $POKEMON_DB \
      --output-db $OUTPUT_DB \
      > /tmp/spark-analytics.log 2>&1 &
  echo "       Spark pid=$! (log: /tmp/spark-analytics.log)"
else
  echo "       [SKIP] $SPARK_JOB not found — upload analytics_events.py first"
fi

# ── 4. Start API server ──
echo "[3/3] Starting API server..."
if [ -d "$API_DIR" ]; then
  export POKEMON_MODE=cluster
  export KAFKA_BROKER=$KAFKA_BROKER
  cd $API_DIR
  nohup python3 standalone_server.py > /tmp/api-server.log 2>&1 &
  cd -
  echo "       API pid=$! (log: /tmp/api-server.log)"
  echo "       http://$(hostname -I | awk '{print $1}'):$API_PORT"
else
  echo "       [SKIP] $API_DIR not found — copy api-server/ first"
fi

echo ""
echo "========================================"
echo "  Cluster startup complete."
echo "  Check:"
echo "    tail -f /tmp/api-server.log"
echo "    tail -f /tmp/spark-analytics.log"
echo "========================================"
