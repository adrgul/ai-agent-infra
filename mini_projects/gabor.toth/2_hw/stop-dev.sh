#!/bin/bash

echo "🛑 RAG Agent Leállítása"
echo "======================"

# Backend és frontend killálása
echo "Processz leállítása..."
ps aux | grep -E "python.*main|npm run dev" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null

sleep 2

# Portklevezetés
echo "🔓 Portok felszabadítása..."
lsof -i :8000 2>/dev/null | grep -v COMMAND | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
lsof -i :5173 2>/dev/null | grep -v COMMAND | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true

echo "✓ Szerver leállítva"
echo "✓ Portok felszabadítva"
