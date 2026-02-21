#!/bin/bash
set -e
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo "=== Fiction Deploy started at $(date) ==="
git pull origin main

DC="docker compose -f docker-compose.fiction.yml"
export GIT_COMMIT=$(git rev-parse --short HEAD)

echo "Building backend and nginx..."
$DC build backend nginx

echo "Restarting backend..."
$DC stop backend && sleep 2 && $DC rm -f backend && $DC up -d backend

# Wait for backend to be healthy
echo "Waiting for backend health..."
for i in $(seq 1 30); do
    if $DC exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" 2>/dev/null; then
        echo "Backend healthy!"
        break
    fi
    echo "  attempt $i/30..."
    sleep 5
done

echo "Restarting nginx..."
$DC stop nginx && $DC rm -f nginx && $DC up -d nginx

docker image prune -f
echo "=== Fiction Deploy finished at $(date) ==="
