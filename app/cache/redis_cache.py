# =============================================================================
# 4. Redis Cache (app/cache/redis_cache.py)
# =============================================================================

import redis
import json
from typing import Any, Optional
import pickle
from datetime import timedelta

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

# Initialize cache
cache = RedisCache(settings.REDIS_URL)