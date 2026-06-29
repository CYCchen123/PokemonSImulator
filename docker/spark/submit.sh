#!/bin/bash
# Submit Spark jobs to the Spark cluster
# Usage: ./submit.sh [job_name] [args...]

set -e

SPARK_MASTER="${SPARK_MASTER:-spark://spark-master:7077}"
SPARK_HOME="${SPARK_HOME:-/opt/spark}"
JOBS_DIR="${JOBS_DIR:-/opt/spark/jobs}"

echo "Spark Master: $SPARK_MASTER"
echo "Jobs directory: $JOBS_DIR"

case "${1:-help}" in
    pokemon-usage)
        echo "Submitting: Pokemon Usage Statistics"
        exec $SPARK_HOME/bin/spark-submit \
            --master $SPARK_MASTER \
            --deploy-mode client \
            --driver-memory 1G \
            --executor-memory 1G \
            --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.3 \
            $JOBS_DIR/batch/pokemon_usage.py \
            "${@:2}"
        ;;

    move-usage)
        echo "Submitting: Move Usage Statistics"
        exec $SPARK_HOME/bin/spark-submit \
            --master $SPARK_MASTER \
            --deploy-mode client \
            --driver-memory 1G \
            --executor-memory 1G \
            --packages org.postgresql:postgresql:42.7.3 \
            $JOBS_DIR/batch/move_usage.py \
            "${@:2}"
        ;;

    realtime-events)
        echo "Submitting: Real-time Event Processing"
        exec $SPARK_HOME/bin/spark-submit \
            --master $SPARK_MASTER \
            --deploy-mode client \
            --driver-memory 2G \
            --executor-memory 1G \
            --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
            $JOBS_DIR/streaming/realtime_events.py \
            "${@:2}"
        ;;

    *)
        echo "PokemonSimulator Spark Job Runner"
        echo ""
        echo "Usage: $0 <job_name> [args...]"
        echo ""
        echo "Available jobs:"
        echo "  pokemon-usage     - Compute pokemon usage statistics (batch)"
        echo "  move-usage        - Compute move usage statistics (batch)"
        echo "  realtime-events   - Real-time event processing (streaming)"
        echo ""
        echo "Examples:"
        echo "  $0 pokemon-usage --start-date 2026-06-01 --end-date 2026-06-24"
        echo "  $0 realtime-events"
        ;;
esac
