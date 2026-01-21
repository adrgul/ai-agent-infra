#!/bin/bash

echo "🚀 AI Agent Cost Optimization Demo - Quick Start"
echo "================================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Build and start services
echo "📦 Building and starting services..."
echo "   - Agent Demo (FastAPI + LangGraph)"
echo "   - Prometheus (metrics)"
echo "   - Grafana (dashboards)"
echo ""

docker compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo ""
echo "🏥 Health checks:"
echo ""

# Check agent
if curl -s http://localhost:8000/healthz > /dev/null; then
    echo "✅ Agent API: http://localhost:8000"
else
    echo "⚠️  Agent API: Not ready yet (wait a few more seconds)"
fi

# Check prometheus
if curl -s http://localhost:9090/-/ready > /dev/null; then
    echo "✅ Prometheus: http://localhost:9090"
else
    echo "⚠️  Prometheus: Not ready yet"
fi

# Check grafana
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo "✅ Grafana: http://localhost:3000 (admin/admin)"
else
    echo "⚠️  Grafana: Not ready yet"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Try These Demo Commands:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Simple query (cheap model only):"
echo '   curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d '"'"'{"user_input": "Hello"}'"'"' | jq'
echo ""
echo "2️⃣  Retrieval query (RAG flow):"
echo '   curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d '"'"'{"user_input": "Find docs about Docker"}'"'"' | jq'
echo ""
echo "3️⃣  Complex query (expensive model):"
echo '   curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d '"'"'{"user_input": "Explain microservices vs monolithic tradeoffs"}'"'"' | jq'
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 View Dashboards:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   Grafana: http://localhost:3000"
echo "   Prometheus: http://localhost:9090"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛠️  Useful Commands:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   View logs:    docker compose logs -f agent-demo"
echo "   Stop:         docker compose down"
echo "   Restart:      docker compose restart"
echo ""
