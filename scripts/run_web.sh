#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
if [[ ! -x .venv/bin/python || ! -d frontend/node_modules ]]; then
  echo "Run bash scripts/setup.sh and (cd frontend && npm install) first."
  exit 1
fi
.venv/bin/python -m src.web_server &
BACKEND_PID=$!
FRONTEND_PID=""
cleanup() {
  kill "$BACKEND_PID" ${FRONTEND_PID:+"$FRONTEND_PID"} 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM
npm --prefix frontend run dev &
FRONTEND_PID=$!
wait -n "$BACKEND_PID" "$FRONTEND_PID"
