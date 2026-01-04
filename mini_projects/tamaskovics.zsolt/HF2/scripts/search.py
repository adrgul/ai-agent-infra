#!/usr/bin/env python3
import os, json, argparse
import requests
from dotenv import load_dotenv
from openai import OpenAI

def main() -> int:
    load_dotenv()

    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True, help="pl: it / hr / compliance / ops / general")
    ap.add_argument("--query", required=True)
    ap.add_argument("--role", default=None, help="opcionális: pl hr / it / ops ... (ha nincs, nincs ACL szűrés)")
    ap.add_argument("--top_k", type=int, default=int(os.getenv("TOP_K", "6")))
    ap.add_argument("--min_score", type=float, default=float(os.getenv("MIN_SCORE", "0.25")))
    args = ap.parse_args()

    qdrant_url = os.getenv("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "CHANGEME":
        raise SystemExit("OPENAI_API_KEY nincs beállítva (.env vagy export)")

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

    body = {
        "vector": qvec,
        "limit": args.top_k,
        "with_payload": True,
        "score_threshold": args.min_score,
    }
    if qdrant_filter:
        body["filter"] = qdrant_filter

    r = requests.post(
        f"{qdrant_url}/collections/{args.domain}/points/search",
        json=body,
        timeout=60
    )
    r.raise_for_status()
    data = r.json()

    hits = data.get("result", [])
    out = []
    for h in hits:
        p = (h.get("payload") or {})
        out.append({
            "score": h.get("score"),
            "doc_id": p.get("doc_id"),
            "chunk_id": p.get("chunk_id"),
            "title": p.get("title"),
            "source": p.get("source"),
            "acl_public": p.get("acl_public"),
            "acl_roles": p.get("acl_roles"),
            "text_preview": (p.get("text","")[:200] + ("..." if len(p.get("text","")) > 200 else "")),
        })

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
