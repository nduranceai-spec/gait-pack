"""Start backend API server for local development with fast reload."""
import os
import subprocess
import sys
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SERVER_ROOT.parent
VENV_PYTHON = PROJECT_ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
if not VENV_PYTHON.is_file():
    VENV_PYTHON = SERVER_ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.is_file() else sys.executable


def main() -> int:
    port = int(os.environ.get("PORT", "8765"))
    host = os.environ.get("HOST", "127.0.0.1")

    # If the user explicitly opts into the local hardware/OpenCV server
    if os.environ.get("GAIT_LOCAL_HARDWARE") == "1":
        print(f"⚡ Starting local hardware OpenCV server on http://{host}:{port}...")
        return subprocess.call([PYTHON, "-m", "src.web_server"], cwd=SERVER_ROOT)

    print(f"⚡ Starting FastAPI server on http://{host}:{port}...")
    cmd = [PYTHON, "-m", "uvicorn", "api.index:app", "--host", host, "--port", str(port), "--reload"]
    try:
        return subprocess.call(cmd, cwd=SERVER_ROOT)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
