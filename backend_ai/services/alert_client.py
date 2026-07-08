from __future__ import annotations

from typing import Any

import requests


class AlertClient:
    def __init__(self, base_url: str = "http://localhost:8080", timeout: float = 5.0, session: Any | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def map_event_to_alert(self, event: dict[str, Any], record_path: str | None = None) -> dict[str, Any]:
        target = event.get("target") or {}
        zone = event.get("zone") or {}
        target_info = {
            key: value
            for key, value in {
                "track_id": target.get("track_id"),
                "bbox": target.get("bbox"),
            }.items()
            if value is not None
        }
        return {
            "event_id": event.get("event_id"),
            "stream_id": event.get("stream_id"),
            "alert_type": event.get("event_type"),
            "alert_name": event.get("event_name"),
            "level": event.get("level"),
            "confidence": event.get("confidence"),
            "occurred_at": event.get("occurred_at"),
            "duration_seconds": event.get("duration_seconds"),
            "student_id": target.get("student_id"),
            "target_info": target_info or None,
            "zone_id": zone.get("zone_id"),
            "snapshot_path": event.get("snapshot_path"),
            "record_path": record_path,
            "extra": {"source": "backend_ai"},
        }

    def push_alert(self, event: dict[str, Any], record_path: str | None = None) -> dict[str, Any]:
        payload = self.map_event_to_alert(event, record_path=record_path)
        response = self.session.post(f"{self.base_url}/alerts/ai", json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

