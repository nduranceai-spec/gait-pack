#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$(command -v python3.12 || command -v python3)"
"$PYTHON" "$PROJECT_DIR/scripts/setup.py"
