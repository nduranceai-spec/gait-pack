import json
import os
import re
import signal
import sys
import threading
import time
from contextlib import ExitStack
from dataclasses import dataclass, field
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
from uuid import uuid4

# Support both `python -m src.web_server` and `python src/web_server.py`.
SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".cache/matplotlib"))

import cv2
import mediapipe as mp
import numpy as np

from src.gait_analysis import analyse_session
from src.hardware_pose import BrowserPoseProcessor
from src.sessions import list_sessions, session_path

# ---------------------------------------------------------------------------
# Hardware mode: True when running locally with a physical camera attached.
# On Vercel (and other serverless platforms) the camera / recording stack is
# unavailable.  Setting GAIT_HARDWARE_MODE=0 (or leaving it unset in a cloud
# environment) skips those imports so the process doesn't crash at startup.
# ---------------------------------------------------------------------------
HARDWARE_MODE: bool = os.environ.get("GAIT_HARDWARE_MODE", "1").strip() not in {"0", "false", "no", ""}

if HARDWARE_MODE:
    try:
        from src.cameras import BUILT_IN_HINTS, find_cameras, open_camera, select_camera
        from src.pose_camera import InferenceWorker, LandmarkSmoother, draw_hands, draw_pose
        from src.recorder import GaitRecorder, RecordingState
    except Exception:  # pragma: no cover
        HARDWARE_MODE = False


ROOT = Path(__file__).resolve().parents[1]

# On Vercel the only writable directory is /tmp.  Fall back to it when the
# configured path is the old hard-coded local one or doesn't exist yet.
_default_data = "/tmp/gait-data" if os.environ.get("VERCEL") else str(ROOT / "data")
DATA_ROOT = Path(os.environ.get("GAIT_DATA_DIR", _default_data)).expanduser()

MAX_FRAME_BYTES = 2_000_000


@dataclass
class BrowserGaitSession:
    session_id: str
    timestamp: str
    frames_received: int = 0
    last_frame_at: str | None = None
    activity_type: str = "Normal Walk"
    state: str = "created"
    started_at: float | None = None
    stopped_at: str | None = None
    detected_frames: int = 0
    camera_name: str = "Browser camera"
    camera_fps: float | None = None
    landmark_frames: list[dict] = field(default_factory=list)
    views: list[dict] = field(default_factory=list)
    landmark_frames_by_view: dict[str, list[dict]] = field(default_factory=dict)
    view_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    received_sequences: set[tuple[str, int]] = field(default_factory=set)
    sent_counts: dict[str, int] = field(default_factory=dict)
    analysis_error: str | None = None
    person: dict[str, str] = field(default_factory=dict)
    duration_sec: int = 30
    storage_dir: Path | None = None
    video_writers: dict[str, object] = field(default_factory=dict, repr=False)
    video_sizes: dict[str, tuple[int, int]] = field(default_factory=dict, repr=False)
    lock: threading.RLock = field(default_factory=threading.RLock, repr=False)
    result: dict | None = None


browser_sessions: dict[str, BrowserGaitSession] = {}
browser_sessions_lock = threading.RLock()

# Locate the model file — support both the repo layout and a flat /var/task
# deployment layout that Vercel uses after bundling.
_model_candidates = [
    ROOT / "models" / "pose_landmarker_lite.task",
    ROOT.parent / "models" / "pose_landmarker_lite.task",
    Path("/var/task/models/pose_landmarker_lite.task"),
    Path("/tmp/models/pose_landmarker_lite.task"),
]
_model_path = next((p for p in _model_candidates if p.is_file()), ROOT / "models" / "pose_landmarker_lite.task")
browser_pose = BrowserPoseProcessor(_model_path)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _clean_person(raw: object) -> dict[str, str]:
    value = raw if isinstance(raw, dict) else {}
    name = str(value.get("name") or "").strip()[:120]
    if not name:
        raise ValueError("Participant name is required")
    def number(key: str, lower: float, upper: float) -> str:
        try:
            parsed = float(value.get(key))
        except (TypeError, ValueError):
            raise ValueError(f"Participant {key} is required") from None
        if not lower <= parsed <= upper:
            raise ValueError(f"Participant {key} is outside the accepted range")
        return str(int(parsed) if parsed.is_integer() else parsed)
    return {"name": name, "age": number("age", 1, 120), "height": number("height", 50, 260), "weight": number("weight", 10, 400)}


def _open_session_storage(session: BrowserGaitSession) -> None:
    folder = DATA_ROOT / session.session_id
    folder.mkdir(parents=True, exist_ok=True)
    session.storage_dir = folder
    _write_json(folder / "person.json", session.person)
    _write_json(folder / "session.json", {
        "sessionId": session.session_id, "createdAt": session.timestamp,
        "startedAt": datetime.now(UTC).isoformat(), "activity": session.activity_type,
        "durationSec": session.duration_sec, "views": session.views,
        "person": session.person,
    })


