#!/bin/bash
# Initialize Kafka topics for PokemonSimulator
# Runs once when docker compose starts

BROKER="kafka:9092"
RETENTION_7D=604800000     # 7 days in ms
RETENTION_30D=2592000000   # 30 days in ms
RETENTION_INF=-1           # infinite retention

echo "================================================"
echo "PokemonSimulator Kafka Topic Initialization"
echo "Broker: $BROKER"
echo "================================================"

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
until kafka-broker-api-versions --bootstrap-server $BROKER > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: Kafka not ready after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "  Attempt $RETRY_COUNT/$MAX_RETRIES..."
    sleep 3
done
echo "Kafka is ready."

# -----------------------------------------------
# Topic 1: battle.requests
# 对战请求流 (创建对战, 处理回合)
# -----------------------------------------------
echo ""
echo "Creating topic: battle.requests"
kafka-topics --bootstrap-server $BROKER \
    --create --if-not-exists \
    --topic battle.requests \
    --partitions 3 \
    --replication-factor 1 \
    --config retention.ms=$RETENTION_7D \
    --config cleanup.policy=delete

# -----------------------------------------------
# Topic 2: battle.results
# 对战结果流 (每回合完整状态)
# -----------------------------------------------
echo "Creating topic: battle.results"
kafka-topics --bootstrap-server $BROKER \
    --create --if-not-exists \
    --topic battle.results \
    --partitions 3 \
    --replication-factor 1 \
    --config retention.ms=$RETENTION_7D \
    --config cleanup.policy=delete

# -----------------------------------------------
# Topic 3: battle.events
# 对战事件流 (细粒度事件)
# -----------------------------------------------
echo "Creating topic: battle.events"
kafka-topics --bootstrap-server $BROKER \
    --create --if-not-exists \
    --topic battle.events \
    --partitions 6 \
    --replication-factor 1 \
    --config retention.ms=$RETENTION_30D \
    --config cleanup.policy=delete

# -----------------------------------------------
# Topic 4: battle.analytics
# 分析结果流 (Spark -> API Server)
# -----------------------------------------------
echo "Creating topic: battle.analytics"
kafka-topics --bootstrap-server $BROKER \
    --create --if-not-exists \
    --topic battle.analytics \
    --partitions 3 \
    --replication-factor 1 \
    --config retention.ms=$RETENTION_INF \
    --config cleanup.policy=compact

echo ""
echo "================================================"
echo "All topics created. Listing topics:"
echo "================================================"
kafka-topics --bootstrap-server $BROKER --list

echo ""
echo "Topic details:"
for topic in battle.requests battle.results battle.events battle.analytics; do
    echo "--- $topic ---"
    kafka-topics --bootstrap-server $BROKER --describe --topic $topic
done

echo ""
echo "Done!"
