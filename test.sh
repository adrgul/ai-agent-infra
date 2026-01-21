#!/bin/bash

echo "🧪 Testing AI Agent Cost Optimization Demo"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8000"

# Function to test endpoint
test_scenario() {
    local name=$1
    local payload=$2
    
    echo "Testing: $name"
    echo "Payload: $payload"
    
    response=$(curl -s -X POST "$BASE_URL/run" \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    # Extract key metrics
    answer=$(echo $response | jq -r '.answer' 2>/dev/null)
    classification=$(echo $response | jq -r '.debug.classification' 2>/dev/null)
    total_cost=$(echo $response | jq -r '.debug.cost_report.total_cost_usd' 2>/dev/null)
    nodes=$(echo $response | jq -r '.debug.nodes_executed[]' 2>/dev/null | tr '\n' ' ')
    cache_hits=$(echo $response | jq -r '.debug.cache' 2>/dev/null)
    
    echo "  Classification: $classification"
    echo "  Nodes executed: $nodes"
    echo "  Total cost: \$$total_cost"
    echo "  Answer: ${answer:0:100}..."
    echo ""
}

echo "1. Simple Query (should use cheap model only)"
test_scenario "Simple" '{"user_input": "What time is it?"}'

echo "2. Retrieval Query (should trigger RAG flow)"
test_scenario "Retrieval" '{"user_input": "Find information about Kubernetes"}'

echo "3. Complex Query (should use expensive model)"
test_scenario "Complex" '{"user_input": "Analyze the architectural differences between microservices and monolithic systems"}'

echo "4. Cached Query (repeat #1 - should hit cache)"
test_scenario "Cached Simple" '{"user_input": "What time is it?"}'

echo "=========================================="
echo "✅ Tests complete!"
echo ""
echo "Check Grafana at http://localhost:3000 to see:"
echo "  - Cost breakdown by model"
echo "  - Cache hit ratios"
echo "  - Latency metrics"
echo ""
