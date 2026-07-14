from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np


@dataclass
class StreamState:
    stream_id: str
    rtmp_url: str | None = None
    online: bool = False
    fps: float = 0.0
    last_frame_at: float | None = None
    last_error: str | None = None
    frame: np.ndarray | None = None
    failure_started_at: float | None = None
    offline_alerted: bool = False


class StreamManager:
    def __init__(self, config_client: Any, offline_after_seconds: float = 10.0, reconnect_interval_seconds: float = 3.0, frame_skip: int = 3):
        self.config_client = config_client
        self.offline_after_seconds = offline_after_seconds
        self.reconnect_interval_seconds = reconnect_interval_seconds
        self.frame_skip = frame_skip
        self._states: dict[str, StreamState] = {}
        self._captures: dict[str, Any] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._frame_counters: dict[str, int] = {}
        self._stop = threading.Event()
        self._lock = threading.RLock()

    def ensure_stream(self, stream_id: str) -> StreamState | None:
        stream = self.config_client.get_stream(stream_id)
        if not stream:
            return None
        with self._lock:
            state = self._states.setdefault(
                stream_id,
                StreamState(stream_id=stream_id, rtmp_url=stream.get("rtmp_url")),
            )
            state.rtmp_url = stream.get("rtmp_url")
            if stream_id not in self._threads:
                thread = threading.Thread(target=self._read_loop, args=(stream_id,), daemon=True)
                self._threads[stream_id] = thread
                thread.start()
            return state

    def _read_loop(self, stream_id: str) -> None:
        frame_count = 0
        fps_window_start = time.time()
        skip_counter = 0
        while not self._stop.is_set():
            state = self._states[stream_id]
            if not state.rtmp_url:
                self._mark_unavailable(state, "missing rtmp_url")
                time.sleep(self.reconnect_interval_seconds)
                continue

            cap = self._captures.get(stream_id)
            if cap is None or not cap.isOpened():
                cap = cv2.VideoCapture(state.rtmp_url)
                self._captures[stream_id] = cap
                if not cap.isOpened():
                    self._mark_unavailable(state, "video stream open failed")
                    time.sleep(self.reconnect_interval_seconds)
                    continue

            ok, frame = cap.read()
            now = time.time()
            if not ok or frame is None:
                self._mark_unavailable(state, "video stream read failed", now=now)
                cap.release()
                time.sleep(self.reconnect_interval_seconds)
                continue

            # 帧跳过：每 frame_skip 帧才更新一次可消费帧
            skip_counter += 1
            if skip_counter % self.frame_skip != 0:
                continue

            with self._lock:
                state.frame = frame
                state.online = True
                state.last_frame_at = now
                state.last_error = None
                state.failure_started_at = None
                state.offline_alerted = False

            frame_count += 1
            elapsed = now - fps_window_start
            if elapsed >= 1.0:
                state.fps = frame_count / elapsed
                frame_count = 0
                fps_window_start = now

    def set_frame_for_test(self, stream_id: str, frame: np.ndarray, rtmp_url: str = "mock://stream") -> None:
        with self._lock:
            self._states[stream_id] = StreamState(
                stream_id=stream_id,
                rtmp_url=rtmp_url,
                online=True,
                fps=1.0,
                last_frame_at=time.time(),
                frame=frame,
            )

    def get_frame(self, stream_id: str) -> np.ndarray | None:
        state = self.ensure_stream(stream_id) or self._states.get(stream_id)
        if not state:
            return None
        now = time.time()
        with self._lock:
            if state.online and state.last_frame_at and now - state.last_frame_at > self.offline_after_seconds:
                self._mark_unavailable(
                    state,
                    "video stream frame timeout",
                    now=state.last_frame_at,
                )
            if not state.online:
                return None
            return None if state.frame is None else state.frame.copy()

    def should_emit_offline_alert(self, stream_id: str, now: float | None = None) -> bool:
        """Return true once when one continuous unavailable period reaches the timeout."""
        current = time.time() if now is None else now
        with self._lock:
            state = self._states.get(stream_id)
            if state is None or state.failure_started_at is None:
                return False
            if current - state.failure_started_at < self.offline_after_seconds:
                return False
            if state.offline_alerted:
                return False
            state.offline_alerted = True
            return True

    def _mark_unavailable(
        self,
        state: StreamState,
        error: str,
        now: float | None = None,
    ) -> None:
        current = time.time() if now is None else now
        with self._lock:
            state.online = False
            state.last_error = error
            if state.failure_started_at is None:
                state.failure_started_at = current

    def status(self) -> list[dict[str, Any]]:
        stream_ids = set(self.config_client.cache.streams.keys()) | set(self._states.keys())
        result = []
        for stream_id in sorted(stream_ids):
            state = self._states.get(stream_id)
            stream = self.config_client.get_stream(stream_id) or {}
            result.append(
                {
                    "stream_id": stream_id,
                    "stream_name": stream.get("stream_name"),
                    "online": bool(state and state.online),
                    "fps": round(state.fps, 2) if state else 0,
                    "last_frame_at": state.last_frame_at if state else None,
                    "last_error": state.last_error if state else None,
                }
            )
        return result

    def stop(self) -> None:
        self._stop.set()
        for cap in self._captures.values():
            try:
                cap.release()
            except Exception:
                pass
