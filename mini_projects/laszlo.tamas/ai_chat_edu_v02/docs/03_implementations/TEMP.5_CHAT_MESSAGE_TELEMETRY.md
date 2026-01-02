# Chat Message Telemetry & Analytics
## Comprehensive Monitoring Specification for AI Chat Phase 2

**Version:** 1.0  
**Date:** 2025-12-30  
**Status:** SPECIFICATION  
**Related TODO:** TEMP.5 in TODO_PHASE2.md

---

## 📊 Overview

### Purpose
Production-grade AI systems require comprehensive telemetry for:
- **Cost Tracking:** Monitor token usage and estimated costs per user/tenant
- **Performance Monitoring:** Track response times, identify bottlenecks, optimize slow queries
- **Cache Effectiveness:** Measure OpenAI prompt cache hit rates and cost savings
- **RAG Analytics:** Understand chunk usage, retrieval patterns, document effectiveness
- **User Behavior:** Analyze RAG vs direct chat usage patterns, optimize workflows

### Business Value
- **Cost Transparency:** Know exactly which users/tenants consume most tokens
- **Proactive Optimization:** Identify slow queries (>5s) before users complain
- **ROI Measurement:** Quantify cache savings (target: 80-90% cost reduction)
- **Data-Driven Decisions:** Make informed choices on model selection, chunk size, Top-K

---

## 🗄️ Database Schema Changes

### Option A: Add Columns to `chat_messages` Table (Recommended)

**Rationale:** Simple, keeps all message data in one place, no JOIN complexity.

#### New Telemetry Columns (12 fields)

```sql
-- Migration Script: 0003_add_chat_telemetry.sql

ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS user_message_tokens INT;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS prompt_prefix_id VARCHAR(50);
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS prompt_prefix_tokens INT;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS assistant_response_tokens INT;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS total_tokens INT;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS openai_cache_hit BOOLEAN DEFAULT FALSE;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS openai_cached_tokens INT DEFAULT 0;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS response_time_ms INT;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS rag_chunks_used INT DEFAULT 0;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS rag_documents_used TEXT[]; -- Array of document titles
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS estimated_cost_usd DECIMAL(10, 6);
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS workflow_path VARCHAR(20); -- 'RAG', 'CHAT', 'LIST'
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS llm_model VARCHAR(50) DEFAULT 'gpt-4o';

-- Add indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_tenant_id ON chat_messages(tenant_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_workflow_path ON chat_messages(workflow_path);
CREATE INDEX IF NOT EXISTS idx_chat_messages_cache_hit ON chat_messages(openai_cache_hit);

-- Add comment for documentation
COMMENT ON COLUMN chat_messages.user_message_tokens IS 'Number of tokens in the user message (input)';
COMMENT ON COLUMN chat_messages.prompt_prefix_id IS 'Hash/ID of the system prompt used (for cache tracking)';
COMMENT ON COLUMN chat_messages.prompt_prefix_tokens IS 'Number of tokens in the system prompt prefix';
COMMENT ON COLUMN chat_messages.assistant_response_tokens IS 'Number of tokens in the assistant response (output)';
COMMENT ON COLUMN chat_messages.total_tokens IS 'Total tokens used (user + prefix + response)';
COMMENT ON COLUMN chat_messages.openai_cache_hit IS 'TRUE if OpenAI prompt cache was used';
COMMENT ON COLUMN chat_messages.openai_cached_tokens IS 'Number of tokens served from cache';
COMMENT ON COLUMN chat_messages.response_time_ms IS 'Total response time in milliseconds';
COMMENT ON COLUMN chat_messages.rag_chunks_used IS 'Number of Qdrant chunks retrieved (0 if direct chat)';
COMMENT ON COLUMN chat_messages.rag_documents_used IS 'Array of document titles used as sources';
COMMENT ON COLUMN chat_messages.estimated_cost_usd IS 'Estimated cost based on GPT-4o pricing';
COMMENT ON COLUMN chat_messages.workflow_path IS 'Workflow taken: RAG, CHAT, or LIST';
COMMENT ON COLUMN chat_messages.llm_model IS 'LLM model used (e.g., gpt-4o, gpt-4o-mini)';
```

