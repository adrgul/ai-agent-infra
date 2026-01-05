from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

import openai
import os


class EmbeddingService(ABC):
    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """Return an embedding vector for `text`."""


class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model

    def get_embedding(self, text: str) -> List[float]:
        if not os.getenv("OPENAI_API_KEY"):
            return []
        try:
            client = openai.OpenAI()
            resp = client.embeddings.create(model=self.model, input=text)
            emb = resp.data[0].embedding
            return emb
        except Exception:
            print("Warning: embedding request failed, returning empty embedding.")
            return []
