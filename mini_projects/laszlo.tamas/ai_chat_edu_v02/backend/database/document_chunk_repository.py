"""Document chunks repository for PostgreSQL operations."""

import logging
from typing import List, Optional, Dict
from database.pg_connection import get_db_connection

logger = logging.getLogger(__name__)


class DocumentChunkRepository:
    """Repository for document_chunks table operations."""
    
    def insert_chunks(
        self,
        tenant_id: int,
        document_id: int,
        chunks: List[dict]
    ) -> List[int]:
        """
        Insert multiple document chunks into the database.
        
        Args:
            tenant_id: Tenant identifier
            document_id: Document identifier (FK to documents.id)
            chunks: List of chunk dictionaries with keys:
                - chunk_index: Sequential index (0-based)
                - start_offset: Start position in original text
                - end_offset: End position in original text
                - content: Chunk text content
                - source_title: Optional document title
        
        Returns:
            List of inserted chunk IDs
        
        Raises:
            Exception: If database insert fails
        """
        chunk_ids = []
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for chunk in chunks:
                cursor.execute(
                    """
                    INSERT INTO document_chunks (
                        tenant_id,
                        document_id,
                        chunk_index,
                        start_offset,
                        end_offset,
                        content,
                        source_title
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        tenant_id,
                        document_id,
                        chunk["chunk_index"],
                        chunk["start_offset"],
                        chunk["end_offset"],
                        chunk["content"],
                        chunk.get("source_title")
                    )
                )
                
                chunk_id = cursor.fetchone()["id"]
                chunk_ids.append(chunk_id)
            
            conn.commit()
        
        logger.info(f"Inserted {len(chunk_ids)} chunks for document_id={document_id}")
        return chunk_ids
    
    def get_chunks_by_document(self, document_id: int) -> List[dict]:
        """
        Retrieve all chunks for a specific document.
        
        Args:
            document_id: Document identifier
        
        Returns:
            List of chunk dictionaries
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT 
                    id,
                    tenant_id,
                    document_id,
                    chunk_index,
                    start_offset,
                    end_offset,
                    content,
                    source_title,
                    qdrant_point_id,
                    embedded_at,
                    created_at
                FROM document_chunks
                WHERE document_id = %s
                ORDER BY chunk_index
                """,
                (document_id,)
            )
            
            rows = cursor.fetchall()
            
            chunks = []
            for row in rows:
                chunks.append({
                    "id": row["id"],
                    "tenant_id": row["tenant_id"],
                    "document_id": row["document_id"],
                    "chunk_index": row["chunk_index"],
                    "start_offset": row["start_offset"],
                    "end_offset": row["end_offset"],
                    "content": row["content"],
                    "source_title": row["source_title"],
                    "qdrant_point_id": row["qdrant_point_id"],
                    "embedded_at": row["embedded_at"],
                    "created_at": row["created_at"]
                })
            
            return chunks
    
    def get_chunk_by_id(self, chunk_id: int) -> Optional[dict]:
        """
        Retrieve a single chunk by its ID.
        
        Args:
            chunk_id: Chunk identifier
        
        Returns:
            Chunk dictionary or None if not found
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT 
                    id,
                    tenant_id,
                    document_id,
                    chunk_index,
                    start_offset,
                    end_offset,
                    content,
                    source_title,
                    qdrant_point_id,
                    embedded_at,
                    created_at
                FROM document_chunks
                WHERE id = %s
                """,
                (chunk_id,)
            )
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return {
                "id": row["id"],
                "tenant_id": row["tenant_id"],
                "document_id": row["document_id"],
                "chunk_index": row["chunk_index"],
                "start_offset": row["start_offset"],
                "end_offset": row["end_offset"],
                "content": row["content"],
                "source_title": row["source_title"],
                "qdrant_point_id": row["qdrant_point_id"],
                "embedded_at": row["embedded_at"],
                "created_at": row["created_at"]
            }
    
    def get_chunks_by_ids(self, chunk_ids: List[int]) -> dict[int, dict]:
        """
        Retrieve multiple chunks by their IDs in a single batch query.
        
        Args:
            chunk_ids: List of chunk identifiers
        
        Returns:
            Dictionary mapping chunk_id to chunk data (only found chunks included)
        """
        if not chunk_ids:
            return {}
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Use IN clause for batch retrieval
            placeholders = ','.join(['%s'] * len(chunk_ids))
            cursor.execute(
                f"""
                SELECT 
                    id,
                    tenant_id,
                    document_id,
                    chunk_index,
                    start_offset,
                    end_offset,
                    content,
                    source_title,
                    qdrant_point_id,
                    embedded_at,
                    created_at
                FROM document_chunks
                WHERE id IN ({placeholders})
                """,
                chunk_ids
            )
            
            rows = cursor.fetchall()
            
            # Return as dict for fast lookup by chunk_id
            result = {}
            for row in rows:
                result[row["id"]] = {
                    "id": row["id"],
                    "tenant_id": row["tenant_id"],
                    "document_id": row["document_id"],
                    "chunk_index": row["chunk_index"],
                    "start_offset": row["start_offset"],
                    "end_offset": row["end_offset"],
                    "content": row["content"],
                    "source_title": row["source_title"],
                    "qdrant_point_id": row["qdrant_point_id"],
                    "embedded_at": row["embedded_at"],
                    "created_at": row["created_at"]
                }
            
            return result
    
    def get_chunks_not_embedded(self, document_id: int = None) -> List[dict]:
        """
        Retrieve chunks that don't have embeddings yet.
        
        Args:
            document_id: Optional document ID filter
        
        Returns:
            List of chunk dictionaries (id, content)
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if document_id:
                cursor.execute(
                    """
                    SELECT id, content, tenant_id, document_id
                    FROM document_chunks
                    WHERE document_id = %s AND qdrant_point_id IS NULL
                    ORDER BY chunk_index
                    """,
                    (document_id,)
                )
            else:
                cursor.execute(
                    """
                    SELECT id, content, tenant_id, document_id
                    FROM document_chunks
                    WHERE qdrant_point_id IS NULL
                    ORDER BY document_id, chunk_index
                    """
                )
            
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "content": row["content"],
                    "tenant_id": row["tenant_id"],
                    "document_id": row["document_id"]
                }
                for row in rows
            ]
    
    def update_chunk_embedding(
        self,
        chunk_id: int,
        qdrant_point_id: str
    ) -> None:
        """
        Update chunk with Qdrant point ID and embedding timestamp.
        
        Args:
            chunk_id: Chunk ID
            qdrant_point_id: UUID from Qdrant
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                UPDATE document_chunks
                SET qdrant_point_id = %s,
                    embedded_at = now()
                WHERE id = %s
                """,
                (qdrant_point_id, chunk_id)
            )
            
            conn.commit()
        
        logger.info(f"Updated chunk {chunk_id} with Qdrant point {qdrant_point_id}")
    
    def update_chunks_embedding_batch(
        self,
        updates: List[Dict]
    ) -> None:
        """
        Batch update chunks with Qdrant point IDs.
        
        Args:
            updates: List of {"chunk_id": int, "qdrant_point_id": str}
        """
        if not updates:
            return
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for update in updates:
                cursor.execute(
                    """
                    UPDATE document_chunks
                    SET qdrant_point_id = %s,
                        embedded_at = now()
                    WHERE id = %s
                    """,
                    (update["qdrant_point_id"], update["chunk_id"])
                )
            
            conn.commit()
        
        logger.info(f"Batch updated {len(updates)} chunks with Qdrant point IDs")
