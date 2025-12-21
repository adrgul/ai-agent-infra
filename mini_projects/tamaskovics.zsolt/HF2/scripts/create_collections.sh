#!/usr/bin/env bash
set -euo pipefail

QDRANT_URL="${QDRANT_URL:-http://127.0.0.1:6333}"
VECTOR_SIZE="${VECTOR_SIZE:-1536}"
DOMAINS=(hr compliance it ops general)

for c in "${DOMAINS[@]}"; do
  echo -n "==> ensure collection: $c ... "
  code="$(curl -sS -o /dev/null -w "%{http_code}" \
    -X PUT "$QDRANT_URL/collections/$c" \
    -H 'Content-Type: application/json' \
    -d "{\"vectors\":{\"size\":${VECTOR_SIZE},\"distance\":\"Cosine\"}}"
  )"

  case "$code" in
    200|201) echo "OK" ;;
    409)     echo "EXISTS" ;;
    *)       echo "ERROR ($code)"; exit 1 ;;
  esac
done
