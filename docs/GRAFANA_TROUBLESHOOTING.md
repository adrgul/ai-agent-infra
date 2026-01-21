# Grafana Metrics Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: Cost Metrics Show "No Data"

**Panels Affected:**
- "Total Cost by Model (Last 1h)"
- "Total Cost (Last 1h)"

**Root Cause:**
You're using **MockLLMClient** which has $0 pricing for all models. Cost metrics are technically working, but all costs are zero.

**Solutions:**

#### Option A: Add OpenAI API Key (Real Costs)
```bash
# Edit .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# Restart services
docker compose restart agent
```

#### Option B: Make MockLLMClient Simulate Costs

Add this to `app/llm/mock_client.py`:

```python
def get_mock_pricing(self, model: str) -> tuple[float, float]:
    """Return mock pricing to simulate costs."""
    pricing = {
        "gpt-3.5-turbo": (0.0001, 0.0002),
        "gpt-4-turbo": (0.001, 0.002),
        "gpt-4": (0.01, 0.03)
    }
    return pricing.get(model, (0.0001, 0.0002))
```

Then ensure the cost tracker uses real pricing even for mock responses.

#### Option C: Accept Zero Costs
Mock client is for demo purposes. Cost panels will remain at $0, which is technically correct for mock responses.

---

### Issue 2: Cache Hit Ratio Shows "NaN"

**Panel:** "Cache Hit Ratio (Triage Node)"

**Root Cause:**
PromQL query divides by zero when there are no cache operations yet:
```promql
sum(rate(cache_hit_total[5m])) / 
  (sum(rate(cache_hit_total[5m])) + sum(rate(cache_miss_total[5m])))
```

When both metrics are 0, you get `0 / 0 = NaN`.

**Solutions:**

#### Solution 1: Run Some Queries First
```bash
# Generate cache activity
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Test query"}'
  
# Run again (cache hit)
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Test query"}'
```

#### Solution 2: Fix PromQL Query (Recommended)

Update the Grafana panel query to handle division by zero:

```promql
(sum(rate(cache_hit_total{cache="node_cache"}[5m])) / 
 (sum(rate(cache_hit_total{cache="node_cache"}[5m])) + 
  sum(rate(cache_miss_total{cache="node_cache"}[5m])) + 0.0001)) 
or vector(0)
```

Or use `clamp_min`:

```promql
clamp_min(
  sum(rate(cache_hit_total{cache="node_cache"}[5m])) / 
  (sum(rate(cache_hit_total{cache="node_cache"}[5m])) + 
   sum(rate(cache_miss_total{cache="node_cache"}[5m]))),
  0
) or vector(0)
```

---

### Issue 3: Agent Execution Latency Shows "NaN"

**Panel:** "Agent Execution Latency (p95)"

**Root Cause:**
Histogram quantile calculation fails when there's no data:
```promql
histogram_quantile(0.95, 
  sum(rate(agent_execution_latency_seconds_bucket[5m])) by (le))
```

**Solutions:**

#### Solution 1: Run Agent First
```bash
# Generate some agent executions
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Test"}'
```

#### Solution 2: Add Default Value

Update panel query:
```promql
histogram_quantile(0.95, 
  sum(rate(agent_execution_latency_seconds_bucket[5m])) by (le))
or vector(0)
```

---

## Quick Fix: Run Test Workload

The easiest solution is to generate some traffic to populate all metrics:

```bash
# Run the test script
./test_benchmark.py

# Or manually:
# 1. Simple query
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Docker?"}'

# 2. Same query (cache hit)
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Docker?"}'

# 3. Benchmark (generates lots of data)
curl -X POST "http://localhost:8000/run?repeat=10" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Kubernetes?"}'
```

Wait 30 seconds, then refresh Grafana. All metrics should populate.

---

## Updated Grafana Dashboard JSON

Here's a fixed version of the dashboard with better "No Data" handling:

