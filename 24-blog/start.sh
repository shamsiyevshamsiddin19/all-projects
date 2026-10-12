#!/usr/bin/env bash
# HAGUE Blog — FastAPI & PostgreSQL Backend Launcher
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
VENV_DIR="$BACKEND_DIR/venv"

echo "=========================================================="
echo "   HAGUE Editorial Blog — FastAPI & PostgreSQL Server    "
echo "=========================================================="

# Check venv
if [ ! -d "$VENV_DIR" ]; then
    echo "⚙️ Virtual environment yaratilmoqda..."
    python3 -m venv "$VENV_DIR"
    echo "📦 Bog'liqliklar o'rnatilmoqda..."
    "$VENV_DIR/bin/pip" install --no-cache-dir -r "$BACKEND_DIR/requirements.txt"
fi

# Run database seeder if needed
echo "🌱 Ma'lumotlar bazasi tekshirilmoqda..."
"$VENV_DIR/bin/python3" "$BACKEND_DIR/seed.py"

echo "🚀 FastAPI server ishga tushmoqda:"
echo "   - Web API: http://127.0.0.1:8000"
echo "   - Swagger Docs: http://127.0.0.1:8000/docs"
echo "   - ReDoc: http://127.0.0.1:8000/redoc"
echo "   - Frontend: index.html (yoki http://127.0.0.1:8000/static/index.html)"
echo "=========================================================="

"$VENV_DIR/bin/python3" "$BACKEND_DIR/run.py"
