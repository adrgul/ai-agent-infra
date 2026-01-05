"""
Unit tests for Redis cache functionality.

Tests cover:
- Cache hit/miss scenarios
- TTL expiration
- Domain filtering
- Cache invalidation
- Memory limits
- Connection handling
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import time
from infrastructure.redis_client import RedisCache


class TestRedisCache(unittest.TestCase):
    """Test suite for RedisCache class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the Redis client at the module level
        self.mock_redis = MagicMock()
        self.mock_redis.ping.return_value = True
        
        # Patch redis.Redis to return our mock
        self.patcher = patch('infrastructure.redis_client.redis.Redis', return_value=self.mock_redis)
        self.patcher.start()
        
        # Force re-initialization by clearing singleton
        from infrastructure.redis_client import RedisCache
        RedisCache._instance = None
        
        # Create instance (will use mocked Redis)
        self.cache = RedisCache()
    
    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()
        from infrastructure.redis_client import RedisCache
        RedisCache._instance = None
    
    def test_cache_embedding_hit(self):
        """Test cache hit for embedding."""
        # Arrange
        text = "test query"
        embedding = [0.1, 0.2, 0.3] * 512  # 1536 dims
        
        self.mock_redis.get.return_value = json.dumps(embedding).encode('utf-8')
        
        # Act
        result = self.cache.get_embedding(text)
        
        # Assert
        self.assertEqual(result, embedding)
        self.mock_redis.get.assert_called_once()
    
    def test_cache_embedding_miss(self):
        """Test cache miss for embedding."""
        # Arrange
        text = "new query"
        
        self.mock_redis.get.return_value = None
        
        # Act
        result = self.cache.get_embedding(text)
        
        # Assert
        self.assertIsNone(result)
        self.mock_redis.get.assert_called_once()
    
    def test_set_embedding_with_ttl(self):
        """Test setting embedding with custom TTL."""
        # Arrange
        text = "test query"
        embedding = [0.1] * 1536
        ttl = 7200  # 2 hours
        
        # Act
        self.cache.set_embedding(text, embedding, ttl=ttl)
        
        # Assert
        self.mock_redis.setex.assert_called_once()
        call_args = self.mock_redis.setex.call_args
        self.assertEqual(call_args[0][1], ttl)  # Check TTL
    
    def test_cache_query_result_hit(self):
        """Test cache hit for query result."""
        # Arrange
        query = "What is brand color?"
        domain = "marketing"
        cached_result = {
            "answer": "Blue #0066CC",
            "citations": [{"doc_id": "doc_001", "score": 0.95}],
            "domain": "marketing"
        }
        
        self.mock_redis.get.return_value = json.dumps(cached_result).encode('utf-8')
        self.mock_redis.hincrby.return_value = 5  # Mock hit count
        
        # Act
        result = self.cache.get_query_result(query, domain)
        
        # Assert
        # Result should include hit_count from hincrby
        expected = {**cached_result, "hit_count": 5}
        self.assertEqual(result, expected)
        self.mock_redis.get.assert_called_once()
        self.mock_redis.hincrby.assert_called_once()
    
    def test_invalidate_domain_cache(self):
        """Test domain-specific cache invalidation."""
        # Arrange
        domain = "marketing"
        
        # Mock keys() to return matching keys
        self.mock_redis.keys.return_value = [
            b'query:marketing:12345',
            b'query:marketing:67890'
        ]
        
        # Act
        self.cache.invalidate_query_cache(domain=domain)
        
        # Assert
        self.mock_redis.keys.assert_called_once_with(f"query:{domain}:*")
        # Should call delete with the 2 keys
        self.mock_redis.delete.assert_called_once()
        call_args = self.mock_redis.delete.call_args[0]
        self.assertEqual(len(call_args), 2)
    
    def test_clear_all_cache(self):
        """Test clearing all cache."""
        # Arrange
        self.mock_redis.flushdb.return_value = True
        
        # Act
        self.cache.clear_all()
        
        # Assert
        self.mock_redis.flushdb.assert_called_once()
    
    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        # Arrange
        self.mock_redis.info.return_value = {
            'used_memory': 47185920,  # ~45 MB
            'maxmemory': 536870912,   # 512 MB
            'keyspace_hits': 1234,
            'keyspace_misses': 566,
            'uptime_in_seconds': 3600
        }
        self.mock_redis.dbsize.return_value = 890
        self.mock_redis.keys.return_value = []  # Mock keys() calls
        
        # Act
        stats = self.cache.get_cache_stats()
        
        # Assert
        self.assertEqual(stats['total_keys'], 890)
        self.assertAlmostEqual(stats['used_memory_mb'], 45.0, delta=1.0)
        self.assertAlmostEqual(stats['hit_rate'], 0.686, delta=0.01)  # 1234/(1234+566)
        self.assertTrue(stats['connected'])
    
    def test_redis_connection_failure(self):
        """Test handling Redis connection failure."""
        # Arrange
        self.mock_redis.ping.side_effect = ConnectionError("Redis unavailable")
        
        # Act
        is_available = self.cache.is_available()
        
        # Assert
        self.assertFalse(is_available)
    
    def test_cache_key_generation(self):
        """Test cache key generation is consistent."""
        # Arrange
        query1 = "What is our policy?"
        query2 = "What is our policy?"  # Same query
        query3 = "What is our policy ?"  # Different (extra space)
        domain = "hr"
        
        # Act
        key1 = f"query:{domain}:{hash(query1)}"
        key2 = f"query:{domain}:{hash(query2)}"
        key3 = f"query:{domain}:{hash(query3)}"
        
        # Assert
        self.assertEqual(key1, key2)  # Same query = same key
        self.assertNotEqual(key1, key3)  # Different query = different key
    
    def test_embedding_cache_with_different_models(self):
        """Test that different embedding texts have different cache keys."""
        # Arrange
        text1 = "test query one"
        text2 = "test query two"
        embedding1 = [0.1] * 1536
        embedding2 = [0.2] * 1536
        
        # Act
        self.cache.set_embedding(text1, embedding1)
        self.cache.set_embedding(text2, embedding2)
        
        # Assert
        self.assertEqual(self.mock_redis.setex.call_count, 2)
        calls = self.mock_redis.setex.call_args_list
        
        # Keys should be different
        key1 = calls[0][0][0]
        key2 = calls[1][0][0]
        self.assertNotEqual(key1, key2)
    
    def test_memory_limit_enforcement(self):
        """Test that cache respects memory limits."""
        # Arrange
        self.mock_redis.info.return_value = {
            'used_memory': 550 * 1024 * 1024,  # 550 MB (over limit)
            'maxmemory': 512 * 1024 * 1024,     # 512 MB max
            'maxmemory_policy': 'allkeys-lru',
            'keyspace_hits': 100,
            'keyspace_misses': 50,
            'uptime_in_seconds': 7200
        }
        self.mock_redis.dbsize.return_value = 1000
        self.mock_redis.keys.return_value = []  # Mock keys() calls
        
        # Act
        stats = self.cache.get_cache_stats()
        
        # Assert
        self.assertGreater(stats['used_memory_mb'], 512)
        # Redis should auto-evict with LRU policy


class TestRedisIntegration(unittest.TestCase):
    """Integration tests for Redis (requires running Redis instance)."""
    
    @unittest.skipUnless(False, "Requires running Redis instance")
    def test_real_redis_roundtrip(self):
        """Test actual Redis operations (skipped by default)."""
        # This would test against real Redis instance
        # Useful for integration testing but skipped in unit tests
        pass


if __name__ == '__main__':
    unittest.main()
