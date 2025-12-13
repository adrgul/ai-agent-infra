"""
Vector store interface for SupportAI.

Manages vector database operations for knowledge base search.
"""

import os
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

try:
    import pinecone
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

try:
    import weaviate
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False

try:
    import qdrant_client
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from ..utils.config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Document:
    """Represents a document in the vector store."""

    def __init__(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ):
        self.doc_id = doc_id
        self.content = content
        self.metadata = metadata
        self.embedding = embedding

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding
        }


class VectorStore(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store."""
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> List[Document]:
        """Search for similar documents."""
        pass

    @abstractmethod
    def delete_by_id(self, doc_id: str) -> None:
        """Delete document by ID."""
        pass


class PineconeVectorStore(VectorStore):
    """Pinecone implementation of vector store."""

    def __init__(self):
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone client not available. Install with: pip install pinecone-client")

        self.api_key = settings.pinecone_api_key
        self.environment = settings.pinecone_environment
        self.index_name = settings.pinecone_index_name
        self.dimension = 3072  # text-embedding-3-large

        self.pc = Pinecone(api_key=self.api_key)
        self.index = None
        self._ensure_index()

    def _ensure_index(self):
        """Ensure the index exists."""
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=self.environment.split("-")[-1] if "-" in self.environment else "us-east-1"
                )
            )
            logger.info(f"Created Pinecone index: {self.index_name}")

        self.index = self.pc.Index(self.index_name)

    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to Pinecone."""
        vectors = []
        for doc in documents:
            if doc.embedding:
                vectors.append({
                    "id": doc.doc_id,
                    "values": doc.embedding,
                    "metadata": {
                        **doc.metadata,
                        "content": doc.content
                    }
                })

        if vectors:
            self.index.upsert(vectors=vectors)
            logger.info(f"Added {len(vectors)} documents to Pinecone")

    def search(self, query: str, top_k: int = 10) -> List[Document]:
        """Search Pinecone for similar documents."""
        # Note: This assumes query is already embedded
        # In practice, you'd embed the query first
        # For now, return empty results as embedding is handled elsewhere
        logger.warning("Pinecone search called without embedding - implement embedding logic")
        return []

    def delete_by_id(self, doc_id: str) -> None:
        """Delete document from Pinecone."""
        self.index.delete(ids=[doc_id])
        logger.info(f"Deleted document {doc_id} from Pinecone")


class WeaviateVectorStore(VectorStore):
    """Weaviate implementation of vector store."""

    def __init__(self):
        if not WEAVIATE_AVAILABLE:
            raise ImportError("Weaviate client not available. Install with: pip install weaviate-client")

        self.url = settings.weaviate_url
        self.api_key = settings.weaviate_api_key
        self.class_name = "SupportDocument"

        self.client = weaviate.Client(
            url=self.url,
            auth_client_secret=weaviate.AuthApiKey(api_key=self.api_key) if self.api_key else None
        )

        self._ensure_class()

    def _ensure_class(self):
        """Ensure the document class exists."""
        schema = {
            "class": self.class_name,
            "vectorizer": "none",  # We'll provide vectors
            "properties": [
                {"name": "doc_id", "dataType": ["string"]},
                {"name": "content", "dataType": ["text"]},
                {"name": "title", "dataType": ["string"]},
                {"name": "category", "dataType": ["string"]},
                {"name": "url", "dataType": ["string"]},
            ]
        }

        if not self.client.schema.exists(self.class_name):
            self.client.schema.create_class(schema)
            logger.info(f"Created Weaviate class: {self.class_name}")

    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to Weaviate."""
        with self.client.batch as batch:
            for doc in documents:
                if doc.embedding:
                    properties = {
                        "doc_id": doc.doc_id,
                        "content": doc.content,
                        **doc.metadata
                    }
                    batch.add_data_object(
                        data_object=properties,
                        class_name=self.class_name,
                        vector=doc.embedding
                    )

        logger.info(f"Added {len(documents)} documents to Weaviate")

    def search(self, query: str, top_k: int = 10) -> List[Document]:
        """Search Weaviate for similar documents."""
        logger.warning("Weaviate search called without embedding - implement embedding logic")
        return []

    def delete_by_id(self, doc_id: str) -> None:
        """Delete document from Weaviate."""
        self.client.data_object.delete(
            class_name=self.class_name,
            where={"path": ["doc_id"], "operator": "Equal", "valueString": doc_id}
        )
        logger.info(f"Deleted document {doc_id} from Weaviate")


class QdrantVectorStore(VectorStore):
    """Qdrant implementation of vector store."""

    def __init__(self):
        if not QDRANT_AVAILABLE:
            raise ImportError("Qdrant client not available. Install with: pip install qdrant-client")

        self.url = settings.qdrant_url
        self.api_key = settings.qdrant_api_key
        self.collection_name = "support_kb"
        self.dimension = 3072

        self.client = qdrant_client.QdrantClient(
            url=self.url,
            api_key=self.api_key
        )

        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure the collection exists."""
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "content": qdrant_client.VectorParams(
                        size=self.dimension,
                        distance=qdrant_client.Distance.COSINE
                    )
                }
            )
            logger.info(f"Created Qdrant collection: {self.collection_name}")

    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to Qdrant."""
        points = []
        for doc in documents:
            if doc.embedding:
                points.append({
                    "id": hash(doc.doc_id) % 2**63,  # Simple ID generation
                    "vector": {"content": doc.embedding},
                    "payload": {
                        "doc_id": doc.doc_id,
                        "content": doc.content,
                        **doc.metadata
                    }
                })

        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Added {len(points)} documents to Qdrant")

    def search(self, query: str, top_k: int = 10) -> List[Document]:
        """Search Qdrant for similar documents."""
        logger.warning("Qdrant search called without embedding - implement embedding logic")
        return []

    def delete_by_id(self, doc_id: str) -> None:
        """Delete document from Qdrant."""
        # This is a simplified deletion - in practice you'd need proper ID mapping
        logger.warning("Qdrant delete_by_id not fully implemented")
        logger.info(f"Delete requested for document {doc_id}")


def create_vector_store(provider: str = None) -> VectorStore:
    """
    Factory function to create vector store instance.

    Args:
        provider: Vector store provider ('pinecone', 'weaviate', 'qdrant')

    Returns:
        Vector store instance
    """
    provider = provider or settings.vector_db_provider

    if provider == "pinecone":
        return PineconeVectorStore()
    elif provider == "weaviate":
        return WeaviateVectorStore()
    elif provider == "qdrant":
        return QdrantVectorStore()
    else:
        raise ValueError(f"Unsupported vector store provider: {provider}")


# Global vector store instance
vector_store = create_vector_store()