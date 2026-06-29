"""
PokemonSimulator API Server
FastAPI application providing REST API for the Vue.js frontend.
"""
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import API_HOST, API_PORT, DEBUG
from services.db import (
    create_player, get_player, list_players,
    create_team, get_team, list_teams, delete_team,
    create_battle_record, get_battle, list_battles, update_battle_status,
    add_battle_turn,
)
from services.kafka_service import send_battle_request, start_consumer, on_battle_result
from services.hdfs_client import store_battle_init, store_battle_turn, store_game_over

# ============================================================
# Logging
# ============================================================
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger("api-server")

# ============================================================
# Kafka result handler (updates DB when battles complete)
# ============================================================
def handle_battle_result(battle_id: str, data: dict):
    """Called by Kafka consumer when a battle result is received."""
    logger.info(f"Processing result for battle {battle_id}, turn {data.get('turn')}")

    turn = data.get("turn", 0)
    state = data.get("state", {})

    # Check if battle is over
    if state:
        sides = state.get("battle", {}).get("sides", state.get("sides", []))
        all_fainted = False
        winner_side = None

        for side in sides:
            pokemons = side.get("pokemons", [])
            side_name = side.get("name", "")
            # Check if all pokemon on this side are fainted
            if pokemons and all(p.get("fainted", False) for p in pokemons):
                all_fainted = True
                # Winner is the other side
                winner_side = "b" if "Side A" in side_name or side.get("side") == 0 else "a"

        if all_fainted and winner_side:
            update_battle_status(battle_id, "completed", winner_side=winner_side,
                                 total_turns=turn)
            logger.info(f"Battle {battle_id} completed, winner: side {winner_side}")

    # Record turn
    add_battle_turn(battle_id, turn)

# Register handler
on_battle_result(handle_battle_result)


# ============================================================
# Application lifecycle
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Kafka consumer...")
    start_consumer()

    # 检查 Redis 连接
    from services.redis_client import RedisClient
    redis = RedisClient.get_instance()
    if await redis.health():
        logger.info("Redis 连接正常")
    else:
        logger.warning("Redis 不可用，缓存功能禁用")

    logger.info("API Server ready")
    yield
    # Shutdown
    await redis.close()
    logger.info("API Server shutting down")


app = FastAPI(
    title="PokemonSimulator API",
    version="1.0.0",
    description="REST API for Pokemon Gen9 Singles Battle Simulator",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Pydantic Models
# ============================================================
class PlayerCreate(BaseModel):
    name: str

class TeamCreate(BaseModel):
    player_id: str
    name: str = "Untitled Team"
    pokemon: list

class BattleCreate(BaseModel):
    player_a_id: str | None = None
    player_b_id: str | None = None
    team_a: dict
    team_b: dict
    seed: int = 0

class TurnAction(BaseModel):
    side: str
    type: str  # attack, switch, pass
    move_index: int | None = None
    move_name: str | None = None
    switch_index: int | None = None
    target_index: int | None = None


class TurnRequest(BaseModel):
    actions: list[TurnAction]


# ============================================================
# Health
# ============================================================
@app.get("/api/v1/health")
async def health_check():
    from services.redis_client import RedisClient
    redis = RedisClient.get_instance()
    redis_ok = await redis.health()
    return {
        "ok": True,
        "data": {
            "status": "healthy",
            "service": "pokemon-simulator-api",
            "version": "1.0.0",
            "redis": "connected" if redis_ok else "unavailable",
        }
    }


# ============================================================
# Players
# ============================================================
@app.get("/api/v1/players")
async def api_list_players(limit: int = 50, offset: int = 0):
    players = list_players(limit=limit, offset=offset)
    return {"ok": True, "data": players}


@app.get("/api/v1/players/{player_id}")
async def api_get_player(player_id: str):
    player = get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return {"ok": True, "data": player}


@app.post("/api/v1/players", status_code=201)
async def api_create_player(body: PlayerCreate):
    player = create_player(body.name)
    return {"ok": True, "data": player}


# ============================================================
# Teams
# ============================================================
@app.get("/api/v1/teams")
async def api_list_teams(player_id: str = None, limit: int = 50, offset: int = 0):
    teams = list_teams(player_id=player_id, limit=limit, offset=offset)
    return {"ok": True, "data": teams}


@app.get("/api/v1/teams/{team_id}")
async def api_get_team(team_id: str):
    team = get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"ok": True, "data": team}


