#!/usr/bin/env python3
"""
Backend entry point - makes the app independent of folder structure
Works from any directory thanks to __file__ path resolution
"""
import sys
from pathlib import Path

# Resolve the absolute path to the backend directory
backend_dir = Path(__file__).resolve().parent

# Add backend directory to path so 'app' package can be imported
sys.path.insert(0, str(backend_dir))

from app.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=3000,
    )
