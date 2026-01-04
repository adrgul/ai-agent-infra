# LangGraph Workflows Documentation

**Implementáció dátuma:** 2025-12-28  
**Verzió:** Phase 2.0 Enhancement  
**Státusz:** ✅ IMPLEMENTED

---

## 🎯 ÁTTEKINTÉS

Ez a dokumentum magyarázza, hogy **miért és hogyan** lettek implementálva a LangGraph-alapú workflow-k a Phase 2.0 projektben.

### Implementált Workflow-k:
1. **Document Processing Workflow** - Automata dokumentum feldolgozás
2. **Session Memory Workflow** - Automata session lezárás és memória létrehozás
3. **(Meglévő) RAG Workflow** - Intelligent RAG routing (P0.7 + P0.8)
4. **(Meglévő) Chat Workflow** - Alapvető chat feldolgozás

---

## 📋 1. DOCUMENT PROCESSING WORKFLOW

### 🔍 Miért?

**PROBLÉMA (Régi megoldás):**
- Dokumentum feltöltés **3 külön API hívás** volt:
  1. `POST /api/documents/upload` → file feltöltés
  2. `POST /api/documents/{id}/chunk` → chunking
  3. `POST /api/documents/{id}/embed` → embedding + Qdrant

**Hátrányok:**
- Frontend-nek 3 külön hívást kellett kezelni
- Hibakezelés bonyolult (melyik lépésnél állt le?)
- Nincs automatikus retry
- Nehéz debuggolni
- Rossz UX (user látja a közbülső lépéseket)

**MEGOLDÁS (LangGraph Workflow):**
- **1 API hívás**: `POST /api/workflows/process-document`
- Automatikus pipeline: upload → extract → chunk → embed → Qdrant → verify
- State tracking minden lépésnél
- Hibakezelés built-in
- Könnyű debuggolni (state inspection)

### 🏗️ Architektúra

**Workflow lépések:**
```
START
  → validate_file          [fájl típus, méret ellenőrzés]
  → extract_content        [PDF/TXT/MD text extraction]
  → store_document         [PostgreSQL tárolás]
  → chunk_document         [LangChain text splitter]
  → generate_embeddings    [OpenAI embeddings batch]
  → upsert_to_qdrant      [Qdrant vector upload]
  → verify_completion     [végső ellenőrzés]
  → END (success)

Error handling:
  Bármelyik lépésnél hiba → handle_error → END (failed)
```

**State Object:**
```python
class DocumentProcessingState(TypedDict):
    # Input
    filename: str
    content_bytes: bytes
    file_type: str
    tenant_id: int
    user_id: int
    visibility: Literal["private", "tenant"]
    
    # Intermediate (tracking)
    extracted_text: Optional[str]
    document_id: Optional[int]
    chunk_ids: List[int]
    embedding_count: int
    qdrant_point_ids: List[str]
    
    # Output
    status: str  # "success" | "failed"
    error: Optional[str]
    processing_summary: Dict[str, Any]
```

### 🎯 Előnyök

1. **Single API Call**
   - Frontend: 1 hívás helyett 3
   - Egyszerűbb error handling
   - Jobb UX (loading state 1x)

2. **State Tracking**
   - Minden lépés eredménye tracked
   - Debug könnyű: "Melyik lépésnél állt le?"
   - Partial failure recovery lehetséges

3. **Automatic Error Recovery**
   - Conditional edges minden lépésnél
   - Hibakezelés központi (handle_error node)
   - Error message kontextuális (melyik lépés failezett)

4. **Consistency**
   - Mindig ugyanaz a pipeline
   - Nincs "elfelejtettem chunk-olni" probléma
   - Guaranteed order of operations

5. **Extensibility**
   - Könnyű új lépés beszúrása (pl. OCR, format detection)
   - Retry logic implementálható
   - Batch processing támogatás

### 📝 Használat

**Frontend (előtte):**
```typescript
// OLD WAY - 3 API calls
const uploadRes = await fetch('/api/documents/upload', {...});
const {document_id} = await uploadRes.json();

const chunkRes = await fetch(`/api/documents/${document_id}/chunk`, {...});
const embeddingRes = await fetch(`/api/documents/${document_id}/embed`, {...});
```

