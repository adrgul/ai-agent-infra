"""
FAISS vector store utilities for RAG pipeline.

Why this module exists:
- Manages FAISS index creation, persistence, and loading
- Provides retrieval interface for chat endpoint
- Handles allow_dangerous_deserialization flag safely

Design decisions:
- FAISS for fast similarity search without external dependencies
- save_local/load_local for persistence (no database required)
- allow_dangerous_deserialization=True (safe for self-generated indexes)

SECURITY NOTE: allow_dangerous_deserialization=True is required for FAISS loading
because FAISS uses pickle internally. This is SAFE for indexes you create yourself,
but NEVER use with untrusted index files (pickle can execute arbitrary code).
"""

import os
from typing import Any, List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def build_vectorstore(
    chunks: List[Document],
    embeddings: Any,
    settings: Settings,
) -> FAISS:
    """
    Build FAISS vector store from chunks and persist to disk.

    Why this function: Creates searchable index of document chunks.
    FAISS provides fast similarity search for RAG retrieval.

    Why persist: Index creation is expensive (API calls for embeddings).
    Persisting allows reusing the index across server restarts.

    Args:
        chunks: List of chunked documents to index
        embeddings: Embeddings instance for vectorization
        settings: Application settings containing storage path

    Returns:
        FAISS: Persisted FAISS vector store instance
    """
    # Assert: Must have chunks to index
    assert len(chunks) > 0, "Cannot build vector store from empty chunks list"

    logger.info(f"Building FAISS index from {len(chunks)} chunks")

    # Why from_documents: Handles embedding and index creation in one step
    # LangChain calls embeddings.embed_documents() internally
    vectorstore = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings,
    )

    logger.info(f"FAISS index built successfully")

    # Persist to disk
    # Why save_local: Allows reloading index without re-embedding
    os.makedirs(settings.VECTORSTORE_DIR, exist_ok=True)
    vectorstore.save_local(settings.VECTORSTORE_DIR)

    logger.info(f"FAISS index saved to: {settings.VECTORSTORE_DIR}")

    return vectorstore


def load_vectorstore(
    embeddings: Any,
    settings: Settings,
) -> FAISS:
    """
    Load FAISS vector store from disk.

    Why this function: Retrieves persisted index for chat endpoint.
    Avoids re-embedding documents on every request.

    SECURITY: Uses allow_dangerous_deserialization=True because FAISS
    internally uses pickle. This is SAFE for self-generated indexes
    but DANGEROUS for untrusted files (pickle can execute code).

    Args:
        embeddings: Embeddings instance (must match the one used for indexing)
        settings: Application settings containing storage path

    Returns:
        FAISS: Loaded vector store ready for retrieval

    Raises:
        FileNotFoundError: If vector store directory doesn't exist
        RuntimeError: If loading fails
    """
    # Assert: Vector store directory must exist
    assert os.path.exists(settings.VECTORSTORE_DIR), (
        f"Vector store not found at {settings.VECTORSTORE_DIR}. "
        "Call /ingest first to create the index."
    )

    logger.info(f"Loading FAISS index from: {settings.VECTORSTORE_DIR}")

    try:
        # Why allow_dangerous_deserialization: FAISS uses pickle internally.
        # Safe here because we only load indexes we created ourselves.
        # NEVER set this to True for user-uploaded or untrusted index files.
        vectorstore = FAISS.load_local(
            settings.VECTORSTORE_DIR,
            embeddings,
            allow_dangerous_deserialization=True,
        )

        logger.info("FAISS index loaded successfully")
        return vectorstore

    except Exception as e:
        error_msg = f"Failed to load vector store: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def vectorstore_exists(settings: Settings) -> bool:
    """
    Check if vector store exists on disk.

    Why this function: Allows /chat endpoint to return 409 if index missing,
    directing user to call /ingest first.

    Why check directory and files: FAISS save_local creates multiple files
    (index.faiss, index.pkl). Directory existence + .faiss file is sufficient check.

    Args:
        settings: Application settings containing storage path

    Returns:
        bool: True if vector store exists, False otherwise
    """
    # Assert: settings must have VECTORSTORE_DIR
    assert hasattr(settings, "VECTORSTORE_DIR"), "Settings must have VECTORSTORE_DIR"

    if not os.path.exists(settings.VECTORSTORE_DIR):
        return False

    # Check for index.faiss file (FAISS main index file)
    # Why index.faiss: Primary indicator that FAISS index was saved
    index_file = os.path.join(settings.VECTORSTORE_DIR, "index.faiss")
    return os.path.exists(index_file)


def retrieve_chunks(
    vectorstore: FAISS,
    query: str,
    top_k: int = 4,
) -> List[Document]:
    """
    Retrieve most relevant chunks for a query.

    Why this function: Wrapper around FAISS similarity search with logging
    and error handling.

    Why similarity_search: Finds chunks with embeddings closest to query embedding.
    This is the core of RAG retrieval.

    Args:
        vectorstore: FAISS vector store to search
        query: User's question
        top_k: Number of chunks to retrieve

    Returns:
        List[Document]: Most relevant chunks with metadata
    """
    # Assert: top_k must be positive
    assert top_k > 0, f"top_k must be positive, got {top_k}"

    logger.info(f"Retrieving top {top_k} chunks for query: {query[:100]}...")

    # Why similarity_search: Returns k most similar documents by cosine similarity
    # LangChain handles embedding the query and comparing to index
    results = vectorstore.similarity_search(
        query=query,
        k=top_k,
    )

    logger.info(f"Retrieved {len(results)} chunks")
    return results
