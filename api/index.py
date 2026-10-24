"""Vercel serverless entrypoint.

Vercel automatically serves any file inside the ``api/`` directory as a
serverless function.  We simply re-export the ``Handler`` class so Vercel can
find it without needing the ``[tool.vercel]`` pyproject.toml hint.

The handler itself lives in ``src/web_server.py`` to keep all logic in one
place and avoid duplication.
"""

import sys
import os
from pathlib import Path

# Make sure the project root is on sys.path so ``src.*`` imports work whether
# Vercel bundles us flat (/var/task) or keeps the directory structure intact.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Force serverless / cloud mode — no physical camera on Vercel workers.
os.environ.setdefault("GAIT_HARDWARE_MODE", "0")
os.environ.setdefault("GAIT_DATA_DIR", "/tmp/gait-data")

from src.web_server import Handler  # noqa: E402  (import after sys.path fix)

__all__ = ["Handler"]
