from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
from urllib.request import urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "server" / "models"
MODEL_URLS = {
    "pose_landmarker_lite.task": (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
    ),
    "pose_landmarker_full.task": (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_full/float16/latest/pose_landmarker_full.task"
    ),
    "hand_landmarker.task": (
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
        "hand_landmarker/float16/latest/hand_landmarker.task"
    ),
}


def run(command: list[str], *, cwd: Path = PROJECT_ROOT) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def install_frontend() -> None:
    npm = shutil.which("npm")
    node = shutil.which("node")
    if not npm or not node:
        raise SystemExit("Node.js 22 LTS (including npm) is required. Install it, then rerun setup.")
    version = subprocess.run([node, "--version"], capture_output=True, text=True, check=True).stdout
    match = re.match(r"v?(\d+)\.(\d+)", version.strip())
    if not match or (int(match.group(1)), int(match.group(2))) < (22, 12):
        raise SystemExit("Vite requires Node.js 22.12 or newer. Install Node.js 22 LTS, then rerun setup.")
    command = [npm, "install", "--prefix", str(PROJECT_ROOT / "client")]
    if os.name == "nt":
        subprocess.run(subprocess.list2cmdline(command), cwd=PROJECT_ROOT, check=True, shell=True)
    else:
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def download_models() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in MODEL_URLS.items():
        destination = MODEL_DIR / filename
        if destination.is_file() and destination.stat().st_size:
            print(f"Model ready: {destination.relative_to(PROJECT_ROOT)}")
            continue
        temporary = destination.with_suffix(destination.suffix + ".download")
        print(f"Downloading {filename}...")
        try:
            with urlopen(url, timeout=60) as response, temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
            temporary.replace(destination)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise


def main() -> int:
    if sys.version_info[:2] != (3, 12):
        print("Use Python 3.12 for setup (Windows: py -3.12; Linux: python3.12).")
        return 1

    environment = PROJECT_ROOT / ".venv"
    if not environment.exists():
        run([sys.executable, "-m", "venv", str(environment)])
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", "-r", str(PROJECT_ROOT / "requirements.txt")])
    install_frontend()
    download_models()
    print("Setup complete. Start GAIT with: python scripts/run_web.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
