#!/bin/bash

echo "🧪 Testing Benchmark Feature"
echo "============================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"

echo -e "${BLUE}Test 1: Single run (no repeat parameter)${NC}"
echo "Request: POST /run"
curl -s -X POST "${API_URL}/run" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is the capital of France?"}' \
  | jq '.answer, .benchmark'

echo ""
echo ""

echo -e "${BLUE}Test 2: Benchmark with repeat=5${NC}"
echo "Request: POST /run?repeat=5"
curl -s -X POST "${API_URL}/run?repeat=5" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is the capital of France?"}' \
  | jq '{answer: .answer, benchmark: .benchmark}'

echo ""
echo ""

echo -e "${BLUE}Test 3: Benchmark with repeat=10${NC}"
echo "Request: POST /run?repeat=10"
curl -s -X POST "${API_URL}/run?repeat=10" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Explain quantum computing"}' \
  | jq '{answer: .answer, benchmark: .benchmark}'

echo ""
echo ""

echo -e "${GREEN}✅ Tests completed${NC}"
echo ""
echo "Check the application logs to see benchmark progress messages like:"
echo "  'Benchmark run 7/20 – cache hit'"
