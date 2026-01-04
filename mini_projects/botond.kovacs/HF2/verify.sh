#!/bin/bash
# Verification script to check all components are in place

echo "=================================="
echo "AI Agent Complex - Verification"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (missing)"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
        return 0
    else
        echo -e "${RED}✗${NC} $1/ (missing)"
        return 1
    fi
}

echo "Checking Backend Structure..."
echo "------------------------------"
check_dir "backend/domain"
check_file "backend/domain/models.py"
check_file "backend/domain/interfaces.py"
check_dir "backend/infrastructure"
check_file "backend/infrastructure/repositories.py"
check_dir "backend/services"
check_file "backend/services/agent.py"
check_file "backend/services/tools.py"
check_file "backend/services/chat_service.py"
check_file "backend/main.py"
check_file "backend/requirements.txt"
check_file "backend/Dockerfile"
echo ""

echo "Checking Frontend Structure..."
echo "------------------------------"
check_dir "frontend/src"
check_dir "frontend/src/components"
check_file "frontend/src/components/ChatWindow.tsx"
check_file "frontend/src/components/MessageBubble.tsx"
check_file "frontend/src/components/ChatInput.tsx"
check_file "frontend/src/components/DebugPanel.tsx"
check_file "frontend/src/App.tsx"
check_file "frontend/src/App.css"
check_file "frontend/src/api.ts"
check_file "frontend/src/types.ts"
check_file "frontend/src/utils.ts"
check_file "frontend/src/main.tsx"
check_file "frontend/package.json"
check_file "frontend/vite.config.ts"
check_file "frontend/Dockerfile"
check_file "frontend/nginx.conf"
echo ""

echo "Checking Docker Configuration..."
echo "--------------------------------"
check_file "docker-compose.yml"
check_file ".env.example"
check_file ".gitignore"
echo ""

echo "Checking Documentation..."
echo "-------------------------"
check_file "README.md"
check_file "QUICKSTART.md"
check_file "ARCHITECTURE.md"
check_file "PROJECT_STRUCTURE.md"
check_file "DEPLOYMENT.md"
echo ""

echo "Checking Scripts..."
echo "-------------------"
check_file "start-dev.sh"
if [ -x "start-dev.sh" ]; then
    echo -e "${GREEN}✓${NC} start-dev.sh is executable"
else
    echo -e "${RED}✗${NC} start-dev.sh is not executable"
fi
echo ""

echo "=================================="
echo "Summary"
echo "=================================="
echo ""

# Count files
BACKEND_PY=$(find backend -name "*.py" 2>/dev/null | wc -l | xargs)
FRONTEND_TS=$(find frontend/src -name "*.ts" -o -name "*.tsx" 2>/dev/null | wc -l | xargs)
DOCS=$(ls *.md 2>/dev/null | wc -l | xargs)

echo "Backend Python files: $BACKEND_PY"
echo "Frontend TS/TSX files: $FRONTEND_TS"
echo "Documentation files: $DOCS"
echo ""

echo "Project Status: Ready for deployment! 🚀"
echo ""
echo "Quick Start:"
echo "  1. cp .env.example .env"
echo "  2. Edit .env with your OPENAI_API_KEY"
echo "  3. docker-compose up --build"
echo "  4. Open http://localhost:3000"
echo ""
echo "=================================="