**Frontend (utána):**
```typescript
// NEW WAY - 1 API call
const formData = new FormData();
formData.append('file', file);
formData.append('tenant_id', tenantId);
formData.append('user_id', userId);
formData.append('visibility', 'tenant');

const response = await fetch('/api/workflows/process-document', {
  method: 'POST',
  body: formData
});

const result = await response.json();
// result = {
//   status: "success",
//   document_id: 123,
//   summary: {
//     filename: "example.pdf",
//     content_length: 5000,
//     chunk_count: 10,
//     embedding_count: 10,
//     qdrant_vectors: 10
//   }
// }
```

### 🧪 Tesztelés

**Manual test script:**
```powershell
# debug/test_document_workflow.ps1
$file = Get-Content "test.pdf" -Encoding Byte -Raw
$boundary = [System.Guid]::NewGuid().ToString()

$body = @"
--$boundary
Content-Disposition: form-data; name="file"; filename="test.pdf"
Content-Type: application/pdf

$([System.Text.Encoding]::Default.GetString($file))
--$boundary
Content-Disposition: form-data; name="tenant_id"

1
--$boundary
Content-Disposition: form-data; name="user_id"

2
--$boundary
Content-Disposition: form-data; name="visibility"

tenant
--$boundary--
"@

Invoke-RestMethod -Uri "http://localhost:8000/api/workflows/process-document" `
  -Method POST `
  -ContentType "multipart/form-data; boundary=$boundary" `
  -Body $body
```

---

## 📋 2. SESSION MEMORY WORKFLOW

### 🔍 Miért?

**PROBLÉMA (Tervezett P1.1):**
- Session lezárás és long-term memory létrehozása **manuális lépések** lennének:
  1. Session-ből messages betöltése
  2. LLM summary generálás
  3. Embedding létrehozás
  4. Qdrant upload (longterm_chat_memory collection)
  5. PostgreSQL long_term_memories táblába mentés
  6. Session processed flag beállítás

**Hátrányok manuális megközelítésnél:**
- Komplex logika (6 lépés)
- Könnyű elrontani (pl. elfelejted a flag-et → duplicate processing)
- Nincs built-in skip logic (rövid session-öket felesleges menteni)
- Error handling bonyolult
- Nehéz batch processing

**MEGOLDÁS (LangGraph Workflow):**
- **Automatikus pipeline** session close-nál
- Decision node: érdemes-e summarize-olni? (min 3 interaction)
- Skip rövid session-öket
- Duplicate prevention (processed_for_ltm flag check)
- Built-in error recovery

### 🏗️ Architektúra

**Workflow lépések:**
```
START
  → validate_session           [létezik? már processed?]
  → load_interactions          [összes message betöltése]
  → decide_if_summary_needed   [min 3 interaction? → YES/NO]
    ├─ YES → generate_summary  [LLM conversation summary]
    │        → embed_summary   [embedding vector]
    │        → upsert_to_qdrant [longterm_chat_memory collection]
    │        → mark_processed  [PostgreSQL update]
    │        → END (success)
    │
    └─ NO  → skip_processing   [túl rövid session]
             → END (skipped)

Error handling:
  Bármelyik lépésnél hiba → handle_error → END (failed)
```

**State Object:**
```python
class SessionMemoryState(TypedDict):
    # Input
    session_id: str
    tenant_id: int
    user_id: int
    
    # Intermediate
    session_data: Optional[Dict]
    interactions: List[Dict]
    interaction_count: int
    needs_summary: bool  # Decision node output
    summary_text: Optional[str]
    embedding_vector: Optional[List[float]]
    qdrant_point_id: Optional[str]
    ltm_id: Optional[int]
    
    # Output
    status: str  # "success" | "skipped" | "failed"
    error: Optional[str]
    processing_summary: Dict[str, Any]
```

### 🎯 Előnyök

1. **Smart Skip Logic**
   - Rövid session-öket (< 3 interaction) automatikusan skipeli
   - Nincs felesleges LLM hívás
   - Nincs "üres" memory Qdrant-ban

2. **Duplicate Prevention**
   - Validate node: `processed_for_ltm` flag check
   - Ha már processed → status: "skipped"
   - Batch processing safe

3. **Automatic Session Close**
   - Frontend: 1 API hívás session close-nál
   - Backend: teljes pipeline automatikus
   - User nem látja a közbülső lépéseket

4. **Error Recovery**
   - Minden lépés independent check
   - Ha embedding fail → Qdrant nem károsodik
   - Részletes error tracking (melyik lépésnél állt le)

5. **Batch Processing Ready**
   - Könnyen batch-elhető: összes "nem processed" session
   - Scheduled job: éjszaka process all old sessions
   - Rate limiting support (LLM quota)

### 📝 Használat

**Session lezárás (Frontend):**
```typescript
// User clicks "End Session" button
const response = await fetch('/api/workflows/close-session', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: currentSessionId,
    tenant_id: userTenantId,
    user_id: userId
  })
});

