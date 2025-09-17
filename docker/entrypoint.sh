#!/bin/bash

# Entrypoint script for Docker container
set -e

# Function to wait for database
wait_for_db() {
    echo "Waiting for database..."
    while ! nc -z $DATABASE_HOST $DATABASE_PORT; do
        sleep 0.1
    done
    echo "Database is ready!"
}

# Function to wait for Redis
wait_for_redis() {
    echo "Waiting for Redis..."
    while ! nc -z $REDIS_HOST $REDIS_PORT; do
        sleep 0.1
    done
    echo "Redis is ready!"
}

# Parse database URL to extract host and port
if [ -n "$DATABASE_URL" ]; then
    DATABASE_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DATABASE_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
fi

# Parse Redis URL to extract host and port
if [ -n "$REDIS_URL" ]; then
    REDIS_HOST=$(echo $REDIS_URL | sed -n 's/.*\/\/\([^:]*\):.*/\1/p')
    REDIS_PORT=$(echo $REDIS_URL | sed -n 's/.*:\([0-9]*\).*/\1/p')
fi

# Wait for services if in production
if [ "$ENVIRONMENT" = "production" ]; then
    if [ -n "$DATABASE_HOST" ] && [ -n "$DATABASE_PORT" ]; then
        wait_for_db
    fi
    
    if [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ]; then
        wait_for_redis
    fi
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Create initial data if specified
if [ "$CREATE_INITIAL_DATA" = "true" ]; then
    echo "Creating initial data..."
    python scripts/init_db.py
fi

# Execute the main command
exec "$@"
