"""Ingestion module: document model, ingest pipeline, incremental updates

This module is responsible for converting Documents -> Chunks, computing
embeddings (or accepting them), and pushing chunks to both dense and sparse
indices. It follows SRP: ingestion only handles conversion and index calls,
not retrieval or synthesis.
"""
from dataclasses import dataclass
from typing import Dict, Any, List
from ..chunking.chunker import DeterministicChunker


@dataclass
class Document:
    doc_id: str
    title: str
    source: str
    doc_type: str
    version: str
    access_scope: str = "public"
    text: str = ""


class Ingester:
    def __init__(self, dense_retriever, sparse_retriever, embedder, config):
        self.chunker = DeterministicChunker(config.chunk_size, config.chunk_overlap)
        self.dense = dense_retriever
        self.sparse = sparse_retriever
        self.embedder = embedder
        self.config = config

    def ingest(self, doc: Document):
        chunks = self.chunker.chunk(doc.doc_id, doc.text)
        prepared = []
        for c in chunks:
            embedding = self.embedder.embed_text(c.text) if self.embedder else None
            prepared.append({
                "id": c.chunk_id,
                "text": c.text,
                "metadata": {"doc_id": c.doc_id, "title": doc.title, "source": doc.source, "doc_type": doc.doc_type, "version": doc.version, **c.metadata},
                "embedding": embedding,
            })
        # write to both indices
        self.dense.add_chunks(prepared)
        self.sparse.add_chunks(prepared)
        return prepared
