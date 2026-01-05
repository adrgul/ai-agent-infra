# KnowledgeRouter - Feature List

**Version:** 2.4  
**Last Updated:** 2026-01-05

---

## ✅ Implemented Features

### 🎫 IT Domain - Qdrant Semantic Search & Jira Integration (NEW in v2.3)

#### Confluence IT Policy Indexing
- **sync_confluence_it_policy.py**: Indexing script for Confluence pages
- **Workflow**: Confluence API → HTML parsing (BeautifulSoup) → Chunking (800 chars) → Embedding (OpenAI) → Qdrant upsert
- **Domain Filtering**: `domain="it"` metadata for precise filtering
- **Confluence API**: REST API v2, HTML storage format parsing
- **Section Extraction**: h1/h2/h3 headers with sibling content collection
- **Metadata**: section_id, section_title, confluence_url, indexed_at

#### Runtime IT Query Flow
- **Semantic Search**: Qdrant retrieval with domain=`it` filter (NOT keyword matching)
- **Redis Caching**: Embedding cache + query result cache
- **LLM Generation**: IT-specific instructions with procedure/responsibility references
- **Jira Ticket Offer**: Always offered at end of IT responses
- **Chat-Based Flow**: "igen" response detection → automatic ticket creation

#### Jira Ticket Integration
- **AtlassianClient**: Singleton for Jira API v3
- **Ticket Creation**: POST `/rest/api/3/issue` (project: SCRUM)
- **API Endpoint**: POST `/api/jira/ticket/` (summary, description, issue_type, priority)
- **Frontend Flow**: `lastITContext` → "igen" detection → `createJiraTicket()` → success message
- **Response Format**: Ticket key (SCRUM-123) with clickable link

#### Architecture Benefits
- **Consistent Workflow**: Same as HR/Marketing (Qdrant semantic search)
- **No Runtime Confluence Calls**: Indexing-time only, performance boost
- **Scalable**: Multiple Confluence pages can be indexed
- **Cached**: Redis reduces OpenAI API calls and search latency

### 🏗️ Architecture & Development Tools

#### LangGraph Orchestration (Production)
- **StateGraph Workflow**: Complete agent workflow using LangGraph StateGraph
- **4 Orchestrated Nodes**:
  - `intent_detection` - Domain classification (keyword + LLM fallback)
  - `retrieval` - Qdrant RAG search with domain filtering
  - `generation` - Context-aware LLM response generation
  - `execute_workflow` - HR/IT workflow automation
- **State Management**: AgentState TypedDict with messages, domain, citations, workflow
- **Linear Execution**: intent → retrieval → generation → workflow → END
- **Benefits**: Declarative workflow, easy debugging, state persistence, extensible graph structure

#### Enhanced ABC Interfaces
- **IEmbeddingService**: Swappable embedding providers (OpenAI/Cohere/HuggingFace)
- **IVectorStore**: Abstraction for Qdrant/Pinecone/Weaviate vector databases
- **IFeedbackStore**: Interface for PostgreSQL/MongoDB/Redis feedback persistence
- **IRAGClient**: Orchestration interface for retrieve operations
- **Benefits**: Easy mocking for tests, clear contracts, DIP compliance

#### Health Check System
- **Startup Validation**: Validates all critical services on app launch
- **Fail-Fast**: Immediate error detection for missing config
- **Graceful Degradation**: Optional services (PostgreSQL, Redis) don't block startup
- **Pretty-Printed Report**: Visual health status with ✅/⚠️ indicators
- **Environment Masking**: Secure display of sensitive API keys (sk-proj-***)

#### Debug CLI Utilities
- **Citation Formatter**: Pretty print RAG search results with scores, metadata, content preview
- **Feedback Statistics**: Visual bar charts with 🟢🟡🔴 indicators based on like percentage
- **Ranking Comparison**: Side-by-side semantic vs feedback-boosted ranking display
- **Interactive Testing**: `test_rag_search()` for live debugging
- **Command Line**: `python -m utils.debug_cli "query" domain top_k`

