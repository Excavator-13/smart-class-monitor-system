from __future__ import annotations

import logging
from typing import Any

import numpy as np
import requests

logger = logging.getLogger(__name__)


def _to_json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: _to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_safe(item) for item in value]
    return value


class AlertClient:
    def __init__(self, base_url: str = "http://localhost:8080", timeout: float = 5.0,
                 session: Any | None = None, internal_token: str | None = None,
                 dingtalk: Any | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.internal_token = internal_token
        self.dingtalk = dingtalk

    def _headers(self) -> dict[str, str] | None:
        return {"X-Internal-Token": self.internal_token} if self.internal_token else None

    def map_event_to_alert(self, event: dict[str, Any], record_path: str | None = None, event_time_offset: float | None = None) -> dict[str, Any]:
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
        return _to_json_safe({
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
            "event_time_offset": event_time_offset,
            "extra": {"source": "backend_ai"},
        })

    def push_alert(self, event: dict[str, Any], record_path: str | None = None) -> dict[str, Any]:
        payload = self.map_event_to_alert(event, record_path=record_path)
        headers = {}
        if self.internal_token:
            headers["X-Internal-Token"] = self.internal_token
        response = self.session.post(f"{self.base_url}/alerts/ai", json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()

        # 钉钉通知 + 逐级上报
        if self.dingtalk:
            try:
                alert_name = event.get("event_type", "未知告警")
                stream = event.get("stream_id", "")
                self.dingtalk(f"{alert_name} | 摄像头：{stream}")
            except Exception:
                logger.exception("钉钉通知失败")

        return response.json()
