#!/bin/bash

# Production startup script for Railway deployment
set -e

echo "Starting MVP Backend Production Server..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "DATABASE_URL not set. Using default for development."
    export DATABASE_URL="postgresql+psycopg://postgres:password@localhost:5435/mvp_db"
fi

echo "Running database migrations..."
alembic upgrade head

echo "Database migrations completed"

# Check if we should seed the database
if [ "$SEED_DATABASE" = "true" ]; then
    echo "Seeding database..."
    python3 seed_db.py || python seed_db.py
    echo "Database seeding completed"
fi

echo "Starting FastAPI server..."
echo "   Environment: ${RAILWAY_ENVIRONMENT:-development}"
echo "   Port: ${PORT:-8000}"
echo "   Workers: 1"

# Start the server
exec uvicorn backend.app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --log-level info \
    --access-log \
    --no-server-header
