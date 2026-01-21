#!/bin/bash
# Quick examples for testing the benchmark feature

BASE_URL="http://localhost:8000"

echo "==================================================="
echo "Benchmark Feature - Quick Examples"
echo "==================================================="
echo ""

echo "1️⃣  Single run (normal mode)"
echo "---------------------------------------------------"
echo "curl -X POST ${BASE_URL}/run \\"
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"user_input": "What is 2+2?"}'"'"
echo ""
read -p "Press Enter to execute..."
curl -X POST "${BASE_URL}/run" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is 2+2?"}' | jq -r '.answer'
echo ""
echo ""

echo "2️⃣  Benchmark with repeat=5"
echo "---------------------------------------------------"
echo "curl -X POST ${BASE_URL}/run?repeat=5 \\"
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"user_input": "What is the capital of France?"}'"'"
echo ""
read -p "Press Enter to execute..."
curl -X POST "${BASE_URL}/run?repeat=5" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is the capital of France?"}' | jq '{answer: .answer, benchmark: .benchmark}'
echo ""
echo ""

echo "3️⃣  Benchmark with repeat=10 (complex query)"
echo "---------------------------------------------------"
echo "curl -X POST ${BASE_URL}/run?repeat=10 \\"
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"user_input": "Explain machine learning"}'"'"
echo ""
read -p "Press Enter to execute..."
curl -X POST "${BASE_URL}/run?repeat=10" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Explain machine learning"}' | jq '{
    answer: .answer[:100] + "...",
    benchmark: .benchmark,
    cache_hit_rate: (
      (.benchmark.cache_hits.node_cache / 
       (.benchmark.cache_hits.node_cache + .benchmark.cache_misses.node_cache)) * 100 | round
    )
  }'
echo ""
echo ""

echo "4️⃣  Large benchmark (repeat=20) - Watch metrics in Grafana!"
echo "---------------------------------------------------"
echo "Open Grafana: http://localhost:3000 (admin/admin)"
echo "Watch metrics while this runs..."
echo ""
read -p "Press Enter to execute..."
curl -X POST "${BASE_URL}/run?repeat=20" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What are the benefits of containerization?"}' | jq '.benchmark'
echo ""
echo ""

echo "✅ Done!"
echo ""
echo "💡 Next steps:"
echo "   - Check application logs: docker compose logs agent -f"
echo "   - View metrics: http://localhost:9090"
echo "   - View dashboards: http://localhost:3000"
echo "   - Read docs: BENCHMARK_FEATURE.md"
