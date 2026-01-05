# KnowledgeRouter - AI Agent

**Vállalati Tudásirányító & Workflow-Automata**

Multi-domain AI agent rendszer Python Django backenddel, LangGraph orchestrációval és modern Tailwind CSS frontenddel (ChatGPT-style UI).

## 🎯 Projekt Áttekintése

KnowledgeRouter egy vállalati belső tudásbázis rendszer, amely:

✅ **6 domain-re** szétválasztott tudásbázisokból keres (HR, IT, Finance, Legal, Marketing, General)  
✅ **Multi-domain Qdrant collection** domain-specifikus szűréssel (egyetlen collection, gyors filtering)  
✅ **Hibrid keresés support** szemantikus (dense vectors) + domain filtering (lexikális BM25 ready)  
✅ **Intent detection** segítségével felismeri, melyik domain-hez tartozik a kérdés  
✅ **RAG (Retrieval-Augmented Generation)** használ releváns dokumentumok megtalálásához  
✅ **Redis cache** embedding és query result cache-eléssel (54% hit rate, domain-scoped invalidation)  
✅ **Google Drive integráció** marketing dokumentumok eléréséhez  
✅ **Workflow-okat** futtat (HR szabadság igénylés, IT ticket, stb.)  
✅ **Citációkkal** ellátott válaszokat ad (dokumentum referenciák)  
✅ **Like/Dislike feedback rendszer** (PostgreSQL, domain-scoped analytics, materialized views)  
✅ **Konverzáció előzményt** mentesít JSON-ban  
✅ **Token tracking** és költség kalkuláció  
✅ **Docker-ben** futtatható (Uvicorn ASGI, async support)

## 📋 Tech Stack

- **Backend**: Python 3.11+ | Django | LangGraph
- **LLM**: OpenAI GPT-4o Mini (gpt-4o-mini)
- **Vector DB**: Qdrant (self-hosted)
- **Cache**: Redis 7 (embedding + query result cache)
- **Database**: PostgreSQL 15 (feedback system)
- **Frontend**: Tailwind CSS + Vanilla JavaScript (ChatGPT-style UI)
- **Deployment**: Docker Compose (Uvicorn ASGI server)

## 🚀 Quick Start (Docker)

### 1. Klón és Setup

```bash
cd benketibor
cp .env.example .env
```

### 2. API Key Beállítása

```bash
# .env-ben add meg az OPENAI_API_KEY-t
nano .env
# Vagy set a Windows PowerShell-ben:
$env:OPENAI_API_KEY = "sk-your-key-here"
```

### 3. Docker Compose Indítása

```bash
docker-compose up --build
```

**Fontos:** Az alkalmazás **Qdrant-alapú RAG-et** használ multi-domain collection-nel.

**Marketing dokumentumok indexelése (példa):**
```bash
cd backend
python scripts/sync_domain_docs.py --domain marketing --folder-id 1Jo5doFrRgTscczqR0c6bsS2H0a7pS2ZR
```

**Más domainek indexelése:**
```bash
# HR dokumentumok
python scripts/sync_domain_docs.py --domain hr --folder-id YOUR_HR_FOLDER_ID

# IT dokumentumok  
python scripts/sync_domain_docs.py --domain it --folder-id YOUR_IT_FOLDER_ID
```

