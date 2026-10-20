from dataclasses import dataclass
from pathlib import Path

import cv2


BUILT_IN_HINTS = ("integrated", "built-in", "builtin", "internal", "laptop")


@dataclass(frozen=True)
class CameraDevice:
    path: Path
    name: str
    connection: str


def find_cameras() -> list[CameraDevice]:
    cameras = []
    for path in sorted(Path("/dev").glob("video*")):
        sysfs_path = Path("/sys/class/video4linux") / path.name
        name_file = sysfs_path / "name"
        name = name_file.read_text().strip() if name_file.exists() else path.name
        try:
            device_path = str((sysfs_path / "device").resolve()).lower()
        except OSError:
            device_path = ""
        connection = "usb" if "/usb" in device_path else "platform"
        cameras.append(CameraDevice(path=path, name=name, connection=connection))
    return cameras


def print_cameras(cameras: list[CameraDevice]) -> None:
    if not cameras:
        print("No Linux camera devices were found.")
        return

    print("Available camera devices:")
    for camera in cameras:
        print(f"  {camera.path}: {camera.name} [{camera.connection}]")


def select_camera(selection: str, cameras: list[CameraDevice]) -> CameraDevice | None:
    if selection.startswith("/dev/video"):
        return next((camera for camera in cameras if str(camera.path) == selection), None)

    if selection.isdigit():
        requested_path = f"/dev/video{selection}"
        return next(
            (camera for camera in cameras if str(camera.path) == requested_path), None
        )

    built_in = [
        camera
        for camera in cameras
        if any(hint in camera.name.lower() for hint in BUILT_IN_HINTS)
    ]
    if selection == "built-in":
        candidates = built_in
    else:
        candidates = [
            camera
            for camera in cameras
            if camera.connection == "usb" and camera not in built_in
        ]

    if len(candidates) == 1:
        return candidates[0]

    camera_type = "built-in" if selection == "built-in" else "external USB"
    if not candidates:
        print(f"No {camera_type} camera could be identified safely.")
    else:
        print(f"More than one {camera_type} camera was found.")
    print("Choose an exact device, for example: --camera /dev/video2")
    return None


def open_camera(
    device: CameraDevice,
    width: int = 1280,
    height: int = 720,
    fps: int = 60,
) -> cv2.VideoCapture:
    camera = cv2.VideoCapture(str(device.path), cv2.CAP_V4L2)
    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    camera.set(cv2.CAP_PROP_FPS, fps)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return camera
