#!/bin/bash
# Quick start script for local development

echo "Starting AI Agent Demo - Local Development"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set"
    echo "Please run: export OPENAI_API_KEY='your_key_here'"
    exit 1
fi

echo ""
echo "✓ Prerequisites checked"
echo ""

# Backend setup
echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing backend dependencies..."
pip install -q -r requirements.txt

echo "Creating data directories..."
mkdir -p data/users data/sessions data/files

echo ""
echo "✓ Backend ready"
echo ""

# Start backend in background
echo "Starting backend server..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "Backend running on PID $BACKEND_PID"

cd ..

# Frontend setup
echo ""
echo "Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo ""
echo "✓ Frontend ready"
echo ""

# Start frontend
echo "Starting frontend server..."
npm run dev &
FRONTEND_PID=$!
echo "Frontend running on PID $FRONTEND_PID"

cd ..

echo ""
echo "=========================================="
echo "✓ AI Agent Demo is running!"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=========================================="

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