Részletek: [🧠 RAG & Embedding Rendszer Architektúra](#-rag--embedding-rendszer-architektúra)

```bash
docker-compose up --build
```

### 4. Hozzáférés

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001/api/
- **Qdrant Dashboard**: http://localhost:6334 (vector DB)
- **Redis**: localhost:6380 (cache)
- **PostgreSQL**: localhost:5433 (feedback database)
- **Cache Stats**: http://localhost:8001/api/cache-stats/
- **Feedback Stats**: http://localhost:8001/api/feedback/stats/
- **Google Drive Files API**: http://localhost:8001/api/google-drive/files/

### 5. Google Drive Setup (opcionális)

A marketing domain Google Drive integrációhoz lásd: [docs/GOOGLE_DRIVE_SETUP.md](docs/GOOGLE_DRIVE_SETUP.md)

## 🎮 Próba Kérések

Nyisd meg a frontend-et és próbáld ezeket:

### HR Domain
```
"Szeretnék szabadságot igényelni október 3-4-re"
"Mi a szabadság politika?"
"Munkaadó támogatások?"
```

### IT Domain
```
"Nem működik a VPN"
"Hogyan telepítsem fel a VPN klienst?"
"Szoftver támogatás"
```

### Marketing Domain
```
"Hol van a brand guideline?"
"Legfrissebb marketing dokumentumok?"
```

## 📁 Projekt Struktúra

```
benketibor/
├── backend/                      # Django + LangGraph
│   ├── core/                    # Django settings & config
│   │   ├── settings.py          # App konfigurció
│   │   ├── urls.py              # URL routing
│   │   ├── wsgi.py / asgi.py    # WSGI/ASGI entry
│   │   └── __init__.py
│   ├── domain/                  # Business logic models
│   │   ├── models.py            # Pydantic data models
│   │   ├── interfaces.py        # Abstract base classes
│   │   └── __init__.py
│   ├── infrastructure/          # External integrations
│   │   ├── repositories.py      # File-based storage (users, sessions)
│   │   ├── rag_client.py        # Mock Qdrant client
│   │   └── __init__.py
│   ├── services/                # Business logic
│   │   ├── agent.py             # LangGraph agent (intent → retrieval → response)
│   │   ├── chat_service.py      # Chat orchestration
│   │   └── __init__.py
│   ├── api/                     # API endpoints
│   │   ├── views.py             # REST views (/api/query/, /api/sessions/)
│   │   ├── urls.py              # API URLs
│   │   ├── apps.py              # App initialization
│   │   └── __init__.py
│   ├── data/                    # Persistent storage (JSON)
│   │   ├── users/              # User profiles
│   │   ├── sessions/           # Conversation histories
│   │   └── files/              # Generated files
│   ├── manage.py                # Django CLI
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile               # Backend container

├── frontend/                    # Tailwind CSS + Vanilla JS
│   ├── templates/
│   │   └── index.html          # Chat UI (HTMX)
│   ├── static/css/
│   │   └── style.css           # Styles
│   ├── package.json            # Node dependencies
│   └── Dockerfile              # Frontend container

├── docker-compose.yml          # Multi-container orchestration
├── .env.example                # Environment template
├── README.md                   # This file
├── INSTALLATION.md             # Detailed setup guide
└── start-dev.sh               # Local dev script (bash)
```

## 🔧 API Végpontok

**Teljes API dokumentáció Swagger formátumban:** [docs/API.md](docs/API.md)

### POST `/api/query/`

Feldolgozz egy felhasználói kérdést az agent-en keresztül multi-domain RAG és workflow támogatással.

**Request:**
```json
{
  "user_id": "emp_001",
  "session_id": "session_abc123",
  "query": "Szeretnék szabadságot igényelni október 3-4-re",
  "organisation": "ACME Corp"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "domain": "hr",
    "answer": "Szabadságkérelmed rögzítésre került október 3-4 között. A policy szerint minimum 2 héttel előre kell jelezni. [HR-POL-001]",
    "citations": [
      {
        "doc_id": "HR-POL-001",
        "title": "Vacation Policy",
        "score": 0.94,
        "url": null
      }
    ],
    "workflow": {
      "action": "hr_request_draft",
      "type": "vacation_request",
      "status": "draft",
      "next_step": "manager_approval"
    }
  }
}
```

**Error Responses:**
- `400 Bad Request`: Üres vagy érvénytelen query
- `413 Request Too Large`: Query túl hosszú (>10,000 tokens)
- `500 Internal Server Error`: Backend hiba
- `503 Service Unavailable`: OpenAI API elérhetetlen

### GET `/api/sessions/{session_id}/`

Lekérd egy session beszélgetési előzményét.

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "session_abc123",
    "messages": [
      {
        "role": "user",
        "content": "Szeretnék szabadságot igényelni...",
        "timestamp": "2025-10-03T14:30:00"
      },
      {
        "role": "assistant",
        "content": "Szabadságkérelmed rögzítésre került...",
        "timestamp": "2025-10-03T14:30:05"
      }
    ]
  }
}
```

### POST `/api/reset-context/`

Töröld a session beszélgetési előzményét (de a user profil megmarad).

**Request:**
```json
{
  "session_id": "session_abc123"
}
```

### GET `/api/usage-stats/`

Token használat és OpenAI API költségek lekérdezése.

**Response:**
```json
{
  "success": true,
  "data": {
    "calls": 127,
    "prompt_tokens": 45200,
    "completion_tokens": 12800,
    "total_tokens": 58000,
    "total_cost_usd": 0.0874
  },
  "message": "Token usage statistics since last reset"
}
```

### DELETE `/api/usage-stats/`

Token használat statisztikák nullázása.

**Response:**
```json
{
  "success": true,
  "message": "Usage statistics reset successfully"
}
```

### GET `/api/google-drive/files/`

Google Drive marketing folder fájlok listázása.

**Response:**
```json
{
  "success": true,
  "folder_id": "1Jo5doFrRgTscczqR0c6bsS2H0a7pS2ZR",
  "file_count": 3,
  "files": [
    {
      "id": "150jnsbIl3HreheZyiCDU3fUt9cdL_EFS",
      "name": "Aurora_Digital_Arculati_Kezikonyv_HU.pdf",
      "mimeType": "application/pdf",
      "size": "163689",
      "createdTime": "2025-12-16T13:59:26.841Z",
      "webViewLink": "https://drive.google.com/file/d/..."
    }
  ]
}
```

## 🌐 Environment Változók

Szükséges `.env` fájl:

```bash
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,backend

