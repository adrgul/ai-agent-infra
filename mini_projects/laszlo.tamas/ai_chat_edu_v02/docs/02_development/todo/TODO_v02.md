# TODO_v02.md
## Phase 2.0 – Task Tracking & Implementation Checklist

**Last Updated:** 2026-01-02  
**Status Overview:** P0 (Core RAG) ✅ | P0.11-P0.17 ✅ | P0.9-P0.10 ⏳ NEXT | P1-P2 ⏳ PENDING

---

## 🔥 **CRITICAL ISSUES**

### ✅ Message Metadata Persistence (P0.13)
**Priority:** HIGH  
**Added:** 2026-01-02  
**Status:** ✅ COMPLETED (2026-01-02)

**Problem:**  
Oldal újratöltés után a chat buborékokban **nem jelentek meg**:
- ❌ RAG forrás hivatkozások (sources)
- ❌ RAG paraméterek (TOP_K, MIN_SCORE_THRESHOLD értékek)

**Root Cause:**  
A `chat_messages` táblában csak a `content` mező volt mentve. A metadata (sources, rag_params) **NEM** perszisteálódott.

**Solution:**
1. **Database Schema Update:**
   ```sql
   ALTER TABLE chat_messages ADD COLUMN metadata JSONB;
   CREATE INDEX idx_chat_messages_metadata ON chat_messages USING gin(metadata);
   ```

2. **Backend - Save Metadata:**
   ```python
   # backend/api/routes.py - /api/chat/rag endpoint
   insert_message_pg(
       session_id=session_id,
       tenant_id=request.tenant_id,
       user_id=request.user_id,
       role="assistant",
       content=assistant_answer,
       metadata={  # NEW!
           "sources": result["sources"],
           "rag_params": result.get("rag_params"),
           "actions_taken": result.get("actions_taken")
       }
   )
   ```

3. **Backend - Load Metadata:**
   ```python
   # backend/database/pg_init.py - get_session_messages_pg
   SELECT message_id, role, content, metadata, created_at
   FROM chat_messages
   WHERE session_id = %s
   ORDER BY created_at ASC
   ```

4. **Frontend - Display Metadata:**
   ```typescript
   // frontend/src/App.tsx - loadChatHistory
   const messages: Message[] = data.messages.map((msg: any) => ({
       role: msg.role,
       content: msg.content,
       timestamp: msg.created_at,
       sources: msg.metadata?.sources || [],
       ragParams: msg.metadata?.rag_params || null
   }));
   ```

**Impact:**
- ✅ Chat history teljes helyreállítása oldal frissítés után
- ✅ Forrás hivatkozások persistence
- ✅ RAG debug információk megmaradnak

**Dependencies:**
- PostgreSQL schema migration
- Backend API update
- Frontend load logic update

---



---

---

## ✅ **RECENTLY COMPLETED** (2026-01-02)

### P0.17 Cache Architecture Review & Control ✅
**Completed:** 2026-01-02  
**Status:** ✅ COMPLETE (Runtime API Architecture)

**Goal:**  
Comprehensive review and documentation of all caching layers in the system, with runtime control from single source of truth (system.ini).

**Architecture:** Frontend fetches DEV_MODE from backend at runtime (no build-time dependency).

**Implemented:**

1. **Backend DEV_MODE Flag (system.ini)**
   ```ini
   [development]
   DEV_MODE=false  # true = all caches disabled
   ```
   - Controls all 4 cache tiers
   - `cache_service.py`: DummyCache when DEV_MODE=true

2. **Backend API Endpoint**
   - `GET /api/config/dev-mode` → `{"dev_mode": false}`
   - `DevModeResponse` schema
   - Used by frontend for runtime configuration

3. **Frontend Runtime Fetch**
   - VITE_DEV_MODE **REMOVED** (no build-time dependency!)
   - `getDevMode()`: Fetch + cache from backend
   - `getDefaultHeaders()`: async, adds Cache-Control if dev_mode=true
   - All API calls: `headers: await getDefaultHeaders()`

4. **Cache Control Service**
   - `backend/services/cache_control.py`: Centralized control
   - `GET /admin/cache/stats`: Memory + DB cache statistics
   - `POST /admin/cache/clear`: Clear all caches
   - `POST /admin/cache/enable|disable`: Stub endpoints (explicit config preferred)

5. **Documentation**
   - `docs/CACHE_ARCHITECTURE.md` (833 lines): Complete cache layer documentation
   - `docs/CACHE_CONTROL_IMPLEMENTATION.md`: Runtime API architecture guide
   - `debug/test_cache_control_runtime.ps1`: Automated test script

**Cache Layers:**
| Tier | Type | Control | Location |
|------|------|---------|----------|
| 1 | Memory (SimpleCache) | system.ini DEV_MODE | backend |
| 2 | PostgreSQL DB | system.ini DEV_MODE | backend |
| 3 | Browser HTTP | Runtime API | frontend |
| 4 | LLM Prompt | system.ini (not impl) | OpenAI |

**Key Improvement:** 
- ✅ Single source of truth (system.ini)
- ✅ No frontend rebuild needed for cache changes
- ✅ Runtime adaptation (frontend auto-detects backend config)

**Test Results:**
- Cache MISS: 47ms → Cache HIT: 13ms (3.4x speedup)
- DEV_MODE=true: All caches disabled (verified)
- Frontend console: `🔧 Dev mode (from system.ini): false`

**Design Decision:**
- ❌ No frontend UI toggle (explicit config > runtime toggle for educational clarity)
- ❌ No true runtime enable/disable without restart (Singleton + thread-safety complexity not justified)

**Files Modified:**
- `backend/api/admin_endpoints.py`: GET /config/dev-mode
- `backend/api/schemas.py`: DevModeResponse
- `backend/services/cache_control.py`: CacheControl service
- `frontend/src/api.ts`: Runtime getDevMode() + async headers
- `docker-compose.yml`: VITE_DEV_MODE build arg removed
- `frontend/Dockerfile`: VITE_DEV_MODE ARG/ENV removed
- `.env.example`: VITE_DEV_MODE documentation removed

---

### P0.14 RAG Parameters Display in Message Bubbles ✅
**Completed:** 2026-01-02  
**Status:** ✅ DONE

**Goal:** Display RAG parameters (TOP_K, MIN_SCORE_THRESHOLD) in message bubbles when RAG was used.

**Implementation:**
1. **Backend - Send RAG params in response:**
   - `unified_chat_workflow.py` (line 1163-1166): Added `rag_params` to workflow result
   - `routes.py` (line 576): Added `rag_params` to RAGChatResponse
   - `schemas.py` (line 30-43): Created RAGParams model and added to RAGChatResponse

2. **Frontend - Display RAG params:**
   - `MessageBubble.tsx` (line 28-34): Display params when sources exist
   - Format: `(TOP_K=5, MIN_SCORE=0.7)`

3. **Condition:** RAG params shown only when `sources` array is not empty

**Files Modified:**
- `backend/services/unified_chat_workflow.py`
- `backend/api/routes.py`
- `backend/api/schemas.py`
- `frontend/src/components/MessageBubble.tsx` (already had display logic)

---

### P0.15 Routing Prompt Enhancement ✅
**Completed:** 2026-01-02  
**Status:** ✅ DONE

