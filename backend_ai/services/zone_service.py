from __future__ import annotations

from typing import Any

from backend_ai.services.config_client import parse_json_field
from backend_ai.utils.geometry import (
    bbox_foot_point,
    distance_point_to_polygon,
    parse_polygon_coordinates,
    point_in_polygon,
)


class ZoneService:
    def detect(self, stream_id: str, persons: list[dict[str, Any]], zones: list[dict[str, Any]], rule: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        danger_zones = [z for z in zones if z.get("zone_type") == "danger"]
        detections: list[dict[str, Any]] = []
        config = parse_json_field((rule or {}).get("config_json"), {})
        safe_distance = float(config.get("safe_distance", 0.05))
        for person in persons:
            bbox = person.get("bbox")
            if bbox is None or len(bbox) == 0:
                continue
            foot = bbox_foot_point(bbox)
            track_id = person.get("track_id") or f"person_{len(detections) + 1}"
            for zone in danger_zones:
                polygon = parse_polygon_coordinates(zone.get("coordinates") or [])
                if len(polygon) < 3:
                    continue
                zone_info = {
                    "zone_id": zone.get("zone_id"),
                    "zone_name": zone.get("zone_name"),
                    "zone_type": zone.get("zone_type"),
                }
                target = {"track_id": track_id, "bbox": bbox}
                if point_in_polygon(foot, polygon):
                    detections.append(
                        {
                            "event_type": "danger_zone_intrusion",
                            "confidence": 1.0,
                            "level": "warning",
                            "target": target,
                            "zone": zone_info,
                            "track_key": f"{track_id}:{zone.get('zone_id')}:intrusion",
                            "threshold_seconds": 0,
                        }
                    )
                    detections.append(
                        {
                            "event_type": "danger_zone_stay",
                            "confidence": 1.0,
                            "level": "high",
                            "target": target,
                            "zone": zone_info,
                            "track_key": f"{track_id}:{zone.get('zone_id')}:stay",
                            "threshold_seconds": float(zone.get("threshold_seconds", 2)),
                        }
                    )
                else:
                    distance = distance_point_to_polygon(foot, polygon)
                    if distance < safe_distance:
                        detections.append(
                            {
                                "event_type": "danger_zone_approach",
                                "confidence": max(0.0, 1.0 - distance / max(safe_distance, 1e-9)),
                                "level": "warning",
                                "target": target,
                                "zone": zone_info,
                                "track_key": f"{track_id}:{zone.get('zone_id')}:approach",
                                "threshold_seconds": 0,
                            }
                        )
        return detections