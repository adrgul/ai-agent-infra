"""Integration tests for KB folder ingestion

Tests:
- End-to-end ingestion from folder
- Incremental updates (new/changed/removed docs)
- Full reindex
- Canary document retrieval
"""
import pytest
from pathlib import Path
import tempfile

from rag.config import RAGConfig
from rag.ingestion.kb_indexer import KBIndexer
from rag.ingestion.version_store import VersionStore
from rag.embeddings.embedder import HashEmbedder
from rag.retrieval.dense import DenseRetriever
from rag.retrieval.sparse import SparseRetriever


class FakeDenseRetriever:
    """In-memory fake for testing without ChromaDB."""
    def __init__(self, config, embedder=None):
        self.storage = {}
        self.embedder = embedder
    
    def add_chunks(self, ids, embeddings, texts, metadatas):
        for i, cid in enumerate(ids):
            self.storage[cid] = {
                "embedding": embeddings[i],
                "text": texts[i],
                "metadata": metadatas[i],
            }
    
    def delete_by_doc_id(self, doc_id):
        prefix = f"{doc_id}:"
        to_delete = [k for k in self.storage if k.startswith(prefix)]
        for k in to_delete:
            del self.storage[k]
    
    def query(self, embedding, k=5, filters=None):
        # Return chunks with matching metadata if filters provided
        results = []
        for cid, data in self.storage.items():
            if filters:
                match = all(data["metadata"].get(fk) == fv for fk, fv in filters.items())
                if not match:
                    continue
            results.append({
                "id": cid,
                "score_vector": 0.9,
                "document": data["text"],
                "metadata": data["metadata"],
            })
        return results[:k]


class FakeSparseRetriever:
    """In-memory fake for testing."""
    def __init__(self):
        self.storage = {}
    
    def add_chunk(self, chunk_id, text, metadata):
        self.storage[chunk_id] = {"text": text, "metadata": metadata}
    
    def delete_by_doc_id(self, doc_id):
        prefix = f"{doc_id}:"
        to_delete = [k for k in self.storage if k.startswith(prefix)]
        for k in to_delete:
            del self.storage[k]


def test_kb_incremental_ingest_new_doc():
    """Test ingesting a new document."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_dir = Path(tmpdir) / "kb-data"
        kb_dir.mkdir()
        version_store_path = Path(tmpdir) / "versions.json"
        
        # Create a test text document
        (kb_dir / "doc1.txt").write_text("This is test document one.", encoding="utf-8")
        
        config = RAGConfig(
            kb_data_dir=str(kb_dir),
            kb_version_store=str(version_store_path),
            chunk_size=100,
            chunk_overlap=10,
        )
        
        embedder = HashEmbedder()
        dense = FakeDenseRetriever(config, embedder)
        sparse = FakeSparseRetriever()
        version_store = VersionStore(version_store_path)
        
        indexer = KBIndexer(config, dense, sparse, embedder, version_store)
        
        stats = indexer.ingest_incremental()
        
        assert stats["new"] == 1
        assert stats["updated"] == 0
        assert stats["removed"] == 0
        assert stats["total_chunks"] > 0
        
        # Verify chunks indexed
        assert len(dense.storage) > 0
        assert len(sparse.storage) > 0


def test_kb_incremental_ingest_update_doc():
    """Test updating an existing document."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_dir = Path(tmpdir) / "kb-data"
        kb_dir.mkdir()
        version_store_path = Path(tmpdir) / "versions.json"
        
        doc_path = kb_dir / "doc1.txt"
        doc_path.write_text("Version 1", encoding="utf-8")
        
        config = RAGConfig(
            kb_data_dir=str(kb_dir),
            kb_version_store=str(version_store_path),
            chunk_size=100,
            chunk_overlap=10,
        )
        
        embedder = HashEmbedder()
        dense = FakeDenseRetriever(config, embedder)
        sparse = FakeSparseRetriever()
        version_store = VersionStore(version_store_path)
        indexer = KBIndexer(config, dense, sparse, embedder, version_store)
        
        # First ingest
        stats1 = indexer.ingest_incremental()
        assert stats1["new"] == 1
        chunks_after_first = len(dense.storage)
        
        # Update document
        doc_path.write_text("Version 2 - updated content", encoding="utf-8")
        
        # Second ingest
        stats2 = indexer.ingest_incremental()
        assert stats2["new"] == 0
        assert stats2["updated"] == 1
        assert stats2["removed"] == 0
        
        # Old chunks should be replaced
        chunks_after_update = len(dense.storage)
        # Since we delete old chunks and add new ones, count should reflect new chunks
        assert chunks_after_update > 0


