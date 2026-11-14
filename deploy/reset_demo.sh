#!/bin/sh
set -eu

DATABASE_URL="${DATABASE_URL:-sqlite:///./warehouse.db}"
case "$DATABASE_URL" in
  sqlite:///*)
    database_path="${DATABASE_URL#sqlite:///}"
    rm -f "$database_path"
    ;;
  *)
    echo "Reset is local-only; refusing to alter non-SQLite DATABASE_URL." >&2
    exit 1
    ;;
esac

cd backend
alembic upgrade head
python -m seed.load
echo "Synthetic demo database reset."
