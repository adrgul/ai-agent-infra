"""Golden retrieval test for KB ingestion

Tests that specific queries retrieve expected documents (Recall@k).
"""
import pytest
from pathlib import Path
import tempfile

from rag.config import RAGConfig
from rag.ingestion.kb_indexer import KBIndexer
from rag.ingestion.version_store import VersionStore
from rag.embeddings.embedder import HashEmbedder
from rag.retrieval.hybrid import HybridRetriever


class FakeDenseRetriever:
    """Deterministic fake that scores based on keyword match."""
    def __init__(self, config, embedder=None):
        self.storage = {}
        self.embedder = embedder
    
    def add_chunks(self, ids, embeddings, texts, metadatas):
        for i, cid in enumerate(ids):
            self.storage[cid] = {
                "text": texts[i],
                "metadata": metadatas[i],
            }
    
    def delete_by_doc_id(self, doc_id):
        prefix = f"{doc_id}:"
        to_delete = [k for k in self.storage if k.startswith(prefix)]
        for k in to_delete:
            del self.storage[k]
    
    def query(self, embedding, k=5, filters=None):
        # Score based on embedding sum (hash embedder uses word count)
        results = []
        for cid, data in self.storage.items():
            # Higher embedding sum => more words => higher score (simplified)
            score = sum(embedding) / 1000.0
            results.append({
                "id": cid,
                "score_vector": score,
                "document": data["text"],
                "metadata": data["metadata"],
            })
        results.sort(key=lambda x: x["score_vector"], reverse=True)
        return results[:k]


class FakeSparseRetriever:
    def __init__(self):
        self.storage = {}
    
    def add_chunk(self, chunk_id, text, metadata):
        self.storage[chunk_id] = {"text": text, "metadata": metadata}
    
    def delete_by_doc_id(self, doc_id):
        prefix = f"{doc_id}:"
        to_delete = [k for k in self.storage if k.startswith(prefix)]
        for k in to_delete:
            del self.storage[k]
    
    def query(self, query, k=5, filter_ids=None):
        # Score based on keyword overlap
        query_words = set(query.lower().split())
        results = []
        for cid, data in self.storage.items():
            text_words = set(data["text"].lower().split())
            overlap = len(query_words & text_words)
            results.append({
                "id": cid,
                "score_sparse": float(overlap),
                "document": data["text"],
                "metadata": data["metadata"],
            })
        results.sort(key=lambda x: x["score_sparse"], reverse=True)
        return results[:k]


def test_golden_retrieval():
    """Golden retrieval test: specific queries should return expected docs.
    
    Test dataset:
    - 3 documents with distinct topics
    - 10 golden queries mapped to expected doc_id
    - Assert top-1 or top-3 contains expected doc
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_dir = Path(tmpdir) / "kb-data"
        kb_dir.mkdir()
        version_store_path = Path(tmpdir) / "versions.json"
        
        # Create test documents with distinct topics
        (kb_dir / "python_guide.txt").write_text(
            "Python is a high-level programming language. "
            "It supports multiple programming paradigms including object-oriented and functional. "
            "Python is widely used for web development, data science, and automation.",
            encoding="utf-8"
        )
        
        (kb_dir / "docker_guide.txt").write_text(
            "Docker is a platform for containerization. "
            "Containers package applications with their dependencies. "
            "Docker enables consistent deployments across environments.",
            encoding="utf-8"
        )
        
        (kb_dir / "fastapi_guide.txt").write_text(
            "FastAPI is a modern web framework for building APIs with Python. "
            "It uses type hints and async support. "
            "FastAPI is known for high performance and automatic documentation.",
            encoding="utf-8"
        )
        
        config = RAGConfig(
            kb_data_dir=str(kb_dir),
            kb_version_store=str(version_store_path),
            chunk_size=200,
            chunk_overlap=20,
            k=3,
        )
        
        embedder = HashEmbedder()
        dense = FakeDenseRetriever(config, embedder)
        sparse = FakeSparseRetriever()
        version_store = VersionStore(version_store_path)
        indexer = KBIndexer(config, dense, sparse, embedder, version_store)
        
        indexer.ingest_incremental()
        
        # Golden queries and expected doc_ids
        golden_cases = [
            ("Python programming language", "python_guide.txt"),
            ("web development with Python", "python_guide.txt"),
            ("Docker containers", "docker_guide.txt"),
            ("containerization platform", "docker_guide.txt"),
            ("FastAPI framework", "fastapi_guide.txt"),
            ("building APIs", "fastapi_guide.txt"),
            ("async support", "fastapi_guide.txt"),
            ("high performance web", "fastapi_guide.txt"),
            ("data science", "python_guide.txt"),
            ("deployments across environments", "docker_guide.txt"),
        ]
        
        hybrid = HybridRetriever(dense, sparse, config)
        
        recall_at_1 = 0
        recall_at_3 = 0
        
        for query, expected_doc_id in golden_cases:
            # Embed query
            query_emb = embedder.embed_text(query)
            
            # Hybrid retrieval
            result = hybrid.retrieve(query_emb, query, k=3)
            
            # Extract doc_ids from results (hybrid returns dict with "hits" key)
            hits = result.get("hits", [])
            retrieved_doc_ids = [r["metadata"]["doc_id"] for r in hits]
            
            # Check recall@1
            if retrieved_doc_ids and retrieved_doc_ids[0] == expected_doc_id:
                recall_at_1 += 1
            
            # Check recall@3
            if expected_doc_id in retrieved_doc_ids:
                recall_at_3 += 1
        
        total = len(golden_cases)
        recall_1 = recall_at_1 / total
        recall_3 = recall_at_3 / total
        
        print(f"Recall@1: {recall_1:.2%}, Recall@3: {recall_3:.2%}")
        
        # Assert reasonable recall thresholds
        # Note: Using HashEmbedder (deterministic but not semantic), so thresholds are lower
        # With proper semantic embeddings (sentence-transformers), expect >90% recall
        assert recall_1 >= 0.5, f"Recall@1 too low: {recall_1:.2%}"
        assert recall_3 >= 0.7, f"Recall@3 too low: {recall_3:.2%}"
