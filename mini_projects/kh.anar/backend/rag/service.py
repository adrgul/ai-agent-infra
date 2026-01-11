"""RAGService: orchestrates embedding, hybrid retrieval, telemetry and run_id

Provides a single entry point `route_and_retrieve` which performs:
  - normalization of query
  - embed the query
  - call dense + sparse retrievers via HybridRetriever
  - measure latencies and construct a telemetry dict (run_id, scores, topk, decision)

This keeps observability in one place and makes it easy to test the routing logic
where KB-first decisions are made (if top hit below threshold -> no_hit -> fallback)
"""
import time
import uuid
import logging
from typing import Dict, Any, Optional
from .config import RAGConfig

logger = logging.getLogger("rag.service")


class RAGService:
    def __init__(self, embedder, hybrid_retriever, config: RAGConfig):
        self.embedder = embedder
        self.hybrid = hybrid_retriever
        self.config = config

    def _normalize_query(self, q: str) -> str:
        return q.strip().lower()

    def route_and_retrieve(self, query: str, filters: Optional[Dict] = None, k: Optional[int] = None) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        norm_q = self._normalize_query(query)
        telemetry = {"run_id": run_id, "query": query, "query_normalized": norm_q, "filters": filters or {}, "k": k or self.config.k}
        start = time.time()
        emb_start = time.time()
        embedding = self.embedder.embed_text(norm_q) if self.embedder else None
        emb_end = time.time()
        telemetry["latency_embed_s"] = emb_end - emb_start

        # call hybrid retriever
        hybrid_start = time.time()
        res = self.hybrid.retrieve(embedding, norm_q, k=k or self.config.k, filters=filters)
        hybrid_end = time.time()
        telemetry["latency_retrieval_s"] = hybrid_end - hybrid_start

        telemetry["decision"] = res.get("decision")
        telemetry["topk"] = res.get("topk", [])
        telemetry["config_snapshot"] = {"k": self.config.k, "threshold": self.config.threshold, "w_dense": self.config.w_dense, "w_sparse": self.config.w_sparse}
        telemetry["elapsed_s"] = time.time() - start

        # structured log for observability
        logger.info({"event": "rag_query", "run_id": run_id, "telemetry": telemetry})

        # routing decision: if no_hit, the caller should fallback
        return telemetry
