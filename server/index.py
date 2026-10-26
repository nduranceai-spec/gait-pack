"""GAIT Server — FastAPI application entrypoint."""
import os
import sys
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parent
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from api.index import app

handler = app

__all__ = ["app", "handler"]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8765"))
    host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run("api.index:app", host=host, port=port, reload=True)
