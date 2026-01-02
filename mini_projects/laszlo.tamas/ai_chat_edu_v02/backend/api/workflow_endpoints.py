"""
API Endpoints for LangGraph Workflows

New endpoints that use the automated LangGraph workflows:
1. POST /api/workflows/process-document - Full document pipeline
2. POST /api/workflows/close-session - Session memory creation
"""

import logging
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any
import os

from services.document_processing_workflow import DocumentProcessingWorkflow

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflows", tags=["workflows"])


# ===== REQUEST/RESPONSE MODELS =====

class WorkflowResponse(BaseModel):
    """Generic workflow response."""
    status: str = Field(..., description="success | skipped | failed")
    error: str = Field(None, description="Error message if failed")
    summary: Dict[str, Any] = Field(..., description="Processing summary")


# ===== DOCUMENT PROCESSING WORKFLOW =====

@router.post("/process-document", status_code=status.HTTP_201_CREATED)
async def process_document_workflow(
    file: UploadFile = File(...),
    tenant_id: int = Form(...),
    user_id: int = Form(...),
    visibility: Literal["private", "tenant"] = Form(...)
):
    """
    **NEW: Automated Document Processing Workflow**
    
    Replaces 3 manual API calls with single automated pipeline:
    
    OLD WAY (manual):
    1. POST /api/documents/upload
    2. POST /api/documents/{id}/chunk
    3. POST /api/documents/{id}/embed
    
    NEW WAY (automated):
    1. POST /api/workflows/process-document ✨
    
    Pipeline steps (automatic):
    - File validation
    - Content extraction (PDF/TXT/MD)
    - Database storage
    - Text chunking
    - Embedding generation
    - Qdrant upload
    - Verification
    
    Benefits:
    - Single API call
    - Automatic error recovery
    - State tracking
    - Consistent processing
    - Better error messages
    
    Args:
        file: Document file (PDF, TXT, or MD)
        tenant_id: Tenant identifier
        user_id: User identifier
        visibility: Document visibility level
    
    Returns:
        {
            "status": "success" | "failed",
            "document_id": int,
            "summary": {
                "filename": str,
                "content_length": int,
                "chunk_count": int,
                "embedding_count": int,
                "qdrant_vectors": int
            }
        }
    
    Raises:
        400: Invalid file or parameters
        500: Processing error
    """
    logger.info(f"[WORKFLOW API] process-document: {file.filename}, tenant={tenant_id}, user={user_id}")
    
    try:
        # Validate file extension
        file_ext = f".{file.filename.split('.')[-1].lower()}" if "." in file.filename else ""
        if file_ext not in {".pdf", ".txt", ".md"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {file_ext}. Allowed: .pdf, .txt, .md"
            )
        
        # Read file content
        content = await file.read()
        
        # Execute workflow
        workflow = DocumentProcessingWorkflow()
        result = await workflow.process_document(
            filename=file.filename,
            content=content,
            file_type=file_ext,
            tenant_id=tenant_id,
            user_id=user_id,
            visibility=visibility
        )
        
        logger.info(f"[WORKFLOW API] process-document complete: status={result['status']}")
        
        if result["status"] == "failed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Document processing failed")
            )
        
        return {
            "status": result["status"],
            "document_id": result["document_id"],
            "summary": result["summary"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKFLOW API] process-document error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )


# ===== UTILITY ENDPOINTS =====

@router.get("/status")
async def workflow_status():
    """
    Get workflow system status.
    
    Returns information about available workflows and their configuration.
    """
    return {
        "workflows": [
            {
                "name": "process-document",
                "description": "Automated document processing pipeline",
                "endpoint": "POST /api/workflows/process-document",
                "status": "operational"
            }
        ],
        "status": "operational"
    }
