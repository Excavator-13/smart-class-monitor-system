from __future__ import annotations

from typing import Any

import numpy as np


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
            face_results = self.face_service.recognize_frame(frame, self.config_client.get_face_features())
            detected.extend(face_results)

            # 反欺骗检测依赖人脸识别结果
            if "anti_spoof" in enabled and self.anti_spoof_service is not None:
                faces_with_bbox = [
                    {"track_id": r.get("target", {}).get("track_id", f"face_{i}"),
                     "bbox": r.get("target", {}).get("bbox"),
                     "landmarks": r.get("target", {}).get("landmarks")}
                    for i, r in enumerate(face_results)
                ]
                detected.extend(self.anti_spoof_service.detect(stream_id, faces_with_bbox, frame))

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

