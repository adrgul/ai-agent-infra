# Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Compose                           │
│                                                                   │
│  ┌────────────────┐  ┌─────────────┐  ┌──────────────────┐     │
│  │   Agent Demo   │  │ Prometheus  │  │    Grafana       │     │
│  │   (FastAPI)    │  │   :9090     │  │     :3000        │     │
│  │     :8000      │  │             │  │                  │     │
│  │                │  │  Scrapes    │  │  Visualizes      │     │
│  │  /run          │─→│  /metrics   │─→│  metrics         │     │
│  │  /metrics      │  │             │  │                  │     │
│  │  /healthz      │  │             │  │  admin/admin     │     │
│  └────────────────┘  └─────────────┘  └──────────────────┘     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Application Architecture (SOLID Principles)

### Layer 1: API Layer (FastAPI)

```
app/main.py
├── POST /run        → Execute agent workflow
├── GET /metrics     → Prometheus exposition format
└── GET /healthz     → Health check
```

**Responsibilities:**
- HTTP request handling
- Request validation (Pydantic models)
- Dependency wiring (Composition Root)
- Metrics middleware

**Key Design Patterns:**
- Dependency Injection (lifespan manager)
- Repository Pattern (cache abstractions)
- Factory Pattern (graph creation)

### Layer 2: Orchestration Layer (LangGraph)

```
app/graph/
├── agent_graph.py   → Workflow definition
└── state.py         → Pydantic state model

Workflow:
  START
    ↓
  Triage (cheap model) → classify: simple/retrieval/complex
    ↓
  Conditional Router
    ├─→ simple    → Summary → END
    ├─→ retrieval → Retrieval → Summary → END
    └─→ complex   → Reasoning → Summary → END
```

**SOLID Principles:**
- **Open/Closed**: New nodes can be added without modifying existing ones
- **Liskov**: All nodes implement same interface (async execute method)
- **Dependency Inversion**: Nodes depend on abstractions (LLMClient, Cache)

### Layer 3: Business Logic Layer (Nodes)

```
app/nodes/
├── triage_node.py      → Classification (cheap model, cached)
├── retrieval_node.py   → RAG simulation (embedding cache)
├── reasoning_node.py   → Complex analysis (expensive model)
└── summary_node.py     → Final response (medium model)
```

**Each Node:**
```python
class Node:
    def __init__(
        self,
        llm_client: LLMClient,      # DIP: depend on interface
        cost_tracker: CostTracker,  # SRP: separate concern
        model_selector: ModelSelector,
        cache: Cache                # ISP: focused interface
    ):
        pass
    
    async def execute(self, state: AgentState) -> Dict:
        # Single responsibility: execute node logic
        # Record metrics
        # Update state
        pass
```

**Key Optimizations:**
| Node | Model | max_tokens | Cache | Rationale |
|------|-------|------------|-------|-----------|
| Triage | Cheap | 20 | Node-level | Just needs 1 word classification |
| Retrieval | Cheap | N/A | Embedding | Avoid re-computing embeddings |
| Reasoning | Expensive | 1000 | None | Complex tasks justify cost |
| Summary | Medium | 300 | None | Balance quality/cost |

### Layer 4: Integration Layer (LLM & Cache)

```
app/llm/
├── interfaces.py        → LLMClient interface (DIP)
├── mock_client.py       → Default implementation (no API key)
├── openai_client.py     → Optional OpenAI integration
├── models.py            → Model tier selection
└── cost_tracker.py      → Token/cost accounting

app/cache/
├── interfaces.py        → Cache interface (ISP)
├── memory_cache.py      → In-memory TTL cache
└── keys.py              → Key normalization
```

**Interface Segregation Example:**
```python
# Small, focused interface
class LLMClient(ABC):
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        **kwargs
    ) -> LLMResponse:
        pass

# Implementations can add extras but must satisfy interface
class MockLLMClient(LLMClient):
    async def complete(...) -> LLMResponse:
        # Deterministic mock responses
        pass

class OpenAIClient(LLMClient):
    async def complete(...) -> LLMResponse:
        # Real API calls
        pass
```

**Open/Closed Principle:**
- Want to add Anthropic? Create `AnthropicClient(LLMClient)`
- Want Redis cache? Create `RedisCache(Cache)`
- **Zero changes to existing nodes!**

### Layer 5: Observability Layer (Metrics)

```
app/observability/
├── metrics.py          → Prometheus metric definitions
└── middleware.py       → HTTP request instrumentation
```

**Metrics Categories:**

1. **LLM Metrics** (cost tracking):
   - `llm_inference_count_total{model, node, status}`
   - `llm_inference_latency_seconds{model, node}`
   - `llm_cost_total_usd{model, node}`
   - `llm_inference_token_input_total{model, node}`
   - `llm_inference_token_output_total{model, node}`