# OpenAI API
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o-mini

# Vector DB (Qdrant)
QDRANT_HOST=localhost
QDRANT_PORT=6334
QDRANT_COLLECTION=multi_domain_kb  # Multi-domain collection with domain filtering

# Database
DATABASE_URL=sqlite:///db.sqlite3
```

## 📝 Tipikus Workflow

```
User Query
    ↓
[Intent Detection] → Classify domain (HR/IT/Finance/Marketing/etc)
    ↓
[Retrieval] → Search Qdrant with domain filter (csak releváns domain docs)
    ↓           ├─ Domain filter: {"domain": "marketing"}
    ↓           ├─ Semantic search: COSINE similarity
    ↓           └─ Top-K chunks returned
    ↓
[Generation] → LLM generates answer with citations
    ↓
[Workflow] → Execute domain-specific action (if needed)
    ↓
Response + Citations + Workflow Result
    ↓
[Persistence] → Save to JSON (conversation history)
```

## 🧠 RAG & Embedding Rendszer Architektúra

### **Áttekintés**

A KnowledgeRouter **Retrieval-Augmented Generation (RAG)** rendszert használ **multi-domain** tudásbázis kezeléséhez. A rendszer egyetlen Qdrant collection-t használ (`multi_domain_kb`) domain-specifikus szűréssel, amely lehetővé teszi:

- **Skálázhatóság**: Új domain hozzáadása = új dokumentumok indexelése ugyanabba a collection-be
- **Gyors filtering**: Domain payload index → milliszekundumos szűrés
- **Hibrid keresés support**: Szemantikus (dense vectors) + domain filter, készenlét lexikálisra (BM25)

A folyamat két fő részre oszlik: **offline indexelés** és **runtime lekérdezés**.

### **1. Offline Indexelés (Multi-Domain Document Ingestion)**

**Cél:** Bármilyen domain Google Drive dokumentumainak betöltése → Qdrant vektor adatbázisba domain metadatával

**Univerzális Script:** `backend/scripts/sync_domain_docs.py`

**Folyamat lépései:**

#### **1.1 Dokumentum letöltés**
```python
# Google Drive API-n keresztül
drive_client = get_drive_client()
content = drive_client.download_file_content(file_id)
```

#### **1.2 Szöveg kinyerés**
```python
# PDF/DOCX → tiszta szöveg
text = DocumentParser.parse_document(content, mime_type)
# Pl.: "Brand Guidelines – AURORA DIGITAL\n\n1. Brand Overview..."
```

#### **1.3 Text Chunking (Darabolás)**
```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,        # Max 800 karakter/chunk
    chunk_overlap=100,     # 100 karakter átfedés
    separators=["\n\n", "\n", ". ", " ", ""]
)
chunks = text_splitter.split_text(text)
```

**Miért kell chunkolni?**
- LLM-nek nem tudunk 100 oldalas dokumentumot küldeni (token limit)
- Kisebb darabok → pontosabb keresés
- **Overlap:** Biztosítja, hogy fontos információ ne vesszen el a határon

#### **1.4 Embedding Generálás (OpenAI)**
```python
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectors = embeddings.embed_documents([chunk["text"] for chunk in chunks])
# Minden chunk → 1536 dimenziós float vektor
# Pl.: [0.234, -0.567, 0.123, ..., 0.891]
```

**Mi az embedding?**
- Szöveg matematikai reprezentációja
- Hasonló jelentésű szövegek → közeli vektorok
- "sorhossz" és "line length" → közel azonos vektorban

#### **1.5 Qdrant-ba Mentés**
```python
qdrant_client.upsert(
    collection_name="marketing",
    points=[
        PointStruct(
            id=unique_id,
            vector=embedding_vector,  # 1536 float szám
            payload={
                "text": chunk_text,
                "source_file_name": "Aurora_Digital_Brand_Guidelines_eng.docx",
                "source_file_id": "1ACEdQxgUuAsDHKPBqKyp2kt88DjfXjhv",
                "chunk_index": 0,
                "domain": "marketing",
                "indexed_at": "2025-12-16T14:30:00Z"
            }
        )
    ]
)
```

**Adatstruktúra Qdrant-ban:**
| **Mező** | **Érték példa** | **Leírás** |
|---|---|---|
| `id` | `uuid4()` | Egyedi chunk azonosító |
| `vector` | `[0.234, -0.567, ...]` | 1536 dimenziós embedding |
| `payload.text` | `"A logo arányai..."` | Chunk szöveg tartalma |
| `payload.source_file_name` | `"Aurora_Brand_Guide.docx"` | Forrás fájl neve |
| `payload.chunk_index` | `0` | Hányadik chunk a dokumentumban |

---

### **2. Runtime Lekérdezés (RAG Query)**

**Komponens:** `backend/infrastructure/qdrant_rag_client.py` → `QdrantRAGClient`

**Folyamat lépései:**

#### **2.1 User Query Embedding**
```python
# User kérdés: "Mi a brand guideline sorhossz ajánlása?"
query_embedding = embeddings.embed_query(query)
# → [0.189, -0.623, 0.412, ..., 0.734] (1536 float)
```

#### **2.2 Szemantikus Keresés + Domain Filtering**
```python
# Domain filter létrehozása (csak marketing docs)
domain_filter = Filter(
    must=[
        FieldCondition(
            key="domain",
            match=MatchValue(value="marketing")
        )
    ]
)

