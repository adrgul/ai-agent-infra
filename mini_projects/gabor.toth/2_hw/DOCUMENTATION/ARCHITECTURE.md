# Rendszer Architektúra

## 1. Magas szintű áttekintés

A RAG Agent egy modern, rétegzett architektúrára épülő alkalmazás, amely dokumentumkezelést és AI-alapú kérdezést kombinál. Az **Activity Logger** valós idejű 16+ loggált eseményt biztosít a teljes feldolgozási folyamatban.

```
┌──────────────────────────────────────────────────────────┐
│ Frontend (React + TypeScript + Vite)                     │
│ ✅ Activity Logger (1s polling, valós idejű)            │
│ ✅ Chat Interface                                        │
│ ✅ Upload Panel                                          │
├──────────────────────────────────────────────────────────┤
│ Port: localhost:5173                                     │
└──────────────────────────────────────────────────────────┘
                        │ HTTP
┌──────────────────────▼──────────────────────────────────┐
│ FastAPI Backend (Python 3.9+)                           │
│ Port: localhost:8000                                    │
│                                                         │
│ ┌──────────────────────────────────────────────────┐   │
│ │ API Layer                                        │   │
│ │ • POST /api/chat                                 │   │
│ │ • POST /api/files/upload                         │   │
│ │ • GET /api/activities (Activity Log - NEW!)      │   │
│ │ • GET /api/categories                            │   │
│ │ • GET /api/profile/{user_id}                     │   │
│ └──────────────────────────────────────────────────┘   │
│                                                         │
│ ┌──────────────────────────────────────────────────┐   │
│ │ Service Layer (ActivityCallback INJECTED)        │   │
│ │ • ChatService ← ActivityCallback                 │   │
│ │ • UploadService ← ActivityCallback               │   │
│ │ • RAGAgent ← ActivityCallback                    │   │
│ └──────────────────────────────────────────────────┘   │
│                                                         │
│ ┌──────────────────────────────────────────────────┐   │
│ │ Domain Layer (SOLID Interfaces)                  │   │
│ │ • ActivityCallback ← ABSTRACT (NEW!)             │   │
│ │ • EmbeddingService, VectorStore, Chunker        │   │
│ │ • CategoryRouter, RAGAnswerer                    │   │
│ │ • Repositories (User, Session, Upload)          │   │
│ └──────────────────────────────────────────────────┘   │
│                                                         │
│ ┌──────────────────────────────────────────────────┐   │
│ │ Infrastructure Layer                             │   │
│ │ • QueuedActivityCallback (asyncio.Queue) - NEW! │   │
│ │ • OpenAIEmbeddingService                         │   │
│ │ • ChromaVectorStore                              │   │
│ │ • OpenAICategoryRouter, OpenAIRAGAnswerer        │   │
│ │ • JSON Repositories                              │   │
│ └──────────────────────────────────────────────────┘   │
│                                                         │
└──────────────────────────────────────────────────────────┘
          ┌────────────────┬────────────────┐
          │                │                │
      ┌───▼────────┐  ┌───▼────────┐  ┌───▼─────────┐
      │ OpenAI API │  │  ChromaDB   │  │ JSON Data   │
      │ (embeddings│  │ (vectors)   │  │ Persistence │
      │+ chat)     │  │             │  │ (users,     │
      └────────────┘  └─────────────┘  │  sessions,  │
                                        │  chunks)    │
                                        └─────────────┘
```

## 2. Backend Rétegek (Clean Architecture)

### Domain Layer (`backend/domain/`)

**interfaces.py** - Absztrakt kontraktok (SOLID):

```python
# ⭐ Activity Logger interface - az új fejlesztés szívverésé
class ActivityCallback(ABC):
    async def log_activity(
        self, 
        message: str, 
        activity_type: str = "info",
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Loggazza az activities-t valós időben.
        Types: "info", "processing", "success", "warning", "error"
        """

class EmbeddingService(ABC):
    async def embed_text(text: str) -> List[float]
    async def embed_texts(texts: List[str], batch_size=100) -> List[List[float]]

class VectorStore(ABC):
    async def add_chunks(collection_name, chunks, embeddings)
    async def query(collection_name, embedding, top_k=5) -> List[RetrievedChunk]

class Chunker(ABC):
    def chunk_text(text: str, chunk_size=900, overlap=150) -> List[Chunk]

class DocumentTextExtractor(ABC):
    def extract(file_content: bytes) -> str

class CategoryRouter(ABC):
    async def route_to_category(question: str, categories: List[str]) -> str

class RAGAnswerer(ABC):
    async def answer(question: str, context_chunks: List[RetrievedChunk]) -> str

class UserProfileRepository(ABC):
    async def get_user(user_id: str) -> UserProfile
    async def save_user(user_id: str, profile: UserProfile)

class SessionRepository(ABC):
    async def get_session(session_id: str) -> List[Message]
    async def append_message(session_id: str, message: Message)
    async def clear_session(session_id: str)

class UploadRepository(ABC):
    def save_upload(category: str, upload_id: str, filename: str, content: str) -> str
    async def save_chunks(category: str, upload_id: str, chunks: List[Chunk])
```

