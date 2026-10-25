"""MediaPipe/OpenCV pose processing for the local hardware server only."""

from __future__ import annotations

import threading
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np


class BrowserPoseProcessor:
    """One lazily-created MediaPipe IMAGE detector protected by a lock."""

    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        self.lock = threading.Lock()
        self.detector = None

    def _detector(self):
        if self.detector is None:
            if not self.model_path.is_file():
                raise RuntimeError(f"Missing {self.model_path.name}. Run scripts/setup.py first.")
            options = mp.tasks.vision.PoseLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(self.model_path)),
                running_mode=mp.tasks.vision.RunningMode.IMAGE, num_poses=1,
                min_pose_detection_confidence=0.55, min_pose_presence_confidence=0.55,
                min_tracking_confidence=0.55,
            )
            self.detector = mp.tasks.vision.PoseLandmarker.create_from_options(options)
        return self.detector

    def process(self, jpeg: bytes) -> list[dict[str, float | int]]:
        encoded = np.frombuffer(jpeg, dtype=np.uint8)
        frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if frame is None or frame.size == 0:
            raise ValueError("JPEG data could not be decoded")
        height, width = frame.shape[:2]
        left, right, top, bottom = round(width * .10), round(width * .90), round(height * .03), round(height * .98)
        crop = frame[top:bottom, left:right]
        crop_height, crop_width = crop.shape[:2]
        if crop_width > 960:
            scale = 960 / crop_width
            crop = cv2.resize(crop, (960, round(crop_height * scale)), interpolation=cv2.INTER_AREA)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
        with self.lock:
            result = self._detector().detect(image)
        if not result or not result.pose_landmarks:
            return []
        
        # Convert landmarks back to original frame coordinate space if cropped
        landmarks: list[dict[str, float | int]] = []
        scale_x = (right - left) / width
        scale_y = (bottom - top) / height
        offset_x = left / width
        offset_y = top / height

        for lm in result.pose_landmarks[0]:
            orig_x = float(lm.x * scale_x + offset_x)
            orig_y = float(lm.y * scale_y + offset_y)
            landmarks.append({
                "x": orig_x,
                "y": orig_y,
                "z": float(lm.z),
                "visibility": float(getattr(lm, "visibility", 1.0) or 0.0),
            })
        return landmarks

    def close(self) -> None:
        with self.lock:
            if self.detector is not None:
                try:
                    self.detector.close()
                except Exception:
                    pass
                self.detector = None
