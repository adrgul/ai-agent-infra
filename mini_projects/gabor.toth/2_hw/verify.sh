#!/bin/bash

# Verification script for RAG Agent application

echo "🔍 RAG Agent - Verification Checklist"
echo "====================================="
echo ""

ERRORS=0

# Check Python 3
echo "✓ Checking Python..."
if ! python3 --version >/dev/null 2>&1; then
    echo "  ✗ Python 3 not found"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✓ Python 3 installed"
fi

# Check Node.js
echo "✓ Checking Node.js..."
if ! node --version >/dev/null 2>&1; then
    echo "  ✗ Node.js not found"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✓ Node.js installed"
fi

# Check file structure
echo "✓ Checking file structure..."
REQUIRED_FILES=(
    "backend/main.py"
    "backend/requirements.txt"
    "backend/domain/models.py"
    "backend/domain/interfaces.py"
    "backend/infrastructure/embedding.py"
    "backend/infrastructure/vector_store.py"
    "backend/infrastructure/chunker.py"
    "backend/infrastructure/extractors.py"
    "backend/services/upload_service.py"
    "backend/services/rag_agent.py"
    "backend/services/chat_service.py"
    "frontend/package.json"
    "frontend/src/main.tsx"
    "frontend/src/components/App.tsx"
    "docker-compose.yml"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "  ✗ Missing: $file"
        ERRORS=$((ERRORS + 1))
    fi
done

if [ $ERRORS -eq 0 ]; then
    echo "  ✓ All required files present"
fi

# Check directories
echo "✓ Checking data directories..."
mkdir -p data/users data/sessions data/uploads data/derived data/chroma_db
echo "  ✓ Data directories ready"

# Check OpenAI API key
echo "✓ Checking OPENAI_API_KEY..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "  ⚠ OPENAI_API_KEY not set"
    echo "    Run: export OPENAI_API_KEY='sk-...'"
else
    echo "  ✓ OPENAI_API_KEY is set"
fi

# Summary
echo ""
echo "====================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ All checks passed!"
    echo ""
    echo "Next steps:"
    echo "1. Set OPENAI_API_KEY: export OPENAI_API_KEY='sk-...'"
    echo "2. Run: ./start-dev.sh"
    exit 0
else
    echo "❌ $ERRORS error(s) found"
    exit 1
fi
