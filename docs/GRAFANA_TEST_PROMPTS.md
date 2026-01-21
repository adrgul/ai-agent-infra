# Grafana Dashboard Test Prompts

This file contains curated prompts to test and demonstrate all Grafana dashboard metrics.

## How to Use

1. Start services: `./start.sh`
2. Open Grafana: http://localhost:3000 (admin/admin)
3. Open the dashboard
4. Run these commands in order
5. Watch metrics update in real-time

---

## 1. Simple Query Tests (Cheap Model - gpt-3.5-turbo)

These should trigger triage classification as "simple" and route to summary directly.

### Test 1.1: Basic Fact

**Request Body:**
```json
{
  "user_input": "What is 2+2?",
  "scenario": "simple"
}
```

**cURL:**
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is 2+2?", "scenario": "simple"}'
```

**Expected Metrics**:
- `llm_inference_count_total{model="gpt-3.5-turbo"}`: +1 (triage)
- `llm_inference_count_total{model="gpt-4-turbo"}`: +1 (summary)
- `agent_execution_count_total`: +1
- Low cost (~$0.002)

### Test 1.2: Simple Question

**Request Body:**
```json
{
  "user_input": "What time is it?",
  "scenario": "simple"
}
```

### Test 1.3: Greeting

**Request Body:**
```json
{
  "user_input": "Hello, how are you?",
  "scenario": "simple"
}
```

### Test 1.4: Definition

**Request Body:**
```json
{
  "user_input": "Define API",
  "scenario": "simple"
}
```

---

## 2. Retrieval Query Tests (RAG Flow)

These should trigger triage classification as "retrieval" and use the retrieval node.

### Test 2.1: Document Search

**Request Body:**
```json
{
  "user_input": "Find information about Docker containers in the documentation",
  "scenario": "retrieval"
}
```

**Expected Metrics**:
- `rag_retrieval_count_total`: +1
- `rag_docs_returned`: Documents returned histogram
- Embedding cache miss on first run

### Test 2.2: Specific Documentation

**Request Body:**
```json
{
  "user_input": "Search for Kubernetes deployment guides",
  "scenario": "retrieval"
}
```

### Test 2.3: Code Examples

**Request Body:**
```json
{
  "user_input": "Look up Python async/await examples",
  "scenario": "retrieval"
}
```

### Test 2.4: Configuration Search

**Request Body:**
```json
{

**Request Body:**
```json
{
  "user_input": "Compare and contrast microservices vs monolithic architecture, considering scalability, maintenance costs, deployment complexity, and team organization. Provide specific examples.",
  "scenario": "complex"
}
```

**Expected Metrics**:
- `llm_inference_count_total{model="gpt-4"}`: +1 (reasoning)
- Higher cost (~$0.005-0.010)
- Higher latency (2-5 seconds)

### Test 3.2: Multi-Factor Analysis

**Request Body:**
```json
{
  "user_input": "Analyze the trade-offs between using serverless functions versus container orchestration for a high-traffic API. Consider cost, performance, scalability, vendor lock-in, and operational complexity.",
  "scenario": "complex"
}
```

### Test 3.3: Technical Deep Dive

**Request Body:**
```json
{
  "user_input": "Explain how distributed consensus algorithms like Raft and Paxos work, their differences, use cases, and why they are important in distributed systems.",
  "scenario": "complex"
}
```

### Test 3.4: Design Decision

**Request Body:**
```json
{
  "user_input": "Design a caching strategy for a social media platform handling 100M users. Discuss cache invalidation, consistency, distributed caching, and cost optimization.",
  "scenario": "complex"
}
### Test 3.3: Technical Deep Dive
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Explain how distributed consensus algorithms like Raft and Paxos work, their differences, use cases, and why they are important in distributed systems."}'
```

### Test 3.4: Design Decision
```bash

**Request Body (use 3 times):**
```json
{
  "user_input": "What is Docker?"
}
```

**cURL (run 3 times with 2s delay):**
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Design a caching strategy for a social media platform handling 100M users. Discuss cache invalidation, consistency, distributed caching, and cost optimization."}'
```

---

## 4. Cache Effectiveness Tests

Run the same query multiple times to demonstrate cache hits.

### Test 4.1: Cache Hit Demo (Manual)
```bash
# First run - cache miss
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Docker?"}'

# Wait 2 seconds, then run again - should be cache hit
sleep 2
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Docker?"}'

# Third time - cache hit
sleep 2
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Docker?"}'
```

**Expected Metrics**:
- First run: `cache_miss_total{cache="node_cache"}`: +1
- Second run: `cache_hit_total{cache="node_cache"}`: +1
- Third run: `cache_hit_total{cache="node_cache"}`: +1
- `llm_inference_count_total`: Only increments on first run

### Test 4.2: Different Queries (No Cache)
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Kubernetes?"}'

curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Terraform?"}'

curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Ansible?"}'
```


**Request Body:**
```json
{
  "user_input": "What is the capital of France?"
}
```

**URL:** `POST /run?repeat=5`

**Expected Metrics**:
- `agent_execution_count_total`: +5
- `cache_hit_total`: +4 (runs 2-5)
- `cache_miss_total`: +1 (run 1)
- `llm_inference_count_total`: Only from first run
- Response includes benchmark summary

**Watch in Grafana**:
- Cache hit rate spikes to 80%
- Cost growth flatlines after first execution

### Test 5.2: Medium Benchmark (10 runs)

**Request Body:**
```json
{
  "user_input": "Explain containerization benefits"
}
```

**URL:** `POST /run?repeat=10`

**Expected Metrics**:
- `agent_execution_count_total`: +10
- Cache hit rate: 90%
- Average latency drops significantly after first run

### Test 5.3: Large Benchmark (20 runs)

**Request Body:**
```json
{
  "user_input": "What is cloud computing?"
}
```

**URL:** `POST /run?repeat=20`

**Expected Metrics**:
- `agent_execution_count_total`: +20
- Cache hit rate: 95%
- Cost savings clearly visible
- Latency histogram shows two distinct patterns

### Test 5.4: Complex Query Benchmark

**Request Body:**
```json
{
  "user_input": "Compare relational databases versus NoSQL databases considering CAP theorem, scalability, consistency models, and use cases.",
  "scenario": "complex"
}
```

**URL:** `POST /run?repeat=15Cache hit rate: 95%
- Cost savings clearly visible
- Latency histogram shows two distinct patterns

### Test 5.4: Complex Query Benchmark
```bash

**Simple Query (cheap models only):**
```json
{
  "user_input": "What is HTTP?",
  "scenario": "simple"
}
```

**Complex Query (includes expensive model):**
```json
{
  "user_input": "Design a highly available, multi-region distributed system architecture with automatic failover, considering network partitions, data consistency, and cost optimization.",
  "scenario": "complex"
}
---

## 6. Cost Comparison Tests

Demonstrate cost differences between model tiers.

### Test 6.1: Cheap vs Expensive Cost
```bash

**Request Body (run twice):**
```json
{
  "user_input": "What is Git?"
}
```

**Expected**: Second request ~40-50ms

### Test 7.2: Slow Path (Complex + No Cache)

**Request Body:**
```json
{
  "user_input": "Explain quantum computing principles, quantum entanglement, superposition, and potential applications in cryptography and optimization.",
  "scenario": "complex"
}
Demonstrate latency variations.

### Test 7.1: Fast Path (Cached)
```bash
# Prime the cache
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Git?"}'

# Fast cached response
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Git?"}'
```

**Expected**: Second request ~40-50ms

### Test 7.2: Slow Path (Complex + No Cache)
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Explain quantum computing principles, quantum entanglement, superposition, and potential applications in cryptography and optimization."}'
```

**Expected**: 2-5 seconds (expensive model)

---

## 8. Volume Tests (Load Simulation)

Generate volume to see metric aggregations.

### Test 8.1: Rapid Fire Simple Queries
```bash
for i in {1..10}; do
  curl -X POST http://localhost:8000/run \
    -H "Content-Type: application/json" \
    -d "{\"user_input\": \"What is question $i?\"}" &
done
wait
```

**Watch in Grafana**:
- Request rate spike
- Concurrent execution metrics
- HTTP request latency distribution

### Test 8.2: Mixed Workload
```bash
# Simple
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello"}' &

# Retrieval
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Find Docker docs"}' &

# Complex
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Design a distributed cache"}' &

wait
```

---

## 9. Automated Test Script

Run this script to exercise all metrics:

```bash
#!/bin/bash
# Save as: test_all_metrics.sh

echo "🚀 Testing all Grafana metrics..."
echo "Open Grafana at http://localhost:3000"
echo ""

# Simple queries
echo "1️⃣ Simple queries (cheap model)..."
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is 1+1?"}' > /dev/null
sleep 2

# Retrieval query
echo "2️⃣ Retrieval query (RAG)..."
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Find documentation about API"}' > /dev/null
sleep 2

# Complex query
echo "3️⃣ Complex query (expensive model)..."
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Compare microservices vs monoliths"}' > /dev/null
sleep 2

# Cache test
echo "4️⃣ Cache effectiveness (2 runs same query)..."
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Docker?"}' > /dev/null
sleep 2
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Docker?"}' > /dev/null
sleep 2

# Benchmark
echo "5️⃣ Benchmark mode (10 runs)..."
curl -s -X POST "http://localhost:8000/run?repeat=10" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Kubernetes?"}' > /dev/null

echo ""
echo "✅ All tests complete!"
echo "Check Grafana dashboard for metrics"
```

---

## 10. Specific Dashboard Panel Tests

### Panel: LLM Inference Count by Model
```bash
# Generate different model usage
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hi"}' # cheap

curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Analyze distributed consensus algorithms"}' # expensive
```

### Panel: Cache Hit Ratio
```bash
# Use benchmark to show clear cache hits
curl -X POST "http://localhost:8000/run?repeat=20" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Test cache ratio"}'
```

### Panel: Total Cost by Model
```bash
# Run multiple expensive queries to see cost accumulation
for i in {1..5}; do
  curl -X POST http://localhost:8000/run \
    -H "Content-Type: application/json" \
    -d '{"user_input": "Design a scalable system for handling 1M concurrent users"}'
  sleep 3
done
```

### Panel: Agent Execution Latency
```bash
# Benchmark shows latency distribution clearly
curl -X POST "http://localhost:8000/run?repeat=15" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Python?"}'
```

### Panel: Node Execution Breakdown
```bash
# Complex query to see all nodes
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Explain Byzantine fault tolerance, its importance in blockchain, and how it relates to consensus mechanisms like PBFT and Tendermint."}'
```

---

## Grafana Query Examples

Use these PromQL queries in Grafana:

### Cache Hit Rate
```promql
rate(cache_hit_total[5m]) / 
  (rate(cache_hit_total[5m]) + rate(cache_miss_total[5m])) * 100
```

### Average Cost per Request
```promql
rate(llm_cost_total_usd[5m]) / rate(agent_execution_count_total[5m])
```

### Model Usage Distribution
```promql
sum by (model) (rate(llm_inference_count_total[5m]))
```

### P95 Latency
```promql
histogram_quantile(0.95, 
  sum(rate(agent_execution_latency_seconds_bucket[5m])) by (le))
```

---

## Expected Metric Ranges

| Metric | Simple Query | Complex Query | Benchmark (20x) |
|--------|--------------|---------------|-----------------|
| Cost | ~$0.002 | ~$0.008 | ~$0.005 total |
| Latency | ~0.5s | ~2-5s | ~50ms avg (cached) |
| LLM Calls | 2 | 3 | 2-3 (first run only) |
| Cache Hit Rate | N/A (first run) | N/A | ~95% |

---

## Pro Tips

1. **Open Grafana first** before running tests
2. **Set time range** to "Last 5 minutes" in Grafana
3. **Auto-refresh** dashboard every 5 seconds
4. **Run tests slowly** (2-3 seconds between) to see individual spikes
5. **Use benchmark mode** for dramatic cache effectiveness demo
6. **Watch logs**: `docker compose logs agent -f`
7. **Clear cache**: Restart service between test scenarios

---

## Demo Script (5 Minutes)

Perfect for live presentation:

```bash
# 1. Show normal execution
echo "Normal execution..."
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Kubernetes?"}'

sleep 3

# 2. Show cache hit
echo "Cache hit (same query)..."
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Kubernetes?"}'

sleep 3

# 3. Show expensive vs cheap
echo "Expensive model (complex query)..."
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Design a fault-tolerant distributed system"}'

sleep 3

# 4. Big benchmark demo
echo "Benchmark: 20 runs..."
curl -X POST "http://localhost:8000/run?repeat=20" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Explain Docker containers"}' | jq '.benchmark'

# 5. Point to Grafana metrics
echo ""
echo "✅ Check Grafana:"
echo "   - Cache hit rate: 95%"
echo "   - Cost savings: 95%"
echo "   - LLM calls: Flat after first run"
```

---

**Created**: January 17, 2026  
**Purpose**: Test and demonstrate Grafana dashboard metrics  
**Related**: [BENCHMARK_FEATURE.md](BENCHMARK_FEATURE.md), [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
