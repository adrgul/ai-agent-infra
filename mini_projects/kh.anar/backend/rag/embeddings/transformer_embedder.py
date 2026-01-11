"""Transformer-based embedder using sentence-transformers when available

Falls back to HashEmbedder if transformer package not installed; this keeps
tests fast and deterministic while enabling higher-quality embeddings in
production when the dependency is present.
"""
from typing import List
from .embedder import Embedder, HashEmbedder

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None


class TransformerEmbedder(Embedder):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers not installed")
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> List[float]:
        vec = self.model.encode(text)
        return vec.tolist()


class FallbackEmbedder(HashEmbedder):
    """Alias to use HashEmbedder when real model isn't available."""
    pass