#### Field Descriptions

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `user_message_tokens` | INT | YES | Token count of user's input message |
| `prompt_prefix_id` | VARCHAR(50) | YES | Hash/ID of system prompt (for cache correlation) |
| `prompt_prefix_tokens` | INT | YES | Token count of system prompt prefix |
| `assistant_response_tokens` | INT | YES | Token count of assistant's response |
| `total_tokens` | INT | YES | Sum of all tokens (user + prefix + response) |
| `openai_cache_hit` | BOOLEAN | NO | TRUE if OpenAI served from prompt cache |
| `openai_cached_tokens` | INT | NO | Number of tokens served from cache (default: 0) |
| `response_time_ms` | INT | YES | Total response time in milliseconds |
| `rag_chunks_used` | INT | NO | Number of Qdrant chunks retrieved (0 if direct chat) |
| `rag_documents_used` | TEXT[] | YES | Array of document titles used as sources |
| `estimated_cost_usd` | DECIMAL(10,6) | YES | Estimated cost based on model pricing |
| `workflow_path` | VARCHAR(20) | YES | Workflow type: 'RAG', 'CHAT', 'LIST' |
| `llm_model` | VARCHAR(50) | NO | Model used (default: 'gpt-4o') |

---

## 💻 Code Changes

### 1. Updated Database Function Signature

**File:** `backend/database/pg_init.py`

**Before:**
```python
def insert_chat_message(conn, session_id, user_id, tenant_id, role, content):
    # Old signature (no telemetry)
    pass
```

**After:**
```python
def insert_chat_message_with_telemetry(
    conn,
    session_id: int,
    user_id: int,
    tenant_id: int,
    role: str,
    content: str,
    # Telemetry fields (all optional)
    user_message_tokens: int = None,
    prompt_prefix_id: str = None,
    prompt_prefix_tokens: int = None,
    assistant_response_tokens: int = None,
    total_tokens: int = None,
    openai_cache_hit: bool = False,
    openai_cached_tokens: int = 0,
    response_time_ms: int = None,
    rag_chunks_used: int = 0,
    rag_documents_used: list = None,
    estimated_cost_usd: float = None,
    workflow_path: str = None,
    llm_model: str = "gpt-4o"
) -> int:
    """
    Insert a chat message with comprehensive telemetry data.
    
    Args:
        conn: PostgreSQL connection
        session_id: Chat session ID
        user_id: User ID
        tenant_id: Tenant ID
        role: 'user' or 'assistant'
        content: Message content
        [12 telemetry parameters...]
    
    Returns:
        int: Inserted message ID
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO chat_messages (
                session_id, user_id, tenant_id, role, content,
                user_message_tokens, prompt_prefix_id, prompt_prefix_tokens,
                assistant_response_tokens, total_tokens,
                openai_cache_hit, openai_cached_tokens,
                response_time_ms, rag_chunks_used, rag_documents_used,
                estimated_cost_usd, workflow_path, llm_model
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s
            ) RETURNING id
        """, (
            session_id, user_id, tenant_id, role, content,
            user_message_tokens, prompt_prefix_id, prompt_prefix_tokens,
            assistant_response_tokens, total_tokens,
            openai_cache_hit, openai_cached_tokens,
            response_time_ms, rag_chunks_used, rag_documents_used,
            estimated_cost_usd, workflow_path, llm_model
        ))
        message_id = cur.fetchone()[0]
        conn.commit()
        return message_id
```

---

### 2. RAG Workflow Telemetry Capture

**File:** `backend/services/rag_workflow.py`

#### A. Add Telemetry Tracking in `execute()` Method

```python
async def execute(
    self,
    query: str,
    user_id: int,
    tenant_id: int,
    session_id: int,
    tenant_context: dict,
    user_context: dict,
    system_prompt: str,
) -> dict:
    """
    Execute RAG workflow with comprehensive telemetry tracking.
    """
    start_time = time.time()  # Start timer
    
    # ... existing workflow logic ...
    
    final_state = graph.invoke(initial_state)
    
    # Capture telemetry
    response_time_ms = int((time.time() - start_time) * 1000)
    telemetry = self._extract_telemetry(
        final_state=final_state,
        query=query,
        system_prompt=system_prompt,
        response_time_ms=response_time_ms
    )
    
    # Insert user message (with telemetry)
    insert_chat_message_with_telemetry(
        conn=self.db,
        session_id=session_id,
        user_id=user_id,
        tenant_id=tenant_id,
        role="user",
        content=query,
        user_message_tokens=telemetry["user_message_tokens"],
        prompt_prefix_tokens=telemetry["prompt_prefix_tokens"],
        workflow_path=telemetry["workflow_path"]
    )
    
    # Insert assistant message (with full telemetry)
    insert_chat_message_with_telemetry(
        conn=self.db,
        session_id=session_id,
        user_id=user_id,
        tenant_id=tenant_id,
        role="assistant",
        content=final_state.get("final_answer", ""),
        user_message_tokens=telemetry["user_message_tokens"],
        prompt_prefix_id=telemetry["prompt_prefix_id"],
        prompt_prefix_tokens=telemetry["prompt_prefix_tokens"],
        assistant_response_tokens=telemetry["assistant_response_tokens"],
        total_tokens=telemetry["total_tokens"],
        openai_cache_hit=telemetry["openai_cache_hit"],
        openai_cached_tokens=telemetry["openai_cached_tokens"],
        response_time_ms=telemetry["response_time_ms"],
        rag_chunks_used=telemetry["rag_chunks_used"],
        rag_documents_used=telemetry["rag_documents_used"],
        estimated_cost_usd=telemetry["estimated_cost_usd"],
        workflow_path=telemetry["workflow_path"],
        llm_model=telemetry["llm_model"]
    )
    
    return final_state
```