def _store_video_frame(session: BrowserGaitSession, view: str, jpeg: bytes) -> None:
    """Persist the actual browser frames for each selected view as a local MP4."""
    if not session.storage_dir:
        return
    image = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return
    height, width = image.shape[:2]
    size = session.video_sizes.get(view)
    writer = session.video_writers.get(view)
    if writer is None:
        output = session.storage_dir / f"{view}.mp4"
        writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (width, height))
        if not writer.isOpened():
            writer.release()
            return
        session.video_writers[view] = writer
        session.video_sizes[view] = (width, height)
        size = (width, height)
    if size and size != (width, height):
        image = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
    writer.write(image)


def _close_video_writers(session: BrowserGaitSession) -> None:
    for writer in session.video_writers.values():
        try:
            writer.release()
        except Exception:
            pass
    session.video_writers.clear()


def valid_session_id(session_id: str) -> bool:
    return bool(re.fullmatch(r"gait-[0-9a-f]{32}", session_id))


def _decode_compact_landmarks(raw_frames: object) -> list[dict]:
    """Validate browser pose payloads and rebuild indexed landmark arrays."""
    if not isinstance(raw_frames, list) or len(raw_frames) > 1800:
        raise ValueError("frames must contain at most 1800 compact frames")
    frames: list[dict] = []
    previous_t = -1.0
    allowed = {11, 12, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32}
    for raw in raw_frames:
        if not isinstance(raw, list) or len(raw) != 4:
            raise ValueError("Each frame must be [t, timestamp, seq, landmarks]")
        t, timestamp, sequence, points = raw
        if not isinstance(t, (int, float)) or not 0 <= float(t) <= 121 or float(t) < previous_t:
            raise ValueError("Frame time is invalid")
        if not isinstance(timestamp, str) or not isinstance(sequence, int) or not isinstance(points, list):
            raise ValueError("Frame metadata is invalid")
        previous_t = float(t)
        indexed = [{"index": index, "x": 0.0, "y": 0.0, "z": 0.0, "visibility": 0.0} for index in range(33)]
        seen: set[int] = set()
        for point in points:
            if not isinstance(point, list) or len(point) != 5:
                raise ValueError("Landmarks must be [index, x, y, z, visibility]")
            index, x, y, z, visibility = point
            if not isinstance(index, int) or index not in allowed or index in seen:
                raise ValueError("Landmark index is invalid")
            if not all(isinstance(value, (int, float)) for value in (x, y, z, visibility)):
                raise ValueError("Landmark coordinates must be numeric")
            if not -1.5 <= x <= 2.5 or not -1.5 <= y <= 2.5 or not -5 <= z <= 5 or not 0 <= visibility <= 1:
                raise ValueError("Landmark coordinate is outside the accepted range")
            seen.add(index)
            indexed[index] = {"index": index, "x": float(x), "y": float(y), "z": float(z), "visibility": float(visibility)}
        frames.append({"t": round(float(t), 3), "timestamp": timestamp, "keypoints": [point for point in indexed if point["visibility"] > 0]})
    return frames


