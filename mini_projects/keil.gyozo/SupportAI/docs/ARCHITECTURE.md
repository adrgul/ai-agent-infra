# SupportAI - Architecture Documentation

## System Overview

SupportAI is an AI-powered customer support automation system that processes incoming tickets, performs intelligent triage, and generates draft responses with knowledge base citations.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Client Application                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ HTTP
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                          │
│  ┌────────────────┐  ┌─────────────────┐  ┌───────────────────┐   │
│  │  Middleware    │  │   API Routes    │  │  Error Handling   │   │
│  │  - Logging     │  │  - /tickets     │  │  - Validation     │   │
│  │  - Metrics     │  │  - /health      │  │  - Exceptions     │   │
│  └────────────────┘  └─────────────────┘  └───────────────────┘   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      LangGraph Workflow Engine                       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  1. detect_intent → 2. triage_classify → 3. expand_queries  │  │
│  │           ↓                                           ↓       │  │
│  │  8. validate_output ← 7. check_policy ← 6. draft_answer     │  │
│  │                                           ↑                   │  │
│  │                      5. rerank_docs ← 4. search_rag          │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ↓                ↓                ↓
    ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
    │  OpenAI API     │  │   Qdrant     │  │    Redis     │
    │  - GPT-4        │  │  Vector DB   │  │   Cache      │
    │  - Embeddings   │  │  (v1.13.2)   │  │   (7.x)      │
    └─────────────────┘  └──────────────┘  └──────────────┘
```

## Workflow Details

### Node 1: Intent Detection

**Purpose**: Classify problem type and customer sentiment

**Input**:
- `raw_message`: Customer's original message
- `customer_name`: Customer name
- `ticket_id`: Ticket identifier

**Output**:
- `problem_type`: billing | technical | account | feature_request
- `sentiment`: frustrated | neutral | satisfied

**LLM Configuration**:
- Model: GPT-4
- Temperature: 0 (deterministic)
- Output: Structured (Pydantic model)

**Logic**:
```python
1. Analyze message content
2. Identify problem category
3. Detect emotional tone
4. Flag urgency keywords
```

---

### Node 2: Triage Classification

**Purpose**: Assign category, priority, SLA, and team

**Input**:
- `problem_type`: From intent detection
- `sentiment`: From intent detection
- `raw_message`: Original message

**Output**:
- `category`: Main category (Billing, Technical, Account, Feature Request)
- `subcategory`: Specific sub-classification
- `priority`: P1 (4h) | P2 (24h) | P3 (72h)
- `sla_hours`: SLA commitment in hours
- `suggested_team`: Team to assign to
- `triage_confidence`: 0-1 confidence score

**Priority Rules**:
- **P1**: Service outages, security issues, payment completely blocked
- **P2**: Significant issues, billing errors, frustrated customers
- **P3**: General questions, minor issues, feature requests

**Logic**:
```python
1. Analyze problem type + sentiment
2. Apply priority rules
3. Boost priority if frustrated
4. Select appropriate team
5. Calculate confidence
```

---

### Node 3: Query Expansion

**Purpose**: Generate multiple search queries for better RAG recall

**Input**:
- `raw_message`: Customer's question
- `category`: From triage

**Output**:
- `search_queries`: List of 2-5 reformulated queries

**LLM Configuration**:
- Model: GPT-4
- Temperature: 0.3 (slightly creative)

**Strategies**:
```python
1. Rephrase with technical terms
2. Break down complex questions
3. Add category-specific keywords
4. Include synonyms and variations
```

**Example**:
```
Input: "I was charged twice for my subscription"
Queries:
  - duplicate subscription charge resolution
  - how to handle double billing
  - refund process for duplicate payment
  - subscription billing error troubleshooting
```

---

### Node 4: RAG Search

**Purpose**: Retrieve relevant documents from vector database

**Input**:
- `search_queries`: From query expansion
- `category`: For filtering (optional)

**Output**:
- `retrieved_docs`: Top-10 documents with scores

**Process**:
```python
1. For each search query:
   a. Generate embedding (text-embedding-3-large)
   b. Query Qdrant with vector
   c. Apply category filter if available
   d. Get top-k results (k=10)
2. Deduplicate by chunk_id (keep highest score)
3. Sort by score descending
4. Return top 10 unique documents
```

**Qdrant Configuration**:
- Collection: `support_knowledge_base`
- Vector size: 3072
- Distance: Cosine
- HNSW ef: 128
- Score threshold: 0.7

---

### Node 5: Re-ranking

**Purpose**: Improve relevance using cross-encoder LLM scoring

**Input**:
- `retrieved_docs`: From RAG search
- `raw_message`: Original question

**Output**:
- `reranked_docs`: Top-3 best documents

**Process**:
```python
1. For each document:
   a. Ask LLM to score relevance (0-1)
   b. Get reasoning for score
2. Combine scores:
   final_score = alpha * vector_score + (1-alpha) * llm_score