#### B. Telemetry Extraction Helper Method

```python
def _extract_telemetry(
    self,
    final_state: dict,
    query: str,
    system_prompt: str,
    response_time_ms: int
) -> dict:
    """
    Extract telemetry data from LangGraph state and OpenAI response.
    
    Args:
        final_state: LangGraph final state
        query: User query
        system_prompt: System prompt used
        response_time_ms: Total response time
    
    Returns:
        dict: Telemetry data
    """
    import tiktoken
    import hashlib
    
    # Token counting (using tiktoken for GPT-4o)
    encoding = tiktoken.encoding_for_model("gpt-4o")
    
    user_message_tokens = len(encoding.encode(query))
    prompt_prefix_tokens = len(encoding.encode(system_prompt))
    assistant_response = final_state.get("final_answer", "")
    assistant_response_tokens = len(encoding.encode(assistant_response))
    
    # Total tokens (including RAG context if used)
    rag_context = final_state.get("context", "")
    rag_context_tokens = len(encoding.encode(rag_context)) if rag_context else 0
    
    total_tokens = (
        user_message_tokens +
        prompt_prefix_tokens +
        rag_context_tokens +
        assistant_response_tokens
    )
    
    # Prompt prefix hash (for cache correlation)
    prompt_prefix_id = hashlib.md5(system_prompt.encode()).hexdigest()[:16]
    
    # OpenAI cache detection (from response metadata)
    # NOTE: Requires OpenAI API response inspection
    openai_response_metadata = final_state.get("llm_response_metadata", {})
    openai_cache_hit = openai_response_metadata.get("cache_hit", False)
    openai_cached_tokens = openai_response_metadata.get("cached_tokens", 0)
    
    # RAG metrics
    chunks = final_state.get("chunks", [])
    rag_chunks_used = len(chunks)
    
    # Extract unique document titles from chunks
    rag_documents_used = []
    if chunks:
        unique_docs = set()
        for chunk in chunks:
            doc_title = chunk.get("document_title", f"Document #{chunk.get('document_id')}")
            unique_docs.add(doc_title)
        rag_documents_used = list(unique_docs)
    
    # Workflow path detection
    workflow_path = "CHAT"  # Default
    if final_state.get("needs_rag") and rag_chunks_used > 0:
        workflow_path = "RAG"
    elif "list" in query.lower() or "show documents" in query.lower():
        workflow_path = "LIST"
    
    # Cost estimation (GPT-4o pricing as of 2025-12)
    # Input: $2.50 / 1M tokens (standard), $1.25 / 1M tokens (cached)
    # Output: $10.00 / 1M tokens
    input_tokens_uncached = total_tokens - assistant_response_tokens - openai_cached_tokens
    input_cost = (input_tokens_uncached * 2.50 / 1_000_000) + (openai_cached_tokens * 1.25 / 1_000_000)
    output_cost = assistant_response_tokens * 10.00 / 1_000_000
    estimated_cost_usd = round(input_cost + output_cost, 6)
    
    # LLM model (from config or state)
    llm_model = final_state.get("llm_model", "gpt-4o")
    
    return {
        "user_message_tokens": user_message_tokens,
        "prompt_prefix_id": prompt_prefix_id,
        "prompt_prefix_tokens": prompt_prefix_tokens,
        "assistant_response_tokens": assistant_response_tokens,
        "total_tokens": total_tokens,
        "openai_cache_hit": openai_cache_hit,
        "openai_cached_tokens": openai_cached_tokens,
        "response_time_ms": response_time_ms,
        "rag_chunks_used": rag_chunks_used,
        "rag_documents_used": rag_documents_used,
        "estimated_cost_usd": estimated_cost_usd,
        "workflow_path": workflow_path,
        "llm_model": llm_model
    }
```

---

### 3. Cost Estimation Formulas

#### GPT-4o Pricing (as of December 2025)

| Tier | Input (per 1M tokens) | Output (per 1M tokens) |
|------|----------------------|------------------------|
| Standard | $2.50 | $10.00 |
| Cached Input | $1.25 (50% discount) | N/A |

