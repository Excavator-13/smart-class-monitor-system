from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from backend_ai.utils.response import now_iso


EVENT_NAMES = {
    "face_recognized": "已识别人员",
    "stranger_detected": "陌生人员出现",
    "danger_zone_intrusion": "危险区域入侵",
    "danger_zone_stay": "危险区域停留超时",
    "danger_zone_approach": "危险区域接近预警",
    "phone_usage": "使用手机",
    "head_down": "长时间低头",
    "crowd_gathering": "异常人流聚集",
    "fall_detected": "人员摔倒",
    "leave_seat": "长时间离座",
    "flame_detected": "明火检测",
    "stream_offline": "视频流中断",
}


@dataclass
class EventState:
    first_seen: float
    last_seen: float
    last_alert_at: float = 0.0
    event_id: str = field(default_factory=lambda: f"evt_{uuid4().hex[:16]}")
    event_status: str = "candidate"


class EventService:
    def __init__(self, max_items: int = 500, default_cooldown_seconds: float = 45.0, state_expire_seconds: float = 300.0):
        self.events: deque[dict[str, Any]] = deque(maxlen=max_items)
        self._states: dict[tuple[str, str, str], EventState] = {}
        self.default_cooldown_seconds = default_cooldown_seconds
        self.state_expire_seconds = state_expire_seconds

    def build_event(
        self,
        stream_id: str,
        event_type: str,
        confidence: float,
        level: str = "warning",
        target: dict[str, Any] | None = None,
        zone: dict[str, Any] | None = None,
        duration_seconds: float = 0.0,
        status: str = "candidate",
        snapshot_path: str | None = None,
        event_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "event_id": event_id or f"evt_{uuid4().hex[:16]}",
            "stream_id": stream_id,
            "event_type": event_type,
            "event_name": EVENT_NAMES.get(event_type, event_type),
            "level": level,
            "event_status": status,
            "confidence": round(float(confidence), 4),
            "occurred_at": now_iso(),
            "duration_seconds": round(float(duration_seconds), 3),
            "target": target,
            "zone": zone,
            "snapshot_path": snapshot_path,
        }

    def add_event(self, event: dict[str, Any]) -> dict[str, Any]:
        self.events.appendleft(event)
        return event

    def observe(
        self,
        stream_id: str,
        event_type: str,
        track_key: str,
        confidence: float,
        threshold_seconds: float = 0.0,
        cooldown_seconds: float | None = None,
        level: str = "warning",
        target: dict[str, Any] | None = None,
        zone: dict[str, Any] | None = None,
        snapshot_path: str | None = None,
        now: float | None = None,
    ) -> tuple[dict[str, Any], bool]:
        current = time.time() if now is None else now
        self.expire_states(current)
        key = (stream_id, event_type, track_key)
        state = self._states.get(key)
        if state is None:
            state = EventState(first_seen=current, last_seen=current)
            self._states[key] = state
        state.last_seen = current

        duration = current - state.first_seen
        cooldown = self.default_cooldown_seconds if cooldown_seconds is None else cooldown_seconds
        should_confirm = duration >= threshold_seconds and current - state.last_alert_at >= cooldown
        if should_confirm:
            state.event_status = "confirmed"
            state.last_alert_at = current

        event = self.build_event(
            stream_id=stream_id,
            event_type=event_type,
            confidence=confidence,
            level=level,
            target=target,
            zone=zone,
            duration_seconds=duration,
            status=state.event_status,
            snapshot_path=snapshot_path,
            event_id=state.event_id,
        )
        self.add_event(event)
        return event, should_confirm

    def query(
        self,
        stream_id: str | None = None,
        event_type: str | None = None,
        level: str | None = None,
        limit: int = 20,
        since: str | None = None,
    ) -> list[dict[str, Any]]:
        result = []
        for event in list(self.events):
            if stream_id and event.get("stream_id") != stream_id:
                continue
            if event_type and event.get("event_type") != event_type:
                continue
            if level and event.get("level") != level:
                continue
            if since and str(event.get("occurred_at", "")) <= since:
                continue
            result.append(event)
            if len(result) >= limit:
                break
        return result

    def mark_confirmed(self, event_id: str) -> None:
        for event in self.events:
            if event.get("event_id") == event_id:
                event["event_status"] = "confirmed"

    def expire_states(self, now: float | None = None) -> int:
        current = time.time() if now is None else now
        expired = [
            key
            for key, state in self._states.items()
            if current - state.last_seen >= self.state_expire_seconds
        ]
        for key in expired:
            del self._states[key]
        return len(expired)

    def counts(self, stream_id: str | None = None) -> dict[str, int]:
        result: dict[str, int] = {}
        for event in list(self.events):
            if stream_id and event.get("stream_id") != stream_id:
                continue
            event_type = str(event.get("event_type") or "unknown")
            result[event_type] = result.get(event_type, 0) + 1
        return result
