"""Citation mapper

Given retrieval hits and the final answer, map which chunks were used
as citations. This is kept separate for testability.
"""
from typing import List, Dict


def map_citations(answer_text: str, hits: List[Dict]):
    # naive implementation: mark any hit whose chunk text or doc title appears
    # in answer_text. More sophisticated approaches could use n-gram overlap or
    # model-based attribution; we keep it simple and deterministic for tests.
    cited = []
    for h in hits:
        if h.get("document") and (h["document"][:100] in answer_text or (h.get("metadata", {}).get("title") or "") in answer_text):
            cited.append({"id": h["id"], "doc_id": h.get("metadata", {}).get("doc_id"), "title": h.get("metadata", {}).get("title")})
    return cited
