#!/bin/bash
set -e
echo "🚀 Starting City Briefing Agent..."
mkdir -p data
docker-compose up --build
