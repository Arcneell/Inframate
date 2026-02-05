#!/usr/bin/env bash
# Rebuild the frontend image without cache and recreate the container.
# Use this after any frontend change to ensure the new build is served.
set -e
cd "$(dirname "$0")/.."
echo "Building frontend (no cache)..."
docker compose build --no-cache frontend
echo "Recreating frontend container..."
docker compose up -d --force-recreate frontend
echo "Done. Frontend is running with the new build."
