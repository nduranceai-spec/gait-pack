from pathlib import Path
import os
import subprocess
import sys

SERVER_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SERVER_ROOT.parent
VENV_PYTHON = PROJECT_ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
if not VENV_PYTHON.is_file():
    VENV_PYTHON = SERVER_ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def main() -> int:
    if not VENV_PYTHON.is_file():
        print("Run setup first: python server/scripts/setup.py")
        return 1
    environment = os.environ.copy()
    existing_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(SERVER_ROOT) + (
        os.pathsep + existing_path if existing_path else ""
    )
    return subprocess.call(
        [str(VENV_PYTHON), "-m", "src.pose_camera", *sys.argv[1:]],
        cwd=SERVER_ROOT,
        env=environment,
    )


if __name__ == "__main__":
    raise SystemExit(main())
