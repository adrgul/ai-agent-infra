# AI Agent Cost Optimization Demo

Educational LangGraph-based agent demonstrating **cost control** and **observability** best practices for AI systems.

## 🎯 Learning Objectives

This project teaches:

1. **Prompt Optimization**: Minimal prompts, output constraints, and token management
2. **Dynamic Model Selection**: Route queries to cheap/medium/expensive models based on complexity
3. **Caching Strategies**: Node-level and embedding caches to avoid redundant LLM calls
4. **Cost Tracking**: Per-node and per-model token/cost accounting
5. **Observability**: Full Prometheus metrics + Grafana dashboards
6. **SOLID Principles**: Clean, testable, extensible architecture

## 🏗️ Architecture

```
┌─────────────┐
│   FastAPI   │  /run, /metrics, /healthz
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         LangGraph Workflow              │
│                                         │
│  START → Triage → Conditional Route    │
│            │                            │
│            ├─→ Simple → Summary → END  │
│            ├─→ Retrieval → Summary     │
│            └─→ Reasoning → Summary     │
└─────────────────────────────────────────┘
       │
       ▼
┌──────────────────┐
│  LLM Interface   │  MockLLM (default) or OpenAI
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  Observability   │  Prometheus + Grafana
└──────────────────┘
```

### Workflow Nodes

| Node | Model | Purpose | Optimizations |
|------|-------|---------|---------------|
| **Triage** | Cheap (gpt-3.5-turbo) | Classify query complexity | Minimal prompt (20 tokens), node cache, low max_tokens |
| **Retrieval** | Cheap | RAG-style document retrieval | Embedding cache, top-k filtering, doc truncation |
| **Reasoning** | Expensive (gpt-4) | Complex analysis | Higher max_tokens, detailed prompts |
| **Summary** | Medium (gpt-4-turbo) | User-facing response | Balanced quality/cost, constrained output |

## 🚀 Quick Start

### Prerequisites

- Docker + Docker Compose
- (Optional) OpenAI API key for real LLM calls

### Run the Demo

```bash
# Clone/navigate to project
cd 10_cost_optimization

# Start all services
docker compose up --build

# Services will be available at:
# - Agent API: http://localhost:8000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

### Test the Agent

#### Scenario 1: Simple Query (Cheap Model Only)

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "What time is it?"
  }'
```

**What happens:**
- Triage classifies as "simple"
- Goes directly to summary (medium model)
- Total: 2 LLM calls (cheap + medium)
- **Cache effect**: Run same query again → triage result cached → only 1 LLM call

#### Scenario 2: Retrieval Query (RAG Flow)

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Find documents about Docker containers"
  }'
```

**What happens:**
- Triage classifies as "retrieval"
- Retrieval node searches knowledge base
- Embedding cache activated
- Summary with retrieved context
- Total: 2 LLM calls + retrieval

#### Scenario 3: Complex Query (Expensive Model)

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Explain the tradeoffs between microservices and monolithic architectures, considering scalability, maintenance, and cost"
  }'
```

**What happens:**
- Triage classifies as "complex"
- Reasoning node uses expensive model (gpt-4)
- Summary synthesizes final answer
- Total: 3 LLM calls (cheap + expensive + medium)

#### Scenario 4: Benchmark Mode (Cache Performance Demo)

```bash
# Run the same query 20 times to demonstrate cache effectiveness
curl -X POST "http://localhost:8000/run?repeat=20" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "What is the capital of France?"
  }'
```

**What happens:**
- First run: Full agent execution with LLM calls
- Runs 2-20: Cache hits, no LLM inference needed
- Response includes benchmark summary with cache statistics
- Total cost: ~$0.005 (vs. ~$0.10 without caching = 95% savings)

**Response includes:**
```json
{
  "answer": "Paris is the capital of France.",
  "benchmark": {
    "repeat": 20,
    "total_time_seconds": 3.4,
    "avg_time_per_run_seconds": 0.17,
    "cache_hits": {
      "node_cache": 19,
      "embedding_cache": 19
    },
    "cache_misses": {
      "node_cache": 1,
      "embedding_cache": 1
    }
  }
}
```

**See full documentation**: [BENCHMARK_FEATURE.md](BENCHMARK_FEATURE.md)

### View Metrics

Open Grafana at http://localhost:3000 (admin/admin)

**Key Dashboard Panels:**

1. **LLM Latency by Model** - p50/p95 response times
2. **Total Cost by Model** - Spend breakdown (last 1h)
3. **Cache Hit Ratio** - Triage node efficiency
4. **Node Latency** - Per-node execution times
5. **Error Rate** - Failures by node/type

**What to Look For:**