#### Python Cost Calculation

```python
def calculate_cost(
    input_tokens_uncached: int,
    input_tokens_cached: int,
    output_tokens: int,
    model: str = "gpt-4o"
) -> float:
    """
    Calculate estimated cost based on GPT-4o pricing.
    
    Args:
        input_tokens_uncached: Non-cached input tokens
        input_tokens_cached: Cached input tokens
        output_tokens: Output tokens
        model: Model name (for future multi-model support)
    
    Returns:
        float: Estimated cost in USD
    """
    # GPT-4o pricing
    PRICE_INPUT_STANDARD = 2.50 / 1_000_000  # $2.50 per 1M tokens
    PRICE_INPUT_CACHED = 1.25 / 1_000_000    # $1.25 per 1M tokens
    PRICE_OUTPUT = 10.00 / 1_000_000          # $10.00 per 1M tokens
    
    input_cost = (
        (input_tokens_uncached * PRICE_INPUT_STANDARD) +
        (input_tokens_cached * PRICE_INPUT_CACHED)
    )
    output_cost = output_tokens * PRICE_OUTPUT
    
    total_cost = input_cost + output_cost
    
    return round(total_cost, 6)  # Round to 6 decimal places ($0.000001 precision)
```

#### Example Calculations

**Scenario 1: Cache MISS (First Query)**
```python
input_tokens_uncached = 500  # System prompt + user message
input_tokens_cached = 0
output_tokens = 150

cost = calculate_cost(500, 0, 150)
# Input: 500 * $2.50 / 1M = $0.00125
# Output: 150 * $10.00 / 1M = $0.00150
# Total: $0.00275
```

**Scenario 2: Cache HIT (Follow-up Query)**
```python
input_tokens_uncached = 50   # Only new user message
input_tokens_cached = 450    # System prompt cached
output_tokens = 120

cost = calculate_cost(50, 450, 120)
# Input (uncached): 50 * $2.50 / 1M = $0.000125
# Input (cached): 450 * $1.25 / 1M = $0.0005625
# Output: 120 * $10.00 / 1M = $0.00120
# Total: $0.00189

# Savings: $0.00275 - $0.00189 = $0.00086 (31% reduction)
```

---

## 📊 Analytics Queries

### 1. Cost Per User (Last 30 Days)

```sql
SELECT 
    u.id AS user_id,
    u.firstname,
    u.lastname,
    u.email,
    COUNT(cm.id) AS total_messages,
    SUM(cm.total_tokens) AS total_tokens,
    SUM(cm.estimated_cost_usd) AS total_cost_usd,
    AVG(cm.response_time_ms) AS avg_response_time_ms,
    SUM(CASE WHEN cm.openai_cache_hit THEN 1 ELSE 0 END) AS cache_hits,
    ROUND(
        100.0 * SUM(CASE WHEN cm.openai_cache_hit THEN 1 ELSE 0 END) / NULLIF(COUNT(cm.id), 0),
        2
    ) AS cache_hit_rate_percent
FROM users u
LEFT JOIN chat_messages cm ON cm.user_id = u.id
WHERE cm.created_at >= NOW() - INTERVAL '30 days'
    AND cm.role = 'assistant'  -- Only count assistant responses (actual costs)
GROUP BY u.id, u.firstname, u.lastname, u.email
ORDER BY total_cost_usd DESC;
```

**Sample Output:**
| user_id | firstname | lastname | email | total_messages | total_tokens | total_cost_usd | avg_response_time_ms | cache_hits | cache_hit_rate_percent |
|---------|-----------|----------|-------|----------------|--------------|----------------|---------------------|------------|----------------------|
| 1 | Alice | Smith | alice@example.com | 145 | 187,500 | 1.875 | 2,340 | 120 | 82.76 |
| 2 | Bob | Johnson | bob@example.com | 89 | 112,000 | 1.120 | 1,890 | 65 | 73.03 |

---

### 2. Cache Hit Rate Per User