2. **Agent Metrics** (workflow performance):
   - `agent_execution_count_total{graph}`
   - `agent_execution_latency_seconds{graph}`
   - `node_execution_latency_seconds{graph, node}`

3. **Cache Metrics** (optimization effectiveness):
   - `cache_hit_total{cache, node}`
   - `cache_miss_total{cache, node}`
   - `cache_lookup_latency_seconds{cache}`

4. **RAG Metrics** (retrieval patterns):
   - `rag_retrieval_count_total{graph}`
   - `rag_docs_returned{graph}`
   - `rag_context_bytes{graph}`

5. **Error Metrics** (reliability):
   - `agent_error_count_total{graph, node, error_type}`
   - `model_fallback_count_total{from_model, to_model, node}`

## Data Flow

### Scenario: Complex Query

```
1. User Request
   POST /run {"user_input": "Explain microservices..."}
   
2. Middleware
   ├─ Start timer
   ├─ http_requests_total++
   └─ Continue to handler

3. Main Handler
   ├─ Create AgentState(user_input="...")
   ├─ Invoke graph.ainvoke(state)
   └─ Wait for result

4. LangGraph Execution
   
   A. Triage Node
      ├─ Check cache (key = hash(user_input))
      ├─ Cache MISS → call LLM
      │  ├─ MockLLM.complete(prompt, model="gpt-3.5-turbo", max_tokens=20)
      │  ├─ Response: "complex"
      │  ├─ Track cost: tracker.track_usage("triage", "gpt-3.5-turbo", 15, 1)
      │  ├─ Metrics: llm_inference_count_total{model="gpt-3.5-turbo",node="triage"}++
      │  └─ Cache result
      └─ Return {"classification": "complex"}
   
   B. Conditional Router
      ├─ Read state.classification == "complex"
      └─ Route to: reasoning_node
   
   C. Reasoning Node
      ├─ Build detailed prompt (longer input)
      ├─ Call expensive model
      │  ├─ MockLLM.complete(prompt, model="gpt-4", max_tokens=1000)
      │  ├─ Response: "After analysis... [detailed reasoning]"
      │  ├─ Track cost: tracker.track_usage("reasoning", "gpt-4", 100, 150)
      │  └─ Metrics: llm_cost_total_usd{model="gpt-4",node="reasoning"} += 0.0055
      └─ Return {"reasoning_output": "..."}
   
   D. Summary Node
      ├─ Build summary prompt (includes reasoning output)
      ├─ Call medium model
      │  ├─ MockLLM.complete(prompt, model="gpt-4-turbo", max_tokens=300)
      │  ├─ Response: "In summary... [user-facing answer]"
      │  ├─ Track cost: tracker.track_usage("summary", "gpt-4-turbo", 120, 80)
      │  └─ Metrics: llm_inference_latency_seconds{model="gpt-4-turbo",node="summary"}.observe(0.15)
      └─ Return {"final_answer": "..."}

5. Response Assembly
   ├─ Get cost report from tracker
   │  ├─ total_cost_usd = 0.0001 (triage) + 0.0055 (reasoning) + 0.002 (summary)
   │  └─ by_node = {"triage": {...}, "reasoning": {...}, "summary": {...}}
   ├─ Build debug object
   └─ Return RunResponse

6. Middleware
   ├─ Stop timer (elapsed = 1.2s)
   ├─ http_request_latency_seconds{path="/run"}.observe(1.2)
   ├─ agent_execution_latency_seconds{graph="agent"}.observe(1.15)
   └─ Return HTTP 200

7. Prometheus Scrape (every 10s)
   GET /metrics
   ├─ Collect all metric families
   └─ Return exposition format

8. Grafana Visualization
   ├─ Query Prometheus datasource
   ├─ Execute PromQL:
   │  └─ histogram_quantile(0.95, sum(rate(llm_inference_latency_seconds_bucket[5m])) by (le, model))
   └─ Render graph
```

## Cost Optimization Flow

