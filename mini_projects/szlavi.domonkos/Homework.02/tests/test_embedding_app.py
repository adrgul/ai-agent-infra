from __future__ import annotations

from typing import List, Tuple
import uuid

import pytest

from app.cli import EmbeddingApp
from app.embeddings import EmbeddingService
from app.vector_store import VectorStore


class FakeEmbeddingService(EmbeddingService):
    def __init__(self, vector: List[float]):
        self.vector = vector

    def get_embedding(self, text: str) -> List[float]:
        return self.vector


class FakeVectorStore(VectorStore):
    def __init__(self):
        self.added = []
        self.next_results: List[Tuple[str, float, str]] = []

    def add(self, id: str, text: str, embedding: List[float]) -> None:
        self.added.append((id, text, embedding))

    def similarity_search(self, embedding: List[float], k: int = 3) -> List[Tuple[str, float, str]]:
        # Return pre-seeded results truncated to k
        return self.next_results[:k]


def test_process_query_adds_and_searches():
    fake_vec = [0.1, 0.2, 0.3]
    emb = FakeEmbeddingService(fake_vec)
    store = FakeVectorStore()

    # prepare fake similarity results
    store.next_results = [
        ("id-self", 0.0, "current text"),
        ("id-1", 0.12, "similar text 1"),
        ("id-2", 0.45, "similar text 2"),
    ]

    app = EmbeddingApp(emb_service=emb, vector_store=store)
    uid, neighbors = app.process_query("hello world", k=3)

    # Ensure stored id was recorded and embedding passed through
    assert len(store.added) == 1
    stored_id, stored_text, stored_embedding = store.added[0]
    assert stored_text == "hello world"
    assert stored_embedding == fake_vec

    # The returned uid should match stored id
    assert uid == stored_id

    # neighbors derived from store.next_results
    assert len(neighbors) == 3
    assert neighbors[0].text == "current text"
    assert abs(neighbors[1].distance - 0.12) < 1e-6