```sql
SELECT 
    u.id AS user_id,
    u.firstname || ' ' || u.lastname AS full_name,
    COUNT(cm.id) AS total_queries,
    SUM(CASE WHEN cm.openai_cache_hit THEN 1 ELSE 0 END) AS cache_hits,
    SUM(CASE WHEN NOT cm.openai_cache_hit THEN 1 ELSE 0 END) AS cache_misses,
    ROUND(
        100.0 * SUM(CASE WHEN cm.openai_cache_hit THEN 1 ELSE 0 END) / NULLIF(COUNT(cm.id), 0),
        2
    ) AS cache_hit_rate_percent,
    SUM(cm.openai_cached_tokens) AS total_cached_tokens,
    SUM(cm.estimated_cost_usd) AS total_cost_usd,
    -- Estimate cost without caching (assume 2x for cached tokens)
    SUM(cm.estimated_cost_usd) + SUM(cm.openai_cached_tokens * 1.25 / 1000000.0) AS estimated_cost_without_cache,
    -- Cost savings
    SUM(cm.openai_cached_tokens * 1.25 / 1000000.0) AS estimated_savings_usd
FROM users u
LEFT JOIN chat_messages cm ON cm.user_id = u.id
WHERE cm.created_at >= NOW() - INTERVAL '7 days'
    AND cm.role = 'assistant'
GROUP BY u.id, u.firstname, u.lastname
ORDER BY cache_hit_rate_percent DESC;
```

---

### 3. RAG vs Direct Chat Performance Comparison

```sql
SELECT 
    cm.workflow_path,
    COUNT(cm.id) AS total_queries,
    AVG(cm.response_time_ms) AS avg_response_time_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cm.response_time_ms) AS median_response_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY cm.response_time_ms) AS p95_response_time_ms,
    MAX(cm.response_time_ms) AS max_response_time_ms,
    AVG(cm.total_tokens) AS avg_total_tokens,
    AVG(cm.rag_chunks_used) AS avg_rag_chunks,
    AVG(cm.estimated_cost_usd) AS avg_cost_usd,
    SUM(cm.estimated_cost_usd) AS total_cost_usd
FROM chat_messages cm
WHERE cm.created_at >= NOW() - INTERVAL '30 days'
    AND cm.role = 'assistant'
GROUP BY cm.workflow_path
ORDER BY cm.workflow_path;
```

**Sample Output:**
| workflow_path | total_queries | avg_response_time_ms | median_response_time_ms | p95_response_time_ms | max_response_time_ms | avg_total_tokens | avg_rag_chunks | avg_cost_usd | total_cost_usd |
|---------------|---------------|----------------------|------------------------|---------------------|---------------------|------------------|----------------|--------------|----------------|
| CHAT | 456 | 1,850 | 1,720 | 3,200 | 5,890 | 750 | 0.0 | 0.0095 | 4.332 |
| RAG | 234 | 3,450 | 3,120 | 6,800 | 12,340 | 1,850 | 4.2 | 0.0215 | 5.031 |
| LIST | 12 | 890 | 820 | 1,200 | 1,450 | 320 | 0.0 | 0.0045 | 0.054 |

---

### 4. Monthly Cost Savings from Caching

```sql
SELECT 
    DATE_TRUNC('day', cm.created_at) AS day,
    COUNT(cm.id) AS total_queries,
    SUM(CASE WHEN cm.openai_cache_hit THEN 1 ELSE 0 END) AS cache_hits,
    ROUND(
        100.0 * SUM(CASE WHEN cm.openai_cache_hit THEN 1 ELSE 0 END) / NULLIF(COUNT(cm.id), 0),
        2
    ) AS cache_hit_rate_percent,
    SUM(cm.estimated_cost_usd) AS actual_cost_usd,
    SUM(cm.openai_cached_tokens * 1.25 / 1000000.0) AS estimated_savings_usd,
    SUM(cm.estimated_cost_usd) + SUM(cm.openai_cached_tokens * 1.25 / 1000000.0) AS cost_without_cache_usd,
    ROUND(
        100.0 * SUM(cm.openai_cached_tokens * 1.25 / 1000000.0) / 
        NULLIF(SUM(cm.estimated_cost_usd) + SUM(cm.openai_cached_tokens * 1.25 / 1000000.0), 0),
        2
    ) AS savings_percent
FROM chat_messages cm
WHERE cm.created_at >= NOW() - INTERVAL '30 days'
    AND cm.role = 'assistant'
GROUP BY DATE_TRUNC('day', cm.created_at)
ORDER BY day DESC;
```

---

### 5. Slowest Queries (Response Time > 5s)

```sql
SELECT 
    cm.id,
    cm.created_at,
    u.firstname || ' ' || u.lastname AS user,
    t.name AS tenant,
    LEFT(cm.content, 100) AS user_query_preview,
    cm.response_time_ms,
    cm.workflow_path,
    cm.rag_chunks_used,
    cm.total_tokens,
    cm.estimated_cost_usd
FROM chat_messages cm
JOIN users u ON u.id = cm.user_id
JOIN tenants t ON t.id = cm.tenant_id
WHERE cm.created_at >= NOW() - INTERVAL '7 days'
    AND cm.role = 'user'
    AND cm.response_time_ms > 5000  -- Slower than 5 seconds
ORDER BY cm.response_time_ms DESC
LIMIT 50;
```

