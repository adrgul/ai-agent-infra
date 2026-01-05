#!/bin/bash
set -e

echo "🐳 RAG Agent - Docker Compose Start"

# Check OPENAI_API_KEY
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY environment variable is not set"
    echo "   Please set it before running: export OPENAI_API_KEY='sk-...'"
    exit 1
fi

# Build and start
docker-compose up --build

echo "✅ RAG Agent is running!"
echo "   Frontend: http://localhost:3000"
