# RAG Agent - Dokumentum-Alapú AI Asszisztens

Teljes körű magyar nyelvű alkalmazás dokumentumok feltöltéséhez, kategorizálásához és AI-alapú kérdezéshez (RAG - Retrieval Augmented Generation) valós idejű aktivitás-naplózással.

## 🎯 Funkciók

- **📄 Dokumentum Feltöltés**: Markdown, TXT, PDF fájlok feltöltése kategóriák szerint
- **🏷️ Kategóriás Indexelés**: Kategóriánként külön vektoradatbázis-gyűjtemények
- **🤖 LLM Kategória-Routing**: OpenAI alapú intelligens kategóriaválasztás
- **🔍 RAG Alapú Válaszadás**: Csak a feltöltött dokumentumokból válaszol
- **📋 Valós Idejű Aktivitás Naplózás**: Háttérfolyamatok nyomon követése az Activity Logger panelban
- **💬 Idézések & Források**: Válaszok idézésekkel és a forrás-chunkok megjelölésével
- **🔄 Kontextus Törlés**: `reset context` paranccsal tisztázza a beszélgetést
- **💾 Perzisztens Tárolás**: JSON-alapú felhasználói profilok és beszélgetési előzmények
- **🌐 Fallback Keresés**: Ha a routed kategóriában nincs találat, az összes kategóriában keres

## 🏗️ Architektúra

```
Backend (Python FastAPI):
├── domain/                      # SOLID interfaces & domain modellek
│   ├── models.py               # Pydantic DataClasses
│   ├── interfaces.py           # Abstract base classes (ActivityCallback, etc.)
│
├── infrastructure/              # Konkrét implementációk
│   ├── embedding.py            # OpenAI embeddings
│   ├── vector_store.py         # ChromaDB vektortárolás
│   ├── chunker.py              # Tiktoken-alapú chunking
│   ├── extractors.py           # Dokumentum-szöveg extraktálás
│   ├── category_router.py      # LLM kategória-routing
│   ├── rag_answerer.py         # RAG válaszgenerálás
│   └── repositories.py         # JSON perzisztencia
│
├── services/                    # Üzleti logika
│   ├── upload_service.py       # Dokumentum feltöltés & indexelés (ActivityCallback)
│   ├── rag_agent.py            # LangGraph agent (ActivityCallback)
│   └── chat_service.py         # Chat koordináció (ActivityCallback)
│
└── main.py                     # FastAPI, QueuedActivityCallback, GET /api/activities

Frontend (React + TypeScript + Vite):
├── components/
│   ├── App.tsx                 # Fő komponens
│   ├── ActivityLogger.tsx      # Valós idejű aktivitás-napló (1s polling)
│   ├── Chat.tsx                # Chat interfész
│   └── UploadPanel.tsx         # Dokumentum feltöltés
├── contexts/
│   └── ActivityContext.tsx     # Global state (useActivity hook)
├── styles/
│   └── activity-logger.css     # Activity Logger stílus
└── api.ts                      # HTTP API kliens

Data:
├── users/                      # user_id.json
├── sessions/                   # session_id.json
├── uploads/                    # Feltöltött fájlok
├── derived/                    # chunks.json
└── chroma_db/                  # ChromaDB vektortárolás
```

## 🚀 Gyors Indítás

### Előfeltételek

- **OpenAI API kulcs** (szükséges: `OPENAI_API_KEY` env var)
- **Python 3.9+** (helyi fejlesztéshez)
- **Node.js 18+** (helyi fejlesztéshez)
- **Docker & Compose** (opcionális)

### 1. Helyi Fejlesztés (Ajánlott)

```bash
cd /path/to/2_hw

# .env fájl beállítása
cp .env.example .env
# Szerkeszd a .env fájlt és add meg az OPENAI_API_KEY értékét

# Szerver indítása (backend + frontend)
source .env && ./start-dev.sh

# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
```

### 2. Docker Compose

