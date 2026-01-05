"""
Unit tests for enhanced domain interfaces.
Tests ABC interface contracts and implementations.
"""
import pytest
from abc import ABC
from domain.interfaces import (
    IEmbeddingService,
    IVectorStore,
    IFeedbackStore,
    IRAGClient
)


class TestInterfaceDefinitions:
    """Test that interfaces are properly defined as ABCs."""
    
    def test_embedding_service_is_abstract(self):
        """Test IEmbeddingService is an abstract base class."""
        assert issubclass(IEmbeddingService, ABC)
        
        # Should not be instantiable
        with pytest.raises(TypeError):
            IEmbeddingService()
    
    def test_vector_store_is_abstract(self):
        """Test IVectorStore is an abstract base class."""
        assert issubclass(IVectorStore, ABC)
        
        with pytest.raises(TypeError):
            IVectorStore()
    
    def test_feedback_store_is_abstract(self):
        """Test IFeedbackStore is an abstract base class."""
        assert issubclass(IFeedbackStore, ABC)
        
        with pytest.raises(TypeError):
            IFeedbackStore()
    
    def test_rag_client_is_abstract(self):
        """Test IRAGClient is an abstract base class."""
        assert issubclass(IRAGClient, ABC)
        
        with pytest.raises(TypeError):
            IRAGClient()


class TestEmbeddingServiceInterface:
    """Test IEmbeddingService interface contract."""
    
    def test_embedding_service_has_required_methods(self):
        """Test IEmbeddingService defines required abstract methods."""
        required_methods = ['get_embedding', 'get_embeddings_batch', 'is_available']
        
        for method_name in required_methods:
            assert hasattr(IEmbeddingService, method_name), \
                f"IEmbeddingService should define {method_name}"
    
    def test_embedding_service_implementation_requires_all_methods(self):
        """Test that implementing IEmbeddingService requires all abstract methods."""
        
        # Missing methods should fail
        with pytest.raises(TypeError):
            class IncompleteEmbedding(IEmbeddingService):
                def get_embedding(self, text):
                    return []
                # Missing get_embeddings_batch and is_available
            
            IncompleteEmbedding()
    
    def test_embedding_service_complete_implementation(self):
        """Test that complete implementation works."""
        
        class CompleteEmbedding(IEmbeddingService):
            def get_embedding(self, text):
                return [0.1, 0.2, 0.3]
            
            def get_embeddings_batch(self, texts):
                return [[0.1, 0.2] for _ in texts]
            
            def is_available(self):
                return True
        
        # Should instantiate successfully
        service = CompleteEmbedding()
        assert service.is_available() is True
        assert service.get_embedding("test") == [0.1, 0.2, 0.3]


class TestVectorStoreInterface:
    """Test IVectorStore interface contract."""
    
    def test_vector_store_has_required_methods(self):
        """Test IVectorStore defines required abstract methods."""
        required_methods = ['search', 'retrieve', 'upsert', 'is_available']
        
        for method_name in required_methods:
            assert hasattr(IVectorStore, method_name), \
                f"IVectorStore should define {method_name}"
    
    def test_vector_store_complete_implementation(self):
        """Test complete IVectorStore implementation."""
        
        class TestVectorStore(IVectorStore):
            async def search(self, query_embedding, collection, limit=5, filters=None):
                return []
            
            async def retrieve(self, query, collection, limit=5, filters=None):
                return []
            
            async def upsert(self, collection, documents):
                return True
            
            def is_available(self):
                return True
        
        store = TestVectorStore()
        assert store.is_available() is True


class TestFeedbackStoreInterface:
    """Test IFeedbackStore interface contract."""
    
    def test_feedback_store_has_required_methods(self):
        """Test IFeedbackStore defines required abstract methods."""
        required_methods = [
            'get_citation_feedback_batch',
            'get_citation_feedback_percentage',
            'record_feedback',
            'is_available'
        ]
        
        for method_name in required_methods:
            assert hasattr(IFeedbackStore, method_name), \
                f"IFeedbackStore should define {method_name}"
    
    def test_feedback_store_complete_implementation(self):
        """Test complete IFeedbackStore implementation."""
        
        class TestFeedbackStore(IFeedbackStore):
            async def get_citation_feedback_batch(self, citation_ids, domain):
                return {}
            
            async def get_citation_feedback_percentage(self, citation_id, domain):
                return 75.0
            
            async def record_feedback(self, citation_id, domain, feedback_type, user_id=None):
                return True
            
            def is_available(self):
                return True
        
        store = TestFeedbackStore()
        assert store.is_available() is True


class TestRAGClientInterface:
    """Test IRAGClient interface contract."""
    
    def test_rag_client_has_required_methods(self):
        """Test IRAGClient defines required abstract methods."""
        required_methods = ['retrieve_for_domain', 'retrieve', 'is_available']
        
        for method_name in required_methods:
            assert hasattr(IRAGClient, method_name), \
                f"IRAGClient should define {method_name}"
    
    def test_rag_client_complete_implementation(self):
        """Test complete IRAGClient implementation."""
        
        class TestRAGClient(IRAGClient):
            async def retrieve_for_domain(self, domain, query, top_k=5):
                return []
            
            async def retrieve(self, query, domain, top_k=5, apply_feedback_boost=True):
                return []
            
            def is_available(self):
                return True
        
        client = TestRAGClient()
        assert client.is_available() is True


class TestInterfaceIntegration:
    """Integration tests for interface usage."""
    
    def test_qdrant_rag_client_implements_interface(self):
        """Test that QdrantRAGClient properly implements IRAGClient."""
        from infrastructure.qdrant_rag_client import QdrantRAGClient
        
        # Should be a subclass
        assert issubclass(QdrantRAGClient, IRAGClient)
        
        # Should have all required methods
        required_methods = ['retrieve_for_domain', 'retrieve', 'is_available']
        for method in required_methods:
            assert hasattr(QdrantRAGClient, method)
    
    def test_interface_type_hints(self):
        """Test that interfaces can be used for type hints."""
        
        def process_embeddings(service: IEmbeddingService) -> list:
            return service.get_embedding("test")
        
        def search_vector_store(store: IVectorStore) -> bool:
            return store.is_available()
        
        # Type hints should work
        assert 'service' in process_embeddings.__annotations__
        assert 'store' in search_vector_store.__annotations__