- **Cache working?** Run same query twice → triage cache hit ratio increases
- **Model selection?** Simple queries = cheap model only; complex = expensive model used
- **Cost differences?** Compare cheap (gpt-3.5) vs expensive (gpt-4) cost metrics
- **Latency impact?** Expensive model calls take longer but happen less frequently

## 📊 Cost Optimization Strategies Demonstrated

### 1. Prompt Optimization

**Triage Node** ([triage_node.py](app/nodes/triage_node.py)):
```python
# ❌ Bad: Verbose prompt
"You are a helpful assistant. Please carefully analyze the following 
user query and determine whether it requires simple, retrieval, or 
complex processing. Provide your classification..."

# ✅ Good: Minimal prompt (saves input tokens)
"Classify query type. Answer with ONE word only: simple, retrieval, or complex.\n\nQuery: {input}\n\nClassification:"
```

**Impact**: ~80% reduction in input tokens per triage call

### 2. Dynamic Model Selection

Queries are routed to appropriate model tiers:

| Tier | Model | Input Price | Output Price | Use Case |
|------|-------|-------------|--------------|----------|
| Cheap | gpt-3.5-turbo | $0.0001/1K | $0.0002/1K | Classification, simple tasks |
| Medium | gpt-4-turbo | $0.001/1K | $0.002/1K | User-facing responses |
| Expensive | gpt-4 | $0.01/1K | $0.03/1K | Complex reasoning only |

**Impact**: 10-50x cost reduction for simple queries vs. using GPT-4 for everything

### 3. Caching Strategies

#### Node-Level Cache ([triage_node.py](app/nodes/triage_node.py))
```python
# Check cache before LLM call
cache_key = generate_cache_key("triage", user_input)
cached_result = await cache.get(cache_key)

if cached_result:
    # Avoid LLM call entirely
    return cached_result
```

**Impact**: 100% cost savings on repeated queries (60min TTL)

#### Embedding Cache ([retrieval_node.py](app/nodes/retrieval_node.py))
```python
# Cache computed embeddings
embedding = await embedding_cache.get(text_hash)
if not embedding:
    embedding = compute_embedding(text)  # Expensive
    await embedding_cache.set(text_hash, embedding)
```

**Impact**: ~90% reduction in embedding API calls for common queries

#### Where Graph-Level Cache Fits

LangGraph supports **graph-level caching** (checkpointing):
- Caches entire workflow state at each node
- Useful for: retries, human-in-the-loop, conversation history
- **Tradeoff**: More memory, but enables complex workflows

**When to use:**
- Multi-turn conversations (cache previous turns)
- Workflows with expensive intermediate steps
- Debugging/replay scenarios

This demo uses **node-level** caching (simpler, more focused).

### 4. Output Constraints

```python
# Limit max_tokens to control output cost
response = await llm.complete(
    prompt=prompt,
    max_tokens=20,  # Triage: just need 1 word
    temperature=0.0  # Deterministic
)
```

**Impact**: Prevents runaway output costs

### 5. Context Management

```python
# Truncate retrieved documents
docs = [truncate(doc, max_length=200) for doc in docs]

# Limit top-k results
docs = docs[:3]  # Only pass 3 most relevant docs
```

**Impact**: Controls context size → reduces input token costs

## 🔬 SOLID Principles in Action

### Single Responsibility Principle
- **TriageNode**: Only classifies queries
- **CostTracker**: Only tracks costs
- **MetricsMiddleware**: Only records HTTP metrics

### Open/Closed Principle
- Swap LLM clients without changing nodes:
  ```python
  # In main.py, change this line:
  llm_client = MockLLMClient()  # → OpenAIClient()
  # Nodes don't change!
  ```

### Liskov Substitution Principle
- `MockLLMClient` and `OpenAIClient` both implement `LLMClient` interface
- Can be used interchangeably

### Interface Segregation Principle
- Small, focused interfaces:
  - `LLMClient`: just `complete()`
  - `Cache`: just `get/set/delete/clear`

### Dependency Inversion Principle
- Nodes depend on **interfaces**, not concrete implementations:
  ```python
  class TriageNode:
      def __init__(
          self,
          llm_client: LLMClient,  # ← Interface
          cache: Cache            # ← Interface
      ):
  ```

## 📈 Metrics Reference

### LLM Metrics
```promql
# Inference count
llm_inference_count_total{model, node, status}

# Latency
histogram_quantile(0.95, llm_inference_latency_seconds_bucket)

# Token usage
llm_inference_token_input_total{model, node}
llm_inference_token_output_total{model, node}

# Cost
llm_cost_total_usd{model, node}
```