def browser_analysis_result(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Analysis payload must be an object")
    view = payload.get("view")
    if view not in {"left", "back", "right"}:
        raise ValueError("view must be left, back, or right")
    session_id = str(payload.get("sessionId") or "")
    if not valid_session_id(session_id):
        raise ValueError("Invalid GAIT session ID")
    duration = payload.get("durationSec")
    if duration not in {30, 60, 120}:
        raise ValueError("durationSec must be 30, 60, or 120")
    person = _clean_person(payload.get("person"))
    activity = str(payload.get("activityType") or "Normal Walk")[:32]
    frames = _decode_compact_landmarks(payload.get("frames"))
    sent = payload.get("sentCount", len(frames))
    if not isinstance(sent, int) or sent < len(frames) or sent > 1800:
        raise ValueError("sentCount is invalid")
    analysis = analyse_session(activity, frames, sent)
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    detail = {"view": view, "cameraLabel": str(metadata.get("cameraLabel") or "Browser camera")[:120], "rotation": metadata.get("rotation") if metadata.get("rotation") in {0, 90, 180, 270} else 0, "width": metadata.get("width") if isinstance(metadata.get("width"), int) else None, "height": metadata.get("height") if isinstance(metadata.get("height"), int) else None, "fps": metadata.get("fps") if isinstance(metadata.get("fps"), (int, float)) else None, "sent": sent, "received": len(frames), "detected": analysis["detectedFrames"], "detectionRate": round(analysis["detectedFrames"] / max(1, len(frames)), 3), "gaps": analysis["quality"]["missingSegments"], "state": "ready"}
    metrics = {name: {**value, "sourceViews": [view]} for name, value in analysis["metrics"].items()}
    return {"sessionId": session_id, "state": "ready", "activity": activity, "timestamp": datetime.now(UTC).isoformat(), "person": person, "frameCount": len(frames), "framesReceived": len(frames), "durationSec": analysis["durationSec"], "detectedFrames": analysis["detectedFrames"], "metrics": metrics, "quality": analysis["quality"], "timeSeries": analysis["timeSeries"], "landmarkTimeline": frames, "landmarksByView": {view: frames}, "views": [detail], "camera": {"name": detail["cameraLabel"], "fps": detail["fps"]}, "message": "Browser-side pose landmarks analyzed locally."}


def _view_metadata(session: BrowserGaitSession, view: str) -> dict:
    return next((item for item in session.views if item.get("view") == view), {
        "view": view, "cameraLabel": session.camera_name, "rotation": 0,
        "width": None, "height": None, "fps": session.camera_fps,
    })


def _view_details(session: BrowserGaitSession) -> list[dict]:
    details: list[dict] = []
    for view in [item.get("view") for item in session.views] or ["left"]:
        counts = session.view_counts.get(view, {})
        frames = session.landmark_frames_by_view.get(view, [])
        missing = []
        start = None
        for frame in frames:
            if not frame.get("keypoints") and start is None:
                start = frame.get("t", 0)
            elif frame.get("keypoints") and start is not None:
                missing.append({"start": round(start, 2), "end": round(frame.get("t", start), 2)})
                start = None
        if start is not None and frames:
            missing.append({"start": round(start, 2), "end": round(frames[-1].get("t", start), 2)})
        metadata = _view_metadata(session, view)
        received = counts.get("received", 0)
        details.append({
            "view": view, "cameraLabel": metadata.get("cameraLabel", "Browser camera"),
            "rotation": metadata.get("rotation", 0), "width": metadata.get("width"),
            "height": metadata.get("height"), "fps": metadata.get("fps"),
            "sent": session.sent_counts.get(view, 0), "received": received,
            "detected": counts.get("detected", 0),
            "detectionRate": round(counts.get("detected", 0) / max(1, received), 3),
            "gaps": missing, "state": session.state,
        })
    return details


def _analyse_browser_session(session_id: str) -> None:
    with browser_sessions_lock:
        session = browser_sessions.get(session_id)
        if not session:
            return
        with session.lock:
            captured = {view: list(frames) for view, frames in session.landmark_frames_by_view.items()}
            counts = {view: values.get("received", 0) for view, values in session.view_counts.items()}
            activity = session.activity_type
    try:
        analyses = {view: analyse_session(activity, frames, counts.get(view, len(frames))) for view, frames in captured.items()}
        preferred = next((view for view in ("left", "right", "back") if view in analyses), "left")
        primary = analyses.get(preferred, analyse_session(activity, [], 0))
        metrics = dict(primary["metrics"])
        # Prefer an available value from another valid view over a fabricated fallback.
        for name, value in list(metrics.items()):
            source = preferred
            if not value.get("available"):
                for view, analysis in analyses.items():
                    candidate = analysis["metrics"].get(name)
                    if candidate and candidate.get("available"):
                        value, source = candidate, view
                        metrics[name] = value
                        break
            metrics[name] = {**value, "sourceViews": [source] if source in analyses else []}
        with browser_sessions_lock:
            current = browser_sessions.get(session_id)
            if not current:
                return
            with current.lock:
                current.result = {**primary, "metrics": metrics, "analyses": analyses, "primaryView": preferred}
                current.state = "ready"
                current.analysis_error = None
                if current.storage_dir:
                    _write_json(current.storage_dir / "result.json", session_result(current))
    except Exception as error:
        with browser_sessions_lock:
            current = browser_sessions.get(session_id)
            if current:
                with current.lock:
                    current.state = "failed"
                    current.analysis_error = str(error)


def session_result(session: BrowserGaitSession) -> dict:
    analysis = session.result or analyse_session(session.activity_type, list(session.landmark_frames), session.frames_received)
    primary_view = analysis.get("primaryView", "left")
    primary_frames = session.landmark_frames_by_view.get(primary_view, session.landmark_frames)
    has_capture = session.frames_received >= 3
    return {
        "sessionId": session.session_id,
        "state": session.state if session.state in {"created", "recording", "processing", "ready", "failed"} else ("captured" if has_capture else "insufficient-data"),
        "activity": session.activity_type,
        "timestamp": session.timestamp,
        "person": session.person,
        "frameCount": session.frames_received,
        "framesReceived": session.frames_received,
        "durationSec": analysis["durationSec"],
        "detectedFrames": analysis["detectedFrames"],
        "quality": analysis["quality"],
        "metrics": analysis["metrics"],
        "timeSeries": analysis["timeSeries"],
        "landmarkTimeline": list(primary_frames),
        "landmarksByView": {view: list(frames) for view, frames in session.landmark_frames_by_view.items()},
        "views": _view_details(session),
        "camera": {"name": session.camera_name, "fps": session.camera_fps},
        "message": session.analysis_error or (
            "Not enough frames were received to analyse this test. Try another capture."
            if not has_capture else ("Analyzing your movement." if session.state == "processing" else "Capture analysed from locally processed pose landmarks.")
        ),
    }


def browser_session_summaries() -> list[dict]:
    with browser_sessions_lock:
        sessions = list(browser_sessions.values())
    return [
        {
            "sessionId": session.session_id,
            "file": "",
            "name": f"{session.activity_type} test",
            "activity": session.activity_type,
            "date": session.timestamp,
            "frames": session.frames_received,
            "landmarks": 33 if session.detected_frames else 0,
            "sample_span_ms": round((session.result or {}).get("durationSec", 0) * 1000),
            "status": "saved" if session.state == "ready" else session.state,
            "size": 0,
            "source": "browser",
        }
        for session in sorted(sessions, key=lambda item: item.timestamp, reverse=True)
    ]


def allowed_origins() -> set[str]:
    configured = os.environ.get("GAIT_ALLOWED_ORIGINS", "")
    defaults = {
        "http://127.0.0.1:5173", "http://localhost:5173",
        "http://127.0.0.1:5174", "http://localhost:5174",
        "http://127.0.0.1:4173", "http://localhost:4173",
        "http://127.0.0.1:8765", "http://localhost:8765",
    }
    # Automatically trust *.vercel.app origins so preview deployments work
    # without having to hard-code each URL.
    vercel_origin = os.environ.get("VERCEL_URL", "")
    if vercel_origin:
        defaults.add(f"https://{vercel_origin}")
    return defaults | {origin.strip() for origin in configured.split(",") if origin.strip()}


def is_origin_allowed(origin: str | None) -> bool:
    if not origin:
        return True
    if origin in allowed_origins():
        return True
    try:
        host = urlparse(origin).netloc or urlparse(origin).path
        host = host.split(":")[0].lower()
        if host.endswith(".vercel.app") or host.endswith(".vercel.dev") or host == "vercel.app":
            return True
    except Exception:
        pass
    return False


def listed_cameras() -> list[dict]:
    """Return locally available video-capture devices for diagnostics.

    A BRIO exposes auxiliary metadata and greyscale nodes. ``find_cameras`` has
    already filtered those, and the node path is intentionally retained so
    identical BRIO labels remain distinguishable.

    Returns an empty list when running in serverless / cloud environments
    where no physical camera device is accessible.
    """
    if not HARDWARE_MODE:
        return []
    unique: dict[str, dict] = {}
    for camera in find_cameras():
        key = str(camera.path)
        unique.setdefault(key, {
            "id": str(camera.path),
            "label": camera.name,
            "node": str(camera.path),
            "connection": camera.connection,
            "modes": list(camera.modes),
        })
    return [unique[key] for key in sorted(unique)]


class CameraService:
    """Live USB-camera recording service.

    On Vercel (HARDWARE_MODE=False) this object is still instantiated so the
    rest of the module stays unchanged, but all methods are no-ops and status
    returns a clear ``unavailable`` state.
    """

    def __init__(self):
        self.lock = threading.RLock()
        self.thread = None
        self.cancel = threading.Event()
        self.jpeg = None
        self.state = "idle"
        self.error = ""
        self.camera_name = ""
        self.pose_fps = 0.0
        self.hand_fps = 0.0
        self.body_detected = False
        self.recorder = None
        self.deadline = None
        self.pending_recording = False
        self.last_seen = time.monotonic()

    def status(self):
        if not HARDWARE_MODE:
            return {
                "state": "unavailable",
                "error": "Camera hardware is not accessible in this environment.",
                "camera": "",
                "pose_fps": 0.0,
                "hand_fps": 0.0,
                "body_detected": False,
                "recording": "IDLE",
                "frames": 0,
                "remaining": 0,
                "file": None,
                "hardware_mode": False,
            }
        with self.lock:
            self.last_seen = time.monotonic()
            return {
                "state": self.state,
                "error": self.error,
                "camera": self.camera_name,
                "pose_fps": round(self.pose_fps, 1),
                "hand_fps": round(self.hand_fps, 1),
                "body_detected": self.body_detected,
                "recording": self.recorder.state.value if self.recorder else "IDLE",
                "frames": self.recorder.frame_count if self.recorder else 0,
                "remaining": max(0, round(self.deadline - time.monotonic())) if self.deadline else 60,
                "file": self.recorder.output_path.name if self.recorder and self.recorder.output_path else None,
                "hardware_mode": True,
            }

    def start(self, record=False):
        if not HARDWARE_MODE:
            raise RuntimeError("Camera hardware is not available in this environment.")
        with self.lock:
            if self.state == "stopping":
                raise RuntimeError("Camera is stopping. Please try again shortly.")
            if self.thread and self.thread.is_alive():
                if record:
                    if self.state == "running":
                        self._record()
                    else:
                        self.pending_recording = True
                return
            self.cancel.clear()
            self.last_seen = time.monotonic()
            self.jpeg = None
            self.error = ""
            self.camera_name = ""
            self.pose_fps = self.hand_fps = 0.0
            self.body_detected = False
            self.state = "starting"
            self.pending_recording = record
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def _record(self):
        if self.recorder and self.recorder.state is RecordingState.RECORDING:
            return
        self.recorder = GaitRecorder("web-gait-test", "walking", DATA_ROOT / "sessions")
        self.recorder.start()
        self.deadline = time.monotonic() + 60

    def stop(self):
        with self.lock:
            self.pending_recording = False
            self.cancel.set()
            if self.thread and self.thread.is_alive():
                self.state = "stopping"
            else:
                self.state = "idle"
            self._save()
            self.jpeg = None

    def _save(self):
        if self.recorder:
            self.recorder.stop()
        self.deadline = None

    def _run(self):
        camera = None
        try:
            with ExitStack() as resources:
                devices = find_cameras()
                requested_camera = os.environ.get("GAIT_CAMERA", "usb").strip()
                candidates = [
                    device for device in devices
                    if device.connection == "usb"
                    and not any(hint in device.name.lower() for hint in BUILT_IN_HINTS)
                ]
                if not candidates and requested_camera == "usb" and len(devices) == 1:
                    if devices[0].connection == "unknown":
                        candidates = devices
                elif requested_camera != "usb":
                    selected = select_camera(requested_camera, devices)
                    candidates = [selected] if selected else []
                for device in candidates:
                    if self.cancel.is_set():
                        return
                    candidate = open_camera(device, fps=30)
                    if candidate.isOpened():
                        readable, frame = candidate.read()
                        if readable:
                            camera = candidate
                            with self.lock:
                                self.camera_name = f"{device.name} ({device.path})"
                            break
                    candidate.release()
                if camera is None:
                    raise RuntimeError(
                        "No readable camera matched the selection. Connect a camera, close other "
                        "camera apps, or set GAIT_CAMERA to a listed device number (for example 0)."
                    )
                models = (ROOT / "models") if (ROOT / "models").is_dir() else (ROOT.parent / "models")
                for filename in ("pose_landmarker_lite.task", "hand_landmarker.task"):
                    if not (models / filename).is_file():
                        raise RuntimeError(f"Missing {filename}. Run scripts/setup.py first.")
                pose = resources.enter_context(mp.tasks.vision.PoseLandmarker.create_from_options(
                    mp.tasks.vision.PoseLandmarkerOptions(
                        base_options=mp.tasks.BaseOptions(model_asset_path=str(models / "pose_landmarker_lite.task")),
                        running_mode=mp.tasks.vision.RunningMode.VIDEO,
                        num_poses=1,
                        min_pose_detection_confidence=0.55,
                        min_pose_presence_confidence=0.55,
                        min_tracking_confidence=0.55,
                    )
                ))
                hands = resources.enter_context(mp.tasks.vision.HandLandmarker.create_from_options(
                    mp.tasks.vision.HandLandmarkerOptions(
                        base_options=mp.tasks.BaseOptions(model_asset_path=str(models / "hand_landmarker.task")),
                        running_mode=mp.tasks.vision.RunningMode.VIDEO,
                        num_hands=2,
                    )
                ))
                worker = InferenceWorker(pose, hands)
                resources.callback(worker.stop)
                smoother = LandmarkSmoother()
                previous_sequence = -1
                with self.lock:
                    if self.cancel.is_set():
                        return
                    self.state = "running"
                    if self.pending_recording:
                        self._record()
                        self.pending_recording = False
                while not self.cancel.is_set():
                    if time.monotonic() - self.last_seen > 15:
                        break
                    readable, frame = camera.read()
                    if not readable:
                        raise RuntimeError("Camera disconnected or stopped delivering frames. Reconnect and retry.")
                    if worker.error:
                        raise RuntimeError(worker.error)
                    worker.submit(cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA))
                    pose_result, hand_result, pose_fps, hand_fps, sequence, timestamp = worker.latest_results()
                    with self.lock:
                        self.pose_fps, self.hand_fps = pose_fps, hand_fps
                        self.body_detected = bool(pose_result and pose_result.pose_landmarks)
                        if self.deadline and time.monotonic() >= self.deadline:
                            self._save()
                        if self.recorder and sequence != previous_sequence and self.body_detected:
                            self.recorder.record_pose(pose_result.pose_landmarks[0], timestamp)
                        previous_sequence = sequence
                    if pose_result:
                        draw_pose(frame, pose_result, smoother)
                    if hand_result:
                        draw_hands(frame, hand_result, smoother)
                    encoded, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if encoded:
                        with self.lock:
                            self.jpeg = buffer.tobytes()
        except Exception as error:
            with self.lock:
                self.error = str(error)
                self.state = "error"
        finally:
            if camera is not None:
                camera.release()
            with self.lock:
                self._save()
                self.jpeg = None
                self.body_detected = False
                if self.state != "error":
                    self.state = "idle"


