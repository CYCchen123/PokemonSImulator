#!/bin/bash
set -e
KAFKA=100.107.105.99:9092
SPARK_HOME=${SPARK_HOME:-/opt/bigdata/spark}
LOG=/tmp

echo "╔══════════════════════════════════════╗"
echo "║  PokemonSimulator VM Cluster        ║"
echo "╚══════════════════════════════════════╝"

# Kill old
pkill -f standalone_server 2>/dev/null || true
pkill -f gen_battle_stream 2>/dev/null || true
pkill -f SparkSubmit 2>/dev/null || true
sleep 2

# 1. Kafka
echo "[1/4] Kafka..."
nc -z 100.107.105.99 9092 && echo "  OK" || { echo "  DEAD"; exit 1; }

# 2. DB
echo "[2/4] Database..."
mkdir -p ~/data
python3 -c "
import sqlite3,os
db=sqlite3.connect(os.path.expanduser('~/data/output.db'))
db.execute('CREATE TABLE IF NOT EXISTS battle_pokemon_states(id INTEGER PRIMARY KEY AUTOINCREMENT,battle_id TEXT,turn INTEGER DEFAULT 0,side_index INTEGER DEFAULT 0,pokemon_index INTEGER DEFAULT 0,species_id INTEGER,hp INTEGER DEFAULT 0,max_hp INTEGER DEFAULT 100,hp_pct REAL DEFAULT 100.0,fainted INTEGER DEFAULT 0,ability_id INTEGER DEFAULT 0,item_id INTEGER DEFAULT 0,move_ids TEXT DEFAULT \"[]\",slot INTEGER DEFAULT 0,created_at TEXT)')
db.commit();db.close()
print('  OK')
"

# 3. API
echo "[3/4] API..."
cd ~/api-server
export POKEMON_MODE=cluster KAFKA_BROKER=$KAFKA
nohup python3 standalone_server.py > $LOG/api.log 2>&1 &
sleep 3
curl -s http://localhost:8000/api/v1/stats/deep/summary
echo ""

# 4. Spark + Gen
echo "[4/4] Spark..."
nohup $SPARK_HOME/bin/spark-submit --master spark://myz:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 ~/analytics_events.py --broker $KAFKA --pokemon-db ~/pokemon.db --output-db ~/data/output.db > $LOG/spark.log 2>&1 &
sleep 2

echo ""
echo "=== Running ==="
echo "API: http://192.168.209.137:8000"
echo "Logs: $LOG/{api,spark,gen}.log"
echo ""
echo "Stop:  pkill -f standalone_server; pkill -f gen_battle_stream; pkill -f SparkSubmit"
