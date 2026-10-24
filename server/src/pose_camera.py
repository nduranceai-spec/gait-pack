import argparse
import json
import math
import os
from pathlib import Path
import queue
import subprocess
import threading
import time

os.environ.setdefault("MPLCONFIGDIR", ".cache/matplotlib")

import cv2
import mediapipe as mp

from src.cameras import find_cameras, open_camera, print_cameras, select_camera
from src.recorder import GaitRecorder, RecordingState


SERVER_ROOT = Path(__file__).resolve().parents[1]
FAST_POSE_MODEL_PATH = SERVER_ROOT / "models" / "pose_landmarker_lite.task"
ACCURATE_POSE_MODEL_PATH = SERVER_ROOT / "models" / "pose_landmarker_full.task"
HAND_MODEL_PATH = SERVER_ROOT / "models" / "hand_landmarker.task"
WINDOW_NAME = "G3-V2 Gait Data Recorder"
FIRST_BODY_LANDMARK = 11
TARGET_CAMERA_FPS = 60
INFERENCE_WIDTH = 640
INFERENCE_HEIGHT = 360
HAND_SEARCH_INTERVAL = 0.20
HAND_TRACK_INTERVAL = 1 / 15


class InferenceWorker:
    def __init__(self, pose_landmarker, hand_landmarker) -> None:
        self.pose_landmarker = pose_landmarker
        self.hand_landmarker = hand_landmarker
        self.pose_frames: queue.Queue = queue.Queue(maxsize=1)
        self.hand_frames: queue.Queue = queue.Queue(maxsize=1)
        self.lock = threading.Lock()
        self.running = True
        self.error = ""
        self.pose_result = None
        self.hand_result = None
        self.pose_fps = 0.0
        self.hand_fps = 0.0
        self.pose_sequence = 0
        self.pose_timestamp_ms = 0
        self.hand_active = False
        self.last_hand_submit = 0.0
        self.pose_thread = threading.Thread(target=self._run_pose, daemon=True)
        self.hand_thread = threading.Thread(target=self._run_hands, daemon=True)
        self.pose_thread.start()
        self.hand_thread.start()

    def submit(self, frame) -> None:
        self._offer_latest(self.pose_frames, frame)
        now = time.monotonic()
        with self.lock:
            hand_active = self.hand_active
        interval = HAND_TRACK_INTERVAL if hand_active else HAND_SEARCH_INTERVAL
        if now - self.last_hand_submit >= interval:
            self._offer_latest(self.hand_frames, frame)
            self.last_hand_submit = now

    @staticmethod
    def _offer_latest(frame_queue: queue.Queue, frame) -> None:
        if frame_queue.full():
            try:
                frame_queue.get_nowait()
            except queue.Empty:
                pass
        try:
            frame_queue.put_nowait(frame)
        except queue.Full:
            pass

    def latest_results(self):
        with self.lock:
            return (
                self.pose_result,
                self.hand_result,
                self.pose_fps,
                self.hand_fps,
                self.pose_sequence,
                self.pose_timestamp_ms,
            )

    def stop(self) -> None:
        self.running = False
        self.pose_thread.join()
        self.hand_thread.join()

    def _run_pose(self) -> None:
        start_time = time.monotonic()
        previous_time = start_time
        while self.running:
            try:
                frame = self.pose_frames.get(timeout=0.1)
            except queue.Empty:
                continue
            image = self._make_image(frame)
            timestamp_ms = int((time.monotonic() - start_time) * 1000)
            try:
                pose_result = self.pose_landmarker.detect_for_video(image, timestamp_ms)
            except Exception as error:
                self.error = f"Pose tracking failed: {error}"
                self.running = False
                return
            now = time.monotonic()
            rate = 1.0 / max(now - previous_time, 0.0001)
            previous_time = now
            with self.lock:
                self.pose_result = pose_result
                self.pose_fps = self._smooth_rate(self.pose_fps, rate)
                self.pose_sequence += 1
                self.pose_timestamp_ms = timestamp_ms

    def _run_hands(self) -> None:
        start_time = time.monotonic()
        previous_time = start_time
        while self.running:
            try:
                frame = self.hand_frames.get(timeout=0.1)
            except queue.Empty:
                continue
            image = self._make_image(frame)
            timestamp_ms = int((time.monotonic() - start_time) * 1000)
            try:
                hand_result = self.hand_landmarker.detect_for_video(image, timestamp_ms)
            except Exception as error:
                self.error = f"Hand tracking failed: {error}"
                self.running = False
                return
            now = time.monotonic()
            rate = 1.0 / max(now - previous_time, 0.0001)
            previous_time = now
            with self.lock:
                self.hand_result = hand_result
                self.hand_fps = self._smooth_rate(self.hand_fps, rate)
                self.hand_active = bool(hand_result.hand_landmarks)

    @staticmethod
    def _make_image(frame) -> mp.Image:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    @staticmethod
    def _smooth_rate(current: float, new_rate: float) -> float:
        return new_rate if current == 0.0 else current * 0.85 + new_rate * 0.15


