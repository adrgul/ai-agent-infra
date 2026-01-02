# Lépésről Lépésre Útmutató

## 1. Előfeltételek

### Szükséges szoftverek:

- **Python 3.9+** (backend)
- **Node.js 16+** és **npm 8+** (frontend)
- **Git** (verziókezelés)
- **Docker & Docker Compose** (opcionális, de ajánlott)

### Szükséges API kulcsok:

- **OPENAI_API_KEY** (szükséges a chattől és az embedding-ektől)

## 2. Projekt Klónozása

```bash
cd /Users/tothgabor/ai-agents-hu/mini_projects/gabor.toth/2_hw
```

## 3. Lokális Fejlesztés (Ajánlott)

### 3.1 Backend Beállítása

```bash
cd backend

# Python virtual environment létrehozása
python3.9 -m venv venv
source venv/bin/activate  # macOS/Linux
# vagy: venv\Scripts\activate  # Windows

# Függőségek telepítése
pip install -r requirements.txt

# OPENAI_API_KEY beállítása
export OPENAI_API_KEY="sk-..."  # macOS/Linux
# vagy: set OPENAI_API_KEY=sk-...  # Windows

# Data könyvtárak létrehozása (ha nem léteznek)
mkdir -p ../data/{users,sessions,uploads,derived}

# Backend indítása
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Kimenet:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 3.2 Frontend Beállítása (Új terminálban)

```bash
cd frontend

# Függőségek telepítése
npm install

# Frontend indítása (Vite dev server)
npm run dev
```

**Kimenet:**
```
  VITE v5.0.0  ready in 123 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

### 3.3 Böngészőben Megnyitás

Nyisd meg: **http://localhost:5173/**

Az alkalmazás betöltődik, és jól működik ha:
- ✅ A Chat interfész látható (jobb oldal)
- ✅ Az Upload Panel látható (bal oldal)
- ✅ Az Activity Logger gomb elérhető (top-right sarokban)

## 4. Az Activity Logger Használata

### 4.1 Mi az Activity Logger?

Az **Activity Logger** egy valós idejű panel, amely megjeleníti az összes háttérfolyamatot:

```
Activity Log (14)  ← Kattints erre a panel megnyitásához
```

Megnyíl a dropdown panel, amely 16+ loggolt eseményt mutat **időrendben** (legújabb felül):

```
🤖 Válasz generálása OpenAI API-val (14:32:15)
📚 Dokumentumok lekérése: 5 chunk (14:32:14)
🎯 Kategória felismerés: Machine Learning (14:32:13)
💬 Kérdés feldolgozása (14:32:12)
```

### 4.2 Dokumentum Feltöltés (7 loggolt esemény)

1. **UploadPanel-ben**: 
   - Válassz egy kategóriát (pl. "Machine Learning")
   - Kattints a "Fájl kiválasztása" gombra
   - Válassz egy `.md` fájlt
   - Kattints az "Feltöltés" gombra

2. **Activity Logger-ben meglátod**:

```
✅ Feltöltés kész (14:25:30)
📊 Vektor-indexelés (14:25:29)
✓ Embedding kész (14:25:27)
🔗 Embedding feldolgozása (14:25:25)
✂️ Chunkolás: 12 darab (14:25:24)
📖 Szöveg kinyerése: 5432 karakter (14:25:23)
📄 Dokumentum feldolgozása (14:25:22)
```

**Mit csinál a backend:**
1. A fájl feldolgozása az UploadService-ben
2. Szöveg kinyerése (Markdown extractor)
3. Szövegdarabolás (TiktokenChunker, 900 token-es chunkok)
4. Embedding generálás (OpenAI API, batch size=100)
5. Vector indexelés (ChromaDB kollekcióba `cat_machine_learning`)
6. Chunkok mentése (data/derived/ JSON formátumban)
7. Feltöltés befejezése

### 4.3 Kérdezés (9 loggolt esemény)

1. **Chat panelban**:
   - Begépelsz egy kérdést: "Mi az a Machine Learning?"
   - Kattints az "Küldés" gombra (vagy Enter)

2. **Activity Logger-ben meglátod**:

```
✅ Válasz kész (14:32:15)
🤖 Válasz generálása OpenAI API-val (14:32:14)
📚 Dokumentumok lekérése: 5 chunk (14:32:12)
🎯 Kategória felismerés: Machine Learning (14:32:11)
💬 Kérdés feldolgozása (14:32:10)
```

**Mit csinál a backend:**
1. ChatService feldolgozza a kérdést
2. Kategória-döntés (GPT-4o-mini)
3. RAGAgent orchestrálódik:
   - A kérdés embedding-je
   - Vector search az adott kategóriában (top-k=5)
   - Fallback search, ha nincs találat (összes kategória)
4. Válasz generálás (ChatCompletion API + system prompt)
5. Válasz megjelenítése a Chat panelban

### 4.4 Activity Logger Kiváló Tulajdonságai

✅ **Valós idejű (1 másodperces polling)**
```
Az Activity Logger a backend-et 1 másodpercenként lekérdezi
Nem szükséges frissíteni a böngészőt
```

✅ **Kombinált nézet (API + lokális események)**
```
API-ből jövő events (backend lépések)
+ Lokális events (frontend interakciók)
```

✅ **Időrendben rendezett (legújabb felül)**
```
Chronologikus sorrend az összes event között
Soha nem keveredik az időrend
```

✅ **Emoji-s visual feedback**
```
📄 Processing
🎯 Decisions
✅ Success
⚠️ Warnings
❌ Errors
```

