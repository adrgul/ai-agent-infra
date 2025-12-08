#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "🚀 AI Weather Agent - Starting Services"
echo "========================================"

# Check if .env exists, if not create from sample
if [ ! -f .env ]; then
  echo "📝 No .env found. Creating from .env.sample..."
  cp .env.sample .env
  echo "⚠️  Please edit .env to set OPENAI_API_KEY before first use."
  echo ""
fi

# Create data directory if it doesn't exist
echo "📁 Ensuring data directory exists..."
mkdir -p data

# Build Docker images
echo ""
echo "🔨 Building Docker images..."
docker compose build --pull

# Start services
echo ""
echo "▶️  Starting services..."
docker compose up -d

# Wait for backend health
echo ""
echo "⏳ Waiting for backend to be healthy..."
for i in {1..30}; do
  if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Backend is healthy!"
    break
  fi
  sleep 1
  if [ "$i" -eq 30 ]; then
    echo "❌ Backend did not become healthy in time." >&2
    echo "   Check logs with: docker compose logs backend"
    exit 1
  fi
done

echo ""
echo "✨ All services started successfully!"
echo ""
echo "📍 Access the application:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📊 View logs:"
echo "   docker compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   ./scripts/down.sh"
echo ""