3. Sort by final_score
4. Return top 3
```

**Parameters**:
- `top_n`: 3 (configurable)
- `alpha`: 0.5 (weight for score combination)

**Why Re-ranking**:
- Vector search optimizes for semantic similarity
- Re-ranking optimizes for query-specific relevance
- Improves precision at the cost of recall

---

### Node 6: Draft Answer

**Purpose**: Generate customer-facing response with citations

**Input**:
- `reranked_docs`: Top-3 documents
- `raw_message`: Customer question
- `customer_name`: For personalization
- `sentiment`: For tone adjustment

**Output**:
- `answer_draft`:
  - `greeting`: Personalized greeting
  - `body`: Response with inline citations [DOC-ID]
  - `closing`: Professional closing
  - `tone`: Response tone
- `citations`: List of cited documents

**LLM Configuration**:
- Model: GPT-4
- Temperature: 0.3 (natural language)

**Citation Format**:
```
"Refunds typically take 5-7 business days [KB-1234]."
```

**Tone Adjustment**:
```python
if sentiment == "frustrated":
    tone = "empathetic and apologetic"
elif sentiment == "satisfied":
    tone = "friendly and positive"
else:
    tone = "professional and helpful"
```

---

### Node 7: Policy Check

**Purpose**: Validate response against business rules

**Input**:
- `answer_draft`: Generated response

**Output**:
- `policy_check`:
  - `refund_promise`: Boolean
  - `sla_mentioned`: Boolean
  - `escalation_needed`: Boolean
  - `compliance`: passed | warning | failed
  - `issues`: List of violations

**Validation Rules**:

1. **Refund Promises** (requires manager approval):
   - ❌ "we will refund", "you'll receive a refund"
   - ✅ "may be eligible", "we'll review"

2. **SLA Commitments** (requires authorization):
   - ❌ "within 24 hours", "by tomorrow"
   - ✅ "within our standard timeframe"

3. **Escalation Required**:
   - Legal matters
   - Security/privacy issues
   - Multiple unresolved issues
   - P1 priority tickets

**Process**:
```python
1. LLM analyzes draft for violations
2. Heuristic checks for obvious patterns
3. Special handling for P1 tickets
4. Determine compliance level
```

---

### Node 8: Validation

**Purpose**: Format and validate final output

**Input**: Complete workflow state

**Output**:
- `output`: Validated TicketOutput JSON

**Process**:
```python
1. Extract all state fields
2. Build Pydantic models
3. Validate schema
4. Add metadata (timestamp)
5. Handle errors with fallback
```

**Output Schema**:
```json
{
  "ticket_id": "string",
  "timestamp": "ISO8601",
  "triage": { ... },
  "answer_draft": { ... },
  "citations": [ ... ],
  "policy_check": { ... }
}
```

---

## Data Models

### SupportTicketState (TypedDict)

The complete workflow state object:

```python
{
    # Input
    "ticket_id": str,
    "raw_message": str,
    "customer_name": str,
    "customer_email": str,

    # Intent (node: detect_intent)
    "problem_type": str,
    "sentiment": str,

    # Triage (node: triage_classify)
    "category": str,
    "subcategory": str,
    "priority": str,
    "sla_hours": int,
    "suggested_team": str,
    "triage_confidence": float,

    # RAG (nodes: expand_queries, search_rag, rerank_docs)
    "search_queries": list[str],
    "retrieved_docs": list[dict],
    "reranked_docs": list[dict],

    # Draft (node: draft_answer)
    "answer_draft": dict,
    "citations": list[dict],

    # Validation (nodes: check_policy, validate_output)
    "policy_check": dict,  # ⚠️ Node: "check_policy"
    "output": dict
}
```

---

## Service Layer

### QdrantService

**Responsibilities**:
- Vector database operations
- Document storage and retrieval
- Collection management

**Key Methods**:
```python
- search(query_vector, top_k, category_filter)
- upsert_documents(documents, vectors)
- create_collection(vector_size, distance)
- health_check()
```

**Important Notes**:
- Uses `query_points()` not `search()` (qdrant-client >= 1.13)
- Point IDs must be UUIDs (use `uuid.uuid5` for deterministic conversion)
- `https=False` for local, `https=True` for Qdrant Cloud

---

### EmbeddingService

**Responsibilities**:
- Generate text embeddings
- Batch processing

**Configuration**:
- Model: text-embedding-3-large
- Dimension: 3072
- Provider: OpenAI

**Key Methods**:
```python
- embed_query(text) → list[float]
- embed_documents(texts) → list[list[float]]
- get_embedding_dimension() → int
```

---

### CacheService

**Responsibilities**:
- Redis caching operations
- TTL management

**Key Methods**:
```python
- get(key) → Any
- set(key, value, ttl)
- delete(key)
- clear_pattern(pattern)
```

**Use Cases**:
- Cache embeddings
- Cache LLM responses
- Session management

---

## API Layer

### Endpoints

**POST /api/v1/tickets/process**
- Process a support ticket
- Returns complete triage and draft

**GET /api/v1/tickets/metrics**
- Get processing metrics
- Counters, timers, gauges

**GET /health**
- Overall health status
- Service availability

**GET /health/ready**
- Kubernetes readiness probe

**GET /health/live**
- Kubernetes liveness probe

### Middleware

1. **LoggingMiddleware**: Request/response logging
2. **ErrorHandlerMiddleware**: Consistent error responses
3. **CORSMiddleware**: Cross-origin support

---

## Deployment

### Docker Compose Services

```yaml
services:
  api:          # FastAPI application
  qdrant:       # Vector database (v1.13.2)
  redis:        # Cache (7-alpine)
