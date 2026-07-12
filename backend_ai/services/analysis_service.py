from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from backend_ai.utils.geometry import parse_polygon_coordinates


class AnalysisService:
    def __init__(self, face_service: Any, zone_service: Any, behavior_service: Any, event_service: Any, config_client: Any, fire_service: Any | None = None, anti_spoof_service: Any | None = None, audio_service: Any | None = None, alert_client: Any | None = None):
        self.face_service = face_service
        self.zone_service = zone_service
        self.behavior_service = behavior_service
        self.fire_service = fire_service
        self.anti_spoof_service = anti_spoof_service
        self.audio_service = audio_service
        self.event_service = event_service
        self.config_client = config_client
        self.alert_client = alert_client

    def analyze_frame(self, stream_id: str, frame: np.ndarray, modules: set[str] | None = None, objects: list[dict[str, Any]] | None = None, audio_chunk: np.ndarray | None = None) -> list[dict[str, Any]]:
        enabled = modules or {"face", "zone", "behavior"}
        detected: list[dict[str, Any]] = []

        if "face" in enabled:
            face_detections = self.face_service.recognize_frame(frame, self.config_client.get_face_features())
            detected.extend(face_detections)
            self._draw_detections(frame, face_detections, color=(80, 220, 80))

            if "anti_spoof" in enabled and self.anti_spoof_service is not None:
                faces_with_bbox = [
                    {"track_id": r.get("target", {}).get("track_id", f"face_{i}"),
                     "bbox": r.get("target", {}).get("bbox")}
                    for i, r in enumerate(face_detections)
                ]
                detected.extend(self.anti_spoof_service.detect(stream_id, faces_with_bbox, frame))

        object_list = objects if objects is not None else []
        needs_objects = "behavior" in enabled or "zone" in enabled
        if needs_objects and objects is None:
            object_list = self.behavior_service.detect_objects(frame)
        self._draw_objects(frame, object_list)

        if "behavior" in enabled:
            rules = {k: v for k, v in self.config_client.cache.rules.items()}
            behavior_detections = self.behavior_service.detect_from_objects(stream_id, object_list, rules)
            detected.extend(behavior_detections)
            self._draw_detections(frame, behavior_detections, color=(80, 180, 255))

        if "zone" in enabled:
            zones = self.config_client.get_zones(stream_id)
            self._draw_zones(frame, zones)
            if not zones:
                self._draw_status(frame, "Danger zone not configured", color=(0, 220, 255))
            persons = [obj for obj in object_list if obj.get("class_name") in {"person", "student"}]
            zone_detections = self.zone_service.detect(
                stream_id,
                persons,
                zones,
                self.config_client.get_rule("danger_zone"),
            )
            detected.extend(zone_detections)
            self._draw_detections(frame, zone_detections, color=(0, 0, 255))

        if "fire" in enabled and self.fire_service is not None:
            detected.extend(
                self.fire_service.detect(
                    stream_id,
                    frame,
                    {k: v for k, v in self.config_client.cache.rules.items()},
                )
            )

        if "audio" in enabled and self.audio_service is not None:
            detected.extend(self.audio_service.process_audio(stream_id, audio_chunk))

        events = []
        for item in detected:
            event, should_confirm = self.event_service.observe(
                stream_id=stream_id,
                event_type=item["event_type"],
                track_key=str(item.get("track_key", item["event_type"])),
                confidence=float(item.get("confidence", 0)),
                threshold_seconds=float(item.get("threshold_seconds", 0)),
                cooldown_seconds=item.get("cooldown_seconds"),
                level=item.get("level", "warning"),
                target=item.get("target"),
                zone=item.get("zone"),
            )
            if should_confirm and self.alert_client is not None:
                try:
                    self.alert_client.push_alert(event)
                    self.event_service.mark_confirmed(event["event_id"])
                except Exception:
                    pass
            events.append(event)
        return events

    def _draw_objects(self, frame: np.ndarray, objects: list[dict[str, Any]]) -> None:
        for idx, obj in enumerate(objects):
            bbox = obj.get("bbox")
            if not bbox:
                continue
            label = obj.get("class_name") or f"object_{idx + 1}"
            confidence = obj.get("confidence")
            if confidence is not None:
                label = f"{label} {float(confidence):.2f}"
            self._draw_bbox(frame, bbox, label, color=(255, 180, 60))

    def _draw_detections(self, frame: np.ndarray, detections: list[dict[str, Any]], color: tuple[int, int, int]) -> None:
        for item in detections:
            target = item.get("target") or {}
            bbox = target.get("bbox")
            if not bbox:
                continue
            label_parts = [str(item.get("event_type", "event"))]
            zone = item.get("zone") or {}
            if zone.get("zone_name"):
                label_parts.append(str(zone["zone_name"]))
            self._draw_bbox(frame, bbox, " ".join(label_parts), color=color)

    def _draw_zones(self, frame: np.ndarray, zones: list[dict[str, Any]]) -> None:
        height, width = frame.shape[:2]
        for zone in zones:
            polygon = parse_polygon_coordinates(zone.get("coordinates") or [])
            if len(polygon) < 3:
                continue
            points = []
            for x, y in polygon:
                px = int(x * width) if 0 <= x <= 1 else int(x)
                py = int(y * height) if 0 <= y <= 1 else int(y)
                points.append([px, py])
            pts = np.asarray(points, dtype=np.int32)
            cv2.polylines(frame, [pts], isClosed=True, color=(0, 0, 255), thickness=2)
            label = str(zone.get("zone_name") or zone.get("zone_type") or "danger zone")
            x0, y0 = points[0]
            cv2.putText(frame, label, (x0, max(18, y0 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)

    def _draw_status(self, frame: np.ndarray, text: str, color: tuple[int, int, int]) -> None:
        height, width = frame.shape[:2]
        scale = 0.58
        thickness = 2
        (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
        x = max(8, width - text_width - 12)
        y = max(text_height + 10, 28)
        cv2.rectangle(frame, (x - 6, y - text_height - 8), (width - 6, y + 6), (0, 0, 0), -1)
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)

    def _draw_bbox(self, frame: np.ndarray, bbox: list[float], label: str, color: tuple[int, int, int]) -> None:
        x1f, y1f, x2f, y2f = [float(v) for v in bbox]
        height, width = frame.shape[:2]
        if 0 <= x1f <= 1 and 0 <= x2f <= 1 and 0 <= y1f <= 1 and 0 <= y2f <= 1:
            x1, x2 = int(x1f * width), int(x2f * width)
            y1, y2 = int(y1f * height), int(y2f * height)
        else:
            x1, y1, x2, y2 = int(x1f), int(y1f), int(x2f), int(y2f)
        x1, x2 = max(0, min(x1, width - 1)), max(0, min(x2, width - 1))
        y1, y2 = max(0, min(y1, height - 1)), max(0, min(y2, height - 1))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
