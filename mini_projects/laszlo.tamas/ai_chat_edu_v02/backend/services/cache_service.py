"""
Simple in-memory cache for tenant and user data.
Reduces PostgreSQL query overhead for frequently accessed data.
P0.17: Now respects ENABLE_MEMORY_CACHE from system.ini
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SimpleCache:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self, default_ttl_seconds: int = 300, dev_mode: bool = False):
        """
        Initialize cache.
        
        Args:
            default_ttl_seconds: Default time-to-live in seconds (default: 5 minutes)
            dev_mode: If True, cache is disabled (always returns None)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = timedelta(seconds=default_ttl_seconds)
        self.dev_mode = dev_mode
        
        if dev_mode:
            logger.warning("⚠️ DEV_MODE=true - Cache DISABLED")
        else:
            logger.info(f"Cache initialized with TTL: {default_ttl_seconds}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found or expired
        """
        # DEV_MODE: Always return None (cache disabled)
        if self.dev_mode:
            return None
        
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if datetime.now() > entry["expires_at"]:
            logger.info(f"⏰ Cache expired: {key}")
            del self._cache[key]
            return None
        
        logger.info(f"✅ Cache hit: {key}")
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds (uses default if None)
        """
        # DEV_MODE: Skip caching
        if self.dev_mode:
            return
        
        ttl = timedelta(seconds=ttl_seconds) if ttl_seconds else self.default_ttl
        expires_at = datetime.now() + ttl
        
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at
        }
        
        logger.info(f"💾 Cache set: {key} (expires: {expires_at.strftime('%H:%M:%S')})")
    
    def invalidate(self, key: str):
        """
        Remove key from cache.
        
        Args:
            key: Cache key to remove
        """
        if key in self._cache:
            del self._cache[key]
            logger.info(f"🗑️ Cache invalidated: {key}")
    
    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def cleanup_expired(self):
        """Remove all expired entries from cache."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


class DummyCache:
    """
    No-op cache for debugging purposes.
    Used when ENABLE_MEMORY_CACHE=false in system.ini.
    """
    
    def get(self, key: str) -> Optional[Any]:
        """Always return None (cache disabled)."""
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Do nothing (cache disabled)."""
        pass
    
    def invalidate(self, key: str):
        """Do nothing (cache disabled)."""
        pass
    
    def clear(self):
        """Do nothing (cache disabled)."""
        pass
    
    def cleanup_expired(self):
        """Do nothing (cache disabled)."""
        pass


# Global cache instance
_context_cache = None  # Will be initialized on first access


def get_context_cache() -> SimpleCache:
    """
    Get the global context cache instance.
    Respects ENABLE_MEMORY_CACHE from system.ini (P0.17).
    """
    global _context_cache
    
    if _context_cache is None:
        # Import here to avoid circular dependency
        from services.config_service import get_config_service
        
        config = get_config_service()
        
        # Check if DEV_MODE is enabled (highest priority - disables all caches)
        if config.is_dev_mode():
            logger.warning("⚠️ DEV_MODE=true - ALL CACHES DISABLED")
            _context_cache = DummyCache()
        # Check if memory cache is explicitly disabled
        elif not config.get_bool('cache', 'ENABLE_MEMORY_CACHE', default=True):
            logger.warning("⚠️ Memory cache DISABLED (system.ini: ENABLE_MEMORY_CACHE=false)")
            _context_cache = DummyCache()
        else:
            # Get TTL from config
            ttl = config.get_int('cache', 'MEMORY_CACHE_TTL_SECONDS', default=3600)
            _context_cache = SimpleCache(default_ttl_seconds=ttl, dev_mode=False)
            logger.info(f"✅ Memory cache ENABLED (TTL: {ttl}s)")
    
    return _context_cache


# Alias for backward compatibility - call the function to get the cache instance
simple_cache = get_context_cache()
