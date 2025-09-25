# =============================================================================
# 4. Redis Cache (app/cache/redis_cache.py)
# =============================================================================

import redis
import json
from typing import Any, Optional
import pickle
from datetime import timedelta
import logging

from app.config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                return pickle.loads(value)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        try:
            serialized = pickle.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    async def delete(self, key: str):
        """Delete key from cache"""
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

# Initialize cache if REDIS_URL is configured, otherwise create a no-op cache
try:
    if settings.REDIS_URL:
        cache = RedisCache(settings.REDIS_URL)
    else:
        raise RuntimeError("No REDIS_URL configured")
except Exception:
    logger.warning("Redis not configured or failed to initialize; using in-memory fallback")

    class _InMemoryCache(RedisCache):
        def __init__(self):
            self._store = {}

        async def get(self, key: str):
            return self._store.get(key)

        async def set(self, key: str, value: Any, ttl: int = 3600):
            self._store[key] = value

        async def delete(self, key: str):
            if key in self._store:
                del self._store[key]

        async def exists(self, key: str) -> bool:
            return key in self._store

    cache = _InMemoryCache()