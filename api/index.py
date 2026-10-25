"""Stateless Vercel API for browser-side GAIT pose analysis."""
from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
from src.gait_analysis import ANALYSIS_LANDMARK_INDICES, analyse_session  # noqa: E402

app = FastAPI(title="GAIT analysis API")
MAX_BODY_BYTES = int(os.environ.get("MAX_BODY_BYTES", "4000000"))
MAX_FRAMES = 1_800
VIEWS = {"left", "back", "right"}


def error(status: int, message: str) -> None:
    raise HTTPException(status_code=status, detail=message)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": f"Internal server error: {str(exc)}"},
    )


def clean_person(raw: object) -> dict[str, str]:
    value = raw if isinstance(raw, dict) else {}
    name = str(value.get("name") or "").strip()[:120]
    if not name:
        error(422, "Participant name is required")

    def number(key: str, low: float, high: float) -> str:
        try:
            parsed = float(value.get(key))
        except (TypeError, ValueError):
            error(422, f"Participant {key} is required")
        if not low <= parsed <= high:
            error(422, f"Participant {key} is outside the accepted range")
        return str(int(parsed) if parsed.is_integer() else parsed)

    return {
        "name": name,
        "age": number("age", 1, 120),
        "height": number("height", 50, 260),
        "weight": number("weight", 10, 400),
    }


def metric_unavailable(unit: str, reason: str) -> dict[str, Any]:
    return {"value": None, "unit": unit, "confidence": 0.0, "available": False, "reason": reason}


def empty_analysis() -> dict[str, Any]:
    return analyse_session("Normal Walk", [], 0)


def decode_frames(raw: object) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or len(raw) > MAX_FRAMES:
        error(422, f"frames must contain at most {MAX_FRAMES} compact frames")
    result: list[dict[str, Any]] = []
    last_t = -1.0
    allowed = set(ANALYSIS_LANDMARK_INDICES)
    for frame in raw:
        if not isinstance(frame, list) or len(frame) != 4:
            error(422, "Each frame must be [t, timestamp, seq, landmarks]")
        t, timestamp, seq, points = frame
        if not isinstance(t, (int, float)) or not 0 <= float(t) <= 121:
            error(422, "Frame time must be between 0 and 121 seconds")
        if float(t) < last_t:
            error(422, "Frame times must be ordered")
        last_t = float(t)
        if not isinstance(timestamp, str) or len(timestamp) > 64 or not isinstance(seq, int):
            error(422, "Frame timestamp or sequence is invalid")
        if not isinstance(points, list) or len(points) > len(allowed):
            error(422, "Landmark array is invalid")
        decoded: list[dict[str, float | int]] = []
        seen: set[int] = set()
        for point in points:
            if not isinstance(point, list) or len(point) != 5:
                error(422, "Landmarks must be [index, x, y, z, visibility]")
            index, x, y, z, visibility = point
            if not isinstance(index, int) or index not in allowed or index in seen:
                error(422, "Landmark index is invalid")
            if not all(isinstance(n, (int, float)) for n in (x, y, z, visibility)):
                error(422, "Landmark coordinates must be numeric")
            if not -1.5 <= float(x) <= 2.5 or not -1.5 <= float(y) <= 2.5 or not -5 <= float(z) <= 5 or not 0 <= float(visibility) <= 1:
                error(422, "Landmark coordinate is outside the accepted range")
            seen.add(index)
            decoded.append({"index": index, "x": float(x), "y": float(y), "z": float(z), "visibility": float(visibility)})
        result.append({"t": round(float(t), 3), "timestamp": timestamp, "keypoints": decoded})
    return result