search_results = qdrant_client.search(
    collection_name="multi_domain_kb",  # Egyetlen multi-domain collection
    query_vector=query_embedding,        # User kérdés vektora
    query_filter=domain_filter,          # Domain-specifikus szűrés!
    limit=5,                             # Top 5 legközelebbi chunk
    with_payload=True                    # Szöveg tartalom is kell
)
```

**Hogyan működik a keresés?**
- **Domain filter**: Előszűrés → csak marketing dokumentumok
- **Cosine similarity**: Szemantikus hasonlóság a szűrt halmazon
- `similarity = cos(θ) = (A · B) / (||A|| × ||B||)`
- Érték: 0 (teljesen eltérő) → 1 (azonos jelentés)
- Pl.: `query_vec ≈ chunk_vec` → magas score (0.7-0.9)
- **Előny**: HR kérdés nem talál marketing anyagokat, gyorsabb keresés

#### **2.3 Citation Objektumok Létrehozása**
```python
citations = [
    Citation(
        doc_id="1ACEdQxgUuAsDHKPBqKyp2kt88DjfXjhv#chunk2",
        title="Aurora_Digital_Brand_Guidelines_eng.docx",
        score=0.89,  # Milyen releváns (0-1)
        content="Maximális sorhossz: 70-80 karakter.\nMegfelelő mennyiségű üres tér..."
    ),
    # ... további 4 chunk
]
```

---

### **3. LLM Generálás (Context-Aware Response)**

**Komponens:** `backend/services/agent.py` → `QueryAgent._generation_node`

#### **3.1 Retrieval Hívás**
```python
# Agent LangGraph node-ja
citations = await rag_client.retrieve_for_domain(
    domain="marketing",
    query="Mi a sorhossz?",
    top_k=5
)
# → 5 legközelebbi chunk visszajön
```

#### **3.2 Context Building**
```python
context_parts = []
for i, citation in enumerate(citations, 1):
    if i <= 3:  # Top 3: teljes tartalom
        context_parts.append(f"[Document {i}: {citation.title}]\n{citation.content}")
    else:  # 4-5: csonkított (timeout elkerülése)
        context_parts.append(f"[Document {i}: {citation.title}]\n{citation.content[:300]}...")

context = "\n\n".join(context_parts)
```

#### **3.3 LLM Prompt Assembly**
```python
prompt = f"""
You are a helpful Marketing assistant.

Retrieved documents (use ALL relevant information):
{context}

User query: "{query}"

Provide a comprehensive answer based on the retrieved documents above.
Use proper formatting with line breaks and bullet points.
Answer in Hungarian if the query is in Hungarian.
"""

answer = llm.invoke(prompt)
```

**Példa Generated Answer:**
```
A brand guideline sorhosszra vonatkozó javaslat:

### Maximális sorhossz
- **70-80 karakter** a javasolt maximális érték
- Megfelelő mennyiségű üres tér alkalmazása kötelező

