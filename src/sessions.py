import csv
from functools import lru_cache
from pathlib import Path
import re


def session_path(directory: Path, filename: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_-]+\.csv", filename):
        raise ValueError("Invalid session filename")
    path = directory / filename
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(filename)
    return path


@lru_cache(maxsize=128)
def summarize_session(path: Path, modified: int, size: int) -> dict:
    summary = {
        "file": path.name,
        "name": "Gait recording",
        "activity": "walking",
        "date": None,
        "frames": 0,
        "landmarks": 0,
        "sample_span_ms": 0,
        "status": "empty",
        "size": size,
    }
    frames = set()
    landmarks = set()
    first_elapsed = None
    last_elapsed = 0
    try:
        with path.open(newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            required = {"frame_index", "landmark_index", "elapsed_ms", "timestamp_utc", "session_name", "activity"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("Unsupported CSV format")
            for row in reader:
                elapsed = int(row["elapsed_ms"])
                frames.add(int(row["frame_index"]))
                landmarks.add(int(row["landmark_index"]))
                if first_elapsed is None:
                    first_elapsed = elapsed
                    summary.update(name=row["session_name"], activity=row["activity"], date=row["timestamp_utc"])
                last_elapsed = max(last_elapsed, elapsed)
        summary.update(
            frames=len(frames),
            landmarks=len(landmarks),
            sample_span_ms=max(0, last_elapsed - (first_elapsed or 0)),
            status="saved" if frames else "empty",
        )
    except (OSError, UnicodeError, ValueError, TypeError, csv.Error):
        summary["status"] = "unreadable"
    return summary


def list_sessions(directory: Path, active_file: str | None = None) -> list[dict]:
    sessions = []
    for path in sorted(directory.glob("*.csv"), reverse=True):
        if path.name == active_file or path.is_symlink():
            continue
        try:
            metadata = path.stat()
            sessions.append(summarize_session(path, metadata.st_mtime_ns, metadata.st_size))
        except OSError:
            continue
    return sessions