**models.py** - DataClasses:
- `Message`, `UserProfile`, `Chunk`, `UploadedDocument`
- `RetrievedChunk`, `CategoryDecision`, `RAGResponse`

### Infrastructure Layer (`backend/infrastructure/`)

**embedding.py**: `OpenAIEmbeddingService`
- OpenAI API wrapper (text-embedding-3-small)
- Batch processing (configurable size)

**vector_store.py**: `ChromaVectorStore`
- ChromaDB persistent client
- Per-category collections (naming: `cat_{category_slug}`)
- Similarity search (cosine distance)

**chunker.py**: `TiktokenChunker`
- Token-aware text chunking
- Overlap support (context preservation)

**extractors.py**: Document text extraction
- `MarkdownExtractor` (implemented)
- `PDFExtractor`, `DocxExtractor` (stubs)

**category_router.py**: `OpenAICategoryRouter`
- GPT-4o-mini for categorization
- Strict JSON output parsing

**rag_answerer.py**: `OpenAIRAGAnswerer`
- ChatCompletion API
- System prompt for context-only answers

**repositories.py**: Persistence implementations
- `JSONUserProfileRepository` (data/users/{user_id}.json)
- `JSONSessionRepository` (data/sessions/{session_id}.json)
- `FileUploadRepository` (data/uploads/, data/derived/)

### Services Layer (`backend/services/`)

**upload_service.py**: `UploadService` (ActivityCallback ← INJECTED)

```python
class UploadService:
    def __init__(
        self,
        activity_callback: Optional[ActivityCallback] = None,
        ...
    ):
        self.activity_callback = activity_callback
    
    async def process_upload(self, ...):
        # asyncio.create_task(_embed_and_index) → log 7 events:
        
        📄 await log_activity("Dokumentum feldolgozása")
        📖 await log_activity("Szöveg kinyerése: X karakter")
        ✂️ await log_activity("Chunkolás kész: Y darab")
        🔗 await log_activity("Embedding feldolgozása")
        ✓ await log_activity("Embedding kész")
        📊 await log_activity("Vektor-indexelés")
        ✅ await log_activity("Feltöltés kész")
        
        # Hiba esetén:
        ❌ await log_activity("Feltöltés hiba", type="error")
```

**chat_service.py**: `ChatService` (ActivityCallback ← INJECTED)

```python
class ChatService:
    def __init__(self, activity_callback: Optional[ActivityCallback] = None, ...):
        self.activity_callback = activity_callback
    
    async def process_message(self, question: str, ...):
        💬 await log_activity("Kérdés feldolgozása")
        🎯 await log_activity(f"Kategória felismerés: X kategória")
        
        # Fallback, ha nincs dokumentum:
        ⚠️ await log_activity("Nincs feltöltött dokumentum", type="warning")
```

**rag_agent.py**: LangGraph-based RAG (ActivityCallback ← STATE)

```
LangGraph Graph:
├── Node 1: category_decide
│   └── LLM kategória döntés
│
├── Node 2: retrieve
│   ├── Embed question
│   └── ChromaDB query (top-k=5)
│
└── Node 3: generate
    ├── 🔄 log_activity("Fallback keresés") [if needed]
    ├── 📚 log_activity(f"Dokumentumok lekérése: X chunk")
    ├── 🤖 log_activity("Válasz generálása OpenAI API-val")
    └── ✅ log_activity("Válasz kész")
```

### Main Application (`backend/main.py`)

FastAPI with Activity Logger (NEW):