const result = await response.json();

if (result.status === 'success') {
  // Long-term memory created
  console.log(`Memory ID: ${result.ltm_id}`);
  console.log(`Summary: ${result.summary.summary_length} chars`);
} else if (result.status === 'skipped') {
  // Session too short, not saved
  console.log('Session too short for memory');
} else {
  // Error
  console.error(`Failed: ${result.error}`);
}
```

**Batch processing (Backend cron job):**
```python
# Scheduled job: Process all old sessions
from services.session_memory_workflow import SessionMemoryWorkflow
from database.pg_init import get_unprocessed_sessions

async def batch_process_sessions():
    workflow = SessionMemoryWorkflow(openai_api_key=API_KEY)
    
    sessions = get_unprocessed_sessions(older_than_hours=24)
    
    for session in sessions:
        try:
            result = await workflow.process_session(
                session_id=session['id'],
                tenant_id=session['tenant_id'],
                user_id=session['user_id']
            )
            
            logger.info(f"Session {session['id']}: {result['status']}")
        except Exception as e:
            logger.error(f"Session {session['id']} failed: {e}")
```

### 🧪 Tesztelés

**Manual test script:**
```powershell
# debug/test_session_memory.ps1
$body = @{
    session_id = "test-session-123"
    tenant_id = 1
    user_id = 2
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:8000/api/workflows/close-session" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**Expected outcomes:**

1. **Success (long session):**
```json
{
  "status": "success",
  "ltm_id": 42,
  "summary": {
    "session_id": "test-session-123",
    "interaction_count": 8,
    "summary_length": 245,
    "qdrant_point_id": "uuid-xxx-yyy"
  }
}
```

2. **Skipped (short session):**
```json
{
  "status": "skipped",
  "ltm_id": null,
  "summary": {
    "session_id": "test-session-123",
    "reason": "Too few interactions (2)"
  }
}
```

3. **Failed (error):**
```json
{
  "status": "failed",
  "error": "Embedding generation failed: API timeout",
  "summary": {
    "session_id": "test-session-123",
    "completed_steps": ["load", "summary"]
  }
}
```

---

## 🔄 3. MEGLÉVŐ WORKFLOWS (már implementált)

### RAG Workflow (P0.7 + P0.8)

**File:** `backend/services/rag_workflow.py`

**Workflow:**
```
START
  → validate_input
  → build_context
  → decide_if_rag_needed        [🆕 P0.8 enhancement]
    ├─ YES → retrieve_document_chunks
    │        → check_retrieval_results
    │        → [generate_answer | fallback]
    │        → END
    │
    └─ NO  → generate_direct_answer  [conversational, no RAG]
             → END
```

**Miért LangGraph?**
- Complex conditional routing (conversational vs RAG)
- State tracking (needs_rag, retrieved_chunks, has_relevant_context)
- Multiple decision points
- Clean separation of concerns

**Előnyök:**
- Natural conversation support (P0.8)
- Document retrieval when needed
- Fallback handling (no relevant docs)
- Source attribution
- Error recovery

### Chat Workflow (Phase 1.5)

**File:** `backend/services/chat_workflow.py`

**Workflow:**
```
START
  → process_message    [validate context]
  → generate_response  [LLM call]
  → END
```

**Miért LangGraph?**
- Hierarchical prompt building (system → tenant → user)
- Message validation
- Clean LLM integration
- Future extensibility (add memory retrieval, tool calling, etc.)

**Előnyök:**
- Consistent prompt hierarchy
- Easy to extend (add nodes)
- State-based message handling
- Error tracking

---

## 📊 ÖSSZEFOGLALÓ: WORKFLOW COMPARISON

| Workflow | Lépések száma | Előnyök | Use Case |
|----------|---------------|---------|----------|
| **Document Processing** | 7 | Single API call, automatic pipeline | Document upload |
| **Session Memory** | 8 (with skip logic) | Smart skip, duplicate prevention | Session close |
| **RAG Workflow** | 5-7 (conditional) | Intelligent routing, fallback | Chat with documents |
| **Chat Workflow** | 2 | Simple, hierarchical prompts | Basic chat |

---

## 🎯 MIKOR HASZNÁLJ LANGGRAPH-OT?

### ✅ Használd LangGraph-ot amikor:

1. **Multi-step process** komplex logikával
2. **Decision points** vannak (conditional routing)
3. **Error recovery** fontos minden lépésnél
4. **State tracking** szükséges (mi történt eddig?)
5. **Extensibility** jövőbeli követelmény
6. **Debugging** nehéz manuális flow-nál
7. **Consistency** kritikus (mindig ugyanaz a pipeline)

### ❌ NE használd LangGraph-ot amikor:

1. **Egyszerű CRUD** művelet (get/update/delete)
2. **Single-step** process (nincs pipeline)
3. **No decisions** (nincs branching)
4. **Trivial logic** (egyszerű if-else elég)
5. **Performance critical** hot path (overhead)

---

## 🚀 KÖVETKEZŐ LÉPÉSEK

### 1. Frontend Integration

**Document Upload:**
- Módosítani `DocumentUpload.tsx` component-et
- Használni új endpoint-ot: `POST /api/workflows/process-document`
- Single loading state (progress: 0-100%)

**Session Close:**
- "End Session" gomb
- Call `POST /api/workflows/close-session`
- Success message: "Session saved to memory"

### 2. Qdrant Extensions

**Session Memory Collection:**
```python
# QdrantService-ben új metódus kell:
def upsert_session_memory(self, embedding: List[float], payload: Dict) -> str:
    """Upload to longterm_chat_memory collection."""
    # Implementation needed
```

**Collection schema:**
```python
collection_name = "longterm_chat_memory"
vector_size = 3072
distance = "Cosine"
payload = {
    "tenant_id": int,
    "user_id": int,
    "session_id": str,
    "summary": str,
    "interaction_count": int,
    "created_at": str (ISO timestamp)
}
```

### 3. PostgreSQL Extensions

**Long-term memories table:**
```sql
-- Már létezik, csak ellenőrizni kell:
CREATE TABLE IF NOT EXISTS long_term_memories (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,  -- summary text
    qdrant_point_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Helper functions:**
```python
# database/pg_init.py-ban kell:
def insert_long_term_memory(...) -> int
def mark_session_processed_for_ltm(session_id: str) -> None
def get_session_by_id(session_id: str) -> Dict
def get_unprocessed_sessions(older_than_hours: int) -> List[Dict]
```

### 4. Testing

**Test scripts (debug/ mappában):**
- `test_document_workflow.ps1` - Full document pipeline
- `test_session_memory.ps1` - Session close workflow
- `test_workflow_status.ps1` - Check workflow availability

**Test cases:**
- [ ] Document upload: PDF, TXT, MD
- [ ] Document upload: invalid file type → error
- [ ] Document upload: empty file → error
- [ ] Session close: long session (8 interactions) → success
- [ ] Session close: short session (2 interactions) → skipped
- [ ] Session close: already processed → skipped
- [ ] Session close: session not found → error

### 5. Documentation Updates

**Update files:**
- [x] `LANGGRAPH_WORKFLOWS.md` (this file)
- [ ] `IMPLEMENTATION_STATUS.md` - Add workflow implementation status
- [ ] `INIT_PROMPT_2.md` - Update P1.1 implementation notes
- [ ] `README.md` - Add workflow usage examples

---

## 📚 TOVÁBBI FORRÁSOK

**LangGraph dokumentáció:**
- https://langchain-ai.github.io/langgraph/
- State management: https://langchain-ai.github.io/langgraph/concepts/#state
- Conditional edges: https://langchain-ai.github.io/langgraph/concepts/#conditional-edges

**Project files:**
- Document Workflow: `backend/services/document_processing_workflow.py`
- Session Memory: `backend/services/session_memory_workflow.py`
- RAG Workflow: `backend/services/rag_workflow.py`
- API Endpoints: `backend/api/workflow_endpoints.py`

**Related documentation:**
- `docs/P0.8_INTELLIGENT_RAG_ROUTING.md` - RAG routing logic
- `docs/HIERARCHICAL_PROMPTS.md` - Prompt hierarchy
- `docs/IMPLEMENTATION_STATUS.md` - Overall project status

---

**Implementált:** 2025-12-28  
**Státusz:** ✅ Implementálva, tesztelésre vár  
**Következő:** Frontend integráció + Qdrant collection setup
