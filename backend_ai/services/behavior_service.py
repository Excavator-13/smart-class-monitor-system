from __future__ import annotations

from itertools import combinations
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
    def __init__(self, model: Any | None = None, device: str | None = None):
        self.model = model
        self.device = device

    def detect_objects(self, frame: Any) -> list[dict[str, Any]]:
        if self.model is None:
            return []
        device = _detect_torch_device(self.device)
        results = self.model(frame, device=device)
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