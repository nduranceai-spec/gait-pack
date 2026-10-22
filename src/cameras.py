from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

import cv2


BUILT_IN_HINTS = ("integrated", "built-in", "builtin", "internal", "laptop")


@dataclass(frozen=True)
class CameraDevice:
    path: Path
    name: str
    connection: str
    modes: tuple[dict[str, object], ...] = ()


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
    # UVC devices commonly list every YUYV frame interval before MJPEG. Sort
    # the concise diagnostic payload so useful high-resolution/MJPEG modes are
    # retained instead of returning only the first low-resolution entries.
    def mode_key(mode: dict[str, object]) -> tuple[int, int, float]:
        width, height = (int(value) for value in str(mode["resolution"]).split("x"))
        return (0 if mode["format"] == "MJPG" else 1, -(width * height), -float(mode["fps"]))

    return tuple(sorted(modes, key=mode_key)[:24])


def _supports_preview_capture(path: Path) -> bool:
    output = _v4l2_output(path, "--all")
    # Device Caps is the effective capability set. Metadata nodes list only
    # "Metadata Capture" and must never be surfaced as selectable cameras.
    match = re.search(r"Device Caps\s*:(.*?)(?:Media Driver Info:|Interface Info:|Priority:)", output, re.S)
    if not (match and "Video Capture" in match.group(1)):
        return False
    # BRIO devices also advertise a small GREY auxiliary stream.  It is a
    # technically-valid capture node, but cannot provide the colour preview
    # required by GAIT, so do not describe it as a usable camera.
    return not bool(re.search(r"Pixel Format\s*:\s*'GREY'", output))


def find_cameras() -> list[CameraDevice]:
    """List one Linux entry per actual video-capture node, never metadata nodes."""
    cameras: list[CameraDevice] = []
    for path in sorted(Path("/dev").glob("video*")):
        sysfs_path = Path("/sys/class/video4linux") / path.name
        name_file = sysfs_path / "name"
        name = name_file.read_text().strip() if name_file.exists() else path.name
        try:
            device_path = str((sysfs_path / "device").resolve()).lower()
        except OSError:
            device_path = ""
        connection = "usb" if "/usb" in device_path else "platform"
        if not _supports_preview_capture(path):
            continue
        cameras.append(CameraDevice(path=path, name=name, connection=connection, modes=_capture_modes(path)))
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
