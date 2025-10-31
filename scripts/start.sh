#!/bin/bash

# Wendy Project Startup Script
# This script starts all Wendy services

set -e

echo "🚀 Starting Wendy Project..."

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $(jobs -p) 2>/dev/null || true
    exit
}

trap cleanup SIGINT SIGTERM

# Create necessary directories
mkdir -p storage dist logs sessions extract

# Validate configuration before starting
echo "🔍 Validating configuration..."
if ! python3 scripts/validate_config.py; then
    echo "❌ Configuration validation failed. Please fix the issues above."
    exit 1
fi

# Start Redis if not using Docker
if ! pgrep -x "redis-server" > /dev/null; then
    echo "🔴 Redis not running. Please start Redis first."
    echo "   On Ubuntu/Debian: sudo service redis-server start"
    echo "   On macOS: brew services start redis"
    echo "   On Windows: Start Redis from Services panel"
    exit 1
fi

# Start PostgreSQL if not using Docker
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "🗄️ PostgreSQL not running. Please start PostgreSQL first."
    echo "   On Ubuntu/Debian: sudo service postgresql start"
    echo "   On macOS: brew services start postgresql"
    echo "   On Windows: Start PostgreSQL from Services panel"
    exit 1
fi

echo "✅ Dependencies OK"

# Start Backend
echo "🔧 Starting Backend..."
cd backend
npm run dev &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start Frontend
echo "🎨 Starting Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a bit for frontend to start
sleep 3

# Start Reader Worker
echo "📖 Starting Reader Worker..."
cd reader
python reader.py &
READER_PID=$!
cd ..

# Start Listener Worker
echo "👂 Starting Listener Worker..."
cd listener
python telegram_listener.py &
LISTENER_PID=$!
cd ..

echo ""
echo "🎉 All services started successfully!"
echo ""
echo "📊 Services running:"
echo "  • Frontend:  http://localhost:4000"
echo "  • Backend:   http://localhost:4141"
echo "  • Reader:    Running in background"
echo "  • Listener:  Running in background"
echo ""
echo "📋 Service PIDs:"
echo "  • Backend:   $BACKEND_PID"
echo "  • Frontend:  $FRONTEND_PID"
echo "  • Reader:    $READER_PID"
echo "  • Listener:  $LISTENER_PID"
echo ""
echo "🛑 Press Ctrl+C to stop all services"

# Wait for all background processes
wait
