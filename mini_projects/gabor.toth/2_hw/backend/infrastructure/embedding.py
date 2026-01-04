"""OpenAI embedding service implementation."""

from typing import List
import openai
import asyncio
from domain.interfaces import EmbeddingService


class OpenAIEmbeddingService(EmbeddingService):
    """Embedding service using OpenAI API."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text."""
        def _embed():
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
            )
            return response.data[0].embedding
        
        # Run blocking I/O in thread pool
        try:
            # Python 3.9+ has asyncio.to_thread
            return await asyncio.to_thread(_embed)
        except AttributeError:
            # Fallback for older Python versions
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _embed)

    async def embed_texts(
        self, texts: List[str], batch_size: int = 100
    ) -> List[List[float]]:
        """Embed multiple texts in batches."""
        def _embed_batch():
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )
                embeddings.extend([item.embedding for item in response.data])
            return embeddings
        
        # Run blocking I/O in thread pool
        try:
            return await asyncio.to_thread(_embed_batch)
        except AttributeError:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _embed_batch)
