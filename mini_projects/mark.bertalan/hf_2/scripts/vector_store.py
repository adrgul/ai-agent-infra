"""
ChromaDB-backed vector store.

Responsibility: persist embeddings + retrieve nearest neighbors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Sequence, Optional, Dict, Any

import chromadb
from chromadb.config import Settings

from scripts.interfaces import VectorDB


@dataclass(frozen=True)
class _Collections:
    """Holds the two collections we use (cosine + L2)."""
    cosine: any
    l2: any


class ChromaVectorStore(VectorDB):
    """VectorStore implementation using ChromaDB (persistent)."""

    def __init__(self, db_path: str, collection_name: str) -> None:
        self._client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collections = self._init_collections(collection_name)

    def _init_collections(self, base_name: str) -> _Collections:
        # Cosine similarity collection
        cosine = self._client.get_or_create_collection(
            name=base_name,
            metadata={"hnsw:space": "cosine"},
        )
        # Euclidean distance (k-NN) collection
        l2 = self._client.get_or_create_collection(
            name=f"{base_name}_knn",
            metadata={"hnsw:space": "l2"},
        )
        return _Collections(cosine=cosine, l2=l2)

    def add(self, id: str, text: str, embedding: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        payload = {
            "ids": [id],
            "documents": [text],
            "embeddings": [embedding],
        }
        if metadata:
            payload["metadatas"] = [metadata]

        # Keep both indices in sync
        self._collections.cosine.add(**payload)
        self._collections.l2.add(**payload)

    def similarity_search(
        self,
        embedding: List[float],
        k: int = 3,
    ) -> List[Tuple[str, float, float, str, Optional[Dict[str, Any]]]]:
        """
        Returns (id, cosine_distance, cosine_similarity, text, metadata)
        where similarity = 1 - distance.
        """
        res = self._collections.cosine.query(query_embeddings=[embedding], n_results=k)
        ids = self._first_or_empty(res.get("ids"))
        if not ids:
            return []

        distances = self._first_or_empty(res.get("distances"))
        docs = self._first_or_empty(res.get("documents"))
        metadatas = self._first_or_empty(res.get("metadatas"))

        out: List[Tuple[str, float, float, str, Optional[Dict[str, Any]]]] = []
        for i, (doc_id, dist, doc) in enumerate(zip(ids, distances, docs)):
            sim = 1.0 - float(dist)
            metadata = metadatas[i] if metadatas and i < len(metadatas) else None
            out.append((doc_id, float(dist), sim, doc, metadata))
        return out

    def knn_search(
        self,
        embedding: List[float],
        k: int = 3,
    ) -> List[Tuple[str, float, str, Optional[Dict[str, Any]]]]:
        """Returns (id, euclidean_distance, text, metadata). Lower distance is better."""
        res = self._collections.l2.query(query_embeddings=[embedding], n_results=k)
        ids = self._first_or_empty(res.get("ids"))
        if not ids:
            return []

        distances = self._first_or_empty(res.get("distances"))
        docs = self._first_or_empty(res.get("documents"))
        metadatas = self._first_or_empty(res.get("metadatas"))

        out = []
        for i, (doc_id, dist, doc) in enumerate(zip(ids, distances, docs)):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else None
            out.append((doc_id, float(dist), doc, metadata))
        return out

    @staticmethod
    def _first_or_empty(value: Optional[Sequence[Sequence]]) -> List:
        """
        Chroma returns nested lists like [[...]] for ids/distances/documents.
        This unwraps the first row safely.
        """
        if not value:
            return []
        first = value[0]
        return list(first) if first else []