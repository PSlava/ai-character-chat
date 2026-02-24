#!/bin/bash
# Auto-deploy script — called by webhook or manually
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo "=== Deploy started at $(date) ==="

# Pull latest code
git pull origin main

# Detect which compose file to use
if [ -f docker-compose.fiction.yml ] && docker compose -f docker-compose.fiction.yml ps --quiet 2>/dev/null | head -1 | grep -q .; then
    DC="docker compose -f docker-compose.fiction.yml"
    echo "Detected fiction mode"
else
    DC="docker compose"
fi

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
deploy_backend() {
    echo "Restarting backend (stop+rm+up with deps)..."
    $DC stop backend
    sleep 2
    $DC rm -f backend
    $DC up -d backend
}

deploy_backend
if ! wait_for_healthy 30; then
    echo "WARN: Backend unhealthy, retrying deploy..."
    deploy_backend
    if ! wait_for_healthy 30; then
        echo "ERROR: Backend still unhealthy after retry. Deploy failed."
        exit 1
    fi
fi

echo "Restarting nginx..."
$DC stop nginx
$DC rm -f nginx
$DC up -d nginx

# --- Verify ALL critical services are running ---
echo "Verifying all services..."
sleep 5

FAILED=0
for svc in backend nginx postgres; do
    status=$($DC ps --format '{{.Status}}' "$svc" 2>/dev/null || echo "missing")
    if echo "$status" | grep -qi "up"; then
        echo "  $svc: OK ($status)"
    else
        echo "  $svc: FAILED ($status)"
        FAILED=1
    fi
done

if [ "$FAILED" -eq 1 ]; then
    echo "ERROR: Some services are down. Attempting full restart..."
    $DC up -d
    sleep 10
    # Final check
    for svc in backend nginx postgres; do
        status=$($DC ps --format '{{.Status}}' "$svc" 2>/dev/null || echo "missing")
        if echo "$status" | grep -qi "up"; then
            echo "  $svc: OK"
        else
            echo "  $svc: STILL DOWN — manual intervention needed"
        fi
    done
fi

# Clean up old images
docker image prune -f

echo "=== Deploy finished at $(date) ==="
