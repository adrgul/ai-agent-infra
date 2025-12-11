#!/bin/bash
# Local development startup script
# Run: ./start-dev.sh (from benketibor root)

set -e

echo "🚀 KnowledgeRouter - Local Development"
echo "======================================"

# Check prerequisites
echo "✓ Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install from https://www.python.org/"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Node.js not found. Install from https://nodejs.org/"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not set"
    echo "   Run: export OPENAI_API_KEY='sk-...'"
    exit 1
fi

echo "✓ Prerequisites OK"
echo ""

# Backend setup
echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating venv..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

echo "Creating data directories..."
mkdir -p data/users data/sessions data/files

echo "✓ Backend ready"
echo ""

# Start backend
echo "Starting backend (Django)..."
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!
echo "Backend running on PID $BACKEND_PID (http://localhost:8001)"
echo ""

cd ..

# Frontend setup
echo "Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install -q
fi

echo "✓ Frontend ready"
echo ""

# Start frontend
echo "Starting frontend (HTTP Server)..."
npx http-server . -p 3000 &
FRONTEND_PID=$!
echo "Frontend running on PID $FRONTEND_PID (http://localhost:3000)"
echo ""

cd ..

echo "======================================"
echo "✅ KnowledgeRouter is running!"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8001/api/"
echo ""
echo "Press Ctrl+C to stop all services"
echo "======================================"

# Cleanup on exit
trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

wait