**Goal:** Fix routing decision to correctly identify document-specific queries as SEARCH (RAG) instead of CHAT.

**Problem:** 
Queries like "És az emberekről mit írnak a dokumentumokban? Kik szerepelnek benne név szerint?" were incorrectly routed to CHAT instead of SEARCH/RAG, causing hallucination issues.

**Implementation:**
Enhanced routing decision prompt in `unified_chat_workflow.py` (line 507-545):

**Hungarian prompt additions:**
```python
3. **SEARCH** - Ha DOKUMENTUMOKBAN lévő specifikus információt keres vagy dokumentumok 
   tartalmáról kérdez
   - Példák: "mit írnak a dokumentumokban?", "kik szerepelnek a doksiban?", 
     "milyen nevek vannak említve?"
   - Példák: "az emberekről mit írnak?", "az orkokról van infó?", 
     "ki az a Lady Miriel?"
   - HASZNÁLD akkor is, ha a kérdés dokumentumok tartalmára, szereplőkre, 
     nevekre, eseményekre vonatkozik!

PRIORITÁS: 
1. Személyes adatok → MINDIG CHAT, SOHA SEARCH!
2. Dokumentumok tartalma, szereplők, nevek, események → MINDIG SEARCH!
```

**English prompt additions:**
```python
3. **SEARCH** - If searching for SPECIFIC INFORMATION IN DOCUMENTS or asking about 
   document content
   - Examples: "what do the documents say?", "who is mentioned in the docs?", 
     "what names are mentioned?"
   - Examples: "what about humans?", "is there info about orcs?", 
     "who is Lady Miriel?"
   - USE this even if the question is about document content, characters, 
     names, events!

PRIORITY: 
1. Personal data → ALWAYS CHAT, NEVER SEARCH!
2. Document content, characters, names, events → ALWAYS SEARCH!
```

**Files Modified:**
- `backend/services/unified_chat_workflow.py` (line 500-560)

---

### P0.16 LLM Hallucination Case Study Documentation ✅
**Completed:** 2026-01-02  
**Status:** ✅ DONE

**Goal:** Document a real hallucination case for learning and debugging purposes.

**Case:** User asked "És az emberekről mit írnak a dokumentumokban? Kik szerepelnek benne név szerint?" 
and LLM provided specific names (Lady Miriel, Aric) that were NOT in the chat history, 
because routing decision was CHAT instead of RAG.

**Documentation Created:**
- `docs/LLM_HALLUCINATION_CASE_STUDY.md`
  - Full chat history from database
  - Backend log analysis
  - Code examination
  - Root cause analysis (routing error)
  - Lessons learned
  - Fix implementation details

**Files Created:**
- `ai_chat_edu_v02/docs/LLM_HALLUCINATION_CASE_STUDY.md`

---

## 📊 **SUMMARY**

| Phase | Status | Progress | Notes |
|-------|--------|----------|-------|
| **P0.1-P0.8** | ✅ COMPLETED | 100% | Core RAG pipeline operational |
| **P0.11** | ✅ COMPLETED | 100% | Chat History Integration via Unified Workflow |
| **P0.12** | ✅ COMPLETED | 100% | Unified Chat Workflow (LangGraph) - Agent Loop |
| **P0.14-P0.16** | ✅ COMPLETED | 100% | RAG params display, routing fix, hallucination docs |
| **P0.13** | 🚨 CRITICAL | 0% | Message metadata persistence (sources, rag_params) |
| **P0.9-P0.10** | ⏳ NEXT | 33% | UX & Performance improvements (P0.9.1 ✅) |
| **P1** | ⏳ TODO | 0% | Knowledge & Memory features |
| **P2** | ⏳ TODO | 0% | Admin & System features |

---

## ✅ **P0 – CORE RAG (COMPLETED)**

### P0.1 File Upload ✅
- [x] POST /api/workflows/process-document endpoint
- [x] File validation (PDF/TXT/MD, max 10MB)
- [x] Content extraction (PDF → text, TXT/MD → direct)
- [x] DB storage (documents table)
- [x] Response structure with summary
- [x] HTTP status codes (201, 400)
- [x] Frontend UI (file picker + upload button) ✅ **COMPLETED** (DocumentUpload.tsx modal + 📎 button)

**Implementation:** [`backend/api/workflow_endpoints.py`](../backend/api/workflow_endpoints.py), [`backend/services/document_processing_workflow.py`](../backend/services/document_processing_workflow.py)

---

### P0.2 Document Data Model ✅
- [x] `documents` table created
- [x] `document_chunks` table created
- [x] Foreign keys configured
- [x] Indexes on document_id, tenant_id

**Schema:** PostgreSQL tables operational

---

### P0.3 Chunking ✅
- [x] RecursiveCharacterTextSplitter integration
- [x] Chunk size: 500 tokens (~2000 chars)
- [x] Overlap: 50 tokens (~200 chars)
- [x] Offset/index calculation
- [x] PostgreSQL storage

**Implementation:** [`backend/services/chunking_service.py`](../backend/services/chunking_service.py)

---

### P0.4 Embedding Pipeline ✅
- [x] OpenAI text-embedding-3-large (3072 dim)
- [x] Batch processing (max 100 chunks/call)
- [x] Error handling
- [x] Timestamp tracking (embedded_at)

**Implementation:** [`backend/services/embedding_service.py`](../backend/services/embedding_service.py)

---

### P0.5 Qdrant Collection ✅
- [x] Collection: `document_chunks`
- [x] Vector size: 3072
- [x] Distance metric: Cosine
- [x] Payload schema: {tenant_id, document_id, chunk_id, visibility, content_preview}
- [x] Tenant filtering support

**Implementation:** [`backend/services/qdrant_service.py`](../backend/services/qdrant_service.py)

---

### P0.6 Retrieval Pipeline ✅
- [x] Query embedding generation
- [x] Qdrant similarity search with tenant filter
- [x] Top-K=5 (configurable)
- [x] Score threshold=0.7
- [x] Response with chunk metadata

**Implementation:** [`backend/services/rag_workflow.py`](../backend/services/rag_workflow.py) - `retrieve_chunks_node`

---

### P0.7 LangGraph RAG Workflow ✅
- [x] StateGraph definition (RAGState)
- [x] Nodes: validate_input, build_context, retrieve_chunks, check_results, generate_answer, fallback
- [x] Conditional edges (has_relevant_context routing)
- [x] Error handling per node
- [x] POST /api/chat/rag endpoint
- [x] Frontend integration

**Implementation:** [`backend/services/rag_workflow.py`](../backend/services/rag_workflow.py)

---

### P0.8 Intelligent RAG Routing ✅
- [x] `decide_if_rag_needed` node (LLM decision)
- [x] `generate_direct_answer` node (no RAG path)
- [x] Routing logic: conversational vs document queries
- [x] State field: `needs_rag`
- [x] Testing: "szia" → conversational, "mi van a dokumentumban?" → RAG
- ⚠️ **KNOWN ISSUE:** No chat history context in routing decision (see P0.11 for fix)

**Implementation:** Enhanced RAG workflow with routing

---

## 🚨 **P0.11 – CHAT HISTORY INTEGRATION (URGENT)**

