#!/usr/bin/env bash
set -euo pipefail

# load local env if present
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

QDRANT_URL="${QDRANT_URL:-http://127.0.0.1:6333}"

docker compose -f compose.yml up -d

echo "Waiting for Qdrant..."
for i in {1..60}; do
  if curl -fsS "$QDRANT_URL/readyz" >/dev/null; then
    echo "Qdrant OK"
    break
  fi
  sleep 1
done

./scripts/create_collections.sh

# Python venv + deps (idempotens)
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
./.venv/bin/pip install -U pip >/dev/null
./.venv/bin/pip install -r requirements.txt >/dev/null

# Ingest only if API key present
if [ -n "${OPENAI_API_KEY:-}" ] && [ "${OPENAI_API_KEY:-}" != "CHANGEME" ]; then
  echo "Running ingest..."
  ./.venv/bin/python scripts/ingest.py
else
  echo "SKIP ingest: OPENAI_API_KEY nincs beállítva (exportáld vagy tedd .env-be - a .env úgyis .gitignore)."
fi
