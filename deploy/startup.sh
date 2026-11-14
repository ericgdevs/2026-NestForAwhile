#!/bin/sh
set -eu

cd /app/backend
alembic upgrade head

if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  python -m seed.load
fi

exec uvicorn vercel_app:app --host 0.0.0.0 --port "${PORT:-8000}"
