"""Qdrant vector database service."""

import logging
import os
import uuid
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)

# Configuration - NO DEFAULT VALUES, must be set in .env
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT_STR = os.getenv("QDRANT_PORT")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_USE_HTTPS_STR = os.getenv("QDRANT_USE_HTTPS")
QDRANT_COLLECTION_PREFIX = os.getenv("QDRANT_COLLECTION_PREFIX")

if not all([QDRANT_HOST, QDRANT_PORT_STR, QDRANT_USE_HTTPS_STR, QDRANT_COLLECTION_PREFIX]):
    raise ValueError("Qdrant configuration missing! Check .env file for: QDRANT_HOST, QDRANT_PORT, QDRANT_USE_HTTPS, QDRANT_COLLECTION_PREFIX")

QDRANT_PORT = int(QDRANT_PORT_STR)
QDRANT_USE_HTTPS = QDRANT_USE_HTTPS_STR.lower() == "true"

# Collection names
COLLECTION_DOCUMENT_CHUNKS = f"{QDRANT_COLLECTION_PREFIX}_document_chunks"
COLLECTION_LONG_TERM_MEMORIES = f"{QDRANT_COLLECTION_PREFIX}_longterm_chat_memory"
COLLECTION_PRODUCT_KNOWLEDGE = f"{QDRANT_COLLECTION_PREFIX}_product_knowledge"


