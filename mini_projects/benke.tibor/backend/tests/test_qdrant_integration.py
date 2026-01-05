"""
Integration tests for Qdrant RAG client end-to-end flow.
Tests the complete retrieval pipeline with deduplication and ranking.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from domain.models import Citation, DomainType
from infrastructure.qdrant_rag_client import QdrantRAGClient


class TestQdrantRAGIntegration:
    """Integration tests for complete RAG retrieval flow."""
    
    @pytest.fixture
    def mock_qdrant_client(self):
        """Mock Qdrant client with search results."""
        client = Mock()
        
        # Mock search results with duplicate content
        mock_point_1 = Mock()
        mock_point_1.id = "point1"
        mock_point_1.score = 0.95
        mock_point_1.payload = {
            "domain": "marketing",
            "source_file_id": "aurora_guide.pdf",
            "file_name": "Aurora_Digital_Arculati_Kezikonyv_HU.pdf",
            "chunk_index": 0,
            "text": "Elsődleges szín: Éjkék (#0B1C2D)\nMásodlagos szín: Aurora türkiz (#1FA6A3)"
        }
        
        mock_point_2 = Mock()
        mock_point_2.id = "point2"
        mock_point_2.score = 0.92
        mock_point_2.payload = {
            "domain": "marketing",
            "source_file_id": "aurora_guide.docx",
            "file_name": "Aurora_Digital_Arculati_Kezikonyv_HU.docx",
            "chunk_index": 0,
            "text": "Elsődleges szín: Éjkék (#0B1C2D)\nMásodlagos szín: Aurora türkiz (#1FA6A3)"
        }
        
        mock_point_3 = Mock()
        mock_point_3.id = "point3"
        mock_point_3.score = 0.88
        mock_point_3.payload = {
            "domain": "marketing",
            "source_file_id": "aurora_guide.pdf",
            "file_name": "Aurora_Digital_Arculati_Kezikonyv_HU.pdf",
            "chunk_index": 1,
            "text": "Tipográfia: Inter (Regular, Medium, SemiBold)"
        }
        
        client.search.return_value = [mock_point_1, mock_point_2, mock_point_3]
        
        return client
    
    @pytest.fixture
    def mock_embeddings(self):
        """Mock OpenAI embeddings."""
        embeddings = Mock()
        embeddings.embed_query.return_value = [0.1] * 1536
        return embeddings
    
    @pytest.fixture
    def mock_postgres(self):
        """Mock PostgreSQL client."""
        with patch('infrastructure.qdrant_rag_client.postgres_client') as mock_pg:
            mock_pg.is_available.return_value = True
            mock_pg.get_citation_feedback_batch = AsyncMock(return_value={
                "aurora_guide.pdf#chunk0": 85.0,  # High feedback
                "aurora_guide.docx#chunk0": 45.0,  # Medium feedback
                "aurora_guide.pdf#chunk1": None,   # No feedback
            })
            yield mock_pg
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis cache."""
        with patch('infrastructure.qdrant_rag_client.redis_cache') as mock_redis:
            mock_redis.get_query_result.return_value = None  # Cache miss
            mock_redis.get_embedding.return_value = None
            mock_redis.set_embedding.return_value = None
            mock_redis.set_query_result.return_value = None
            yield mock_redis
    
    @pytest.mark.asyncio
    async def test_end_to_end_retrieval_with_deduplication(
        self, 
        mock_qdrant_client, 
        mock_embeddings,
        mock_postgres,
        mock_redis
    ):
        """
        Test complete retrieval flow:
        1. Qdrant search (returns 3 points, 2 are duplicates)
        2. Deduplication (3 → 2 unique)
        3. Feedback ranking (scores adjusted)
        4. Return to user
        """
        rag_client = QdrantRAGClient(qdrant_url="http://mock:6333")
        rag_client.qdrant_client = mock_qdrant_client
        rag_client.embeddings = mock_embeddings
        
        # Execute retrieval
        result = await rag_client._retrieve_from_qdrant(
            query="milyen színek használhatók?",
            top_k=5,
            domain="marketing"
        )
        
        # Verify deduplication: 3 points → 2 unique citations
        # (PDF and DOCX with same content should be deduplicated)
        assert len(result) == 2
        
        # Verify highest-scoring duplicate was kept
        titles = [c.title for c in result]
        assert "Aurora_Digital_Arculati_Kezikonyv_HU.pdf" in titles
        
        # Verify feedback ranking was applied
        # Point 1 (PDF, chunk 0) has 85% feedback → +30% boost
        # Original score: 0.95, boosted: 0.95 * 1.3 = 1.235
        assert result[0].score > 0.95
        
        # Verify unique content is preserved
        content_previews = [c.content[:50] for c in result]
        assert any("Elsődleges szín" in preview for preview in content_previews)
        assert any("Tipográfia" in preview for preview in content_previews)
    
    @pytest.mark.asyncio
    async def test_it_domain_with_overlap_boost(
        self,
        mock_embeddings,
        mock_postgres,
        mock_redis
    ):
        """Test IT domain with section_id extraction and overlap boost."""
        # Mock IT-specific search results
        mock_qdrant = Mock()
        
        mock_point_vpn = Mock()
        mock_point_vpn.id = "vpn_point"
        mock_point_vpn.score = 0.85
        mock_point_vpn.payload = {
            "domain": "it",
            "section_id": "IT-KB-234",
            "text": "[IT-KB-234] VPN kliens nem fut vagy lefagyott",
            "chunk_index": 0
        }
        
        mock_point_network = Mock()
        mock_point_network.id = "network_point"
        mock_point_network.score = 0.90
        mock_point_network.payload = {
            "domain": "it",
            "section_id": "IT-KB-255",
            "text": "[IT-KB-255] Hálózati kapcsolat megszakadt",
            "chunk_index": 0
        }
        
        mock_qdrant.search.return_value = [mock_point_network, mock_point_vpn]
        
        rag_client = QdrantRAGClient(qdrant_url="http://mock:6333")
        rag_client.qdrant_client = mock_qdrant
        rag_client.embeddings = mock_embeddings
        
        # Query with IT-specific terms
        result = await rag_client._retrieve_from_qdrant(
            query="VPN nem működik",
            top_k=5,
            domain="it"
        )
        
        # Verify IT overlap boost reranked results
        # VPN point should be first (query contains "VPN")
        assert result[0].section_id == "IT-KB-234"
        
        # Verify section_id is extracted
        assert all(c.section_id is not None for c in result)
    
    @pytest.mark.asyncio
    async def test_cache_hit_flow(
        self,
        mock_qdrant_client,
        mock_embeddings,
        mock_postgres
    ):
        """Test retrieval with Redis cache hit."""
        with patch('infrastructure.qdrant_rag_client.redis_cache') as mock_redis:
            # Simulate cache hit
            mock_redis.get_query_result.return_value = {
                "doc_ids": ["point1", "point3"],
                "metadata": {"top_score": 0.95}
            }
            
            # Mock retrieve by IDs
            mock_qdrant_client.retrieve.return_value = [
                Mock(
                    id="point1",
                    payload={
                        "domain": "marketing",
                        "source_file_id": "test.pdf",
                        "file_name": "Test.pdf",
                        "text": "Test content",
                        "chunk_index": 0
                    }
                )
            ]
            
            rag_client = QdrantRAGClient(qdrant_url="http://mock:6333")
            rag_client.qdrant_client = mock_qdrant_client
            rag_client.embeddings = mock_embeddings
            
            result = await rag_client._retrieve_from_qdrant(
                query="test query",
                top_k=5,
                domain="marketing"
            )
            
            # Verify cache was used (search not called)
            mock_qdrant_client.search.assert_not_called()
            
            # Verify retrieve was called instead
            mock_qdrant_client.retrieve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_postgres_unavailable_fallback(
        self,
        mock_qdrant_client,
        mock_embeddings,
        mock_redis
    ):
        """Test graceful degradation when PostgreSQL is unavailable."""
        with patch('infrastructure.qdrant_rag_client.postgres_client') as mock_pg:
            mock_pg.is_available.return_value = False
            
            rag_client = QdrantRAGClient(qdrant_url="http://mock:6333")
            rag_client.qdrant_client = mock_qdrant_client
            rag_client.embeddings = mock_embeddings
            
            result = await rag_client._retrieve_from_qdrant(
                query="test query",
                top_k=5,
                domain="marketing"
            )
            
            # Should still return results (without feedback ranking)
            assert len(result) > 0
            
            # Verify feedback ranking was skipped
            mock_pg.get_citation_feedback_batch.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_empty_search_results(
        self,
        mock_embeddings,
        mock_postgres,
        mock_redis
    ):
        """Test handling of empty search results."""
        mock_qdrant = Mock()
        mock_qdrant.search.return_value = []
        
        rag_client = QdrantRAGClient(qdrant_url="http://mock:6333")
        rag_client.qdrant_client = mock_qdrant
        rag_client.embeddings = mock_embeddings
        
        result = await rag_client._retrieve_from_qdrant(
            query="unknown topic",
            top_k=5,
            domain="marketing"
        )
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_feedback_ranking_score_adjustment(
        self,
        mock_embeddings,
        mock_redis
    ):
        """Test that feedback ranking correctly adjusts scores."""
        mock_qdrant = Mock()
        
        # Mock 3 points with different feedback levels
        mock_high_feedback = Mock()
        mock_high_feedback.id = "high"
        mock_high_feedback.score = 0.80
        mock_high_feedback.payload = {
            "domain": "marketing",
            "source_file_id": "doc_high",
            "file_name": "High Feedback Doc",
            "text": "Content with high feedback",
            "chunk_index": 0
        }
        
        mock_low_feedback = Mock()
        mock_low_feedback.id = "low"
        mock_low_feedback.score = 0.85
        mock_low_feedback.payload = {
            "domain": "marketing",
            "source_file_id": "doc_low",
            "file_name": "Low Feedback Doc",
            "text": "Content with low feedback",
            "chunk_index": 0
        }
        
        mock_no_feedback = Mock()
        mock_no_feedback.id = "none"
        mock_no_feedback.score = 0.82
        mock_no_feedback.payload = {
            "domain": "marketing",
            "source_file_id": "doc_none",
            "file_name": "No Feedback Doc",
            "text": "Content with no feedback",
            "chunk_index": 0
        }
        
        mock_qdrant.search.return_value = [
            mock_low_feedback,   # Highest semantic score
            mock_no_feedback,
            mock_high_feedback   # Lowest semantic score
        ]
        
        with patch('infrastructure.qdrant_rag_client.postgres_client') as mock_pg:
            mock_pg.is_available.return_value = True
            mock_pg.get_citation_feedback_batch = AsyncMock(return_value={
                "doc_high#chunk0": 85.0,  # +30% boost
                "doc_low#chunk0": 25.0,   # -20% penalty
                "doc_none#chunk0": None,  # No boost
            })
            
            rag_client = QdrantRAGClient(qdrant_url="http://mock:6333")
            rag_client.qdrant_client = mock_qdrant
            rag_client.embeddings = mock_embeddings
            
            result = await rag_client._retrieve_from_qdrant(
                query="test",
                top_k=5,
                domain="marketing"
            )
            
            # Verify ranking after feedback:
            # high: 0.80 * 1.3 = 1.04
            # none: 0.82 * 1.0 = 0.82
            # low: 0.85 * 0.8 = 0.68
            assert result[0].title == "High Feedback Doc"  # Boosted to first
            assert result[1].title == "No Feedback Doc"    # Neutral
            assert result[2].title == "Low Feedback Doc"   # Penalized to last
