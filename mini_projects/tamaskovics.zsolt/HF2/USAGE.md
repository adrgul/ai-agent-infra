# HF2 – Usage & Operations Guide

Ez egy rövid, de “beadás + üzemeltetés” kompatibilis runbook a HF2 projekthez (Qdrant + ingest + search + domain router).

## 0) Fogalmak
- **KB (knowledge base)**: a `kb_sources/<domain>/*.md` alatt lévő forrásdokik.
- **Chunk**: a doksi feldarabolt része (`CHUNK_SIZE` + `CHUNK_OVERLAP` alapján).
- **Embedding**: a szöveg vektorreprezentációja (OpenAI embeddings model).
- **Qdrant point**: 1 db (chunk → embedding) rekord a Qdrantban.
- **Collection**: Qdrant “tábla/index”; nálunk domainenként külön.

---

## 1) Gyors indítás (reprodukálható)

### 1.1 OpenAI API key (shell env-be)
```bash
read -s -p "OPENAI_API_KEY=" OPENAI_API_KEY; echo
export OPENAI_API_KEY
```

### 1.2 Bootstrap (idempotens)
```bash
./scripts/bootstrap.sh
```

---

## 2) Demo / teszt

### 2.1 Domain routing (ajánlott demo)
A router nem kérdez domaint az LLM-től. Top1 score alapján választ domaint, majd ott futtat top-k keresést.

```bash
./.venv/bin/python scripts/router_search.py --query "Sev1 war-room" --min_score 0.0
./.venv/bin/python scripts/router_search.py --query "eszköz kiadás onboarding" --min_score 0.0
./.venv/bin/python scripts/router_search.py --query "MFA követelmény a jelszó policy-ban" --min_score 0.0
```

Finomhangolás:
- `.env`: `ROUTER_THRESHOLD=0.18`
  - ha túl gyakran rossz domaint választ → emeld
  - ha túl sok a fallback → csökkentsd

### 2.2 Direkt domain keresés
```bash
./.venv/bin/python scripts/search.py --domain it --query "Mi az MFA követelmény a jelszó policy-ban?" --min_score 0.0
./.venv/bin/python scripts/search.py --domain ops --query "Sev1 war-room" --min_score 0.0
```

---

## 3) KB karbantartás

### 3.1 Új dokumentum hozzáadása
1) Másold be a doksit a megfelelő domain alá:
```bash
cp my_doc.md kb_sources/it/my_doc.md
```

2) Ingest:
```bash
./.venv/bin/python scripts/ingest.py
```

### 3.2 Meglévő dokumentum módosítása
Alapesetben elég újra futtatni:
```bash
./.venv/bin/python scripts/ingest.py
```

Megjegyzés: a pontok ID-ja determinisztikus (`uuid5(domain:chunk_id)`), ezért azonos chunk indexek felülíródnak (upsert).

### 3.3 “Árva chunkok” kezelése (mikor kell törölni)
Árva chunkok akkor maradhatnak, ha:
- a doksi rövidebb lett (kevesebb chunk keletkezik),
- változott a chunkolás (`CHUNK_SIZE` / `CHUNK_OVERLAP`),
- nagy átrendezés történt a szövegben.

Korrekt eljárás: **doksi pontok törlése** → ingest.

#### Dokumentum-szintű törlés Qdrantból
- `DOC_ID` = fájlnév slugja (pl. `password_policy.md` → `password-policy`)
```bash
DOMAIN=it
DOC_ID=password-policy

curl -sS -X POST "http://127.0.0.1:6333/collections/$DOMAIN/points/delete?wait=true"   -H 'Content-Type: application/json'   -d "{"filter":{"must":[{"key":"doc_id","match":{"value":"$DOC_ID"}}]}}"

./.venv/bin/python scripts/ingest.py
```

### 3.4 Domain reset (HF2-ben teljesen oké)
```bash
DOMAIN=it
curl -sS -X DELETE "http://127.0.0.1:6333/collections/$DOMAIN" | python3 -m json.tool

./scripts/create_collections.sh
./.venv/bin/python scripts/ingest.py
```

### 3.5 Teljes reset (minden domain)
```bash
for DOMAIN in hr compliance it ops general; do
  curl -sS -X DELETE "http://127.0.0.1:6333/collections/$DOMAIN" >/dev/null || true
done

./scripts/create_collections.sh
./.venv/bin/python scripts/ingest.py
```

---

## 4) Nagy dokumentumok (szabályzat)
- működik egyben is (sok chunk), de jobb: fejezetenként külön fájl + 1 oldalas summary
- javasolt tuning:
  - `CHUNK_SIZE=500..800`
  - `CHUNK_OVERLAP=60..120`

Ha változtatsz chunk paramokon, ajánlott domain reset vagy doksi törlés + ingest (árva chunkok miatt).

---

## 5) Paraméterezés (tuning)

### 5.1 Chunkolás
`.env` példák:
```env
CHUNK_SIZE=600
CHUNK_OVERLAP=80
```

### 5.2 Keresési paramok
```env
TOP_K=6
MIN_SCORE=0.25
ROUTER_THRESHOLD=0.18
```

- `TOP_K`: hány találat jöjjön vissza
- `MIN_SCORE`: minimum hasonlósági küszöb (túl magas → semmi, túl alacsony → zaj)
- `ROUTER_THRESHOLD`: router domain-választási küszöb (top1 score alapján)

---

## 6) Embedding modell vs VECTOR_SIZE
A collection vektor dimenziója fix (`VECTOR_SIZE`).

Ha más embedding modellre váltasz, és **más a dimenzió**, akkor:
1) töröld/recreate a collectionöket a megfelelő `VECTOR_SIZE`-zal
2) ingest újra

---

## 7) ACL (opcionális váz, HF2-safe)
Payloadban:
- `acl_public` (bool)
- `acl_roles` (list)

Jelenleg minden public. A `search.py` és `router_search.py` támogatja az opcionális role szűrést:
```bash
./.venv/bin/python scripts/router_search.py --query "onboarding" --role hr --min_score 0.0
./.venv/bin/python scripts/search.py --domain hr --query "onboarding" --role hr --min_score 0.0
```

Ha nincs `--role`, nincs ACL filter.

---

## 8) Backup / restore
A Qdrant adat a `qdrant_storage/` könyvtárban van (bind mount).

### Backup
```bash
tar -czf qdrant_storage_backup.tgz qdrant_storage
```

### Restore
```bash
docker compose down
rm -rf qdrant_storage
tar -xzf qdrant_storage_backup.tgz
docker compose up -d
```

---

## 9) Troubleshooting (gyors)

### Qdrant ready check
```bash
curl -sS http://127.0.0.1:6333/readyz ; echo
```

### Collection lista
```bash
curl -sS http://127.0.0.1:6333/collections | python3 -m json.tool
```

### Pontszám túl alacsony / nincs találat
- csökkentsd `MIN_SCORE`-t (demohoz simán `0.0`)
- növeld `TOP_K`-t
- ellenőrizd a pontszámokat routerrel (top1 score/domain)
```bash
./.venv/bin/python scripts/router_search.py --query "Sev1 war-room" --min_score 0.0
```

### Van-e adat a collectionben?
```bash
DOMAIN=it
curl -sS -X POST "http://127.0.0.1:6333/collections/$DOMAIN/points/count"   -H 'Content-Type: application/json'   -d '{"exact": true}' | python3 -m json.tool
```
