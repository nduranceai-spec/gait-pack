#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

mkdir -p models
if [[ ! -f models/pose_landmarker_lite.task ]]; then
  curl --fail --location \
    --output models/pose_landmarker_lite.task \
    https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task
fi

if [[ ! -f models/pose_landmarker_full.task ]]; then
  curl --fail --location \
    --output models/pose_landmarker_full.task \
    https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task
fi

if [[ ! -f models/hand_landmarker.task ]]; then
  curl --fail --location \
    --output models/hand_landmarker.task \
    https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
fi

echo "Setup complete."
echo "Run: .venv/bin/python -m src.check_setup"
