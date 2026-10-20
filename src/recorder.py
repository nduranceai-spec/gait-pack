import csv
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import re
import time
import uuid


LANDMARK_NAMES = (
    "nose",
    "left_eye_inner",
    "left_eye",
    "left_eye_outer",
    "right_eye_inner",
    "right_eye",
    "right_eye_outer",
    "left_ear",
    "right_ear",
    "mouth_left",
    "mouth_right",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_pinky",
    "right_pinky",
    "left_index",
    "right_index",
    "left_thumb",
    "right_thumb",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
    "left_heel",
    "right_heel",
    "left_foot_index",
    "right_foot_index",
)
BODY_LANDMARK_START = 11
CSV_FIELDS = (
    "session_id",
    "session_name",
    "activity",
    "frame_index",
    "timestamp_utc",
    "elapsed_ms",
    "model_timestamp_ms",
    "landmark_index",
    "landmark_name",
    "x",
    "y",
    "z",
    "visibility",
    "presence",
)


class RecordingState(str, Enum):
    IDLE = "IDLE"
    RECORDING = "RECORDING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class GaitRecorder:
    def __init__(
        self,
        session_name: str,
        activity: str,
        output_dir: Path,
        include_face: bool = False,
    ) -> None:
        self.session_name = session_name.strip() or "gait-session"
        self.activity = activity.strip() or "walking"
        self.output_dir = output_dir
        self.include_face = include_face
        self.state = RecordingState.IDLE
        self.session_id = ""
        self.output_path: Path | None = None
        self.frame_count = 0
        self.row_count = 0
        self._file = None
        self._writer = None
        self._started_at = 0.0
        self._paused_at = 0.0
        self._paused_duration = 0.0

    @property
    def landmark_count(self) -> int:
        return 33 if self.include_face else 22

    def start(self) -> Path:
        if self.state is not RecordingState.IDLE:
            raise RuntimeError("This recorder session has already started.")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        unique_suffix = uuid.uuid4().hex[:8]
        self.session_id = f"{timestamp}-{unique_suffix}"
        safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "-", self.session_name).strip("-")
        safe_name = safe_name or "gait-session"
        self.output_path = (
            self.output_dir / f"{timestamp}_{safe_name}_{unique_suffix}.csv"
        )
        self._file = self.output_path.open("x", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=CSV_FIELDS)
        self._writer.writeheader()
        self._file.flush()
        self._started_at = time.monotonic()
        self.state = RecordingState.RECORDING
        return self.output_path

    def pause(self) -> None:
        if self.state is RecordingState.RECORDING:
            self._paused_at = time.monotonic()
            self.state = RecordingState.PAUSED
            self._file.flush()

    def resume(self) -> None:
        if self.state is RecordingState.PAUSED:
            self._paused_duration += time.monotonic() - self._paused_at
            self._paused_at = 0.0
            self.state = RecordingState.RECORDING

    def stop(self) -> Path | None:
        if self.state in (RecordingState.RECORDING, RecordingState.PAUSED):
            self._file.flush()
            self._file.close()
            self._file = None
            self._writer = None
            self.state = RecordingState.STOPPED
        return self.output_path

    def record_pose(self, landmarks, model_timestamp_ms: int) -> bool:
        if self.state is not RecordingState.RECORDING:
            return False

        frame_index = self.frame_count
        timestamp_utc = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        elapsed_ms = int(
            (time.monotonic() - self._started_at - self._paused_duration) * 1000
        )
        first_index = 0 if self.include_face else BODY_LANDMARK_START

        for landmark_index in range(first_index, min(len(landmarks), 33)):
            landmark = landmarks[landmark_index]
            self._writer.writerow(
                {
                    "session_id": self.session_id,
                    "session_name": self.session_name,
                    "activity": self.activity,
                    "frame_index": frame_index,
                    "timestamp_utc": timestamp_utc,
                    "elapsed_ms": elapsed_ms,
                    "model_timestamp_ms": model_timestamp_ms,
                    "landmark_index": landmark_index,
                    "landmark_name": LANDMARK_NAMES[landmark_index],
                    "x": f"{landmark.x:.8f}",
                    "y": f"{landmark.y:.8f}",
                    "z": f"{landmark.z:.8f}",
                    "visibility": self._confidence(landmark, "visibility"),
                    "presence": self._confidence(landmark, "presence"),
                }
            )
            self.row_count += 1

        self.frame_count += 1
        if self.frame_count % 30 == 0:
            self._file.flush()
        return True

    @staticmethod
    def _confidence(landmark, attribute: str) -> str:
        value = getattr(landmark, attribute, None)
        return "" if value is None else f"{value:.8f}"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()