```bash
cd /path/to/2_hw
export OPENAI_API_KEY="sk-..."
docker-compose up --build

# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

## 📊 Activity Logger

Az Activity Logger panel (**📋 Tevékenység** gomb) valós időben mutatja az összes háttérfolyamatot:

**Feltöltési Folyamat:**
- 📄 Dokumentum feldolgozása
- 📖 Szöveg kinyerése (karakterszám)
- ✂️ Chunkolás (chunk darabszám)
- 🔗 Embedding feldolgozása
- 📊 Vektor-indexelés
- 💾 Chunkok mentése
- ✅ Feltöltés kész

**Chat & RAG Pipeline:**
- 💬 Kérdés feldolgozása
- 🎯 Kategória felismerés
- 🔍 Dokumentum keresése
- 📚 Chunkok lekérése
- �� Válasz generálása
- ✅ Válasz kész

Az összes event időrendben jelenik meg (legfrissebb felül).

## 🔌 API Végpontok

### Chat & Dokumentumkezelés

- `POST /api/chat` - Kérdés feldolgozása
- `POST /api/files/upload` - Dokumentum feltöltés
- `GET /api/activities` - Aktivitás-naplók (1s polling-hez)

### Admin

- `GET /api/health` - Szerver státusz
- `GET /api/desc-get` - Kategória leírása
- `POST /api/desc-save` - Kategória leírás mentése
- `POST /api/cat-match` - Kategória felismerés

## 🔧 Fejlesztés

### Backend

```bash
cd backend
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
python3 main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📁 Projektstruktúra

```
2_hw/
├── README.md
├── ARCHITECTURE.md                # Részletes architektúra
├── GETTING_STARTED.md             # Lépésenkénti útmutató
├── DEPLOYMENT.md                  # Deployment útmutató
├── PROJECT_SUMMARY.md             # Projekt összefoglalása
├── ACTIVITY_LOGGER_GUIDE.md       # Activity Logger dokumentáció
│
├── backend/
├── frontend/
├── DOCUMENTATION/                 # Teszt fájlok (almappában)
├── data/                          # Runtime adatok
├── start-dev.sh                   # Szerver indítás
├── stop-dev.sh                    # Szerver leállítás
└── .env                           # Env változók
```

## 🐛 Hibaelhárítás

### A backend nem indul el
```bash
# Ellenőrizd az API kulcsot
echo $OPENAI_API_KEY
source .env  # Újra betöltés
```

### Az Activity Logger nem frissül
```bash
# Ellenőrizd az API-t
curl http://localhost:8000/api/activities
```

---

# 📚 TELJES KÖRŰ HASZNÁLATI ÚTMUTATÓ

## 1️⃣ Felhasználó Azonosítás

Az alkalmazás automatikusan az operációs rendszer felhasználónevét használja a felhasználó azonosítására.

### Hogyan működik?
1. Az alkalmazás induláskor **GET /api/system-info** kérést küld a backendhez
2. A backend lekéri az aktuális OS felhasználónevet (`os.getenv('USER')`)
3. Ez az érték minden adatmappában megjelenik:
   - User profil: `data/users/{username}.json`
   - Beszélgetés előzmények: `data/sessions/{username}_{session_id}.json`
   - Feltöltött dokumentumok: `data/uploads/{username}/...`

### Felhasználói Profil Estrutúra
```json
{
  "username": "gabor.toth",
  "created_at": "2026-01-01T12:00:00",
  "categories": {
    "Dokumentáció": { "description": "...", "created_at": "2026-01-01T12:15:00" },
    "Oktatási Anyagok": { "description": "...", "created_at": "2026-01-01T12:30:00" }
  },
  "preferences": {
    "similarity_threshold": 0.6,
    "max_chunks_per_answer": 5,
    "language": "hu"
  }
}
```

---

## 2️⃣ Kategória Létrehozás & Description.json Generálása

### A folyamat lépésről lépésre

#### **Lépés 1: Kategória Megnevezése (UI)**
1. Kattints az **"Dokumentum Feltöltés"** panel jobb felső "➕ Új Kategória" gombra
2. Írj be egy kategórianevet: pl. **"Projekt Dokumentáció"**
3. Kattints az **"✓ Mentés"** gombra
   - Az Activity Logger jelenítse: `🏷️ Kategória létrehozva: Projekt Dokumentáció`

#### **Lépés 2: Mi történik a Backenden?**

Amikor új kategóriát hozol létre:
1. Az alkalmazás létrehozza a kategóriát a user profil `categories` mapjében
2. **Description.json generálódik automatikusan** az első feltöltéskor
3. Addig üres/generic leírás: `"A Projekt Dokumentáció kategória dokumentumai"`

