"""
Embedding generation for SupportAI.

Handles text embedding using OpenAI's text-embedding-3-large.
"""

from typing import List, Dict, Any, Optional
import asyncio
from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from ..utils.config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            api_key=settings.openai_api_key,
            dimensions=3072  # Explicit dimension for consistency
        )

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")

            # LangChain's embed_documents is synchronous, so run in thread
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                self.embeddings.embed_documents,
                texts
            )

            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a single query.

        Args:
            query: Query text to embed

        Returns:
            Embedding vector
        """
        try:
            # LangChain's embed_query is synchronous
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                self.embeddings.embed_query,
                query
            )

            return embedding

        except Exception as e:
            logger.error(f"Query embedding failed: {str(e)}")
            raise

    def get_dimensions(self) -> int:
        """Get the dimensionality of embeddings."""
        return 3072


# Global embedding service instance
embedding_service = EmbeddingService()


async def embed_texts_batch(
    texts: List[str],
    batch_size: int = 100
) -> List[List[float]]:
    """
    Embed texts in batches to handle rate limits.

    Args:
        texts: List of texts to embed
        batch_size: Number of texts per batch

    Returns:
        List of embedding vectors
    """
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")

        batch_embeddings = await embedding_service.embed_texts(batch)
        all_embeddings.extend(batch_embeddings)

        # Small delay between batches to respect rate limits
        if i + batch_size < len(texts):
            await asyncio.sleep(0.1)

    return all_embeddings


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks for embedding.

    Args:
        text: Text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Find a good breaking point (sentence end)
        if end < len(text):
            # Look for sentence endings in the last 200 characters
            search_end = min(end + 200, len(text))
            sentence_end = text.rfind('.', end, search_end)
            if sentence_end != -1:
                end = sentence_end + 1
            else:
                # Look for other sentence endings
                for punct in ['!', '?', '\n\n']:
                    punct_end = text.rfind(punct, end, search_end)
                    if punct_end != -1:
                        end = punct_end + 1
                        break

        chunk = text[start:end].strip()
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)

        # Move start position with overlap
        start = end - overlap

        # Ensure we don't get stuck
        if start >= end:
            start = end

    return chunks


def prepare_documents_for_embedding(
    documents: List[Dict[str, Any]],
    chunk_size: int = 1000,
    overlap: int = 100
) -> List[Dict[str, Any]]:
    """
    Prepare documents for embedding by chunking long texts.

    Args:
        documents: List of document dictionaries
        chunk_size: Maximum characters per chunk
        overlap: Characters to overlap

    Returns:
        List of chunked documents ready for embedding
    """
    chunked_docs = []

    for doc in documents:
        content = doc.get("content", "")
        chunks = chunk_text(content, chunk_size, overlap)

        for i, chunk in enumerate(chunks):
            chunked_doc = doc.copy()
            chunked_doc["content"] = chunk
            chunked_doc["chunk_id"] = f"c-{i}"
            chunked_docs.append(chunked_doc)

    logger.info(f"Chunked {len(documents)} documents into {len(chunked_docs)} chunks")
    return chunked_docs