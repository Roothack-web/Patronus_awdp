#!/bin/bash
# ============================================================
# 砺剑AWDp — Backup & Image Save Script
# Run this on Windows (Git Bash / WSL) to create a full backup
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backup"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_PATH="$BACKUP_DIR/awdp-backup-$TIMESTAMP"

echo "=========================================="
echo " 砺剑AWDp — Full Backup"
echo "=========================================="

# ─── 1. Create backup directories ──────────────────────────
echo "[1/5] Creating backup directories..."
mkdir -p "$BACKUP_PATH/source"
mkdir -p "$BACKUP_PATH/images"
mkdir -p "$BACKUP_PATH/database"
mkdir -p "$BACKUP_PATH/uploads"

# ─── 2. Save Docker images ─────────────────────────────────
echo "[2/5] Saving Docker images..."

save_image() {
    local name="$1"
    local filename="$(echo "$name" | tr ':/' '__').tar"
    echo "  Saving $name ..."
    if docker image inspect "$name" >/dev/null 2>&1; then
        (cd "$BACKUP_PATH/images" && MSYS2_ARG_CONV_EXCL="*" docker save -o "$filename" "$name")
        echo "    -> saved to images/$filename"
    else
        echo "    -> NOT FOUND (skipped)"
    fi
}

save_image "awdp-sqli:latest"
save_image "awdp-ssrf:latest"

# ─── 3. Copy source code (exclude venv, __pycache__) ──────
echo "[3/5] Copying source code..."
mkdir -p "$BACKUP_PATH/source"
# Use tar to exclude patterns, works everywhere
tar -cf - --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='.git' --exclude='backup' \
    -C "$PROJECT_DIR" . | tar -xf - -C "$BACKUP_PATH/source"
echo "  source/ copied"

# ─── 4. Copy database ──────────────────────────────────────
echo "[4/5] Copying database..."
if [ -f "$PROJECT_DIR/awdp.db" ]; then
    cp "$PROJECT_DIR/awdp.db" "$BACKUP_PATH/database/"
    echo "  awdp.db ($(du -h "$PROJECT_DIR/awdp.db" | cut -f1))"
fi

# ─── 5. Copy defense uploads ──────────────────────────────
echo "[5/5] Copying uploads..."
if [ -d "$PROJECT_DIR/instance/uploads" ]; then
    cp -r "$PROJECT_DIR/instance/uploads/." "$BACKUP_PATH/uploads/" 2>/dev/null
    echo "  uploads/ copied"
fi

# ─── Create summary ────────────────────────────────────────
BACKUP_SIZE="$(du -sh "$BACKUP_PATH" | cut -f1)"
echo ""
echo "=========================================="
echo " Backup Complete!"
echo "   Path: $BACKUP_PATH"
echo "   Size: $BACKUP_SIZE"
echo "=========================================="
echo ""
echo "To restore on Linux:"
echo "  1. Copy this backup to your Linux server"
echo "  2. Run: bash deploy/load.sh $BACKUP_PATH"
echo ""
