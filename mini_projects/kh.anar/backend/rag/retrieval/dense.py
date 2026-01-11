"""Dense retriever using ChromaDB

This module encapsulates Chroma interactions so the rest of the app doesn't
depend on Chroma directly. The implementation supports incremental updates
(add/update/delete) and persists to disk when configured.

Why: Chroma gives a robust, persistent vector DB; isolating it behind an
interface makes it replaceable for tests and future drivers.
"""
from typing import List, Dict, Optional
from uuid import uuid4

# We import lazily to avoid making Chroma a hard requirement for unit tests
# that don't touch dense retrieval. In production, Chroma client will be used.
try:
    import chromadb
except Exception:
    chromadb = None


class DenseRetriever:
    def __init__(self, config, embedder=None):
        """embedder: optional embedder used to compute embeddings for chunks that
        don't provide precomputed embeddings (useful for ingestion).
        """
        self.config = config
        self.embedder = embedder
        self.client = None
        self.collection = None
        if chromadb is not None:
            self._init_chroma()

    def _init_chroma(self):
        """Initialize ChromaDB using the new v1.4+ API.
        
        Uses PersistentClient instead of the deprecated Client(settings=...) pattern.
        See: https://docs.trychroma.com/deployment/migration
        """
        self.client = chromadb.PersistentClient(path=self.config.chroma_dir)
        self.collection = self.client.get_or_create_collection(name=self.config.chroma_collection)

    def add_chunks(self, chunks_or_ids, embeddings=None, texts=None, metadatas=None):
        """Add chunks to chroma.
        
        Two signatures:
        1. add_chunks(chunks: List[Dict]) - each chunk: {id, text, embedding, metadata}
        2. add_chunks(ids, embeddings, texts, metadatas) - positional arrays
        
        We accept pre-computed embeddings for test determinism; in production
        caller may compute embeddings here as well.
        """
        if self.collection is None:
            raise RuntimeError("Chroma not available")
        
        # Detect signature
        if embeddings is None and texts is None and metadatas is None:
            # Dict-based signature
            chunks = chunks_or_ids
            ids = [c["id"] for c in chunks]
            metadatas = [c.get("metadata", {}) for c in chunks]
            documents = [c.get("text", "") for c in chunks]
            embeddings = [c.get("embedding") for c in chunks]
        else:
            # Positional signature
            ids = chunks_or_ids
            documents = texts
            metadatas = metadatas or [{} for _ in ids]
        
        # compute embeddings if not present and embedder is available
        if any(e is None for e in embeddings):
            if not self.embedder:
                raise RuntimeError("Embeddings missing and no embedder provided")
            embeddings = [e if e is not None else self.embedder.embed_text(doc) for e, doc in zip(embeddings, documents)]
        self.collection.upsert(ids=ids, metadatas=metadatas, documents=documents, embeddings=embeddings)

    def delete_chunks(self, ids: List[str]):
        if self.collection is None:
            raise RuntimeError("Chroma not available")
        self.collection.delete(where={"id": ids})
    
    def delete_by_doc_id(self, doc_id: str):
        """Delete all chunks belonging to a document by doc_id.
        
        Uses metadata filter to find chunks with matching doc_id.
        """
        if self.collection is None:
            raise RuntimeError("Chroma not available")
        try:
            # ChromaDB where filter for metadata.doc_id
            self.collection.delete(where={"doc_id": doc_id})
        except Exception as e:
            # Fallback: query for matching chunks and delete by ID
            # This is needed if metadata filtering in delete is not supported
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"delete with where filter failed, using fallback: {e}")
            res = self.collection.get(where={"doc_id": doc_id})
            if res and res["ids"]:
                self.collection.delete(ids=res["ids"])

    def query(self, embedding, k=5, filters: Optional[Dict] = None):
        if self.collection is None:
            raise RuntimeError("Chroma not available")
        res = self.collection.query(query_embeddings=[embedding], n_results=k, where=filters)
        # normalize into list of {id, score, metadata, document}
        results = []
        for ids, distances, documents, metadatas in zip(res["ids"], res["distances"], res["documents"], res["metadatas"]):
            for _id, dist, doc, meta in zip(ids, distances, documents, metadatas):
                results.append({"id": _id, "score_vector": 1 - dist, "document": doc, "metadata": meta})
        return results