**Priority:** **URGENT - BLOCKING P0.12**  
**Goal:** Fix RAG routing bug by injecting conversation context into decision node  
**Requested:** 2025-12-31  
**Dependencies:** None (can start immediately)

### **Problem Statement**

**Bug:** RAG routing decision (`_decide_rag_needed_node`) only sees current query, not conversation history.

**Example Failure:**
```
User: "van kutyád?" → LLM: "milyen fajta?"
User: "uszkár" → ❌ INCORRECTLY routed to RAG/SEARCH (LLM thought "uszkár" was document keyword)
```

**Expected:** "uszkár" should trigger CHAT (direct conversational response), not RAG retrieval.

**Root Cause:** RAG workflow state doesn't include chat history, so LLM cannot understand conversational context.

---

### **Solution Architecture**

**1. Extend RAGState Schema**
```python
# backend/services/rag_workflow.py
class RAGState(TypedDict):
    query: str
    tenant_id: int
    user_id: int
    chat_history: List[Dict[str, str]]  # NEW FIELD
    needs_rag: str
    chunks: List[Dict]
    # ... existing fields
```

**2. Fetch Chat History in build_context_node**
```python
# backend/services/rag_workflow.py - build_context_node
def build_context_node(state: RAGState) -> RAGState:
    # Fetch last N messages from PostgreSQL
    recent_messages = pg_service.get_chat_history(
        user_id=state["user_id"],
        tenant_id=state["tenant_id"],
        limit=10
    )
    
    # Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    state["chat_history"] = [
        {"role": msg["sender"], "content": msg["message"]}
        for msg in recent_messages
    ]
    return state
```

**3. Inject History into Routing Decision**
```python
# backend/services/rag_workflow.py - _decide_rag_needed_node
def _decide_rag_needed_node(state: RAGState) -> RAGState:
    # Build conversation context
    history_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in state.get("chat_history", [])
    ])
    
    # Enhanced prompt with context
    prompt = f"""CONVERSATION HISTORY:
{history_text}

CURRENT QUERY: {state['query']}

Should this query trigger RAG search? Consider conversation context."""
    
    # LLM decision with context
    response = llm.invoke(prompt)
    state["needs_rag"] = response.content  # "RAG", "CHAT", "LIST"
    return state
```

**4. Include History in Answer Generation**
```python
# backend/services/rag_workflow.py - generate_answer_node
def generate_answer_node(state: RAGState) -> RAGState:
    history_context = _format_history(state.get("chat_history", []))
    
    prompt = f"""CONVERSATION HISTORY:
{history_context}

DOCUMENTS:
{state['context_text']}

CURRENT QUERY: {state['query']}

Answer considering both conversation and documents."""
    # ... existing LLM call
```

---

### **Implementation Tasks**

- [ ] **STEP 1:** Modify RAGState TypedDict (add chat_history field)
- [ ] **STEP 2:** Update build_context_node to fetch chat history from PostgreSQL
- [ ] **STEP 3:** Modify _decide_rag_needed_node prompt to include conversation context
- [ ] **STEP 4:** Modify generate_answer_node to include conversation context
- [ ] **STEP 5:** Add _format_history() helper function
- [ ] **STEP 6:** Test multi-turn conversation: "van kutyád?" → "milyen fajta?" → "uszkár"

**Expected Result:** "uszkár" correctly routed to CHAT, not RAG

---

### **Database Integration**

**Existing Function (reuse):**
```python
# backend/database/pg_init.py - get_chat_history()
def get_chat_history(user_id: int, tenant_id: int, limit: int = 10):
    query = """
    SELECT sender, message, created_at
    FROM chat_messages
    WHERE user_id = %s AND tenant_id = %s
    ORDER BY created_at DESC
    LIMIT %s
    """
    result = execute_query(query, (user_id, tenant_id, limit))
    return list(reversed(result))  # Chronological order
```

**No new DB tables required** - reuse existing chat_messages table.

---

### **Testing Checklist**

- [ ] **Test 1:** Single-turn query still works ("mi van a dokumentumban?")
- [ ] **Test 2:** Multi-turn conversational query routed to CHAT ("uszkár" after dog question)
- [ ] **Test 3:** Multi-turn RAG query maintains history ("második dokumentum címe?")
- [ ] **Test 4:** Empty history (first message) doesn't break workflow
- [ ] **Test 5:** History limit respected (only last 10 messages fetched)

---

### **Files to Modify**

1. **backend/services/rag_workflow.py** (main changes)
   - RAGState TypedDict definition
   - build_context_node (fetch history)
   - _decide_rag_needed_node (inject history into prompt)
   - generate_answer_node (include history in answer generation)
   
2. **backend/database/pg_init.py** (verify existing)
   - get_chat_history() function (already exists, reuse)

---

### **Success Criteria**

- ✅ RAGState includes chat_history field
- ✅ Chat history fetched from PostgreSQL in build_context_node
- ✅ Routing decision considers conversation context
- ✅ "uszkár" example correctly routed to CHAT (not RAG)
- ✅ Multi-turn RAG queries still work correctly
- ✅ No performance degradation (<100ms overhead)

---

## 🚨 **P0.12 – UNIFIED CHAT WORKFLOW (URGENT)**

**Priority:** **HIGH - Depends on P0.11**  
**Goal:** Replace separate chat_service.py and rag_workflow.py with single LangGraph workflow  
**Requested:** 2025-12-31  
**Dependencies:** P0.11 completion (chat history integration)

### **Problem Statement**

**Current Architecture Issues:**
1. **Duplicate Code:** chat_service.py and rag_workflow.py both build system prompts, fetch context
2. **Hardcoded Routing:** `/chat` vs `/rag` endpoints require manual client-side logic
3. **Maintenance Burden:** Two separate workflows for similar tasks
4. **No Unified State:** Cannot share context between chat and RAG paths

**Current Endpoint Structure:**
```
POST /api/chat (→ chat_service.py)  # Direct LLM, no documents
POST /api/chat/rag (→ rag_workflow.py)  # LangGraph RAG workflow
```

---

### **Solution Architecture: Unified Chat Workflow**

**Single LangGraph Workflow with Dynamic Routing**

```
START
  ↓
validate_input_node
  ↓
build_context_node (fetch user/tenant prompts + chat history)
  ↓
decide_route_node (LLM decision: CHAT | LIST | RAG)
  ↓
  ├→ [CHAT] → generate_chat_response_node → END
  ├→ [LIST] → list_documents_node → END
  └→ [RAG] → retrieve_chunks_node → check_results_node
             ↓                         ↓
             [SUCCESS] → generate_answer_node → END
             [FAIL] → fallback_node → END
```

---

### **Workflow State Schema**

```python
# backend/services/unified_chat_workflow.py
class UnifiedChatState(TypedDict):
    # Input
    query: str
    tenant_id: int
    user_id: int
    
    # Context (from P0.11)
    chat_history: List[Dict[str, str]]
    system_prompt: str
    
    # Routing
    route_decision: str  # "CHAT" | "LIST" | "RAG"
    
    # RAG-specific
    chunks: List[Dict]
    context_text: str
    has_relevant_context: bool
    
    # Output
    answer: str
    sources: List[Dict]
    error: Optional[str]
```

