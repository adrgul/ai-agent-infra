#!/bin/bash

# Verify project setup
echo "🔍 Verifying City Briefing Agent setup..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi
echo "✅ Docker found"

# Check requirements files
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi
echo "✅ Backend requirements found"

if [ ! -f "frontend/package.json" ]; then
    echo "❌ frontend/package.json not found"
    exit 1
fi
echo "✅ Frontend package.json found"

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found - using defaults"
fi

echo ""
echo "✅ All checks passed!"
echo "Run 'docker-compose up --build' to start the application"