---

### 🔍 Core RAG & Search

#### Multi-Domain Knowledge Base
- **6 Domain Support**: HR, IT, Finance, Legal, Marketing, General
- **Single Qdrant Collection**: `multi_domain_kb` with domain filtering
- **Payload-Based Filtering**: Fast domain-specific searches without separate collections
- **Hybrid Search Ready**: Dense vectors (semantic) + metadata filtering (BM25 preparation)

#### Intent Detection (LangGraph Node)
- **Dual-Strategy Classification**: 
  - **Keyword-Based** (primary): Fast, cost-free pre-classification (20+ marketing terms, HR/IT keywords)
  - **LLM-Based** (fallback): GPT-4o-mini classification for ambiguous queries
- **State Management**: Domain stored in AgentState, passed to subsequent nodes
- **Supported Domains**: HR, IT, Finance, Legal, Marketing, General
- **Example Flow**: 
  - Query: "Mi a brand sorhossz?" → Keyword match: "brand" → Domain: marketing
  - Query: "VPN nem működik" → Keyword match: "VPN" → Domain: it
  - Query: "Contract terms" → LLM classification → Domain: legal

#### RAG Pipeline
- **Semantic Search**: OpenAI `text-embedding-3-small` (1536 dims)
- **Top-K Retrieval**: Configurable number of relevant documents
- **Citation Support**: Document references with source links
- **Context Window Management**: Auto-truncate to fit model limits (128k tokens)

---

### 💾 Caching & Performance

#### Redis Cache System
- **Embedding Cache**: Text → vector cache (reduces OpenAI API calls by 54%)
- **Query Result Cache**: Domain-specific query response caching
- **TTL Management**: Configurable expiration (default: 1 hour)
- **Memory Limits**: 512MB max with LRU eviction policy
- **Cache Stats API**: `/api/cache-stats/` endpoint for monitoring

#### Domain-Scoped Invalidation
- **Auto-Invalidation**: Document sync triggers cache clear per domain
- **Manual Invalidation**: `DELETE /api/cache-stats/?domain=marketing`
- **Selective Clearing**: Invalidate specific domains without affecting others

---

### 📊 Feedback & Analytics

#### Like/Dislike System (NEW in v2.1)
- **Citation-Level Feedback**: 👍👎 per document source
- **PostgreSQL Storage**: Async database with connection pooling
- **Background Processing**: Non-blocking feedback save (thread-safe)
- **Duplicate Handling**: ON CONFLICT update for same user/citation/session

#### Feedback Analytics
- **Domain-Scoped Stats**: Separate aggregation per domain
- **Materialized Views**: Fast query performance (`citation_stats` view)
- **API Endpoints**:
  - `POST /api/feedback/citation/` - Submit feedback
  - `GET /api/feedback/stats/` - Get aggregated statistics
  - `GET /api/feedback/stats/?domain=marketing` - Domain filtering

#### Citation Ranking (✅ IMPLEMENTED in v2.4)
- **Rank Tracking**: Store citation position (1st, 2nd, 3rd result)
- **Query Context**: Optional embedding storage for context-aware scoring
- **✅ Feedback-Weighted Re-ranking**: Live production feature
  - **Tiered Boost System**: +30% (>70% likes), +10% (40-70%), -20% (<40%)
  - **Batch PostgreSQL Queries**: Single SQL call for all citation feedback
  - **Score Formula**: `final_score = semantic_score × (1 + feedback_boost)`
  - **Adaptive Learning**: Popular content rises, poor quality demoted
- **✅ Content Deduplication**: Remove PDF/DOCX duplicates before ranking
  - **Signature-Based**: Title + content preview (80 chars)
  - **Highest Score Wins**: Keeps best-scoring duplicate
  - **Marketing Domain**: Solves Aurora Arculat kézikönyv duplicate issue
