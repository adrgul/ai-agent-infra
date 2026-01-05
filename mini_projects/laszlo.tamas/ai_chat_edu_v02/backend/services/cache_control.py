"""
Cache Control Service - P0.17 Phase 2
Centralized cache management for all cache layers.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from services.cache_service import get_context_cache
from services.config_service import get_config_service
from database.pg_init import get_db_connection

logger = logging.getLogger(__name__)


class CacheControl:
    """Centralized cache control for all cache layers."""
    
    def __init__(self):
        self.config = get_config_service()
        self.cache = get_context_cache()
    
    # ============================================================================
    # Configuration Checks
    # ============================================================================
    
    def is_memory_cache_enabled(self) -> bool:
        """Check if in-memory cache (Tier 1) is enabled."""
        return self.config.get_bool('cache', 'ENABLE_MEMORY_CACHE', default=True)
    
    def is_db_cache_enabled(self) -> bool:
        """Check if PostgreSQL cache (Tier 2) is enabled."""
        return self.config.get_bool('cache', 'ENABLE_DB_CACHE', default=True)
    
    def is_browser_cache_enabled(self) -> bool:
        """Check if browser HTTP cache (Tier 3) is enabled."""
        return self.config.get_bool('cache', 'ENABLE_BROWSER_CACHE', default=True)
    
    def is_llm_cache_enabled(self) -> bool:
        """Check if OpenAI LLM prompt cache (Tier 4) is enabled."""
        return self.config.get_bool('cache', 'ENABLE_LLM_CACHE', default=False)
    
    def get_memory_cache_ttl(self) -> int:
        """Get memory cache TTL in seconds."""
        return self.config.get_int('cache', 'MEMORY_CACHE_TTL_SECONDS', default=3600)
    
    def is_cache_debug_enabled(self) -> bool:
        """Check if cache debug mode is enabled."""
        return self.config.get_bool('cache', 'MEMORY_CACHE_DEBUG', default=False)
    
    # ============================================================================
    # Statistics
    # ============================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics for all layers.
        
        Returns:
            {
                "memory_cache": {...},
                "db_cache": {...},
                "config": {...},
                "timestamp": "2026-01-02T12:34:56"
            }
        """
        return {
            "memory_cache": self._get_memory_cache_stats(),
            "db_cache": self._get_db_cache_stats(),
            "config": self._get_cache_config(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_memory_cache_stats(self) -> Dict[str, Any]:
        """Get in-memory cache statistics (Tier 1)."""
        enabled = self.is_memory_cache_enabled()
        
        if not enabled:
            return {
                "enabled": False,
                "size": 0,
                "keys": [],
                "ttl_seconds": 0
            }
        
        # Access internal cache dict
        cache_dict = self.cache._cache if hasattr(self.cache, '_cache') else {}
        
        return {
            "enabled": True,
            "size": len(cache_dict),
            "keys": list(cache_dict.keys()),
            "ttl_seconds": self.get_memory_cache_ttl(),
            "debug_mode": self.is_cache_debug_enabled()
        }
    
    def _get_db_cache_stats(self) -> Dict[str, Any]:
        """Get PostgreSQL cache statistics (Tier 2)."""
        enabled = self.is_db_cache_enabled()
        
        if not enabled:
            return {
                "enabled": False,
                "cached_users": 0,
                "total_entries": 0
            }
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Count unique users with cached prompts
                    cursor.execute("""
                        SELECT 
                            COUNT(DISTINCT user_id) as cached_users,
                            COUNT(*) as total_entries
                        FROM user_prompt_cache
                    """)
                    result = cursor.fetchone()
                    
                    return {
                        "enabled": True,
                        "cached_users": result['cached_users'] if result else 0,
                        "total_entries": result['total_entries'] if result else 0
                    }
        except Exception as e:
            logger.error(f"Failed to get DB cache stats: {e}")
            return {
                "enabled": True,
                "cached_users": 0,
                "total_entries": 0,
                "error": str(e)
            }
    
    def _get_cache_config(self) -> Dict[str, bool]:
        """Get current cache configuration from system.ini."""
        return {
            "memory_enabled": self.is_memory_cache_enabled(),
            "db_enabled": self.is_db_cache_enabled(),
            "browser_enabled": self.is_browser_cache_enabled(),
            "llm_enabled": self.is_llm_cache_enabled()
        }
    
    # ============================================================================
    # Cache Invalidation
    # ============================================================================
    
    def invalidate_user(self, user_id: int) -> Dict[str, Any]:
        """
        Invalidate all caches for a specific user.
        
        Args:
            user_id: User ID to invalidate
            
        Returns:
            Operation result with counts
        """
        result = {
            "user_id": user_id,
            "memory_cleared": 0,
            "db_cleared": 0
        }
        
        try:
            # Clear memory cache
            if self.is_memory_cache_enabled():
                memory_keys = [
                    f"system_prompt:{user_id}",
                    f"user:{user_id}"
                ]
                for key in memory_keys:
                    if hasattr(self.cache, 'invalidate'):
                        self.cache.invalidate(key)
                        result["memory_cleared"] += 1
                        logger.info(f"🗑️ Memory cache cleared: {key}")
            
            # Clear DB cache
            if self.is_db_cache_enabled():
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "DELETE FROM user_prompt_cache WHERE user_id = %s",
                            (user_id,)
                        )
                        result["db_cleared"] = cursor.rowcount
                        conn.commit()
                        logger.info(f"🗑️ DB cache cleared for user {user_id}: {cursor.rowcount} entries")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to invalidate user cache: {e}")
            result["error"] = str(e)
            return result
    
    def invalidate_tenant(self, tenant_id: int) -> Dict[str, Any]:
        """
        Invalidate all caches for a tenant and its users.
        
        Args:
            tenant_id: Tenant ID to invalidate
            
        Returns:
            Operation result with counts
        """
        result = {
            "tenant_id": tenant_id,
            "users_affected": 0,
            "memory_cleared": 0,
            "db_cleared": 0
        }
        
        try:
            # Get all users in tenant
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT user_id FROM users WHERE tenant_id = %s",
                        (tenant_id,)
                    )
                    users = cursor.fetchall()
            
            # Invalidate each user
            for user in users:
                user_result = self.invalidate_user(user['user_id'])
                result["users_affected"] += 1
                result["memory_cleared"] += user_result.get("memory_cleared", 0)
                result["db_cleared"] += user_result.get("db_cleared", 0)
            
            # Clear tenant cache
            if self.is_memory_cache_enabled():
                tenant_key = f"tenant:{tenant_id}"
                if hasattr(self.cache, 'invalidate'):
                    self.cache.invalidate(tenant_key)
                    result["memory_cleared"] += 1
                    logger.info(f"🗑️ Memory cache cleared: {tenant_key}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to invalidate tenant cache: {e}")
            result["error"] = str(e)
            return result
    
    def clear_all(self) -> Dict[str, Any]:
        """
        Clear ALL cache layers (memory + DB).
        WARNING: This is a destructive operation!
        
        Returns:
            Operation result with counts
        """
        result = {
            "memory_cleared": False,
            "db_cleared": 0
        }
        
        try:
            # Clear memory cache
            if self.is_memory_cache_enabled():
                if hasattr(self.cache, 'clear'):
                    self.cache.clear()
                    result["memory_cleared"] = True
                    logger.warning("🗑️ ALL memory cache cleared!")
            
            # Clear DB cache
            if self.is_db_cache_enabled():
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("DELETE FROM user_prompt_cache")
                        result["db_cleared"] = cursor.rowcount
                        conn.commit()
                        logger.warning(f"🗑️ ALL DB cache cleared! ({cursor.rowcount} entries)")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to clear all caches: {e}")
            result["error"] = str(e)
            return result


# Singleton instance
_cache_control_instance: Optional[CacheControl] = None


def get_cache_control() -> CacheControl:
    """Get or create the singleton CacheControl instance."""
    global _cache_control_instance
    if _cache_control_instance is None:
        _cache_control_instance = CacheControl()
    return _cache_control_instance
