#!/bin/bash
# Auto-deploy script — called by webhook or manually
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo "=== Deploy started at $(date) ==="

# Pull latest code
git pull origin main

# Rebuild and restart app services only (NOT webhook — it runs this script,
# restarting it kills the deploy process mid-way, leaving containers in "Created" state)
docker compose up -d --build --force-recreate --no-deps backend nginx

# Clean up old images
docker image prune -f

echo "=== Deploy finished at $(date) ==="
