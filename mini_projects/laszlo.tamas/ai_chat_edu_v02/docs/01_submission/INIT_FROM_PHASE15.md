# INIT_PROMPT_2.md
## Phase 2.0 – RAG + Knowledge Management (FULL SCOPE)

---

## 📜 AGENT CONSTITUTION BETÖLTÉSE (KÖTELEZŐ)

⚠️ **Ez a prompt az AGENT_CONSTITUTION.md szabályai alapján működik.**

**Kritikus referenciák:**
- **Section 3.2:** PLAN → PERMISSION → CODE (implementáció csak engedéllyel)
- **Section 3.3:** Fejlesztési workflow (BUILD → TEST → REPORT ciklus)
- **Section 4:** Failure Mode (bizonytalanság esetén KÉRDEZ és MEGÁLL)
- **Section 5:** Red Lines (tilos hardcode-olás, input-specifikus workaround)
- **Section 6.1:** TODO policy (külön fájl, nem az INIT_PROMPT-ban)
- **Section 6.4:** Debug fájlok kezelése (debug/ könyvtár használata)

👉 **Ha az INIT_PROMPT és az AGENT_CONSTITUTION között ellentmondás van:**  
**→ az AGENT_CONSTITUTION az elsődleges.**

---

## 0️⃣ KONFIGURÁCIÓS ALAPFÁJLOK (KÖTELEZŐ ELSŐ LÉPÉS)

A fejlesztés megkezdése előtt **KÖTELEZŐEN** létre kell hozni az alábbi konfigurációs fájlokat.

⚠️ **SZABÁLYOK:**
- ÉRTÉKET SEHOL NEM SZABAD MEGADNI
- CSAK változónevek szerepelhetnek
- Ezek **struktúrát definiálnak**, nem konfigurációt
- Az értékeket a futtatási környezet adja meg

---

### 0.1 PROMPT HIERARCHIA (KÖTELEZŐ MODELL)

```
system.ini              → APPLICATION PROMPT
tenants.system_prompt   → TENANT POLICY
users.system_prompt     → USER PREFERENCES
runtime task prompt     → QUESTION + RETRIEVED CONTEXT
```

Ez a sorrend **nem megfordítható**.

**MAGYARÁZAT:**

A hierarchia azt határozza meg, hogyan épül fel az LLM számára a teljes környezeti prompt:

1. **System szint** (`system.ini` → APPLICATION PROMPT)  
   - Rendszerszinten meghatározott utasítások
   - **NEM ÍRHATÓ FELÜL** semmilyen alacsonyabb szinten
   - Globális működési szabályok

2. **Tenant szint** (`tenants.system_prompt` → TENANT POLICY)  
   - Tenant-specifikus szabályok
   - A tenant-ban lévő **MINDEN userre vonatkozik**
   - Vállalati policy-ként működik
   - Nem írhatja felül a system szintet

3. **User szint** (`users.system_prompt` → USER PREFERENCES)  
   - User-specifikus preferenciák
   - Nem írhatja felül a system vagy tenant szabályokat
   - Személyre szabás

4. **Runtime szint** (task prompt)  
   - Aktuális kérdés + RAG context
   - A legalacsonyabb prioritás
   - Nem írhat felül semmilyen magasabb szintet

**PÉLDA:**
- System: "Mindig magyar nyelven válaszolj"
- Tenant: "Soha ne adj pénzügyi tanácsot"
- User: "Informatív stílusban válaszolj"
- Runtime: "Mi a részvény árfolyama?" ← Ez NEM kaphat pénzügyi tanácsot, még ha kéri is

---

## 🎯 PROJEKT CÉL (PHASE 2.0)

Egy **multi-tenant, user-aware belső AI rendszer**, amely:

- dokumentum-, termék- és chat-alapú tudást kezel
- Retrieval-Augmented Generation (RAG) architektúrát használ
- PostgreSQL + Qdrant + LangGraph stackre épül
- oktatási / vizsga környezetben **védhető**

Nem production rendszer.  
A cél: **tiszta, magyarázható architektúra**.

---

## 🛠️ TECH STACK (KÖTELEZŐ PARAMÉTEREK)

### Backend
- **Python**: 3.11+
- **Framework**: FastAPI 0.104.1
- **ASGI Server**: Uvicorn 0.24.0
- **Validation**: Pydantic 2.5.0
- **LLM Client**: OpenAI 1.54.0
- **Orchestration**: LangGraph 0.0.26
- **LangChain**: langchain-core 0.1.25+, langchain-openai 0.0.5

### Frontend
- **Framework**: React 18.2.0
- **Language**: TypeScript 5.3.3
- **Build Tool**: Vite 5.0.8
- **Styling**: Native CSS (no framework)

### Database & Vector Store
- **Relational DB**: PostgreSQL 15+ (via psycopg2-binary 2.9.9)
- **Vector DB**: Qdrant (latest stable)
- **Embedding Model**: OpenAI `text-embedding-3-large` (3072 dim)

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Ports**: 
  - Backend: 8000
  - Frontend: 3000
  - PostgreSQL: 5432 (Docker local)
  - Qdrant: 6333 (HTTP API), 6334 (gRPC)

### Environment
- `.env` file kötelező
- Environment változók: OPENAI_API_KEY, POSTGRES_*, USE_LANGGRAPH

---

## 🧠 VECTOR DATABASE STRATÉGIA (KÖTELEZŐ)

**Egy Qdrant instance, külön collectionök:**

- document_chunks
- longterm_chat_memory
- product_knowledge

Ezek **SOHA** nem keverhetők.

---

## 🟥 P0 – CORE RAG ✅ COMPLETED (P0.1-P0.8)

**STÁTUSZ:** Core RAG pipeline **100% kész** és működik LangGraph workflow-kban.

**AMIT MÁR TUDSZ:**
- ✅ P0.1-P0.6: Dokumentum feltöltés, chunkolás, embedding, Qdrant retrieval
- ✅ P0.7: LangGraph RAG workflow (teljes pipeline)
- ✅ P0.8: Intelligent RAG routing (conversational vs document kérdések)

**KÖVETKEZŐ:** P0.9 továbbfejlesztések (UX + performance)

---

### P0.1 File upload ✅ COMPLETED (LangGraph)
- PDF / TXT / MD
- tenant + user kontextus
- DB-be írás: documents tábla

**ENDPOINT:**
- ~~POST /api/documents/upload~~ → **POST /api/workflows/process-document** (automated)
- Multipart form-data: file + tenant_id + user_id + visibility

**DB INSERT (documents tábla):**
- tenant_id: request-ből
- user_id: request-ből (auth alapján)
- visibility: 'private' vagy 'tenant'
- source: 'upload' (fix érték)
- title: file.filename
- content: file text tartalma (extracted)
- created_at: auto (DEFAULT now())

**DONE WHEN:**
- [x] POST /api/workflows/process-document endpoint működik ✅
- [x] File validation: max 10MB, csak PDF/TXT/MD ✅
- [x] File content extrakció (PDF → text, TXT/MD → direct read) ✅
- [x] documents táblába INSERT valós mezőkkel ✅
- [x] Response: {"document_id": <id>, "summary": {...}} ✅
- [x] HTTP 201 Created, 400 invalid file ✅
- [ ] Frontend: file picker + upload gomb (UI TODO)

### P0.2 Dokumentum adatmodell (PostgreSQL)
- documents
- document_chunks
- visibility: private / tenant
- source metaadatok

**VALÓS DB SÉMA (már létezik):**

**documents tábla:**
- id (bigint, PK)
- tenant_id (bigint, FK → tenants.id)
- user_id (bigint, FK → users.user_id, nullable)
- visibility (text: 'private' | 'tenant')
- source (text: forrás típusa)
- title (text: dokumentum címe/fájlnév)
- content (text: teljes dokumentum tartalma)
- created_at (timestamp)

**document_chunks tábla:**
- id (bigint, PK)
- tenant_id (bigint, FK → tenants.id)
- document_id (bigint, FK → documents.id)
- chunk_index (integer)
- start_offset (integer)
- end_offset (integer)
- content (text)
- source_title, source_section, source_page_from, source_page_to (metadata)
- qdrant_point_id (uuid: Qdrant kapcsolat)
- embedded_at (timestamp)
- created_at (timestamp)

**DONE WHEN:**
- [x] documents tábla létezik ✅
- [x] document_chunks tábla létezik ✅
- [x] Foreign keys: document_chunks.document_id → documents.id ✅
- [x] Index: document_id, tenant_id ✅
- [ ] Migration script (ha új mező kell): NEM SZÜKSÉGES

### P0.3 Chunkolás ✅ COMPLETED
- stratégia: **recursive** (system.ini)
- chunk_size: **500 tokens** (~2000 chars)
- overlap: **50 tokens** (~200 chars)
- offsetek és indexek tárolása PostgreSQL-ben

