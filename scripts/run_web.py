from pathlib import Path
import os
import shutil
import subprocess
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_ROOT = PROJECT_ROOT / "server"
CLIENT_ROOT = PROJECT_ROOT / "client"
VENV_PYTHON = PROJECT_ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
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
    if not VENV_PYTHON.is_file() or not VITE_ENTRY.is_file() or not node:
        print("Run the setup first: python scripts/setup.py")
        return 1

    processes: list[subprocess.Popen] = []
    try:
        processes.append(subprocess.Popen(
            [str(VENV_PYTHON), "-m", "src.web_server"],
            cwd=SERVER_ROOT,
        ))
        processes.append(subprocess.Popen(
            [node, str(VITE_ENTRY), "--host", "127.0.0.1", "--port", "5173", "--strictPort"],
            cwd=CLIENT_ROOT,
        ))
        print("GAIT is starting:")
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
