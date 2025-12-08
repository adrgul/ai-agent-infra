#!/bin/bash

# LangGraph Mode Toggle Test Script
# This script demonstrates switching between traditional and LangGraph agent modes

set -e

echo "🧪 LangGraph Mode Toggle Test"
echo "=============================="
echo ""

# Function to check which mode is active by looking at logs
check_mode() {
    echo "📋 Checking current mode..."
    docker compose logs backend --tail=5 | grep -q "LangGraph" && echo "✅ LangGraph mode is ACTIVE" || echo "✅ Traditional mode is ACTIVE"
}

# Function to test a briefing request
test_briefing() {
    local city=$1
    echo ""
    echo "🌍 Testing briefing for $city..."
    
    # Make request and capture response
    response=$(curl -s -G "http://localhost:8000/api/briefing" \
        --data-urlencode "city=$city" \
        --data-urlencode "date=$(date -v+2d +%Y-%m-%d)" 2>&1)
    
    # Check logs for execution
    echo "📊 Recent logs:"
    docker compose logs backend --tail=10 | grep -E "(LANGGRAPH|AGENT|NODE|Traditional)" || true
    
    echo ""
}

echo "1️⃣  Current Configuration"
echo "   Checking .env file..."
grep "USE_LANGGRAPH" .env || echo "   USE_LANGGRAPH not set (defaults to true)"

echo ""
echo "2️⃣  Testing Current Mode"
test_briefing "Paris"

echo ""
echo "3️⃣  Mode Switching Instructions"
echo "   To switch to traditional mode:"
echo "   1. Edit .env and set USE_LANGGRAPH=false"
echo "   2. Run: docker compose restart backend"
echo ""
echo "   To switch to LangGraph mode:"
echo "   1. Edit .env and set USE_LANGGRAPH=true"
echo "   2. Run: docker compose restart backend"
echo ""

echo "4️⃣  Verifying LangGraph Dependencies"
echo "   Checking if LangGraph is installed in backend..."
docker compose exec backend pip list | grep -E "(langgraph|langchain)" || echo "   ⚠️  LangGraph packages not found"

echo ""
echo "✅ Test complete!"
echo ""
echo "📚 Documentation:"
echo "   - LANGGRAPH.md - LangGraph architecture and benefits"
echo "   - LANGGRAPH_INTEGRATION_SUMMARY.md - Implementation details"
echo "   - README.md - General usage"
