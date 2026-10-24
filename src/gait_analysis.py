"""Pose processing and conservative gait metrics for browser-uploaded frames.

Only normalized landmarks and timestamps leave the frame-processing function.
Raw JPEG bytes are decoded in memory and are never persisted.
"""

from __future__ import annotations

import math
import statistics
import threading
from pathlib import Path
from typing import Any

import cv2
import mediapipe as mp
import numpy as np


MIN_VISIBILITY = 0.5
POSE_CONNECTIONS = (
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24), (23, 25), (25, 27),
    (24, 26), (26, 28), (27, 29), (29, 31), (28, 30), (30, 32),
)


class BrowserPoseProcessor:
    """One lazily-created MediaPipe IMAGE detector protected by a lock."""

    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        self.lock = threading.Lock()
        self.detector = None

    def _detector(self):
        if self.detector is None:
            if not self.model_path.is_file():
                raise RuntimeError(f"Missing {self.model_path.name}. Run scripts/setup.sh first.")
            options = mp.tasks.vision.PoseLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(self.model_path)),
                running_mode=mp.tasks.vision.RunningMode.IMAGE,
                num_poses=1,
                min_pose_detection_confidence=0.55,
                min_pose_presence_confidence=0.55,
                min_tracking_confidence=0.55,
            )
            self.detector = mp.tasks.vision.PoseLandmarker.create_from_options(options)
        return self.detector

    def process(self, jpeg: bytes) -> list[dict[str, float | int]]:
        encoded = np.frombuffer(jpeg, dtype=np.uint8)
        frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if frame is None or frame.size == 0:
            raise ValueError("JPEG data could not be decoded")
        # Pose inference is deliberately focused on the centre placement zone.
        # This prevents a person at the edge of a multi-camera frame becoming the
        # tracked subject, while coordinates are mapped back to full-frame space.
        full_height, full_width = frame.shape[:2]
        left, right = round(full_width * 0.10), round(full_width * 0.90)
        top, bottom = round(full_height * 0.03), round(full_height * 0.98)
        frame = frame[top:bottom, left:right]
        crop_height, crop_width = frame.shape[:2]
        if frame.shape[1] > 960:
            scale = 960 / frame.shape[1]
            frame = cv2.resize(frame, (960, round(frame.shape[0] * scale)), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        with self.lock:
            result = self._detector().detect(image)
        if not result.pose_landmarks:
            return []
        return [
            {
                "index": index,
                "x": round((left + float(point.x) * crop_width) / full_width, 6),
                "y": round((top + float(point.y) * crop_height) / full_height, 6),
                "z": round(float(point.z), 6),
                "visibility": round(float(point.visibility), 5),
            }
            for index, point in enumerate(result.pose_landmarks[0])
        ]

    def close(self) -> None:
        with self.lock:
            if self.detector is not None:
                self.detector.close()
                self.detector = None


def unavailable(unit: str, reason: str) -> dict[str, Any]:
    return {"value": None, "unit": unit, "confidence": 0.0, "available": False, "reason": reason}


def available(value: float | int, unit: str, confidence: float, reason: str = "") -> dict[str, Any]:
    return {
        "value": value,
        "unit": unit,
        "confidence": round(max(0.0, min(1.0, confidence)), 2),
        "available": True,
        "reason": reason,
    }


def _point(frame: dict[str, Any], index: int, minimum: float = MIN_VISIBILITY):
    points = frame.get("keypoints", [])
    if index >= len(points):
        return None
    point = points[index]
    if float(point.get("visibility", 0)) < minimum:
        return None
    return float(point["x"]), float(point["y"])


def _angle(a, b, c) -> float | None:
    if not a or not b or not c:
        return None
    first = (a[0] - b[0], a[1] - b[1])
    second = (c[0] - b[0], c[1] - b[1])
    denominator = math.hypot(*first) * math.hypot(*second)
    if denominator <= 1e-9:
        return None
    cosine = max(-1.0, min(1.0, (first[0] * second[0] + first[1] * second[1]) / denominator))
    return math.degrees(math.acos(cosine))


def _series_range(values: list[float], unit: str, quality: float, label: str) -> dict[str, Any]:
    if len(values) < 12:
        return unavailable(unit, f"Not enough visible {label} samples.")
    ordered = sorted(values)
    low = ordered[max(0, round(len(ordered) * 0.05) - 1)]
    high = ordered[min(len(ordered) - 1, round(len(ordered) * 0.95))]
    return available(round(high - low, 1), unit, quality, "5th–95th percentile motion range.")


def _smooth(values: list[float]) -> list[float]:
    if len(values) < 3:
        return values
    return [statistics.median(values[max(0, i - 1): min(len(values), i + 2)]) for i in range(len(values))]


def _peaks(samples: list[tuple[float, float, str]]) -> list[tuple[float, str]]:
    if len(samples) < 5:
        return []
    values = _smooth([value for _, value, _ in samples])
    spread = (max(values) - min(values)) if values else 0
    prominence = max(0.008, spread * 0.12)
    peaks: list[tuple[float, str]] = []
    for index in range(1, len(samples) - 1):
        timestamp, value, side = samples[index]
        if value < values[index - 1] or value <= values[index + 1]:
            continue
        local_low = min(values[max(0, index - 3): min(len(values), index + 4)])
        if value - local_low < prominence:
            continue
        if peaks and timestamp - peaks[-1][0] < 0.28:
            if value > next((sample[1] for sample in samples if sample[0] == peaks[-1][0] and sample[2] == peaks[-1][1]), -1):
                peaks[-1] = (timestamp, side)
            continue
        peaks.append((timestamp, side))
    return peaks


def _polygon_area(points: list[tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    centre_x = statistics.mean(point[0] for point in points)
    centre_y = statistics.mean(point[1] for point in points)
    ordered = sorted(points, key=lambda point: math.atan2(point[1] - centre_y, point[0] - centre_x))
    return abs(sum(
        ordered[index][0] * ordered[(index + 1) % len(ordered)][1]
        - ordered[(index + 1) % len(ordered)][0] * ordered[index][1]
        for index in range(len(ordered))
    )) / 2


def analyse_session(activity: str, frames: list[dict[str, Any]], total_frames: int) -> dict[str, Any]:
    detected = [frame for frame in frames if frame.get("keypoints")]
    duration = max(0.0, (frames[-1]["t"] - frames[0]["t"]) if len(frames) > 1 else 0.0)
    detection_ratio = len(detected) / max(1, total_frames)
    full_body_frames = 0
    feet_visible_frames = 0
    time_series: list[dict[str, Any]] = []
    heel_samples: list[tuple[float, float, str]] = []
    left_knee: list[float] = []
    right_knee: list[float] = []
    left_hip: list[float] = []
    right_hip: list[float] = []
    trunk_values: list[float] = []
    sway_points: list[tuple[float, float]] = []

    for frame in frames:
        t = round(float(frame["t"]), 3)
        row: dict[str, Any] = {"t": t}
        if not frame.get("keypoints"):
            time_series.append(row)
            continue
        shoulders = (_point(frame, 11), _point(frame, 12))
        hips = (_point(frame, 23), _point(frame, 24))
        knees = (_point(frame, 25), _point(frame, 26))
        ankles = (_point(frame, 27), _point(frame, 28))
        heels = (_point(frame, 29), _point(frame, 30))
        feet = (_point(frame, 31), _point(frame, 32))
        if all((*shoulders, *hips, *knees, *ankles)):
            full_body_frames += 1
        if all((*ankles, *heels, *feet)):
            feet_visible_frames += 1

        angles = {
            "leftKnee": _angle(hips[0], knees[0], ankles[0]),
            "rightKnee": _angle(hips[1], knees[1], ankles[1]),
            "leftHip": _angle(shoulders[0], hips[0], knees[0]),
            "rightHip": _angle(shoulders[1], hips[1], knees[1]),
        }
        for key, value in angles.items():
            if value is not None:
                row[key] = round(value, 2)
        if angles["leftKnee"] is not None:
            left_knee.append(angles["leftKnee"])
        if angles["rightKnee"] is not None:
            right_knee.append(angles["rightKnee"])
        if angles["leftHip"] is not None:
            left_hip.append(angles["leftHip"])
        if angles["rightHip"] is not None:
            right_hip.append(angles["rightHip"])

        if all(shoulders) and all(hips):
            shoulder_mid = ((shoulders[0][0] + shoulders[1][0]) / 2, (shoulders[0][1] + shoulders[1][1]) / 2)
            hip_mid = ((hips[0][0] + hips[1][0]) / 2, (hips[0][1] + hips[1][1]) / 2)
            lean = math.degrees(math.atan2(shoulder_mid[0] - hip_mid[0], hip_mid[1] - shoulder_mid[1]))
            trunk_values.append(abs(lean))
            sway_points.append(hip_mid)
            row.update(trunkLean=round(abs(lean), 2), swayX=round(hip_mid[0], 5), swayY=round(hip_mid[1], 5))

        if heels[0]:
            heel_samples.append((t, heels[0][1], "left"))
            row["leftHeelY"] = round(heels[0][1], 5)
        if heels[1]:
            heel_samples.append((t, heels[1][1], "right"))
            row["rightHeelY"] = round(heels[1][1], 5)
        time_series.append(row)

    full_ratio = full_body_frames / max(1, total_frames)
    feet_ratio = feet_visible_frames / max(1, total_frames)
    quality_score = round(100 * (detection_ratio * 0.45 + full_ratio * 0.35 + feet_ratio * 0.20))
    quality_confidence = min(1.0, len(detected) / 45) * detection_ratio
    quality_notes: list[str] = []
    if detection_ratio < 0.7:
        quality_notes.append(f"Body missing in {round((1 - detection_ratio) * 100)}% of uploaded frames.")
    if feet_ratio < 0.7:
        quality_notes.append(f"Feet not fully visible in {round((1 - feet_ratio) * 100)}% of uploaded frames.")
    if duration < 4:
        quality_notes.append("Capture duration is too short for reliable timing metrics.")
    if not quality_notes:
        quality_notes.append("Full body and feet were visible for most of the capture.")

    missing_segments: list[dict[str, float]] = []
    missing_start = None
    for frame in frames:
        if not frame.get("keypoints") and missing_start is None:
            missing_start = float(frame["t"])
        elif frame.get("keypoints") and missing_start is not None:
            missing_segments.append({"start": round(missing_start, 2), "end": round(float(frame["t"]), 2)})
            missing_start = None
    if missing_start is not None and frames:
        missing_segments.append({"start": round(missing_start, 2), "end": round(float(frames[-1]["t"]), 2)})

    metrics = {
        "steps": unavailable("steps", "At least four clear alternating foot contacts are required."),
        "cadence": unavailable("spm", "At least four clear alternating foot contacts are required."),
        "stepTimeSymmetry": unavailable("%", "Both left and right step intervals are required."),
        "leftKneeRange": _series_range(left_knee, "°", quality_confidence, "left-knee"),
        "rightKneeRange": _series_range(right_knee, "°", quality_confidence, "right-knee"),
        "leftHipRange": _series_range(left_hip, "°", quality_confidence, "left-hip"),
        "rightHipRange": _series_range(right_hip, "°", quality_confidence, "right-hip"),
        "trunkLean": unavailable("°", "Not enough visible shoulder and hip samples."),
        "swayPath": unavailable("% frame", "Sway metrics are reported only for Balance tests."),
        "swayArea": unavailable("% frame²", "Sway metrics are reported only for Balance tests."),
        "strideLength": unavailable("m", "Stride length requires camera calibration or a known body-height reference."),
        "speed": unavailable("m/s", "Speed requires calibrated distance or depth data."),
    }
    if len(trunk_values) >= 12:
        metrics["trunkLean"] = available(round(statistics.mean(trunk_values), 1), "°", quality_confidence, "Mean absolute lean from vertical.")

    if activity == "Balance":
        if len(sway_points) >= 20 and duration >= 4:
            path = sum(math.dist(sway_points[index - 1], sway_points[index]) for index in range(1, len(sway_points))) * 100
            area = _polygon_area(sway_points) * 10_000
            metrics["swayPath"] = available(round(path, 2), "% frame", quality_confidence, "Normalized hip-centre path; not a distance in centimetres.")
            metrics["swayArea"] = available(round(area, 2), "% frame²", quality_confidence, "Normalized sway envelope; not a clinical force-plate measure.")
    else:
        left_samples = [sample for sample in heel_samples if sample[2] == "left"]
        right_samples = [sample for sample in heel_samples if sample[2] == "right"]
        events = sorted(_peaks(left_samples) + _peaks(right_samples))
        # Collapse near-simultaneous contacts, retaining alternating events where possible.
        filtered: list[tuple[float, str]] = []
        for event in events:
            if filtered and event[0] - filtered[-1][0] < 0.22:
                continue
            filtered.append(event)
        if len(filtered) >= 4 and duration >= 3:
            metrics["steps"] = available(len(filtered), "steps", quality_confidence * min(1.0, len(filtered) / 8), "Heel-contact peaks visible in the normalized pose signal.")
            metrics["cadence"] = available(round(len(filtered) / duration * 60), "spm", quality_confidence * min(1.0, len(filtered) / 8), "Calculated from detected heel-contact peaks.")
            left_intervals: list[float] = []
            right_intervals: list[float] = []
            for index in range(1, len(filtered)):
                interval = filtered[index][0] - filtered[index - 1][0]
                (left_intervals if filtered[index][1] == "left" else right_intervals).append(interval)
            if left_intervals and right_intervals:
                left_mean = statistics.mean(left_intervals)
                right_mean = statistics.mean(right_intervals)
                symmetry = 100 * min(left_mean, right_mean) / max(left_mean, right_mean)
                metrics["stepTimeSymmetry"] = available(round(symmetry, 1), "%", quality_confidence, "100% means equal mean left and right step times.")
                for row in time_series:
                    row["stepEvent"] = next((side for event_t, side in filtered if abs(event_t - row["t"]) < 0.06), None)

    return {
        "durationSec": round(duration, 2),
        "detectedFrames": len(detected),
        "quality": {
            "score": quality_score,
            "confidence": round(quality_confidence, 2),
            "fullBodyRatio": round(full_ratio, 3),
            "feetVisibleRatio": round(feet_ratio, 3),
            "notes": quality_notes,
            "missingSegments": missing_segments,
        },
        "metrics": metrics,
        "timeSeries": time_series,
    }