---

### **Node Implementations**

**1. validate_input_node**
```python
def validate_input_node(state: UnifiedChatState) -> UnifiedChatState:
    if not state["query"].strip():
        state["error"] = "Empty query"
    return state
```

**2. build_context_node (REUSE FROM P0.11)**
```python
def build_context_node(state: UnifiedChatState) -> UnifiedChatState:
    # Fetch chat history (from P0.11)
    state["chat_history"] = pg_service.get_chat_history(...)
    
    # Fetch hierarchical prompt
    state["system_prompt"] = build_system_prompt(...)
    
    return state
```

**3. decide_route_node (LLM DECISION)**
```python
def decide_route_node(state: UnifiedChatState) -> UnifiedChatState:
    history_text = _format_history(state["chat_history"])
    
    prompt = f"""CONVERSATION HISTORY:
{history_text}

CURRENT QUERY: {state['query']}

Choose routing:
- CHAT: Conversational query (greeting, follow-up, opinion)
- LIST: User wants document list ("milyen dokumentumok vannak?")
- RAG: User needs document retrieval ("mi van a dokumentumban?")

RESPOND WITH ONLY: CHAT, LIST, or RAG"""
    
    response = llm.invoke(prompt)
    state["route_decision"] = response.content.strip().upper()
    return state
```

**4. generate_chat_response_node (MIGRATE FROM chat_service.py)**
```python
def generate_chat_response_node(state: UnifiedChatState) -> UnifiedChatState:
    history_text = _format_history(state["chat_history"])
    
    messages = [
        {"role": "system", "content": state["system_prompt"]},
        {"role": "user", "content": f"HISTORY:\n{history_text}\n\nQUERY: {state['query']}"}
    ]
    
    response = llm.invoke(messages)
    state["answer"] = response.content
    return state
```

**5. list_documents_node**
```python
def list_documents_node(state: UnifiedChatState) -> UnifiedChatState:
    docs = pg_service.list_documents(state["tenant_id"], state["user_id"])
    
    doc_list = "\n".join([f"- {doc['title']}" for doc in docs])
    state["answer"] = f"Available documents:\n{doc_list}"
    return state
```

**6. retrieve_chunks_node (REUSE FROM rag_workflow.py)**
```python
def retrieve_chunks_node(state: UnifiedChatState) -> UnifiedChatState:
    # Existing RAG retrieval logic
    state["chunks"] = qdrant_service.search_similar(...)
    return state
```

**7. check_results_node (REUSE)**
```python
def check_results_node(state: UnifiedChatState) -> UnifiedChatState:
    state["has_relevant_context"] = len(state["chunks"]) > 0
    return state
```

**8. generate_answer_node (REUSE, ADD HISTORY)**
```python
def generate_answer_node(state: UnifiedChatState) -> UnifiedChatState:
    history_text = _format_history(state["chat_history"])
    context_text = _format_chunks(state["chunks"])
    
    prompt = f"""HISTORY:
{history_text}

DOCUMENTS:
{context_text}

QUERY: {state['query']}

Answer using documents and conversation context."""
    
    state["answer"] = llm.invoke(prompt).content
    return state
```

**9. fallback_node (REUSE)**
```python
def fallback_node(state: UnifiedChatState) -> UnifiedChatState:
    state["answer"] = "No relevant documents found."
    return state
```

---

### **Conditional Routing Logic**

```python
def route_after_decision(state: UnifiedChatState) -> str:
    decision = state.get("route_decision", "CHAT").upper()
    
    if decision == "LIST":
        return "list"
    elif decision == "RAG":
        return "rag"
    else:  # CHAT (default fallback)
        return "chat"

def route_after_retrieval(state: UnifiedChatState) -> str:
    if state.get("has_relevant_context", False):
        return "generate"
    else:
        return "fallback"
```

---

### **LangGraph Workflow Definition**

```python
# backend/services/unified_chat_workflow.py
from langgraph.graph import StateGraph, END

workflow = StateGraph(UnifiedChatState)

# Add nodes
workflow.add_node("validate_input", validate_input_node)
workflow.add_node("build_context", build_context_node)
workflow.add_node("decide_route", decide_route_node)
workflow.add_node("generate_chat", generate_chat_response_node)
workflow.add_node("list_docs", list_documents_node)
workflow.add_node("retrieve", retrieve_chunks_node)
workflow.add_node("check_results", check_results_node)
workflow.add_node("generate_answer", generate_answer_node)
workflow.add_node("fallback", fallback_node)

# Add edges
workflow.set_entry_point("validate_input")
workflow.add_edge("validate_input", "build_context")
workflow.add_edge("build_context", "decide_route")

# Conditional routing
workflow.add_conditional_edges(
    "decide_route",
    route_after_decision,
    {
        "chat": "generate_chat",
        "list": "list_docs",
        "rag": "retrieve"
    }
)

# RAG path
workflow.add_edge("retrieve", "check_results")
workflow.add_conditional_edges(
    "check_results",
    route_after_retrieval,
    {
        "generate": "generate_answer",
        "fallback": "fallback"
    }
)

# End points
workflow.add_edge("generate_chat", END)
workflow.add_edge("list_docs", END)
workflow.add_edge("generate_answer", END)
workflow.add_edge("fallback", END)

app = workflow.compile()
```

---

### **API Endpoint Changes**

**Before (2 endpoints):**
```python
# backend/api/routes.py
POST /api/chat → chat_service.generate_response()
POST /api/chat/rag → rag_workflow.execute()
```

**After (1 unified endpoint):**
```python
# backend/api/routes.py
POST /api/chat → unified_chat_workflow.execute()

# Deprecate /api/chat/rag (mark as deprecated, remove in future)
```

**Frontend Change:**
```typescript
// frontend/src/services/api.ts
// BEFORE: Manual routing logic
const endpoint = needsRAG ? '/api/chat/rag' : '/api/chat';

// AFTER: Always use unified endpoint
const endpoint = '/api/chat';
```

---

### **Implementation Tasks**

- [ ] **STEP 1:** Create unified_chat_workflow.py file
- [ ] **STEP 2:** Define UnifiedChatState schema
- [ ] **STEP 3:** Implement decide_route_node (LLM routing decision)
- [ ] **STEP 4:** Migrate generate_chat_response_node from chat_service.py
- [ ] **STEP 5:** Implement list_documents_node
- [ ] **STEP 6:** Integrate retrieve/check/generate nodes from rag_workflow.py
- [ ] **STEP 7:** Build LangGraph workflow with conditional routing
- [ ] **STEP 8:** Update API endpoint (POST /api/chat → unified workflow)
- [ ] **STEP 9:** Mark chat_service.py as deprecated (add @deprecated comments)
- [ ] **STEP 10:** Update frontend to use single endpoint
- [ ] **STEP 11:** Test all paths: CHAT, LIST, RAG
- [ ] **STEP 12:** (Optional) Remove /api/chat/rag endpoint after validation

---

### **Testing Checklist**

