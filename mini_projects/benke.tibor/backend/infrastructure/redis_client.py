"""
Redis cache manager for embeddings and query results.

Provides caching layers:
1. Embedding cache: Query text → vector embeddings
2. Query result cache: Query + domain → top document IDs
3. Statistics tracking: Hit counts, cache efficiency
"""
import os
import redis
import hashlib
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis cache manager (Singleton pattern).
    
    Caching strategy:
    - Embedding cache: 7 days TTL, LRU eviction
    - Query result cache: 24 hours TTL
    - Max memory: 512MB with allkeys-lru policy
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        try:
            self.client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=0,
                decode_responses=False,  # Binary for embeddings
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            self.client.ping()
            self._initialized = True
            logger.info("✅ Redis client initialized successfully")
        except redis.ConnectionError as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Cache will be disabled.")
            self.client = None
            self._initialized = True
        except Exception as e:
            logger.error(f"❌ Redis initialization error: {e}")
            self.client = None
            self._initialized = True
    
    def is_available(self) -> bool:
        """Check if Redis is available."""
        if self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except Exception:
            return False
    
    @staticmethod
    def _hash_query(query: str) -> str:
        """Create SHA256 hash of normalized query."""
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    # ========== EMBEDDING CACHE ==========
    
    def get_embedding(self, query: str) -> Optional[List[float]]:
        """
        Get cached embedding for query.
        
        Args:
            query: Query text
            
        Returns:
            Embedding vector or None if not cached
        """
        if not self.is_available():
            return None
            
        key = f"emb:{self._hash_query(query)}"
        try:
            data = self.client.get(key)
            if data:
                logger.info(f"✅ Embedding cache HIT: {query[:50]}...")
                return json.loads(data)
            logger.debug(f"❌ Embedding cache MISS: {query[:50]}...")
            return None
        except Exception as e:
            logger.error(f"Redis get_embedding error: {e}")
            return None
    
    def set_embedding(
        self, 
        query: str, 
        embedding: List[float], 
        ttl: int = 604800  # 7 days
    ):
        """
        Cache embedding vector.
        
        Args:
            query: Query text
            embedding: Vector embedding (1536 floats for OpenAI)
            ttl: Time to live in seconds (default: 7 days)
        """
        if not self.is_available():
            return
            
        key = f"emb:{self._hash_query(query)}"
        try:
            self.client.setex(
                key,
                ttl,
                json.dumps(embedding)
            )
            size_kb = len(json.dumps(embedding)) / 1024
            logger.info(f"💾 Embedding cached: {query[:50]}... ({size_kb:.1f}KB)")
        except Exception as e:
            logger.error(f"Redis set_embedding error: {e}")
    
    # ========== QUERY RESULT CACHE ==========
    
    def get_query_result(self, query: str, domain: str) -> Optional[Dict[str, Any]]:
        """
        Get cached query result (document IDs + metadata).
        
        Args:
            query: Query text
            domain: Domain filter (hr, marketing, etc.)
            
        Returns:
            {
                "doc_ids": [123, 456, 789],
                "query": "original query",
                "domain": "hr",
                "metadata": {...},
                "cached_at": "2024-12-17T10:30:00",
                "hit_count": 5
            }
        """
        if not self.is_available():
            return None
            
        key = f"query:{domain}:{self._hash_query(query)}"
        try:
            data = self.client.get(key)
            if data:
                result = json.loads(data)
                # Increment hit count
                stats_key = f"{key}:stats"
                hit_count = self.client.hincrby(stats_key, "hits", 1)
                result["hit_count"] = hit_count
                
                logger.info(
                    f"✅ Query cache HIT: {query[:50]}... "
                    f"(hits: {hit_count}, docs: {len(result.get('doc_ids', []))})"
                )
                return result
            logger.debug(f"❌ Query cache MISS: {query[:50]}...")
            return None
        except Exception as e:
            logger.error(f"Redis get_query_result error: {e}")
            return None
    
    def set_query_result(
        self,
        query: str,
        domain: str,
        doc_ids: List[int],
        metadata: Dict[str, Any],
        ttl: int = 86400  # 24 hours
    ):
        """
        Cache query result.
        
        Args:
            query: Query text
            domain: Domain filter
            doc_ids: List of Qdrant document IDs
            metadata: Additional metadata (scores, etc.)
            ttl: Time to live in seconds (default: 24 hours)
        """
        if not self.is_available():
            return
            
        key = f"query:{domain}:{self._hash_query(query)}"
        try:
            data = {
                "doc_ids": doc_ids,
                "query": query,
                "domain": domain,
                "metadata": metadata,
                "cached_at": datetime.utcnow().isoformat()
            }
            
            # Set query data with TTL
            self.client.setex(key, ttl, json.dumps(data))
            
            # Initialize stats (longer TTL to track popularity)
            stats_key = f"{key}:stats"
            self.client.hset(stats_key, "hits", 0)
            self.client.expire(stats_key, ttl)
            
            logger.info(
                f"💾 Query result cached: {query[:50]}... "
                f"→ {len(doc_ids)} docs (TTL: {ttl/3600:.1f}h)"
            )
        except Exception as e:
            logger.error(f"Redis set_query_result error: {e}")
    
    def invalidate_query_cache(self, domain: str = None):
        """
        Invalidate query result cache (e.g., after document update).
        
        Args:
            domain: If specified, only invalidate this domain's cache
        """
        if not self.is_available():
            return
            
        try:
            if domain:
                pattern = f"query:{domain}:*"
            else:
                pattern = "query:*"
            
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.info(f"🗑️ Invalidated {len(keys)} query cache entries (domain: {domain or 'all'})")
        except Exception as e:
            logger.error(f"Redis invalidate error: {e}")
    
    # ========== STATISTICS ==========
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get overall cache statistics.
        
        Returns:
            {
                "connected": True,
                "used_memory_mb": 45.2,
                "total_keys": 1234,
                "hit_rate": 0.78,
                "embedding_keys": 890,
                "query_keys": 344
            }
        """
        if not self.is_available():
            return {"connected": False, "error": "Redis not available"}
            
        try:
            info = self.client.info()
            
            # Count keys by type
            emb_keys = len(self.client.keys("emb:*"))
            query_keys = len(self.client.keys("query:*"))
            
            return {
                "connected": True,
                "used_memory_mb": round(info['used_memory'] / 1024 / 1024, 2),
                "total_keys": self.client.dbsize(),
                "hit_rate": round(
                    info.get('keyspace_hits', 0) / 
                    max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0)),
                    3
                ),
                "embedding_keys": emb_keys,
                "query_keys": query_keys,
                "uptime_hours": round(info['uptime_in_seconds'] / 3600, 1)
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {"connected": False, "error": str(e)}
    
    def get_top_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most frequently accessed queries.
        
        Args:
            limit: Number of top queries to return
            
        Returns:
            List of {query, domain, hits, cached_at}
        """
        if not self.is_available():
            return []
            
        try:
            queries = []
            
            # Get all query keys
            for key in self.client.keys("query:*:stats"):
                # Extract query data key
                data_key = key.decode().replace(":stats", "")
                
                # Get hit count
                hits = int(self.client.hget(key, "hits") or 0)
                
                # Get query data
                data = self.client.get(data_key)
                if data:
                    query_data = json.loads(data)
                    queries.append({
                        "query": query_data["query"],
                        "domain": query_data["domain"],
                        "hits": hits,
                        "cached_at": query_data["cached_at"]
                    })
            
            # Sort by hits and return top N
            queries.sort(key=lambda x: x["hits"], reverse=True)
            return queries[:limit]
        except Exception as e:
            logger.error(f"Redis get_top_queries error: {e}")
            return []
    
    def clear_all(self):
        """Clear all cache (use with caution!)."""
        if not self.is_available():
            return
            
        try:
            self.client.flushdb()
            logger.warning("🗑️ All cache cleared!")
        except Exception as e:
            logger.error(f"Redis clear error: {e}")


# Singleton instance
redis_cache = RedisCache()