**IMPLEMENTÁCIÓ:** `services/chunking_service.py` + LangGraph workflow node

**DONE WHEN:**
- [x] Chunking service implementálva ✅
- [x] RecursiveCharacterTextSplitter használata (LangChain) ✅
- [x] Chunk index, start_offset, end_offset számítása helyes ✅
- [x] PostgreSQL-be írás sikeres minden chunk-kal ✅
- [x] Workflow: chunk_document node működik ✅

### P0.4 Embedding pipeline (documents) ✅ COMPLETED
- chunk → embedding
- large modell (text-embedding-3-large)
- időbélyeg rögzítése

**IMPLEMENTÁCIÓ:** `services/embedding_service.py` + LangGraph workflow node

**DONE WHEN:**
- [x] OpenAI text-embedding-3-large használata (3072 dim) ✅
- [x] Batch processing: max 100 chunk/call (system.ini: EMBEDDING_BATCH_SIZE) ✅
- [x] Embedding vektorok generálása minden chunk-hoz ✅
- [x] Error handling implementálva ✅
- [x] Timestamp: embedded_at mező PostgreSQL-ben ✅

### P0.5 Qdrant – document_chunks collection ✅ COMPLETED
- payload: tenant_id, document_id, chunk_id, visibility
- cosine similarity
- tenant szűrés kötelező

**IMPLEMENTÁCIÓ:** `services/qdrant_service.py` + workflow upsert node

**DONE WHEN:**
- [x] Qdrant collection létezik: prefix + "document_chunks" ✅
- [x] Vector size: 3072 (text-embedding-3-large) ✅
- [x] Distance metric: Cosine ✅
- [x] Payload schema: {tenant_id, document_id, chunk_id, visibility, content_preview} ✅
- [x] Filter on payload: tenant_id (gyors szűrés) ✅
- [x] Workflow: upsert_to_qdrant node működik ✅

### P0.6 Retrieval pipeline ✅ COMPLETED
- query → embedding
- similarity search
- Top-K chunk
- forrásmegőrzés

**IMPLEMENTÁCIÓ:** `services/rag_workflow.py` - retrieve_chunks_node

**DONE WHEN:**
- [x] Query text → OpenAI embedding ✅
- [x] Qdrant search with tenant_id filter (kötelező) ✅
- [x] Top-K = 5 (system.ini: TOP_K_DOCUMENTS) ✅
- [x] Min score threshold = 0.7 (system.ini: MIN_SCORE_THRESHOLD) ✅
- [x] Response: List[DocumentChunk] with document_id, content, score ✅
- [x] RAG workflow retrieve_document_chunks node működik ✅

### P0.7 LangGraph RAG workflow

**WORKFLOW DIAGRAM:**

```
START
 → validate_input          [ellenőrzés: tenant_id, user_id, query]
 → build_context           [prompt hierarchia összeszedése]
 → retrieve_document_chunks [Qdrant similarity search]
 → check_retrieval_results  [van-e releváns chunk?]
    ├─ YES → generate_answer_from_context
    ├─ NO  → generate_fallback_response
 → END
```

**ERROR HANDLING:**
- Minden node try-catch wrapper-rel
- Hiba esetén: error state + fallback válasz
- Timeout: 30s per node (konfiguratív)
- Retry logic: NEM implementált Phase 2.0-ban

**STATE DEFINÍCIÓ (Python TypedDict):**

```python
from typing import TypedDict, List, Optional

class DocumentChunk(TypedDict):
    chunk_id: int
    document_id: int
    content: str
    metadata: dict
    similarity_score: float

class UserContext(TypedDict):
    tenant_id: int
    user_id: int
    tenant_prompt: Optional[str]
    user_prompt: Optional[str]
    user_language: str  # 'hu' | 'en'

class RAGState(TypedDict):
    # Input
    query: str
    user_context: UserContext
    
    # Intermediate
    system_prompt: str
    combined_prompt: str
    retrieved_chunks: List[DocumentChunk]
    has_relevant_context: bool
    
    # Output
    final_answer: str
    sources: List[int]  # document_id list
    error: Optional[str]
```

**NODE FELELŐSSÉGEK:**

