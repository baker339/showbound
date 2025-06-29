#!/bin/bash
set -e

# Wait for the database to be ready
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 2
done

# Run Alembic migrations
alembic upgrade head

# Start FastAPI app
exec uvicorn main:app --host 0.0.0.0 --port 8000 