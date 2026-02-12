#!/bin/bash
# Auto-deploy script — called by webhook or manually
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo "=== Deploy started at $(date) ==="

# Pull latest code
git pull origin main

# When running inside the webhook container, docker compose reads the file from
# /app/repo/ (container mount). Volume paths in docker-compose.yml use
# ${HOST_REPO_DIR:-.} which expands to the absolute host path (/opt/ai-chat),
# so no --project-directory hack is needed.
DC="docker compose"

# Build images first (no containers affected)
echo "Building images..."
$DC build backend nginx

# Restart backend, wait for healthy, then restart nginx
echo "Restarting backend..."
$DC up -d --no-deps backend
echo "Waiting for backend to be healthy..."
for i in $(seq 1 30); do
    if $DC exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" 2>/dev/null; then
        echo "Backend healthy."
        break
    fi
    sleep 2
done

echo "Restarting nginx..."
$DC up -d --no-deps nginx

# Clean up old images
docker image prune -f

echo "=== Deploy finished at $(date) ==="