- `validate_input`: tenant_id, user_id, query nem üres
- `build_context`: system.ini + tenant + user prompt összefűzés
- `retrieve_document_chunks`: query → embedding → Qdrant search → top-K
- `check_retrieval_results`: similarity_score >= 0.7 threshold
- `generate_answer_from_context`: LLM hívás context + query-vel
- `generate_fallback_response`: "Nincs releváns dokumentum" válasz

**DONE WHEN:**
- [x] LangGraph StateGraph definiálva RAGState-tel
- [x] Minden node implementálva fenti felelősségekkel
- [x] Conditional edge: check_retrieval_results → YES/NO
- [x] Error state kezelés minden node-ban
- [x] POST /api/chat/rag endpoint LangGraph-ot hívja
- [x] Teszt: query + user_context → final_answer + sources
- [x] Frontend: válasz megjelenítése source attribution-nel

---

### P0.8 Intelligent RAG Routing (✅ COMPLETED - Enhancement)

**⚠️ NOTE:** Ez egy P0.7 továbbfejlesztés, amely a UX javítása érdekében került implementálásra.

**PROBLÉMA:** P0.7 minden query-re RAG retrieval-t indított, még köszönésekre is ("szia" → "Nincs releváns dokumentum").

**MEGOLDÁS:** LLM-based decision node a RAG szükségességéről.

**ÚJ WORKFLOW:**

```
START
 → validate_input
 → build_context
 → decide_if_rag_needed    [🆕 LLM döntés: kell-e dokumentum?]
    ├─ YES → retrieve_document_chunks → check_retrieval_results → [answer | fallback]
    └─ NO  → generate_direct_answer [normál chat, NINCS RAG]
 → END
```

**ÚJ STATE FIELD:**

```python
class RAGState(TypedDict):
    # ... (eredeti fieldek)
    needs_rag: bool  # 🆕 LLM decision: igényel-e RAG-et a query?
```

**ÚJ NODE-OK:**
- `decide_if_rag_needed`: LLM elemzi a query-t (conversational vs document-related)
- `generate_direct_answer`: Közvetlen válasz NINCS RAG (gyors, beszélgetéshez)

**PÉLDÁK:**
- "szia" → NO RAG → "Szia! Miben segíthetek?" (sources: [])
- "mi van a dokumentumban?" → YES RAG → document search + answer (sources: [1,2,3])

**ELŐNYÖK:**
- Természetes beszélgetés lehetséges
- Gyorsabb válasz conversational query-knél (nincs embedding + Qdrant overhead)
- Jobb UX: nincs zavaró "nincs dokumentum" üzenet köszönésekre

**RÉSZLETEK:** Lásd [docs/P0.8_INTELLIGENT_RAG_ROUTING.md](./P0.8_INTELLIGENT_RAG_ROUTING.md)

**DONE WHEN:**
- [x] RAGState bővítve needs_rag field-del
- [x] decide_if_rag_needed node implementálva
- [x] generate_direct_answer node implementálva
- [x] Routing logic: conversational vs RAG
- [x] Backend build + deploy
- [x] Teszt: "szia" → conversational válasz (nem "nincs dokumentum")
- [x] Teszt: "mi van a dokumentumban?" → RAG aktiválódik

---

### P0.9 Planned Improvements (⏳ TODO)

**STATUS:** Pending implementation  
**PRIORITY:** HIGH (before P1)  
**GOAL:** UX és teljesítmény továbbfejlesztések a meglévő RAG rendszeren

