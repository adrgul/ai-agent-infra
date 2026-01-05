"""OpenAI embedding service."""

import logging
from typing import Optional

from langchain_openai import OpenAIEmbeddings

from ..config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """Initialize embedding service.

        Args:
            model: Embedding model name (default: text-embedding-3-large)
            api_key: OpenAI API key
        """
        self.model = model or settings.OPENAI_EMBEDDING_MODEL
        self.api_key = api_key or settings.OPENAI_API_KEY

        self.embeddings = OpenAIEmbeddings(
            model=self.model,
            openai_api_key=self.api_key,
            max_retries=settings.OPENAI_MAX_RETRIES,
            timeout=settings.OPENAI_TIMEOUT,
        )

        logger.info(f"Initialized embedding service with model: {self.model}")

    async def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector as list of floats

        Raises:
            Exception: If embedding generation fails
        """
        try:
            embedding = await self.embeddings.aembed_query(text)
            logger.debug(f"Generated query embedding (dim: {len(embedding)})")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple documents.

        Args:
            texts: List of document texts to embed

        Returns:
            List of embedding vectors

        Raises:
            Exception: If embedding generation fails
        """
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
            logger.info(
                f"Generated {len(embeddings)} document embeddings "
                f"(dim: {len(embeddings[0]) if embeddings else 0})"
            )
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate document embeddings: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings for this model.

        Returns:
            Embedding vector dimension
        """
        # text-embedding-3-large: 3072 dimensions
        # text-embedding-3-small: 1536 dimensions
        # text-embedding-ada-002: 1536 dimensions
        dimension_map = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536,
        }

        return dimension_map.get(self.model, 1536)
