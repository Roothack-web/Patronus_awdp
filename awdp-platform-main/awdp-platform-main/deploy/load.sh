#!/bin/bash
# ============================================================
# 砺剑AWDp — Restore & Deploy Script
# Run this on Linux to restore from a backup and start the
# platform using Docker Compose.
# ============================================================
set -e

if [ -z "$1" ]; then
    echo "Usage: bash deploy/load.sh <backup_path>"
    echo "Example: bash deploy/load.sh backup/awdp-backup-20260509_120000"
    exit 1
fi

BACKUP_PATH="$1"

if [ ! -d "$BACKUP_PATH" ]; then
    echo "Error: Backup path not found: $BACKUP_PATH"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo " 砺剑AWDp — Restore & Deploy"
echo "=========================================="
echo "Backup: $BACKUP_PATH"

# ─── 1. Load Docker images ─────────────────────────────────
echo "[1/4] Loading Docker images..."
for img in "$BACKUP_PATH/images/"*.tar; do
    if [ -f "$img" ]; then
        echo "  Loading $(basename "$img") ..."
        docker load -i "$img"
    fi
done

# ─── 2. Restore database ───────────────────────────────────
echo "[2/4] Restoring database..."
if [ -f "$BACKUP_PATH/database/awdp.db" ]; then
    cp "$BACKUP_PATH/database/awdp.db" "$PROJECT_DIR/awdp.db"
    echo "  awdp.db restored"
fi

# ─── 3. Restore uploads ────────────────────────────────────
echo "[3/4] Restoring uploads..."
if [ -d "$BACKUP_PATH/uploads" ]; then
    mkdir -p "$PROJECT_DIR/instance/uploads"
    cp -r "$BACKUP_PATH/uploads/." "$PROJECT_DIR/instance/uploads/" 2>/dev/null
    echo "  uploads/ restored"
fi

# ─── 4. Start with Docker Compose ─────────────────────────
echo "[4/4] Starting platform..."
cd "$PROJECT_DIR"
docker compose -f deploy/docker-compose.yml up -d --build

echo ""
echo "=========================================="
echo " Deploy Complete!"
echo "   Platform: http://localhost:5000"
echo "   Default admin: admin / admin"
echo "=========================================="
echo ""
echo "Commands:"
echo "  docker compose logs -f    # View logs"
echo "  docker compose down       # Stop platform"
echo "  docker compose restart    # Restart"
echo ""
