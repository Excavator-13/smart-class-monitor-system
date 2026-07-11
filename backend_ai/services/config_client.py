from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import requests


def parse_json_field(value: Any | None, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
    return default


def _items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and "data" in payload:
        payload = payload["data"]
    if isinstance(payload, dict) and "items" in payload:
        payload = payload["items"]
    elif isinstance(payload, dict) and "records" in payload:
        payload = payload["records"]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


@dataclass
class ConfigCache:
    streams: dict[str, dict[str, Any]] = field(default_factory=dict)
    zones_by_stream: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    rules: dict[str, dict[str, Any]] = field(default_factory=dict)
    face_features: dict[str, dict[str, Any]] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


class ConfigClient:
    def __init__(self, base_url: str = "http://localhost:8080", timeout: float = 5.0, session: Any | None = None, internal_token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.internal_token = internal_token
        self.cache = ConfigCache()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        headers = {}
        if self.internal_token:
            headers["X-Internal-Token"] = self.internal_token
        response = self.session.get(f"{self.base_url}{path}", params=params, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def load_streams(self) -> int:
        items = _items(self._get("/streams"))
        self.cache.streams = {
            str(item.get("stream_id")): item
            for item in items
            if item.get("stream_id") and item.get("status", "enabled") != "disabled"
        }
        self.cache.updated_at = time.time()
        return len(self.cache.streams)

    def load_zones(self, stream_id: str | None = None) -> int:
        stream_ids = [stream_id] if stream_id else list(self.cache.streams.keys())
        count = 0
        for sid in stream_ids:
            items = _items(self._get("/zones", params={"stream_id": sid}))
            zones = [zone for zone in items if zone.get("enabled", True)]
            self.cache.zones_by_stream[sid] = zones
            count += len(zones)
        self.cache.updated_at = time.time()
        return count

    def load_rules(self) -> int:
        items = _items(self._get("/rules"))
        self.cache.rules = {
            str(item.get("rule_type")): item
            for item in items
            if item.get("rule_type") and item.get("enabled", True)
        }
        self.cache.updated_at = time.time()
        return len(self.cache.rules)

    def load_face_features(self, student_id: str | None = None) -> int:
        items = _items(self._get("/students/face-features"))
        features = {
            str(item.get("student_id")): item
            for item in items
            if item.get("student_id") and item.get("enabled", True)
        }
        if student_id:
            if student_id in features:
                self.cache.face_features[student_id] = features[student_id]
        else:
            self.cache.face_features = features
        self.cache.updated_at = time.time()
        return len(self.cache.face_features)

    def reload(self, stream_id: str | None = None, reload_items: list[str] | None = None) -> dict[str, Any]:
        items = set(reload_items or ["streams", "zones", "rules"])
        result: dict[str, Any] = {"stream_id": stream_id, "updated_at": time.time()}
        if "streams" in items:
            result["streams_loaded"] = self.load_streams()
        if "zones" in items:
            result["zones_loaded"] = self.load_zones(stream_id)
        if "rules" in items:
            result["rules_loaded"] = self.load_rules()
        return result

    def reload_face_features(self, scope: str = "all", student_id: str | None = None) -> dict[str, Any]:
        loaded = self.load_face_features(student_id if scope != "all" else None)
        return {"loaded_count": loaded, "updated_at": time.time()}

    def get_stream(self, stream_id: str) -> dict[str, Any] | None:
        return self.cache.streams.get(stream_id)

    def get_zones(self, stream_id: str) -> list[dict[str, Any]]:
        return self.cache.zones_by_stream.get(stream_id, [])

    def get_rule(self, rule_type: str) -> dict[str, Any]:
        return self.cache.rules.get(rule_type, {})

    def get_face_features(self) -> dict[str, dict[str, Any]]:
        return self.cache.face_features