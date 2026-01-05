"""Qdrant vector database service.

VERSION COMPATIBILITY:
- qdrant-client and qdrant server: max 1 minor version difference
- Recommended: client ~1.13.0, server v1.13.x

HTTPS CONFIGURATION:
- Local/Docker: https=False (default HTTP on port 6333)
- Qdrant Cloud: https=True (required for cloud instances)
"""

import logging
import uuid
from typing import Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchParams,
)

from ..config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for interacting with Qdrant vector database."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        collection_name: Optional[str] = None,
        api_key: Optional[str] = None,
        https: Optional[bool] = None,
    ):
        """Initialize Qdrant client.

        Args:
            host: Qdrant host address
            port: Qdrant port (default: 6333)
            collection_name: Name of the collection to use
            api_key: API key for Qdrant Cloud (optional)
            https: Use HTTPS connection (False for local, True for cloud)
        """
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self.api_key = api_key or settings.QDRANT_API_KEY

        # ⚠️ CRITICAL: Default to False for local development
        # Set QDRANT_HTTPS=true in .env for Qdrant Cloud
        self.https = https if https is not None else settings.QDRANT_HTTPS

        self.client = AsyncQdrantClient(
            host=self.host,
            port=self.port,
            api_key=self.api_key,
            https=self.https,  # ⚠️ Must be False for local, True for cloud
        )

        logger.info(
            f"Initialized Qdrant client: {self.host}:{self.port} "
            f"(https={'enabled' if self.https else 'disabled'})"
        )

    @staticmethod
    def chunk_id_to_uuid(chunk_id: str) -> str:
        """Convert chunk_id to a deterministic UUID.

        IMPORTANT: Qdrant only accepts UUID or unsigned integer IDs!
        uuid5 is deterministic → same chunk_id = same UUID every time.
        This enables proper upsert behavior (overwrites existing records).

        Args:
            chunk_id: String chunk identifier (e.g., "KB-1234-c-45")

        Returns:
            UUID string that can be used as Qdrant point ID
        """
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

    async def create_collection(
        self,
        vector_size: int = 3072,
        distance: Distance = Distance.COSINE
    ) -> bool:
        """Create a new collection in Qdrant.

        Args:
            vector_size: Dimension of vectors (default: 3072 for text-embedding-3-large)
            distance: Distance metric (COSINE, DOT, EUCLID)

        Returns:
            True if successful

        Raises:
            Exception: If collection creation fails
        """
        try:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance),
            )
            logger.info(f"Created collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        category_filter: Optional[str] = None,
        score_threshold: float = 0.7,
    ) -> list[dict]:
        """Search for similar documents in Qdrant.

        NOTE: qdrant-client >= 1.13 uses query_points() instead of search().

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            category_filter: Optional category to filter by
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of matching documents with scores

        Raises:
            Exception: If search fails
        """
        search_filter = None
        if category_filter:
            search_filter = Filter(
                must=[FieldCondition(key="category", match=MatchValue(value=category_filter))]
            )

        try:
            # qdrant-client >= 1.13: use query_points() instead of search()
            results = await self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,  # NOTE: parameter is 'query', not 'query_vector'
                query_filter=search_filter,
                limit=top_k,
                score_threshold=score_threshold,
                search_params=SearchParams(hnsw_ef=128, exact=False),
            )

            documents = [
                {
                    "doc_id": hit.payload.get("doc_id"),
                    "chunk_id": hit.payload.get("chunk_id"),
                    "title": hit.payload.get("title"),
                    "content": hit.payload.get("content"),
                    "url": hit.payload.get("url"),
                    "score": hit.score,
                    "category": hit.payload.get("category"),
                    "subcategory": hit.payload.get("subcategory"),
                    "doc_type": hit.payload.get("doc_type"),
                }
                for hit in results.points  # NOTE: results.points, not results
            ]

            logger.info(f"Found {len(documents)} documents for query")
            return documents

        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            raise

    async def upsert_documents(
        self,
        documents: list[dict],
        vectors: list[list[float]]
    ) -> bool:
        """Insert or update documents in Qdrant.

        Args:
            documents: List of document payloads with metadata
            vectors: List of embedding vectors (must match documents length)

        Returns:
            True if successful

        Raises:
            ValueError: If documents and vectors lengths don't match
            Exception: If upsert fails
        """
        if len(documents) != len(vectors):
            raise ValueError(
                f"Number of documents ({len(documents)}) must match "
                f"number of vectors ({len(vectors)})"
            )

        points = [
            PointStruct(
                id=self.chunk_id_to_uuid(doc["chunk_id"]),  # UUID conversion!
                vector=vector,
                payload=doc  # Original chunk_id preserved in payload
            )
            for doc, vector in zip(documents, vectors)
        ]

        try:
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} documents to {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Qdrant upsert failed: {e}")
            raise

    async def health_check(self) -> bool:
        """Check Qdrant connection health.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            await self.client.get_collections()
            return True
        except Exception as e:
            logger.warning(f"Qdrant health check failed: {e}")
            return False

    async def collection_exists(self) -> bool:
        """Check if collection exists.

        Returns:
            True if collection exists, False otherwise
        """
        try:
            collections = await self.client.get_collections()
            return any(c.name == self.collection_name for c in collections.collections)
        except Exception:
            return False

    async def delete_collection(self) -> bool:
        """Delete the collection.

        Returns:
            True if successful

        Raises:
            Exception: If deletion fails
        """
        try:
            await self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise

    async def get_collection_info(self) -> dict:
        """Get collection information and statistics.

        Returns:
            Dictionary with collection info
        """
        try:
            info = await self.client.get_collection(collection_name=self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise

    async def close(self) -> None:
        """Close the Qdrant client connection."""
        await self.client.close()
        logger.info("Closed Qdrant client connection")