---

## 🔌 API Endpoints

### 1. Cost Summary Endpoint

**Endpoint:** `GET /api/analytics/cost-summary`

**Query Parameters:**
- `days` (optional, default: 7): Number of days to analyze
- `tenant_id` (optional): Filter by specific tenant

**Response:**
```json
{
  "period": {
    "start": "2025-12-23T00:00:00Z",
    "end": "2025-12-30T00:00:00Z",
    "days": 7
  },
  "summary": {
    "total_queries": 1247,
    "total_tokens": 1_542_000,
    "total_cost_usd": 15.42,
    "avg_cost_per_query_usd": 0.0124,
    "cache_hit_rate_percent": 78.5,
    "estimated_savings_usd": 8.23,
    "cost_without_cache_usd": 23.65
  },
  "by_workflow": [
    {
      "workflow_path": "RAG",
      "total_queries": 456,
      "total_cost_usd": 9.85,
      "avg_response_time_ms": 3450
    },
    {
      "workflow_path": "CHAT",
      "total_queries": 789,
      "total_cost_usd": 5.52,
      "avg_response_time_ms": 1850
    },
    {
      "workflow_path": "LIST",
      "total_queries": 2,
      "total_cost_usd": 0.05,
      "avg_response_time_ms": 890
    }
  ],
  "by_user_top10": [
    {
      "user_id": 1,
      "user_name": "Alice Smith",
      "total_queries": 234,
      "total_cost_usd": 4.56,
      "cache_hit_rate_percent": 82.1
    },
    {
      "user_id": 2,
      "user_name": "Bob Johnson",
      "total_queries": 189,
      "total_cost_usd": 3.78,
      "cache_hit_rate_percent": 75.3
    }
  ]
}
```

**Implementation:**
```python
# File: backend/api/analytics_endpoints.py

from fastapi import APIRouter, Query, Depends
from backend.database.pg_init import get_db_connection
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/cost-summary")
async def get_cost_summary(
    days: int = Query(default=7, ge=1, le=365),
    tenant_id: int = Query(default=None)
):
    """
    Get cost summary with cache effectiveness metrics.
    """
    conn = get_db_connection()
    start_date = datetime.now() - timedelta(days=days)
    
    # Query 1: Overall summary
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                COUNT(id) AS total_queries,
                SUM(total_tokens) AS total_tokens,
                SUM(estimated_cost_usd) AS total_cost_usd,
                AVG(estimated_cost_usd) AS avg_cost_per_query_usd,
                ROUND(
                    100.0 * SUM(CASE WHEN openai_cache_hit THEN 1 ELSE 0 END) / NULLIF(COUNT(id), 0),
                    2
                ) AS cache_hit_rate_percent,
                SUM(openai_cached_tokens * 1.25 / 1000000.0) AS estimated_savings_usd,
                SUM(estimated_cost_usd) + SUM(openai_cached_tokens * 1.25 / 1000000.0) AS cost_without_cache_usd
            FROM chat_messages
            WHERE created_at >= %s
                AND role = 'assistant'
                AND (%s IS NULL OR tenant_id = %s)
        """, (start_date, tenant_id, tenant_id))
        summary = dict(zip([desc[0] for desc in cur.description], cur.fetchone()))
    
    # Query 2: By workflow
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                workflow_path,
                COUNT(id) AS total_queries,
                SUM(estimated_cost_usd) AS total_cost_usd,
                AVG(response_time_ms) AS avg_response_time_ms
            FROM chat_messages
            WHERE created_at >= %s
                AND role = 'assistant'
                AND (%s IS NULL OR tenant_id = %s)
            GROUP BY workflow_path
            ORDER BY total_queries DESC
        """, (start_date, tenant_id, tenant_id))
        by_workflow = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]
    
    # Query 3: Top 10 users
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                u.id AS user_id,
                u.firstname || ' ' || u.lastname AS user_name,
                COUNT(cm.id) AS total_queries,
                SUM(cm.estimated_cost_usd) AS total_cost_usd,
                ROUND(
                    100.0 * SUM(CASE WHEN cm.openai_cache_hit THEN 1 ELSE 0 END) / NULLIF(COUNT(cm.id), 0),
                    2
                ) AS cache_hit_rate_percent
            FROM users u
            JOIN chat_messages cm ON cm.user_id = u.id
            WHERE cm.created_at >= %s
                AND cm.role = 'assistant'
                AND (%s IS NULL OR cm.tenant_id = %s)
            GROUP BY u.id, u.firstname, u.lastname
            ORDER BY total_cost_usd DESC
            LIMIT 10
        """, (start_date, tenant_id, tenant_id))
        by_user_top10 = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]
    
    conn.close()
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": datetime.now().isoformat(),
            "days": days
        },
        "summary": summary,
        "by_workflow": by_workflow,
        "by_user_top10": by_user_top10
    }
```