### Elrendezés
- Rácsszerkezethez igazított layout
- Függőleges ritmus előnyben részesítése
```

---

### **4. Adatfolyam Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│              OFFLINE INDEXELÉS (Multi-Domain)                │
├─────────────────────────────────────────────────────────────┤
│ Google Drive Docs (HR/IT/Finance/Marketing/etc.)            │
│                          ↓                                   │
│              Text Extraction → Chunking                      │
│                          ↓                                   │
│          Domain Metadata Tag ({"domain": "marketing"})       │
│                          ↓                                   │
│              OpenAI Embedding (1536-d)                       │
│                          ↓                                   │
│    Qdrant multi_domain_kb (COSINE + domain payload index)   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              RUNTIME LEKÉRDEZÉS (Domain-Filtered)            │
├─────────────────────────────────────────────────────────────┤
│ User Query: "Mi a sorhossz?"                                 │
│       ↓                                                      │
│ [1] Intent Detection (keyword: "sorhossz" → marketing)      │
│       ↓                                                      │
│ [2] Query Embedding (OpenAI)                                 │
│       ↓                                                      │
│ [3] Qdrant Search (Domain Filter + Cosine Similarity)       │
│     ├─ Filter: {"domain": "marketing"}                      │
│     └─ Semantic: COSINE similarity, top_k=5                 │
│       ↓                                                      │
│ [4] Top 5 Chunks Retrieved (csak marketing docs!)           │
│   - Aurora_Brand_Guidelines_eng.docx (score: 0.89)          │
│   - Aurora_Arculati_Kezikonyv_HU.docx (score: 0.87)         │
│   - ...                                                      │
│       ↓                                                      │
│ [5] Context Building (Top 3 full, rest truncated)           │
│       ↓                                                      │
│ [6] LLM Prompt + Generation (GPT-4o-mini)                    │
│       ↓                                                      │
│ [7] Formatted Answer + Citations                             │
│       ↓                                                      │
│ [8] Frontend Rendering (Markdown → HTML)                     │
└─────────────────────────────────────────────────────────────┘
```

---

### **5. Kulcs Technológiák**

| **Komponens** | **Szerepe** | **Technológia** |
|---|---|---|
| `sync_domain_docs.py` | **Multi-domain indexelés** | Google Drive API, OpenAI Embeddings, Qdrant, domain metadata |
| `sync_marketing_docs.py` | Régi marketing-specifikus indexelés | Google Drive API, OpenAI Embeddings, Qdrant |
| `QdrantRAGClient` | **Hibrid retrieval (szemantikus + domain filter)** | Qdrant Python client, COSINE similarity, payload filtering |
| `QueryAgent._retrieval_node` | RAG orchestration | LangGraph workflow |
| `QueryAgent._generation_node` | Context-aware LLM generálás | OpenAI GPT-4o-mini |
| Qdrant Database | Vektor tárolás + domain indexelés | In-memory vector DB (Docker), payload index |
| LangChain Text Splitter | Chunking | RecursiveCharacterTextSplitter |
| OpenAI Embeddings | Szöveg → vektor | `text-embedding-3-small` (1536-d) |

---

### **6. Miért Működik Jól?**

✅ **Szemantikus keresés**: Nem keyword match, hanem jelentés alapú
   - "sorhossz", "line length", "character limit" → azonos vektorban

✅ **Domain-specifikus szűrés**: Csak releváns tudásbázisban keres
   - HR kérdés → csak HR dokumentumok
   - Marketing kérdés → csak marketing dokumentumok
   - Gyors payload index → ms-os szűrés

✅ **Chunking stratégia**: Nagy dokumentumok → kezelhető darabok
   - 800 char chunks + 100 char overlap
   - Natural separators: `\n\n`, `\n`, `. `

✅ **Hibrid keresés készenlét**: 
   - Jelenleg: Szemantikus (dense vectors) + domain filter
   - Jövő: + Lexikális (sparse vectors/BM25) márkanevek, kódok esetén

✅ **Top-K ranking**: Csak releváns információk kerülnek az LLM-nek
   - 5 legjobb chunk (0.4-0.9 score)
   - Timeout elkerülése: Top 3 full content, rest truncated

✅ **Domain detection**: Marketing queries → marketing collection
   - Keyword-based pre-classification (20+ terms)
   - LLM fallback általános esetekre

✅ **Citation tracking**: Minden chunk forrása nyomon követhető
   - `source_file_name` → Frontend "Források" megjelenítés
   - `chunk_index` → Pontos hivatkozás a dokumentumon belül
   - **`domain`** → Domain szűrés (hr, it, finance, marketing, stb.)

---

### **7. Indexelés Futtatása**

#### **Univerzális Multi-Domain Indexelés (ÚJ)**

Az új `sync_domain_docs.py` script bármilyen domainhez tud dokumentumokat indexelni:

