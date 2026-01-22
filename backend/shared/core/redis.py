"""Redis connection and utilities."""
import json
import os
from typing import Any, Optional

import redis.asyncio as redis

# Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Redis client instance
redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    global redis_client

    if redis_client is None:
        redis_client = redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    return redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client

    if redis_client is not None:
        await redis_client.close()
        redis_client = None


class CacheService:
    """Cache service using Redis."""

    def __init__(self, redis: redis.Redis, default_ttl: int = 3600):
        self.redis = redis
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        value = await self.redis.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set a value in cache."""
        ttl = ttl or self.default_ttl

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        await self.redis.setex(key, ttl, value)

    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        await self.redis.delete(key)

    async def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching a pattern."""
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            await self.redis.delete(*keys)

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return bool(await self.redis.exists(key))

    async def incr(self, key: str) -> int:
        """Increment a counter."""
        return await self.redis.incr(key)

    async def expire(self, key: str, ttl: int) -> None:
        """Set expiration on a key."""
        await self.redis.expire(key, ttl)


# Cache key generators
def user_cache_key(user_id: str) -> str:
    """Generate cache key for user data."""
    return f"user:{user_id}"


def book_cache_key(isbn: str) -> str:
    """Generate cache key for book data."""
    return f"book:{isbn}"


def feed_cache_key(user_id: str, page: int = 1) -> str:
    """Generate cache key for user feed."""
    return f"feed:{user_id}:page:{page}"


def stats_cache_key(user_id: str, period: str) -> str:
    """Generate cache key for user stats."""
    return f"stats:{user_id}:{period}"


def search_cache_key(query: str, page: int = 1) -> str:
    """Generate cache key for search results."""
    return f"search:{query}:page:{page}"


# Global cache service instance
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """Get cache service instance."""
    global _cache_service
    if _cache_service is None:
        redis = await get_redis()
        _cache_service = CacheService(redis)
    return _cache_service


class CacheServiceProxy:
    """Proxy for cache service that lazily initializes."""

    async def get(self, key: str) -> Optional[Any]:
        svc = await get_cache_service()
        return await svc.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        svc = await get_cache_service()
        await svc.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        svc = await get_cache_service()
        await svc.delete(key)

    async def delete_pattern(self, pattern: str) -> None:
        svc = await get_cache_service()
        await svc.delete_pattern(pattern)

    async def exists(self, key: str) -> bool:
        svc = await get_cache_service()
        return await svc.exists(key)


# Singleton proxy for cache service
cache_service = CacheServiceProxy()