#### **Lépés 3: Description.json Struktúra**

```json
{
  "Projekt Dokumentáció": {
    "title": "Projekt Dokumentáció",
    "description": "Projekt specifikáció, fejlesztési útmutatók, API referencia",
    "created_at": "2026-01-01T12:15:00",
    "document_count": 3,
    "sample_topics": [
      "Rendszerarchitektúra",
      "API végpontok",
      "Konfigurációs paraméterek"
    ],
    "llm_description": "Technikai dokumentáció, fejlesztőknek szól, tartalmaz kódpéldákat"
  },
  "Jogi Dokumentumok": {
    "title": "Jogi Dokumentumok",
    "description": "Szerződések, adatvédelmi szabályzatok, felhasználási feltételek",
    ...
  }
}
```

#### **Mire Használódik a Description?**

Az LLM kategória-routing lépésben ezt a leírást használja:

```
Felhasználó kérdése: "Mi a maximum chunk méret?"

LLM instrukció:
  "Mely kategóriához tartozik ez a kérdés?"
  
  Elérhető kategóriák:
  - Projekt Dokumentáció: "Technikai dokumentáció, fejlesztőknek szól, tartalmaz kódpéldákat"
  - Jogi Dokumentumok: "Szerződések, adatvédelmi szabályzatok, felhasználási feltételek"
  
LLM válasza: → "Projekt Dokumentáció" ✓
```

#### **Description Szerkesztése (Optional)**

Ha pontosítani akarod a kategória leírását:
1. Chat interfészbe írj: `/desc Projekt Dokumentáció`
2. Az alkalmazás megjeleníti az aktuális description-t
3. Meghatározhatod az új szöveget, majd `/save` paranccsal mentheted

---

## 3️⃣ Dokumentum Feltöltés - Teljes Folyamat

### Mi történik valós időben az Activity Loggerben?

Amikor egy dokumentumot feltöltesz, ez az eseményszekvencia jelenik meg:

```
📋 Tevékenység (7 esemény)

1. 📄 Dokumentum feldolgozása: "projekt_spec.pdf" (kategória: Projekt Dokumentáció)
2. 📖 Szöveg kinyerése: 4532 karakter feldolgozva
3. ✂️ Chunkolás: 12 chunk-ra felosztva (átl. 378 karakter/chunk)
4. 🔗 Embedding generálása: 12 vektor feldolgozása (OpenAI API)
5. 📊 Vektor-indexelés: ChromaDB-ben tárolva
6. 💾 Metadata mentése: chunks.json frissítve
✅ Feltöltés sikeresen befejezve!
```

### Mi történik a Backenden?

**1. Fájl validáció & szöveg kinyerés**
```
▶ backend/services/upload_service.py
  └─ Támogatott formátumok:
     ├─ .txt / .md (egyszerű szöveg)
     ├─ .pdf (PyPDF2 library)
     └─ .docx (python-docx library)
```

**2. Chunkolás (Token-alapú szegmentálás)**
```
Eredeti szöveg (4532 karakter):
"Az alkalmazás egy teljes körű RAG rendszer, amely OpenAI API-t "
"használ a szöveg-embedding generálásához. A dokumentumok feltöltése "
"után azok automatikusan indexelésre kerülnek egy ChromaDB vektortárolóban..."

↓ Tiktoken tokenizer (cl100k_base encoding)

Chunkok (max 400 token):
├─ Chunk 1: "Az alkalmazás egy teljes körű RAG rendszer..." (380 token)
├─ Chunk 2: "A dokumentumok feltöltése után azok..." (395 token)
└─ Chunk 3: "...indexelésre kerülnek egy ChromaDB..." (290 token)
```

**3. Embedding & Indexelés**
```
Minden chunk → OpenAI API (text-embedding-3-small model)
↓
1536-dimenziós vektorbemenet
↓
ChromaDB kollekcióba tárolás (kategóriánként külön)
```

**4. Metadata Mentése**

Egyenlege feltöltés után a `data/derived/chunks.json` frissül:

