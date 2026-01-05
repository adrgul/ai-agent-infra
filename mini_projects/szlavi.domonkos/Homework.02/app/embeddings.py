"""Embedding service abstraction and OpenAI implementation.

Follows a small EmbeddingService interface (ABC) so implementations
can be swapped without changing application logic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
import logging

import openai

logger = logging.getLogger(__name__)


class EmbeddingService(ABC):
    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """Return embedding vector for given text."""


class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        openai.api_key = api_key
        self.model = model

    def get_embedding(self, text: str) -> List[float]:
        try:
            resp = openai.Embedding.create(model=self.model, input=text)
            embedding = resp["data"][0]["embedding"]
            return embedding
        except Exception as exc:  # keep broad to avoid breaking the CLI
            logger.error("Embedding generation failed: %s", exc)
            return []
