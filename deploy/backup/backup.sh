#!/bin/bash
# Daily backup: PostgreSQL dump + uploads → Yandex Disk via rclone
#
# Strategy:
#   - DB: 3 rotating slots (day-0, day-1, day-2) — always last 3 days
#   - Uploads: incremental sync (rclone sync — only transfers changes)
#   - Minimal disk usage on both server and cloud
#
# Structure on Yandex Disk:
#   ai-chat-backups/
#     db/
#       slot-0.sql.gz  (each slot = one day, cyclic overwrite)
#       slot-1.sql.gz
#       slot-2.sql.gz
#       slot-0.meta     (timestamp + size info)
#       slot-1.meta
#       slot-2.meta
#     uploads/           (mirror of current uploads, incremental sync)
#
# Setup:
#   1. Install rclone: curl https://rclone.org/install.sh | sudo bash
#   2. Configure Yandex Disk: rclone config (name: yadisk, type: yandex)
#   3. Test: rclone lsd yadisk:
#   4. Add to cron: crontab -e
#      0 4 * * * /opt/ai-chat/deploy/backup/backup.sh >> /var/log/ai-chat-backup.log 2>&1

set -euo pipefail

# --- Config ---
REPO_DIR="${REPO_DIR:-/opt/ai-chat}"
RCLONE_REMOTE="${RCLONE_REMOTE:-yadisk}"
REMOTE_DIR="${REMOTE_DIR:-ai-chat-backups}"
SLOTS=3
LOCAL_TMP="/tmp/ai-chat-backup"

# Determine today's slot (0, 1, or 2)
DAY_OF_YEAR=$(date +%j)
SLOT=$(( DAY_OF_YEAR % SLOTS ))
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")

echo "=== Backup started: $TIMESTAMP (slot $SLOT) ==="

# --- Create local temp dir ---
rm -rf "$LOCAL_TMP"
mkdir -p "$LOCAL_TMP"

# --- 1. PostgreSQL dump → rotating slot ---
echo "Dumping PostgreSQL..."
docker compose -f "$REPO_DIR/docker-compose.yml" exec -T postgres \
    pg_dump -U aichat -d aichat --no-owner --no-acl \
    | gzip > "$LOCAL_TMP/slot-${SLOT}.sql.gz"

DB_SIZE=$(du -h "$LOCAL_TMP/slot-${SLOT}.sql.gz" | cut -f1)
echo "  DB dump: $DB_SIZE → slot-${SLOT}"

# Write metadata file
echo "date: $TIMESTAMP" > "$LOCAL_TMP/slot-${SLOT}.meta"
echo "size: $DB_SIZE" >> "$LOCAL_TMP/slot-${SLOT}.meta"

# Upload DB dump (overwrites previous slot)
rclone mkdir "${RCLONE_REMOTE}:${REMOTE_DIR}/db"
rclone copyto "$LOCAL_TMP/slot-${SLOT}.sql.gz" "${RCLONE_REMOTE}:${REMOTE_DIR}/db/slot-${SLOT}.sql.gz"
rclone copyto "$LOCAL_TMP/slot-${SLOT}.meta" "${RCLONE_REMOTE}:${REMOTE_DIR}/db/slot-${SLOT}.meta"
echo "  DB uploaded"

# --- 2. Uploads — incremental sync ---
echo "Syncing uploads (incremental)..."
UPLOADS_MOUNT=$(docker volume inspect ai-chat_uploads -f '{{.Mountpoint}}' 2>/dev/null || echo "")

if [ -n "$UPLOADS_MOUNT" ] && [ -d "$UPLOADS_MOUNT" ]; then
    # rclone sync: only transfers new/changed files, deletes removed files
    rclone sync "$UPLOADS_MOUNT/" "${RCLONE_REMOTE}:${REMOTE_DIR}/uploads/" \
        --transfers 4 \
        --checkers 8 \
        --stats-one-line \
        -v
    echo "  Uploads synced"
else
    echo "  Uploads volume not found, skipping"
fi

# --- Cleanup ---
rm -rf "$LOCAL_TMP"

echo "=== Backup finished: $(date "+%Y-%m-%d %H:%M") ==="
