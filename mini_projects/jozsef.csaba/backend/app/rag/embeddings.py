"""
Embedding utilities for RAG pipeline.

Why this module exists:
- Creates embeddings using OpenAI's embedding models
- Provides factory function for dependency injection and testing
- Abstracts embedding provider (could swap to other providers later)

Design decisions:
- OpenAI embeddings for quality and compatibility
- text-embedding-3-small for balance of speed and quality
- Factory pattern allows injecting fake embeddings in tests
"""

from typing import Any

from langchain_openai import OpenAIEmbeddings

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_embeddings(settings: Settings) -> Any:
    """
    Create OpenAI embeddings instance.

    Why this function: Factory pattern allows:
    1. Dependency injection (can pass different settings in tests)
    2. Easy mocking (tests can inject FakeEmbeddings)
    3. Configuration centralized in Settings

    Why OpenAI embeddings: High quality, well-maintained, compatible with
    LangChain's vector store abstractions.

    Why text-embedding-3-small: Good balance of speed, quality, and cost.
    Produces 1536-dimension vectors.

    Args:
        settings: Application settings containing API key and model name

    Returns:
        Any: LangChain embeddings instance (typed as Any for flexibility with fakes)
    """
    # Assert: API key must be present
    assert settings.OPENAI_API_KEY, "OPENAI_API_KEY must be set"

    logger.info(f"Creating OpenAI embeddings with model: {settings.OPENAI_EMBED_MODEL}")

    # Why OpenAIEmbeddings: LangChain's wrapper for OpenAI API
    # Handles API calls, retries, and integration with vector stores
    embeddings = OpenAIEmbeddings(
        openai_api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_EMBED_MODEL,
    )

    return embeddings