### Agent Metrics
```promql
# Execution count
agent_execution_count_total{graph}

# Latency
histogram_quantile(0.95, agent_execution_latency_seconds_bucket)

# Node latency
node_execution_latency_seconds{graph, node}
```

### Cache Metrics
```promql
# Hit ratio
sum(rate(cache_hit_total[5m])) / 
  (sum(rate(cache_hit_total[5m])) + sum(rate(cache_miss_total[5m])))

# Operations
cache_hit_total{cache, node}
cache_miss_total{cache, node}
```

### Example Queries

**Total cost in last hour:**
```promql
sum(increase(llm_cost_total_usd[1h]))
```

**Most expensive node:**
```promql
topk(1, sum(increase(llm_cost_total_usd[1h])) by (node))
```

**Cache effectiveness:**
```promql
sum(rate(cache_hit_total{cache="node_cache"}[5m])) / 
  (sum(rate(cache_hit_total{cache="node_cache"}[5m])) + 
   sum(rate(cache_miss_total{cache="node_cache"}[5m])))
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

**Key settings:**

```bash
# Optional: Use real OpenAI API
OPENAI_API_KEY=sk-...

# Model names (change to use different models)
MODEL_CHEAP=gpt-3.5-turbo
MODEL_MEDIUM=gpt-4-turbo-preview
MODEL_EXPENSIVE=gpt-4

# Pricing (adjust for your models)
PRICE_CHEAP_INPUT=0.0001
PRICE_CHEAP_OUTPUT=0.0002

# Cache settings
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000
```

### Using OpenAI (Optional)

1. Set `OPENAI_API_KEY` in `.env`
2. Restart services: `docker compose down && docker compose up`
3. Application will use real OpenAI API instead of mock

**Note**: Real API calls cost money! Use mock for learning.

## 🧪 Running Without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload

# In separate terminals:
# - Prometheus: Use local prometheus binary with prometheus/prometheus.yml
# - Grafana: Use local grafana or cloud instance
```

## 📚 Educational Extensions

### Next Steps to Try

1. **Add Redis Cache**
   - Replace `MemoryCache` with Redis client
   - Demonstrates cache persistence across restarts

2. **Add Real Vector DB**
   - Replace simulated retrieval with Pinecone/Weaviate
   - Show production RAG patterns

3. **Add Real Tools**
   - Integrate web search, calculator, etc.
   - Demonstrate tool cost tracking

4. **Add Streaming**
   - Implement SSE for streaming responses
   - Show latency vs. time-to-first-token tradeoffs

5. **Add Retry/Fallback**
   - Implement exponential backoff
   - Demonstrate fallback to cheaper models on failure

6. **Add Human-in-the-Loop**
   - Use LangGraph checkpointing
   - Show graph-level caching benefits

## � Bad Version – What NOT to Do

> **⚠️ WARNING**: The `bad-version` branch contains intentionally inefficient code for teaching purposes. **DO NOT use in production!**

### Viewing the Bad Version

```bash
git checkout bad-version
docker compose up --build
# Then run test queries and observe Grafana
```

### What's Wrong with the Bad Version?

The `bad-version` branch demonstrates common anti-patterns that cause **excessive costs and poor performance**:

#### 1. **Verbose, Wasteful Prompts**
- ❌ Long, friendly, narrative prompts with repeated instructions
- ❌ Explains the same rules in every single node
- ❌ No token budget constraints

**Impact**: 
- Input tokens increase 5-10x per request
- Higher `llm_cost_total_usd` for no quality gain
- Metrics show: high `llm_input_tokens_total`

#### 2. **Wrong Model Selection**
- ❌ Uses expensive model (GPT-4) for EVERYTHING
- ❌ Classification uses expensive model (should be cheap)
- ❌ Summary uses expensive model (should be medium)
- ❌ No model routing or tiering strategy

**Impact**:
- Cost per request increases 10-20x
- `llm_inference_count` shows all calls use expensive model
- No cost savings from simple queries

#### 3. **Caching Completely Disabled**
- ❌ Node cache disabled (every query hits LLM)
- ❌ Embedding cache disabled (recompute every time)
- ❌ Results never reused

**Impact**:
- `cache_hit_total` remains at 0 (flat line in Grafana)
- Duplicate queries cost the same as first query
- Linear cost scaling with request volume

#### 4. **All Nodes Run for Every Request**
- ❌ Triage result is ignored
- ❌ Simple queries run retrieval + reasoning + summary
- ❌ No conditional routing

**Impact**:
- `nodes_executed` shows 4 nodes for all queries (should be 2-3)
- `llm_inference_count` is 4x higher than necessary
- p95 latency increases 3-5x

