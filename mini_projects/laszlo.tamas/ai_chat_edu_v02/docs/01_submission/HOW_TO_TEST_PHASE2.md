# AI Chat Phase 2 - Testing Guide for Instructors

**Submission Date:** 2026-01-05  
**Phase:** RAG & Knowledge Base Implementation

---

## 🎯 What Was Built (Phase 2 Objectives)

This phase implements a complete **Retrieval-Augmented Generation (RAG)** system with:
- ✅ Document upload (PDF, TXT, Markdown)
- ✅ Intelligent text processing and chunking
- ✅ Vector embeddings (OpenAI 3072-dim)
- ✅ Qdrant vector database integration
- ✅ Semantic search and retrieval
- ✅ LangGraph workflow (8+ nodes)
- ✅ Intelligent routing (conversational vs document queries)

---

## 🚀 Quick Start (5 Minutes)

### 1. Prerequisites
- Docker & Docker Compose installed
- OpenAI API key
- Qdrant (Docker local)

### 2. Environment Setup
Create `.env` file in `ai_chat_phase2/` root:
```dotenv
OPENAI_API_KEY=your_openai_key_here
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_key
POSTGRES_DB=ai_chat_db
POSTGRES_USER=app_user
POSTGRES_PASSWORD=your_secure_password
```

### 3. Start Application
```bash
cd ai_chat_phase2
docker-compose up -d
```

### 4. Access Points
- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### 5. Verify Startup
Check backend logs:
```bash
docker logs ai_chat_phase2-backend-1 --tail 30
```

Expected output:
```
✅ PostgreSQL connection established
✅ Qdrant connection established  
✅ RAG workflow initialized (8 nodes)
✅ Application startup complete
```

---

## 🧪 Test Scenarios

### Test 1: Simple Chat (No RAG)
**Purpose:** Verify LLM responds without triggering RAG

**Steps:**
1. Select user: **Alice Jones (ACME Corp)**
2. Send message: `Hello, how are you?`

**Expected Result:**
- ✅ Response within 2-3 seconds
- ✅ Natural greeting response
- ✅ No document retrieval (check backend logs: "direct_answer path")

---

### Test 2: Document Upload
**Purpose:** Verify document processing pipeline

**Steps:**
1. Click **"Upload Document"** button
2. Select test file: `test_files/sample.pdf`
3. Submit upload

**Expected Result:**
- ✅ Success message: "Document processed: sample.pdf"
- ✅ Backend logs show:
  ```
  [WORKFLOW] Processing document: sample.pdf
  [CHUNKING] Created 15 chunks
  [EMBEDDING] Embedded 15 chunks
  [QDRANT] Uploaded 15 vectors
  ```
- ✅ Database: Check `documents` table for new entry
- ✅ Qdrant: Check `document_chunks` collection

**Verification Query:**
```sql
-- PostgreSQL
SELECT * FROM documents WHERE title = 'sample.pdf';
SELECT COUNT(*) FROM document_chunks WHERE document_id = 1;
```

---

### Test 3: RAG Query (Document Search)
**Purpose:** Verify semantic search and retrieval

**Test file:** Upload `test_files/fantasy_story.txt` (contains: elves, dwarves, dragons)

**Steps:**
1. Wait for upload to complete
2. Send message: `What do the documents say about elves?`

**Expected Result:**
- ✅ Response includes information from fantasy_story.txt
- ✅ Source attribution: `[Source: Doc#1]` (or document title if P0.9.1 implemented)
- ✅ Backend logs show:
  ```
  [ROUTING] Decision: SEARCH (needs RAG)
  [RETRIEVAL] Retrieved 5 chunks (similarity > 0.7)
  [GENERATE] Answer with context
  ```

