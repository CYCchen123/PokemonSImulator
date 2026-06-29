"""
Spark Structured Streaming: Real-time Event Processing

Consumes battle.events from Kafka, computes windowed statistics,
and writes results to the battle.analytics Kafka topic.

Usage:
  spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
      realtime_events.py
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, window, count, when, sum as spark_sum,
    to_json, struct, lit, current_timestamp
)
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType


# Event schema (matches Kafka battle.events messages)
EVENT_SCHEMA = StructType([
    StructField("battle_id", StringType(), True),
    StructField("turn", IntegerType(), True),
    StructField("timeline_index", IntegerType(), True),
    StructField("event_type", StringType(), True),
    StructField("description", StringType(), True),
    StructField("details", StringType(), True),  # JSON string
    StructField("timestamp", StringType(), True),
])


def main():
    spark = SparkSession.builder \
        .appName("PokemonSimulator-RealtimeEvents") \
        .config("spark.sql.streaming.schemaInference", "true") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()

    # Read from Kafka
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "battle.events") \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()

    # Parse JSON values
    events_df = kafka_df.select(
        from_json(col("value").cast("string"), EVENT_SCHEMA).alias("event")
    ).select("event.*")

    # Convert timestamp string to timestamp type
    events_df = events_df.withColumn(
        "event_time",
        col("timestamp").cast(TimestampType())
    )

    # --- Windowed aggregations ---

    # 1. Event counts by type (5-minute windows)
    event_counts = events_df \
        .withWatermark("event_time", "1 minute") \
        .groupBy(
            window(col("event_time"), "5 minutes", "1 minute"),
            col("event_type")
        ) \
        .agg(count("*").alias("count")) \
        .select(
            lit("realtime_event_counts").alias("type"),
            to_json(struct(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("event_type"),
                col("count")
            )).alias("value")
        )

    # 2. Active battles count
    active_battles = events_df \
        .withWatermark("event_time", "1 minute") \
        .groupBy(
            window(col("event_time"), "5 minutes", "1 minute")
        ) \
        .agg(count("battle_id").alias("event_count")) \
        .select(
            lit("realtime_battle_activity").alias("type"),
            to_json(struct(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("event_count")
            )).alias("value")
        )

    # Write to Kafka battle.analytics topic
    def write_to_analytics(df, checkpoint_name: str):
        return df.writeStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "kafka:9092") \
            .option("topic", "battle.analytics") \
            .option("checkpointLocation", f"/tmp/spark-checkpoint/{checkpoint_name}") \
            .outputMode("append") \
            .start()

    query1 = write_to_analytics(event_counts, "event-counts")
    query2 = write_to_analytics(active_battles, "battle-activity")

    print("Real-time event processing started. Waiting for data...")
    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()
