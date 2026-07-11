from __future__ import annotations

import base64
import platform
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def _find_chinese_font() -> str | None:
    system = platform.system()
    candidates: list[str] = []
    if system == "Darwin":
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ]
    elif system == "Linux":
        candidates = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        ]
    elif system == "Windows":
        candidates = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
        ]
    for p in candidates:
        if Path(p).is_file():
            return p
    return None


_cached_font_path: str | None | bool = False


def _get_chinese_font_path() -> str | None:
    global _cached_font_path
    if _cached_font_path is False:
        _cached_font_path = _find_chinese_font()
    return _cached_font_path


def draw_text(frame: np.ndarray, text: str, org: tuple[int, int], font_scale: float = 0.55, color: tuple[int, int, int] = (255, 255, 255), thickness: int = 2) -> None:
    if not text:
        return
    if all(ord(c) < 128 for c in text):
        cv2.putText(frame, text, org, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
        return
    font_path = _get_chinese_font_path()
    if font_path is None:
        cv2.putText(frame, text.encode("ascii", "replace").decode(), org, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
        return
    try:
        from PIL import Image, ImageDraw, ImageFont

        font_size = max(12, int(font_scale * 28))
        font = ImageFont.truetype(font_path, font_size)
        dummy = Image.new("RGBA", (1, 1))
        bbox = ImageDraw.Draw(dummy).textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        text_img = Image.new("RGBA", (tw + 4, th + 4), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)
        draw.text((-bbox[0] + 2, -bbox[1] + 2), text, font=font, fill=(color[2], color[1], color[0]))
        text_np = np.array(text_img)
        mask = text_np[:, :, 3] > 0
        h, w = mask.shape[:2]
        fh, fw = frame.shape[:2]
        x0, y0 = org[0] - 2, org[1] - th - 2
        fx1, fy1 = max(0, x0), max(0, y0)
        fx2, fy2 = min(fw, x0 + w), min(fh, y0 + h)
        tx1, ty1 = fx1 - x0, fy1 - y0
        tx2, ty2 = tx1 + (fx2 - fx1), ty1 + (fy2 - fy1)
        if fx2 > fx1 and fy2 > fy1:
            roi = frame[fy1:fy2, fx1:fx2]
            sub_mask = mask[ty1:ty2, tx1:tx2]
            sub_rgb = text_np[ty1:ty2, tx1:tx2, :3]
            roi[sub_mask] = sub_rgb[sub_mask]
    except Exception:
        cv2.putText(frame, text.encode("ascii", "replace").decode(), org, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)


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
    draw_text(frame, label, (x1, max(20, y1 - 8)), font_scale=0.6, color=color, thickness=2)


def blank_frame(width: int = 640, height: int = 360, text: str = "stream offline") -> np.ndarray:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    draw_text(frame, text, (30, height // 2), font_scale=0.9, color=(255, 255, 255), thickness=2)
    return frame