#!/usr/bin/env bash
set -euo pipefail
SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="$(cd "$SERVER_DIR/.." && pwd)"
PYTHON="${PROJECT_DIR}/.venv/bin/python"
if [ ! -f "$PYTHON" ]; then
  PYTHON="${SERVER_DIR}/.venv/bin/python"
fi
exec "$PYTHON" "$SERVER_DIR/scripts/run_pose.py" "$@"