```json
{
  "Projekt Dokumentáció": {
    "project_spec.pdf": {
      "chunks": [
        {
          "id": "proj_spec_chunk_1",
          "text": "Az alkalmazás egy teljes körű RAG rendszer...",
          "embedding": [0.123, -0.456, 0.789, ...],  // 1536 dimenzió
          "start_char": 0,
          "end_char": 380,
          "metadata": {
            "source": "project_spec.pdf",
            "page": 1,
            "uploaded_by": "gabor.toth",
            "uploaded_at": "2026-01-01T12:30:00"
          }
        },
        { ... }
      ]
    }
  }
}
```

---

## 4️⃣ Keresés & RAG Pipeline - A Válasz Megalkotása

### A felhasználó szemszögéből
1. **Kérdés begépelése**: `"Hogyan működik a kategória routing?"`
2. **Enter lenyomása** → Activity Logger aktiválódik
3. **Válasz és chunkok** megjelennek (~2-5 másodperc)

### A backend szemszögéből - 4 Fázis

#### **Fázis 1: Kategória-Routing (LLM döntés)**

```
Input: "Hogyan működik a kategória routing?"
↓
LLM instrukció:
  "Mely kategóriában keressünk?"
  Lehetőségek: [Projekt Dokumentáció, Jogi Dokumentumok, ...]
↓
LLM Output: "Projekt Dokumentáció"
Activity Log: 🎯 Kategória felismerve: Projekt Dokumentáció
```

#### **Fázis 2: Vektor-Keresés (Embedding Hasonlóság)**

```
Input kérdés: "Hogyan működik a kategória routing?"
↓
OpenAI Embedding API
↓
Query vektor (1536 dim): [0.234, -0.567, ...]
↓
ChromaDB keresés (Projekt Dokumentáció kollekcióban):
  - Cosine similarity számolása az összes chunk ellen
  - Top-5 eredmény (< 0.7 similarity alapértelmezett)

Activity Log: 🔍 Dokumentum keresése (Projekt Dokumentáció)
             📚 5 chunk találva, átl. 0.78 hasonlóság
```

#### **Fázis 3: Fallback Keresés (Ha nincs találat)**

```
Ha Projekt Dokumentációban < 2 relevans chunk:
  Activity Log: ⚠️ Fallback keresés aktiválva
  ↓
  Összes kategóriában keresés
  ↓
  Activity Log: 📚 Összesen 8 chunk találva az összes kategóriában
```

#### **Fázis 4: LLM Válasz Generálása (RAG)**

```
Context (az 5 relevans chunk):
  - Chunk 1: "A kategória routing az LLM-et használja..." (0.89 hasonlóság)
  - Chunk 2: "A kategóriák description.json alapján..." (0.84 hasonlóság)
  - Chunk 3: "Fallback keresés aktiválódik, ha..." (0.76 hasonlóság)
  - ...
↓
LLM instrukció:
  "Válaszolj a következő kérdésre csak az alábbi dokumentumok alapján:
   Kérdés: 'Hogyan működik a kategória routing?'
   Dokumentumok: [5 chunk szövege]"
↓
LLM Output (markdown formátum):
  "A kategória routing a LLM-et használja a felhasználó kérdésének 
   automatikus kategóriához rendeléséhez. 
   
   [[chunk_proj_spec_1 | 0.89 hasonlóság]]
   
   A kategóriák description.json alapján történik az intelligens 
   kategóriaválasztás.
   
   [[chunk_routing_guide_2 | 0.84 hasonlóság]]"

Activity Log: 🤖 Válasz generálása OpenAI API-val
             ✅ Válasz kész! (2.3s alatt)
```

---

## 5️⃣ Data Persistencia - Hol Tárolódik Min?

Az alkalmazás JSON-alapú tárolást használ automatikus persistenciához:

```
data/
├── users/
│   └── gabor.toth.json              # Felhasználói profil, kategóriák, preferenciák
│
├── sessions/
│   ├── gabor.toth_session_001.json  # Chat előzmények
│   └── gabor.toth_session_002.json  # (új session minden újraindítás)
│
├── uploads/
│   └── gabor.toth/
│       ├── projekt_spec.pdf         # Feltöltött fájlok
│       ├── api_guide.md
│       └── ...
│
├── derived/
│   └── chunks.json                  # Feldolgozott chunkok, embedding metaadatok
│
└── chroma_db/
    └── (ChromaDB vektoradatbázis)   # Valódi embeddings, indexek
```

