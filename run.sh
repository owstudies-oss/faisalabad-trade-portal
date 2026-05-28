#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  Faisalabad Trade Portal — Setup & Run"
echo "=========================================="
echo ""

if [ ! -d "venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv venv
fi

echo "[2/3] Installing dependencies..."
venv/bin/pip install -q -r backend/requirements.txt

PORT="${PORT:-8000}"
echo "[3/3] Starting server on port $PORT..."
echo ""
echo "  Open:  http://localhost:$PORT"
echo "  Stop:  Ctrl+C"
echo ""

venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" --reload