```

### Health Checks

All services have health checks:
- **API**: `curl http://localhost:8000/health`
- **Qdrant**: `curl http://localhost:6333/`
- **Redis**: `redis-cli ping`

### Resource Limits

**Qdrant**:
- No memory limit (configurable)
- Volume for persistence

**Redis**:
- 512MB max memory
- LRU eviction policy
- AOF persistence

---

## Performance Considerations

### Latency Breakdown (Estimated)

```
Total: ~3-5 seconds

Intent Detection:    0.5s  (GPT-4)
Triage:              0.5s  (GPT-4)
Query Expansion:     0.5s  (GPT-4)
Embedding (5 queries): 0.3s  (Batch)
RAG Search:          0.2s  (Qdrant)
Re-ranking (3 docs): 1.0s  (GPT-4 × 3)
Draft Answer:        1.0s  (GPT-4)
Policy Check:        0.5s  (GPT-4)
Validation:          0.1s  (Pydantic)
```

### Optimization Strategies

1. **Caching**:
   - Cache embeddings (TTL: 1 hour)
   - Cache common query results
   - Cache triage for similar tickets

2. **Batching**:
   - Batch embedding generation
   - Parallel re-ranking (if needed)

3. **Async Operations**:
   - All I/O is async
   - Concurrent service calls where possible

4. **Connection Pooling**:
   - Reuse HTTP clients
   - Persistent Qdrant connections

---

## Monitoring & Observability

### Metrics

**Counters**:
- `tickets_processed`
- `tickets_failed`
- `priority_P1`, `priority_P2`, `priority_P3`
- `category_Billing`, `category_Technical`, etc.
- `compliance_passed`, `compliance_failed`, `compliance_warning`

**Timers**:
- `ticket_processing_{ticket_id}` (total time)
- Individual node timings

**Gauges**:
- Current queue size
- Active connections

### Logging

**Levels**:
- DEBUG: Detailed workflow steps
- INFO: Request/response, metrics
- WARNING: Policy violations, retries
- ERROR: Failures, exceptions

**Structured Logs**:
```json
{
  "timestamp": "2025-01-23T10:30:00Z",
  "level": "INFO",
  "message": "Ticket processed successfully",
  "ticket_id": "TKT-001",
  "priority": "P2",
  "duration": 3.5
}
```

---

## Security

### API Security

- Input validation (Pydantic)
- Rate limiting (TODO)
- API key authentication (TODO)

### Data Security

- Customer data in memory only
- No PII logging
- Secure credentials (environment variables)

### Policy Enforcement

- Automated compliance checks
- Refund promise detection
- SLA commitment validation

---

## Scalability

### Horizontal Scaling

- Stateless API (can run multiple instances)
- Load balancer in front
- Shared Redis cache
- Shared Qdrant database

### Vertical Scaling

- Increase API workers
- More memory for Qdrant
- Larger Redis cache

### Bottlenecks

1. **OpenAI API**: Rate limits, latency
2. **Qdrant**: Vector search at high QPS
3. **Redis**: Memory limits

---

## Future Enhancements

1. **Advanced RAG**:
   - Hybrid search (keyword + vector)
   - Multiple re-rankers
   - Citation quality scoring

2. **Learning**:
   - Fine-tune on accepted responses
   - Feedback loop for model improvement
   - A/B testing different prompts

3. **Integrations**:
   - Zendesk, Jira, ServiceNow
   - Slack notifications
   - Real-time webhooks

4. **Analytics**:
   - Prometheus metrics export
   - Grafana dashboards
   - Alert rules

5. **Quality**:
   - Response quality scoring
   - Human-in-the-loop review
   - Automated testing suite

---

## Critical Implementation Details

### ⚠️ Node Naming Convention

LangGraph uses the same namespace for nodes and state fields!

**Rule**: State fields = nouns, Node names = verb_noun

```python
# State
policy_check: dict  # Noun

# Node
workflow.add_node("check_policy", ...)  # Verb_noun
```

### ⚠️ DateTime Handling

Python 3.12+ deprecates `datetime.utcnow()`:

```python
# ❌ Old way
datetime.utcnow()

# ✅ New way
datetime.now(timezone.utc)
```

### ⚠️ Qdrant Point IDs

Only UUID or unsigned int allowed:

```python
# ❌ Wrong
id="KB-1234"

# ✅ Correct
id=str(uuid.uuid5(uuid.NAMESPACE_DNS, "KB-1234"))
```

### ⚠️ Qdrant HTTPS

Must match deployment:

```python
# Local/Docker
QdrantClient(https=False)

# Cloud
QdrantClient(https=True, api_key="...")
```

---

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