---

### 2. User Costs Endpoint

**Endpoint:** `GET /api/analytics/user-costs`

**Query Parameters:**
- `days` (optional, default: 30): Number of days to analyze
- `user_id` (optional): Filter by specific user

**Response:**
```json
{
  "period": {
    "start": "2025-11-30T00:00:00Z",
    "end": "2025-12-30T00:00:00Z",
    "days": 30
  },
  "users": [
    {
      "user_id": 1,
      "user_name": "Alice Smith",
      "email": "alice@example.com",
      "total_queries": 456,
      "total_tokens": 587_000,
      "total_cost_usd": 5.87,
      "avg_cost_per_query_usd": 0.0129,
      "cache_hit_rate_percent": 82.1,
      "estimated_savings_usd": 3.45,
      "workflow_breakdown": {
        "RAG": {"queries": 234, "cost_usd": 4.12},
        "CHAT": {"queries": 220, "cost_usd": 1.73},
        "LIST": {"queries": 2, "cost_usd": 0.02}
      }
    }
  ]
}
```

---

## 💡 Expected Insights

### 1. Cost Optimization
- **User/Tenant Breakdown:** Identify heavy users consuming most tokens
- **Workflow Efficiency:** Compare RAG vs direct chat costs
- **Model Selection:** Analyze if GPT-4o-mini could replace GPT-4o for simple queries
- **Chunking Strategy:** Evaluate if Top-K=3 is better than Top-K=5 (fewer tokens)

### 2. Performance Monitoring
- **Latency Tracking:** Identify slow queries (>5s) and investigate bottlenecks
- **RAG Performance:** Measure retrieval time vs LLM inference time
- **Outlier Detection:** Flag unusually long response times for investigation
- **SLA Compliance:** Track percentage of queries < 3s (target: 95%)

### 3. Cache Effectiveness
- **Hit Rate Tracking:** Monitor cache hit rate per user (target: >70%)
- **Cost Savings:** Quantify actual savings from prompt caching
- **Cache Optimization:** Identify users with low cache hit rates (prompt inconsistency?)
- **ROI Measurement:** Calculate cache implementation ROI (target: 80-90% savings)

### 4. User Behavior Patterns
- **RAG vs Chat Usage:** Understand when users rely on documents vs direct chat
- **Document Popularity:** Identify most-referenced documents
- **Query Patterns:** Detect common question types for optimization
- **Session Analysis:** Track multi-turn conversation patterns

---

## 🚀 Implementation Steps

### Step 1: Database Migration
```bash
# Run migration script
psql -U postgres -d ai_chat_phase2 -f backend/database/migrations/0003_add_chat_telemetry.sql

# Verify columns added
psql -U postgres -d ai_chat_phase2 -c "\d+ chat_messages"
```

**Expected Output:**
```
Column                      | Type           | Nullable | Default
----------------------------+----------------+----------+---------
user_message_tokens         | integer        | YES      | 
prompt_prefix_id            | varchar(50)    | YES      | 
prompt_prefix_tokens        | integer        | YES      | 
assistant_response_tokens   | integer        | YES      | 
total_tokens                | integer        | YES      | 
openai_cache_hit            | boolean        | NO       | false
openai_cached_tokens        | integer        | NO       | 0
response_time_ms            | integer        | YES      | 
rag_chunks_used             | integer        | NO       | 0
rag_documents_used          | text[]         | YES      | 
estimated_cost_usd          | decimal(10,6)  | YES      | 
workflow_path               | varchar(20)    | YES      | 
llm_model                   | varchar(50)    | NO       | 'gpt-4o'
```

---

### Step 2: Update `pg_init.py`
```bash
# Modify backend/database/pg_init.py
# Replace insert_chat_message() with insert_chat_message_with_telemetry()
# Add all 12 telemetry parameters
```

**Testing:**
```python
# backend/debug/test_telemetry_insert.py
from backend.database.pg_init import get_db_connection, insert_chat_message_with_telemetry

conn = get_db_connection()

message_id = insert_chat_message_with_telemetry(
    conn=conn,
    session_id=1,
    user_id=1,
    tenant_id=1,
    role="assistant",
    content="This is a test response.",
    user_message_tokens=50,
    prompt_prefix_id="abc123def456",
    prompt_prefix_tokens=450,
    assistant_response_tokens=120,
    total_tokens=620,
    openai_cache_hit=True,
    openai_cached_tokens=450,
    response_time_ms=2340,
    rag_chunks_used=3,
    rag_documents_used=["User Guide", "FAQ"],
    estimated_cost_usd=0.00189,
    workflow_path="RAG",
    llm_model="gpt-4o"
)

print(f"Inserted message ID: {message_id}")
conn.close()
```