## 5. Docker Használata (Alternatív)

### 5.1 Docker Compose-val

```bash
# A projekt gyökérjében (ahol docker-compose.yml van)
cd /Users/tothgabor/ai-agents-hu/mini_projects/gabor.toth/2_hw

# Setted az OPENAI_API_KEY-t:
export OPENAI_API_KEY="sk-..."

# Services indítása
docker-compose up --build

# Kimenet:
# backend_1   | INFO:     Uvicorn running on http://0.0.0.0:8000
# frontend_1  | ➜  Local:   http://localhost:5173/
```

### 5.2 Docker Compose Leállítása

```bash
docker-compose down

# Volumok törlésével (data törlése):
docker-compose down -v
```

## 6. Első Tesztüzenet

### Szcenárió: Oktatási Dokumentum Feltöltés

1. **Kategória**: "AI & Machine Learning"
2. **Fájl**: Ez a markdown (GETTING_STARTED.md)
3. **Kérdés**: "Mi az Activity Logger?"

### Lépések:

**Lépés 1: Feltöltés**

```
1. Kattints az Upload Panel "Fájl kiválasztása" gombjára
2. Válaszd ki a README.md-et
3. Kattints "Feltöltés"
4. Figyeld az Activity Logger-t
```

**Lépés 2: Kérdezés**

```
1. Chat panelban begépeled: "Mi az Activity Logger?"
2. Kattints "Küldés"
3. Figyeld az Activity Logger-t
4. Válasz megjelenik a chat-ben
```

**Lépés 3: Verifikálás**

```
✅ Mindkét panelban látod az eseményeket?
✅ Az Activity Logger 1 másodpercenként frissül?
✅ Az Activity Logger legújabb eventeket mutatja felül?
```

## 7. Hibaelhárítás

### Probléma: "OPENAI_API_KEY nincs beállítva"

**Megoldás:**

```bash
# macOS/Linux
export OPENAI_API_KEY="sk-..."

# Verifikálás
echo $OPENAI_API_KEY

# Windows
set OPENAI_API_KEY=sk-...

# Verifikálás
echo %OPENAI_API_KEY%
```

### Probléma: Port 8000/5173 már foglalt

**Megoldás:**

```bash
# Backend portjának megváltoztatása
cd backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Frontend portjának megváltoztatása
cd frontend
npm run dev -- --port 5174
```

### Probléma: "ModuleNotFoundError: No module named 'fastapi'"

**Megoldás:**

```bash
cd backend
pip install -r requirements.txt
```

### Probléma: "npm ERR! Cannot find module"

**Megoldás:**

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Probléma: Activity Logger nem frissül

**Megoldás:**

1. Nyisd meg a browser dev tools-ot (F12)
2. Nézd meg a Network tab-ot
3. Keress `api/activities` kéréseket
4. Hiba? Nézd meg a backend loggot

```bash
# Backend konzolja:
# INFO:     127.0.0.1:54321 - "GET /api/activities?count=100" - 200
```

## 8. Fejlesztő Parancsok

### Backend

```bash
cd backend

# Development mode (auto-reload)
uvicorn main:app --reload

# Linting
flake8 .

# Type checking
mypy .
```

### Frontend

```bash
cd frontend

# Development (Vite dev server)
npm run dev

# Production build
npm run build

# Linting
npm run lint
```

## 9. Projekt Szerkezete (Gyors Referencia)

```
2_hw/
├── backend/
│   ├── main.py                 ← FastAPI app entry
│   ├── requirements.txt         ← Python dependencies
│   ├── domain/
│   │   ├── interfaces.py        ← SOLID interfaces (ActivityCallback)
│   │   └── models.py            ← DataClasses
│   ├── infrastructure/
│   │   ├── embedding.py         ← OpenAI embedding
│   │   ├── vector_store.py      ← ChromaDB integration
│   │   ├── category_router.py   ← LLM categorization
│   │   ├── rag_answerer.py      ← LLM RAG answering
│   │   ├── chunker.py           ← Text chunking
│   │   ├── extractors.py        ← Document extractors
│   │   └── repositories.py      ← JSON persistence
│   └── services/
│       ├── upload_service.py    ← Document processing (7 logs)
│       ├── chat_service.py      ← Chat orchestration (2 logs)
│       └── rag_agent.py         ← LangGraph RAG (4 logs)
│
├── frontend/
│   ├── index.html               ← HTML entry
│   ├── vite.config.ts           ← Vite config
│   ├── package.json             ← Node dependencies
│   └── src/
│       ├── main.tsx             ← React entry
│       ├── App.tsx              ← Main component
│       ├── api.ts               ← HTTP client
│       ├── components/
│       │   ├── ActivityLogger.tsx ← Activity panel (NEW)
│       │   ├── Chat.tsx
│       │   └── UploadPanel.tsx
│       ├── contexts/
│       │   └── ActivityContext.tsx ← Global state (NEW)
│       └── styles/
│           └── activity-logger.css ← Activity styling (NEW)
│
├── data/                        ← Persistence (szerver indítésekor létrejon)
│   ├── users/
│   ├── sessions/
│   ├── uploads/
│   ├── derived/
│   └── chroma_db/
│
├── docker-compose.yml           ← Container orchestration
├── README.md                    ← Projekt README
├── ARCHITECTURE.md              ← Rendszer design
└── GETTING_STARTED.md           ← Ez a fájl
```

---

**Verzió**: 1.0  
**Legutolsó frissítés**: 2026. január 1.
