#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "🛑 AI Weather Agent - Stopping Services"
echo "========================================"

docker compose down -v

echo ""
echo "✅ All services stopped and removed."
echo ""