@app.post("/api/v1/teams", status_code=201)
async def api_create_team(body: TeamCreate):
    team = create_team(body.player_id, body.name, body.pokemon)
    return {"ok": True, "data": team}


@app.delete("/api/v1/teams/{team_id}")
async def api_delete_team(team_id: str):
    if not delete_team(team_id):
        raise HTTPException(status_code=404, detail="Team not found")
    return {"ok": True, "data": {"deleted": team_id}}


# ============================================================
# Battles
# ============================================================
@app.post("/api/v1/battles", status_code=201)
async def api_create_battle(body: BattleCreate):
    battle_id = str(uuid.uuid4())

    init_json = {
        "side_a": body.team_a,
        "side_b": body.team_b,
        "seed": body.seed,
    }

    # 1. Create record in PostgreSQL
    battle = create_battle_record(
        battle_id=battle_id,
        player_a_id=body.player_a_id,
        player_b_id=body.player_b_id,
        team_a_id=None,
        team_b_id=None,
        seed=body.seed,
        init_json=init_json,
    )

    # 2. Send to Kafka for processing
    success = send_battle_request(battle_id, "create", init_json)
    if not success:
        update_battle_status(battle_id, "error")
        raise HTTPException(status_code=500, detail="Failed to send battle request to Kafka")

    return {"ok": True, "data": battle}


