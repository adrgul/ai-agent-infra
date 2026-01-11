"""KB Indexer Orchestrator

Design rationale:
- Orchestrates the full KB ingestion pipeline: scan → parse → chunk → embed → index.
- SRP: Each step delegates to specialized modules (scanner, parser, chunker, retrievers).
- DIP: Depends on interfaces/config, not concrete implementations.
- Handles incremental updates: only reindex changed documents.

Lifecycle:
1. Scan kb-data folder for documents
2. Compare with version store to detect new/changed/removed docs
3. For changed docs: delete old chunks, re-chunk, re-embed, re-index
4. For removed docs: delete chunks from indices
5. Update version store

Why this approach:
- Deterministic: same files => same index state.
- Incremental: fast updates; only process changed files.
- Observable: logs every action with counts and timings.
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional
import logging
import time
from datetime import datetime, timezone

from rag.config import RAGConfig
from rag.chunking.chunker import DeterministicChunker
from rag.embeddings.embedder import Embedder
from rag.retrieval.dense import DenseRetriever
from rag.retrieval.sparse import SparseRetriever
from rag.ingestion.scanner import scan_kb_folder
from rag.ingestion.pdf_parser import parse_pdf
from rag.ingestion.version_store import VersionStore

logger = logging.getLogger(__name__)


class KBIndexer:
    """Orchestrates KB document ingestion and indexing.
    
    Design:
    - Stateless orchestrator; state lives in version_store and retrievers.
    - Each ingest call reconciles folder state with index state.
    - Thread-safe for single-process use.
    """
    
    def __init__(
        self,
        config: RAGConfig,
        dense_retriever: DenseRetriever,
        sparse_retriever: SparseRetriever,
        embedder: Embedder,
        version_store: VersionStore,
        chunker: Optional[DeterministicChunker] = None,
    ):
        self.config = config
        self.dense = dense_retriever
        self.sparse = sparse_retriever
        self.embedder = embedder
        self.version_store = version_store
        self.chunker = chunker or DeterministicChunker(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        )
        self.kb_dir = Path(config.kb_data_dir)
    
    def ingest_incremental(self) -> dict:
        """Incremental ingestion: only process new/changed documents.
        
        Returns:
            Dict with stats: new, updated, removed, total_chunks
        """
        start_time = time.time()
        logger.info(f"Starting incremental KB ingestion from {self.kb_dir}")
        
        # Scan folder
        discovered = scan_kb_folder(self.kb_dir)
        discovered_ids = {d["doc_id"] for d in discovered}
        
        # Compare with version store
        tracked_ids = set(self.version_store.get_all_doc_ids())
        
        new_docs = [d for d in discovered if d["doc_id"] not in tracked_ids]
        updated_docs = [
            d for d in discovered 
            if d["doc_id"] in tracked_ids and self.version_store.has_changed(d["doc_id"], d["version_hash"])
        ]
        removed_ids = tracked_ids - discovered_ids
        
        logger.info(f"KB scan: {len(new_docs)} new, {len(updated_docs)} updated, {len(removed_ids)} removed")
        
        total_chunks = 0
        
        # Process new documents
        for doc_meta in new_docs:
            chunks = self._process_document(doc_meta)
            total_chunks += len(chunks)
            self.version_store.update(
                doc_meta["doc_id"],
                doc_meta["version_hash"],
                doc_meta["file_path"],
                len(chunks),
            )
        
        # Process updated documents (delete old chunks first)
        for doc_meta in updated_docs:
            self._delete_document_chunks(doc_meta["doc_id"])
            chunks = self._process_document(doc_meta)
            total_chunks += len(chunks)
            self.version_store.update(
                doc_meta["doc_id"],
                doc_meta["version_hash"],
                doc_meta["file_path"],
                len(chunks),
            )
        
        # Process removed documents
        for doc_id in removed_ids:
            self._delete_document_chunks(doc_id)
            self.version_store.remove(doc_id)
        
        elapsed = time.time() - start_time
        logger.info(f"KB ingestion complete: {total_chunks} chunks indexed in {elapsed:.2f}s")
        
        return {
            "new": len(new_docs),
            "updated": len(updated_docs),
            "removed": len(removed_ids),
            "total_chunks": total_chunks,
            "elapsed_s": elapsed,
        }
    
    def ingest_full_reindex(self) -> dict:
        """Full reindex: clear version store and reindex all documents.
        
        Use when:
        - Chunking config changed
        - Embedding model changed
        - Index corruption suspected
        
        Returns:
            Dict with stats: total_docs, total_chunks, elapsed_s
        """
        start_time = time.time()
        logger.info(f"Starting full KB reindex from {self.kb_dir}")
        
        # Clear version store
        self.version_store.clear()
        
        # Note: We don't clear the dense/sparse indices here because they may
        # contain manually added docs. For a true clean slate, the caller should
        # delete the chroma_dir and reinitialize. For incremental behavior, we
        # rely on delete_document_chunks to remove old data.
        
        # Scan and process all documents
        discovered = scan_kb_folder(self.kb_dir)
        total_chunks = 0
        
        for doc_meta in discovered:
            chunks = self._process_document(doc_meta)
            total_chunks += len(chunks)
            self.version_store.update(
                doc_meta["doc_id"],
                doc_meta["version_hash"],
                doc_meta["file_path"],
                len(chunks),
            )
        
        elapsed = time.time() - start_time
        logger.info(f"Full reindex complete: {len(discovered)} docs, {total_chunks} chunks in {elapsed:.2f}s")
        
        return {
            "total_docs": len(discovered),
            "total_chunks": total_chunks,
            "elapsed_s": elapsed,
        }
    
    def _process_document(self, doc_meta: dict) -> List:
        """Parse, chunk, embed, and index a single document.
        
        Returns:
            List of chunks indexed
        """
        file_path = Path(doc_meta["file_path"])
        doc_id = doc_meta["doc_id"]
        ext = doc_meta["extension"]
        
        logger.debug(f"Processing document: {doc_id} ({ext})")
        
        # Parse based on extension
        if ext == ".pdf":
            parse_result = parse_pdf(file_path)
            text = parse_result.text
            doc_metadata = {
                "doc_id": doc_id,
                "title": parse_result.metadata.get("title") or file_path.name,
                "source": str(file_path),
                "doc_type": "pdf",
                "version_hash": doc_meta["version_hash"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        elif ext in [".txt", ".md"]:
            text = file_path.read_text(encoding="utf-8")
            doc_metadata = {
                "doc_id": doc_id,
                "title": file_path.name,
                "source": str(file_path),
                "doc_type": ext.lstrip("."),
                "version_hash": doc_meta["version_hash"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            logger.warning(f"Unsupported file type: {ext} for {doc_id}")
            return []
        
        # Chunk
        chunks = self.chunker.chunk(doc_id, text, doc_metadata)
        
        if not chunks:
            logger.warning(f"No chunks generated for {doc_id}")
            return []
        
        # Embed and index
        chunk_texts = [c.text for c in chunks]
        chunk_ids = [c.chunk_id for c in chunks]
        chunk_metas = [c.metadata for c in chunks]
        
        embeddings = self.embedder.embed_batch(chunk_texts)
        
        # Add to dense index
        self.dense.add_chunks(chunk_ids, embeddings, chunk_texts, chunk_metas)
        
        # Add to sparse index
        for chunk_id, text, meta in zip(chunk_ids, chunk_texts, chunk_metas):
            self.sparse.add_chunk(chunk_id, text, meta)
        
        logger.debug(f"Indexed {len(chunks)} chunks for {doc_id}")
        
        return chunks
    
    def _delete_document_chunks(self, doc_id: str) -> None:
        """Delete all chunks for a document from indices.
        
        Design note:
        - We use doc_id prefix matching to find and delete chunks.
        - For Chroma, we filter by metadata.doc_id.
        - For sparse index, we remove by chunk_id prefix.
        """
        logger.debug(f"Deleting chunks for doc_id: {doc_id}")
        
        # Delete from dense index (ChromaDB)
        # Note: This requires the dense retriever to support deletion by metadata filter.
        # We'll add a delete_by_doc_id method to DenseRetriever.
        try:
            self.dense.delete_by_doc_id(doc_id)
        except AttributeError:
            logger.warning("DenseRetriever does not support delete_by_doc_id; skipping dense deletion")
        
        # Delete from sparse index
        # Note: SparseRetriever needs a delete_by_doc_id method as well.
        try:
            self.sparse.delete_by_doc_id(doc_id)
        except AttributeError:
            logger.warning("SparseRetriever does not support delete_by_doc_id; skipping sparse deletion")
