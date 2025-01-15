#!/bin/sh
set -e

echo "Running migrations..."
alembic upgrade head

echo "Starting server..."
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --threads 8 --bind 0.0.0.0:80
#uvicorn app.main:app --host 0.0.0.0 --port 80 --reload
exec "$@"
