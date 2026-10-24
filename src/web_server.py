import json
import os
import signal
import threading
import time
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".cache/matplotlib"))

import cv2
import mediapipe as mp

from src.cameras import BUILT_IN_HINTS, find_cameras, open_camera
from src.pose_camera import InferenceWorker, LandmarkSmoother, draw_hands, draw_pose
from src.recorder import GaitRecorder, RecordingState
from src.sessions import list_sessions, session_path


ROOT = Path(__file__).resolve().parents[1]


class CameraService:
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
            }

    def start(self, record=False):
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
        self.recorder = GaitRecorder("web-gait-test", "walking", ROOT / "data/sessions")
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
                candidates = [
                    device for device in find_cameras()
                    if device.connection == "usb"
                    and not any(hint in device.name.lower() for hint in BUILT_IN_HINTS)
                ]
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
                    raise RuntimeError("No readable external USB camera found. Connect it, close other camera apps, and retry.")
                models = ROOT / "models"
                for filename in ("pose_landmarker_lite.task", "hand_landmarker.task"):
                    if not (models / filename).is_file():
                        raise RuntimeError(f"Missing {filename}. Run scripts/setup.sh first.")
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
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/sessions" or path.startswith("/api/sessions/"):
            with service.lock:
                recorder = service.recorder
                active_file = (
                    recorder.output_path.name
                    if recorder and recorder.output_path
                    and recorder.state in (RecordingState.RECORDING, RecordingState.PAUSED)
                    else None
                )
            directory = ROOT / "data/sessions"
            if path == "/api/sessions":
                self._send(200, json.dumps(list_sessions(directory, active_file)).encode())
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
        elif path == "/api/frame":
            with service.lock:
                frame = service.jpeg
            self._send(200 if frame else 503, frame or b"Camera not ready", "image/jpeg" if frame else "text/plain")
        else:
            self._send(404, b'{"error":"Not found"}')

    def do_POST(self):
        origin = self.headers.get("Origin")
        if self.headers.get("X-Gait-Control") != "1" or (origin and origin not in {
            "http://127.0.0.1:5173", "http://localhost:5173",
            "http://127.0.0.1:4173", "http://localhost:4173",
            "http://127.0.0.1:8765",
        }):
            self._send(403, b'{"error":"Untrusted control request"}')
            return
        try:
            path = urlparse(self.path).path
            if path == "/api/camera/start":
                service.start()
            elif path == "/api/test/start":
                service.start(record=True)
            elif path == "/api/camera/stop":
                service.stop()
            else:
                self._send(404, b'{"error":"Not found"}')
                return
            self._send(200, json.dumps(service.status()).encode())
        except Exception as error:
            self._send(409, json.dumps({"error": str(error)}).encode())

    def log_message(self, format, *args):
        pass


def main():
    def shutdown(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, shutdown)
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Gait backend ready at http://127.0.0.1:8765", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        service.stop()
        if service.thread:
            service.thread.join(timeout=10)
        server.server_close()


if __name__ == "__main__":
    main()