#### 5. **Unnecessarily High `max_tokens`**
- ❌ Triage: 2000 tokens (needs ~10)
- ❌ Reasoning: 3000 tokens (was 1000)
- ❌ Summary: 2000 tokens (was 300)

**Impact**:
- `llm_output_tokens_total` spikes unnecessarily
- Output token costs dominate (often 2x input cost)
- Slower response times (generating unused tokens)

### Expected Metrics (Bad Version vs Good Version)

| Metric | Good Version | Bad Version | Factor |
|--------|--------------|-------------|--------|
| **Cost per simple query** | $0.0015 | $0.025 | **16x higher** |
| **LLM calls per query** | 2-3 | 4 | **2x higher** |
| **Cache hit rate** | 40-60% | 0% | **No caching** |
| **p95 latency** | 1.2s | 4-6s | **4x slower** |
| **Input tokens** | 150-300 | 800-1500 | **5x higher** |
| **Output tokens** | 100-200 | 1500-3000 | **10x higher** |

### What the Grafana Dashboard Reveals

When running the bad version, you'll see:

1. **llm_cost_total_usd** - Steep upward curve (even for simple queries)
2. **cache_hit_total** - Flat at zero (no cache utilization)
3. **llm_inference_count** by model - All requests use expensive model
4. **nodes_executed** - Always 4 nodes (triage + retrieval + reasoning + summary)
5. **p95_latency** - Much higher than good version
6. **llm_output_tokens_total** - Wastefully high due to excessive `max_tokens`

### Why This Would Be Unacceptable in Production

1. **Financial Impact**:
   - With 10,000 queries/day: ~$250/day vs $15/day (good version)
   - Monthly cost: **$7,500** vs **$450**
   - Annual waste: **$84,600**

2. **Performance Degradation**:
   - Users experience 4-6s response times
   - Poor UX leads to abandonment
   - Cannot scale to high traffic

3. **Resource Waste**:
   - Generates tokens that are never read
   - Computes embeddings repeatedly
   - Executes unnecessary reasoning

4. **Technical Debt**:
   - No caching infrastructure used
   - Routing logic broken/ignored
   - Prompt engineering neglected

### Key Lessons

✅ **DO**: 
- Use the cheapest model that meets quality requirements
- Cache aggressively (node results, embeddings, classifications)
- Constrain `max_tokens` based on actual needs
- Route queries intelligently (don't run unnecessary nodes)
- Keep prompts minimal and focused

❌ **DON'T**:
- Use expensive models for simple tasks
- Write verbose prompts with repeated instructions
- Ignore caching opportunities
- Execute all nodes regardless of query type
- Set `max_tokens` higher than necessary

### Returning to Good Version

```bash
git checkout main
docker compose down
docker compose up --build
```

## �🐛 Troubleshooting

### Services won't start

```bash
# Check logs
docker compose logs agent-demo
docker compose logs prometheus
docker compose logs grafana

# Restart
docker compose down
docker compose up --build
```

### Metrics not showing in Grafana

1. Check Prometheus targets: http://localhost:9090/targets
2. Verify agent-demo is "UP"
3. Check datasource: Grafana → Configuration → Data Sources

### Cache not working

- Caches are in-memory → cleared on restart
- Check TTL settings in `.env`
- Run same query twice and check `cache_hits` in response debug

### High costs (real API)

- Check `total_cost_usd` in responses
- View cost breakdown in Grafana
- Switch to mock client: remove `OPENAI_API_KEY`

## 📖 Learning Resources

### Code Organization
- [app/llm/interfaces.py](app/llm/interfaces.py) - Interface design
- [app/nodes/triage_node.py](app/nodes/triage_node.py) - Node-level caching
- [app/graph/agent_graph.py](app/graph/agent_graph.py) - Workflow composition
- [app/observability/metrics.py](app/observability/metrics.py) - Metrics definitions

### Key Patterns
- **Dependency Injection**: [app/main.py](app/main.py) (lifespan function)
- **Cost Tracking**: [app/llm/cost_tracker.py](app/llm/cost_tracker.py)
- **Caching**: [app/cache/memory_cache.py](app/cache/memory_cache.py)
- **Instrumentation**: All nodes use `async_timer` + metrics helpers

## 📝 License

MIT - Educational purposes

## 🤝 Contributing

This is an educational demo. Feel free to:
- Extend with new optimization strategies
- Add more comprehensive examples
- Improve documentation
- Add tests

## 📞 Support

For questions about:
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **Prometheus**: https://prometheus.io/docs/
- **Grafana**: https://grafana.com/docs/

---

**Built with ❤️ for teaching AI cost optimization and observability**
