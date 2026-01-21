# Bad Version Guide

> ⚠️ **This is the INTENTIONALLY INEFFICIENT version for teaching purposes!**

## What You're Looking At

This branch demonstrates **what NOT to do** when building AI agents. Every design decision here is deliberately wrong to help you learn cost optimization through contrast.

## Quick Test

```bash
# Start the services
docker compose up --build

# Run a simple query
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is 2+2?"}'

# Open Grafana
open http://localhost:3000
# Login: admin/admin
# Go to the Agent Dashboard
```

## What to Observe in Grafana

### 1. **LLM Cost Total USD** (Top Left)
- Should increase rapidly even for simple queries
- Compare to main branch: 10-20x higher

### 2. **Cache Hit Total** (Middle)
- Will stay at **0** (flat line)
- No cache reuse happening

### 3. **LLM Inference Count by Model** (Bottom)
- **ALL calls** use expensive model (gpt-4)
- No cheap or medium model usage

### 4. **Nodes Executed** (Right)
- Shows **4 nodes** for every query:
  - triage
  - retrieval
  - reasoning
  - summary

### 5. **P95 Latency** (Top Right)
- Much higher than main branch
- 4-6 seconds typical

### 6. **Token Metrics**
- Input tokens: 800-1500 per request
- Output tokens: 1500-3000 per request
- Compare to main: 5-10x higher

## The Anti-Patterns Implemented

### ❌ Anti-Pattern #1: Verbose Prompts
**Location**: `prompts/*.txt`

**What's wrong**: 
- Triage prompt is 26 lines of friendly chatter
- Reasoning prompt explains methodology in detail
- Summary prompt has lengthy preamble

**Cost impact**: 5-10x more input tokens

**Fix**: See main branch for minimal, focused prompts

---

### ❌ Anti-Pattern #2: Wrong Model Selection
**Location**: All `app/nodes/*.py` files

**What's wrong**:
```python
# BAD: Using expensive model for everything
self.model_name = model_selector.get_model_name(ModelTier.EXPENSIVE)
```

**Cost impact**: 10-20x higher per request

**Fix**: Use cheap for triage, medium for summary, expensive only for complex reasoning

---

### ❌ Anti-Pattern #3: Disabled Caching
**Location**: `triage_node.py`, `retrieval_node.py`

**What's wrong**:
```python
# BAD: Force cache miss
cached_result = None
# Don't write to cache
# await self.cache.set(cache_key, classification)
```

**Cost impact**: No savings from repeated queries

**Fix**: See main branch for proper cache usage

---

### ❌ Anti-Pattern #4: All Nodes Run Always
**Location**: `agent_graph.py`

**What's wrong**:
```python
# BAD: Always route to retrieval
return "retrieval"

# BAD: Chain all nodes
workflow.add_edge("retrieval", "reasoning")
workflow.add_edge("reasoning", "summary")
```

**Cost impact**: 4 LLM calls instead of 2-3

**Fix**: Conditional routing based on query classification

---

### ❌ Anti-Pattern #5: Excessive max_tokens
**Location**: All nodes

**What's wrong**:
```python
# BAD: Way too high
max_tokens=2000  # For one-word classification!
max_tokens=3000  # For reasoning
```

**Cost impact**: Output tokens cost 2x input tokens

**Fix**: Constrain based on actual needs (20, 1000, 300)

---

## Cost Comparison Example

### Simple Query: "What is 2+2?"

| Metric | Good Version (main) | Bad Version | Multiplier |
|--------|---------------------|-------------|------------|
| **Nodes executed** | 2 (triage, summary) | 4 (all) | 2x |
| **LLM calls** | 2 | 4 | 2x |
| **Input tokens** | ~150 | ~1200 | 8x |
| **Output tokens** | ~100 | ~2000 | 20x |
| **Cost** | $0.0015 | $0.025 | **16x** |
| **Latency** | 0.8s | 4.5s | 5.6x |
| **Cache hits** | 1 (on repeat) | 0 | N/A |

**Annual cost at 10k queries/day**:
- Good: $5,475/year
- Bad: **$91,250/year**
- **Wasted: $85,775**

## Learning Exercise

1. **Run the bad version** and observe Grafana for 5-10 queries
2. **Switch to main branch**: `git checkout main && docker compose up --build`
3. **Run the same queries** on the good version
4. **Compare the dashboards** side-by-side

## Key Takeaways

✅ **DO**:
- Use the cheapest model that meets quality requirements
- Cache aggressively (node results, embeddings)
- Constrain max_tokens appropriately
- Route intelligently based on query type
- Keep prompts minimal and focused

❌ **DON'T**:
- Use expensive models for simple classification
- Write verbose, chatty prompts
- Disable caching
- Run all nodes for every request
- Set max_tokens higher than needed

## Switching Back to Good Version

```bash
git checkout main
docker compose down
docker compose up --build
```

---

**Remember**: This bad version exists purely for education. The patterns here would be catastrophic in production. Use the main branch for actual implementations.