**Automatikus mentések:**
- User profil: Kategória-módosítás után
- Chunks: Feltöltés után
- Chat előzmények: Minden üzenet után
- ChromaDB: Embedding létrehozás után

---

## 6️⃣ Activity Logger - Összes Event Típus Részletesen

Az Activity Logger **valós idejű** a háttérfolyamatok megjeleníti a felhasználónak.

### Event Típusok & Szín-Kódozás

#### 📄 **Info (Kék) - Információs Üzenetek**
```
💬 Chat üzenet begépelve
📋 Activity Logger megnyitva
🏷️ Kategória létrehozva: Új kategória név
📌 Preferenciák módosítva
```

#### 🔄 **Processing (Narancs) - Folyamatban Lévő Műveletek**
```
📖 Szöveg kinyerése...
✂️ Chunkolás folyamatban...
🔗 Embedding generálása...
🎯 Kategória felismerés...
🔍 Dokumentum keresése...
🤖 Válasz generálása...
📊 Vektor-indexelés...
```

#### ✅ **Success (Zöld) - Sikeres Műveletek**
```
✅ Feltöltés sikeresen befejezve!
✅ Válasz kész! (2.3s alatt)
✅ Kategória sikeresen létrehozva
✅ Description frissítve
```

#### ⚠️ **Warning (Sárga) - Figyelmeztetések**
```
⚠️ Fallback keresés aktiválva
⚠️ Alacsony hasonlóság (< 0.6)
⚠️ Max chunkok száma elérve
```

#### ❌ **Error (Piros) - Hibák**
```
❌ Fájl feldolgozási hiba: Nem támogatott formátum
❌ OpenAI API hiba: Rate limit exceeded
❌ ChromaDB kapcsolódási hiba
❌ Kategória nem található
```

### Activity Panel Kezelése

**Gomb funkciók (jobb felső sarok):**
- **📋 Tevékenység (N)** - Megnyitja/bezárja a panelt (N = aktív eventek száma)
- **🔼/🔽 Kiterjesztés** - Kicsiny → Teljes képernyő (50% viewport)
- **🗑 Törlés** - Összes log bejegyzés törlése
- **✕ Bezárás** - Panel bezárása (de az eventek továbbra is logolódnak)

**Eventos lista:**
- Minden event **FIFO** sorrendben jelenik meg (legfrissebb felül)
- Timestamp minden event mellett: HH:MM:SS
- **Kattintható chunkok**: Lásd a 7. fejezetet

---

## 7️⃣ LLM Válasz & Kattintható Chunk Hivatkozások

### Válasz Formátuma

Az LLM-től kapott válasz **markdown formátum** + **embed hivatkozások**:

```
A kategória routing a LLM-et használja a felhasználó kérdésének 
automatikus kategóriához rendeléséhez.

[[chunk_proj_spec_1 | 0.89 hasonlóság]]

A kategóriák description.json alapján történik az intelligens 
kategóriaválasztás. Ez lehetővé teszi a pontosabb keresést.

[[chunk_routing_guide_2 | 0.84 hasonlóság]]

Ha az elsődleges kategóriában nincs elegendő relevans dokumentum,
a rendszer aktiválja a fallback keresést.

[[chunk_fallback_explain | 0.76 hasonlóság]]
```

### Chunk Hivatkozás Struktúra

Minden `[[chunk_id | hasonlóság]]` hivatkozás:
- **Kattintható link** → Megnyit egy modal panelt
- **chunk_id** = a forrás chunk egyedi azonosítója
- **hasonlóság** = cosine similarity érték (0.0 - 1.0)

### Modal Panel - Chunk Részletei

Kattintás a `[[chunk_proj_spec_1 | 0.89]]` hivatkozásra:

