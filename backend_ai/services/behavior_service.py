from __future__ import annotations

import os
from itertools import combinations
from pathlib import Path
from typing import Any

from backend_ai.services.config_client import parse_json_field


def _detect_torch_device(device: str | None = None) -> str:
    if device and device != "auto":
        return device
    try:
        import torch
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _iou_like_relation(person_bbox: list[float], object_bbox: list[float]) -> bool:
    px1, py1, px2, py2 = person_bbox
    ox1, oy1, ox2, oy2 = object_bbox
    cx = (ox1 + ox2) / 2
    cy = (oy1 + oy2) / 2
    return px1 <= cx <= px2 and py1 <= cy <= py2


def _bbox_center(bbox: list[float]) -> tuple[float, float]:
    return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)


class BehaviorService:
    def __init__(self, model: Any | None = None, confidence_threshold: float = 0.6):
        self.model = model
        self.loaded = model is not None
        self.model_name = "ultralytics"
        self.model_version = "v1"
        self.weights_path: str | None = None
        self.last_error: str | None = None
        self.confidence_threshold = confidence_threshold

    def load_model(self, settings: dict[str, Any], base_dir: Path) -> None:
        if not settings.get("enabled", True):
            self.loaded = False
            self.last_error = "behavior model disabled"
            return
        if self.model is not None:
            self.loaded = True
            self.last_error = None
            return

        weights = str(settings.get("weights") or "").strip()
        if not weights:
            self.loaded = False
            self.last_error = "behavior model weights not configured"
            return

        weights_path = Path(weights)
        if not weights_path.is_absolute():
            weights_path = base_dir / weights_path
        self.weights_path = str(weights_path)
        self.confidence_threshold = float(settings.get("confidence_threshold", self.confidence_threshold))
        self.model_name = str(settings.get("name") or weights_path.stem or "ultralytics")

        if not weights_path.exists():
            self.loaded = False
            self.last_error = f"behavior model weights not found: {weights_path}"
            return

        try:
            ultralytics_config_dir = base_dir / "config" / "ultralytics"
            ultralytics_config_dir.mkdir(parents=True, exist_ok=True)
            os.environ.setdefault("YOLO_CONFIG_DIR", str(ultralytics_config_dir))

            from ultralytics import YOLO

            self.model = YOLO(str(weights_path))
            self.loaded = True
            self.last_error = None
        except Exception as exc:
            self.model = None
            self.loaded = False
            self.last_error = f"behavior model load failed: {exc}"

    def detect_objects(self, frame: Any) -> list[dict[str, Any]]:
        if self.model is None:
            return []
        results = self.model.predict(frame, conf=self.confidence_threshold, verbose=False) if hasattr(self.model, "predict") else self.model(frame)
        device = _detect_torch_device(self.device)
        detections: list[dict[str, Any]] = []
        for result in results:
            names = getattr(result, "names", {})
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for box in boxes:
                cls_id = int(box.cls[0])
                detections.append(
                    {
                        "class_name": names.get(cls_id, str(cls_id)),
                        "confidence": float(box.conf[0]),
                        "bbox": [float(v) for v in box.xyxy[0]],
                    }
                )
        return detections

    def detect_from_objects(self, stream_id: str, objects: list[dict[str, Any]], rules: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        persons = [obj for obj in objects if obj.get("class_name") in {"person", "student"}]
        phones = [obj for obj in objects if obj.get("class_name") in {"phone", "cell phone", "mobile_phone"}]
        detections: list[dict[str, Any]] = []

        phone_rule = rules.get("phone_usage", {})
        phone_threshold = float(phone_rule.get("confidence_threshold", 0.6))
        for idx, person in enumerate(persons):
            for phone in phones:
                if phone.get("confidence", 0) >= phone_threshold and _iou_like_relation(person["bbox"], phone["bbox"]):
                    detections.append(
                        {
                            "event_type": "phone_usage",
                            "confidence": min(1.0, float(phone.get("confidence", 0))),
                            "level": "warning",
                            "target": {"track_id": person.get("track_id", f"person_{idx + 1}"), "bbox": person["bbox"]},
                            "track_key": person.get("track_id", f"person_{idx + 1}"),
                            "threshold_seconds": float(phone_rule.get("threshold_seconds", 3)),
                            "cooldown_seconds": float(phone_rule.get("cooldown_seconds", 45)),
                        }
                    )

        head_rule = rules.get("head_down", {})
        for idx, person in enumerate(persons):
            ratio = person.get("head_down_ratio")
            if ratio is not None and float(ratio) >= float(head_rule.get("confidence_threshold", 0.6)):
                detections.append(
                    {
                        "event_type": "head_down",
                        "confidence": float(ratio),
                        "level": "warning",
                        "target": {"track_id": person.get("track_id", f"person_{idx + 1}"), "bbox": person["bbox"]},
                        "track_key": person.get("track_id", f"person_{idx + 1}"),
                        "threshold_seconds": float(head_rule.get("threshold_seconds", 3)),
                        "cooldown_seconds": float(head_rule.get("cooldown_seconds", 45)),
                    }
                )

        crowd_rule = rules.get("crowd_gathering", {})
        min_count = int(parse_json_field(crowd_rule.get("config_json"), {}).get("min_count", 4))
        max_distance = float(parse_json_field(crowd_rule.get("config_json"), {}).get("max_center_distance", 0.15))
        if len(persons) >= min_count and self._has_crowd(persons, min_count=min_count, max_distance=max_distance):
            detections.append(
                {
                    "event_type": "crowd_gathering",
                    "confidence": 1.0,
                    "level": "warning",
                    "target": {"track_id": "crowd", "bbox": None},
                    "track_key": "crowd",
                    "threshold_seconds": float(crowd_rule.get("threshold_seconds", 3)),
                    "cooldown_seconds": float(crowd_rule.get("cooldown_seconds", 45)),
                }
            )

        fall_rule = rules.get("fall_detected", {})
        fall_config = fall_rule.get("config_json") or {}
        min_aspect_ratio = float(fall_config.get("min_width_height_ratio", 1.2))
        for idx, person in enumerate(persons):
            bbox = person.get("bbox")
            if not bbox:
                continue
            width = abs(float(bbox[2]) - float(bbox[0]))
            height = abs(float(bbox[3]) - float(bbox[1]))
            if height > 0 and width / height >= min_aspect_ratio:
                detections.append(
                    {
                        "event_type": "fall_detected",
                        "confidence": float(person.get("confidence", 0.75)),
                        "level": "high",
                        "target": {"track_id": person.get("track_id", f"person_{idx + 1}"), "bbox": bbox},
                        "track_key": person.get("track_id", f"person_{idx + 1}"),
                        "threshold_seconds": float(fall_rule.get("threshold_seconds", 1)),
                        "cooldown_seconds": float(fall_rule.get("cooldown_seconds", 45)),
                    }
                )
        return detections

    def _has_crowd(self, persons: list[dict[str, Any]], min_count: int, max_distance: float) -> bool:
        centers = [_bbox_center(person["bbox"]) for person in persons]
        for group in combinations(centers, min_count):
            distances = []
            for a, b in combinations(group, 2):
                distances.append(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5)
            if distances and max(distances) <= max_distance:
                return True
        return False
