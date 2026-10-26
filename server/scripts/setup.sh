#!/usr/bin/env bash
set -euo pipefail
SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$(command -v python3.12 || command -v python3)"
"$PYTHON" "$SERVER_DIR/scripts/setup.py"
