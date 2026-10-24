import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("GAIT_HARDWARE_MODE", "0")
os.environ.setdefault("GAIT_DATA_DIR", "/tmp/gait-data")

from src.web_server import Handler

handler = Handler
app = Handler

__all__ = ["handler", "Handler", "app"]
