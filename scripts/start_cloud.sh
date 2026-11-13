#!/usr/bin/env bash
# ==============================================================================
# Unified Cortex Cloud Container Startup Script
# Starts Alembic migrations, Celery worker, and Uvicorn FastAPI server
# ==============================================================================
set -e

echo "=== Starting Cortex AI Research Platform ==="

# 1. Run migrations if DATABASE_URL is configured
if [ -n "${DATABASE_URL:-}" ]; then
    echo "Running Alembic database migrations..."
    python3 -m alembic upgrade head || echo "Database migration warning: proceeding with startup..."
fi

# 2. Start Celery worker in background
echo "Starting Celery background worker..."
celery -A app.workers.celery_app.celery_app worker --loglevel=info --concurrency=2 &

# 3. Start Uvicorn FastAPI server in foreground on PORT (default: 7860)
PORT="${PORT:-7860}"
echo "Starting FastAPI server on port ${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"

