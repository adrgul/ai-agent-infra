#!/bin/bash
set -e

echo "Starting agent demo application..."

# Run uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
