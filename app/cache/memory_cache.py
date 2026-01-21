"""
In-memory cache implementation with TTL support.
"""
import asyncio
import time
from typing import Optional, Any, Dict
from dataclasses import dataclass
from app.cache.interfaces import Cache
from app.config import settings


@dataclass
class CacheEntry:
    """Cache entry with value and expiration."""
    value: Any
    expires_at: float  # Unix timestamp


class MemoryCache(Cache):
    """
    Simple in-memory cache with TTL.
    
    Features:
    - TTL-based expiration
    - Automatic cleanup of expired entries
    - Thread-safe operations
    - Size limit enforcement
    
    This demonstrates the Open/Closed Principle: can be swapped
    for Redis or other implementations without changing callers.
    """
    
    def __init__(self, default_ttl_seconds: Optional[int] = None, max_size: int = 1000):
        """
        Initialize memory cache.
        
        Args:
            default_ttl_seconds: Default TTL (defaults to config)
            max_size: Maximum number of entries
        """
        self.default_ttl = default_ttl_seconds or settings.cache_ttl_seconds
        self.max_size = max_size
        self._store: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache, returning None if expired or missing."""
        async with self._lock:
            entry = self._store.get(key)
            
            if entry is None:
                return None
            
            # Check expiration
            if time.time() > entry.expires_at:
                del self._store[key]
                return None
            
            return entry.value
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store value in cache with TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expires_at = time.time() + ttl
        
        async with self._lock:
            # Enforce size limit
            if len(self._store) >= self.max_size and key not in self._store:
                # Simple eviction: remove oldest (first) entry
                oldest_key = next(iter(self._store))
                del self._store[oldest_key]
            
            self._store[key] = CacheEntry(value=value, expires_at=expires_at)
    
    async def delete(self, key: str) -> None:
        """Remove key from cache."""
        async with self._lock:
            self._store.pop(key, None)
    
    async def clear(self) -> None:
        """Clear all entries."""
        async with self._lock:
            self._store.clear()
    
    async def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        async with self._lock:
            now = time.time()
            expired_keys = [
                key for key, entry in self._store.items()
                if now > entry.expires_at
            ]
            
            for key in expired_keys:
                del self._store[key]
            
            return len(expired_keys)
    
    def size(self) -> int:
        """Get current number of entries."""
        return len(self._store)
