from __future__ import annotations

from typing import Any

import numpy as np


class AnalysisService:
    def __init__(self, face_service: Any, zone_service: Any, behavior_service: Any, event_service: Any, config_client: Any, alert_client: Any | None = None):
        self.face_service = face_service
        self.zone_service = zone_service
        self.behavior_service = behavior_service
        self.event_service = event_service
        self.config_client = config_client
        self.alert_client = alert_client

    def analyze_frame(self, stream_id: str, frame: np.ndarray, modules: set[str] | None = None, objects: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        enabled = modules or {"face", "zone", "behavior"}
        detected: list[dict[str, Any]] = []

        if "face" in enabled:
            detected.extend(self.face_service.recognize_frame(frame, self.config_client.get_face_features()))

        object_list = objects if objects is not None else []
        if "behavior" in enabled:
            if objects is None:
                object_list = self.behavior_service.detect_objects(frame)
            rules = {k: v for k, v in self.config_client.cache.rules.items()}
            detected.extend(self.behavior_service.detect_from_objects(stream_id, object_list, rules))

        if "zone" in enabled:
            persons = [obj for obj in object_list if obj.get("class_name") in {"person", "student"}]
            detected.extend(
                self.zone_service.detect(
                    stream_id,
                    persons,
                    self.config_client.get_zones(stream_id),
                    self.config_client.get_rule("danger_zone"),
                )
            )

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