@app.middleware("http")
async def size_limit(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and int(length) > MAX_BODY_BYTES:
        return JSONResponse({"error": "Analysis payload exceeds the 4 MB server limit. Reduce samples and retry."}, status_code=413)
    return await call_next(request)


@app.get("/api/hardware")
def hardware() -> dict[str, bool]:
    """Report hardware mode availability (False on serverless cloud)."""
    return {"hardware_mode": False}


@app.get("/api/health")
def health() -> dict[str, str]:
    """Liveness probe returning required status: ok."""
    return {"status": "ok", "state": "ready"}


@app.get("/api/cameras")
def get_cameras() -> list[dict[str, Any]]:
    """Hardware camera discovery stub for cloud serverless."""
    return []


@app.get("/api/sessions")
def get_sessions() -> list[dict[str, Any]]:
    """Local session list stub for cloud serverless (cloud uses browser IndexedDB)."""
    return []


@app.delete("/api/session/{session_id}")
def delete_session(session_id: str) -> dict[str, Any]:
    """Session deletion handler."""
    return {"sessionId": session_id, "deleted": True}


@app.get("/api/gait/result/{session_id}")
def get_session_result(session_id: str) -> dict[str, Any]:
    """Cloud session results fallback."""
    error(404, "Session results are preserved in browser storage (IndexedDB) on cloud deployments.")


@app.post("/api/session/create")
def create_session() -> dict[str, str]:
    from uuid import uuid4
    return {"sessionId": f"gait-{uuid4().hex}", "timestamp": datetime.now(UTC).isoformat()}


@app.post("/api/analyze")
async def analyze(request: Request) -> dict[str, Any]:
    body = await request.body()
    if len(body) > MAX_BODY_BYTES:
        error(413, "Analysis payload exceeds the 4 MB server limit. Reduce samples and retry.")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        error(400, "Analysis payload must be valid JSON")
    if not isinstance(payload, dict):
        error(422, "Analysis payload must be an object")
    view = payload.get("view")
    if view not in VIEWS:
        error(422, "view must be left, back, or right")
    session_id = str(payload.get("sessionId") or "")
    if not session_id.startswith("gait-") or len(session_id) > 64:
        error(422, "Invalid GAIT session ID")
    duration = payload.get("durationSec")
    if not isinstance(duration, (int, float)) or duration not in {30, 60, 120}:
        error(422, "durationSec must be 30, 60, or 120")
    activity = str(payload.get("activityType") or "Normal Walk")[:32]
    person = clean_person(payload.get("person"))
    frames = decode_frames(payload.get("frames"))
    sent_count = payload.get("sentCount", len(frames))
    if not isinstance(sent_count, int) or sent_count < len(frames) or sent_count > MAX_FRAMES:
        error(422, "sentCount is invalid")

    try:
        analysis = analyse_session(activity, frames, sent_count)
    except Exception as exc:
        error(500, f"Analysis computation failed: {str(exc)}")

    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    detail = {
        "view": view,
        "cameraLabel": str(metadata.get("cameraLabel") or "Browser camera")[:120],
        "rotation": metadata.get("rotation") if metadata.get("rotation") in {0, 90, 180, 270} else 0,
        "width": metadata.get("width") if isinstance(metadata.get("width"), int) else None,
        "height": metadata.get("height") if isinstance(metadata.get("height"), int) else None,
        "fps": metadata.get("fps") if isinstance(metadata.get("fps"), (int, float)) else None,
        "sent": sent_count,
        "received": len(frames),
        "detected": analysis["detectedFrames"],
        "detectionRate": round(analysis["detectedFrames"] / max(1, len(frames)), 3),
        "gaps": analysis["quality"]["missingSegments"],
        "state": "ready",
    }
    metrics = {name: {**value, "sourceViews": [view]} for name, value in analysis["metrics"].items()}
    return {
        "sessionId": session_id,
        "state": "ready",
        "activity": activity,
        "timestamp": datetime.now(UTC).isoformat(),
        "person": person,
        "frameCount": len(frames),
        "framesReceived": len(frames),
        "durationSec": analysis["durationSec"],
        "detectedFrames": analysis["detectedFrames"],
        "metrics": metrics,
        "quality": analysis["quality"],
        "timeSeries": analysis["timeSeries"],
        "landmarkTimeline": frames,
        "landmarksByView": {view: frames},
        "views": [detail],
        "camera": {"name": detail["cameraLabel"], "fps": detail["fps"]},
        "message": "Browser-side pose landmarks analyzed.",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8765"))
    host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run("index:app", host=host, port=port, reload=True)