- **✅ IT Overlap Boost**: Lexical query-term matching for IT domain
  - **Generic Algorithm**: No hardcoded section IDs
  - **0-20% Score Boost**: Based on token overlap ratio
  - **Query Tokens**: Minimum 3-char tokens from user query

---

### 🔗 External Integrations

#### Google Drive (Marketing Domain)
- **OAuth 2.0 Authentication**: Service account with domain delegation
- **Folder Sync**: Auto-sync documents from specific Drive folders
- **File Parsing**: DOCX, PDF, TXT extraction
- **Metadata Preservation**: Filename, path, modification date

#### Qdrant Vector Database
- **Self-Hosted**: Docker container (port 6334)
- **Multi-Domain Collection**: Single collection with payload filtering
- **Async Client**: asyncpg for non-blocking operations
- **Health Monitoring**: Connection status checks

#### OpenAI API
- **GPT-4o-mini**: Response generation (cost-optimized)
- **text-embedding-3-small**: Document and query embeddings
- **Token Tracking**: Per-request usage logging
- **Cost Calculation**: Real-time cost estimation

---

### 🔄 Workflow Automation (LangGraph-Powered)

#### LangGraph Workflow Node
- **Integrated Node**: `execute_workflow` as final node in StateGraph
- **Domain-Specific Logic**: Different workflows per domain (HR, IT, Finance)
- **State-Based Execution**: Accesses full agent state (query, domain, citations)
- **Non-Blocking**: Workflow execution doesn't block response generation

#### Predefined Workflows
- **HR Vacation Request**: Parse dates, create workflow object
- **IT Support Ticket**: Generate ticket ID, track status
- **Extensible Framework**: Easy to add new workflow types as graph nodes

#### Workflow Structure
```json
{
  "action": "vacation_request",
  "type": "hr",
  "status": "pending",
  "next_step": "Manager approval",
  "data": {"start_date": "2024-10-03", "end_date": "2024-10-04"}
}
```

---

### ⚡ Cached Regeneration (NEW in v2.2)

**Optimize repeat queries by skipping intent detection and RAG retrieval.**

#### Architecture
- **Node Skipping**: Bypasses 2 of 4 LangGraph nodes (intent_detection + retrieval)
- **Session Cache**: Reads domain + citations from previous bot message
- **Partial Execution**: Runs ONLY generation + workflow nodes
- **State Reuse**: Injects cached data directly into AgentState

#### Performance Benefits

| Metric              | Full Pipeline (4 nodes) | Cached Regeneration (2 nodes) | Improvement |
|---------------------|-------------------------|-------------------------------|-------------|
| **Execution Time**  | ~5600ms                 | ~3500ms                       | **38% faster** |
| **Token Usage**     | ~2500 tokens            | ~500 tokens                   | **80% cheaper** |
| **LLM Calls**       | 2 (intent + generation) | 1 (generation only)           | **50% fewer** |
| **Qdrant Queries**  | 1 (RAG retrieval)       | 0 (uses session cache)        | **100% saved** |

#### Use Cases
- 🔄 **Refresh answer**: Same question, regenerate with different phrasing
- 🎯 **Refine response**: Retry generation without changing context
- 💰 **Cost optimization**: Multiple attempts at fraction of the cost
- ⚡ **Speed**: Sub-second regeneration for better UX

#### API Endpoint
```http
POST /api/regenerate/
{
  "session_id": "session_xyz",
  "query": "Mi a brand sorhossz?",
  "user_id": "user_123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "domain": "marketing",
    "answer": "Regenerated answer...",
    "citations": [...],
    "regenerated": true,
    "cache_info": {
      "skipped_nodes": ["intent_detection", "retrieval"],
      "executed_nodes": ["generation", "workflow"],
      "cached_citations_count": 5
    }
  }
}
```