- [ ] **Test 1 (CHAT):** "szia, hogy vagy?" → generate_chat_response_node
- [ ] **Test 2 (LIST):** "milyen dokumentumok vannak?" → list_documents_node
- [ ] **Test 3 (RAG):** "mi van az első dokumentumban?" → RAG path
- [ ] **Test 4 (Multi-turn CHAT):** "van kutyád?" → "milyen fajta?" → "uszkár" → CHAT (not RAG)
- [ ] **Test 5 (Multi-turn RAG):** "mi van a doc-ban?" → "és a második bekezdés?" → RAG with history
- [ ] **Test 6 (Fallback):** RAG query with no matching documents → fallback_node
- [ ] **Test 7 (Error):** Empty query → validation error
- [ ] **Test 8 (Performance):** All paths <3s response time

---

### **Files to Modify**

1. **backend/services/unified_chat_workflow.py** (NEW FILE)
   - UnifiedChatState definition
   - All 9 nodes
   - Conditional routing logic
   - LangGraph workflow definition

2. **backend/api/routes.py**
   - Update POST /api/chat endpoint to use unified workflow
   - Mark POST /api/chat/rag as deprecated

3. **backend/services/chat_service.py** (DEPRECATE)
   - Add @deprecated docstring
   - Mark for removal in next phase (P0.13 cleanup)
   - No longer used after unified workflow deployment

4. **backend/services/rag_workflow.py** (DEPRECATE)
   - Mark as deprecated
   - Migrate code to unified_chat_workflow.py

5. **frontend/src/services/api.ts**
   - Remove manual routing logic
   - Always call POST /api/chat

---

### **Success Criteria**

- ✅ Single POST /api/chat endpoint handles all query types
- ✅ LLM-based dynamic routing (no hardcoded keywords)
- ✅ All 3 paths work: CHAT, LIST, RAG
- ✅ Chat history integrated (from P0.11)
- ✅ No duplicate code between chat/RAG paths
- ✅ Frontend simplified (single API call)
- ✅ Performance: <3s for all paths
- ✅ Test coverage: all 8 test cases pass

---

## ⏳ **P0.9 – UX IMPROVEMENTS**

**Priority:** MEDIUM (after P0.11-P0.12)  
**Goal:** Improve user experience

### P0.9.1 Document Title Metadata ✅
**Status:** ✅ COMPLETED  
**Problem:** Only "Doc#1" shown as source (not informative)

**Solution Implemented:**
- ✅ `documents.title` column exists (VARCHAR(500), nullable)
- ✅ Backend schema: `DocumentSource` includes `title` field
- ✅ Frontend types: `sources?: {id: number, title: string}[]`
- ✅ MessageBubble displays document titles instead of "Doc#X"
- ✅ Test: uploaded document title appears in chat

**Files Modified:**
- `backend/api/schemas.py` (DocumentSource with title)
- `frontend/src/types.ts` (Message type with title)
- `frontend/src/components/MessageBubble.tsx` (displays source.title)

---

### P0.9.2 Enhanced Source Attribution
**Goal:** Show chapter/page numbers in source references

