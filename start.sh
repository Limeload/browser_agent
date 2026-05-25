#!/bin/bash
set -e

echo "Voice Browser Agent — starting up"
echo "=================================="

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed." >&2
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is required but not installed." >&2
    exit 1
fi

echo "Installing Python dependencies..."
pip3 install -r requirements.txt

echo "Installing Playwright browsers..."
playwright install chromium 2>/dev/null || true

echo "Installing Node.js dependencies..."
npm install

echo "Building React frontend..."
npm run build

echo "Starting Python backend on port 8000..."
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 2

echo "Starting React dev server on port 3000..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Backend API : http://localhost:8000"
echo "API docs    : http://localhost:8000/docs"
echo "Frontend    : http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
