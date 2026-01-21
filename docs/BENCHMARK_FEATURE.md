# Benchmark Feature Documentation

## Overview

The `/run` endpoint now supports repeated agent executions for benchmarking cache performance and cost optimization. This feature demonstrates how caching dramatically reduces LLM inference costs and latency on subsequent runs with the same input.

## Usage

### Single Run (Normal Behavior)

```bash
POST /run
Content-Type: application/json

{
  "user_input": "What is the capital of France?"
}
```

**Response:**
```json
{
  "answer": "Paris is the capital of France.",
  "debug": { ... },
  "benchmark": null
}
```

### Benchmark Mode (Repeated Runs)

```bash
POST /run?repeat=20
Content-Type: application/json

{
  "user_input": "What is the capital of France?"
}
```

**Response:**
```json
{
  "answer": "Paris is the capital of France.",
  "debug": { ... },
  "benchmark": {
    "repeat": 20,
    "total_time_seconds": 12.4,
    "avg_time_per_run_seconds": 0.62,
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

## Parameters

- **repeat** (optional): Number of times to execute the agent (1-1000)
  - If not provided or `repeat=1`: Normal single execution
  - If `repeat>1`: Benchmark mode with repeated executions

## Behavior

When `repeat=N` is provided:

1. **Sequential Execution**: Runs the agent N times sequentially (not parallel)
2. **Shared Cache**: All runs share the same cache instances (node_cache and embedding_cache)
3. **Metrics Recording**: Each run increments Prometheus metrics normally
4. **Cache Tracking**: Accumulates cache hits/misses across all runs
5. **Response**: Returns only the LAST run's answer plus benchmark summary

## Cache Performance Demonstration

The benchmark feature clearly demonstrates cache effectiveness:

**First Run (Cache Miss):**
- Full LLM inference required
- All nodes execute normally
- Cost: Full model inference cost
- Time: Typical agent execution time

**Subsequent Runs (Cache Hits):**
- Cached results returned instantly
- No LLM inference calls
- Cost: ~$0
- Time: <50ms (cache lookup only)

## Example: Cost Savings

```bash
# Run 20 times with caching enabled
curl -X POST "http://localhost:8000/run?repeat=20" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Explain quantum entanglement"}'
```

**Expected Results:**
- Run 1: ~$0.0050 (GPT-4 inference)
- Runs 2-20: ~$0 (cache hits)
- Total cost: ~$0.0050 (95% savings vs. 20 independent calls)
- Total time: ~15s (vs. ~200s without caching)

## Prometheus Metrics

The benchmark feature uses existing metrics - no special benchmark counters:

### Key Metrics to Watch

1. **agent_execution_count_total**: Increments for each run (should show 20 after repeat=20)
2. **cache_hit_total**: Shows cumulative cache hits rising rapidly
3. **cache_miss_total**: Shows only 1 miss (first run)
4. **llm_inference_count_total**: Shows only 1 inference (first run), then flatlines
5. **llm_cost_total_usd**: Cost growth slows dramatically after first run

### Grafana Visualization

After running a benchmark with `repeat=20`, Grafana dashboards will clearly show:

- **Cache hit rate**: Spikes to 95%+ after first execution
- **LLM cost over time**: Sharp initial cost, then flat (no new costs)
- **Agent execution count**: Linear increase (all 20 runs counted)
- **Response latency**: First run slow, subsequent runs <100ms

## Logging

Each benchmark run produces a log entry:

```
INFO: Benchmark mode: will execute 20 times
INFO: Benchmark run 1/20 – cache miss – 2.134s
INFO: Benchmark run 2/20 – cache hit – 0.042s
INFO: Benchmark run 3/20 – cache hit – 0.038s
...
INFO: Benchmark run 20/20 – cache hit – 0.041s
INFO: Benchmark completed: 20 runs in 3.47s (avg 0.173s/run), node_cache hits=19, embedding_cache hits=19
```

## Testing

### Quick Test
```bash
# Test with 5 runs
curl -X POST "http://localhost:8000/run?repeat=5" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is the capital of France?"}' \
  | jq '.benchmark'
