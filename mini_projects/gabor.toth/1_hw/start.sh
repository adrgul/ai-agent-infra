#!/bin/bash
# 🚀 Teljes alkalmazás indítása egy parancsban

# Dinamikus elérési út - működik bármelyik mappából
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$SCRIPT_DIR"
VENV="$HOME/.venv"

# Szín kódok
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# PID fájl tárolása
PID_FILE="$BASE_DIR/.server_pids"

# Cleanup függvény
cleanup() {
    echo -e "${YELLOW}🛑 Leállítás...${NC}"
    
    # PIDs olvasása és leállítása
    if [ -f "$PID_FILE" ]; then
        while IFS= read -r pid; do
            if [ ! -z "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null
            fi
        done < "$PID_FILE"
        rm "$PID_FILE"
    fi
    
    # Portok felszabadítása
    echo -e "${YELLOW}Portok felszabadítása...${NC}"
    if command -v fuser &> /dev/null; then
        fuser -k 3000/tcp 5173/tcp 2>/dev/null || true
    else
        lsof -i :3000,:5173 2>/dev/null | awk 'NR!=1 {print $2}' | sort -u | xargs kill -9 2>/dev/null || true
    fi
    sleep 1
    
    echo -e "${GREEN}✅ Összes szerver leállítva${NC}"
    exit 0
}

# Trap a Ctrl+C-re
trap cleanup SIGINT SIGTERM

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 Város Briefing Alkalmazás Indítása${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"

# 1. Portok ellenőrzése és felszabadítása
echo -e "\n${YELLOW}1️⃣ Portok ellenőrzése...${NC}"
for port in 3000 5173; do
    if lsof -i :$port 2>/dev/null | grep -q LISTEN; then
        echo -e "${YELLOW}  Port $port már foglalt, felszabadítás...${NC}"
        if command -v fuser &> /dev/null; then
            fuser -k $port/tcp 2>/dev/null || true
        else
            lsof -i :$port 2>/dev/null | awk 'NR!=1 {print $2}' | xargs kill -9 2>/dev/null || true
        fi
        sleep 1
    fi
done
echo -e "${GREEN}  ✓ Portok szabadok${NC}"

# 2. Virtuális környezet aktiválása
echo -e "\n${YELLOW}2️⃣ Virtuális környezet aktiválása...${NC}"
source "$VENV/bin/activate"
echo -e "${GREEN}  ✓ Virtuális környezet aktív${NC}"

# 3. Backend indítása
echo -e "\n${YELLOW}3️⃣ Backend indítása (3000-es port)...${NC}"
cd "$BASE_DIR/backend"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 3000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" >> "$PID_FILE"
echo -e "${GREEN}  ✓ Backend PID: $BACKEND_PID${NC}"

# Backend szerver feltöltődésének várása
echo -e "${YELLOW}  Backend szerver indulása...${NC}"
sleep 3
if curl -s http://127.0.0.1:3000/api/history >/dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Backend válaszol${NC}"
else
    echo -e "${RED}  ❌ Backend nem válaszol${NC}"
    tail -20 /tmp/backend.log
fi

# 4. Frontend indítása
echo -e "\n${YELLOW}4️⃣ Frontend indítása (5173-as port)...${NC}"
cd "$BASE_DIR/frontend"
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" >> "$PID_FILE"
echo -e "${GREEN}  ✓ Frontend PID: $FRONTEND_PID${NC}"

# Frontend szerver feltöltődésének várása
echo -e "${YELLOW}  Frontend szerver indulása...${NC}"
sleep 4
if lsof -i :5173 2>/dev/null | grep -q LISTEN; then
    echo -e "${GREEN}  ✓ Frontend fut 5173-on${NC}"
else
    echo -e "${RED}  ❌ Frontend nem fut${NC}"
    tail -20 /tmp/frontend.log
fi

# 5. Összefoglaló
echo -e "\n${BLUE}════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ ALKALMAZÁS FUTÓ!${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "\n${BLUE}Elérhetőségek:${NC}"
echo -e "  🌐 Frontend: ${GREEN}http://localhost:5173${NC}"
echo -e "  📡 Backend:  ${GREEN}http://localhost:3000${NC}"
echo -e "\n${BLUE}Logfájlok:${NC}"
echo -e "  📋 Backend:  /tmp/backend.log"
echo -e "  📋 Frontend: /tmp/frontend.log"
echo -e "\n${YELLOW}Leállításhoz: Ctrl+C${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}\n"

# Nyitott logok figyelése
tail -f /tmp/backend.log 2>/dev/null &
TAIL_PID=$!
echo "$TAIL_PID" >> "$PID_FILE"

# Szerverfutások figyelése
while true; do
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Backend leállt!${NC}"
        cleanup
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Frontend leállt!${NC}"
        cleanup
    fi
    sleep 5
done
