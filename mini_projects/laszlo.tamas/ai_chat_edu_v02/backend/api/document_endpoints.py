"""
Document management endpoints.

Provides API endpoints for listing, viewing, and managing documents.
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from database.pg_init import (
    get_documents_for_user,
    get_document_by_id,
    delete_document
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


# Schemas
class DocumentSummary(BaseModel):
    """Summary of a document (without full content)."""
    id: int
    tenant_id: int
    user_id: Optional[int] = None
    visibility: str
    source: str
    title: str
    created_at: datetime  # Changed from str to datetime
    
    class Config:
        from_attributes = True


class DocumentDetail(BaseModel):
    """Full document with content."""
    id: int
    tenant_id: int
    user_id: Optional[int] = None
    visibility: str
    source: str
    title: str
    content: str
    created_at: datetime  # Changed from str to datetime
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response for document list."""
    documents: List[DocumentSummary]
    count: int


# Endpoints
@router.get("/", response_model=DocumentListResponse)
def list_documents(
    user_id: int = Query(..., description="User ID"),
    tenant_id: int = Query(..., description="Tenant ID")
):
    """
    List all documents accessible to the user.
    
    Includes:
    - Private documents owned by the user
    - Tenant-wide documents in the user's tenant
    
    Returns document metadata without full content.
    """
    try:
        logger.info(f"Listing documents for user {user_id}, tenant {tenant_id}")
        
        documents = get_documents_for_user(user_id=user_id, tenant_id=tenant_id)
        
        logger.info(f"Found {len(documents)} documents for user {user_id}")
        
        return DocumentListResponse(
            documents=documents,
            count=len(documents)
        )
    
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: int):
    """
    Get full document by ID including content.
    
    TODO: Add permission check (user must have access to this document).
    """
    try:
        logger.info(f"Fetching document {document_id}")
        
        document = get_document_by_id(document_id)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        
        logger.info(f"Retrieved document {document_id}: {document['title']}")
        
        return document
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch document: {str(e)}"
        )


@router.delete("/{document_id}")
def remove_document(document_id: int):
    """
    Delete a document and all its chunks.
    
    TODO: Add permission check (user must own document or be admin).
    """
    try:
        logger.info(f"Deleting document {document_id}")
        
        # Check if document exists
        document = get_document_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        
        delete_document(document_id)
        
        logger.info(f"Deleted document {document_id}: {document['title']}")
        
        return {
            "status": "success",
            "message": f"Document {document_id} deleted",
            "document_id": document_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )
