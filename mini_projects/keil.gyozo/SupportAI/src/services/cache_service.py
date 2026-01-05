"""Redis caching service."""

import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from ..config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service for Redis caching operations."""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        ttl: Optional[int] = None
    ):
        """Initialize Redis cache service.

        Args:
            redis_url: Redis connection URL
            ttl: Default TTL in seconds
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.ttl = ttl or settings.REDIS_TTL

        self.client: Optional[redis.Redis] = None
        logger.info(f"Initialized cache service (TTL: {self.ttl}s)")

    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value (deserialized from JSON) or None if not found
        """
        if not self.client:
            await self.connect()

        try:
            value = await self.client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache MISS: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache get failed for key '{key}': {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: TTL in seconds (default: from settings)

        Returns:
            True if successful
        """
        if not self.client:
            await self.connect()

        cache_ttl = ttl or self.ttl

        try:
            serialized_value = json.dumps(value)
            await self.client.setex(key, cache_ttl, serialized_value)
            logger.debug(f"Cache SET: {key} (TTL: {cache_ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set failed for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted
        """
        if not self.client:
            await self.connect()

        try:
            deleted = await self.client.delete(key)
            if deleted:
                logger.debug(f"Cache DELETE: {key}")
            return bool(deleted)
        except Exception as e:
            logger.error(f"Cache delete failed for key '{key}': {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists
        """
        if not self.client:
            await self.connect()

        try:
            exists = await self.client.exists(key)
            return bool(exists)
        except Exception as e:
            logger.error(f"Cache exists check failed for key '{key}': {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern.

        Args:
            pattern: Redis pattern (e.g., "ticket:*")

        Returns:
            Number of keys deleted
        """
        if not self.client:
            await self.connect()

        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                deleted = await self.client.delete(*keys)
                logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache pattern delete failed for '{pattern}': {e}")
            return 0

    async def health_check(self) -> bool:
        """Check Redis connection health.

        Returns:
            True if connection is healthy
        """
        try:
            if not self.client:
                await self.connect()
            await self.client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False
