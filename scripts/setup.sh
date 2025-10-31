#!/bin/bash

# Wendy Project Setup Script
# This script sets up the entire Wendy project

set -e

echo "🚀 Starting Wendy Project Setup..."

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Docker found. Setting up services with Docker..."

    # Check if docker-compose exists
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        echo "❌ Docker Compose not found. Please install Docker and Docker Compose."
        exit 1
    fi

    # Create necessary directories
    mkdir -p storage dist logs sessions extract

    # Start services with Docker
    echo "📦 Starting PostgreSQL and Redis with Docker..."
    $DOCKER_COMPOSE_CMD up -d postgres redis

    # Wait for services to be ready
    echo "⏳ Waiting for services to start..."
    sleep 10

    # Setup database
    echo "🗄️ Setting up database..."
    if command -v psql &> /dev/null; then
        PGPASSWORD=password psql -h localhost -U postgres -d postgres -f backend/setup.sql
    else
        echo "⚠️ psql not found. Please run the SQL setup manually."
    fi

else
    echo "🐳 Docker not found. Setting up manually..."

    # Check system dependencies
    echo "📋 Checking system dependencies..."

    # Check if PostgreSQL is running
    if ! pg_isready -h localhost -p 5432 &> /dev/null; then
        echo "❌ PostgreSQL not running. Please start PostgreSQL service."
        echo "   On Ubuntu/Debian: sudo service postgresql start"
        echo "   On macOS: brew services start postgresql"
        echo "   On Windows: Start PostgreSQL from Services panel"
        exit 1
    fi

    # Check if Redis is running
    if ! redis-cli ping &> /dev/null; then
        echo "❌ Redis not running. Please start Redis service."
        echo "   On Ubuntu/Debian: sudo service redis-server start"
        echo "   On macOS: brew services start redis"
        echo "   On Windows: Start Redis from Services panel"
        exit 1
    fi

    echo "✅ System dependencies OK"

    # Create database and user
    echo "🗄️ Setting up database..."
    sudo -u postgres psql -c "CREATE DATABASE wendy_db;" 2>/dev/null || echo "Database might already exist"
    sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'password';" 2>/dev/null || echo "User might already exist"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE wendy_db TO postgres;" 2>/dev/null || true

    # Run database setup
    PGPASSWORD=password psql -h localhost -U postgres -d wendy_db -f backend/setup.sql
fi

# Install dependencies for each service
echo "📦 Installing dependencies..."

# Backend dependencies
echo "🔧 Installing backend dependencies..."
cd backend
if [ ! -f ".env" ]; then
    cp config.env.template .env
    echo "⚠️ Please edit backend/.env with your configuration"
fi
npm install

# Frontend dependencies
echo "🎨 Installing frontend dependencies..."
cd ../frontend
npm install

# Python workers dependencies
echo "🐍 Installing Python dependencies..."
cd ../listener
pip install -r requirements.txt

cd ../reader
pip install -r requirements.txt

cd ..

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Edit backend/.env with your configuration"
echo "2. Run: ./scripts/start.sh"
echo "3. Open http://localhost:4000 in your browser"
echo ""
echo "📖 For more information, see README.md"
