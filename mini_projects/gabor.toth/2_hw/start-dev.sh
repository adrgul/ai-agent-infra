#!/bin/bash

# Set script directory for proper path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 RAG Agent Fejlesztési Szerver Indítása"
echo "============================================"

# PID tárolás az exit handler-ben való felhasználásra
BACKEND_PID=""
FRONTEND_PID=""

# Graceful shutdown kezelése - ELÖL az exit trap!
cleanup() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🛑 SZERVER LEÁLLÍTÁSA INDUL"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Backend leállítása
    if [ -n "$BACKEND_PID" ] 2>/dev/null; then 
        echo "  📍 Backend leállítása (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Frontend leállítása
    if [ -n "$FRONTEND_PID" ] 2>/dev/null; then 
        echo "  📍 Frontend leállítása (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    sleep 2
    
    # Portok felszabadítása
    echo ""
    echo "🔓 Portok felszabadítása..."
    for port in 8000 5173; do
        pids=$(lsof -i :$port 2>/dev/null | grep -v COMMAND | awk '{print $2}')
        if [ -n "$pids" ]; then
            echo "  📍 Port $port: felszabadítás (PID: $pids)"
            echo "$pids" | xargs -r kill -9 2>/dev/null || true
        else
            echo "  ✓ Port $port: szabad"
        fi
    done
    
    echo ""
    echo "✓ Szerver leállítva"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
}

trap cleanup EXIT SIGINT SIGTERM

# 1. Felszabadítjuk a portokat
echo "🔓 Portok felszabadítása..."
for port in 8000 5173; do
  lsof -i :$port 2>/dev/null | grep -v COMMAND | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
done
sleep 2
echo "✓ Portok felszabadítva"

# 2. API key ellenőrzése
echo "🔑 API key ellenőrzése..."
if [ -z "$OPENAI_API_KEY" ]; then
    if [ -f ".env" ]; then
        # .env fájl betöltése
        export $(cat .env | grep -v '^#' | grep OPENAI_API_KEY)
        if [ -z "$OPENAI_API_KEY" ]; then
            echo "❌ Hiba: OPENAI_API_KEY nem található a .env-ben"
            exit 1
        fi
        echo "✓ OPENAI_API_KEY betöltve a .env-ből"
    else
        echo "❌ Hiba: OPENAI_API_KEY nem található"
        echo "   Állítsd be: export OPENAI_API_KEY='sk-...'"
        exit 1
    fi
else
    echo "✓ OPENAI_API_KEY már beállítva"
fi

# 3. Data mappák létrehozása
echo "📁 Data mappák létrehozása..."
mkdir -p data/users data/sessions data/uploads data/derived data/chroma_db
echo "✓ Data mappák kész"

# 4. Backend indítása
echo "📦 Backend indítása (http://localhost:8000)..."
cd backend
pip install -q -r requirements.txt 2>/dev/null || true
# Pass OPENAI_API_KEY explicitly to Python subprocess
OPENAI_API_KEY="$OPENAI_API_KEY" python3 main.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "✓ Backend indítva (PID: $BACKEND_PID)"

# Várakozás a backend startup-jára (maximum 10 próbálkozás, 2 másodperc interval)
for i in {1..10}; do
    sleep 2
    if curl -s --connect-timeout 1 http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✓ Backend válaszol"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ Backend nem indult el 20 másodperc után"
        tail -20 /tmp/backend.log
        exit 1
    fi
done
cd ..

# 5. Frontend indítása
echo "📦 Frontend indítása (http://localhost:5173)..."
cd frontend
npm install -q 2>/dev/null || true
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✓ Frontend indítva (PID: $FRONTEND_PID)"
cd ..

echo ""
echo "✅ RAG Agent Szerver Futása"
echo "============================"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo ""
echo "💡 Tipp: Használd a kilépés gombot a frontenden"
echo "   vagy nyomj Ctrl+C leállításhoz"
echo ""

# Várakozás a processzekre - bármelyik leállásakor aktiválódik a cleanup trap
wait $BACKEND_PID
echo "ℹ️ Backend leállt, összes process leállítása..."
cleanup

