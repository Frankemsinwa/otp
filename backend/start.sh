#!/usr/bin/env bash
# ============================================================
# Production entrypoint — runs migrations, then boots uvicorn.
# Railway sets PORT automatically; defaults to 8000 for local.
# ============================================================
set -e

PORT="${PORT:-8000}"

echo "▶ Running database migrations..."
alembic upgrade head

echo "▶ Starting uvicorn on 0.0.0.0:${PORT}..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers 2 \
    --log-level info \
    --access-log