service = CameraService()


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        origin = self.headers.get("Origin")
        if origin and is_origin_allowed(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Gait-Control")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        origin = self.headers.get("Origin")
        if origin and not is_origin_allowed(origin):
            self._send(403, b'{"error":"Untrusted origin"}')
            return
        self._send(204, b"")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send(200, json.dumps({"state": "ready", "ok": True}).encode())
        elif path == "/api/sessions" or path.startswith("/api/sessions/"):
            with service.lock:
                recorder = service.recorder
                active_file = (
                    recorder.output_path.name
                    if recorder and recorder.output_path
                    and recorder.state in (RecordingState.RECORDING, RecordingState.PAUSED)
                    else None
                )
            directory = DATA_ROOT / "sessions"
            if path == "/api/sessions":
                payload = browser_session_summaries() + list_sessions(directory, active_file)
                self._send(200, json.dumps(payload).encode())
            else:
                filename = unquote(path.removeprefix("/api/sessions/"))
                try:
                    if filename == active_file:
                        self._send(409, b'{"error":"Recording is still active"}')
                        return
                    self._send(200, session_path(directory, filename).read_bytes(), "text/csv; charset=utf-8")
                except (ValueError, OSError):
                    self._send(404, b'{"error":"Session not found"}')
        elif path == "/api/status":
            self._send(200, json.dumps(service.status()).encode())
        elif path == "/api/hardware":
            self._send(200, json.dumps({"hardware_mode": HARDWARE_MODE}).encode())
        elif path == "/api/cameras":
            self._send(200, json.dumps(listed_cameras()).encode())
        elif path.startswith("/api/gait/result/"):
            session_id = unquote(path.removeprefix("/api/gait/result/"))
            if not valid_session_id(session_id):
                self._send(400, b'{"error":"Invalid GAIT session ID"}')
                return
            with browser_sessions_lock:
                session = browser_sessions.get(session_id)
                if not session:
                    self._send(404, b'{"error":"GAIT session not found"}')
                    return
                with session.lock:
                    payload = session_result(session)
            self._send(200, json.dumps(payload).encode())
        elif path == "/api/frame":
            with service.lock:
                frame = service.jpeg
            self._send(200 if frame else 503, frame or b"Camera not ready", "image/jpeg" if frame else "text/plain")
        else:
            self._send(404, b'{"error":"Not found"}')

    def do_POST(self):
        origin = self.headers.get("Origin")
        if self.headers.get("X-Gait-Control") != "1" or (origin and not is_origin_allowed(origin)):
            self._send(403, b'{"error":"Untrusted control request"}')
            return
        try:
            path = urlparse(self.path).path
            if path == "/api/session/create":
                created_at = datetime.now(UTC).isoformat()
                session = BrowserGaitSession(session_id=f"gait-{uuid4().hex}", timestamp=created_at)
                with browser_sessions_lock:
                    browser_sessions[session.session_id] = session
                self._send(201, json.dumps({"sessionId": session.session_id, "timestamp": session.timestamp}).encode())
                return
            if path == "/api/analyze":
                try:
                    content_length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < content_length <= 4_000_000:
                        self._send(413, b'{"error":"Analysis payload must be smaller than 4 MB"}')
                        return
                    result = browser_analysis_result(json.loads(self.rfile.read(content_length)))
                except (ValueError, json.JSONDecodeError) as error:
                    self._send(400, json.dumps({"error": str(error)}).encode())
                    return
                self._send(200, json.dumps(result).encode())
                return
            if path == "/api/gait/start":
                try:
                    content_length = int(self.headers.get("Content-Length", "0"))
                    payload = json.loads(self.rfile.read(content_length or 0) or b"{}")
                except (ValueError, json.JSONDecodeError):
                    self._send(400, b'{"error":"Invalid GAIT start payload"}')
                    return
                requested_id = payload.get("sessionId")
                activity = payload.get("activityType")
                if not isinstance(requested_id, str) or not valid_session_id(requested_id) or not isinstance(activity, str):
                    self._send(400, b'{"error":"sessionId and activityType are required"}')
                    return
                try:
                    person = _clean_person(payload.get("person"))
                    duration_sec = int(payload.get("durationSec", 30))
                    if duration_sec not in {30, 60, 120}:
                        raise ValueError("Capture duration must be 30, 60, or 120 seconds")
                except (TypeError, ValueError) as error:
                    self._send(400, json.dumps({"error": str(error)}).encode())
                    return
                raw_views = payload.get("views")
                views = []
                if isinstance(raw_views, list):
                    for raw in raw_views:
                        if not isinstance(raw, dict) or raw.get("view") not in {"left", "back", "right"}:
                            continue
                        if any(view["view"] == raw["view"] for view in views):
                            continue
                        views.append({
                            "view": raw["view"],
                            "cameraLabel": str(raw.get("cameraLabel") or "Browser camera")[:160],
                            "rotation": int(raw.get("rotation", 0)) % 360,
                            "width": raw.get("width") if isinstance(raw.get("width"), int) else None,
                            "height": raw.get("height") if isinstance(raw.get("height"), int) else None,
                            "fps": round(float(raw["fps"]), 1) if isinstance(raw.get("fps"), (int, float)) else None,
                        })
                if not views:
                    camera = payload.get("camera") if isinstance(payload.get("camera"), dict) else {}
                    views = [{"view": "left", "cameraLabel": str(camera.get("name") or "Browser camera")[:160], "rotation": 0, "width": None, "height": None, "fps": camera.get("fps") if isinstance(camera.get("fps"), (int, float)) else None}]
                with browser_sessions_lock:
                    session = browser_sessions.get(requested_id)
                    if not session:
                        self._send(404, b'{"error":"GAIT session not found"}')
                        return
                    with session.lock:
                        session.activity_type = activity[:80]
                        session.state = "recording"
                        session.started_at = time.monotonic()
                        session.stopped_at = None
                        session.frames_received = 0
                        session.detected_frames = 0
                        session.landmark_frames.clear()
                        session.views = views
                        session.landmark_frames_by_view = {view["view"]: [] for view in views}
                        session.view_counts = {view["view"]: {"received": 0, "detected": 0} for view in views}
                        session.received_sequences.clear()
                        session.sent_counts.clear()
                        session.analysis_error = None
                        session.result = None
                        session.camera_name = views[0]["cameraLabel"]
                        session.camera_fps = views[0]["fps"]
                        session.person = person
                        session.duration_sec = duration_sec
                        _close_video_writers(session)
                        _open_session_storage(session)
                self._send(200, json.dumps({"sessionId": requested_id, "state": "recording"}).encode())
                return
            if path.startswith("/api/gait/stop/"):
                requested_id = unquote(path.removeprefix("/api/gait/stop/"))
                if not valid_session_id(requested_id):
                    self._send(400, b'{"error":"Invalid GAIT session ID"}')
                    return
                try:
                    content_length = int(self.headers.get("Content-Length", "0"))
                    stop_payload = json.loads(self.rfile.read(content_length or 0) or b"{}")
                except (ValueError, json.JSONDecodeError):
                    stop_payload = {}
                with browser_sessions_lock:
                    session = browser_sessions.get(requested_id)
                    if not session:
                        self._send(404, b'{"error":"GAIT session not found"}')
                        return
                    with session.lock:
                        session.state = "processing"
                        session.stopped_at = datetime.now(UTC).isoformat()
                        sent = stop_payload.get("sentCounts") if isinstance(stop_payload, dict) else None
                        session.sent_counts = {str(view): int(count) for view, count in sent.items() if view in {"left", "back", "right"} and isinstance(count, int) and count >= 0} if isinstance(sent, dict) else {}
                        _close_video_writers(session)
                threading.Thread(target=_analyse_browser_session, args=(requested_id,), daemon=True).start()
                self._send(202, json.dumps({"sessionId": requested_id, "state": "processing"}).encode())
                return
            if path.startswith("/api/frame/"):
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)
                session_id = unquote(path.removeprefix("/api/frame/"))
                view = query.get("view", ["left"])[0].lower()
                if view not in {"left", "back", "right"}:
                    self._send(400, b'{"error":"Frame view must be left, back, or right"}')
                    return
                try:
                    sequence = int(query.get("seq", ["-1"])[0])
                except ValueError:
                    sequence = -1
                try:
                    client_t = max(0.0, float(query.get("t", ["0"])[0]) / 1000)
                except ValueError:
                    client_t = 0.0
                if not valid_session_id(session_id):
                    self._send(400, b'{"error":"Invalid GAIT session ID"}')
                    return
                try:
                    content_length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    content_length = 0
                if not 0 < content_length <= MAX_FRAME_BYTES:
                    self._send(413, b'{"error":"Frame must be a JPEG smaller than 2 MB"}')
                    return
                frame = self.rfile.read(content_length)
                if not frame.startswith(b"\xff\xd8"):
                    self._send(415, b'{"error":"Frame must be JPEG data"}')
                    return
                with browser_sessions_lock:
                    session = browser_sessions.get(session_id)
                    if not session:
                        self._send(404, b'{"error":"GAIT session not found"}')
                        return
                    with session.lock:
                        if sequence >= 0 and (view, sequence) in session.received_sequences:
                            count = session.view_counts.get(view, {}).get("received", 0)
                            self._send(200, json.dumps({"accepted": True, "framesReceived": count, "view": view, "seq": sequence, "bodyDetected": False, "keypoints": [], "deduplicated": True}).encode())
                            return
                try:
                    keypoints = browser_pose.process(frame)
                except ValueError as error:
                    self._send(415, json.dumps({"error": str(error)}).encode())
                    return
                except RuntimeError as error:
                    self._send(503, json.dumps({"error": str(error)}).encode())
                    return
                captured_at = datetime.now(UTC).isoformat()
                with browser_sessions_lock:
                    session = browser_sessions.get(session_id)
                    if not session:
                        self._send(404, b'{"error":"GAIT session not found"}')
                        return
                    with session.lock:
                        elapsed = client_t if client_t > 0 else (max(0.0, time.monotonic() - session.started_at) if session.started_at else 0.0)
                        if session.state == "recording":
                            _store_video_frame(session, view, frame)
                            session.frames_received += 1
                            session.last_frame_at = captured_at
                            if keypoints:
                                session.detected_frames += 1
                            frames = session.landmark_frames_by_view.setdefault(view, [])
                            frames.append({"t": round(elapsed, 4), "timestamp": captured_at, "keypoints": keypoints, "view": view, "seq": sequence})
                            session.landmark_frames = frames
                            counts = session.view_counts.setdefault(view, {"received": 0, "detected": 0})
                            counts["received"] += 1
                            if keypoints:
                                counts["detected"] += 1
                            if sequence >= 0:
                                session.received_sequences.add((view, sequence))
                        count = session.view_counts.get(view, {}).get("received", 0)
                self._send(202, json.dumps({
                    "accepted": True,
                    "framesReceived": count,
                    "view": view,
                    "seq": sequence,
                    "detectedCount": session.view_counts.get(view, {}).get("detected", 0),
                    "bodyDetected": bool(keypoints),
                    "keypoints": keypoints,
                    "timestamp": captured_at,
                    "elapsedSec": round(elapsed, 4),
                }).encode())
                return
            if path in ("/api/camera/start", "/api/test/start", "/api/camera/stop"):
                if not HARDWARE_MODE:
                    self._send(503, json.dumps({
                        "error": "Camera hardware is not available in this deployment.",
                        "hardware_mode": False,
                    }).encode())
                    return
                if path == "/api/camera/start":
                    service.start()
                elif path == "/api/test/start":
                    service.start(record=True)
                elif path == "/api/camera/stop":
                    service.stop()
                self._send(200, json.dumps(service.status()).encode())
            else:
                self._send(404, b'{"error":"Not found"}')
                return
        except Exception as error:
            self._send(409, json.dumps({"error": str(error)}).encode())

    def do_DELETE(self):
        origin = self.headers.get("Origin")
        if self.headers.get("X-Gait-Control") != "1" or (origin and not is_origin_allowed(origin)):
            self._send(403, b'{"error":"Untrusted control request"}')
            return
        path = urlparse(self.path).path
        if not path.startswith("/api/session/"):
            self._send(404, b'{"error":"Not found"}')
            return
        session_id = unquote(path.removeprefix("/api/session/"))
        if not valid_session_id(session_id):
            self._send(400, b'{"error":"Invalid GAIT session ID"}')
            return
        with browser_sessions_lock:
            removed = browser_sessions.pop(session_id, None)
        if not removed:
            self._send(404, b'{"error":"GAIT session not found"}')
            return
        self._send(200, json.dumps({"sessionId": session_id, "deleted": True}).encode())

    def log_message(self, format, *args):
        pass


def main():
    def shutdown(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, shutdown)
    host = os.environ.get("GAIT_HOST", "127.0.0.1")
    port = int(os.environ.get("GAIT_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Gait backend ready at http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        service.stop()
        browser_pose.close()
        if service.thread:
            service.thread.join(timeout=10)
        server.server_close()


if __name__ == "__main__":
    main()
