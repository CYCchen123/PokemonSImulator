"""
Redis 客户端 (Person A)

提供:
- 连接池管理
- Session 缓存（24h TTL）
- 热数据缓存（species/moves）
- 实时排行榜（Sorted Set）
- API 限流（滑动窗口）
- 全局统计缓存

用法:
    from services.redis_client import RedisClient
    redis_client = RedisClient()
    await redis_client.get("key")
"""
import json
import logging
from typing import Optional, Any
from redis import asyncio as aioredis
from redis.asyncio import ConnectionPool
from config import REDIS_URL

logger = logging.getLogger(__name__)


class RedisClient:
    """异步 Redis 客户端封装"""

    _instance: Optional["RedisClient"] = None
    _pool: Optional[ConnectionPool] = None

    def __init__(self):
        if not REDIS_URL:
            logger.warning("REDIS_URL 未配置，Redis 功能禁用")
            self._redis = None
            return
        self._redis = aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )

    @classmethod
    def get_instance(cls) -> "RedisClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def redis(self):
        return self._redis

    async def health(self) -> bool:
        """检查 Redis 连接。"""
        if not self._redis:
            return False
        try:
            return await self._redis.ping()
        except Exception:
            return False

    # ============================================================
    # 基础操作
    # ============================================================
    async def get(self, key: str) -> Optional[str]:
        if not self._redis:
            return None
        return await self._redis.get(key)

    async def set(self, key: str, value: str, ttl: int = 0) -> bool:
        if not self._redis:
            return False
        if ttl > 0:
            await self._redis.setex(key, ttl, value)
        else:
            await self._redis.set(key, value)
        return True

    async def get_json(self, key: str) -> Optional[dict]:
        if not self._redis:
            return None
        val = await self._redis.get(key)
        return json.loads(val) if val else None

    async def set_json(self, key: str, data: Any, ttl: int = 0) -> bool:
        if not self._redis:
            return False
        val = json.dumps(data, ensure_ascii=False)
        return await self.set(key, val, ttl)

    async def delete(self, *keys: str) -> int:
        if not self._redis:
            return 0
        return await self._redis.delete(*keys)

    # ============================================================
    # Session 管理
    # ============================================================
    SESSION_TTL = 86400  # 24h
    SESSION_PREFIX = "session:"

    async def set_session(self, token: str, user_data: dict) -> bool:
        return await self.set_json(
            f"{self.SESSION_PREFIX}{token}", user_data, self.SESSION_TTL
        )

    async def get_session(self, token: str) -> Optional[dict]:
        return await self.get_json(f"{self.SESSION_PREFIX}{token}")

    async def delete_session(self, token: str) -> int:
        return await self.delete(f"{self.SESSION_PREFIX}{token}")

    # ============================================================
    # 热数据缓存 (species / moves)
    # ============================================================
    DATA_TTL = 3600  # 1h
    DATA_PREFIX = "data:"

    async def cache_species(self, species_id: int, data: dict) -> bool:
        return await self.set_json(
            f"{self.DATA_PREFIX}species:{species_id}", data, self.DATA_TTL
        )

    async def get_cached_species(self, species_id: int) -> Optional[dict]:
        return await self.get_json(f"{self.DATA_PREFIX}species:{species_id}")

    async def cache_move(self, move_id: int, data: dict) -> bool:
        return await self.set_json(
            f"{self.DATA_PREFIX}move:{move_id}", data, self.DATA_TTL
        )

    async def get_cached_move(self, move_id: int) -> Optional[dict]:
        return await self.get_json(f"{self.DATA_PREFIX}move:{move_id}")

    # ============================================================
    # 实时排行榜 (Sorted Set)
    # ============================================================
    RANK_PREFIX = "rank:"

    async def update_rank(self, name: str, member: str, score: float) -> bool:
        """更新排行榜分数。"""
        if not self._redis:
            return False
        await self._redis.zadd(f"{self.RANK_PREFIX}{name}", {member: score})
        return True

    async def get_rank(self, name: str, limit: int = 20, desc: bool = True) -> list:
        """获取排行榜前 N 名。[(member, score), ...]"""
        if not self._redis:
            return []
        if desc:
            return await self._redis.zrevrange(
                f"{self.RANK_PREFIX}{name}", 0, limit - 1, withscores=True
            )
        return await self._redis.zrange(
            f"{self.RANK_PREFIX}{name}", 0, limit - 1, withscores=True
        )

    async def get_rank_of_member(self, name: str, member: str) -> Optional[int]:
        """获取成员的排名（从 1 开始）。"""
        if not self._redis:
            return None
        rank = await self._redis.zrevrank(f"{self.RANK_PREFIX}{name}", member)
        return rank + 1 if rank is not None else None

    # ============================================================
    # 事件计数
    # ============================================================
    EVENT_PREFIX = "event:count:"

    async def incr_event(self, event_type: str) -> int:
        if not self._redis:
            return 0
        return await self._redis.incr(f"{self.EVENT_PREFIX}{event_type}")

    async def get_event_count(self, event_type: str) -> int:
        if not self._redis:
            return 0
        val = await self._redis.get(f"{self.EVENT_PREFIX}{event_type}")
        return int(val) if val else 0

    # ============================================================
    # 对战房间状态
    # ============================================================
    BATTLE_PREFIX = "battle:"

    async def set_battle_state(self, battle_id: str, state: dict, ttl: int = 3600) -> bool:
        return await self.set_json(
            f"{self.BATTLE_PREFIX}{battle_id}:state", state, ttl
        )

    async def get_battle_state(self, battle_id: str) -> Optional[dict]:
        return await self.get_json(f"{self.BATTLE_PREFIX}{battle_id}:state")

    async def delete_battle_state(self, battle_id: str) -> int:
        return await self.delete(f"{self.BATTLE_PREFIX}{battle_id}:state")

    # ============================================================
    # API 限流 (滑动窗口)
    # ============================================================
    RATELIMIT_PREFIX = "ratelimit:"
    RATELIMIT_WINDOW = 60  # 60s 窗口
    RATELIMIT_MAX_REQUESTS = 100  # 每窗口最多 100 次

    async def check_rate_limit(self, ip: str, endpoint: str,
                                max_req: int = RATELIMIT_MAX_REQUESTS,
                                window: int = RATELIMIT_WINDOW) -> tuple[bool, int]:
        """
        检查 API 限流。

        Returns:
            (allowed: bool, remaining: int)
        """
        if not self._redis:
            return (True, max_req)

        key = f"{self.RATELIMIT_PREFIX}{ip}:{endpoint}"
        current = await self._redis.incr(key)

        if current == 1:
            await self._redis.expire(key, window)

        remaining = max(0, max_req - current)
        return (current <= max_req, remaining)

    # ============================================================
    # 全局统计缓存
    # ============================================================
    STATS_PREFIX = "stats:"
    STATS_TTL = 30  # 30s

    async def cache_global_stats(self, stats: dict) -> bool:
        return await self.set_json(
            f"{self.STATS_PREFIX}global", stats, self.STATS_TTL
        )

    async def get_global_stats(self) -> Optional[dict]:
        return await self.get_json(f"{self.STATS_PREFIX}global")

    # ============================================================
    # 关闭
    # ============================================================
    async def close(self):
        if self._redis:
            await self._redis.close()
            logger.info("Redis 连接已关闭")
