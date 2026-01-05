from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple
import uuid

import chromadb
from chromadb.config import Settings


class VectorStore(ABC):
    @abstractmethod
    def add(self, id: str, text: str, embedding: List[float]) -> None:
        pass

    @abstractmethod
    def similarity_search(self, embedding: List[float], k: int = 3) -> List[Tuple[str, float, str]]:
        """Return list of tuples: (id, distance, text)"""


class ChromaVectorStore(VectorStore):
    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "prompts"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        # Attempt to create a Chroma client. Newer chromadb versions changed
        # client construction; keep this wrapped so callers can fallback.
        try:
            self.client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=self.persist_directory))
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
        except Exception:
            # Propagate exception so higher level can choose a fallback store.
            raise

    def add(self, id: str, text: str, embedding: List[float]) -> None:
        # wrap embedding/list into lists for the Chroma API
        try:
            self.collection.add(ids=[id], metadatas=[{"text": text}], embeddings=[embedding])
            self.client.persist()
        except Exception as e:
            print(f"Warning: failed to add vector to Chroma: {e}")

    def similarity_search(self, embedding: List[float], k: int = 3) -> List[Tuple[str, float, str]]:
        if not embedding:
            return []
        try:
            results = self.collection.query(query_embeddings=[embedding], n_results=k, include=["metadatas", "distances", "ids"])
            # results contains lists for each query; we used single query
            res = []
            ids = results.get("ids", [[]])[0]
            dists = results.get("distances", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            for i, _id in enumerate(ids):
                text = metadatas[i].get("text") if isinstance(metadatas[i], dict) else ""
                res.append((_id, dists[i], text))
            return res
        except Exception as e:
            print(f"Warning: similarity search failed: {e}")
            return []


class InMemoryVectorStore(VectorStore):
    """Simple in-memory vector store as a fallback for environments without
    a working ChromaDB installation.
    """

    def __init__(self):
        self._items: List[Tuple[str, List[float], str]] = []

    def add(self, id: str, text: str, embedding: List[float]) -> None:
        self._items.append((id, embedding, text))

    def similarity_search(self, embedding: List[float], k: int = 3) -> List[Tuple[str, float, str]]:
        if not embedding:
            return []
        # use cosine similarity
        from math import sqrt

        def dot(a: List[float], b: List[float]) -> float:
            return sum(x * y for x, y in zip(a, b))

        def norm(a: List[float]) -> float:
            return sqrt(sum(x * x for x in a))

        scores = []
        for _id, emb, text in self._items:
            if not emb:
                continue
            try:
                sim = dot(embedding, emb) / (norm(embedding) * norm(emb))
            except Exception:
                sim = 0.0
            # convert similarity to a distance-like number (1 - sim)
            scores.append((_id, 1.0 - sim, text))
        scores.sort(key=lambda x: x[1])
        return scores[:k]
