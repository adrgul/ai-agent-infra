# HOW_TO.md
## AI Chat v0.2.0 - Oktatói Útmutató

---

## 📝 **EREDETI FELADAT**

### 1. Felhasználó képes legyen fájlt feltölteni
### 2. Rendszer chunkolja + embeddingelje + tárolja vector adatbázisban
### 3. Felhasználó képes legyen a fájl tartalmára rákérdezni
### 4. Rendszer képes legyen a megfelelő chunkokat kiválasztva releváns választ generálni

---

## ✅ **MEGVALÓSÍTÁS & ELLENŐRZÉS**

### 🚀 **Indítás**
```powershell
cd ai_chat_edu_v02
docker-compose up -d
```
**Frontend:** http://localhost:3000 | **Backend:** http://localhost:8000

---

### ✅ **1. Fájl Feltöltés**

**Megvalósítás:** 
- Frontend: **📎** ikon (Chat input mezőtől balra) → DocumentUpload modal
- Backend: `POST /api/workflows/process-document` (single endpoint)
- Támogatott formátumok: PDF, TXT, Markdown (max 10MB)

**Tesztelés:**
1. Kattints **📎** ikonra
2. Válassz fájlt: `test_files/test_doc.txt` vagy `chunk_test_fantasy_elfek_orkok.txt`
3. Upload gomb
4. **Elvárt:** "Document processed successfully" + document ID

---

### ✅ **2. Automatikus Chunking + Embedding + Tárolás**

**Megvalósítás:**
- **Chunking:** RecursiveCharacterTextSplitter (500 token/chunk, 50 overlap)
- **Embedding:** OpenAI text-embedding-3-large (3072 dim)
- **PostgreSQL:** `documents` + `document_chunks` táblák
- **Qdrant:** `document_chunks` collection (vector storage)

**Tesztelés (háttér folyamat ellenőrzés):**
```powershell
# Chunk-ok ellenőrzése PostgreSQL-ben
docker exec ai_chat_edu_v02-backend-1 python /app/debug/check_docs_chunks.py
# Output: "test_doc.txt - 3 chunks"

# Vector embedding ellenőrzése Qdrant-ban
docker exec ai_chat_edu_v02-backend-1 python /app/debug/check_qdrant_data.py
# Output: "Tenant 1: 3 vectors"
```

**Elvárt:** Chunk count PostgreSQL == Qdrant vector count

---

### ✅ **3. Rákérdezés Fájl Tartalmára**

**Megvalósítás:**
- Unified Chat Workflow (LangGraph)
- Intelligens routing: LLM dönti el, hogy RAG keresés szükséges-e
- Chat interface: session-based conversation

**Tesztelés:**
1. Válassz tenantot: "ACME Corporation"
2. Válassz usert: "Alice Johnson"
3. Írj kérdést: **"Miről szól a feltöltött dokumentum?"**
4. **Elvárt:** LLM válasz + forrás hivatkozás (📄 test_doc.txt)

---

### ✅ **4. Releváns Chunkök Kiválasztása + Válaszgenerálás**

**Megvalósítás:**
- Query embedding → Qdrant similarity search (TOP_K=5, min_score=0.1)
- Chunk filtering tenant_id alapján (security)
- Retrieved chunks → LLM context (GPT-3.5-turbo)
- Answer generation + source attribution

**Tesztelés (RAG pipeline részletek):**
```powershell
# Backend logs: RAG workflow lépések
docker logs ai_chat_edu_v02-backend-1 --tail 50 | Select-String "RAG|chunk|Qdrant"
```

**Elvárt kimenet a chatben:**
- Válasz tartalmazza a dokumentum specifikus információkat
- **Forrás hivatkozás:** 📄 "test_doc.txt" vagy "chunk_test_fantasy_elfek_orkok.txt"
- **Response time:** ~2-3s (látható buborékban)

**Kontrollteszt (nem RAG query):**
- Kérdés: **"Szia!"**
- **Elvárt:** Direkt LLM válasz, NINCS forrás hivatkozás (routing = CHAT)

---

## 🎯 **A RENDSZER EZEN FELÜL MÉG...**

### Multi-tenant Architecture
- Több cég (tenant) párhuzamos működése
- Adatok teljes szeparációja (PostgreSQL + Qdrant filters)
- Tenant-specifikus system prompt (cég-szintű AI testreszabás)

### Multi-user Support
- User-szintű system prompt (személyre szabott AI viselkedés)
- User-specifikus dokumentumtár (private vs tenant visibility)
- Session management (több beszélgetés párhuzamosan)

### Intelligent Routing (LangGraph Agent Loop)
- Automatikus döntés: CHAT | RAG | LIST | EXPLICIT_MEMORY
- Nincs hardcoded keyword detection
- Adaptív workflow (max 10 iteráció)

### Chat History & Context Awareness
- PostgreSQL persistence (metadata oszlop: sources, rag_params)
- Oldal frissítés után chat megmarad
- Kontextuális follow-up kérdések ("És hol élnek?" → érti az "ők" = elfek)

### Explicit Memory (Fact Extraction)
- LLM-alapú fact extraction ("Kedvenc könyv: XYZ")
- Automatikus spell-check (GPT-4o mini)
- Long-term memory tárolás (külön Qdrant collection)

### 3-tier Cache Architecture
- In-memory cache (tenant/user data)
- PostgreSQL query cache
- DEV_MODE runtime toggle (system.ini)
- Performance: 47ms → 13ms (cache HIT)

### Debug & Development Tools
- Debug panel: PostgreSQL + Qdrant reset
- Cache statistics endpoint
- UTF-8 encoding support
- PowerShell test scripts (`debug/` könyvtár)

---

**Verzió:** 0.2.0 | **Dokumentáció:** `docs/` könyvtár (CACHE_ARCHITECTURE.md, LANGGRAPH_WORKFLOWS.md)  
**Utolsó frissítés:** 2026-01-02
