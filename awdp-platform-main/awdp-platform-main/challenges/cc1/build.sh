#!/bin/bash
# ============================================================
# Build Script — Build and tag the challenge Docker image
# ============================================================
# Usage: ./build.sh <image_name>
#
# Examples: awdp-cc1
#
# After building, go to admin panel → 添加题目
# Set "Docker 镜像" to the image name you used here.
# ============================================================

set -e

NAME="${1:-awdp-cc1}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Building challenge image: $NAME"
docker build -t "$NAME" "$SCRIPT_DIR"

echo ""
echo "Done! Image: $NAME"
echo ""
echo "Next steps:"
echo "  1. Go to Admin → 添加题目"
echo "  2. Set 'Docker 镜像' = $NAME"
echo "  3. Set '容器内部端口' = 8080 (留空外部端口让平台自动分配)"
echo "  4. Set 'EXP 命令' = python3 /opt/exp.py --target http://127.0.0.1:{PORT}"
echo "  5. Test: docker run --rm -e FLAG=flag{test} -p 8080:8080 $NAME"
