from __future__ import annotations

import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from backend_ai.utils.geometry import parse_polygon_coordinates
from backend_ai.utils.image_utils import draw_text
from backend_ai.utils.logger import get_logger


class AnalysisService:
    ZONE_COLORS: dict[str, tuple[int, int, int]] = {
        "danger": (0, 0, 255),
        "phone_forbidden": (0, 140, 255),
    }
    SNAPSHOT_EVENT_TYPES = {
        "danger_zone_intrusion",
        "danger_zone_stay",
        "danger_zone_approach",
        "stranger_detected",
        "phone_usage",
        "head_down",
        "crowd_gathering",
        "fall_detected",
        "flame_detected",
        "spoof_detected",
        "deepfake_detected",
    }
    VISIBLE_DETECTION_EVENT_TYPES = {
        "face_recognized",
        "phone_usage",
        "spoof_detected",
        "deepfake_detected",
        "flame_detected",
        "danger_zone_intrusion",
        "danger_zone_stay",
        "danger_zone_approach",
    }
    VISIBLE_OBJECT_CLASSES = {"person", "student"}
    RULE_GOVERNED_TYPES = frozenset({
        "stranger_detected",
        "leave_seat",
        "stream_offline",
        "spoof_detected",
        "deepfake_detected",
        "abnormal_sound",
    })

    def __init__(self, face_service: Any, zone_service: Any, behavior_service: Any, event_service: Any, config_client: Any, fire_service: Any | None = None, anti_spoof_service: Any | None = None, audio_service: Any | None = None, alert_client: Any | None = None, snapshot_root: Path | None = None, snapshot_pusher: Any | None = None, alert_cooldown_seconds: float = 10.0, alert_overlay_seconds: float = 2.0):
        self.face_service = face_service
        self.zone_service = zone_service
        self.behavior_service = behavior_service
        self.fire_service = fire_service
        self.anti_spoof_service = anti_spoof_service
        self.audio_service = audio_service
        self.event_service = event_service
        self.config_client = config_client
        self.alert_client = alert_client
        self.snapshot_root = snapshot_root
        self.snapshot_pusher = snapshot_pusher
        self.alert_cooldown_seconds = alert_cooldown_seconds
        self.alert_overlay_seconds = alert_overlay_seconds
        self.logger = get_logger(__name__)
        self._latencies: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=100))
        self._alert_overlays: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
        # 音视频联动：近 5 秒音频事件历史
        self._audio_history: deque[dict[str, Any]] = deque(maxlen=50)

    def analyze_frame(self, stream_id: str, frame: np.ndarray, modules: set[str] | None = None, objects: list[dict[str, Any]] | None = None, audio_chunk: np.ndarray | None = None) -> list[dict[str, Any]]:
        enabled = modules or {"face", "zone", "behavior"}
        detected: list[dict[str, Any]] = []
        height, width = frame.shape[:2]

        if "face" in enabled:
            started = time.perf_counter()
            face_detections = self.face_service.recognize_frame(frame, self.config_client.get_face_features())
            self._observe_latency("face", started)
            detected.extend(face_detections)
            self._draw_detections(frame, face_detections, color=(80, 220, 80))

            if "anti_spoof" in enabled and self.anti_spoof_service is not None:
                faces_with_bbox = [
                    {"track_id": r.get("target", {}).get("track_id", f"face_{i}"),
                     "bbox": r.get("target", {}).get("bbox"),
                     "landmarks": r.get("target", {}).get("landmarks")}
                    for i, r in enumerate(face_detections)
                ]
                anti_spoof_detections = self.anti_spoof_service.detect(stream_id, faces_with_bbox, frame)
                detected.extend(anti_spoof_detections)
                self._draw_detections(frame, anti_spoof_detections, color=(0, 0, 255))

        object_list = objects if objects is not None else []
        needs_objects = "behavior" in enabled or "zone" in enabled
        if needs_objects and objects is None:
            started = time.perf_counter()
            object_list = self.behavior_service.detect_objects(frame)
            self._observe_latency("behavior", started)
        if self.behavior_service.loaded:
            self._draw_objects(frame, object_list)

        zones = self.config_client.get_zones(stream_id) if ("zone" in enabled or "behavior" in enabled) else []
        danger_zones = [z for z in zones if z.get("zone_type") == "danger"]
        phone_forbidden_zones = [z for z in zones if z.get("zone_type") == "phone_forbidden"]

        if "behavior" in enabled:
            rules = {k: v for k, v in self.config_client.cache.rules.items()}
            behavior_detections = self.behavior_service.detect_from_objects(stream_id, object_list, rules, phone_forbidden_zones=phone_forbidden_zones, frame_size=(width, height))
            detected.extend(behavior_detections)
            self._draw_detections(frame, behavior_detections, color=(0, 255, 255))

        if "zone" in enabled:
            started = time.perf_counter()
            self._draw_zones(frame, zones)
            if not zones:
                self._draw_status(frame, "Danger zone not configured", color=(0, 220, 255))
            persons = [obj for obj in object_list if obj.get("class_name") in {"person", "student"}]
            zone_detections = self.zone_service.detect(
                stream_id,
                persons,
                danger_zones,
                self.config_client.get_rule("danger_zone"),
                frame_size=(width, height),
            )
            detected.extend(zone_detections)
            self._draw_detections(frame, zone_detections, color=(0, 0, 255))
            self._observe_latency("zone", started)

        if "fire" in enabled and self.fire_service is not None:
            fire_detections = self.fire_service.detect(
                stream_id,
                frame,
                {k: v for k, v in self.config_client.cache.rules.items()},
            )
            detected.extend(fire_detections)
            self._draw_detections(frame, fire_detections, color=(0, 80, 255))

        if "audio" in enabled and self.audio_service is not None:
            detected.extend(self.audio_service.process_audio(stream_id, audio_chunk))

        # 音视频联动：同帧内音频事件增强视频事件置信度
        detected = self._fuse_audio_video(detected)

        events = []
        for item in detected:
            if item["event_type"] in self.RULE_GOVERNED_TYPES and not self.config_client.get_rule(item["event_type"]):
                continue
            configured_level = self._event_level(
                item["event_type"], item.get("level", "warning")
            )
            event, should_confirm = self.event_service.observe(
                stream_id=stream_id,
                event_type=item["event_type"],
                track_key=str(item.get("track_key", item["event_type"])),
                confidence=float(item.get("confidence", 0)),
                threshold_seconds=float(item.get("threshold_seconds", 0)),
                cooldown_seconds=self.alert_cooldown_seconds,
                level=configured_level,
                target=item.get("target"),
                zone=item.get("zone"),
                continuity_gap_seconds=item.get("continuity_gap_seconds"),
            )
            if should_confirm:
                self._add_alert_overlay(stream_id, event)
                if self.alert_client is not None:
                    try:
                        if event["event_type"] in self.SNAPSHOT_EVENT_TYPES:
                            event["snapshot_path"] = self._save_snapshot(frame, event["event_id"])
                        self.alert_client.push_alert(event)
                        self.event_service.mark_confirmed(event["event_id"])
                    except Exception as exc:
                        self.logger.warning("Failed to push alert event_id=%s type=%s: %s", event.get("event_id"), event.get("event_type"), exc)
            events.append(event)
        self._draw_alert_overlays(frame, stream_id)
        return events

    def observe_stream_offline(self, stream_id: str) -> dict[str, Any]:
        if "stream_offline" in self.RULE_GOVERNED_TYPES and not self.config_client.get_rule("stream_offline"):
            return {"event_id": "", "event_type": "stream_offline", "event_status": "skipped", "level": "high", "confidence": 1.0}
        event, should_confirm = self.event_service.observe(
            stream_id=stream_id,
            event_type="stream_offline",
            track_key=stream_id,
            confidence=1.0,
            threshold_seconds=0,
            cooldown_seconds=self.alert_cooldown_seconds,
            level=self._event_level("stream_offline", "high"),
            target={"track_id": stream_id},
        )
        if should_confirm and self.alert_client is not None:
            try:
                self.alert_client.push_alert(event)
                self.event_service.mark_confirmed(event["event_id"])
            except Exception as exc:
                self.logger.warning("Failed to push stream_offline alert stream_id=%s: %s", stream_id, exc)
        return event

    def _event_level(self, event_type: str, default: str) -> str:
        resolver = getattr(self.config_client, "get_event_level", None)
        return resolver(event_type, default) if callable(resolver) else default

    def avg_latency_ms(self, module: str) -> float | None:
        values = self._latencies.get(module)
        if not values:
            return None
        return round(sum(values) / len(values), 2)

    def _observe_latency(self, module: str, started: float) -> None:
        self._latencies[module].append((time.perf_counter() - started) * 1000)

    # 音视频联动规则：音频事件类型 → 视频事件类型 → 置信度提升
    AUDIO_VIDEO_FUSION: dict[str, dict[str, float]] = {
        "abnormal_sound": {
            "fall_detected": 0.15,
            "stranger_detected": 0.12,
            "danger_zone_intrusion": 0.10,
            "danger_zone_stay": 0.10,
            "danger_zone_approach": 0.08,
            "crowd_gathering": 0.10,
            "phone_usage": 0.05,
            "head_down": 0.05,
            "leave_seat": 0.05,
        },
    }

    def _fuse_audio_video(self, detected: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """音视频联动：近 5 秒内音频+视频同时出现时互相提升置信度"""
        now = time.time()

        # 将本次检测到的音频事件加入历史队列
        audio_events = [d for d in detected if d.get("event_type") == "abnormal_sound"]
        for ae in audio_events:
            self._audio_history.append({"time": now, "confidence": float(ae.get("confidence", 0))})

        # 清理超过 5 秒的历史
        while self._audio_history and now - self._audio_history[0]["time"] > 5.0:
            self._audio_history.popleft()

        # 没有音频历史或没有视频事件 → 跳过
        video_events = [d for d in detected if d.get("event_type") != "abnormal_sound"]
        if not self._audio_history or not video_events:
            return detected

        # 最近 5 秒内音频的最高置信度
        best_audio = max(e["confidence"] for e in self._audio_history)
        if best_audio < 0.6:
            return detected

        fusion_map = self.AUDIO_VIDEO_FUSION.get("abnormal_sound", {})

        # 增强视频事件：有音频异常 → 对应视频事件置信度提升
        for ve in video_events:
            et = ve.get("event_type", "")
            boost = fusion_map.get(et, 0.03)
            old_conf = float(ve.get("confidence", 0))
            ve["confidence"] = round(min(1.0, old_conf + boost), 4)
            ve["fusion"] = True  # 标记为音视频联动
            if ve.get("level") == "warning" and ve["confidence"] >= 0.85:
                ve["level"] = "high"

        # 增强音频事件：有视频异常 → 音频置信度也提升
        video_event_types = {ve.get("event_type") for ve in video_events}
        if any(et in fusion_map for et in video_event_types):
            for ae in audio_events:
                old_conf = float(ae.get("confidence", 0))
                ae["confidence"] = round(min(1.0, old_conf + 0.08), 4)
                ae["fusion"] = True

        return detected

    def _save_snapshot(self, frame: np.ndarray, event_id: str) -> str | None:
        if self.snapshot_root is None:
            return None
        day = time.strftime("%Y%m%d")
        directory = self.snapshot_root / day
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{event_id}.jpg"
        ok = cv2.imwrite(str(path), frame)
        if not ok:
            raise RuntimeError("snapshot encode failed")
        relative_path = f"/snapshots/{day}/{event_id}.jpg"
        if self.snapshot_pusher is not None:
            self.snapshot_pusher.push_async(path, relative_path)
        return relative_path

    def _draw_objects(self, frame: np.ndarray, objects: list[dict[str, Any]]) -> None:
        for idx, obj in enumerate(objects):
            if obj.get("class_name") not in self.VISIBLE_OBJECT_CLASSES:
                continue
            bbox = obj.get("bbox")
            if bbox is None or len(bbox) == 0:
                continue
            label = obj.get("class_name") or f"object_{idx + 1}"
            confidence = obj.get("confidence")
            if confidence is not None:
                label = f"{label} {float(confidence):.2f}"
            self._draw_bbox(frame, bbox, label, color=(255, 180, 60))

    def _draw_detections(self, frame: np.ndarray, detections: list[dict[str, Any]], color: tuple[int, int, int]) -> None:
        for item in detections:
            if item.get("event_type") not in self.VISIBLE_DETECTION_EVENT_TYPES:
                continue
            target = item.get("target") or {}
            bbox = target.get("bbox")
            if bbox is None or len(bbox) == 0:
                continue
            event_type = str(item.get("event_type", "event"))
            if event_type == "face_recognized":
                label = target.get("student_no") or target.get("student_id") or target.get("student_name") or "recognized"
            else:
                label = {
                    "phone_usage": "Using phone",
                    "spoof_detected": "Spoof detected",
                    "deepfake_detected": "Deepfake detected",
                    "flame_detected": "Fire",
                    "danger_zone_intrusion": "Danger zone intrusion",
                    "danger_zone_stay": "Danger zone stay",
                    "danger_zone_approach": "Danger zone approach",
                }.get(event_type, event_type)
            label_parts = [str(label)]
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
            zone_type = zone.get("zone_type", "danger")
            color = self.ZONE_COLORS.get(zone_type, (0, 0, 255))
            cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)
            label = str(zone.get("zone_name") or zone.get("zone_type") or "danger zone")
            x0, y0 = points[0]
            draw_text(frame, label, (x0, max(18, y0 - 8)), font_scale=0.55, color=color, thickness=2)

    def _draw_status(self, frame: np.ndarray, text: str, color: tuple[int, int, int]) -> None:
        height, width = frame.shape[:2]
        scale = 0.58
        thickness = 2
        (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
        x = max(8, width - text_width - 12)
        y = max(text_height + 10, 28)
        cv2.rectangle(frame, (x - 6, y - text_height - 8), (width - 6, y + 6), (0, 0, 0), -1)
        draw_text(frame, text, (x, y), font_scale=scale, color=color, thickness=thickness)

    def _add_alert_overlay(self, stream_id: str, event: dict[str, Any], now: float | None = None) -> None:
        current = time.time() if now is None else now
        labels = {
            "flame_detected": "Fire detected",
            "phone_usage": "Using phone",
            "spoof_detected": "Spoof detected",
            "deepfake_detected": "Deepfake detected",
            "fall_detected": "Fall detected",
        }
        event_type = str(event.get("event_type") or "alert")
        self._alert_overlays[stream_id].append({
            "event_id": event.get("event_id"),
            "text": labels.get(event_type, event_type),
            "event_type": event_type,
            "bbox": (event.get("target") or {}).get("bbox"),
            "expires_at": current + self.alert_overlay_seconds,
        })

    def _draw_alert_overlays(self, frame: np.ndarray, stream_id: str, now: float | None = None) -> None:
        current = time.time() if now is None else now
        queue = self._alert_overlays[stream_id]
        while queue and float(queue[0]["expires_at"]) <= current:
            queue.popleft()
        for index, item in enumerate(queue):
            text = str(item["text"])
            bbox = item.get("bbox")
            if bbox is not None and len(bbox) == 4:
                color = (0, 255, 255) if item.get("event_type") == "phone_usage" else (0, 80, 255)
                self._draw_bbox(frame, bbox, text, color=color)
            y = 28 + index * 28
            (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.58, 2)
            cv2.rectangle(frame, (8, y - text_height - 8), (text_width + 20, y + 6), (0, 0, 0), -1)
            draw_text(frame, text, (14, y), font_scale=0.58, color=(0, 80, 255), thickness=2)

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
        draw_text(frame, label, (x1, max(18, y1 - 8)), font_scale=0.55, color=color, thickness=2)