```bash
# Marketing dokumentumok
cd backend
python scripts/sync_domain_docs.py --domain marketing --folder-id 1Jo5doFrRgTscczqR0c6bsS2H0a7pS2ZR

# HR dokumentumok (példa)
python scripts/sync_domain_docs.py --domain hr --folder-id YOUR_HR_FOLDER_ID

# IT dokumentumok (példa)
python scripts/sync_domain_docs.py --domain it --folder-id YOUR_IT_FOLDER_ID

# Finance dokumentumok (példa)
python scripts/sync_domain_docs.py --domain finance --folder-id YOUR_FINANCE_FOLDER_ID
```

**Kimenet:**
```
🚀 Starting Domain Documents Sync
🏷️  Domain: MARKETING
📂 Google Drive Folder: 1Jo5doFrRgTscczqR0c6bsS2H0a7pS2ZR
🗄️  Qdrant Collection: multi_domain_kb
📊 Qdrant: localhost:6333

✅ Collection 'multi_domain_kb' created with domain index
📥 Downloading: Aurora_Digital_Brand_Guidelines_eng.docx
📄 Parsing: Aurora_Digital_Brand_Guidelines_eng.docx
✅ Extracted 5234 characters
✂️  Split into 7 chunks (domain=marketing)
🧠 Generating embeddings for 7 chunks...
✅ Generated 7 embeddings
⬆️  Uploading 7 points to Qdrant (domain=marketing)...
✅ Uploaded 7 points

🎉 Sync Complete for MARKETING Domain!
✅ Success: 3 files
❌ Errors: 0 files
📊 Total points in collection: 11
📊 Points for MARKETING domain: 11
```

#### **Régi Marketing-Specifikus Script (Kompatibilitás)**

A régi `sync_marketing_docs.py` továbbra is működik:

```bash
cd backend
python scripts/sync_marketing_docs.py
```

#### **Domain-Specifikus Keresés Előnyei**

**Hibrid Keresés + Domain Szűrés:**
- **Szemantikus keresés**: Vektor hasonlóság (COSINE distance)
- **Domain filter**: Csak az adott domain dokumentumaiban keres
- **Készenlét lexikálisra**: BM25 support készen áll (sparse vectors hozzáadásával)

**Példa: HR kérdés csak HR dokumentumokban keres**
```python
# Backend automatikusan domain filter-t alkalmaz
query = "szabadság politika"
domain = "hr"  # Intent detection alapján

# Qdrant keresés domain filter-rel:
filter = {"must": [{"key": "domain", "match": {"value": "hr"}}]}
results = qdrant.search(query_vector=..., query_filter=filter)
# Eredmény: Csak HR dokumentumok, nem találja a marketing/IT anyagokat
```

**Multi-Domain Collection Előnyei:**
- ✅ Egyetlen Qdrant collection az összes domainhez
- ✅ Domain filter index → gyors szűrés (ms)
- ✅ Skálázható: Új domain hozzáadása egyszerű
- ✅ Központosított管理: Egy helyen az összes tudásbázis

---

### **8. Példa: End-to-End Trace**

**User Input:**
```
"Mi a brand guideline sorhossz ajánlása?"
```

**1. Intent Detection:**
```
Keyword match: "sorhossz" → marketing domain
```

**2. Query Embedding:**
```
[0.189, -0.623, 0.412, ..., 0.734] (1536 floats)
```

**3. Qdrant Search Results:**
```json
[
  {
    "score": 0.89,
    "payload": {
      "text": "Maximális sorhossz: 70–80 karakter.\nMegfelelő mennyiségű üres tér alkalmazása.",
      "source_file_name": "Aurora_Digital_Brand_Guidelines_eng.docx",
      "chunk_index": 2
    }
  },
  {
    "score": 0.87,
    "payload": {
      "text": "Rács szerkezethez igazított elrendezés.\nFüggőleges ritmus előnyben részesítése.",
      "source_file_name": "Aurora_Digital_Arculati_Kezikonyv_HU.docx",
      "chunk_index": 1
    }
  }
]
```

**4. LLM Context:**
```
Retrieved documents:
[Document 1: Aurora_Digital_Brand_Guidelines_eng.docx]
Maximális sorhossz: 70–80 karakter.
Megfelelő mennyiségű üres tér alkalmazása.

[Document 2: Aurora_Digital_Arculati_Kezikonyv_HU.docx]
Rács szerkezethez igazított elrendezés.
...

User query: "Mi a brand guideline sorhossz ajánlása?"
```