```
╔═══════════════════════════════════════════════════════════╗
║  Chunk Részletei - projekt_spec.pdf                       ║
╠═══════════════════════════════════════════════════════════╣
║                                                            ║
║  📄 Forrás: projekt_spec.pdf                              ║
║  🏷️  Kategória: Projekt Dokumentáció                      ║
║  📍 Pozíció: 0-380 karakter                               ║
║  👤 Feltöltő: gabor.toth                                 ║
║  📅 Feltöltés dátuma: 2026-01-01 12:30:00                 ║
║                                                            ║
║  🎯 Hasonlóság: 0.89 (89%)                                ║
║                                                            ║
║  ═══════════════════════════════════════════════════════  ║
║  CHUNK SZÖVEGE:                                            ║
║  ───────────────────────────────────────────────────────  ║
║  "Az alkalmazás egy teljes körű RAG rendszer, amely       ║
║   OpenAI API-t használ a szöveg-embedding generálásához.  ║
║   A dokumentumok feltöltése után azok automatikusan       ║
║   indexelésre kerülnek egy ChromaDB vektoradatbázisban,  ║
║   mely lehetővé teszi a gyors és pontos keresést..."      ║
║                                                            ║
║  ═══════════════════════════════════════════════════════  ║
║  TOVÁBBI RELEVÁNS CHUNKOK (ugyanből a dokumentumból):     ║
║  ───────────────────────────────────────────────────────  ║
║  • Chunk 2 (0.84 hasonlóság) - "Kategória routing..."    ║
║  • Chunk 3 (0.78 hasonlóság) - "ChromaDB integrálás..."  ║
║  • Chunk 5 (0.72 hasonlóság) - "Embedding modell..."     ║
║                                                            ║
║                          [Bezárás]                        ║
╚═══════════════════════════════════════════════════════════╝
```

### Hasonlóság Értékek Értelmezése

```
🟢 0.85 - 1.00  → Kiváló találat (szinte azonos téma)
🟡 0.70 - 0.84  → Jó találat (relevans, de nem azonos)
🟠 0.60 - 0.69  → Elfogadható (tárgyhoz kapcsolódó)
🔴 < 0.60       → Gyenge találat (nem jelenik meg alapértelmezetten)
```

### Miért Fontos a Hasonlóság?

Segít megérteni:
- **Mennyire relevans** a válasz a kérdéshez
- **Miért választotta ki** ezt a chunk-ot az LLM
- **Hogy van más**, még relevánsabb chunk a dokumentumban

---

## 📋 Teljes Workflow Összefoglaló

```
┌─────────────────────────────────────────────────────────┐
│                    FELHASZNÁLÓ                           │
└─────────────┬───────────────────────────────────────────┘
              │
    1. Kategória létrehozás (pl. "Projekt Dokumentáció")
    │  ↓ Backend: categories szekció a user profil-ban
    │  ↓ Description.json placeholder létrehozása
    │
    2. Dokumentum feltöltés (proj_spec.pdf)
    │  ↓ Szöveg kinyerés (4532 karakter)
    │  ↓ Chunkolás (12 chunk)
    │  ↓ Embedding generálása (OpenAI)
    │  ↓ ChromaDB indexelés
    │  ↓ chunks.json frissítés
    │
    3. Kérdés feltevése ("Hogyan működik a kategória routing?")
    │  ↓ Kategória-routing (LLM → Projekt Dokumentáció)
    │  ↓ Vektor-keresés (top-5 chunk a kategóriából)
    │  ↓ Fallback keresés (ha <2 relevans chunk)
    │  ↓ LLM válasz generálása
    │  ↓ Chunk hivatkozások beágyazása
    │
    4. Chunk modal megnyitása (kattintás a hivatkozásra)
    │  ↓ Hasonlóság érték (0.89)
    │  ↓ Chunk teljes szövege
    │  ↓ Metaadatok (forrás, dátum, feltöltő)
    │  ↓ További relevans chunkok
    │
    5. Activity Logger követése
       ✓ Összes esemény időrendben
       ✓ Szín-kódozás típus szerint
       ✓ Success/Error/Processing indikátorok

┌─────────────────────────────────────────────────────────┐
│                    ADATBÁZISOK                           ║
├─────────────────────────────────────────────────────────┤
│ • ChromaDB          - Vektorok & hasonlóság keresés     │
│ • JSON fájlok       - User profil, chunkok, előzmények  │
│ • OpenAI API        - Embedding & LLM API hívások       │
└─────────────────────────────────────────────────────────┘
```

---

**Legutolsó frissítés**: 2026. január 1.
