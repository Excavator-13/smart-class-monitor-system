from __future__ import annotations

import threading
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
    "spoof_detected": "活体检测异常",
    "deepfake_detected": "疑似AI换脸攻击",
    "abnormal_sound": "异常声学事件",
    "stream_offline": "视频流中断",
}


@dataclass
class EventState:
    first_seen: float
    last_seen: float
    event_id: str = field(default_factory=lambda: f"evt_{uuid4().hex[:16]}")
    event_status: str = "candidate"
    occurred_at: str = field(default_factory=now_iso)


class EventService:
    def __init__(
        self,
        max_items: int = 500,
        default_cooldown_seconds: float = 10.0,
        state_expire_seconds: float = 300.0,
        continuity_gap_seconds: float = 2.0,
    ):
        self.events: deque[dict[str, Any]] = deque(maxlen=max_items)
        self._states: dict[tuple[str, str], EventState] = {}
        self._last_alerts: dict[tuple[str, str], float] = {}
        self.default_cooldown_seconds = default_cooldown_seconds
        self.state_expire_seconds = state_expire_seconds
        self.continuity_gap_seconds = max(0.0, continuity_gap_seconds)
        self._lock = threading.RLock()

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
        occurred_at: str | None = None,
    ) -> dict[str, Any]:
        return {
            "event_id": event_id or f"evt_{uuid4().hex[:16]}",
            "stream_id": stream_id,
            "event_type": event_type,
            "event_name": EVENT_NAMES.get(event_type, event_type),
            "level": level,
            "event_status": status,
            "confidence": round(float(confidence), 4),
            "occurred_at": occurred_at or now_iso(),
            "duration_seconds": round(float(duration_seconds), 3),
            "target": target,
            "zone": zone,
            "snapshot_path": snapshot_path,
        }

    def add_event(self, event: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            event_id = event.get("event_id")
            if event_id:
                for index, existing in enumerate(self.events):
                    if existing.get("event_id") == event_id:
                        self.events[index] = event
                        return event
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
        continuity_gap_seconds: float | None = None,
        now: float | None = None,
    ) -> tuple[dict[str, Any], bool]:
        del track_key  # 同类事件的连续周期与冷却统一按视频流聚合。
        current = time.time() if now is None else now
        with self._lock:
            self.expire_states(current)
            key = (stream_id, event_type)
            state = self._states.get(key)
            continuity_gap = self.continuity_gap_seconds if continuity_gap_seconds is None else max(0.0, float(continuity_gap_seconds))
            if state is None or current - state.last_seen > continuity_gap:
                state = EventState(first_seen=current, last_seen=current)
                self._states[key] = state
            else:
                state.last_seen = current

            duration = max(0.0, current - state.first_seen)
            threshold = max(0.0, float(threshold_seconds))
            cooldown = max(
                0.0,
                self.default_cooldown_seconds if cooldown_seconds is None else float(cooldown_seconds),
            )
            last_alert_at = self._last_alerts.get(key)
            cooldown_ready = last_alert_at is None or current - last_alert_at >= cooldown
            should_confirm = (
                state.event_status != "confirmed"
                and duration >= threshold
                and cooldown_ready
            )
            if should_confirm:
                state.event_status = "confirmed"
                self._last_alerts[key] = current

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
                occurred_at=state.occurred_at,
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
        with self._lock:
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
        with self._lock:
            for event in self.events:
                if event.get("event_id") == event_id:
                    event["event_status"] = "confirmed"

    def expire_states(self, now: float | None = None) -> int:
        current = time.time() if now is None else now
        with self._lock:
            expired = [
                key
                for key, state in self._states.items()
                if current - state.last_seen >= self.state_expire_seconds
            ]
            for key in expired:
                del self._states[key]
            return len(expired)

    def counts(self, stream_id: str | None = None) -> dict[str, int]:
        with self._lock:
            result: dict[str, int] = {}
            for event in list(self.events):
                if stream_id and event.get("stream_id") != stream_id:
                    continue
                event_type = str(event.get("event_type") or "unknown")
                result[event_type] = result.get(event_type, 0) + 1
            return result