#### Frontend UX
- **Dual Refresh Buttons**: ⚡ (cached) vs 🔄 (full RAG)
- **Visual Indicator**: Badge showing "⚡ Gyors újragenerálás (cached context)"
- **Color-Coded**: Green hover for cached, blue for full refresh

#### Technical Implementation
- **Backend**: `agent.regenerate()` method bypasses intent + retrieval nodes
- **Frontend**: `refreshQuery(question, useCache=true)` dual-mode function
- **Session Storage**: Message model enhanced with domain/citations/workflow fields
- **Validation**: Unit tests for node skipping + cache extraction

---

### 🛡️ Error Handling & Reliability

#### Retry Logic
- **Exponential Backoff**: 1s → 2s → 4s delays
- **Max Retries**: 3 attempts per request
- **Jitter**: Randomized delays to prevent thundering herd
- **Smart Retry**: Only retries transient errors (429, 5xx, timeouts)

#### Input Validation
- **Token Limits**: Max 10,000 input tokens (HTTP 413 if exceeded)
- **Empty Query Check**: Rejects blank requests (HTTP 400)
- **Prompt Truncation**: Auto-truncate to 100k tokens
- **SQL Injection Protection**: Parameterized queries

#### Error Status Codes
- `400` - Invalid request (empty query, missing fields)
- `413` - Payload too large (>10k tokens)
- `429` - Rate limit exceeded
- `500` - Internal server error
- `503` - OpenAI API unavailable

---

### 📈 Monitoring & Observability

#### Monitoring
- **Token Tracking**: Input + output tokens per request
- **Cost Calculation**: $0.15/1M input, $0.60/1M output (gpt-4o-mini)
- **API Endpoint**: `GET /api/usage-stats/`
- **Reset Capability**: `DELETE /api/usage-stats/`
- **Telemetry API** (NEW v2.2): Performance & debug data in `/api/query/` response
  - `total_latency_ms` - End-to-end pipeline time
  - `chunk_count` - RAG retrieval count
  - `max_similarity_score` - Top relevance score
  - `request/response/rag/llm` - Full debug payloads

#### Cache Monitoring
- **Hit Rate Tracking**: Cache hits vs misses
- **Memory Usage**: Current usage vs limit (512MB)
- **Key Count**: Total cached items
- **Connection Status**: Redis availability check

#### Logging
- **Structured Logs**: Timestamp, level, module, thread ID
- **Request Tracing**: Full request/response logging
- **Error Details**: Stack traces with context
- **Performance Metrics**: Query execution time

---

### 🎨 Frontend & UX

#### ChatGPT-Style Interface
- **Tailwind CSS**: Modern, responsive design
- **Markdown Rendering**: Rich text formatting in responses
- **Code Highlighting**: Syntax highlighting for code blocks
- **Loading States**: Skeleton loaders during processing

#### Citation Display
- **Document References**: Clickable source links
- **Citation Cards**: Title, snippet, relevance score
- **Rank Indicators**: #1, #2, #3 badges
- **Feedback Buttons**: 👍👎 per citation (NEW)

#### Conversation History
- **Session Persistence**: JSON-based storage
- **Multi-Session Support**: Isolated conversations per session
- **History Retrieval**: `GET /api/sessions/{session_id}/`
- **Context Reset**: Clear conversation context

#### Debug Panel (NEW in v2.2)
- **Real-Time Telemetry**: Live performance & pipeline metrics (bottom-right corner)
- **Performance Metrics**:
  - ⏱️ **Pipeline Latency** - Total request-response time (milliseconds)
  - 📦 **Chunk Count** - Number of retrieved RAG documents
  - 🎯 **Max Similarity Score** - Highest relevance score (0.0-1.0)
