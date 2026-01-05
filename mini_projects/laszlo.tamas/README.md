# AI Course Playground

Educational workspace for building multi-tenant RAG chat systems with FastAPI, React, and LangGraph.

## 📁 Workspace Structure

### Active Projects

#### HomeWork 1 : `ai_chat_phase1/`

A complete, working multi-user chat application with OpenAI API integration. This is Phase 1 of a larger AI system, focusing on foundational chat functionality with external API calls.

**Project Overview:**
- ✅ External API integration (OpenAI Chat Completions)
- ✅ Multi-user support (3 test users)
- ✅ Short-term conversation history in SQLite
- ✅ Clean, testable architecture
- ✅ Docker containerization

**Note:** This is Phase 1 ONLY. No LangGraph, no tools, no RAG, no vector database.

---

#### NOT UPLOADED, ONLY PREPARATION FOR V02 : `_archive_/ai_chat_phase15/` 

Multi-tenant chat system with LangGraph workflow and PostgreSQL. This is Phase 1.5, transitioning from single-user SQLite-based system to scalable, multi-tenant architecture.

**Project Overview:**
- ✅ **Multi-tenant architecture** (tenant-based data isolation)
- ✅ **LangGraph workflow** (2-node processing pipeline)
- ✅ **3-level hierarchical system prompts** (Application → Tenant → User)
- ✅ PostgreSQL database with normalized schema
- ✅ Document management (private/tenant visibility)
- ✅ Long-term memory preparation (Qdrant-ready data model)
- ✅ Short-term conversation history (20 messages)

**Note:** Phase 1.5 introduces LangGraph and multi-tenancy, but no RAG or vector store yet.

---

#### HomeWork 2 : `ai_chat_edu_v02/` ⭐ SUBMITTED

Complete RAG-enabled multi-tenant chat system with document upload, chunking, embeddings, and intelligent retrieval. This implements the full assignment: upload documents → process (chunk + embed) → store in vector database → query with LLM-based answers.

**Project Overview:**
- ✅ **Document upload & processing** (PDF, TXT, Markdown → chunk → embed → Qdrant)
- ✅ **RAG-based answering** (similarity search + LLM generation with sources)
- ✅ **Intelligent agent routing** (CHAT | RAG | LIST | EXPLICIT_MEMORY decisions)
- ✅ **Qdrant vector database** (3072-dim embeddings with tenant isolation)
- ✅ **2 LangGraph workflows** (unified chat orchestration + document processing)
- ✅ **Explicit memory system** (LLM-based fact extraction + long-term storage)
- ✅ **3-tier caching** (Memory → PostgreSQL → LLM for 47ms→13ms speedup)
- ✅ **Multi-tenant architecture** (isolated data per tenant in PostgreSQL + Qdrant)

**Note:** This is the complete RAG implementation. Document processing automated via single API call, intelligent routing prevents unnecessary RAG lookups.