```

### Automated Test Script
```bash
./test_benchmark.py
```

### Manual Testing Workflow
1. Start the application: `./start.sh`
2. Wait for services to be ready (~10 seconds)
3. Run first benchmark: `repeat=10` with simple query
4. Check Grafana: http://localhost:3000 (admin/admin)
5. Observe cache hit metrics rising
6. Run second benchmark: `repeat=20` with different query
7. Compare cost metrics before/after

## Implementation Details

### Code Structure

The implementation splits the endpoint into three functions:

1. **`run_agent()`**: Main endpoint handler
   - Accepts `repeat` query parameter
   - Routes to single or benchmark mode

2. **`_run_single()`**: Normal single execution
   - Original behavior preserved
   - Returns response without benchmark data

3. **`_run_benchmark()`**: Benchmark execution loop
   - Executes agent N times sequentially
   - Tracks cache statistics
   - Returns last run's answer + benchmark summary

### Cache Statistics Tracking

Cache hits/misses are tracked by inspecting the `cache_hits` field in the agent state:

```python
cache_stats = final_state.get("cache_hits", {})
node_cache_hit = cache_stats.get("node_cache", 0)
embedding_cache_hit = cache_stats.get("embedding_cache", 0)
```

The first run will have zero cache hits (cache miss), while subsequent runs should show cache hits.

### Sequential Execution (Teaching Clarity)

The implementation uses an explicit loop for educational purposes:

```python
for run_idx in range(1, repeat + 1):
    # Execute agent
    final_state = await graph.ainvoke(initial_state)
    # Track metrics
    # Log progress
```

This makes the code easy to understand during live demos and workshops.

## Use Cases

### 1. Live Demo: Cache Effectiveness
Show stakeholders how caching reduces costs by 90%+ on repeated queries.

### 2. Performance Testing
Measure cache lookup performance vs. LLM inference performance.

### 3. Cost Analysis
Demonstrate ROI of implementing caching in production systems.

### 4. Load Testing
Test cache behavior under repeated load (though not parallel load).

### 5. Teaching Tool
Educational demonstration of caching principles in LLM applications.

## Limitations

1. **Sequential Only**: Runs are not parallelized (by design for clarity)
2. **Same Input**: All runs use identical input (no variation)
3. **In-Memory Cache**: Cache resets on service restart
4. **No Warmup**: First run always cache miss (expected behavior)
5. **Single Metric Context**: All runs share same Prometheus label context

## Best Practices

1. **Start Small**: Use `repeat=5` for quick tests
2. **Watch Logs**: Monitor for cache hit/miss patterns
3. **Check Grafana**: Visualize metrics in real-time during benchmark
4. **Clear Cache**: Restart service to clear cache between different tests
5. **Vary Queries**: Test with different query types (simple/complex/retrieval)

## API Examples

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/run?repeat=20",
    json={"user_input": "What is machine learning?"}
)

benchmark = response.json()["benchmark"]
print(f"Avg time: {benchmark['avg_time_per_run_seconds']}s")
print(f"Cache hit rate: {benchmark['cache_hits']['node_cache'] / benchmark['repeat'] * 100}%")
```

### cURL
```bash
curl -X POST "http://localhost:8000/run?repeat=10" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Explain Docker"}' \
  | jq '.benchmark'
```

### JavaScript/Fetch
```javascript
const response = await fetch('http://localhost:8000/run?repeat=15', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_input: 'What is Kubernetes?' })
});

const data = await response.json();
console.log('Benchmark:', data.benchmark);
```

## Troubleshooting

### Benchmark returns null
- Check that `repeat > 1` in query parameter
- Verify parameter is passed as query param, not in body

### No cache hits after first run
- Check that cache TTL hasn't expired (default 300s)
- Verify input is exactly the same between runs
- Check logs for cache key generation

### Performance worse than expected
- Verify Docker resources (CPU/memory)
- Check for other system load
- Review cache size limits in config

## Related Files

- **Implementation**: `app/main.py` - Main endpoint and benchmark logic
- **Cache**: `app/cache/memory_cache.py` - In-memory cache with TTL
- **Metrics**: `app/observability/metrics.py` - Prometheus metrics definitions
- **Tests**: `test_benchmark.py` - Automated validation script
- **Config**: `app/config.py` - Cache configuration settings