- **Collapsible Debug Sections** (scrollable, max 85vh):
  - 📤 **Request JSON** - Sent payload (user_id, session_id, query)
  - 📥 **Response JSON** - Complete API response structure
  - 🔍 **RAG Context** - Full document context sent to LLM
  - 🤖 **LLM Prompt** - Complete prompt with system message + context
  - 💬 **LLM Response** - Raw LLM output before processing
- **Auto-Update**: Refreshes on every query (new, cached ⚡, full refresh 🔄)
- **Graceful Degradation**: Shows "No RAG context" for general domain queries
- **Use Cases**: 
  - 🐛 Debug LLM prompt engineering
  - 📊 Performance monitoring & latency tracking
  - 🔬 RAG chunk quality validation
  - 🧪 End-to-end pipeline inspection

---

### 🐳 Deployment & DevOps

#### Docker Compose
- **Multi-Container**: Backend, Frontend, Qdrant, Redis, PostgreSQL
- **Hot Reload**: Uvicorn auto-reload on code changes
- **Volume Mounts**: Persistent data for Qdrant, Postgres, Redis
- **Health Checks**: Automated service health monitoring

#### ASGI Server
- **Uvicorn**: High-performance async server
- **uvloop**: Fast event loop (C-based)
- **Async Views**: Django REST Framework with async support
- **Connection Pooling**: Reusable database connections

#### Environment Configuration
- **`.env` File**: Centralized configuration
- **Environment Variables**: API keys, database credentials
- **Secrets Management**: `.env.example` template

---

### 🧪 Testing & Quality

#### Unit Tests (Updated v2.2)
- **121 Passing Tests**: Expanded test coverage (+60 tests)
- **49% Code Coverage**: Nearly doubled from 25% baseline
- **Pytest Framework**: Modern testing with fixtures and async support
- **Mock Support**: External API mocking with pytest-mock

#### Test Categories
- **Error Handling**: Retry logic, exponential backoff (39 tests ✅)
- **OpenAI Clients**: Embedding, LLM, token tracking (24 tests ✅)
- **Redis Cache**: Hit/miss, TTL, invalidation (partial legacy)
- **Feedback Ranking**: Boost calculation, PostgreSQL batch ops (14 tests ✅)
- **Health Checks**: Startup validation, config checks (10 tests ✅ NEW)
- **Debug CLI**: Citation formatting, feedback stats (17 tests ✅ NEW)
- **Interfaces**: ABC contracts, implementation validation (15 tests ✅ NEW)
- **Telemetry**: Pipeline metrics, RAG/LLM capture (9 tests ✅ NEW v2.2)

#### Test Execution
```bash
# Run all tests with coverage
docker-compose exec backend pytest tests/ --cov=infrastructure --cov=domain --cov=utils --cov-report=html

# Run specific test suites
docker-compose exec backend pytest tests/test_health_check.py -v
docker-compose exec backend pytest tests/test_debug_cli.py -v
docker-compose exec backend pytest tests/test_interfaces.py -v
docker-compose exec backend pytest tests/test_feedback_ranking.py -v

# View HTML coverage report
# Open: backend/htmlcov/index.html
```

#### CI/CD Ready
- **pytest.ini**: Configured test settings
- **Coverage Reports**: HTML + terminal output
- **Docker Tests**: Run tests in container environment
- **Coverage Threshold**: 25% minimum (currently 49% ✅)

---

## 🚧 Planned Features (Roadmap)

### High Priority
- [ ] **Multi-Query Generation**: 5 query variations with frequency ranking
- [ ] **BM25 Sparse Vectors**: Lexical search for brand names, codes

### Medium Priority
- [ ] **PII Detection**: Automatic sensitive data filtering
- [ ] **Rate Limiting**: Per-user request limits (100/hour)
- [ ] **Prometheus Metrics**: Advanced monitoring dashboard

### Low Priority
- [ ] **Authentication**: API key or JWT token auth
- [ ] **Audit Logging**: Compliance logs for all queries
- [ ] **WebSocket Support**: Real-time streaming responses
- [ ] **Multi-Language**: Auto-detect and translate

