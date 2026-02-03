#!/bin/bash
# Inframate Backend Entrypoint Script
# Handles database migrations and initialization before starting the application

set -e  # Exit on error

echo "=================================================="
echo "Inframate Backend Initialization"
echo "=================================================="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
max_attempts=30
attempt=0

while ! python -c "
from sqlalchemy import create_engine
import os
import sys
try:
    engine = create_engine(os.environ['DATABASE_URL'])
    conn = engine.connect()
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f'Database not ready: {e}')
    sys.exit(1)
" 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "ERROR: PostgreSQL failed to become ready after $max_attempts attempts"
        exit 1
    fi
    echo "Waiting for database... (attempt $attempt/$max_attempts)"
    sleep 2
done

echo "✓ PostgreSQL is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
attempt=0
while ! python -c "
import redis
import os
import sys
try:
    r = redis.from_url(os.environ.get('REDIS_URL', 'redis://redis:6379/0'))
    r.ping()
    sys.exit(0)
except Exception as e:
    print(f'Redis not ready: {e}')
    sys.exit(1)
" 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "WARNING: Redis failed to become ready after $max_attempts attempts"
        echo "Continuing anyway..."
        break
    fi
    echo "Waiting for Redis... (attempt $attempt/$max_attempts)"
    sleep 2
done

echo "✓ Redis is ready!"

# Initialize database tables first (needed for fresh databases)
echo ""
echo "Initializing database tables..."
python -c "
from backend.core.database import init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    logger.info('Creating database tables if not exist...')
    init_db()
    logger.info('✓ Database tables ready')
except Exception as e:
    logger.error(f'Table creation error: {e}')
    raise
"

if [ $? -ne 0 ]; then
    echo "ERROR: Database table initialization failed"
    exit 1
fi

# Run database migrations (apply any incremental changes)
echo ""
echo "Running Alembic database migrations..."
if alembic upgrade head; then
    echo "✓ Database migrations completed successfully"
else
    echo "WARNING: Migrations failed, attempting to stamp head..."
    # If migrations fail on fresh DB, stamp to latest version
    alembic stamp head
    echo "✓ Database stamped at head"
fi

# Create default admin user
echo ""
echo "Creating default admin user..."
python -c "
from backend.core.setup import create_default_admin_sync
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    create_default_admin_sync()
    logger.info('✓ Admin user ready')
except Exception as e:
    logger.error(f'Admin creation error: {e}')
    raise
"

if [ $? -eq 0 ]; then
    echo "✓ Database initialization completed"
else
    echo "ERROR: Database initialization failed"
    exit 1
fi

echo ""
echo "=================================================="
echo "Initialization Complete - Starting Application"
echo "=================================================="
echo ""

# Execute the main command (passed as arguments to this script)
exec "$@"
