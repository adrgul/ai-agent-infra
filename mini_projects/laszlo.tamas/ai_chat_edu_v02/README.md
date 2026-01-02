# AI Chat v0.2.0 - Educational Reference

Multi-tenant RAG chat system with LangGraph workflows, 3-tier caching, and intelligent routing.

---

## 🚀 Quick Start

```powershell
# 1. Setup
Copy-Item .env.example .env
# Edit .env: Set OPENAI_API_KEY=sk-...

# 2. Start (includes seed data)
docker-compose up -d

# 3. Access
# Frontend: http://localhost:3000
# Backend: http://localhost:8000/docs
```

---

## ✅ Core Features (Original Assignment)

### 1. File Upload
**UI:** 📎 icon → Upload modal | **Formats:** PDF, TXT, Markdown (max 10MB)

### 2. Auto Processing
**Workflow:** Chunking (500 tokens) → Embedding (OpenAI 3072d) → Qdrant storage  
**Endpoint:** `POST /api/workflows/process-document`

### 3. RAG Query
**Example:** "Miről szól a dokumentum?" | **Result:** LLM answer + 📄 source

### 4. Intelligent Chunk Selection
**Method:** Qdrant similarity search (TOP_K=5) | **Security:** Tenant-isolated

---

## 🎯 Advanced Features

**Multi-Tenant:** 4 seed tenants (ACME, TechStart) + isolated data (PostgreSQL + Qdrant)  
**LangGraph Agent:** CHAT | RAG | LIST | EXPLICIT_MEMORY routing (max 10 iterations)  
**3-Tier Cache:** Memory → PostgreSQL → LLM (47ms→13ms performance gain)  
**Chat History:** PostgreSQL metadata persistence + context-aware follow-up  
**Explicit Memory:** Auto fact extraction + spell-check + long-term storage

---

## 📂 Test Scenarios

```
1. RAG: "Miről szól a dokumentum?" → Answer + 📄 test_doc.txt
2. Chat: "Szia!" → LLM response (no RAG)
3. Upload: test_files/test_doc.txt → "Document processed successfully"
4. Context: "Kik az elfek?" + "És hol élnek?" → Q2 understands "they"
```

---

## 🔍 Debugging

```powershell
# Chunks in PostgreSQL
docker exec ai_chat_edu_v02-backend-1 python /app/debug/check_docs_chunks.py

# Vectors in Qdrant
docker exec ai_chat_edu_v02-backend-1 python /app/debug/check_qdrant_data.py

# Cache stats
curl.exe http://localhost:8000/api/admin/cache/stats

# Reset (DEV ONLY!)
.\reset.ps1
```

---

## 🔧 Configuration

**Required:** `OPENAI_API_KEY` in `.env`  
**Ports:** Backend 8000, Frontend 3000 (configurable in `.env`)  
**Data:** Local storage in `./data/` (postgres + qdrant)

---

## 📚 Documentation

- **[HOW_TO.md](docs/HOW_TO.md)** - Testing guide (Hungarian)
- **[CACHE_ARCHITECTURE.md](docs/03_architecture/CACHE_ARCHITECTURE.md)** - Cache details
- **[LANGGRAPH_WORKFLOWS.md](docs/LANGGRAPH_WORKFLOWS.md)** - Workflow architecture
- **[TODO_v02.md](docs/02_development/todo/TODO_v02.md)** - Implementation status

---

**Tech Stack:** Python 3.11, FastAPI, LangGraph 0.0.26, React 18, PostgreSQL 15, Qdrant  
**Version:** 0.2.0 | **Updated:** 2026-01-02