```python
# NEW: QueuedActivityCallback implementation
class QueuedActivityCallback(ActivityCallback):
    def __init__(self, max_size: int = 1000):
        self.events: asyncio.Queue = asyncio.Queue(maxsize=max_size)
    
    async def log_activity(self, message, activity_type="info", metadata=None):
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "type": activity_type,  # "info", "processing", "success", "warning", "error"
            "metadata": metadata or {}
        }
        self.events.put_nowait(event)
    
    async def get_activities(self, count: int = 50) -> List[Dict]:
        # Return last N events
        ...

# Initialize activity callback
activity_callback = QueuedActivityCallback(max_size=1000)

# Inject into services (DEPENDENCY INJECTION)
upload_service = UploadService(activity_callback=activity_callback, ...)
chat_service = ChatService(activity_callback=activity_callback, ...)

# API Endpoints
@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Calls chat_service.process_message(activity_callback injected)
    ...

@app.post("/api/files/upload")
async def upload_file(file: UploadFile):
    # Calls upload_service.process_upload(activity_callback injected)
    ...

@app.get("/api/activities")  # NEW!
async def get_activities(count: int = 50):
    # Returns recent events from QueuedActivityCallback
    return {"activities": await activity_callback.get_activities(count)}
```

## 3. Frontend Rétegek (React + TypeScript + Vite)

### Activity Logger System (NEW)

**ActivityContext.tsx** - Global State Management:

```typescript
interface Activity {
  id: string
  timestamp: string
  message: string
  type: "info" | "processing" | "success" | "warning" | "error"
  metadata?: Record<string, any>
}

interface ActivityContextValue {
  entries: Activity[]
  addActivity(message: string, type?: string): void
  updateActivity(id: string, updates: Partial<Activity>): void
  clearActivities(): void
}

// Hook usage:
const { entries, addActivity } = useActivity()
```

**ActivityLogger.tsx** - Valós idejű Panel (NEW):

```typescript
// Polling mechanism (1 second interval when open)
useEffect(() => {
  if (!isOpen) return

  const interval = setInterval(async () => {
    const response = await fetch('http://localhost:8000/api/activities?count=100')
    const data = await response.json()
    setApiActivities(data.activities)
  }, 1000)

  return () => clearInterval(interval)
}, [isOpen])

// Combine & Sort (newest first)
const allActivities = [...apiActivities, ...entries]
  .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))

// Display in dropdown
return (
  <div className="activity-logger">
    <button onClick={() => setIsOpen(!isOpen)}>
      Activity Log ({allActivities.length})
    </button>
    {isOpen && (
      <div className="activity-panel">
        {allActivities.map(activity => (
          <ActivityItem key={activity.id} activity={activity} />
        ))}
      </div>
    )}
  </div>
)
```

### Components (`src/components/`)

- **App.tsx**: Main app with ActivityProvider wrapper
- **ActivityLogger.tsx**: Real-time activity display (1s polling) NEW
- **Chat.tsx**: Chat interface (logs messages locally + via activity callback)
- **UploadPanel.tsx**: Document upload UI (logs locally + via activity callback)

### Contexts (`src/contexts/`)

- **ActivityContext.tsx**: Global activity state + useActivity hook NEW

### Styling (`src/`)

- **activity-logger.css**: Activity Logger styling (350+ lines) NEW
  - Dropdown animation
  - Event type colors (info, processing, success, warning, error)
  - Timestamps & metadata display

## 4. Adatkezelés

### Persistence Stratégia

```
data/
├── users/{user_id}.json
│   └── UserProfile (never deleted)
│
├── sessions/{session_id}.json
│   └── Message[] (append-only)
│       └── "reset context" command clears only this
│
├── uploads/
│   └── {category}/{upload_id}__{filename}
│       └── Original documents
│
├── derived/
│   └── {category}/{upload_id}/chunks.json
│       └── Text chunks metadata
│
└── chroma_db/
    ├── cat_machine_learning/
    ├── cat_ai/
    └── ... (Category collections)
```

### ChromaDB Gyűjtemények

- Collection naming: `cat_{category_slug}`
- Chunk ID format: `{upload_id}:{chunk_index}`
- Metadata per chunk: chunk_id, source_file, category, chunk_index, chunk_size_tokens, overlap_tokens

## 5. Adatfolyamok (Data Flows)

### Dokumentum Feltöltés Pipeline

