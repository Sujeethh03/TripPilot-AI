#!/bin/sh
# Bring the schema up to date, then hand the container over to uvicorn.
# `exec` matters: uvicorn becomes PID 1 so the platform's SIGTERM reaches it
# and in-flight WebSocket turns get a clean shutdown.
set -e

if [ -n "$DATABASE_URL" ]; then
  echo "running migrations..."
  alembic upgrade head
else
  echo "DATABASE_URL unset — skipping migrations"
fi

# The host tells us which port to bind (Render sets $PORT); 8000 locally.
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --ws-ping-interval 20 \
  --ws-ping-timeout 60
