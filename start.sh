#!/usr/bin/env bash
# FolioTrack — one-command launcher
# Usage: ./start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "  📊 FolioTrack — UK Account Tracker"
echo "  ─────────────────────────────────"
echo ""

# ── Backend ───────────────────────────────────────────────────────────────────
cd "$SCRIPT_DIR/backend"

if [ ! -d "venv" ]; then
  echo "  → Creating Python virtual environment…"
  python3 -m venv venv
fi

echo "  → Installing Python dependencies…"
source venv/bin/activate
pip install -q -r requirements.txt

echo "  → Starting FastAPI backend on http://localhost:8000 (listening on all interfaces)"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# ── Frontend ──────────────────────────────────────────────────────────────────
cd "$SCRIPT_DIR/frontend"

if [ ! -d "node_modules" ]; then
  echo "  → Installing Node dependencies…"
  npm install
fi

echo "  → Starting Vite frontend on http://localhost:5173"
echo ""
echo "  Open: http://localhost:5173"
echo ""

npm run dev &
FRONTEND_PID=$!

# ── Cleanup on exit ───────────────────────────────────────────────────────────
trap "echo ''; echo '  Stopping servers…'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait
