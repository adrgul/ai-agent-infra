"""
Document ingestion endpoint for building FAISS index.

Why this module exists:
- Provides API for rebuilding RAG index from markdown files
- Orchestrates loading, chunking, embedding, and indexing pipeline
- Returns detailed statistics for verification

Design decisions:
- POST (not GET) because it's not idempotent (rebuilds index)
- force_rebuild flag allows skipping if index exists
- Detailed response helps debug indexing issues
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.rag.chunking import chunk_docs
from app.rag.embeddings import create_embeddings
from app.rag.loaders import load_markdown_docs
from app.rag.vectorstore import build_vectorstore, vectorstore_exists
from app.schemas.ingest import IngestRequest, IngestResponse

router = APIRouter()
logger = get_logger(__name__)


def _build_index(
    settings: Settings,
    embeddings: Any,
) -> IngestResponse:
    """
    Internal function to build FAISS index.

    Why separate function: Allows injecting embeddings for testing
    (tests can pass FakeEmbeddings to avoid OpenAI calls).

    Args:
        settings: Application settings
        embeddings: Embeddings instance (real or fake)

    Returns:
        IngestResponse: Statistics about indexed documents

    Raises:
        ValueError: If no markdown files found
        RuntimeError: If indexing fails
    """
    # Assert: settings and embeddings must be provided
    assert settings is not None, "Settings must be provided"
    assert embeddings is not None, "Embeddings must be provided"

    try:
        # Step 1: Load markdown documents
        # Why first: Need documents before chunking
        documents = load_markdown_docs(settings.DOCS_PATH)

        # Step 2: Chunk documents
        # Why: Large docs need splitting for effective retrieval
        chunks = chunk_docs(documents)

        # Step 3: Build and persist vector store
        # Why: Creates searchable index for RAG retrieval
        build_vectorstore(chunks, embeddings, settings)

        # Step 4: Compile response statistics
        # Why: Helps verify indexing worked correctly
        filenames = sorted(set(doc.metadata["filename"] for doc in documents))

        return IngestResponse(
            indexed_files=len(documents),
            chunk_count=len(chunks),
            vectorstore_dir=settings.VECTORSTORE_DIR,
            filenames=filenames,
        )

    except ValueError as e:
        # Why ValueError: Raised when no markdown files found
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e

    except Exception as e:
        # Why 500: Unexpected errors during processing
        logger.error(f"Unexpected error during ingestion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        ) from e


@router.post("/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_documents(
    request: IngestRequest,
    settings: Settings = Depends(get_settings),
) -> IngestResponse:
    """
    Build or rebuild FAISS vector index from markdown files.

    Why this endpoint: Allows on-demand indexing without restarting service.
    Call this endpoint after adding/updating markdown files.

    Why force_rebuild: Skip indexing if index already exists and docs haven't changed.
    Set to true to force re-indexing (e.g., after changing chunking parameters).

    Args:
        request: Ingest request with force_rebuild flag
        settings: Injected application settings

    Returns:
        IngestResponse: Statistics about indexed documents

    Raises:
        HTTPException 400: No markdown files found
        HTTPException 500: Unexpected error during ingestion
    """
    # Assert: Request must be valid IngestRequest
    # (Pydantic validates this before function is called)

    logger.info(f"Ingest requested (force_rebuild={request.force_rebuild})")

    # Check if index already exists and force_rebuild is False
    # Why: Avoid expensive re-indexing if not needed
    if not request.force_rebuild and vectorstore_exists(settings):
        logger.info("Vector store already exists, skipping rebuild")
        raise HTTPException(
            status_code=200,
            detail="Vector store already exists. Set force_rebuild=true to rebuild.",
        )

    # Create embeddings (or inject fake ones in tests)
    # Why create_embeddings: Factory pattern allows test mocking
    embeddings = create_embeddings(settings)

    # Build index and return statistics
    return _build_index(settings, embeddings)