**Tasks:**
- [ ] PDF chunking: implement page_number tracking
- [ ] MD chunking: detect headings (# titles)
- [ ] Qdrant payload: add `chunk_metadata` object (page_number, chapter, section)
- [ ] Frontend: display detailed source info
- [ ] Test: PDF page number and chapter visible in chat

**Implementation notes:**
- Use PyPDF2 for PDF page tracking
- Markdown heading detection via regex

---

### P0.9.3 Search Performance Optimization
**Problem:** Slow retrieval on large document sets

**Tasks:**
- [ ] Optimize Qdrant HNSW config (ef_construct: 100 → 200)
- [ ] Reduce Top-K: 5 → 3 (fewer chunks)
- [ ] Add retrieval time logging (per node)
- [ ] Test: >1000 chunk search <2s
- [ ] (Optional) Redis cache for frequent queries

**system.ini changes:**
```ini
TOP_K_DOCUMENTS=3
```

---

## ⏳ **P0.10 – PERFORMANCE OPTIMIZATION**

**Priority:** MEDIUM (after P0.11-P0.12)  
**Goal:** System performance improvements

### P0.10.1 Document Summary Generation
**Goal:** Auto-generate summaries for long documents

**Tasks:**
- [ ] Add `documents.summary` column (TEXT)
- [ ] Implement auto-summary on upload (if content >5000 chars)
- [ ] Store summary chunk in Qdrant (chunk_type="summary")
- [ ] Retrieval: prioritize summary chunks for general queries
- [ ] Frontend: display summary in document list
- [ ] Test: long document → summary generated

**LLM Prompt:**
```
"Summarize the main topics of this document in 3-5 sentences."
```

---

### P0.10.2 Keyword Detection Improvements ❌ **OBSOLETE**
**Status:** ❌ **DEPRECATED - Replaced by P0.12 LLM-based routing**

**Reason:** P0.12 Unified Chat Workflow eliminates hardcoded keyword routing in favor of dynamic LLM-based decision making. This task is no longer relevant.

**Original Goal:** Fine-tune P0.8 keyword list

**Current keywords (Hungarian):**
```python
["keress", "találd", "van-e", "dokumentum", "elfek", "fantasy", "örök", "kapcsolat"]
```

~~**Tasks:**~~
- ~~[ ] Expand keyword list (min. 20 keywords)~~
- ~~[ ] Add false positive/negative logging~~
- ~~[ ] (Optional) Implement stemming/lemmatization~~
- ~~[ ] User feedback mechanism: "This shouldn't trigger RAG" button~~
- ~~[ ] Test: false positive rate <5%~~

---

### P0.10.3 API Branding Fix ✅ COMPLETED
**Issue:** Root endpoint returns "AI Chat Phase 1 API" in Phase 2 project

**Priority:** LOW (non-critical, cosmetic)  
**Source:** Version branding verification (2025-12-31)  
**Status:** ✅ **COMPLETED** (2026-01-01)

**Solution Implemented:**
- ✅ Created `backend/config/config_service.py` for system.ini reading
- ✅ Added `APP_VERSION=0.2.0` to `backend/config/system.ini`
- ✅ Updated `backend/main.py`: Dynamic version loading from system.ini
  - FastAPI title: `AI Chat {APP_VERSION}`
  - Root endpoint: `{"message": "AI Chat {APP_VERSION} API", "version": APP_VERSION}`
  - New endpoint: `GET /api/version` returns `{"version": "0.2.0", "name": "AI Chat 0.2.0"}`
- ✅ Updated `frontend/src/App.tsx`: Header displays `AI Chat {version}` (fetched from API)
- ✅ All hardcoded "Phase 1", "Phase 1.5", "Phase 2" references replaced with dynamic version

**Testing:**
```bash
$ curl http://localhost:18000/
{"status":"ok","message":"AI Chat 0.2.0 API","version":"0.2.0"}

$ curl http://localhost:18000/api/version
{"version":"0.2.0","name":"AI Chat 0.2.0"}
```

**Files Modified:**
- `backend/config/system.ini` (new: APP_VERSION)
- `backend/config/config_service.py` (NEW FILE - config reader)
- `backend/main.py` (dynamic version loading)
- `frontend/src/App.tsx` (API-based version display)

---

## ⏳ **P1 – KNOWLEDGE & MEMORY**

**Priority:** MEDIUM  
**Dependencies:** P0.9 completion recommended

### P1.1 Long-term Chat Memory

**Database:**
- [x] `chat_sessions` table exists ✅
- [x] `long_term_memories` table exists ✅ **VERIFIED** (2026-01-01)
  - Columns: id, tenant_id, user_id, source_session_id, content, qdrant_point_id, embedded_at, created_at
  - Foreign keys: tenant_id → tenants, user_id → users, source_session_id → chat_sessions
  - Ready for implementation

**Tasks:**
- [ ] Session close endpoint: `POST /api/sessions/{id}/close`
- [ ] LLM summary generation (max 200 tokens)
- [ ] Store summary in `long_term_memories` table
- [ ] Generate embedding → Qdrant `longterm_chat_memory` collection
- [ ] Update `chat_sessions.processed_for_ltm` flag
- [ ] Retrieval: load previous session summaries on new session start
- [ ] LangGraph node: `retrieve_chat_history`
- [ ] system.ini config: `ENABLE_LONGTERM_CHAT_RETRIEVAL=true`

**Retrieval logic:**
- Query: "What did we discuss last time?"
- Top-K previous session summaries
- Context injection: "Based on your previous conversations..."

---

### P1.2 Product Knowledge

**Database:**
- [ ] Create `products` table:
  - id (PK)
  - tenant_id (FK → tenants.id)
  - name (VARCHAR)
  - description (TEXT)
  - specs (JSONB)
  - price (DECIMAL)
  - qdrant_point_id (UUID)
  - embedded_at (TIMESTAMP)
  - created_at (TIMESTAMP)

**Tasks:**
- [ ] Implement text representation: "[name] - [description] - Specs: [specs]"
- [ ] Embedding on insert/update
- [ ] Qdrant collection: `product_knowledge` (3072 dim, cosine)
- [ ] Payload: {tenant_id, product_id, name, price}
- [ ] Retrieval service: product-specific queries
- [ ] Test: "What products cost less than 10000 Ft?" → relevant products

---

### P1.3 Multi-source RAG

**Goal:** Query both documents and products simultaneously

**Tasks:**
- [ ] Keyword-based routing: "product", "price" → product pipeline
- [ ] Parallel search: both collections queried at once
- [ ] Result merging: sort by similarity_score
- [ ] Final Top-K selection (max 5)
- [ ] LangGraph node: `route_and_retrieve` (conditional branching)
- [ ] Source attribution: response indicates document/product/mixed
- [ ] Test: "product documentation" → results from both sources

**Routing keywords:**
- Product: "termék", "product", "ár", "price", "spec"
- Document: "dokumentum", "document", "útmutató", "guide", "hogyan", "how to"
- Mixed: everything else

---

## ⏳ **P2 – ADMIN & SYSTEM**

**Priority:** LOW  
**Dependencies:** P1 completion

### P2.1 Admin Interface (Profile & Tenant Editing)

**User Profile Editing (all users):**

**API:**
- [ ] `GET /api/users/{user_id}` → user data
- [ ] `PATCH /api/users/{user_id}` → update firstname, lastname, nickname, email, default_lang, system_prompt

**Frontend:**
- [ ] Profile form: firstname, lastname, nickname, email, default_lang dropdown, system_prompt textarea
- [ ] Form validation: email regex, required fields
- [ ] Success/error messages
- [ ] Test: user updates profile → DB changes persist

**Read-only fields:**
- user_id
- role
- is_active (unless tenant admin)

---

**Tenant Admin (admin-only):**

**API:**
- [ ] `GET /api/tenants/{tenant_id}` → tenant data
- [ ] `PATCH /api/tenants/{tenant_id}` → update key, name, system_prompt, is_active
- [ ] Authorization check: users.role == 'admin' OR 'tenant_admin'
- [ ] 403 Forbidden if not admin

**Frontend:**
- [ ] "Tenant Admin" tab (visible only to admins)
- [ ] Form: key, name, system_prompt, is_active checkbox
- [ ] Test: admin modifies tenant → success, non-admin → 403

**UI Layout:**
- Tab 1: "Profile" (all users)
- Tab 2: "Tenant Admin" (admins only)
- Tab 3: "README" (all users)

---

### P2.2 system.ini Configuration

**Tasks:**
- [ ] Create `backend/config/system.ini` file
- [ ] Config service: `get_system_prompt()` function
- [ ] Prompt hierarchy enforcement: system.ini > tenant > user > runtime
- [ ] Frontend: NO editing capability (read-only reference)
- [ ] Documentation: manual edit + restart required

**system.ini structure:**
```ini
[application]
SYSTEM_PROMPT = "You are a helpful AI assistant..."

[rag]
CHUNKING_STRATEGY = recursive
CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50
...
```

---

### P2.3 README.md Frontend Display

**Tasks:**
- [ ] Create `backend/docs/README.md` (or root README.md)
- [ ] Content: RAG pipeline explanation, Postgres/Qdrant roles, collection strategy
- [ ] API endpoint: `GET /api/docs/readme`
- [ ] Frontend: "README" tab with markdown rendering (react-markdown or marked.js)
- [ ] Read-only view, scroll support, syntax highlighting
- [ ] Test: README tab displays formatted markdown

**README content sections:**
1. System overview
2. RAG pipeline diagram
3. PostgreSQL schema
4. Qdrant collections
5. LangGraph workflows
6. Phase 2.0 scope & limitations

---

## 🚧 **TEMP - Ad-hoc Tasks**

**Purpose:** Temporary holding area for user-requested modifications that don't fit into existing phases.

### TEMP.1 Frontend Language Consistency ✅ COMPLETED
**Requested:** 2025-12-28  
**Status:** ✅ DONE

**Tasks:**
- [x] Convert all Hungarian UI text to English
- [x] Update DocumentUpload.tsx (all labels)
- [x] Update DebugModal.tsx (section headers, labels)
- [x] Update HowTo.tsx (header, loading messages)
- [x] Full frontend rebuild (no-cache)

**Files modified:**
- `frontend/src/components/DocumentUpload.tsx`
- `frontend/src/components/DebugModal.tsx`
- `frontend/src/components/HowTo.tsx`

**Result:** All UI now in English

---

### TEMP.2 Debug File Organization ✅ COMPLETED
**Requested:** 2025-12-28  
**Status:** ✅ DONE

**Tasks:**
- [x] Move all `test_*.py` files to `backend/debug/`
- [x] Move all `check_*.py` files to `backend/debug/`
- [x] Create `backend/debug/README.md` documentation

**Files moved:**
- test_qdrant_connection.py
- test_documents.py
- check_user.py
- check_qdrant_data.py
- check_document_chunks_encoding.py
- check_doc.py
- check_doc_7.py
- check_db_structure.py

**Rationale:** AGENT_CONSTITUTION Section 6.4 compliance

---

### TEMP.3 Documentation Restructuring ✅ COMPLETED
**Requested:** 2025-12-28  
**Status:** ✅ DONE (this file)

**Tasks:**
- [x] Create TODO_PHASE2.md with all task checklists
- [x] Mark completed P0 tasks
- [x] Add TEMP section for ad-hoc requests
- [ ] Clean INIT_PROMPT_2.md (remove TODO sections) ⏳ NEXT

---

### TEMP.4 OpenAI Prompt Caching (GPT-4o) ⏳ TODO
**Requested:** 2025-12-30  
**Priority:** HIGH (cost optimization - 80-90% token cost reduction)  
**Status:** ⏳ PENDING

**Problem:**  
Current system rebuilds full system prompt (~450 tokens) on every request:
- **Expensive:** 450 tokens input for even simple messages like "hello"
- **Slow:** More tokens = longer processing time
- **Redundant:** 95% of prompt content is identical across requests

**Solution:** 3-Tier Prompt Caching System
- **Tier 1:** In-memory cache (Python dict) - 99% hit rate, <1ms latency
- **Tier 2:** PostgreSQL cache (user_prompt_cache table) - 1% hit rate, ~10ms latency
- **Tier 3:** LLM generation - 0.01% hit rate, ~2000ms latency

**Expected Benefits:**
- 80-90% cost reduction for multi-turn conversations
- Cache HIT: 45 tokens input (cached) vs MISS: 450 tokens input (full)
- OpenAI prompt caching: 5-10 min TTL (ephemeral cache)
- LLM-optimized prefix: 250 tokens (compressed from 450)

**Detailed Specification:** See [../04_implementations/TEMP.4_PROMPT_CACHING_IMPLEMENTATION.md](../04_implementations/TEMP.4_PROMPT_CACHING_IMPLEMENTATION.md)

**Prerequisites:**
- GPT-4o model (`gpt-4o` or `gpt-4o-mini`)
- OpenAI Python SDK >= 1.0.0 (prompt caching support)
- PostgreSQL user_prompt_cache table

**Implementation Summary:**
- [ ] Create user_prompt_cache table (migration)
- [ ] Implement PromptCacheService class (3-tier cache)
- [ ] Integrate into RAG workflow (Node 2: build_context)
- [ ] Add cache_control parameter to all LLM calls
- [ ] Implement cache invalidation triggers (tenant/user updates)
- [ ] Add debug endpoints for cache stats
- [ ] Test cache effectiveness (hit rate >90%)

**Success Criteria:**
- ✅ Cache hit rate >90% after warm-up
- ✅ Average response time <100ms for cache hits
- ✅ Cost reduction 80-90% for multi-turn sessions
- ✅ Zero cross-tenant cache leaks

---

### TEMP.5 Chat Message Telemetry & Analytics ⏳ TODO
**Requested:** 2025-12-30  
**Priority:** MEDIUM-HIGH (production monitoring)  
**Status:** ⏳ PENDING

**Context:**  
Production-ready AI systems require comprehensive monitoring of costs, performance, and cache effectiveness. Currently, we lack visibility into:
- **Cost tracking:** Per-user, per-tenant token usage and estimated costs
- **Performance monitoring:** Response times, slow queries, bottlenecks
- **Cache effectiveness:** OpenAI prompt cache hit/miss rates, cost savings
- **RAG metrics:** Number of chunks used, retrieval performance
- **User behavior:** RAG vs direct chat usage patterns

**Solution:** Chat Message Telemetry System
- Comprehensive telemetry capture for every chat message
- Database schema extension with 12 new telemetry fields
- Analytics queries for cost optimization and performance insights
- RESTful API endpoints for dashboard integration
- Expected cost reduction visibility: 80-90% from caching

**Detailed Specification:** See [../04_implementations/TEMP.5_CHAT_MESSAGE_TELEMETRY.md](../04_implementations/TEMP.5_CHAT_MESSAGE_TELEMETRY.md)

**Key Features:**
- ✅ Token counting (user message, prompt prefix, assistant response)
- ✅ OpenAI cache metrics (hit/miss, cached tokens)
- ✅ Response time tracking (milliseconds)
- ✅ RAG metrics (chunks used, document sources)
- ✅ Cost estimation (GPT-4o pricing: $2.50/$1.25 input, $10 output per 1M tokens)
- ✅ Workflow path tracking (RAG/CHAT/LIST)
- ✅ LLM model versioning

**Implementation Tasks:**
- [ ] Run database migration (add 12 telemetry columns)
- [ ] Update `insert_chat_message_with_telemetry()` in pg_init.py
- [ ] Modify RAG workflow to capture telemetry
- [ ] Implement `_extract_telemetry()` helper method
- [ ] Create analytics API endpoints (cost-summary, user-costs)
- [ ] Test with sample data
- [ ] (Optional) Deploy monitoring dashboard

**Expected Benefits:**
- **Cost Transparency:** Know exactly which users/tenants consume most tokens
- **Performance Monitoring:** Identify slow queries (>5s) and optimize
- **Cache ROI:** Measure actual cache savings (target: 80-90% cost reduction)
- **Data-Driven Optimization:** Make informed decisions on model selection, chunk size, Top-K

**Analytics Queries:**
- Cost per user (last 30 days)
- Cache hit rate by user
- RAG vs Chat performance comparison
- Monthly cost savings from caching
- Slowest queries (response time >5s)

**Success Criteria:**
- ✅ All chat messages have telemetry data
- ✅ Analytics API responds in <500ms
- ✅ Cost estimates within ±5% of actual OpenAI billing
- ✅ Cache hit rate tracking matches OpenAI dashboard
- ✅ Zero performance degradation from telemetry capture

---

## � **EXPERIMENTAL FEATURES**

### EXP.1 RAG Parameter Tuning Interface
**Requested:** 2026-01-02  
**Priority:** LOW (developer tool)  
**Status:** ⏳ PLANNED (documentation only)

**Goal:** 
Real-time RAG parameter tuning via frontend UI for development/debugging purposes.

**Problem Statement:**
Currently, RAG parameters (threshold, top_k) are hardcoded in `system.ini` and require restart. During development and fine-tuning, developers need to experiment with different parameter values to find optimal settings for specific document types and queries.

**Proposed Solution: API-Level Override**

#### 1. Backend Changes

**API Request Model Extension:**
```python
# backend/api/routes.py or models.py
class RAGChatRequest(BaseModel):
    user_id: int
    tenant_id: int
    message: str
    session_id: Optional[str]
    
    # 🆕 Debug/tuning parameters (optional, dev-only)
    rag_override: Optional[Dict[str, Any]] = None
    # Example: {"min_score_threshold": 0.3, "top_k": 10}
```

**RAGWorkflow.execute() Parameter:**
```python
# backend/services/rag_workflow.py
def execute(
    self, 
    query: str, 
    user_context: Dict[str, Any],
    config_override: Optional[Dict[str, Any]] = None  # 🆕
) -> Dict[str, Any]:
    
    # Default values from system.ini
    threshold = self.config.get_min_score_threshold()
    top_k = self.config.get_top_k_documents()
    
    # Override only in development mode
    if config_override and os.getenv("ENV") == "development":
        threshold = config_override.get("min_score_threshold", threshold)
        top_k = config_override.get("top_k", top_k)
        logger.warning(f"🔧 Config override: threshold={threshold}, top_k={top_k}")
    
    # Use overridden values in workflow...
```

**Enhanced Response (debug info):**
```python
# Return detailed metrics
return {
    "answer": final_answer,
    "sources": [1, 3, 7],
    
    # 🆕 Debug metadata (dev-only)
    "debug": {
        "used_threshold": threshold,
        "used_top_k": top_k,
        "total_chunks_searched": 47,
        "chunks_above_threshold": 12,
        "chunks_returned": 5,
        "chunk_scores": [
            {"chunk_id": 15, "score": 0.85, "document_id": 1},
            {"chunk_id": 23, "score": 0.72, "document_id": 3},
            # ...
        ]
    }
}
```

#### 2. Frontend Changes

**New Component: RAGTuningPanel**
```typescript
// frontend/src/components/RAGTuningPanel.tsx
function RAGTuningPanel() {
  const [query, setQuery] = useState("fantasy books");
  const [threshold, setThreshold] = useState(0.7);
  const [topK, setTopK] = useState(5);
  const [results, setResults] = useState(null);

  const testQuery = async () => {
    const response = await fetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        user_id: currentUser.id,
        tenant_id: currentUser.tenant_id,
        message: query,
        rag_override: {  // 🆕
          min_score_threshold: threshold,
          top_k: topK
        }
      })
    });
    const data = await response.json();
    setResults(data);
  };

  return (
    <div className="rag-tuning-panel">
      <h3>🔧 RAG Parameter Tuning</h3>
      
      <input type="text" value={query} onChange={...} />
      
      {/* Threshold slider */}
      <label>Threshold: {threshold}</label>
      <input type="range" min="0" max="1" step="0.1" 
             value={threshold} onChange={...} />
      
      {/* Top K slider */}
      <label>Top K: {topK}</label>
      <input type="range" min="1" max="20" step="1" 
             value={topK} onChange={...} />
      
      <button onClick={testQuery}>Run Test</button>
      
      {/* Results display with chunk scores */}
      {results && (
        <div>
          <p>Found {results.sources.length} documents</p>
          <p>Threshold: {results.debug.used_threshold}</p>
          {results.debug.chunk_scores.map(chunk => (
            <div key={chunk.chunk_id}>
              Score: {chunk.score} | Chunk: {chunk.chunk_id}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

**Optional: Auto-test Mode**
```typescript
// Automatically re-test when slider changes (debounced)
useEffect(() => {
  const timer = setTimeout(() => {
    testQuery(); // Auto-run after 500ms
  }, 500);
  return () => clearTimeout(timer);
}, [threshold, topK]);
```

#### 3. Security & Safety

**Safeguards:**
- ✅ Only works when `ENV=development` (disabled in production)
- ✅ No persistence: overrides are per-request only
- ✅ Logged as warnings for audit trail
- ✅ Original system.ini values remain unchanged
- ✅ Frontend UI only visible in debug panel

**ENV Check:**
```python
# backend/config/settings.py or routes.py
ALLOW_CONFIG_OVERRIDE = os.getenv("ENV", "production") == "development"

if request.rag_override and not ALLOW_CONFIG_OVERRIDE:
    raise HTTPException(403, "Config overrides disabled in production")
```

#### 4. Use Cases

**A. Find Optimal Threshold:**
```
Test query: "Tell me about fantasy books"
- threshold=0.9 → 0 results (too strict)
- threshold=0.7 → 2 results (good balance)
- threshold=0.5 → 5 results (more context)
- threshold=0.3 → 12 results (too noisy)

Decision: threshold=0.7 is optimal for this document set
```

**B. Compare Top K Values:**
```
Same query with threshold=0.7:
- top_k=3  → concise answer, focused sources
- top_k=5  → balanced (current default)
- top_k=10 → comprehensive, but may include noise
```

**C. A/B Testing Different Queries:**
```
Query A: "What are the main characters?"
Query B: "Who are the protagonists?"

Compare results with same threshold to identify 
which phrasing works better with current embeddings.
```

#### 5. Benefits

✅ **No restart required** for parameter experiments  
✅ **Real-time feedback** on parameter impact  
✅ **Visual comparison** of different settings  
✅ **Production safety** (dev-only feature)  
✅ **Educational value** for understanding RAG behavior  

#### 6. Implementation Checklist

**Backend:**
- [ ] Add `rag_override` field to RAGChatRequest model
- [ ] Extend `RAGWorkflow.execute()` with `config_override` parameter
- [ ] Add ENV check for production safety
- [ ] Implement override logic in relevant nodes (`retrieve_chunks`, etc.)
- [ ] Enhance response with debug metadata (chunk scores, counts)
- [ ] Add warning logs when overrides are active

**Frontend:**
- [ ] Create `RAGTuningPanel.tsx` component
- [ ] Add threshold slider (0.0 - 1.0, step 0.1)
- [ ] Add top_k slider (1 - 20, step 1)
- [ ] Implement test query button
- [ ] Display results with detailed chunk metrics
- [ ] Optional: implement auto-test debounced mode
- [ ] Integrate into Debug Modal or separate tab

**Testing:**
- [ ] Test with ENV=development (overrides work)
- [ ] Test with ENV=production (overrides blocked)
- [ ] Verify threshold changes affect retrieved chunks
- [ ] Verify top_k changes affect result count
- [ ] Verify original system.ini unchanged
- [ ] Test edge cases (threshold=0, top_k=100)

**Documentation:**
- [x] Document architecture decision (this TODO entry)
- [ ] Add usage instructions to README
- [ ] Add screenshot/video demo
- [ ] Document why this is dev-only feature

#### 7. Future Enhancements

**Phase 1:** Basic threshold + top_k tuning (this feature)  
**Phase 2:** Add more parameters:
- chunk_size_tokens
- chunk_overlap_tokens
- embedding_model selection
- temperature (for LLM)

**Phase 3:** Parameter presets:
```typescript
const presets = {
  "strict": { threshold: 0.9, top_k: 3 },
  "balanced": { threshold: 0.7, top_k: 5 },
  "comprehensive": { threshold: 0.3, top_k: 10 }
};
```

**Phase 4:** A/B comparison view:
- Split screen: same query, two different parameter sets
- Side-by-side result comparison

**Phase 5:** Parameter recommendation:
- ML-based suggestion: "Based on your document set, try threshold=0.65"

---

**Dependencies:**
- None (can be implemented independently)

**Estimated Effort:**
- Backend: 2-3 hours
- Frontend: 3-4 hours
- Testing: 1-2 hours
- Total: ~8 hours

**Priority Justification:**
- LOW: Not required for production functionality
- EDUCATIONAL: Demonstrates RAG tuning workflow
- PRACTICAL: Speeds up development/debugging

---

## �📝 **NOTES**

### Development Workflow (AGENT_CONSTITUTION)
1. **PLAN** → Present options to user
2. **PERMISSION** → Wait for explicit approval
3. **CODE** → Implement approved plan
4. **VERIFY** → Build + Test + Report

### TODO Management Rules
- ✅ Completed tasks marked immediately
- ⏳ In-progress tasks updated in real-time
- ❌ Blocked tasks documented with reason
- TEMP section for unclassified user requests

### File Locations
- Backend: `ai_chat_edu_v02/backend/`
- Frontend: `ai_chat_edu_v02/frontend/src/`
- Docs: `ai_chat_edu_v02/docs/`
- Debug: `ai_chat_edu_v02/backend/debug/`
- Production: `ai_chat_prod_v02/` (copy verified changes from edu)

---

**END OF TODO_PHASE2.md**
