#!/usr/bin/env python3
"""
Blog FastAPI Server Launcher
Ishga tushirish: python3 run.py
"""
import sys
from pathlib import Path
import uvicorn

# Set python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":
    print("🚀 Starting Blog FastAPI Server on http://127.0.0.1:8000 ...")
    print("📖 API Documentation: http://127.0.0.1:8000/docs")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
