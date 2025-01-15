#!/bin/sh
set -e

echo "Running migrations..."
alembic upgrade head

echo "Starting server..."
gunicorn app.main:app \
-w "${WORKERS_COUNT:-4}" \
-k uvicorn.workers.UvicornWorker \
--threads "${THREADS_COUNT:-8}" \
--bind 0.0.0.0:80 \
--log-level "${LOG_LEVEL:-info}"

#uvicorn app.main:app --host 0.0.0.0 --port 80 --reload
exec "$@"