**5. Generated Answer:**
```markdown
A brand guideline sorhosszra vonatkozó javaslat:

### Maximális sorhossz
- **70-80 karakter** a javasolt maximális érték
- Megfelelő mennyiségű üres tér alkalmazása kötelező

### Elrendezés
- Rács szerkezethez igazított layout
- Függőleges ritmus előnyben részesítése
```

**6. Frontend Display:**
```
🤖 Bot válasz: [formatált markdown HTML-lé renderelve]
📎 Források: Aurora_Digital_Brand_Guidelines_eng.docx, Aurora_Digital_Arculati_Kezikonyv_HU.docx
```

---

### **9. Troubleshooting**

**Probléma:** "Unknown" források jelennek meg
- **Ok:** Frontend cache vagy payload field mapping hiba
- **Megoldás:** 
  - Ellenőrizd: `payload.get("source_file_name")` helyes?
  - Cache buster: `<script src="/static/app.js?v=X"></script>`
  - Frontend rebuild: `docker-compose build --no-cache frontend`

**Probléma:** Üres vagy irreleváns válaszok
- **Ok:** Nincs elég releváns chunk Qdrant-ban
- **Megoldás:**
  - Futtasd újra: `python scripts/sync_marketing_docs.py`
  - Ellenőrizd: `qdrant_client.count(collection_name="marketing")`
  - Növeld `top_k` értékét 5-ről 10-re

**Probléma:** Worker timeout
- **Ok:** Túl sok full content az LLM promptban
- **Megoldás:** Context truncation (Top 3 full, rest 300 char limit)

---

## 🛡️ Hibakezelés és Production Features

### **Automatikus Retry Logika**

A rendszer automatikus retry-t használ exponenciális backoff-fal OpenAI API hibák esetén:

**Hibakezelés rétegek:**
```
┌─────────────────────────────────────────┐
│ Layer 1: Input Validation (API)        │
│ - Max 10,000 tokens (~40k chars)       │
│ - HTTP 413 if exceeded                 │
│ - Empty query check                    │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Layer 2: Prompt Validation (Agent)     │
│ - Max 100,000 tokens                   │
│ - Auto-truncate to top 3 docs          │
│ - Token estimation logging             │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Layer 3: Retry Logic (OpenAI Client)   │
│ - Max 3 retries                        │
│ - Exponential backoff (1s, 2s, 4s)    │
│ - Jitter for thundering herd           │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Layer 4: Model Limit (gpt-4o-mini)     │
│ - 128k context window                  │
└─────────────────────────────────────────┘
```

**Retry stratégia:**
- ✅ **RateLimitError (429)**: Retry with `Retry-After` header respect
- ✅ **APITimeoutError**: Retry with exponential backoff
- ✅ **APIConnectionError**: Retry for network issues
- ✅ **Server errors (5xx)**: Retry up to 3 times
- ❌ **Client errors (4xx)**: No retry (immediate fail)
- ❌ **AuthenticationError (401)**: No retry (invalid API key)

**Használat:**
```python
from infrastructure.error_handling import retry_with_exponential_backoff

@retry_with_exponential_backoff(max_retries=3)
def call_openai_api():
    return client.chat.completions.create(...)
```

### **Token és Költség Tracking**

**Usage Stats Endpoint:**
```bash
# Aktuális használat lekérdezése
curl http://localhost:8001/api/usage-stats/

# Response:
{
  "calls": 127,
  "prompt_tokens": 45200,
  "completion_tokens": 12800,
  "total_tokens": 58000,
  "total_cost_usd": 0.0874  # GPT-4o-mini pricing
}

# Statisztikák nullázása
curl -X DELETE http://localhost:8001/api/usage-stats/
```

**Költség becslés (GPT-4o-mini per 1M tokens):**
- Input: $0.15
- Output: $0.60
- Példa: 5k input + 500 output = $0.00105

### **HTTP Status Codes**

A rendszer részletes HTTP státusz kódokat használ:

| Kód | Jelentés | Példa |
|-----|----------|-------|
| **200** | Success | Query sikeresen feldolgozva |
| **400** | Bad Request | Üres query, validációs hiba |
| **404** | Not Found | Session vagy file nem létezik |
| **413** | Request Too Large | Query >10k tokens (~40k chars) |
| **500** | Internal Server Error | Backend exception |
| **503** | Service Unavailable | OpenAI API down vagy timeout |

### **Input Validation**

**Query méret védelem:**
```python
# views.py
query_text = request.data.get("query", "")

# 1. Empty check
if not query_text.strip():
    return Response({"error": "Query cannot be empty"}, status=400)

# 2. Token limit check (10k tokens)
try:
    check_token_limit(query_text, max_tokens=10000)
except ValueError:
    return Response(
        {"error": "Query too long. Max 10,000 tokens (~40k chars)"},
        status=413
    )
```

