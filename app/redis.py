import json
import redis.asyncio as aioredis
from app.config import settings

redis_client: aioredis.Redis = None


async def init_redis():
    global redis_client
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        print("Redis connected")
    except Exception as e:
        print(f"Redis connection failed: {e} — running without cache")
        redis_client = None


async def close_redis():
    if redis_client:
        await redis_client.close()


async def cache_get(key: str) -> dict | None:
    """Get JSON value from cache. Returns None if not found or Redis unavailable."""
    if not redis_client:
        return None
    try:
        data = await redis_client.get(key)
        return json.loads(data) if data else None
    except Exception:
        return None


async def cache_set(key: str, value: dict, ttl_seconds: int = 3600):
    """Set JSON value in cache with TTL."""
    if not redis_client:
        return
    try:
        await redis_client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
    except Exception:
        pass


async def cache_delete(key: str):
    """Delete a cache key."""
    if not redis_client:
        return
    try:
        await redis_client.delete(key)
    except Exception:
        pass
