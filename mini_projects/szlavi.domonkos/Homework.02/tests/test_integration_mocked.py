from __future__ import annotations

import builtins
from typing import List, Dict, Any
import pytest

import app.embeddings as embeddings_mod
import app.vector_store as vs_mod
from app.cli import EmbeddingApp


class FakeOpenAI:
    """Simple fake for openai.Embedding.create"""

    def __init__(self, vector: List[float]):
        self._vector = vector

    class Embedding:
        pass

    def embedding_create(self, model: str, input: str) -> Dict[str, Any]:
        return {"data": [{"embedding": self._vector}]}


class FakeCollection:
    def __init__(self):
        self.ids: List[str] = []
        self.docs: List[str] = []
        self.embs: List[List[float]] = []

    def add(self, ids: List[str], documents: List[str], embeddings: List[List[float]]):
        self.ids.extend(ids)
        self.docs.extend(documents)
        self.embs.extend(embeddings)

    def query(self, query_embeddings=None, n_results=3, include=None, **kwargs):
        # compute simple euclidean distances between first query embedding and stored embeddings
        q = query_embeddings[0]
        distances = []
        for e in self.embs:
            # squared euclidean
            d = sum((a - b) ** 2 for a, b in zip(e, q))
            distances.append(d)
        # sort by distance
        idxs = sorted(range(len(distances)), key=lambda i: distances[i])[:n_results]
        return {
            "ids": [[self.ids[i] for i in idxs]],
            "documents": [[self.docs[i] for i in idxs]],
            "distances": [[distances[i] for i in idxs]],
        }

    def get(self, include=None):
        return {"ids": [self.ids], "documents": [self.docs]}


class FakeClient:
    def __init__(self, settings=None):
        self._col = FakeCollection()

    def get_or_create_collection(self, name: str):
        return self._col

    def persist(self):
        pass


@pytest.fixture(autouse=True)
def patch_openai_and_chroma(monkeypatch):
    # Patch openai.Embedding.create
    fake_vector = [0.1, 0.2, 0.3]
    fake_openai = FakeOpenAI(fake_vector)

    def fake_create(model, input):
        return {"data": [{"embedding": fake_vector}]}

    monkeypatch.setattr(embeddings_mod, "openai", type("O", (), {"Embedding": type("E", (), {"create": staticmethod(fake_create)}), "api_key": None}))

    # Patch chromadb.Client to return FakeClient
    monkeypatch.setattr(vs_mod, "chromadb", type("C", (), {"Client": lambda settings: FakeClient(), "config": vs_mod.chromadb.config if hasattr(vs_mod.chromadb, 'config') else None}))

    yield


def test_integration_process_query(monkeypatch):
    cfg_api_key = "sk-test"
    emb_srv = embeddings_mod.OpenAIEmbeddingService(api_key=cfg_api_key, model="text-embedding-3-small")

    # ChromaVectorStore will use FakeClient via monkeypatch in fixture
    store = vs_mod.ChromaVectorStore(persist_dir="./chroma_db_test")
    app = EmbeddingApp(emb_service=emb_srv, vector_store=store)

    uid, neighbors = app.process_query("hello integration", k=2, mode="semantic")

    # After insert, the fake collection should have one doc
    assert len(store._ids) == 1 or len(store.collection.ids) == 1
    # neighbors should be returned (may be empty if underlying query returns less)
    assert isinstance(neighbors, list)
