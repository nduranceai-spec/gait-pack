import argparse
import os
from pathlib import Path
import sys

os.environ.setdefault("MPLCONFIGDIR", ".cache/matplotlib")

import cv2
import mediapipe as mp

from src.cameras import find_cameras, open_camera, print_cameras, select_camera


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check packages, model, and camera")
    parser.add_argument(
        "--camera",
        default="usb",
        help="usb (default), built-in, a number such as 2, or /dev/video2",
    )
    parser.add_argument("--list-cameras", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(f"Python: {sys.version.split()[0]}")
    print(f"MediaPipe: {mp.__version__}")
    print(f"OpenCV: {cv2.__version__}")

    pose_model_path = Path("models/pose_landmarker_full.task")
    hand_model_path = Path("models/hand_landmarker.task")
    print(f"Pose model: {'ready' if pose_model_path.exists() else 'missing'}")
    print(f"Hand model: {'ready' if hand_model_path.exists() else 'missing'}")

    cameras = find_cameras()
    if args.list_cameras:
        print_cameras(cameras)
        return 0

    device = select_camera(args.camera, cameras)
    if device is None:
        print_cameras(cameras)
        return 1

    camera = open_camera(device)
    if not camera.isOpened():
        print(f"Camera {device.path}: not available")
        print("Close other camera applications, then run this check again.")
        return 1

    ok, frame = camera.read()
    camera.release()
    if not ok or frame is None:
        print("Camera 0: opened, but no frame was received")
        return 1

    height, width = frame.shape[:2]
    print(f"Camera {device.path}: ready ({width}x{height}) - {device.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
