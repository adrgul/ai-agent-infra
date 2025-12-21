#!/usr/bin/env python3
import os, re, uuid, json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import requests
from dotenv import load_dotenv
from openai import OpenAI

# optional, but we want token-based chunking
try:
    import tiktoken
except Exception:
    tiktoken = None


def slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "doc"


def extract_title(md: str, fallback: str) -> str:
    for line in md.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()[:120] or fallback
        if line:
            return line[:120]
    return fallback


def chunk_text_tokens(text: str, chunk_size: int, overlap: int, model: str) -> List[str]:
    if tiktoken is None:
        # fallback: ~4 chars/token approximation
        cs = max(200, chunk_size * 4)
        ov = max(0, overlap * 4)
        chunks = []
        i = 0
        while i < len(text):
            chunks.append(text[i:i+cs])
            i += max(1, cs - ov)
        return chunks

    enc = tiktoken.get_encoding("cl100k_base")
    toks = enc.encode(text)
    chunks = []
    i = 0
    step = max(1, chunk_size - overlap)
    while i < len(toks):
        part = toks[i:i+chunk_size]
        chunks.append(enc.decode(part))
        i += step
    return chunks


def qdrant_upsert(qdrant_url: str, collection: str, points: List[Dict[str, Any]]) -> None:
    url = f"{qdrant_url.rstrip('/')}/collections/{collection}/points?wait=true"
    r = requests.put(url, json={"points": points}, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Qdrant upsert failed ({r.status_code}): {r.text[:500]}")


def main() -> int:
    load_dotenv()

    qdrant_url = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
    kb_root = Path(os.getenv("KB_ROOT", "kb_sources"))
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    chunk_size = int(os.getenv("CHUNK_SIZE", "600"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "80"))

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "CHANGEME":
        raise SystemExit("OPENAI_API_KEY nincs beállítva (.env)")

    client = OpenAI(api_key=api_key)

    domains_env = os.getenv("DOMAINS", "hr,compliance,it,ops,general")
    domains = [d.strip() for d in domains_env.split(",") if d.strip()]

    total_chunks = 0

    for domain in domains:
        domain_dir = kb_root / domain
        if not domain_dir.exists():
            continue

        md_files = sorted(domain_dir.glob("*.md"))
        if not md_files:
            continue

        batch: List[Dict[str, Any]] = []

        for fp in md_files:
            md = fp.read_text(encoding="utf-8", errors="ignore")
            md_norm = re.sub(r"\s+\n", "\n", md).strip()

            doc_id = slug(fp.stem)
            title = extract_title(md_norm, fp.stem)

            chunks = chunk_text_tokens(md_norm, chunk_size, chunk_overlap, embedding_model)

            for idx, ch in enumerate(chunks):
                ch = ch.strip()
                if not ch:
                    continue

                chunk_id = f"{doc_id}#{idx:03d}"
                point_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{domain}:{chunk_id}"))

                emb = client.embeddings.create(
                    model=embedding_model,
                    input=ch
                ).data[0].embedding

                payload = {
                    "domain": domain,
                    "doc_id": doc_id,
                    "title": title,
                    "source": str(fp),
                    "chunk_id": chunk_id,
                    "acl_roles": [],
                    "acl_public": True,
                    "text": ch,
                }

                batch.append({
                    "id": point_uuid,
                    "vector": emb,
                    "payload": payload,
                })

                total_chunks += 1

                # small batching
                if len(batch) >= 16:
                    qdrant_upsert(qdrant_url, domain, batch)
                    batch.clear()

        if batch:
            qdrant_upsert(qdrant_url, domain, batch)
            batch.clear()

    print(json.dumps({"status": "ok", "chunks_upserted": total_chunks}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