def test_kb_incremental_ingest_remove_doc():
    """Test removing a document from folder."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_dir = Path(tmpdir) / "kb-data"
        kb_dir.mkdir()
        version_store_path = Path(tmpdir) / "versions.json"
        
        doc_path = kb_dir / "doc1.txt"
        doc_path.write_text("Document to be removed", encoding="utf-8")
        
        config = RAGConfig(
            kb_data_dir=str(kb_dir),
            kb_version_store=str(version_store_path),
            chunk_size=100,
            chunk_overlap=10,
        )
        
        embedder = HashEmbedder()
        dense = FakeDenseRetriever(config, embedder)
        sparse = FakeSparseRetriever()
        version_store = VersionStore(version_store_path)
        indexer = KBIndexer(config, dense, sparse, embedder, version_store)
        
        # First ingest
        stats1 = indexer.ingest_incremental()
        assert stats1["new"] == 1
        assert len(dense.storage) > 0
        
        # Remove document
        doc_path.unlink()
        
        # Second ingest
        stats2 = indexer.ingest_incremental()
        assert stats2["new"] == 0
        assert stats2["updated"] == 0
        assert stats2["removed"] == 1
        
        # Chunks should be deleted
        assert len(dense.storage) == 0
        assert len(sparse.storage) == 0


def test_kb_full_reindex():
    """Test full reindex clears version store and reindexes all."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_dir = Path(tmpdir) / "kb-data"
        kb_dir.mkdir()
        version_store_path = Path(tmpdir) / "versions.json"
        
        (kb_dir / "doc1.txt").write_text("Document 1", encoding="utf-8")
        (kb_dir / "doc2.txt").write_text("Document 2", encoding="utf-8")
        
        config = RAGConfig(
            kb_data_dir=str(kb_dir),
            kb_version_store=str(version_store_path),
            chunk_size=100,
            chunk_overlap=10,
        )
        
        embedder = HashEmbedder()
        dense = FakeDenseRetriever(config, embedder)
        sparse = FakeSparseRetriever()
        version_store = VersionStore(version_store_path)
        indexer = KBIndexer(config, dense, sparse, embedder, version_store)
        
        stats = indexer.ingest_full_reindex()
        
        assert stats["total_docs"] == 2
        assert stats["total_chunks"] > 0
        assert len(dense.storage) > 0


def test_kb_canary_document_retrieval():
    """Test that a canary document with unique token is retrievable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_dir = Path(tmpdir) / "kb-data"
        kb_dir.mkdir()
        version_store_path = Path(tmpdir) / "versions.json"
        
        # Create canary doc with unique token
        canary_content = "This is a CANARY_TOKEN_XYZ123 document for testing retrieval."
        (kb_dir / "canary.txt").write_text(canary_content, encoding="utf-8")
        
        config = RAGConfig(
            kb_data_dir=str(kb_dir),
            kb_version_store=str(version_store_path),
            chunk_size=100,
            chunk_overlap=10,
        )
        
        embedder = HashEmbedder()
        dense = FakeDenseRetriever(config, embedder)
        sparse = FakeSparseRetriever()
        version_store = VersionStore(version_store_path)
        indexer = KBIndexer(config, dense, sparse, embedder, version_store)
        
        indexer.ingest_incremental()
        
        # Query for canary token (fake embedding)
        results = dense.query([0.1] * 128, k=5)
        
        # At least one result should contain the canary token
        texts = [r["document"] for r in results]
        assert any("CANARY_TOKEN_XYZ123" in t for t in texts)