**Negative Test:**
- Message: `Tell me about space exploration`
- Expected: "I don't have relevant documents" (if fantasy_story.txt doesn't contain space content)

---

### Test 4: Intelligent Routing
**Purpose:** Verify LLM correctly routes conversational vs document queries

| Message | Expected Route | Reason |
|---------|---------------|--------|
| `Hi there!` | CHAT (no RAG) | Simple greeting |
| `How's the weather?` | CHAT (no RAG) | Conversational |
| `Summarize the uploaded document` | RAG (SEARCH) | Document query |
| `List all documents` | LIST | List request |
| `What does document 3 say about dragons?` | RAG (SEARCH) | Specific document query |

**Verification:** Check backend logs for routing decisions:
```
[NODE 3: decide_if_rag_needed] Decision: CHAT / SEARCH / LIST
```

---

### Test 5: Multi-Tenant Isolation
**Purpose:** Verify tenant data isolation

**Steps:**
1. Upload document as **Alice (ACME Corp, tenant_id=1)**
2. Send query: `What documents do I have?`
3. Switch user to **Bob (TechStart Inc, tenant_id=2)**
4. Send same query: `What documents do I have?`

**Expected Result:**
- ✅ Alice sees her uploaded document
- ✅ Bob does NOT see Alice's document (tenant isolation working)
- ✅ Each user only retrieves from their tenant's documents

---

### Test 6: Hierarchical Prompts
**Purpose:** Verify 3-tier prompt system (Application → Tenant → User)

**Setup:**
```sql
-- Set tenant-specific policy
UPDATE tenants 
SET system_prompt = 'Always respond in a formal, professional tone' 
WHERE key = 'acme';

-- Set user-specific preference
UPDATE users 
SET system_prompt = 'Include technical details and code examples when relevant' 
WHERE nickname = 'alice_j';
```

**Steps:**
1. Select Alice (ACME Corp)
2. Send: `Explain how vector embeddings work`

**Expected Result:**
- ✅ Formal tone (tenant policy)
- ✅ Includes technical details (user preference)
- ✅ Backend logs show prompt assembly:
  ```
  [CONTEXT] Building hierarchical prompt:
  - Application: <global instructions>
  - Tenant: Always respond formally...
  - User: Include technical details...
  ```

---

## 🐛 Debug Panel

**Access:** Click **"Debug Panel"** button (bottom-left)

**Features:**
- **User Info:** Current user details, tenant, language
- **AI Summary:** LLM-generated user summary
- **Chat History:** Last 10 message exchanges
- **Encoding Test:** Database text encoding verification
- **Prompt Inspection:** View assembled system prompt

**Use Case:** When testing fails, check debug panel for:
- Incorrect tenant assignment
- Missing system prompts
- Chat history issues

---

## 📊 Performance Benchmarks

| Metric | Expected Value | Actual (your setup) |
|--------|----------------|---------------------|
| **Document Upload** (1 PDF, 5 pages) | < 10 seconds | _______ |
| **Chunking** (5 pages → 50 chunks) | < 2 seconds | _______ |
| **Embedding** (50 chunks) | < 5 seconds | _______ |
| **RAG Query** (retrieve + generate) | < 5 seconds | _______ |
| **Simple Chat** (no RAG) | < 2 seconds | _______ |

---

## 🔍 Common Issues & Solutions

### Issue 1: "Qdrant connection failed"
**Solution:** Check `.env` QDRANT_URL and QDRANT_API_KEY

### Issue 2: "No chunks retrieved" despite document upload
**Possible causes:**
- Embedding model mismatch (check: text-embedding-3-large, 3072 dim)
- Similarity threshold too high (default: 0.7)
- Tenant filter blocking results

**Debug:**
```python
# Check Qdrant directly
from qdrant_client import QdrantClient
client = QdrantClient(url="...", api_key="...")
client.scroll(collection_name="document_chunks", limit=10)
```

### Issue 3: "RAG triggers for simple greetings"
**Cause:** Routing logic issue (P0.8 feature)

**Expected behavior:**
- "Hello" → CHAT (direct)
- "What's in the document?" → RAG (SEARCH)

**Fix:** Check `_decide_rag_needed_node` in `rag_workflow.py`

---

## 📦 Test Files

Included in `ai_chat_phase2/test_files/`:

| File | Content | Purpose |
|------|---------|---------|
| `sample.pdf` | Generic text | Basic upload test |
| `fantasy_story.txt` | Elves, dwarves, dragons | RAG retrieval test |
| `technical_doc.md` | Programming concepts | Markdown test |

**Generate your own test:**
```bash
# Create a custom test document
echo "This is a test document about artificial intelligence. Machine learning models..." > test_files/custom.txt
```

---

## ✅ Homework Checklist

**Required Features:**
- [x] Document upload endpoint
- [x] PDF text extraction
- [x] Text chunking (500 tokens)
- [x] Embedding generation (OpenAI)
- [x] Qdrant vector storage
- [x] RAG retrieval pipeline
- [x] LangGraph workflow
- [x] LLM integration with context

**Bonus Features (Implemented):**
- [x] Intelligent routing (SEARCH/LIST/CHAT)
- [x] Hierarchical prompts (3-tier)
- [x] Multi-tenant isolation
- [x] Debug panel enhancements

**Status:** ✅ **All requirements met, ready for evaluation**

---

## 📞 Support

**Documentation:**
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Homework mapping: [HOMEWORK_CHECKLIST.md](HOMEWORK_CHECKLIST.md)
- Build instructions: [INIT_FROM_PHASE15.md](INIT_FROM_PHASE15.md)

**Logs:**
```bash
# Backend logs (detailed)
docker logs -f ai_chat_phase2-backend-1

# Frontend logs
docker logs -f ai_chat_phase2-frontend-1

# Database access
docker exec -it ai_chat_phase2-postgres-1 psql -U app_user -d ai_chat_db
```

---

**Last Updated:** 2025-12-30  
**Tested on:** Docker 24.0+, macOS/Linux/Windows
