"""Hybrid retriever that merges dense and sparse scores and applies threshold

This module performs score normalization and final score computation using
configurable weights. It also contains the 'no_hit' logic to drive fallback.
"""
from typing import List, Dict, Any
import math


def _min_max_norm(scores: List[float]):
    """Min-max normalize a list of scores.

    Why min-max? It's simple and keeps the range [0,1] which plays nicely with
    weighted combinations. Alternative (z-score) could be more robust to
    outliers but introduces negative values and depends on distribution.
    Tradeoff: min-max is sensitive to extremes so we guard the constant case.
    """
    if not scores:
        return []
    mn = min(scores)
    mx = max(scores)
    if math.isclose(mx, mn):
        return [1.0 for _ in scores]
    return [(s - mn) / (mx - mn) for s in scores]


class HybridRetriever:
    def __init__(self, dense_retriever, sparse_retriever, config):
        self.dense = dense_retriever
        self.sparse = sparse_retriever
        self.config = config

    def retrieve(self, query_embedding, query_text, k=None, filters=None):
        k = k or self.config.k
        dense_res = self.dense.query(query_embedding, k=k, filters=filters)
        sparse_res = self.sparse.query(query_text, k=k)

        # Map results by id for merge
        by_id = {}
        for i, r in enumerate(dense_res):
            _id = r["id"]
            by_id.setdefault(_id, {}).update({"score_vector": r.get("score_vector", 0), "document": r.get("document"), "metadata": r.get("metadata")})
        for i, r in enumerate(sparse_res):
            _id = r["id"]
            by_id.setdefault(_id, {}).update({"score_sparse": r.get("score_sparse", 0), "document": r.get("document")})

        ids = list(by_id.keys())
        dense_scores = [by_id[_id].get("score_vector", 0) for _id in ids]
        sparse_scores = [by_id[_id].get("score_sparse", 0) for _id in ids]

        dense_norm = _min_max_norm(dense_scores)
        sparse_norm = _min_max_norm(sparse_scores)

        merged = []
        for idx, _id in enumerate(ids):
            ds = dense_norm[idx] if idx < len(dense_norm) else 0
            ss = sparse_norm[idx] if idx < len(sparse_norm) else 0
            final = self.config.w_dense * ds + self.config.w_sparse * ss
            entry = {"id": _id, "score_vector": ds, "score_sparse": ss, "score_final": final, "document": by_id[_id].get("document"), "metadata": by_id[_id].get("metadata")}
            merged.append(entry)

        merged.sort(key=lambda x: x["score_final"], reverse=True)

        # threshold logic
        if not merged or merged[0]["score_final"] < self.config.threshold:
            return {"hits": [], "decision": "no_hit", "topk": merged}
        return {"hits": merged[:k], "decision": "hit", "topk": merged}


def _get(d, idx, key):
    k = list(d.keys())[idx]
    return d[k].get(key, 0)