**RÉSZLETES TASK LIST:** Lásd [`TODO_PHASE2.md § P0.9`](./TODO_PHASE2.md#-p09--ux--performance-improvements)

**Főbb területek:**
1. **P0.9.1** - Document Title Metadata (forrás címek megjelenítése)
2. **P0.9.2** - Enhanced Source Attribution (oldalszám, fejezet)
3. **P0.9.3** - Search Performance Optimization (Qdrant tuning, cache)
4. **P0.9.4** - Document Summary Generation (auto-summary hosszú dokumentumokhoz)
5. **P0.9.5** - Keyword Detection Improvements (P0.8 routing finomhangolása)

---

## 🟧 P1 – KNOWLEDGE & MEMORY

**STATUS:** Pending implementation  
**PRIORITY:** MEDIUM (after P0.9)  
**RÉSZLETES TASK LIST:** Lásd [`TODO_PHASE2.md § P1`](./TODO_PHASE2.md#-p1--knowledge--memory)

### P1.1 Long-term Chat Memory
**Cél:** Session summaries tárolása és retrieval korábbi beszélgetésekből

**Főbb lépések:**
- Session lezárásakor LLM summary generálás
- Embedding + Qdrant `longterm_chat_memory` collection
- Új session indításakor previous session retrieval
- LangGraph node: `retrieve_chat_history`

**DB Séma:**
- [x] `chat_sessions` tábla létezik ✅
- [x] `long_term_memories` tábla létezik ✅

---

### P1.2 Product Knowledge
**Cél:** Strukturált termékadat tárolása és RAG retrieval

**Főbb lépések:**
- `products` tábla létrehozása (PostgreSQL)
- Szöveges reprezentáció generálás
- Embedding + Qdrant `product_knowledge` collection
- Termék-specifikus retrieval pipeline

---

### P1.3 Multi-source RAG
**Cél:** Párhuzamos keresés dokumentum + termék adatforrásokban

**Főbb lépések:**
- Keyword-based routing (document vs product)
- Parallel search mindkét collection-ben
- Result merging (similarity score alapján)
- LangGraph node: `route_and_retrieve`

---

## 🟨 P2 – ADMIN & SYSTEM

**STATUS:** Pending implementation  
**PRIORITY:** LOW (after P1)  
**RÉSZLETES TASK LIST:** Lásd [`TODO_PHASE2.md § P2`](./TODO_PHASE2.md#-p2--admin--system)

### P2.1 Admin Felület (Profil és Tenant Szerkesztés)

**User Profile Editing (minden user):**
- Szerkeszthető mezők: firstname, lastname, nickname, email, default_lang, system_prompt
- API: GET/PATCH `/api/users/{user_id}`
- Frontend form + validation

**Tenant Admin (csak admin role):**
- Szerkeszthető mezők: key, name, system_prompt, is_active
- API: GET/PATCH `/api/tenants/{tenant_id}` (authorization check)
- Frontend: "Tenant Admin" tab (csak adminoknak látható)

---

### P2.2 system.ini Konfiguráció
- Globális application prompt
- Backend-only file (frontend NEM módosíthatja)
- Manuális szerkesztés + restart szükséges
- Prompt hierarchia: system.ini > tenant > user > runtime

---

### P2.3 README.md Frontend Megjelenítés
- RAG pipeline magyarázat
- Postgres vs Qdrant szerep
- Collection-stratégia dokumentáció
- API endpoint: GET `/api/docs/readme`
- Frontend: "README" tab (markdown renderelés)

---

## � DEPLOYMENT & SETUP

### Előfeltételek
- Docker + Docker Compose telepítve
- OpenAI API key
- PostgreSQL (Docker local)
- Qdrant (Docker local)

### .env fájl konfiguráció

**KÖTELEZŐ környezeti változók:**

```env
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL_CHAT=gpt-3.5-turbo
OPENAI_MODEL_EMBEDDING=text-embedding-3-large

# PostgreSQL (Docker local)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=ai_chat_edu
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Qdrant (Docker local)
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=
QDRANT_USE_HTTPS=true
QDRANT_COLLECTION_PREFIX=r_d_ai_chat

# Application
USE_LANGGRAPH=true
ENV=development
LOG_LEVEL=INFO
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### Indítás lépései

**1. Környezet setup:**
```powershell
# .env file másolása
Copy-Item .env.example .env
# Szerkeszd az értékeket!
```

**2. Docker build & start:**
```powershell
docker-compose up --build
```

**3. Health check:**
- Backend: http://localhost:8000/health
- Frontend: http://localhost:3000

**4. PostgreSQL migráció:**
```powershell
# Ha van migration script
docker-compose exec backend python -m alembic upgrade head
```

**5. Qdrant collection létrehozás:**
- Automatikus az első embedding push-nál
- Vagy manuális: backend init script

### Leállítás
```powershell
docker-compose down
```

### Reset (clean slate)
```powershell
docker-compose down -v  # törli a volume-okat is
```

---

## �🚦 FEJLESZTÉSI SZABÁLY (MEGSZEGHETETLEN)

Ha egy funkció:
- nem segíti a RAG / knowledge megértését, vagy
- nem magyarázható el 5 perc alatt,

akkor **NEM kerül be Phase 2.0-ba**.

---

## 🔒 ZÁRÓ UTASÍTÁS AZ AI AGENTNEK

Te **kontrolláltan építesz**.

Lépés → build → teszt → felhasználói jóváhagyás → tovább.

Másképp **nem dolgozol**.

