"""Shared RAG instances for the application.

This module provides singleton-like shared instances of the RAG components
to ensure that all parts of the application use the same retrievers.

Critical for BM25 sparse retriever which is in-memory and non-persistent:
- If each endpoint creates its own SparseRetriever, they have separate data
- KB ingestion must populate the SAME instances used by the chat agent

Design:
- Initialize once at module load
- Import from here in routes.py, admin.py, main.py lifespan
- Ensures consistent state across requests
"""
from rag.config import default_config
from rag.embeddings.embedder import HashEmbedder
from rag.retrieval.dense import DenseRetriever
from rag.retrieval.sparse import SparseRetriever
from rag.retrieval.hybrid import HybridRetriever
from rag.service import RAGService

# Shared instances - initialized once at module import
embedder = HashEmbedder()
dense_retriever = DenseRetriever(default_config, embedder=embedder)
sparse_retriever = SparseRetriever()
hybrid_retriever = HybridRetriever(dense_retriever, sparse_retriever, default_config)
rag_service = RAGService(embedder, hybrid_retriever, default_config)
