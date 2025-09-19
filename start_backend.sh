#!/bin/bash

# Quick start script for frontend developers
echo "Starting MVP Backend for Frontend Development..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/installed" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    touch venv/installed
fi

# Check if PostgreSQL container is running
if ! docker ps | grep -q mvp-postgres; then
    echo "Starting PostgreSQL database..."
    
    # Stop any existing container
    docker stop mvp-postgres 2>/dev/null || true
    docker rm mvp-postgres 2>/dev/null || true
    
    # Start fresh container
    docker run -d --name mvp-postgres \
        -e POSTGRES_DB=mvp_db \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=password \
        -p 5435:5432 postgres:15
    
    echo "Waiting for PostgreSQL to start..."
    sleep 5
fi

# Check if database is migrated
echo "Setting up database..."
alembic upgrade head

# Check if database has data
if ! python -c "
from backend.app.db.session import SessionLocal
from backend.app.db.models import CanonicalIdentity
db = SessionLocal()
count = db.query(CanonicalIdentity).count()
db.close()
exit(0 if count > 0 else 1)
" 2>/dev/null; then
    echo "Seeding database with sample data..."
    python seed_db.py
fi

echo "Database ready with sample data!"
echo ""
echo "Starting FastAPI server..."
echo "API Base URL: http://localhost:8006"
echo "API Documentation: http://localhost:8006/docs"
echo "Health Check: http://localhost:8006/health"
echo ""
echo "Authentication: Bearer demo-token-12345"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="

# Start the server
python -m backend.app.main
