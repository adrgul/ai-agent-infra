#!/bin/bash

echo "🔧 Populating Grafana Metrics"
echo "=============================="
echo ""
echo "This will generate traffic to populate all dashboard panels."
echo ""

sleep 2

echo "1️⃣  Generating cache miss..."
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Docker?"}' > /dev/null
echo "✅ Done"
sleep 1

echo "2️⃣  Generating cache hit..."
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Docker?"}' > /dev/null
echo "✅ Done"
sleep 1

echo "3️⃣  Running benchmark (generates lots of data)..."
curl -s -X POST "http://localhost:8000/run?repeat=10" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Kubernetes?"}' > /dev/null
echo "✅ Done"
sleep 1

echo "4️⃣  Complex query (shows model tiers)..."
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Analyze the trade-offs between microservices and monolithic architectures"}' > /dev/null
echo "✅ Done"
sleep 1

echo ""
echo "✅ All metrics populated!"
echo ""
echo "📊 Now check Grafana:"
echo "   1. Open http://localhost:3000"
echo "   2. Refresh the dashboard (or wait 10s for auto-refresh)"
echo "   3. All panels should show data (not NaN)"
echo ""
echo "Expected Results:"
echo "   - Cache Hit Ratio: ~91% (10/11 cache hits)"
echo "   - Agent Executions: 12 total"
echo "   - Cost: $0.000000 (MockLLM has zero cost)"
echo "   - Latency: Shows actual values"
