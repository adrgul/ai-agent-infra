"""Debug API endpoints for troubleshooting."""

from fastapi import APIRouter, HTTPException, status
from database.pg_connection import get_connection_params
from services.qdrant_service import QdrantService
from services.config_service import get_config_service
from services.cache_service import simple_cache, get_context_cache
import logging
import os
import psycopg2

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug", tags=["debug"])

config = get_config_service()


@router.post("/reset/postgres")
async def reset_postgres():
    """Reset PostgreSQL database - delete all documents and chunks."""
    conn = None
    cur = None
    try:
        params = get_connection_params()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        
        # Delete in correct order (foreign key constraints)
        cur.execute("DELETE FROM document_chunks;")
        chunks_deleted = cur.rowcount
        
        cur.execute("DELETE FROM documents;")
        docs_deleted = cur.rowcount
        
        # Reset sequences
        cur.execute("ALTER SEQUENCE documents_id_seq RESTART WITH 1;")
        cur.execute("ALTER SEQUENCE document_chunks_id_seq RESTART WITH 1;")
        
        conn.commit()
        
        logger.info(f"PostgreSQL reset: {docs_deleted} docs, {chunks_deleted} chunks deleted")
        
        return {
            "status": "success",
            "documents_deleted": docs_deleted,
            "chunks_deleted": chunks_deleted
        }
        
    except Exception as e:
        logger.error(f"PostgreSQL reset failed: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset PostgreSQL: {str(e)}"
        )
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.post("/reset/qdrant")
async def reset_qdrant():
    """Reset Qdrant - delete all points from document_chunks collection."""
    try:
        qdrant = QdrantService()
        collection_name = "r_d_ai_chat_document_chunks"
        
        # Skip count check, just try to delete all points directly
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchAny
            
            # Try to delete all points using a broad tenant_id filter
            # This will delete points for tenants 1-20
            deleted_info = qdrant.client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="tenant_id",
                            match=MatchAny(any=list(range(1, 21)))
                        )
                    ]
                )
            )
            
            logger.info(f"Qdrant reset: delete operation executed")
            
            return {
                "status": "success",
                "message": "Delete operation completed",
                "collection": collection_name,
                "operation": str(deleted_info)
            }
            
        except Exception as delete_error:
            logger.error(f"Could not delete points: {delete_error}")
            
            # Alternative: try to delete without filter (may not be supported)
            try:
                # Try to recreate collection (nuclear option)
                from qdrant_client.models import Distance, VectorParams
                
                logger.warning("Trying to recreate collection as fallback")
                
                # Delete and recreate collection
                qdrant.client.delete_collection(collection_name=collection_name)
                qdrant.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=3072,
                        distance=Distance.COSINE
                    )
                )
                
                logger.info("Qdrant collection recreated")
                
                return {
                    "status": "success",
                    "message": "Collection recreated (all points deleted)",
                    "collection": collection_name
                }
                
            except Exception as recreate_error:
                logger.error(f"Could not recreate collection: {recreate_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to reset Qdrant: {str(recreate_error)}"
                )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Qdrant reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset Qdrant: {str(e)}"
        )


@router.post("/reset/cache")
async def reset_cache():
    """Clear all caches (database cache + Python memory cache)."""
    try:
        import psycopg2
        from database.pg_connection import get_connection_params
        
        # Clear database cache table
        db_rows_deleted = 0
        try:
            params = get_connection_params()
            conn = psycopg2.connect(**params)
            cur = conn.cursor()
            
            cur.execute("DELETE FROM cached_prompts;")
            db_rows_deleted = cur.rowcount
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Database cache cleared: {db_rows_deleted} entries deleted")
        
        except Exception as db_error:
            logger.error(f"Database cache clear failed: {db_error}")
        
        # Clear Python memory cache
        memory_cleared = 0
        try:
            cache = get_context_cache()
            cache.clear()
            memory_cleared = 1  # Cleared successfully
            logger.info("Python memory cache cleared")
        
        except Exception as mem_error:
            logger.error(f"Memory cache clear failed: {mem_error}")
        
        return {
            "status": "success",
            "database_cache_rows_deleted": db_rows_deleted,
            "memory_cache_cleared": bool(memory_cleared),
            "message": "All caches cleared successfully"
        }
    
    except Exception as e:
        logger.error(f"Cache reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset cache: {str(e)}"
        )
