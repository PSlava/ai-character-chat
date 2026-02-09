#!/bin/bash
# Auto-deploy script — called by webhook or manually
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo "=== Deploy started at $(date) ==="

# Pull latest code
git pull origin main

# Rebuild and restart containers
docker compose up -d --build --remove-orphans

# Clean up old images
docker image prune -f

echo "=== Deploy finished at $(date) ==="
