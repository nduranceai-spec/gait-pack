#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
exec env PYTHONPATH="${PROJECT_DIR}/server" .venv/bin/python -m src.pose_camera "$@"
