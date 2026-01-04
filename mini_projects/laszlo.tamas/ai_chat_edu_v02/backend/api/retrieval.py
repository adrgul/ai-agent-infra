"""RAG retrieval API endpoint."""

import logging
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List

from services.embedding_service import EmbeddingService
from services.qdrant_service import QdrantService
from database.document_chunk_repository import DocumentChunkRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["rag"])


# Request/Response models
class DocumentChunkResult(BaseModel):
    """Document chunk with retrieval metadata."""
    chunk_id: int = Field(..., description="Document chunk ID (PostgreSQL)")
    document_id: int = Field(..., description="Parent document ID")
    content: str = Field(..., description="Chunk text content")
    score: float = Field(..., description="Similarity score (0-1)")
    source_title: str = Field(None, description="Document title")


class RetrievalResponse(BaseModel):
    """RAG retrieval response."""
    query: str = Field(..., description="Original query text")
    chunks: List[DocumentChunkResult] = Field(..., description="Retrieved document chunks")
    total_found: int = Field(..., description="Total chunks found")


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_documents(
    query: str = Query(..., min_length=1, description="Search query text"),
    tenant_id: int = Query(..., description="Tenant ID for filtering"),
    limit: int = Query(None, ge=1, le=50, description="Max results (default from system.ini)")
):
    """
    Retrieve relevant document chunks using RAG pipeline.
    
    Pipeline:
    1. Query → embedding (OpenAI text-embedding-3-large)
    2. Qdrant similarity search (tenant_id filter)
    3. Top-K selection (system.ini: TOP_K_DOCUMENTS)
    4. Score threshold filter (system.ini: MIN_SCORE_THRESHOLD)
    
    Args:
        query: Search query text
        tenant_id: Tenant ID (required for multi-tenancy)
        limit: Optional limit override (default from system.ini)
    
    Returns:
        RetrievalResponse with chunks, scores, and metadata
    
    Raises:
        400: Invalid query
        500: Embedding or search error
    """
    logger.info(f"Retrieval request: query='{query[:50]}...', tenant_id={tenant_id}, limit={limit}")
    
    try:
        # Step 1: Generate query embedding
        embedding_service = EmbeddingService()
        query_vector = embedding_service.generate_embedding(query)
        logger.info(f"Query embedding generated: {len(query_vector)} dimensions")
        
        # Step 2: Search Qdrant
        qdrant_service = QdrantService()
        search_results = qdrant_service.search_document_chunks(
            query_vector=query_vector,
            tenant_id=tenant_id,
            limit=limit  # None → uses system.ini default
        )
        logger.info(f"Qdrant search complete: {len(search_results)} chunks found")
        
        # Step 3: Enrich with full chunk data from PostgreSQL
        chunk_repo = DocumentChunkRepository()
        enriched_chunks = []
        
        for result in search_results:
            chunk_id = result["chunk_id"]
            chunk_data = chunk_repo.get_chunk_by_id(chunk_id)
            
            if chunk_data:
                enriched_chunks.append(DocumentChunkResult(
                    chunk_id=chunk_id,
                    document_id=result["document_id"],
                    content=chunk_data["content"],
                    score=result["score"],
                    source_title=chunk_data.get("source_title", "Unknown")
                ))
        
        logger.info(f"Retrieval complete: {len(enriched_chunks)} chunks enriched")
        
        return RetrievalResponse(
            query=query,
            chunks=enriched_chunks,
            total_found=len(enriched_chunks)
        )
    
    except Exception as e:
        logger.error(f"Retrieval failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval error: {str(e)}"
        )
