#!/bin/bash

# Voice Browser Agent Startup Script

echo "🎤 Voice Browser Agent - Starting up..."
echo "======================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Build React frontend
echo "🔨 Building React frontend..."
npm run build

# Start Python backend
echo "🚀 Starting Python backend on port 8000..."
python3 -m backend.main &

# Wait a moment for backend to start
sleep 3

# Start React frontend dev server
echo "🚀 Starting React frontend on port 3000..."
npm run dev &

echo ""
echo "✅ Voice Browser Agent is running!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
wait
