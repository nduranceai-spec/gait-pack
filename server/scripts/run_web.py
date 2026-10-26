from pathlib import Path
import os
import shutil
import subprocess
import sys
import time

SERVER_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SERVER_ROOT.parent
CLIENT_ROOT = PROJECT_ROOT / "client"
VENV_PYTHON = PROJECT_ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
if not VENV_PYTHON.is_file():
    VENV_PYTHON = SERVER_ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
VITE_ENTRY = CLIENT_ROOT / "node_modules" / "vite" / "bin" / "vite.js"


def stop_processes(processes: list[subprocess.Popen]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    for process in processes:
        if process.poll() is None:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main() -> int:
    node = shutil.which("node")
    python_cmd = VENV_PYTHON if VENV_PYTHON.is_file() else Path(sys.executable)
    if not node:
        print("Run setup first: python server/scripts/setup.py")
        return 1

    print("=" * 65)
    print("  ⚡ GAIT // KINETIC X — HIGH-PERFORMANCE SPORTS ANIMATION ENGINE")
    print("=" * 65)

    processes: list[subprocess.Popen] = []
    try:
        processes.append(subprocess.Popen(
            [str(python_cmd), "-m", "src.web_server"],
            cwd=SERVER_ROOT,
        ))
        processes.append(subprocess.Popen(
            [node, str(VITE_ENTRY), "--host", "127.0.0.1", "--port", "5173", "--strictPort"],
            cwd=CLIENT_ROOT,
        ))
        print("GAIT Kinetic X is starting:")
        print("  App:     http://127.0.0.1:5173")
        print("  API:     http://127.0.0.1:8765")
        print("Press Ctrl+C to stop both services.")
        while all(process.poll() is None for process in processes):
            time.sleep(0.25)
        return next((process.returncode for process in processes if process.returncode), 0)
    except KeyboardInterrupt:
        return 130
    finally:
        stop_processes(processes)


if __name__ == "__main__":
    raise SystemExit(main())