### Cache Hit Ratio Panel (Fixed)
```json
{
  "id": 3,
  "title": "Cache Hit Ratio (Triage Node)",
  "type": "singlestat",
  "gridPos": {"h": 4, "w": 6, "x": 0, "y": 8},
  "targets": [
    {
      "expr": "(sum(rate(cache_hit_total{cache=\"node_cache\"}[5m])) / (sum(rate(cache_hit_total{cache=\"node_cache\"}[5m])) + sum(rate(cache_miss_total{cache=\"node_cache\"}[5m])) + 0.0001)) or vector(0)",
      "refId": "A"
    }
  ],
  "format": "percentunit",
  "sparkline": {"show": true},
  "valueName": "current",
  "nullPointMode": "connected"
}
```

### Agent Execution Latency Panel (Fixed)
```json
{
  "id": 4,
  "title": "Agent Execution Latency (p95)",
  "type": "singlestat",
  "gridPos": {"h": 4, "w": 6, "x": 6, "y": 8},
  "targets": [
    {
      "expr": "histogram_quantile(0.95, sum(rate(agent_execution_latency_seconds_bucket[5m])) by (le)) or vector(0)",
      "refId": "A"
    }
  ],
  "format": "s",
  "sparkline": {"show": true},
  "valueName": "current",
  "nullPointMode": "connected"
}
```

### Total Cost Panel (Shows $0 for Mock)
```json
{
  "id": 6,
  "title": "Total Cost (Last 1h)",
  "type": "singlestat",
  "gridPos": {"h": 4, "w": 6, "x": 18, "y": 8},
  "targets": [
    {
      "expr": "sum(increase(llm_cost_total_usd[1h])) or vector(0)",
      "refId": "A"
    }
  ],
  "format": "currencyUSD",
  "sparkline": {"show": true},
  "valueName": "current",
  "decimals": 6
}
```

---

## Verification Checklist

After applying fixes:

- [ ] Run test queries to generate metrics
- [ ] Wait 30 seconds for Prometheus to scrape
- [ ] Refresh Grafana dashboard
- [ ] Cache Hit Ratio shows 0% or actual percentage (not NaN)
- [ ] Agent Execution Latency shows a value (not NaN)
- [ ] Cost shows $0.000000 (if using mock) or actual cost (if using OpenAI)
- [ ] Total Agent Executions shows count
- [ ] LLM Inference Latency shows data

---

## Why These Issues Occur

1. **Mock Client = Zero Cost**: By design, mock responses have no cost
2. **Fresh Start = No Data**: Grafana needs data points to display
3. **Division by Zero = NaN**: PromQL doesn't handle empty metrics well
4. **Time Range**: If time range is "Last 1h" but service just started, no data exists

---

## Recommended: Update Dashboard Permanently

I'll create an updated dashboard file that handles all these cases:

```bash
# Apply the fixed dashboard
# (File will be created next)
docker compose restart grafana
```

---

## Test Each Metric

### Test Cache Hit Ratio
```bash
# Generate cache miss
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Unique query 1"}'

# Generate cache hit
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Unique query 1"}'

# Expected: 50% hit rate
```

### Test Execution Latency
```bash
# Generate multiple executions
for i in {1..5}; do
  curl -X POST http://localhost:8000/run \
    -H "Content-Type: application/json" \
    -d "{\"user_input\": \"Query $i\"}"
done

# Expected: p95 latency appears
```

### Test Cost Metrics
```bash
# With Mock: Always $0
# With OpenAI: Shows actual cost

curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Test"}'

# Expected: $0 (mock) or ~$0.002 (real)
```

---

## Summary

| Issue | Cause | Quick Fix |
|-------|-------|-----------|
| Cost shows "No data" | Mock client has $0 pricing | Run queries (will show $0) or use real API key |
| Cache ratio shows "NaN" | No cache activity yet | Run a query twice |
| Latency shows "NaN" | No executions yet | Run any query |

**Fastest Solution**: Run `./test_benchmark.py` to populate all metrics at once.
