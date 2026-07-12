from __future__ import annotations

from typing import Any

import numpy as np


class FireService:
    """明火检测服务"""

    def __init__(
        self,
        model: Any | None = None,
        confidence_threshold: float = 0.25,
        max_detections: int = 20,
        min_bbox_area: int = 1000,
        device: str | None = None,
    ):
        self.model = model
        self.confidence_threshold = confidence_threshold
        self.max_detections = max_detections
        self.min_bbox_area = min_bbox_area
        self.device = device
        self._total_detections = 0

    @property
    def loaded(self) -> bool:
        return self.model is not None

    def detect(
        self,
        stream_id: str,
        frame: np.ndarray,
        rules: dict[str, dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """
        检测画面中的明火

        Returns:
            list[dict]: 每个元素包含 event_type, confidence, level, target, track_key 等
        """
        if self.model is None:
            return []

        rule = (rules or {}).get("flame_detected", {})
        threshold = float(rule.get("confidence_threshold", self.confidence_threshold))
        cooldown = float(rule.get("cooldown_seconds", 10))
        threshold_seconds = float(rule.get("threshold_seconds", 0))

        if hasattr(self.model, "predict"):
            predict_args: dict[str, Any] = {"verbose": False}
            if self.device:
                predict_args["device"] = self.device
            results = self.model.predict(frame, **predict_args)
        else:
            results = self.model(frame, verbose=False)
        detections: list[dict[str, Any]] = []

        for r in results:
            boxes = getattr(r, "boxes", None)
            if boxes is None:
                continue
            for box in boxes:
                conf = float(box.conf[0])
                if conf < threshold:
                    continue
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
                area = (x2 - x1) * (y2 - y1)
                if area < self.min_bbox_area:
                    continue

                level = self._classify_level(conf)
                idx = len(detections)
                detections.append(
                    {
                        "event_type": "flame_detected",
                        "confidence": round(conf, 4),
                        "level": level,
                        "target": {"track_id": f"fire_{idx}", "bbox": [x1, y1, x2, y2]},
                        "track_key": f"fire_{idx}",
                        "threshold_seconds": threshold_seconds,
                        "cooldown_seconds": cooldown,
                    }
                )

        detections = sorted(detections, key=lambda d: d["confidence"], reverse=True)
        detections = detections[: self.max_detections]
        self._total_detections += len(detections)
        return detections

    @staticmethod
    def _classify_level(confidence: float) -> str:
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "warning"
        return "info"

    def status(self) -> dict[str, Any]:
        return {
            "loaded": self.loaded,
            "confidence_threshold": self.confidence_threshold,
            "max_detections": self.max_detections,
            "min_bbox_area": self.min_bbox_area,
            "device": self.device,
            "total_detections": self._total_detections,
        }