**Példa túl nagy query blokkolása:**
```bash
# 54k karakteres query
curl -X POST http://localhost:8001/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "very long text..." * 2000}'

# Response: HTTP 413
{
  "error": "Query is too long. Please shorten your question to under 10,000 tokens (~40,000 characters)."
}
```

### **Logging és Monitoring**

**Strukturált logging minden rétegen:**
```python
# Intent detection
logger.info(f"Detected domain: {domain}")

# Retrieval
logger.info(f"Retrieved {len(citations)} documents from Qdrant (domain={domain})")

# Token tracking
logger.info(f"Prompt size: ~{estimate_tokens(prompt)} tokens")

# Error handling
logger.warning(f"Rate limited (attempt {attempt}/3). Waiting {wait_time:.1f}s...")
logger.error(f"Query too long: {estimated} tokens (max: {max_tokens})")
```

**Log példa:**
```
2025-12-17 08:14:31 INFO QueryAgent: Detected domain: marketing
2025-12-17 08:14:32 INFO QdrantRAGClient: Retrieved 5 docs (domain=marketing)
2025-12-17 08:14:32 INFO QueryAgent: Prompt size: ~3200 tokens
2025-12-17 08:14:33 INFO error_handling: API call #127: 3200 + 450 tokens, cost: $0.000750
```

---

## 🔐 Biztonság & Compliance

✅ **Citations**: Minden válasz tartalmazza a forrás dokumentum ID-ját  
✅ **Audit Log**: Teljes conversation history mentése  
✅ **Reset Context**: Special command a beszélgetési előzmények törlésére  
✅ **User Profiles**: Soha nem törlődnek, csak frissíthetők  

## 🛠️ Fejlesztés

### Local Dev (BASH/WSL)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # vagy venv\Scripts\activate (Windows)
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
python manage.py runserver 0.0.0.0:8000

# Frontend (új terminal)
cd frontend
npx http-server . -p 3000
```

### Docker Dev

```bash
docker-compose up --build
# Changes are auto-reloaded (gunicorn --reload)
```

## 📚 Kapcsolódó Dokumentumok

- [**Feature List (FEATURES.md)**](FEATURES.md) - **🆕 Teljes feature lista implementációs részletekkel**
- [Installation Guide](../INSTALLATION.md)
- [API Documentation](API.md) - REST API endpoints, cache-stats
- [Redis Cache Architecture](REDIS_CACHE.md) - Cache stratégia, invalidálás, monitoring
- [Google Drive Setup](GOOGLE_DRIVE_SETUP.md) - Drive API konfiguráció
- [Frontend Setup](FRONTEND_SETUP.md) - Tailwind CSS, Nginx
- [LangGraph Usage (Repo)](../ai_agent_complex/docs/LANGGRAPH_USAGE_HU.md)
- [Agent Loop (Repo)](../ai_agent_complex/docs/AGENT_LOOP_HU.md)
- [Architecture (Repo)](../ai_agent_complex/docs/ARCHITECTURE.md)

## 🤝 Roadmap

### ✅ Elkészült
- [x] Multi-domain Qdrant collection (domain filtering)
- [x] Google Drive API integration (marketing docs)
- [x] Redis cache (embedding + query result, 54% hit rate)
- [x] Cache invalidálás (sync_domain_docs.py auto-invalidation)
- [x] Token tracking & cost calculation
- [x] Unit tesztek (61 teszt, 87-100% coverage)
- [x] Hibakezelés (retry logic, exponential backoff)
- [x] Multi-domain workflows (HR szabadság, IT ticket)
- [x] **Like/Dislike feedback system** (Postgres + background threading)
- [x] **Citation feedback API** (/api/feedback/citation/, /api/feedback/stats/)
- [x] **Domain-scoped feedback aggregation** (materialized views)

### 🚧 Tervezett
- [ ] Frontend UI feedback buttons (👍👎 per citation)
- [ ] Citation re-ranking (feedback-weighted semantic relevance)
- [ ] Query embedding context-aware feedback scoring
- [ ] Multi-query generation (5 variáció, frequency ranking)
- [ ] BM25 sparse vectors (lexikális keresés)
- [ ] Monitoring & logging (Prometheus + Grafana)
- [ ] Integration tesztek (E2E multi-domain RAG + feedback)
- [ ] Slack integration
- [ ] Frontend React version (optional)

## 📞 Support

Ha kérdésed van, nyisd meg az issue-t vagy nézd meg a `docs/` mappát.

---

**Happy Knowledge Routing! 🚀**
