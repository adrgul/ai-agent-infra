"""
Cache interface following Interface Segregation Principle.
Simple, focused contract for caching operations.
"""
from abc import ABC, abstractmethod
from typing import Optional, Any


class Cache(ABC):
    """
    Abstract cache interface.
    
    Implementations can be in-memory, Redis, or any other backend.
    Nodes depend on this interface, not concrete implementations.
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Store a value in cache.
        
        Args:
            key: Cache key
            value: Value to store
            ttl_seconds: Time to live in seconds (None = use default)
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Remove a key from cache.
        
        Args:
            key: Cache key to delete
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all entries from cache."""
        pass
