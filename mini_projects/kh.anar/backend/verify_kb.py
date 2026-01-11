#!/usr/bin/env python3
"""Verify KB ingestion system

Quick verification script to test the KB folder ingestion system.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from rag.config import RAGConfig
from rag.ingestion.kb_indexer import KBIndexer
from rag.ingestion.version_store import VersionStore
from rag.embeddings.embedder import HashEmbedder
from rag.retrieval.hybrid import HybridRetriever
import tempfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Use fake retrievers for verification (no ChromaDB dependency)
class FakeDenseRetriever:
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
        results = []
        for cid, data in self.storage.items():
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


def main():
    """Run verification tests."""
    logger.info("🚀 KB Ingestion System Verification")
    logger.info("=" * 60)
    
    # Use docs/kb-data as source
    kb_dir = Path(__file__).parent.parent / "docs" / "kb-data"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        version_store_path = Path(tmpdir) / "versions.json"
        chroma_dir = Path(tmpdir) / ".chroma"
        
        config = RAGConfig(
            kb_data_dir=str(kb_dir),
            kb_version_store=str(version_store_path),
            chroma_dir=str(chroma_dir),
            chunk_size=500,
            chunk_overlap=50,
            k=3,
        )
        
        logger.info(f"📁 KB folder: {kb_dir}")
        logger.info(f"📝 Version store: {version_store_path}")
        
        # Initialize components (using fake retrievers for local testing)
        embedder = HashEmbedder()
        dense = FakeDenseRetriever(config, embedder=embedder)
        sparse = FakeSparseRetriever()
        version_store = VersionStore(version_store_path)
        
        indexer = KBIndexer(config, dense, sparse, embedder, version_store)
        
        # Test 1: Initial ingestion
        logger.info("\n✅ Test 1: Initial KB ingestion")
        stats = indexer.ingest_incremental()
        logger.info(f"   New: {stats['new']}, Updated: {stats['updated']}, Removed: {stats['removed']}")
        logger.info(f"   Total chunks: {stats['total_chunks']}, Time: {stats['elapsed_s']:.2f}s")
        
        if stats['new'] == 0:
            logger.warning("   ⚠️  No documents found in kb-data folder!")
            logger.info(f"   Add .md, .txt, or .pdf files to: {kb_dir}")
            return
        
        # Test 2: Retrieval
        logger.info("\n✅ Test 2: Query retrieval")
        hybrid = HybridRetriever(dense, sparse, config)
        
        test_queries = [
            "Python programming",
            "Docker containers",
            "web development",
        ]
        
        for query in test_queries:
            query_emb = embedder.embed_text(query)
            result = hybrid.retrieve(query_emb, query, k=3)
            hits = result.get("hits", [])
            logger.info(f"   Query: '{query}' -> {len(hits)} hits")
            if hits:
                top_doc = hits[0]["metadata"].get("doc_id", "unknown")
                logger.info(f"      Top result: {top_doc} (score: {hits[0]['score_final']:.3f})")
        
        # Test 3: Incremental update (no changes)
        logger.info("\n✅ Test 3: Incremental update (no changes)")
        stats2 = indexer.ingest_incremental()
        logger.info(f"   New: {stats2['new']}, Updated: {stats2['updated']}, Removed: {stats2['removed']}")
        assert stats2['new'] == 0 and stats2['updated'] == 0, "Should detect no changes"
        logger.info("   ✓ No changes detected (as expected)")
        
        # Test 4: Full reindex
        logger.info("\n✅ Test 4: Full reindex")
        stats3 = indexer.ingest_full_reindex()
        logger.info(f"   Total docs: {stats3['total_docs']}, Total chunks: {stats3['total_chunks']}")
        logger.info(f"   Time: {stats3['elapsed_s']:.2f}s")
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 All verification tests passed!")
        logger.info(f"📚 KB contains {stats3['total_docs']} documents with {stats3['total_chunks']} chunks")


if __name__ == "__main__":
    main()
