#!/bin/bash
# ============================================
# 完全重置：清 Kafka + 清 DB + 重启集群
# 在 cyc 上运行
# ============================================

KAFKA_IP=100.107.105.99
KAFKA_PORT=9092
TOPIC=battle.logs
MYZ="hadoop@myz"

echo "╔══════════════════════════════════════╗"
echo "║  Full Reset — Clear Everything      ║"
echo "╚══════════════════════════════════════╝"

# ── 1. Stop all ──
echo "[1/5] Stopping all..."
pkill -f SparkSubmit 2>/dev/null || true
pkill -f gen_battle_stream 2>/dev/null || true
pkill -f standalone_server 2>/dev/null || true
sleep 2

# ── 2. Clear DB ──
echo "[2/5] Clearing DB..."
BEFORE=$(python3 -c "import sqlite3;db=sqlite3.connect('/home/hadoop/data/output.db');print(db.execute('SELECT COUNT(*) FROM battle_pokemon_states').fetchone()[0])")
python3 -c "import sqlite3;db=sqlite3.connect('/home/hadoop/data/output.db');db.execute('DELETE FROM battle_pokemon_states');db.commit();print(f'  Deleted {db.total_changes} rows (was {db.execute(\"SELECT COUNT(*) FROM battle_pokemon_states\").fetchone()[0]+db.total_changes})')"
echo "  Before: $BEFORE rows → Now: 0"

# ── 3. Clear Kafka (set 1s retention, wait, restore) ──
echo "[3/5] Clearing Kafka topic ($TOPIC)..."
ssh $MYZ "/opt/bigdata/kafka/bin/kafka-configs.sh --bootstrap-server ${KAFKA_IP}:${KAFKA_PORT} --entity-type topics --entity-name $TOPIC --alter --add-config retention.ms=1000,segment.ms=1000" 2>&1 | grep -v "^$\|WARNING"
echo "  Waiting 20s for Kafka cleanup..."
sleep 20
ssh $MYZ "/opt/bigdata/kafka/bin/kafka-configs.sh --bootstrap-server ${KAFKA_IP}:${KAFKA_PORT} --entity-type topics --entity-name $TOPIC --alter --add-config retention.ms=604800000,segment.ms=604800000" 2>&1 | grep -v "^$\|WARNING"
echo "  Kafka cleared"

# ── 4. Clear Spark checkpoints ──
echo "[4/5] Clearing Spark checkpoints..."
rm -rf /tmp/spark-* /tmp/checkpoint* ~/checkpoint* ~/.ivy2/cache 2>/dev/null
echo "  Done"

# ── 5. Restart ──
echo "[5/5] Restarting cluster..."
~/start.sh
