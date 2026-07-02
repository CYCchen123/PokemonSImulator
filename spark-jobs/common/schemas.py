"""
PySpark StructType schemas for PokemonSimulator battle data.

All schemas used by parsers and analytics modules are defined here
to ensure consistent column names and types across the pipeline.
"""

from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    FloatType, BooleanType, ArrayType, MapType, DoubleType
)

# ── Battle State: one row per pokemon per turn ──────────────────────
BATTLE_STATE_SCHEMA = StructType([
    StructField("battle_id", StringType(), True),
    StructField("turn", IntegerType(), True),
    StructField("side_index", IntegerType(), True),
    StructField("pokemon_index", IntegerType(), True),
    StructField("species_id", IntegerType(), True),
    StructField("hp", IntegerType(), True),
    StructField("max_hp", IntegerType(), True),
    StructField("hp_pct", DoubleType(), True),
    StructField("fainted", BooleanType(), True),
    StructField("ability_id", IntegerType(), True),
    StructField("item_id", IntegerType(), True),
    StructField("types", ArrayType(IntegerType()), True),
    StructField("move_ids", ArrayType(IntegerType()), True),
    StructField("move_pps", ArrayType(IntegerType()), True),
    StructField("stat_stages", ArrayType(IntegerType()), True),
    StructField("status_count", IntegerType(), True),
    StructField("slot", IntegerType(), True),
])

# ── Battle Event: one row per timeline event ────────────────────────
EVENT_SCHEMA = StructType([
    StructField("battle_id", StringType(), True),
    StructField("turn", IntegerType(), True),
    StructField("timeline_index", IntegerType(), True),
    StructField("turn_index", IntegerType(), True),
    StructField("event_type", StringType(), True),
    StructField("description", StringType(), True),
    StructField("side_index", IntegerType(), True),
    StructField("pokemon_index", IntegerType(), True),
    StructField("pokemon_name", StringType(), True),
    StructField("reason", StringType(), True),
])

# ── Turn Action: one row per action input ───────────────────────────
ACTION_SCHEMA = StructType([
    StructField("battle_id", StringType(), True),
    StructField("turn", IntegerType(), True),
    StructField("side", StringType(), True),
    StructField("action_type", StringType(), True),
    StructField("move_index", IntegerType(), True),
    StructField("switch_index", IntegerType(), True),
])

# ── Pokemon Species lookup ──────────────────────────────────────────
SPECIES_SCHEMA = StructType([
    StructField("id", IntegerType(), True),
    StructField("name", StringType(), True),
    StructField("type1", IntegerType(), True),
    StructField("type2", IntegerType(), True),
    StructField("base_hp", IntegerType(), True),
    StructField("base_atk", IntegerType(), True),
    StructField("base_def", IntegerType(), True),
    StructField("base_spa", IntegerType(), True),
    StructField("base_spd", IntegerType(), True),
    StructField("base_spe", IntegerType(), True),
])

# ── Move lookup ─────────────────────────────────────────────────────
MOVE_SCHEMA = StructType([
    StructField("id", IntegerType(), True),
    StructField("name", StringType(), True),
    StructField("type", IntegerType(), True),
    StructField("category", StringType(), True),
    StructField("power", IntegerType(), True),
    StructField("accuracy", IntegerType(), True),
    StructField("pp", IntegerType(), True),
    StructField("priority", IntegerType(), True),
])

# ── Ability lookup ──────────────────────────────────────────────────
ABILITY_SCHEMA = StructType([
    StructField("id", IntegerType(), True),
    StructField("name", StringType(), True),
])

# ── Item lookup ─────────────────────────────────────────────────────
ITEM_SCHEMA = StructType([
    StructField("id", IntegerType(), True),
    StructField("name", StringType(), True),
])

# ── BData metagame stats ────────────────────────────────────────────
BDATA_SCHEMA = StructType([
    StructField("period", StringType(), True),
    StructField("cutoff", IntegerType(), True),
    StructField("metagame", StringType(), True),
    StructField("num_battles", IntegerType(), True),
    StructField("species_name", StringType(), True),
    StructField("raw_count", IntegerType(), True),
    StructField("usage_pct", DoubleType(), True),
    StructField("viability_0", FloatType(), True),
    StructField("viability_1", FloatType(), True),
    StructField("viability_2", FloatType(), True),
    StructField("viability_3", FloatType(), True),
    StructField("top_ability", StringType(), True),
    StructField("top_ability_pct", DoubleType(), True),
    StructField("top_item", StringType(), True),
    StructField("top_item_pct", DoubleType(), True),
    StructField("top_spread", StringType(), True),
    StructField("top_spread_pct", DoubleType(), True),
    StructField("top_move", StringType(), True),
    StructField("top_move_pct", DoubleType(), True),
    StructField("top_teammate", StringType(), True),
    StructField("top_teammate_pct", DoubleType(), True),
])
