#!/bin/bash
# 🧪 API végpontok tesztelése

BASE_URL="http://localhost:3000/api"

# Szín kódok
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}🧪 API TESZT SUITE${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}\n"

# Backend ellenőrzése
echo -e "${YELLOW}Backend ellenőrzése...${NC}"
if ! curl -s "$BASE_URL/history" >/dev/null 2>&1; then
    echo -e "${RED}❌ Backend nem válaszol (3000-es port)${NC}"
    echo -e "    Indítsd el: ${CYAN}./start.sh${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backend elérhető${NC}\n"

# Test 1: History végpont
echo -e "${CYAN}TEST 1: History végpont${NC}"
echo -e "GET ${BASE_URL}/history\n"
RESPONSE=$(curl -s "$BASE_URL/history" | python3 -m json.tool)
echo "$RESPONSE" | head -20
if echo "$RESPONSE" | grep -q "entries"; then
    echo -e "${GREEN}✓ PASS${NC}\n"
else
    echo -e "${RED}❌ FAIL${NC}\n"
fi

# Test 2: Briefing - Parks
echo -e "${CYAN}TEST 2: Briefing - Parks in Budapest${NC}"
echo -e "GET ${BASE_URL}/briefing?city=budapest&activity=parks\n"
RESPONSE=$(curl -s "${BASE_URL}/briefing?city=budapest&activity=parks" | python3 -m json.tool)
echo "$RESPONSE" | head -40
if echo "$RESPONSE" | grep -q "briefing"; then
    echo -e "${GREEN}✓ PASS${NC}\n"
else
    echo -e "${RED}❌ FAIL${NC}\n"
fi

# Test 3: Briefing - Cafes
echo -e "${CYAN}TEST 3: Briefing - Cafes in Budapest${NC}"
echo -e "GET ${BASE_URL}/briefing?city=budapest&activity=cafes\n"
RESPONSE=$(curl -s "${BASE_URL}/briefing?city=budapest&activity=cafes" | python3 -m json.tool)
echo "$RESPONSE" | head -40
if echo "$RESPONSE" | grep -q "briefing"; then
    echo -e "${GREEN}✓ PASS${NC}\n"
else
    echo -e "${RED}❌ FAIL${NC}\n"
fi

# Test 4: Briefing - Museums
echo -e "${CYAN}TEST 4: Briefing - Museums in Budapest${NC}"
echo -e "GET ${BASE_URL}/briefing?city=budapest&activity=museums\n"
RESPONSE=$(curl -s "${BASE_URL}/briefing?city=budapest&activity=museums" | python3 -m json.tool)
echo "$RESPONSE" | head -40
if echo "$RESPONSE" | grep -q "briefing"; then
    echo -e "${GREEN}✓ PASS${NC}\n"
else
    echo -e "${RED}❌ FAIL${NC}\n"
fi

# Test 5: Briefing - Random City & Activity
echo -e "${CYAN}TEST 5: Briefing - Random City & Activity${NC}"
echo -e "GET ${BASE_URL}/briefing?city=paris&activity=shopping\n"
RESPONSE=$(curl -s "${BASE_URL}/briefing?city=paris&activity=shopping" | python3 -m json.tool)
echo "$RESPONSE" | head -40
if echo "$RESPONSE" | grep -q "briefing"; then
    echo -e "${GREEN}✓ PASS${NC}\n"
else
    echo -e "${RED}❌ FAIL${NC}\n"
fi

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ TESZTELÉS KÉSZ${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}\n"
echo -e "${CYAN}Frontend: http://localhost:5173${NC}"
echo -e "${CYAN}Backend:  http://localhost:3000${NC}\n"