---

### Step 3: Modify RAG Workflow
```bash
# Update backend/services/rag_workflow.py
# Add _extract_telemetry() method
# Modify execute() to capture telemetry
# Update all LangGraph node calls
```

**Testing:**
```bash
# Run RAG workflow test
cd backend
python debug/test_rag_telemetry.py

# Expected output:
# [TELEMETRY] User message tokens: 45
# [TELEMETRY] Prompt prefix tokens: 520
# [TELEMETRY] Assistant response tokens: 185
# [TELEMETRY] Total tokens: 750
# [TELEMETRY] Cache hit: True
# [TELEMETRY] Cached tokens: 520
# [TELEMETRY] Response time: 2,850 ms
# [TELEMETRY] RAG chunks used: 4
# [TELEMETRY] Documents used: ["Product Manual", "Quick Start"]
# [TELEMETRY] Estimated cost: $0.00234
# [TELEMETRY] Workflow path: RAG
```

---

### Step 4: Create Analytics Endpoints
```bash
# Create backend/api/analytics_endpoints.py
# Implement GET /api/analytics/cost-summary
# Implement GET /api/analytics/user-costs
# Register router in main.py
```

**Testing:**
```bash
# Test cost summary endpoint
curl http://localhost:8000/api/analytics/cost-summary?days=7

# Test user costs endpoint
curl http://localhost:8000/api/analytics/user-costs?days=30&user_id=1
```

---

### Step 5: Test with Sample Data
```bash
# Generate sample telemetry data
python backend/debug/generate_sample_telemetry.py

# Run analytics queries
psql -U postgres -d ai_chat_phase2 -f backend/debug/test_analytics_queries.sql
```

---

### Step 6: Deploy Monitoring Dashboard (Optional)
```bash
# Frontend: Create Analytics page
# Display cost trends, cache hit rates, slow queries
# Use Chart.js or Recharts for visualization
```

---

## ✅ Success Criteria

### Functional Requirements
- ✅ All chat messages have complete telemetry data (12 fields populated)
- ✅ Token counts match OpenAI API response (±2% accuracy)
- ✅ Cost estimates within ±5% of actual OpenAI billing
- ✅ Cache hit rate tracking matches OpenAI dashboard
- ✅ Response time tracking accurate (±50ms)

### Performance Requirements
- ✅ Telemetry capture adds <50ms overhead per request
- ✅ Analytics API responds in <500ms
- ✅ Database queries optimized with indexes (scan time <100ms)
- ✅ Zero user-facing performance degradation

### Business Requirements
- ✅ Cost transparency: per-user, per-tenant breakdown available
- ✅ Cache ROI: quantifiable savings (target: 80-90%)
- ✅ Performance SLA: track 95th percentile response times
- ✅ Actionable insights: identify optimization opportunities

---

## 📚 References

### OpenAI Documentation
- [Prompt Caching Guide](https://platform.openai.com/docs/guides/prompt-caching)
- [GPT-4o Pricing](https://openai.com/pricing)
- [Token Counting (tiktoken)](https://github.com/openai/tiktoken)

### LangChain/LangGraph
- [LangGraph State Management](https://python.langchain.com/docs/langgraph)
- [LangChain Callbacks for Telemetry](https://python.langchain.com/docs/modules/callbacks/)

### PostgreSQL
- [Array Data Types](https://www.postgresql.org/docs/current/arrays.html)
- [Indexes for Analytics](https://www.postgresql.org/docs/current/indexes-types.html)

---

## 📝 Notes

### Production Considerations
1. **Privacy:** Ensure telemetry data complies with GDPR/data retention policies
2. **Storage:** Monitor `chat_messages` table growth (consider partitioning by date)
3. **Archival:** Move old telemetry data (>90 days) to cold storage
4. **Monitoring:** Set up alerts for cost spikes (e.g., >$100/day)
5. **Validation:** Periodically compare estimated costs vs actual OpenAI billing

### Future Enhancements
- **Real-time Dashboard:** Stream telemetry to Grafana/Datadog
- **Anomaly Detection:** ML-based alerting for unusual cost/performance patterns
- **Multi-model Support:** Track costs for GPT-4o, GPT-4o-mini, Claude, etc.
- **User Budget Limits:** Implement per-user monthly spending caps
- **Cost Attribution:** Tag queries with project/feature for granular tracking

---

**END OF SPECIFICATION**
