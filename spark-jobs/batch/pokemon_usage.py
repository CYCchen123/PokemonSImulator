"""
Spark Batch Job: Pokemon Usage Statistics

Reads raw battle data from HDFS, computes per-species usage statistics,
and writes results to PostgreSQL.

Usage:
  spark-submit pokemon_usage.py --hdfs-path /user/pokemon/raw/battles/ --period 7d
"""
import json
import sys
from datetime import datetime, timedelta
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, explode, count, sum as spark_sum, avg, when, lit, max as spark_max
)
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, ArrayType


# ============================================================
# Schema definitions
# ============================================================
TURN_SCHEMA = StructType([
    StructField("battle_id", StringType(), True),
    StructField("turn", IntegerType(), True),
    StructField("ok", StringType(), True),
    StructField("state", StringType(), True),  # JSON string
    StructField("timestamp", StringType(), True),
])


def parse_battle_state(state_json: str) -> dict:
    """Parse the nested battle state JSON."""
    try:
        data = json.loads(state_json)
        return data.get("battle", data)
    except (json.JSONDecodeError, TypeError):
        return {}


def compute_pokemon_usage(spark: SparkSession, hdfs_base: str, start_date: str, end_date: str):
    """
    Compute pokemon usage statistics from raw battle data.

    Args:
        spark: SparkSession
        hdfs_base: HDFS base path (e.g., /user/pokemon/raw/battles/)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    # Generate date paths
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    paths = []
    current = start
    while current <= end:
        paths.append(f"{hdfs_base}{current.year}/{current.month:02d}/{current.day:02d}/*/turn_*.json")
        current += timedelta(days=1)

    print(f"Reading from {len(paths)} date paths...")

    # Read all turn JSON files
    df = spark.read.schema(TURN_SCHEMA).json(paths)

    # Parse state and extract pokemon data
    # Since state is a complex nested JSON, we use RDD for flexibility
    rdd = df.select("battle_id", "turn", "state").rdd

    # Extract pokemon usage per battle
    pokemon_records = rdd.flatMap(lambda row: extract_pokemon_from_state(
        row["battle_id"], row["turn"], row["state"]
    ))

    # Convert to DataFrame
    pokemon_schema = StructType([
        StructField("battle_id", StringType(), True),
        StructField("turn", IntegerType(), True),
        StructField("species_id", IntegerType(), True),
        StructField("species_name", StringType(), True),
        StructField("fainted", IntegerType(), True),  # 0 or 1
        StructField("hp_percent", IntegerType(), True),
        StructField("side", IntegerType(), True),  # 0 or 1
    ])
    pokemon_df = spark.createDataFrame(pokemon_records, schema=pokemon_schema)

    # Aggregate statistics
    stats = pokemon_df.groupBy("species_id").agg(
        spark_max("species_name").alias("species_name"),
        count("*").alias("times_used"),
        spark_sum("fainted").alias("times_koed"),
        avg("hp_percent").alias("avg_hp_percent"),
    )

    # Count unique battles per species (for win rate later)
    battle_counts = pokemon_df.select("battle_id", "species_id", "side").distinct() \
        .groupBy("species_id").agg(
            count("*").alias("total_appearances")
        )

    final_stats = stats.join(battle_counts, "species_id") \
        .orderBy(col("times_used").desc()) \
        .limit(100)

    print("=== Pokemon Usage Statistics ===")
    final_stats.show(50, truncate=False)

    return final_stats


def extract_pokemon_from_state(battle_id: str, turn: int, state_str: str) -> list:
    """Extract pokemon records from a single turn's battle state."""
    state = parse_battle_state(state_str)
    records = []

    sides = state.get("sides", [])
    for side_idx, side in enumerate(sides):
        for pokemon in side.get("pokemons", []):
            records.append({
                "battle_id": battle_id,
                "turn": turn,
                "species_id": pokemon.get("speciesId", 0),
                "species_name": str(pokemon.get("speciesId", "")),
                "fainted": 1 if pokemon.get("fainted", False) else 0,
                "hp_percent": int((pokemon.get("hp", 0) / max(pokemon.get("maxHp", 1), 1)) * 100),
                "side": side_idx,
            })

    return records


def write_to_postgres(df: DataFrame, table: str, url: str, properties: dict):
    """Write DataFrame to PostgreSQL."""
    df.write \
        .format("jdbc") \
        .option("url", url) \
        .option("dbtable", table) \
        .option("user", properties["user"]) \
        .option("password", properties["password"]) \
        .option("driver", "org.postgresql.Driver") \
        .mode("overwrite") \
        .save()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pokemon Usage Statistics")
    parser.add_argument("--hdfs-path", default="/user/pokemon/raw/battles/",
                        help="HDFS base path for raw battle data")
    parser.add_argument("--start-date", default=None,
                        help="Start date (YYYY-MM-DD), default: 7 days ago")
    parser.add_argument("--end-date", default=None,
                        help="End date (YYYY-MM-DD), default: today")
    parser.add_argument("--db-url", default="jdbc:postgresql://postgres:5432/pokemon_simulator",
                        help="PostgreSQL JDBC URL")
    parser.add_argument("--db-user", default="pokemon")
    parser.add_argument("--db-password", default="pokemon123")
    args = parser.parse_args()

    # Default date range: last 7 days
    end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
    start_date = args.start_date or (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    # Initialize Spark
    spark = SparkSession.builder \
        .appName("PokemonSimulator-PokemonUsage") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()

    try:
        print(f"Computing pokemon usage: {start_date} to {end_date}")
        stats = compute_pokemon_usage(spark, args.hdfs_path, start_date, end_date)

        # Write to PostgreSQL
        db_props = {
            "user": args.db_user,
            "password": args.db_password,
        }
        write_to_postgres(stats, "pokemon_usage_stats", args.db_url, db_props)
        print("Results written to PostgreSQL")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