def get_screen_size() -> tuple[int, int]:
    try:
        result = subprocess.run(
            ["hyprctl", "-j", "monitors"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
        monitors = json.loads(result.stdout)
        monitor = next(
            (item for item in monitors if item.get("focused")),
            monitors[0],
        )
        return int(monitor["width"]), int(monitor["height"])
    except (FileNotFoundError, subprocess.SubprocessError, ValueError, KeyError):
        return 1920, 1080


def crop_to_fill(frame, target_width: int, target_height: int):
    height, width = frame.shape[:2]
    scale = max(target_width / width, target_height / height)
    resized_width = round(width * scale)
    resized_height = round(height * scale)
    resized = cv2.resize(
        frame,
        (resized_width, resized_height),
        interpolation=cv2.INTER_LINEAR,
    )
    left = (resized_width - target_width) // 2
    top = (resized_height - target_height) // 2
    return resized[top : top + target_height, left : left + target_width]


class LandmarkSmoother:
    def __init__(self) -> None:
        self.points: dict[tuple[str, int, int], tuple[float, float]] = {}

    def smooth(
        self,
        group: str,
        group_index: int,
        landmark_index: int,
        x: float,
        y: float,
        width: int,
        height: int,
    ) -> tuple[int, int]:
        key = (group, group_index, landmark_index)
        previous = self.points.get(key)
        if previous is None:
            smoothed = (x, y)
        else:
            movement = math.hypot(
                (x - previous[0]) * width,
                (y - previous[1]) * height,
            )
            if movement < 3:
                alpha = 0.12
            elif movement < 15:
                alpha = 0.35
            else:
                alpha = 0.70
            smoothed = (
                previous[0] + alpha * (x - previous[0]),
                previous[1] + alpha * (y - previous[1]),
            )
        self.points[key] = smoothed
        return int(smoothed[0] * width), int(smoothed[1] * height)

    def clear_group(self, group: str) -> None:
        self.points = {
            key: point for key, point in self.points.items() if key[0] != group
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CPU pose detection from one camera")
    parser.add_argument(
        "--camera",
        default="usb",
        help="usb (default), built-in, a numeric device index such as 0, or Linux /dev/video2",
    )
    parser.add_argument(
        "--list-cameras",
        action="store_true",
        help="list camera devices and exit",
    )
    parser.add_argument(
        "--quality",
        choices=("fast", "accurate"),
        default="fast",
        help="fast uses the lite pose model; accurate uses the slower full model",
    )
    parser.add_argument(
        "--session-name",
        default="gait-session",
        help="name stored with the CSV session",
    )
    parser.add_argument(
        "--activity",
        default="walking",
        help="activity label, for example walking or running",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=SERVER_ROOT / "data" / "sessions",
        help="folder for recorded CSV files",
    )
    parser.add_argument(
        "--include-face",
        action="store_true",
        help="store all 33 landmarks instead of the default 22 body landmarks",
    )
    return parser.parse_args()


def draw_pose(frame, result, smoother: LandmarkSmoother) -> None:
    height, width = frame.shape[:2]
    if not result.pose_landmarks:
        smoother.clear_group("pose")
        return

    pose = result.pose_landmarks[0]
    points: dict[int, tuple[int, int]] = {}
    for index, landmark in enumerate(pose):
        if index < FIRST_BODY_LANDMARK or landmark.visibility < 0.55:
            continue
        points[index] = smoother.smooth(
            "pose", 0, index, landmark.x, landmark.y, width, height
        )

    for connection in mp.tasks.vision.PoseLandmarksConnections.POSE_LANDMARKS:
        if connection.start in points and connection.end in points:
            cv2.line(
                frame,
                points[connection.start],
                points[connection.end],
                (0, 210, 255),
                3,
                cv2.LINE_AA,
            )

    for point in points.values():
        cv2.circle(frame, point, 4, (0, 255, 80), -1, cv2.LINE_AA)


def draw_hands(frame, result, smoother: LandmarkSmoother) -> None:
    height, width = frame.shape[:2]
    if not result.hand_landmarks:
        smoother.clear_group("hand")
        return

    for hand_index, hand in enumerate(result.hand_landmarks):
        points = {
            index: smoother.smooth(
                "hand", hand_index, index, landmark.x, landmark.y, width, height
            )
            for index, landmark in enumerate(hand)
        }
        for connection in mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS:
            cv2.line(
                frame,
                points[connection.start],
                points[connection.end],
                (255, 180, 0),
                1,
                cv2.LINE_AA,
            )
        for point in points.values():
            cv2.circle(frame, point, 2, (255, 255, 255), -1, cv2.LINE_AA)


def main() -> int:
    cv2.setUseOptimized(True)
    args = parse_args()
    cameras = find_cameras()
    if args.list_cameras:
        print_cameras(cameras)
        return 0

    device = select_camera(args.camera, cameras)
    if device is None:
        print_cameras(cameras)
        return 1

    pose_model_path = (
        FAST_POSE_MODEL_PATH if args.quality == "fast" else ACCURATE_POSE_MODEL_PATH
    )
    missing_models = [
        path for path in (pose_model_path, HAND_MODEL_PATH) if not path.exists()
    ]
    if missing_models:
        print("Missing model files:")
        for path in missing_models:
            print(f"  {path}")
        print("Run the cross-platform setup command from README.md first.")
        return 1

    pose_base_options = mp.tasks.BaseOptions(
        model_asset_path=str(pose_model_path),
        delegate=mp.tasks.BaseOptions.Delegate.CPU,
    )
    pose_options = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=pose_base_options,
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.55,
        min_pose_presence_confidence=0.55,
        min_tracking_confidence=0.55,
    )
    hand_base_options = mp.tasks.BaseOptions(
        model_asset_path=str(HAND_MODEL_PATH),
        delegate=mp.tasks.BaseOptions.Delegate.CPU,
    )
    hand_options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=hand_base_options,
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.60,
        min_hand_presence_confidence=0.60,
        min_tracking_confidence=0.60,
    )

    print(f"Using camera: {device.path} - {device.name}")
    camera = open_camera(device, fps=TARGET_CAMERA_FPS)
    if not camera.isOpened():
        print(f"Could not open {device.path}.")
        print("Close other camera applications and check camera permissions.")
        return 1

    actual_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_camera_fps = camera.get(cv2.CAP_PROP_FPS)
    print(
        f"Camera mode: {actual_width}x{actual_height} "
        f"at {actual_camera_fps:.1f} FPS"
    )
    print(
        f"Tracking profile: {args.quality}, inference: "
        f"{INFERENCE_WIDTH}x{INFERENCE_HEIGHT}"
    )

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    screen_width, screen_height = get_screen_size()
    fullscreen = True
    smoother = LandmarkSmoother()
    recorder = GaitRecorder(
        session_name=args.session_name,
        activity=args.activity,
        output_dir=args.output_dir,
        include_face=args.include_face,
    )
    last_recorded_pose_sequence = -1
    display_fps = 0.0
    previous_frame_time = time.monotonic()
    with (
        mp.tasks.vision.PoseLandmarker.create_from_options(
            pose_options
        ) as pose_landmarker,
        mp.tasks.vision.HandLandmarker.create_from_options(
            hand_options
        ) as hand_landmarker,
    ):
        worker = InferenceWorker(pose_landmarker, hand_landmarker)
        try:
            while True:
                ok, frame = camera.read()
                if not ok:
                    print("Camera stopped returning frames.")
                    break

                inference_frame = cv2.resize(
                    frame,
                    (INFERENCE_WIDTH, INFERENCE_HEIGHT),
                    interpolation=cv2.INTER_AREA,
                )
                worker.submit(inference_frame)
                (
                    pose_result,
                    hand_result,
                    pose_fps,
                    hand_fps,
                    pose_sequence,
                    pose_timestamp_ms,
                ) = worker.latest_results()
                if pose_result is not None:
                    draw_pose(frame, pose_result, smoother)
                    if (
                        pose_sequence != last_recorded_pose_sequence
                        and pose_result.pose_landmarks
                    ):
                        recorder.record_pose(
                            pose_result.pose_landmarks[0], pose_timestamp_ms
                        )
                        last_recorded_pose_sequence = pose_sequence
                if hand_result is not None:
                    draw_hands(frame, hand_result, smoother)

                now = time.monotonic()
                instant_fps = 1.0 / max(now - previous_frame_time, 0.0001)
                previous_frame_time = now
                display_fps = (
                    instant_fps
                    if display_fps == 0.0
                    else display_fps * 0.90 + instant_fps * 0.10
                )

                if fullscreen:
                    output = crop_to_fill(frame, screen_width, screen_height)
                else:
                    output = frame

                overlay_y = output.shape[0] - 24
                if recorder.state is RecordingState.RECORDING:
                    recording_text = (
                        f"RECORDING | {recorder.frame_count} frames | "
                        f"{recorder.landmark_count} landmarks"
                    )
                    recording_color = (80, 80, 255)
                elif recorder.state is RecordingState.PAUSED:
                    recording_text = f"PAUSED | {recorder.frame_count} frames"
                    recording_color = (0, 210, 255)
                elif recorder.state is RecordingState.STOPPED:
                    recording_text = f"SAVED | {recorder.frame_count} frames"
                    recording_color = (80, 255, 140)
                else:
                    recording_text = (
                        "R: start recording | P: pause/resume | S: save and stop"
                    )
                    recording_color = (255, 255, 255)
                cv2.putText(
                    output,
                    recording_text,
                    (20, 38),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.72,
                    (0, 0, 0),
                    4,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    output,
                    recording_text,
                    (20, 38),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.72,
                    recording_color,
                    1,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    output,
                    f"Display {display_fps:.0f} | Pose ML {pose_fps:.0f} | "
                    f"Hand ML {hand_fps:.0f} | Camera {actual_camera_fps:.0f} FPS",
                    (20, overlay_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (0, 0, 0),
                    4,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    output,
                    f"Display {display_fps:.0f} | Pose ML {pose_fps:.0f} | "
                    f"Hand ML {hand_fps:.0f} | Camera {actual_camera_fps:.0f} FPS",
                    (20, overlay_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )
                cv2.imshow(WINDOW_NAME, output)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
                if key == ord("r") and recorder.state is RecordingState.IDLE:
                    output_path = recorder.start()
                    print(f"Recording started: {output_path}")
                if key == ord("p"):
                    if recorder.state is RecordingState.RECORDING:
                        recorder.pause()
                        print("Recording paused.")
                    elif recorder.state is RecordingState.PAUSED:
                        recorder.resume()
                        print("Recording resumed.")
                if key == ord("s"):
                    output_path = recorder.stop()
                    if output_path is not None:
                        print(f"Recording saved: {output_path}")
                if key == ord("f"):
                    fullscreen = not fullscreen
                    mode = cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL
                    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, mode)
        finally:
            output_path = recorder.stop()
            if output_path is not None:
                print(f"Recording file: {output_path}")
            worker.stop()

    camera.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