class QdrantService:
    """Service for interacting with Qdrant vector database."""
    
    def __init__(self):
        from .config_service import get_config_service
        
        if not QDRANT_HOST:
            raise ValueError("QDRANT_HOST environment variable is required")
        
        # Load from system.ini
        config = get_config_service()
        self.vector_size = config.get_embedding_dimensions()
        self.default_limit = config.get_top_k_documents()
        self.default_score_threshold = config.get_min_score_threshold()
        self.upload_batch_size = config.get_qdrant_upload_batch_size()
        
        # Build URL
        protocol = "https" if QDRANT_USE_HTTPS else "http"
        url = f"{protocol}://{QDRANT_HOST}:{QDRANT_PORT}"
        
        self.client = QdrantClient(
            url=url,
            api_key=QDRANT_API_KEY
        )
        
        logger.info(
            f"QdrantService initialized: url={url}, "
            f"prefix={QDRANT_COLLECTION_PREFIX}, "
            f"batch_size={self.upload_batch_size}"
        )
        
        # Ensure collections exist
        self._ensure_collection(COLLECTION_DOCUMENT_CHUNKS)
        self._ensure_collection(COLLECTION_LONG_TERM_MEMORIES)
    
    def _ensure_collection(self, collection_name: str):
        """
        Ensure a collection exists, create if not.
        
        Args:
            collection_name: Name of the collection
        """
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            
            if not exists:
                # Try to create, but don't fail if API key lacks global access
                try:
                    logger.info(f"Creating collection: {collection_name}")
                    
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=self.vector_size,
                            distance=Distance.COSINE
                        )
                    )
                    
                    logger.info(f"Collection created: {collection_name}")
                except Exception as create_error:
                    logger.warning(
                        f"Cannot create collection {collection_name}: {create_error}. "
                        f"Collection might already exist or API key lacks global access. "
                        f"Continuing..."
                    )
            else:
                logger.info(f"Collection exists: {collection_name}")
        
        except Exception as e:
            logger.error(f"Failed to ensure collection {collection_name}: {e}")
            raise
    
    def upsert_document_chunks(
        self,
        chunks: List[Dict],
        batch_size: int = 50
    ) -> List[Dict]:
        """
        Insert or update document chunks in Qdrant with batching.
        
        Args:
            chunks: List of dicts with:
                - chunk_id: int (PostgreSQL chunk ID)
                - embedding: List[float] (3072 dim)
                - tenant_id: int
                - document_id: int                - user_id: int | None (document owner for private docs)
                - visibility: str ('private' | 'tenant')                - content: str (for preview in payload)
            batch_size: Number of chunks to upload per batch (default: 50)
        
        Returns:
            List of dicts with chunk_id and qdrant_point_id
            [{"chunk_id": int, "qdrant_point_id": str}, ...]
        
        Raises:
            Exception: If upsert fails
        """
        if not chunks:
            return []
        
        total_chunks = len(chunks)
        logger.info(f"Upserting {total_chunks} chunks to Qdrant in batches of {batch_size}")
        
        all_results = []
        
        # Process in batches to avoid Qdrant payload size limit (32 MB)
        for batch_start in range(0, total_chunks, batch_size):
            batch_end = min(batch_start + batch_size, total_chunks)
            batch = chunks[batch_start:batch_end]
            
            batch_num = (batch_start // batch_size) + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)")
            
            points = []
            batch_results = []
            
            for chunk in batch:
                # Generate UUID for Qdrant point
                point_id = str(uuid.uuid4())
                
                # Create point
                point = PointStruct(
                    id=point_id,
                    vector=chunk["embedding"],
                    payload={
                        "chunk_id": chunk["chunk_id"],
                        "tenant_id": chunk["tenant_id"],
                        "document_id": chunk["document_id"],
                        "user_id": chunk.get("user_id"),  # Document owner (None for tenant docs)
                        "visibility": chunk.get("visibility", "tenant"),  # 'private' or 'tenant'
                        "content_preview": chunk["content"][:200]  # First 200 chars
                    }
                )
                
                points.append(point)
                batch_results.append({
                    "chunk_id": chunk["chunk_id"],
                    "qdrant_point_id": point_id
                })
            
            try:
                # Batch upsert
                self.client.upsert(
                    collection_name=COLLECTION_DOCUMENT_CHUNKS,
                    points=points
                )
                
                logger.info(f"Successfully upserted batch {batch_num}/{total_batches} ({len(points)} points)")
                all_results.extend(batch_results)
                
            except Exception as e:
                logger.error(f"Qdrant upsert failed for batch {batch_num}/{total_batches}: {e}", exc_info=True)
                raise
        
        logger.info(f"✅ All {total_chunks} chunks successfully uploaded to Qdrant")
        return all_results
    
    def search_document_chunks(
        self,
        query_vector: List[float],
        tenant_id: int,
        user_id: int,
        limit: int = None,
        score_threshold: float = None
    ) -> List[Dict]:
        """
        Search for similar document chunks with access control.
        
        Returns only chunks the user has permission to see:
        - Private documents owned by the user
        - Tenant-wide documents
        
        Args:
            query_vector: Query embedding (3072 dim)
            tenant_id: Tenant ID filter
            user_id: User ID (for private document access control)
            limit: Maximum results to return (default from system.ini)
            score_threshold: Minimum similarity score (default from system.ini)
        
        Returns:
            List of search results with chunk_id, document_id, score, content_preview
        """
        # Use system.ini defaults if not provided
        if limit is None:
            limit = self.default_limit
        if score_threshold is None:
            score_threshold = self.default_score_threshold
        
        try:
            results = self.client.search(
                collection_name=COLLECTION_DOCUMENT_CHUNKS,
                query_vector=query_vector,
                query_filter={
                    "must": [
                        {
                            "key": "tenant_id",
                            "match": {"value": tenant_id}
                        },
                        {
                            "should": [
                                # Private doc owned by user
                                {
                                    "must": [
                                        {"key": "visibility", "match": {"value": "private"}},
                                        {"key": "user_id", "match": {"value": user_id}}
                                    ]
                                },
                                # Tenant-wide doc
                                {"key": "visibility", "match": {"value": "tenant"}}
                            ]
                        }
                    ]
                },
                limit=limit,
                score_threshold=score_threshold
            )
            
            logger.info(
                f"Qdrant search: {len(results)} results "
                f"(tenant={tenant_id}, limit={limit}, threshold={score_threshold})"
            )
            
            return [
                {
                    "chunk_id": hit.payload["chunk_id"],
                    "document_id": hit.payload["document_id"],
                    "score": hit.score,
                    "content_preview": hit.payload.get("content_preview", "")
                }
                for hit in results
            ]
        
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}", exc_info=True)
            raise
    
    # ===== LONG-TERM MEMORY METHODS =====
    
    def upsert_long_term_memory(
        self,
        tenant_id: int,
        user_id: int,
        session_id: str,
        memory_type: str,
        ltm_id: int,
        content_full: str,
        embedding_vector: List[float]
    ) -> str:
        """
        Store long-term memory in Qdrant.
        
        Args:
            tenant_id: Tenant ID (for filtering)
            user_id: User ID (for filtering)
            session_id: Source session ID
            memory_type: "session_summary" or "explicit_fact"
            ltm_id: PostgreSQL long_term_memories.id (for retrieval)
            content_full: Full text (preview extracted here)
            embedding_vector: Embedding of the content
        
        Returns:
            UUID of the created point
        
        Payload structure:
            {
                "tenant_id": int,
                "user_id": int,
                "session_id": str,
                "memory_type": str,
                "ltm_id": int,  # PostgreSQL reference
                "content_preview": str,  # First 200 chars (DEBUG only)
                "created_at": ISO timestamp
            }
        
        Note: content_preview is for debugging/monitoring only.
              LLM workflows must load full content from PostgreSQL via ltm_id.
        """
        from datetime import datetime
        
        point_id = str(uuid.uuid4())
        
        try:
            self.client.upsert(
                collection_name=COLLECTION_LONG_TERM_MEMORIES,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding_vector,
                        payload={
                            "tenant_id": tenant_id,
                            "user_id": user_id,
                            "session_id": session_id,
                            "memory_type": memory_type,
                            "ltm_id": ltm_id,
                            "content_preview": content_full[:200],  # Debug only
                            "created_at": datetime.now().isoformat()
                        }
                    )
                ]
            )
            
            logger.info(
                f"Long-term memory stored: ltm_id={ltm_id}, "
                f"type={memory_type}, point_id={point_id}"
            )
            return point_id
        
        except Exception as e:
            logger.error(f"Failed to store long-term memory: {e}", exc_info=True)
            raise
    
    def search_long_term_memories(
        self,
        query_vector: List[float],
        user_id: int,
        limit: int = 3,
        score_threshold: float = 0.5
    ) -> List[Dict]:
        """
        Search user's long-term memories (previous session summaries + explicit facts).
        
        Args:
            query_vector: Embedding of current query
            user_id: User ID to filter memories
            limit: Max results (default: 3)
            score_threshold: Min similarity score (default: 0.5)
        
        Returns:
            List of matching memories with ltm_id for PostgreSQL batch load.
            content_preview is included for debugging but should NOT be used in LLM workflow.
        
        Example:
            [
                {
                    "ltm_id": 42,
                    "memory_type": "session_summary",
                    "score": 0.87,
                    "content_preview": "User discussed..."
                }
            ]
        """
        try:
            results = self.client.search(
                collection_name=COLLECTION_LONG_TERM_MEMORIES,
                query_vector=query_vector,
                query_filter={
                    "must": [
                        {"key": "user_id", "match": {"value": user_id}}
                    ]
                },
                limit=limit,
                score_threshold=score_threshold
            )
            
            logger.info(
                f"Long-term memory search: {len(results)} results "
                f"(user={user_id}, limit={limit}, threshold={score_threshold})"
            )
            
            return [
                {
                    "ltm_id": hit.payload["ltm_id"],
                    "memory_type": hit.payload["memory_type"],
                    "score": hit.score,
                    "content_preview": hit.payload["content_preview"]  # Debug info
                }
                for hit in results
            ]
        
        except Exception as e:
            logger.error(f"Long-term memory search failed: {e}", exc_info=True)
            raise
