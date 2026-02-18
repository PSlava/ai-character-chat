#!/bin/bash
# Auto-deploy script — called by webhook or manually
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo "=== Deploy started at $(date) ==="

# Pull latest code
git pull origin main

# Webhook container mounts the repo at the same path as on the host
# (HOST_REPO_DIR:/HOST_REPO_DIR), so docker compose sees identical paths
# and build contexts resolve correctly for the daemon on the host.
DC="docker compose"

# Build images first (no containers affected)
echo "Building images..."
export GIT_COMMIT=$(git rev-parse --short HEAD)
$DC build backend nginx

# --- Helper: wait for backend health ---
wait_for_healthy() {
    local max_tries=$1
    echo "Waiting for backend to be healthy (up to ${max_tries}x2s)..."
    for i in $(seq 1 "$max_tries"); do
        if $DC exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" 2>/dev/null; then
            echo "Backend healthy."
            return 0
        fi
        sleep 2
    done
    echo "Backend NOT healthy after $((max_tries * 2))s."
    return 1
}

# --- Deploy backend with recovery ---
echo "Restarting backend (force-recreate)..."
$DC up -d --no-deps --force-recreate backend

if ! wait_for_healthy 30; then
    echo "First attempt failed. Doing full down+up..."
    $DC stop backend
    $DC rm -f backend
    $DC up -d --no-deps backend

    if ! wait_for_healthy 30; then
        echo "ERROR: Backend still unhealthy after recovery. Deploy failed."
        exit 1
    fi
fi

echo "Restarting nginx..."
$DC up -d --no-deps nginx

# Clean up old images
docker image prune -f

echo "=== Deploy finished at $(date) ==="
