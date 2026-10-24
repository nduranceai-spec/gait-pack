from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import sys

import cv2


BUILT_IN_HINTS = ("integrated", "built-in", "builtin", "internal", "laptop")
MAX_CAMERA_INDEX = 10


@dataclass(frozen=True)
class CameraDevice:
    path: str | int
    name: str
    connection: str
    modes: tuple[dict[str, object], ...] = ()
    backend: int = cv2.CAP_ANY


def _v4l2_output(path: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["v4l2-ctl", "-d", str(path), *args],
            check=False, capture_output=True, text=True, timeout=2,
        ).stdout
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return ""


def _capture_modes(path: Path) -> tuple[dict[str, object], ...]:
    """Return a concise list of capture-capable modes for diagnostics only."""
    output = _v4l2_output(path, "--list-formats-ext")
    modes: list[dict[str, object]] = []
    pixel_format = ""
    resolution = ""
    for line in output.splitlines():
        format_match = re.search(r"'([^']+)'", line)
        if format_match:
            pixel_format = format_match.group(1)
        size_match = re.search(r"Size: Discrete (\d+x\d+)", line)
        if size_match:
            resolution = size_match.group(1)
        fps_match = re.search(r"\(([0-9.]+) fps\)", line)
        if fps_match and pixel_format and resolution:
            mode = {"format": pixel_format, "resolution": resolution, "fps": float(fps_match.group(1))}
            if mode not in modes:
                modes.append(mode)

    def mode_key(mode: dict[str, object]) -> tuple[int, int, float]:
        width, height = (int(value) for value in str(mode["resolution"]).split("x"))
        return (0 if mode["format"] == "MJPG" else 1, -(width * height), -float(mode["fps"]))

    return tuple(sorted(modes, key=mode_key)[:24])


def _supports_preview_capture(path: Path) -> bool:
    output = _v4l2_output(path, "--all")
    match = re.search(r"Device Caps\s*:(.*?)(?:Media Driver Info:|Interface Info:|Priority:)", output, re.S)
    if not (match and "Video Capture" in match.group(1)):
        return False
    return not bool(re.search(r"Pixel Format\s*:\s*'GREY'", output))


def _probe_camera(device: str | int, backend: int) -> bool:
    camera = cv2.VideoCapture(device, backend)
    try:
        if not camera.isOpened():
            return False
        readable, frame = camera.read()
        return bool(readable and frame is not None)
    finally:
        camera.release()


def _find_linux_cameras() -> list[CameraDevice]:
    paths = sorted(Path("/dev").glob("video*"))
    use_v4l2_metadata = shutil.which("v4l2-ctl") is not None
    cameras: list[CameraDevice] = []
    for path in paths:
        sysfs_path = Path("/sys/class/video4linux") / path.name
        name_file = sysfs_path / "name"
        try:
            name = name_file.read_text().strip() if name_file.exists() else path.name
            device_path = str((sysfs_path / "device").resolve()).lower()
        except OSError:
            name = path.name
            device_path = ""
        connection = "usb" if "/usb" in device_path else "platform"
        if use_v4l2_metadata:
            if not _supports_preview_capture(path):
                continue
            modes = _capture_modes(path)
        else:
            if not _probe_camera(str(path), cv2.CAP_V4L2):
                continue
            modes = ()
        cameras.append(CameraDevice(
            path=str(path),
            name=name,
            connection=connection,
            modes=modes,
            backend=cv2.CAP_V4L2,
        ))
    return cameras


def _find_indexed_cameras(backend: int) -> list[CameraDevice]:
    cameras: list[CameraDevice] = []
    for index in range(MAX_CAMERA_INDEX):
        if _probe_camera(index, backend):
            cameras.append(CameraDevice(
                path=index,
                name=f"Camera {index}",
                connection="unknown",
                backend=backend,
            ))
    return cameras


def find_cameras() -> list[CameraDevice]:
    """Discover cameras using the native Linux backend or portable OpenCV indices."""
    if sys.platform.startswith("linux"):
        return _find_linux_cameras()
    if sys.platform == "win32":
        cameras = _find_indexed_cameras(cv2.CAP_DSHOW)
        return cameras or _find_indexed_cameras(cv2.CAP_MSMF)
    if sys.platform == "darwin":
        return _find_indexed_cameras(cv2.CAP_AVFOUNDATION)
    return _find_indexed_cameras(cv2.CAP_ANY)


def print_cameras(cameras: list[CameraDevice]) -> None:
    if not cameras:
        print("No usable camera devices were found.")
        return

    print("Available camera devices:")
    for camera in cameras:
        print(f"  {camera.path}: {camera.name} [{camera.connection}]")


def select_camera(selection: str, cameras: list[CameraDevice]) -> CameraDevice | None:
    if selection.startswith("/dev/video"):
        return next((camera for camera in cameras if str(camera.path) == selection), None)

    if selection.isdigit():
        return next(
            (
                camera for camera in cameras
                if str(camera.path) == selection or str(camera.path) == f"/dev/video{selection}"
            ),
            None,
        )

    built_in = [
        camera for camera in cameras
        if any(hint in camera.name.lower() for hint in BUILT_IN_HINTS)
    ]
    if selection == "built-in":
        candidates = built_in
    else:
        candidates = [
            camera for camera in cameras
            if camera.connection == "usb" and camera not in built_in
        ]
        if not candidates and selection == "usb":
            unknown = [camera for camera in cameras if camera.connection == "unknown"]
            if len(unknown) == 1:
                candidates = unknown

    if len(candidates) == 1:
        return candidates[0]

    camera_type = "built-in" if selection == "built-in" else "external USB"
    if not candidates:
        print(f"No {camera_type} camera could be identified safely.")
    else:
        print(f"More than one {camera_type} camera was found.")
    if any(camera.connection == "unknown" for camera in cameras):
        print("Use --camera followed by a listed device number, for example: --camera 0")
    else:
        print("Choose an exact device, for example: --camera /dev/video2")
    return None


def open_camera(
    device: CameraDevice,
    width: int = 1280,
    height: int = 720,
    fps: int = 60,
) -> cv2.VideoCapture:
    source: str | int = device.path
    if isinstance(source, str) and source.isdigit():
        source = int(source)
    camera = cv2.VideoCapture(source, device.backend)
    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    camera.set(cv2.CAP_PROP_FPS, fps)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return camera
