"""Embedder interface and deterministic test embedder

The real embedder would call a model like sentence-transformers or OpenAI
embeddings. For test determinism we provide a HashEmbedder that turns text
into a fixed-length pseudo-embedding derived from a hashing function.
"""
from typing import List
import hashlib


class Embedder:
    def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts. Default implementation calls embed_text for each."""
        return [self.embed_text(t) for t in texts]


class HashEmbedder(Embedder):
    def __init__(self, dim: int = 32):
        self.dim = dim

    def embed_text(self, text: str) -> List[float]:
        # deterministic pseudo-embedding: take sha256 and split into dim floats
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vals = [b for b in h]
        # repeat/trim to dim
        rep = (vals * ((self.dim // len(vals)) + 1))[: self.dim]
        # normalize to 0-1
        emb = [v / 255.0 for v in rep]
        return emb
