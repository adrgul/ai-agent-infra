#!/bin/bash

# KnowledgeRouter Startup Script
# Starts both Backend (FastAPI) and Frontend (Next.js)

# Function to handle script exit
cleanup() {
    echo -e "\n🛑 Shutting down services..."
    # Kill backend process if it exists
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    # Kill all child processes
    pkill -P $$ 2>/dev/null
    exit 0
}

# Trap interrupt signals (Ctrl+C)
trap cleanup SIGINT SIGTERM EXIT

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting KnowledgeRouter..."

# 1. Start Backend
echo "📦 Starting Backend (FastAPI)..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to create virtual environment"
        exit 1
    fi
fi

source venv/bin/activate

# Upgrade pip first
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install/upgrade requirements
echo "Installing/updating dependencies..."
pip install --upgrade -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to install backend dependencies"
    exit 1
fi

# Run backend in background
echo "Starting backend server..."
python main.py > ../backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Error: Backend failed to start. Check backend.log for details:"
    tail -20 ../backend.log
    exit 1
fi

# Check if backend is responding
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend running on PID $BACKEND_PID (http://localhost:8000)"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "⚠️  Warning: Backend started but health check failed. Continuing anyway..."
    else
        sleep 1
    fi
done

cd ..

# 2. Start Frontend
echo "🎨 Starting Frontend (Next.js)..."
cd frontend

if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found in frontend directory"
    exit 1
fi

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install frontend dependencies"
        exit 1
    fi
fi

# Run frontend in foreground so we can see logs and keep script running
echo "✅ Starting frontend development server..."
npm run dev

# The script waits here until frontend is stopped
