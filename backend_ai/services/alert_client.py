from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import requests

from backend_ai.services.event_service import EVENT_NAMES

logger = logging.getLogger(__name__)

# 钉钉通知白名单（只推这些事件）
DINGTALK_ALERT_TYPES = {
    "stranger_detected", "danger_zone_intrusion", "danger_zone_stay",
    "danger_zone_approach", "crowd_gathering", "fall_detected",
    "flame_detected", "spoof_detected", "deepfake_detected",
    "abnormal_sound", "stream_offline", "phone_usage",
    "head_down", "leave_seat",
}


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
                 dingtalk: Any | None = None, snapshot_root: Path | None = None,
                 nginx_base_url: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.internal_token = internal_token
        self.dingtalk = dingtalk
        self.snapshot_root = snapshot_root
        self.nginx_base_url = (nginx_base_url or "").rstrip("/")

    def _headers(self) -> dict[str, str] | None:
        return {"X-Internal-Token": self.internal_token} if self.internal_token else None

    def _resolve_local_snapshot(self, snapshot_path: str) -> str:
        if not snapshot_path:
            return snapshot_path
        if self.snapshot_root is not None and snapshot_path.startswith("/snapshots/"):
            local = self.snapshot_root / snapshot_path[len("/snapshots/"):]
            if local.exists():
                return str(local)
        if self.nginx_base_url and snapshot_path.startswith("/snapshots/"):
            return f"{self.nginx_base_url}{snapshot_path}"
        return snapshot_path

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

    def push_alert(self, event: dict[str, Any], record_path: str | None = None, event_time_offset: float | None = None) -> dict[str, Any]:
        payload = self.map_event_to_alert(event, record_path=record_path, event_time_offset=event_time_offset)
        headers = {}
        if self.internal_token:
            headers["X-Internal-Token"] = self.internal_token
        response = self.session.post(f"{self.base_url}/alerts/ai", json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()

        # 钉钉通知 + 逐级上报
        if self.dingtalk:
            try:
                event_type = event.get("event_type", "")
                if event_type not in DINGTALK_ALERT_TYPES:
                    logger.debug("事件 %s 不在钉钉通知范围，跳过", event_type)
                else:
                    alert_name = EVENT_NAMES.get(event_type, event_type)
                    stream = event.get("stream_id", "")
                    snapshot = event.get("snapshot_path", "")
                    local_snapshot = self._resolve_local_snapshot(snapshot)
                    self.dingtalk(f"{alert_name} | 摄像头：{stream}", snapshot=local_snapshot)
            except Exception:
                logger.exception("钉钉通知失败")

        return response.json()