```
Frontend Upload Panel
  ↓ POST /api/files/upload
Backend UploadService.process_upload()
  ├─→ 📄 "Dokumentum feldolgozása"
  ├─→ Extract text
  ├─→ 📖 "Szöveg kinyerése: X karakter"
  ├─→ Chunk text
  ├─→ ✂️ "Chunkolás: Y darab"
  ├─→ Create embeddings
  ├─→ 🔗 "Embedding feldolgozása"
  ├─→ 📊 "Vektor-indexelés"
  ├─→ 💾 Save chunks to JSON
  └─→ ✅ "Feltöltés kész"
      ↓
Frontend Activity Logger (polling /api/activities every 1s)
  └─→ Combine API + local events
  └─→ Sort by timestamp (newest first)
  └─→ Display all 7 events in real-time
```

### Kérdezés Pipeline

```
Frontend Chat
  ↓ POST /api/chat + question
Backend ChatService.process_message()
  ├─→ 💬 "Kérdés feldolgozása"
  ├─→ 🎯 "Kategória felismerés"
  └─→ Call RAGAgent
      ↓
  LangGraph State Machine
  ├─ category_decide node → route question
  ├─ retrieve node → embed + vector search
  └─ generate node
      ├─→ 🔄 "Fallback keresés" [if needed]
      ├─→ 📚 "Dokumentumok lekérése: X chunk"
      ├─→ 🤖 "Válasz generálása OpenAI API-val"
      └─→ ✅ "Válasz kész"
      ↓
Frontend Activity Logger (polling /api/activities)
  └─→ Combine API + local events
  └─→ Sort by timestamp (newest first)
  └─→ Display all 9 events in real-time
```

## 6. Technológiai Stack

**Backend:**
- FastAPI (async, ASGI)
- LangGraph (state-based RAG workflow)
- OpenAI API (embeddings + ChatCompletion)
- ChromaDB (vector database)
- Tiktoken (token-aware chunking)
- asyncio + Queue (activity logging)
- Python 3.9+

**Frontend:**
- React 18
- TypeScript
- Vite (build tool)
- fetch API (HTTP client)
- Context API (state management)

**Infrastructure:**
- Docker & Docker Compose
- JSON files (persistence)
- ChromaDB (vector storage)

## 7. Event Logging Teljesség (16 Events)

| # | Komponens | Esemény | Emoji | Típus | New? |
|---|-----------|---------|-------|-------|------|
| 1 | UploadService | Dokumentum feldolgozása | 📄 | processing | ✅ |
| 2 | UploadService | Szöveg kinyerése | 📖 | processing | ✅ |
| 3 | UploadService | Chunkolás kész | ✂️ | success | ✅ |
| 4 | UploadService | Embedding feldolgozása | 🔗 | processing | ✅ |
| 5 | UploadService | Embedding kész | ✓ | success | ✅ |
| 6 | UploadService | Vektor-indexelés | 📊 | processing | ✅ |
| 7 | UploadService | Feltöltés kész | ✅ | success | ✅ |
| 8 | ChatService | Kérdés feldolgozása | 💬 | processing | ✅ |
| 9 | ChatService | Kategória felismerés | 🎯 | info | ✅ |
| 10 | ChatService | Nincs dokumentum | ⚠️ | warning | ✅ |
| 11 | RAGAgent | Fallback keresés | �� | processing | ✅ |
| 12 | RAGAgent | Dokumentumok lekérése | 📚 | processing | ✅ |
| 13 | RAGAgent | Válasz generálása | 🤖 | processing | ✅ |
| 14 | RAGAgent | Válasz kész | ✅ | success | ✅ |
| 15 | Any | Hiba történt | ❌ | error | ✅ |
| 16 | Any | Egyedi metadata | 📌 | info | ✅ |

## 8. Performance & Configuration

- **Embedding Batch Size**: 100 texts per OpenAI call
- **Chunk Size**: 900 tokens (tunable in TiktokenChunker)
- **Chunk Overlap**: 150 tokens (preserves context)
- **Vector Search Top-K**: 5 per category
- **Activity Polling Interval**: 1 second (frontend, when Activity Logger is open)
- **Activity Queue Max Size**: 1000 events (configurable)

## 9. Error Handling & Resilience

- Try-catch in service methods
- Activity log records all errors automatically
- Graceful degradation (fallback search if category not found)
- Queue size limits prevent memory bloat
- Activity polling stops when Activity Logger is closed (cleanup)

## 10. Ports (Simplified)

- **Backend**: 8000
- **Frontend**: 5173
- Only 2 ports in use (previously 5-6)

---

**Verzió**: 2.0 (Activity Logger integrálásával)  
**Legutolsó frissítés**: 2026. január 1.  
**Jelenlegi állapot**: ✅ Production-ready, 16 loggált eseménnyel
