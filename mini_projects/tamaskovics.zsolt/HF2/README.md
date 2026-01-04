# HF2 – Internal Knowledge Base Vectorization (Qdrant)

## Cél
Belső tudásbázis (Markdown fájlok) **vektorizálása** és **hasonlósági keresése** domainenként szétválasztott Qdrant collectionökben.

HF2 scope: **Retrieval** (ingest + vector search). Nincs LLM válaszgenerálás (az tipikusan HF3).

---

## Mi az a Qdrant?
**Vector database**: embedding (vektor) tárolás + gyors similarity search (Cosine/Dot/Euclid).

- Nem generál szöveget
- Nem készít embeddinget
- Csak indexel + keres a vektorokon

---

## Architektúra (röviden)
1) `kb_sources/<domain>/*.md` → forrás tudás  
2) `scripts/ingest.py`  
   - chunkolás (CHUNK_SIZE + CHUNK_OVERLAP)  
   - embedding generálás OpenAI embeddings endpointtal  
   - upsert Qdrantba domain collectionbe  
3) `scripts/search.py`  
   - query → embedding  
   - Qdrant `points/search` → top-k találat payload-dal  
4) `scripts/router_search.py` (demo / praktikus)  
   - automatikus domain kiválasztás a top1 score alapján (LLM nélkül)  
   - majd rendes top-k keresés a kiválasztott domainben  

---

## Projekt struktúra
```
HF2/
  compose.yml
  .env.example
  .gitignore
  kb_sources/
    hr/ compliance/ it/ ops/ general/
  qdrant_storage/              # bind mount, perzisztens (gitignore)
  scripts/
    bootstrap.sh
    create_collections.sh
    ingest.py
    search.py
    router_search.py
  requirements.txt
  README.md
```

---

## Perzisztencia
A Qdrant storage bind mounton van:
- `./qdrant_storage:/qdrant/storage`

Ezért konténer restart után is megmarad:
- collectionök
- index
- feltöltött pontok

---

## Konfig
`./.env.example` minta, a valós `.env` nincs gitben.

Fontosabb változók:
- `QDRANT_URL` (default: `http://127.0.0.1:6333`)
- `VECTOR_SIZE` (default: `1536`)
- `EMBEDDING_MODEL` (default: `text-embedding-3-small`)
- `CHUNK_SIZE`, `CHUNK_OVERLAP`
- `TOP_K`, `MIN_SCORE`
- `DOMAINS=hr,compliance,it,ops,general`
- `ROUTER_THRESHOLD` (default: `0.18`) – router minimum score a domain kiválasztáshoz

⚠️ `VECTOR_SIZE` és `EMBEDDING_MODEL` összhangban legyen (különben Qdrant hibázik).

---

## Gyors indítás (reprodukálható)

### 1) OpenAI API key (shell env-be)
```bash
read -s -p "OPENAI_API_KEY=" OPENAI_API_KEY; echo
export OPENAI_API_KEY
```

### 2) Bootstrap (idempotens)
Feladata:
- Qdrant felhúzás compose-ból
- readiness check
- collectionök létrehozása (idempotens)
- python venv + deps
- ingest (ha van OPENAI_API_KEY)

```bash
./scripts/bootstrap.sh
```

---

## Demo parancsok

### Domain routing (LLM nélkül)
```bash
./.venv/bin/python scripts/router_search.py --query "Sev1 war-room" --min_score 0.0
./.venv/bin/python scripts/router_search.py --query "eszköz kiadás onboarding" --min_score 0.0
./.venv/bin/python scripts/router_search.py --query "MFA követelmény a jelszó policy-ban" --min_score 0.0
```

### Közvetlen domain search
```bash
./.venv/bin/python scripts/search.py --domain it --query "Mi az MFA követelmény a jelszó policy-ban?" --min_score 0.0
./.venv/bin/python scripts/search.py --domain ops --query "Sev1 war-room" --min_score 0.0
```

---

## Idempotencia (miért jó beadáshoz)
- `create_collections.sh` “EXISTS” esetben nem hibázik (409 = már létezik)
- `ingest.py` determinisztikus point ID-t használ (`uuid5(domain:chunk_id)`), ezért újrafuttatás = update/upsert, nem duplikál

---

## Troubleshooting

### Docker socket permission denied
A usernek benne kell lennie a `docker` groupban, és a shell/VS Code folyamatnak is friss group-listával kell futnia.

### docker-credential-desktop not found
Ha `~/.docker/config.json` tartalmaz `credsStore: desktop`, akkor Linuxon gyakran elszáll.  
Megoldás: törölni a `credsStore/credHelpers` részt a configból.

---

## Következő lépés (opcionális)
RAG “answer” script (HF3 jelleg): a router találatait promptba rakod, és LLM-mel generálsz választ.