### ✅ Recently Completed (moved from roadmap)
- [x] **Feedback-Weighted Re-ranking** (v2.4)
- [x] **Content Deduplication** (v2.4)
- [x] **IT Overlap Boost** (v2.4)
- [x] **Section ID Citations** (v2.3)
- [x] **Jira Ticket Integration** (v2.3)

---

## 📊 Feature Metrics

| Category | Features | Status |
|----------|----------|--------|
| **Core RAG** | 8 | ✅ Complete |
| **Caching** | 6 | ✅ Complete |
| **Feedback** | 7 | ✅ Backend Complete, 🚧 Frontend Testing |
| **Architecture** | 3 | ✅ Complete (NEW v2.2) |
| **Testing** | 121 tests | ✅ 49% Coverage (NEW v2.2) |
| **Integrations** | 3 | ✅ Complete |
| **Workflows** | 2 types | ✅ Complete |
| **Frontend** | 12 | ✅ Complete |
| **DevOps** | 5 | ✅ Complete |

**Total Features:** 48 implemented | 10 planned

---

## 🔧 Development Tools

### Health Check System
```bash
# Health checks run automatically on startup
docker-compose up

# Example output:
# ======================================================================
# 🏥 INFRASTRUCTURE HEALTH CHECK
# ======================================================================
# 
# 📌 CRITICAL SERVICES:
#   ✅ ENV:OPENAI_API_KEY=sk-proj-***
#   ✅ OpenAI client importable
#   ✅ Qdrant URL configured: http://qdrant:6333
# 
# 📋 OPTIONAL SERVICES:
#   ⚠️ PostgreSQL will use lazy init: postgres
#   ⚠️ Redis configured: redis://redis:6379
# 
# ======================================================================
# ✅ ALL CRITICAL SERVICES READY
# ======================================================================
```

### Debug CLI
```bash
# Interactive RAG testing
docker-compose exec backend python -c "
from utils.debug_cli import quick_search
import asyncio
asyncio.run(quick_search('brand colors', 'marketing', 5))
"

# Command line usage
docker-compose exec backend python -m utils.debug_cli "szabadság igénylés" hr 5

# Example output:
# 📚 RETRIEVED 3 CITATIONS:
# ================================================================================
# 
#   [1] Score: 1.3000 | ID: 1ACEdQxgUuAsDHKPBqKyp2kt88DjfXjhv#chunk0
#       Title: Aurora_Digital_Brand_Guidelines_eng.docx
#       Content: "Brand colors are #0066CC (primary blue)..."
# 
# 📊 FEEDBACK STATISTICS (3 citations):
# ================================================================================
# 
#   🟢  85.0% [█████████████████░░░] doc_123#chunk0
#   🟡  55.0% [███████████░░░░░░░░░] doc_456#chunk1
#   🔴  25.0% [█████░░░░░░░░░░░░░░░] doc_789#chunk2
```
| **Integrations** | 3 | ✅ Complete |
| **Workflows** | 2 | ✅ Complete |
| **Error Handling** | 5 | ✅ Complete |
| **Monitoring** | 4 | ✅ Complete |
| **Frontend** | 6 | 🚧 Feedback UI Testing |
| **Deployment** | 4 | ✅ Complete |
| **Testing** | 4 | ✅ Complete |

**Overall Progress**: 47/52 features (90% complete)

---

## 🔗 Related Documentation

- [Main README](README.md) - Project overview
- [API Documentation](API.md) - Endpoint reference
- [Redis Cache](REDIS_CACHE.md) - Cache architecture
- [Installation Guide](INSTALLATION.md) - Setup instructions
- [Google Drive Setup](GOOGLE_DRIVE_SETUP.md) - Drive integration

---

**Last Updated:** 2025-12-18  
**Version:** 2.2 (Telemetry & Observability Release)
