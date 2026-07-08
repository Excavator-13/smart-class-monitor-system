from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def decode_base64_image(image: str) -> np.ndarray:
    if not image:
        raise ValueError("image is required")
    payload = image.split(",", 1)[1] if image.startswith("data:") and "," in image else image
    try:
        raw = base64.b64decode(payload, validate=True)
    except Exception as exc:
        raise ValueError("invalid base64 image") from exc
    arr = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("invalid image")
    return frame


def encode_jpeg(frame: np.ndarray) -> bytes:
    ok, buffer = cv2.imencode(".jpg", frame)
    if not ok:
        raise ValueError("failed to encode jpeg")
    return buffer.tobytes()


def save_snapshot(frame: np.ndarray, snapshot_dir: str | Path, filename: str) -> str:
    path = Path(snapshot_dir)
    path.mkdir(parents=True, exist_ok=True)
    target = path / filename
    if not cv2.imwrite(str(target), frame):
        raise OSError("failed to save snapshot")
    return str(target.as_posix())


def draw_label(frame: np.ndarray, bbox: list[int] | tuple[int, int, int, int], label: str, color: tuple[int, int, int]) -> None:
    x1, y1, x2, y2 = [int(v) for v in bbox]
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.putText(frame, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def blank_frame(width: int = 640, height: int = 360, text: str = "stream offline") -> np.ndarray:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.putText(frame, text, (30, height // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    return frame

