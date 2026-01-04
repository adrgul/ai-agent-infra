"""Database repository for documents."""

import logging
from typing import Literal
from datetime import datetime

from database.pg_connection import get_db_connection

logger = logging.getLogger(__name__)


class DocumentRepository:
    """Repository for document database operations."""
    
    def insert_document(
        self,
        tenant_id: int,
        user_id: int,
        visibility: Literal["private", "tenant"],
        source: str,
        title: str,
        content: str
    ) -> int:
        """
        Insert a new document into the documents table.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User identifier (ignored if visibility='tenant')
            visibility: Document visibility ('private' or 'tenant')
            source: Document source (e.g., 'upload')
            title: Document title/filename
            content: Full text content
        
        Returns:
            document_id: ID of the inserted document
        
        Raises:
            Exception: If database operation fails
        """
        # For tenant visibility, user_id must be NULL per DB constraint
        actual_user_id = None if visibility == 'tenant' else user_id
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO documents (
                        tenant_id,
                        user_id,
                        visibility,
                        source,
                        title,
                        content,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    RETURNING id
                """, (tenant_id, actual_user_id, visibility, source, title, content))
                
                document_id = cursor.fetchone()['id']
                
                logger.info(f"Document inserted: id={document_id}, tenant={tenant_id}, visibility={visibility}, title={title}")
                
                return document_id
    
    def get_document_by_id(self, document_id: int) -> dict | None:
        """
        Retrieve a document by its ID.
        
        Args:
            document_id: Document identifier
        
        Returns:
            Document dictionary or None if not found
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        id,
                        tenant_id,
                        user_id,
                        visibility,
                        source,
                        title,
                        content,
                        created_at
                    FROM documents
                    WHERE id = %s
                """, (document_id,))
                
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return {
                    "id": row["id"],
                    "tenant_id": row["tenant_id"],
                    "user_id": row["user_id"],
                    "visibility": row["visibility"],
                    "source": row["source"],
                    "title": row["title"],
                    "content": row["content"],
                    "created_at": row["created_at"]
                }

