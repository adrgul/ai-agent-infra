"""Vector store abstraction and ChromaDB implementation.

Provides a minimal VectorStore interface and a Chroma-backed concrete
implementation that persists embeddings on disk.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import uuid
import logging

import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi
import math

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    @abstractmethod
    def add(self, id: str, text: str, embedding: List[float]) -> None:
        """Add a vector with metadata to the store."""

    @abstractmethod
    def similarity_search(self, embedding: List[float], k: int = 3) -> List[Tuple[str, float, str]]:
        """Return top-k (id, distance, text) tuples ordered by distance ascending."""

    @abstractmethod
    def hybrid_search(self, embedding: List[float], query_text: str, k: int = 3, alpha: float = 0.5) -> List[Tuple[str, float, str]]:
        """Hybrid search combining semantic similarity and BM25 ranking.

        alpha: weighting for semantic score (0..1). BM25 weight = 1-alpha.
        Returns list of (id, combined_score, text) ordered by combined_score desc.
        """


class ChromaVectorStore(VectorStore):
    def __init__(self, persist_dir: str = "./chroma_db", collection_name: str = "prompts") -> None:
        settings = Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_dir)
        self.client = chromadb.Client(settings)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        # Load existing documents for BM25 and keep tokenized docs for incremental updates
        self._ids: List[str] = []
        self._docs: List[str] = []
        self._tokenized_docs: List[List[str]] = []
        self._bm25: Optional[BM25Okapi] = None
        try:
            all_data = self.collection.get(include=["ids", "documents"]) or {}
            ids = all_data.get("ids", [[]])[0] if all_data.get("ids") else []
            docs = all_data.get("documents", [[]])[0] if all_data.get("documents") else []
            if ids and docs:
                self._ids = ids
                self._docs = docs
                # tokenize once and keep tokenized list for incremental updates
                self._tokenized_docs = [doc.split() for doc in self._docs]
                if self._tokenized_docs:
                    self._bm25 = BM25Okapi(self._tokenized_docs)
        except Exception:
            # If getting documents fails (older chroma versions), continue without BM25
            self._ids = []
            self._docs = []
            self._tokenized_docs = []
            self._bm25 = None

    def add(self, id: str, text: str, embedding: List[float]) -> None:
        try:
            self.collection.add(ids=[id], documents=[text], embeddings=[embedding])
            # Persist is automatic for duckdb+parquet client, but we call persist to be explicit
            try:
                self.client.persist()
            except Exception:
                # Some chroma client versions don't expose persist()
                pass
            # Update BM25 index state incrementally: append tokenized doc and rebuild BM25 from tokenized list
            try:
                self._ids.append(id)
                self._docs.append(text)
                tokenized_new = text.split()
                self._tokenized_docs.append(tokenized_new)
                # Recreate BM25 using tokenized docs (avoids re-tokenizing existing docs)
                self._bm25 = BM25Okapi(self._tokenized_docs)
            except Exception:
                # Non-critical if BM25 update fails
                pass
        except Exception as exc:
            logger.error("Failed to add vector to Chroma: %s", exc)

    def similarity_search(self, embedding: List[float], k: int = 3) -> List[Tuple[str, float, str]]:
        if not embedding:
            return []
        try:
            result = self.collection.query(query_embeddings=[embedding], n_results=k, include=["documents", "distances", "ids"])
            docs = result.get("documents", [[]])[0]
            distances = result.get("distances", [[]])[0]
            ids = result.get("ids", [[]])[0]

            hits: List[Tuple[str, float, str]] = []
            for ident, dist, doc in zip(ids, distances, docs):
                hits.append((ident, float(dist), doc))

            return hits
        except Exception as exc:
            logger.error("Chroma similarity search failed: %s", exc)
            return []

    def hybrid_search(self, embedding: List[float], query_text: str, k: int = 3, alpha: float = 0.5) -> List[Tuple[str, float, str]]:
        """Combine semantic scores (from chroma distances) with BM25 scores.

        Strategy: get semantic distances for all documents, convert to semantic scores,
        compute BM25 scores for all documents, normalize both and compute weighted sum.
        """
        # if no docs, return empty
        if not self._docs:
            return []

        try:
            # Get semantic distances for all docs
            total_docs = len(self._ids)
            sem_result = self.collection.query(query_embeddings=[embedding], n_results=total_docs, include=["ids", "documents", "distances"])
            sem_ids = sem_result.get("ids", [[]])[0]
            sem_docs = sem_result.get("documents", [[]])[0]
            sem_distances = sem_result.get("distances", [[]])[0]

            # Map id -> semantic score (higher is better)
            sem_scores = {}
            for ident, dist in zip(sem_ids, sem_distances):
                # convert distance to score, avoid negative
                try:
                    s = 1.0 / (1.0 + float(dist)) if dist is not None else 0.0
                except Exception:
                    s = 0.0
                sem_scores[ident] = s

            # BM25 scores across corpus
            if self._bm25 is not None:
                tokenized_query = query_text.split()
                bm25_raw = self._bm25.get_scores(tokenized_query)
            else:
                bm25_raw = [0.0] * len(self._docs)

            # Normalize BM25 and semantic scores
            # Create maps id -> bm25
            id_to_bm25 = {ident: float(score) for ident, score in zip(self._ids, bm25_raw)}

            max_bm25 = max(bm25_raw) if bm25_raw else 0.0
            max_sem = max(sem_scores.values()) if sem_scores else 0.0

            combined_list: List[Tuple[str, float, str]] = []
            for ident, doc in zip(self._ids, self._docs):
                sem = sem_scores.get(ident, 0.0)
                bm25 = id_to_bm25.get(ident, 0.0)

                sem_norm = sem / max_sem if max_sem > 0.0 else sem
                bm25_norm = bm25 / max_bm25 if max_bm25 > 0.0 else bm25

                combined = alpha * sem_norm + (1.0 - alpha) * bm25_norm
                combined_list.append((ident, combined, doc))

            # Sort by combined score descending
            combined_list.sort(key=lambda x: x[1], reverse=True)
            return combined_list[:k]
        except Exception as exc:
            logger.error("Hybrid search failed: %s", exc)
            return []