@app.post("/api/v1/battles/{battle_id}/turns")
async def api_process_turn(battle_id: str, body: TurnRequest):
    # Validate battle exists
    battle = get_battle(battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    if battle["status"] not in ("active", "pending"):
        raise HTTPException(status_code=400, detail=f"Battle is {battle['status']}")

    # Send turn actions to Kafka
    actions = [action.model_dump() for action in body.actions]
    success = send_battle_request(battle_id, "turn", {"actions": actions})
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send turn request to Kafka")

    return {
        "ok": True,
        "data": {
            "battle_id": battle_id,
            "status": "processing",
            "message": f"Turn actions sent for processing"
        }
    }


@app.get("/api/v1/battles")
async def api_list_battles(
    status: str = None,
    player_id: str = None,
    limit: int = 50,
    offset: int = 0
):
    battles = list_battles(status=status, player_id=player_id, limit=limit, offset=offset)
    return {"ok": True, "data": battles}


@app.get("/api/v1/battles/{battle_id}")
async def api_get_battle(battle_id: str):
    battle = get_battle(battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    return {"ok": True, "data": battle}


# ============================================================
# Data (static enumerations)
# ============================================================
@app.get("/api/v1/data/enums")
async def api_get_enums():
    """Return all enum value-to-name mappings for the frontend."""
    enums = {
        "type": [
            {"value": 0, "name": "Normal", "label": "一般"},
            {"value": 1, "name": "Fire", "label": "火"},
            {"value": 2, "name": "Water", "label": "水"},
            {"value": 3, "name": "Electric", "label": "电"},
            {"value": 4, "name": "Grass", "label": "草"},
            {"value": 5, "name": "Ice", "label": "冰"},
            {"value": 6, "name": "Fighting", "label": "格斗"},
            {"value": 7, "name": "Poison", "label": "毒"},
            {"value": 8, "name": "Ground", "label": "地面"},
            {"value": 9, "name": "Flying", "label": "飞行"},
            {"value": 10, "name": "Psychic", "label": "超能力"},
            {"value": 11, "name": "Bug", "label": "虫"},
            {"value": 12, "name": "Rock", "label": "岩石"},
            {"value": 13, "name": "Ghost", "label": "幽灵"},
            {"value": 14, "name": "Dragon", "label": "龙"},
            {"value": 15, "name": "Dark", "label": "恶"},
            {"value": 16, "name": "Steel", "label": "钢"},
            {"value": 17, "name": "Fairy", "label": "妖精"},
        ],
        "category": [
            {"value": 0, "name": "Physical", "label": "物理"},
            {"value": 1, "name": "Special", "label": "特殊"},
            {"value": 2, "name": "Status", "label": "变化"},
        ],
        "weather": [
            {"value": 0, "name": "Clear", "label": "无天气"},
            {"value": 1, "name": "Rain", "label": "雨天"},
            {"value": 2, "name": "Sun", "label": "晴天"},
            {"value": 3, "name": "Sandstorm", "label": "沙暴"},
            {"value": 4, "name": "Hail", "label": "冰雹"},
            {"value": 5, "name": "Snow", "label": "雪天"},
        ],
        "field": [
            {"value": 0, "name": "None", "label": "无场地"},
            {"value": 1, "name": "Psychic", "label": "精神场地"},
            {"value": 2, "name": "Electric", "label": "电气场地"},
            {"value": 3, "name": "Grassy", "label": "青草场地"},
            {"value": 4, "name": "Misty", "label": "薄雾场地"},
            {"value": 5, "name": "TrickRoom", "label": "戏法空间"},
        ],
        "status": [
            {"value": 0, "name": "None", "label": "无状态"},
            {"value": 1, "name": "Burn", "label": "灼伤"},
            {"value": 2, "name": "Freeze", "label": "冰冻"},
            {"value": 3, "name": "Paralysis", "label": "麻痹"},
            {"value": 4, "name": "Poison", "label": "中毒"},
            {"value": 5, "name": "Sleep", "label": "睡眠"},
            {"value": 6, "name": "Flinch", "label": "畏缩"},
            {"value": 7, "name": "ToxicPoison", "label": "剧毒"},
            {"value": 8, "name": "Confusion", "label": "混乱"},
        ],
        "nature": [
            {"value": 0, "name": "Hardy"},
            {"value": 1, "name": "Lonely", "boost": "atk", "reduce": "def"},
            {"value": 2, "name": "Brave", "boost": "atk", "reduce": "spe"},
            {"value": 3, "name": "Adamant", "boost": "atk", "reduce": "spa"},
            {"value": 4, "name": "Naughty", "boost": "atk", "reduce": "spd"},
            {"value": 5, "name": "Bold", "boost": "def", "reduce": "atk"},
            {"value": 6, "name": "Docile"},
            {"value": 7, "name": "Relaxed", "boost": "def", "reduce": "spe"},
            {"value": 8, "name": "Impish", "boost": "def", "reduce": "spa"},
            {"value": 9, "name": "Lax", "boost": "def", "reduce": "spd"},
            {"value": 10, "name": "Timid", "boost": "spe", "reduce": "atk"},
            {"value": 11, "name": "Hasty", "boost": "spe", "reduce": "def"},
            {"value": 12, "name": "Serious"},
            {"value": 13, "name": "Jolly", "boost": "spe", "reduce": "spa"},
            {"value": 14, "name": "Naive", "boost": "spe", "reduce": "spd"},
            {"value": 15, "name": "Modest", "boost": "spa", "reduce": "atk"},
            {"value": 16, "name": "Mild", "boost": "spa", "reduce": "def"},
            {"value": 17, "name": "Quiet", "boost": "spa", "reduce": "spe"},
            {"value": 18, "name": "Bashful"},
            {"value": 19, "name": "Rash", "boost": "spa", "reduce": "spd"},
            {"value": 20, "name": "Calm", "boost": "spd", "reduce": "atk"},
            {"value": 21, "name": "Gentle", "boost": "spd", "reduce": "def"},
            {"value": 22, "name": "Sassy", "boost": "spd", "reduce": "spe"},
            {"value": 23, "name": "Careful", "boost": "spd", "reduce": "spa"},
            {"value": 24, "name": "Quirky"},
        ],
    }
    return {"ok": True, "data": enums}


# ============================================================
# Stats
# ============================================================
@app.get("/api/v1/stats/global")
async def api_global_stats():
    """Return global statistics (with Redis cache)."""
    from services.redis_client import RedisClient
    redis = RedisClient.get_instance()

    # 尝试从 Redis 读取缓存
    cached = await redis.get_global_stats()
    if cached:
        return {"ok": True, "data": cached, "source": "redis"}

    # 从 PostgreSQL 查询
    from services.db import get_connection
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) as cnt FROM players;")
        total_players = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) as cnt FROM battles;")
        total_battles = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) as cnt FROM teams;")
        total_teams = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) as cnt FROM battles WHERE status = 'completed';")
        total_completed = cur.fetchone()[0]
        data = {
            "total_players": total_players,
            "total_battles": total_battles,
            "total_teams": total_teams,
            "total_completed_battles": total_completed,
        }
    finally:
        cur.close()
        conn.close()

    # 写入 Redis 缓存 (TTL 30s)
    await redis.cache_global_stats(data)
    return {"ok": True, "data": data, "source": "postgresql"}


