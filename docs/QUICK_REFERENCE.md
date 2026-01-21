# Benchmark Feature - Quick Reference

## Basic Usage

```bash
# Single run (normal)
POST /run
{"user_input": "your query"}

# Benchmark mode
POST /run?repeat=20
{"user_input": "your query"}
```

## Quick Test

```bash
curl -X POST "http://localhost:8000/run?repeat=10" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Docker?"}' | jq '.benchmark'
```

## Response Format

```json
{
  "answer": "Docker is...",
  "benchmark": {
    "repeat": 10,
    "total_time_seconds": 2.1,
    "avg_time_per_run_seconds": 0.21,
    "cache_hits": {"node_cache": 9, "embedding_cache": 9},
    "cache_misses": {"node_cache": 1, "embedding_cache": 1}
  }
}
```

## What to Expect

| Run # | Cache | LLM Calls | Cost | Time |
|-------|-------|-----------|------|------|
| 1 | Miss | 2-3 | $0.005 | ~2s |
| 2-20 | Hit | 0 | $0 | ~50ms |

**Cache Hit Rate**: ~95% (19/20 runs)
**Cost Savings**: ~95% vs. no caching

## Grafana Metrics

Watch these during benchmark:

1. **cache_hit_total** ↗️ Rising fast
2. **llm_inference_count_total** → Flat after run 1
3. **llm_cost_total_usd** → Flat after run 1
4. **agent_execution_count_total** ↗️ Linear increase

## Common Commands

```bash
# Test single run
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello"}' | jq '.answer'

# Small benchmark (5 runs)
curl -X POST "http://localhost:8000/run?repeat=5" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is AI?"}' | jq '.benchmark'

# Medium benchmark (10 runs)
curl -X POST "http://localhost:8000/run?repeat=10" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Explain caching"}' | jq

# Large benchmark (20 runs) - watch Grafana!
curl -X POST "http://localhost:8000/run?repeat=20" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Benefits of Docker?"}' | jq '.benchmark'

# Extract cache hit rate
curl -s -X POST "http://localhost:8000/run?repeat=10" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Test"}' | \
  jq '.benchmark | 
    (.cache_hits.node_cache / 
     (.cache_hits.node_cache + .cache_misses.node_cache) * 100 
     | round)'
```

## View Logs

```bash
# Follow application logs
docker compose logs agent -f

# Search for benchmark messages
docker compose logs agent | grep "Benchmark run"

# Last 50 lines
docker compose logs agent --tail 50
```

## Test Scripts

```bash
# Python test suite
./test_benchmark.py

# Interactive examples
./examples_benchmark.sh

# Shell tests
./test_benchmark.sh
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No benchmark in response | Add `?repeat=N` to URL (not in body) |
| All cache misses | Restart service to clear cache |
| Timeout | Reduce repeat count or increase timeout |
| 422 Error | Check `repeat` is between 1-1000 |

## URLs

- **API**: http://localhost:8000
- **Metrics**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Docs**: http://localhost:8000/docs

## Parameter Limits

- **Min repeat**: 1 (same as no parameter)
- **Max repeat**: 1000
- **Default**: None (single run)

## Demo Talking Points

1. **First run**: "See the cache miss? LLM had to do real work."
2. **Second run**: "Cache hit! Instant response, zero cost."
3. **Grafana**: "Watch how the cost line goes flat."
4. **Savings**: "95% cost reduction with caching."
5. **Speed**: "50ms vs 2000ms - 40x faster!"

## Full Documentation

See [BENCHMARK_FEATURE.md](BENCHMARK_FEATURE.md) for complete details.
