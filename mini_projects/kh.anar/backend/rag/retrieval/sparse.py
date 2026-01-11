"""Sparse retriever: BM25 minimal wrapper

We use rank_bm25 if available; otherwise a minimal in-memory fallback is
implemented for tests. BM25 gives lexical matching and complements dense
retrieval.
"""
from typing import List, Dict, Optional

try:
    from rank_bm25 import BM25Okapi
except Exception:
    BM25Okapi = None


class SparseRetriever:
    def __init__(self):
        self.docs = []
        self.doc_ids = []
        self.metadatas = []
        self.tokenized = []
        self.bm25 = None

    def add_chunk(self, chunk_id: str, text: str, metadata: Dict):
        """Add a single chunk (used by KB indexer)."""
        self.doc_ids.append(chunk_id)
        self.docs.append(text)
        self.metadatas.append(metadata)
        self.tokenized = [d.split() for d in self.docs]
        if BM25Okapi is not None:
            self.bm25 = BM25Okapi(self.tokenized)

    def add_chunks(self, chunks: List[Dict]):
        """Add multiple chunks (legacy dict-based signature)."""
        for c in chunks:
            self.doc_ids.append(c["id"])
            self.docs.append(c.get("text", ""))
            self.metadatas.append(c.get("metadata", {}))
        self.tokenized = [d.split() for d in self.docs]
        if BM25Okapi is not None:
            self.bm25 = BM25Okapi(self.tokenized)
    
    def delete_by_doc_id(self, doc_id: str):
        """Delete all chunks belonging to a document.
        
        Uses doc_id prefix matching (chunks are named doc_id:index).
        """
        prefix = f"{doc_id}:"
        # Find indices to keep (not matching doc_id prefix)
        keep_indices = [i for i, cid in enumerate(self.doc_ids) if not cid.startswith(prefix)]
        
        # Rebuild lists
        self.doc_ids = [self.doc_ids[i] for i in keep_indices]
        self.docs = [self.docs[i] for i in keep_indices]
        self.metadatas = [self.metadatas[i] for i in keep_indices]
        self.tokenized = [d.split() for d in self.docs]
        if BM25Okapi is not None:
            self.bm25 = BM25Okapi(self.tokenized) if self.tokenized else None

    def query(self, query: str, k=5, filter_ids: Optional[List[str]] = None):
        query_tokens = query.split()
        if self.bm25 is not None:
            scores = self.bm25.get_scores(query_tokens)
        else:
            # naive fallback: count token overlap
            scores = []
            for tokens in self.tokenized:
                overlap = len(set(tokens) & set(query_tokens))
                scores.append(overlap)
        scored = list(zip(self.doc_ids, self.docs, scores))
        # apply filter if given
        if filter_ids is not None:
            scored = [s for s in scored if s[0] in filter_ids]
        scored.sort(key=lambda x: x[2], reverse=True)
        results = []
        for doc_id, doc, score in scored[:k]:
            results.append({"id": doc_id, "score_sparse": score, "document": doc})
        return results