```
┌──────────────────────────────────────────────────────────────┐
│                     Optimization Layers                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  1. ROUTING LAYER                                            │
│     ┌────────────┐                                           │
│     │   Triage   │ → Cheap model classifies query           │
│     └────────────┘                                           │
│          ↓                                                    │
│     Simple/Retrieval/Complex                                 │
│          ↓                                                    │
│     Route to appropriate node                                │
│                                                               │
│  2. CACHE LAYER                                              │
│     ┌─────────────────┬─────────────────┐                   │
│     │  Node Cache     │  Embedding Cache│                   │
│     │  (Triage)       │  (Retrieval)    │                   │
│     └─────────────────┴─────────────────┘                   │
│          ↓                     ↓                              │
│     Avoid redundant     Avoid re-computing                   │
│     LLM calls           embeddings                           │
│                                                               │
│  3. PROMPT OPTIMIZATION                                      │
│     ┌────────────────────────────────────┐                  │
│     │ Triage:    20 tokens max_tokens    │                  │
│     │ Summary:   300 tokens max_tokens   │                  │
│     │ Reasoning: 1000 tokens max_tokens  │                  │
│     └────────────────────────────────────┘                  │
│          ↓                                                    │
│     Only pay for tokens you need                            │
│                                                               │
│  4. CONTEXT MANAGEMENT                                       │
│     ┌────────────────────────────────────┐                  │
│     │ Top-K filtering (3 docs max)      │                  │
│     │ Doc truncation (200 chars)        │                  │
│     │ Minimal prompts                    │                  │
│     └────────────────────────────────────┘                  │
│          ↓                                                    │
│     Reduce input token costs                                │
│                                                               │
│  5. MODEL SELECTION                                          │
│     ┌──────────────────────────────────────────┐            │
│     │ Cheap:     $0.0001/1K in, $0.0002/1K out│            │
│     │ Medium:    $0.001/1K in,  $0.002/1K out │            │
│     │ Expensive: $0.01/1K in,   $0.03/1K out  │            │
│     └──────────────────────────────────────────┘            │
│          ↓                                                    │
│     Use expensive models only when justified                │
│                                                               │
└──────────────────────────────────────────────────────────────┘

Cost Savings Examples:
┌──────────────────────────────────────────────────────────────┐
│ Scenario: 1000 simple queries/day                            │
│                                                               │
│ ❌ Naive (all GPT-4):                                        │
│    1000 × 100 tokens × $0.01/1K = $1.00/day                 │
│                                                               │
│ ✅ Optimized (triage → cheap model):                        │
│    1000 × 15 tokens × $0.0001/1K = $0.015/day               │
│                                                               │
│ Savings: $1.00 - $0.015 = $0.985/day (98.5% reduction!)    │
│                                                               │
│ ✅✅ With caching (50% hit rate):                           │
│    500 × 0 (cached) + 500 × $0.015/1000 = $0.0075/day       │
│                                                               │
│ Total savings: 99.25%                                        │
└──────────────────────────────────────────────────────────────┘
```

## Extension Points (Where to Add Features)

### 1. Add New LLM Provider
```python
# app/llm/anthropic_client.py
class AnthropicClient(LLMClient):
    async def complete(...) -> LLMResponse:
        # Call Claude API
        pass

# app/main.py (composition root)
if settings.anthropic_api_key:
    llm_client = AnthropicClient()
```

### 2. Add Redis Cache
```python
# app/cache/redis_cache.py
class RedisCache(Cache):
    async def get(self, key: str):
        return await self.redis.get(key)
    
# app/main.py
node_cache = RedisCache(redis_url="redis://...")
```

### 3. Add New Node
```python
# app/nodes/validation_node.py
class ValidationNode:
    async def execute(self, state: AgentState):
        # Validate reasoning output
        pass

# app/graph/agent_graph.py
workflow.add_node("validation", validation_node.execute)
workflow.add_edge("reasoning", "validation")
workflow.add_edge("validation", "summary")
```

### 4. Add Tool Integration
```python
# app/tools/web_search.py
async def search_web(query: str):
    # Call search API
    metrics.tool_invocation_count_total.labels(tool="search", status="success").inc()
    return results
```

## Monitoring Queries (PromQL)

### Cost Analysis
```promql
# Total cost per hour by model
sum(increase(llm_cost_total_usd[1h])) by (model)

# Most expensive node
topk(1, sum(increase(llm_cost_total_usd[1h])) by (node))

# Cost efficiency (cost per request)
sum(increase(llm_cost_total_usd[1h])) / 
  sum(increase(agent_execution_count_total[1h]))
```

### Cache Effectiveness
```promql
# Hit ratio
sum(rate(cache_hit_total[5m])) / 
  (sum(rate(cache_hit_total[5m])) + sum(rate(cache_miss_total[5m])))

# Savings from cache (estimated)
sum(rate(cache_hit_total{cache="node_cache"}[5m])) * 0.0001
```

### Performance
```promql
# p95 latency by node
histogram_quantile(0.95, 
  sum(rate(node_execution_latency_seconds_bucket[5m])) by (le, node))

# Slowest requests
topk(10, http_request_latency_seconds)
```

---

**This architecture demonstrates production-ready AI agent patterns with focus on cost, performance, and maintainability.**