@app.get("/api/v1/stats/rank/usage")
async def api_usage_rank(limit: int = 20):
    """Get real-time pokemon usage ranking from Redis."""
    from services.redis_client import RedisClient
    redis = RedisClient.get_instance()
    rank = await redis.get_rank("pokemon:usage", limit=limit)
    return {
        "ok": True,
        "data": [{"species_id": int(m), "score": s} for m, s in rank],
    }


@app.get("/api/v1/stats/rank/winrate")
async def api_winrate_rank(limit: int = 20):
    """Get real-time winrate ranking from Redis."""
    from services.redis_client import RedisClient
    redis = RedisClient.get_instance()
    rank = await redis.get_rank("pokemon:winrate", limit=limit)
    return {
        "ok": True,
        "data": [{"species_id": int(m), "score": s} for m, s in rank],
    }


@app.get("/api/v1/stats/events")
async def api_event_counts():
    """Get real-time event counts from Redis."""
    from services.redis_client import RedisClient
    redis = RedisClient.get_instance()
    event_types = ["damage", "faint", "switch", "ability_trigger",
                   "item_trigger", "status_apply", "stat_change"]
    counts = {}
    for et in event_types:
        counts[et] = await redis.get_event_count(et)
    return {"ok": True, "data": counts}


@app.get("/api/v1/stats/usage/history")
async def api_usage_history(days: int = 7):
    """Get pokemon usage history from PostgreSQL (PySpark batch results)."""
    from services.db import get_connection
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT species_id, species_name, times_used, times_koed,
                      avg_hp_percent, total_appearances
               FROM pokemon_usage_stats
               WHERE period_start >= NOW() - INTERVAL '%s days'
               ORDER BY times_used DESC LIMIT 50;""",
            (days,)
        )
        rows = cur.fetchall()
        return {"ok": True, "data": [dict(r) for r in rows]}
    finally:
        cur.close()
        conn.close()


@app.get("/api/v1/stats/analytics")
async def api_analytics(minutes: int = 30):
    """Get recent battle analytics from PostgreSQL (Spark Streaming results)."""
    from services.db import get_connection
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT window_start, window_end, event_type, count, metadata
               FROM battle_analytics
               WHERE window_start >= NOW() - INTERVAL '%s minutes'
               ORDER BY window_start DESC LIMIT 100;""",
            (minutes,)
        )
        rows = cur.fetchall()
        return {"ok": True, "data": [dict(r) for r in rows]}
    finally:
        cur.close()
        conn.close()


# ============================================================
# Entry point
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=DEBUG)
