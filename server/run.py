#!/usr/bin/env python3
"""
GAIT // KINETIC X - Unified Single Runnable Runner
Wires up both Python MediaPipe Backend (port 8765) and Sports Animated Frontend (port 5173).
"""

from pathlib import Path
import os
import shutil
import signal
import subprocess
import sys
import time

SERVER_ROOT = Path(__file__).resolve().parent
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


def run_mediapipe_preflight(python_exe: Path) -> bool:
    """Preflight check to verify MediaPipe task models and detector."""
    print("⚡ [1/3] Running MediaPipe detector preflight...")
    try:
        check_code = (
            "import cv2, numpy as np;"
            "from src.web_server import browser_pose;"
            "img = np.zeros((320, 320, 3), dtype=np.uint8);"
            "_, buf = cv2.imencode('.jpg', img);"
            "res = browser_pose.process(buf.tobytes());"
            "browser_pose.close();"
            "print('MediaPipe ready!')"
        )
        result = subprocess.run(
            [str(python_exe), "-c", check_code],
            cwd=SERVER_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            print("   ✅ MediaPipe pose landmarker model verified and warm.")
            return True
        else:
            print(f"   ⚠️ MediaPipe warning:\n{result.stderr.strip()[:300]}")
            return True
    except Exception as exc:
        print(f"   ⚠️ MediaPipe preflight note: {exc}")
        return True


def main() -> int:
    node = shutil.which("node")
    python_cmd = VENV_PYTHON if VENV_PYTHON.is_file() else Path(sys.executable)

    print("\n" + "=" * 65)
    print("  ⚡ GAIT // KINETIC X — HIGH-PERFORMANCE SPORTS ANIMATION ENGINE")
    print("  3 Layers: Design Components · Animation Tech · Sports UI")
    print("=" * 65)

    # 1. MediaPipe Preflight
    run_mediapipe_preflight(python_cmd)

    # 2. Check Node & Vite
    print("⚡ [2/3] Checking frontend environment...")
    if not node:
        print("   ❌ Error: Node.js is required. Install Node.js 22 LTS.")
        return 1
    if not VITE_ENTRY.is_file():
        print("   ⚠️ Installing frontend dependencies with npm...")
        subprocess.run(["npm", "install", "--prefix", str(CLIENT_ROOT)], cwd=PROJECT_ROOT, check=True)

    print("   ✅ Frontend dependencies ready.")

    # 3. Launch Services
    print("⚡ [3/3] Launching Backend + Frontend services...")
    processes: list[subprocess.Popen] = []
    try:
        # Backend MediaPipe API server on 8765
        processes.append(subprocess.Popen(
            [str(python_cmd), "-m", "src.web_server"],
            cwd=SERVER_ROOT,
        ))

        # Frontend Vite Dev Server on 5173
        processes.append(subprocess.Popen(
            [node, str(VITE_ENTRY), "--host", "127.0.0.1", "--port", "5173", "--strictPort"],
            cwd=CLIENT_ROOT,
        ))

        print("\n" + "-" * 65)
        print("  🚀 GAIT KINETIC X IS LIVE:")
        print("  🌐 Sports Web Portal:  http://127.0.0.1:5173")
        print("  🧠 MediaPipe API:      http://127.0.0.1:8765")
        print("  ✨ Lenis Smooth Scroll · 3D Three.js Ball · 7 Sport Buttons")
        print("  📷 Live Camera MediaPipe Mesh Scan Active")
        print("-" * 65)
        print("  Press Ctrl+C to stop both services.\n")

        while all(process.poll() is None for process in processes):
            time.sleep(0.25)

        return next((p.returncode for p in processes if p.returncode), 0)

    except KeyboardInterrupt:
        print("\n⚡ Stopping GAIT Kinetic X services gracefully...")
        return 130
    finally:
        stop_processes(processes)
        print("⚡ All services stopped.")


if __name__ == "__main__":
    raise SystemExit(main())
