"""
Document chunking utilities for RAG pipeline.

Why this module exists:
- Splits documents into smaller chunks for embedding and retrieval
- Preserves metadata across chunks for source attribution
- Adds chunk-specific metadata for identification

Design decisions:
- RecursiveCharacterTextSplitter for semantic splitting (respects paragraphs, sentences)
- 1200 char chunks balance context vs embedding quality
- 150 char overlap prevents information loss at boundaries
"""

from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.core.logging import get_logger

logger = get_logger(__name__)


def chunk_docs(
    documents: List[Document],
    chunk_size: int = 1200,
    chunk_overlap: int = 150,
) -> List[Document]:
    """
    Split documents into chunks with overlap.

    Why this function: Large documents need to be split into smaller chunks for:
    1. Embedding models have context limits
    2. Retrieval works better with focused, specific chunks
    3. Smaller chunks = more precise attribution

    Why these defaults:
    - 1200 chars: ~200-300 tokens, fits well in embedding models and provides
      enough context for answering questions
    - 150 char overlap: Prevents losing information at chunk boundaries
      (e.g., sentence split mid-thought)

    Why RecursiveCharacterTextSplitter: Tries to split on natural boundaries
    (paragraphs, sentences) rather than arbitrary character counts.

    Args:
        documents: List of LangChain Documents to chunk
        chunk_size: Target size for each chunk in characters
        chunk_overlap: Number of overlapping characters between chunks

    Returns:
        List[Document]: Chunked documents with preserved + augmented metadata
    """
    # Assert: chunk_size must be greater than chunk_overlap
    assert chunk_size > chunk_overlap, (
        f"chunk_size ({chunk_size}) must be > chunk_overlap ({chunk_overlap})"
    )

    logger.info(
        f"Chunking {len(documents)} documents "
        f"(chunk_size={chunk_size}, overlap={chunk_overlap})"
    )

    # Why RecursiveCharacterTextSplitter: Respects document structure
    # by trying separators in order: paragraphs, sentences, words, characters
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,  # Count characters, not tokens
        is_separator_regex=False,
    )

    chunked_docs = []
    for doc in documents:
        # Split document into chunks
        chunks = splitter.split_documents([doc])

        # Add chunk-specific metadata
        # Why chunk_id: Unique identifier for source attribution
        filename = doc.metadata.get("filename", "unknown")
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"{filename}:{i}"
            chunked_docs.append(chunk)

        logger.debug(f"Split {filename} into {len(chunks)} chunks")

    logger.info(f"Created {len(chunked_docs)} total chunks")
    return chunked_docs
