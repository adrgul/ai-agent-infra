"""
Document loading utilities for RAG pipeline.

Why this module exists:
- Recursively loads all markdown files from a directory
- Creates LangChain Documents with proper metadata
- Deterministic ordering for reproducible indexing

Design decisions:
- UTF-8 encoding assumed (standard for modern markdown)
- Sorted paths ensure consistent indexing order across runs
- Metadata includes source path and filename for attribution
"""

import os
from pathlib import Path
from typing import List

from langchain_core.documents import Document

from app.core.logging import get_logger

logger = get_logger(__name__)


def load_markdown_docs(docs_path: str) -> List[Document]:
    """
    Recursively load all markdown files from a directory.

    Why this function: Centralizes markdown loading logic with proper error handling
    and metadata extraction. Creates LangChain Documents ready for chunking.

    Why UTF-8: Standard encoding for markdown; most modern editors default to UTF-8.

    Why sorted: Deterministic ordering ensures reproducible indexing. If files are
    processed in different orders, FAISS index may differ between runs.

    Args:
        docs_path: Path to directory containing markdown files

    Returns:
        List[Document]: LangChain documents with page_content and metadata

    Raises:
        FileNotFoundError: If docs_path does not exist
        ValueError: If no markdown files found
    """
    # Assert: docs_path must exist and be a directory
    assert os.path.exists(docs_path), f"docs_path must exist: {docs_path}"
    assert os.path.isdir(docs_path), f"docs_path must be a directory: {docs_path}"

    docs_path_obj = Path(docs_path).resolve()
    logger.info(f"Loading markdown files from: {docs_path_obj}")

    # Recursively find all .md files
    # Why rglob: Handles nested directories automatically
    md_files = sorted(docs_path_obj.rglob("*.md"))

    if not md_files:
        error_msg = f"No markdown files found in {docs_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Found {len(md_files)} markdown files")

    documents = []
    for md_file in md_files:
        try:
            # Why read as UTF-8: Standard encoding for text files
            content = md_file.read_text(encoding="utf-8")

            # Why relative path: Makes metadata portable (doesn't leak absolute paths)
            try:
                relative_path = md_file.relative_to(docs_path_obj)
            except ValueError:
                # Fallback to absolute if relative fails
                relative_path = md_file

            # Why these metadata fields:
            # - source: For attribution in chat responses
            # - filename: User-friendly reference
            doc = Document(
                page_content=content,
                metadata={
                    "source": str(relative_path),
                    "filename": md_file.name,
                },
            )
            documents.append(doc)

            logger.debug(f"Loaded: {relative_path} ({len(content)} chars)")

        except Exception as e:
            # Why log and continue: One bad file shouldn't break entire indexing
            logger.warning(f"Failed to load {md_file}: {e}")
            continue

    if not documents:
        error_msg = "No documents successfully loaded"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Successfully loaded {len(documents)} documents")
    return documents
