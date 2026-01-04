#!/usr/bin/env python3
import os, json, argparse
import requests
from dotenv import load_dotenv
from openai import OpenAI


def qdrant_search(qdrant_url: str, collection: str, vector, limit: int, min_score: float, qfilter):
    body = {
        "vector": vector,
        "limit": limit,
        "with_payload": True,
        "score_threshold": min_score,
    }
    if qfilter:
        body["filter"] = qfilter

    r = requests.post(
        f"{qdrant_url}/collections/{collection}/points/search",
        json=body,
        timeout=60
    )
    r.raise_for_status()
    return r.json().get("result", [])


def main() -> int:
    load_dotenv()

    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--role", default=None, help="opcionális ACL: pl hr/it/ops (ha nincs, nincs szűrés)")
    ap.add_argument("--top_k", type=int, default=int(os.getenv("TOP_K", "6")))
    ap.add_argument("--min_score", type=float, default=float(os.getenv("MIN_SCORE", "0.25")))
    ap.add_argument("--router_threshold", type=float, default=float(os.getenv("ROUTER_THRESHOLD", "0.18")))
    ap.add_argument("--fallback", choices=["general", "all"], default="general")
    args = ap.parse_args()

    qdrant_url = os.getenv("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "CHANGEME":
        raise SystemExit("OPENAI_API_KEY nincs beállítva (.env vagy export)")

    domains = [d.strip() for d in os.getenv("DOMAINS", "hr,compliance,it,ops,general").split(",") if d.strip()]

    client = OpenAI(api_key=api_key)
    qvec = client.embeddings.create(model=model, input=args.query).data[0].embedding

    qdrant_filter = None
    if args.role:
        # public OR role-hoz engedett
        qdrant_filter = {
            "should": [
                {"key": "acl_public", "match": {"value": True}},
                {"key": "acl_roles", "match": {"value": args.role}},
            ]
        }

    # Router probe: top1 per domain
    scores = {}
    best_domain = None
    best_score = -1.0

    for d in domains:
        hits = qdrant_search(qdrant_url, d, qvec, limit=1, min_score=0.0, qfilter=qdrant_filter)
        score = float(hits[0]["score"]) if hits else 0.0
        scores[d] = score
        if score > best_score:
            best_score = score
            best_domain = d

    picked = best_domain or "general"
    mode = "picked"
    results = []

    # Decide + search
    if best_score < args.router_threshold:
        mode = f"fallback:{args.fallback}"
        if args.fallback == "general":
            picked = "general"
            results = qdrant_search(qdrant_url, "general", qvec, limit=args.top_k, min_score=args.min_score, qfilter=qdrant_filter)
        else:
            pool = []
            for d in domains:
                pool.extend(qdrant_search(qdrant_url, d, qvec, limit=args.top_k, min_score=args.min_score, qfilter=qdrant_filter))
            pool.sort(key=lambda x: x.get("score", 0.0), reverse=True)
            results = pool[: args.top_k]
    else:
        results = qdrant_search(qdrant_url, picked, qvec, limit=args.top_k, min_score=args.min_score, qfilter=qdrant_filter)

    out = {
        "query": args.query,
        "picked_domain": picked,
        "router_mode": mode,
        "router_threshold": args.router_threshold,
        "domain_scores_top1": scores,
        "results": [
            {
                "score": r.get("score"),
                "domain": (r.get("payload") or {}).get("domain", picked),
                "doc_id": (r.get("payload") or {}).get("doc_id"),
                "chunk_id": (r.get("payload") or {}).get("chunk_id"),
                "title": (r.get("payload") or {}).get("title"),
                "source": (r.get("payload") or {}).get("source"),
                "text_preview": (
                    ((r.get("payload") or {}).get("text", "")[:200]) +
                    ("..." if len((r.get("payload") or {}).get("text", "")) > 200 else "")
                ),
            }
            for r in results
        ],
    }

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
