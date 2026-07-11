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


class StreamManager:
    def __init__(self, config_client: Any, offline_after_seconds: float = 10.0, reconnect_interval_seconds: float = 3.0):
        self.config_client = config_client
        self.offline_after_seconds = offline_after_seconds
        self.reconnect_interval_seconds = reconnect_interval_seconds
        self._states: dict[str, StreamState] = {}
        self._captures: dict[str, Any] = {}
        self._threads: dict[str, threading.Thread] = {}
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
        while not self._stop.is_set():
            state = self._states[stream_id]
            if not state.rtmp_url:
                state.online = False
                state.last_error = "missing rtmp_url"
                time.sleep(self.reconnect_interval_seconds)
                continue

            cap = self._captures.get(stream_id)
            if cap is None or not cap.isOpened():
                cap = cv2.VideoCapture(state.rtmp_url)
                self._captures[stream_id] = cap
                if not cap.isOpened():
                    state.online = False
                    state.last_error = "video stream read failed"
                    time.sleep(self.reconnect_interval_seconds)
                    continue

            ok, frame = cap.read()
            now = time.time()
            if not ok or frame is None:
                state.online = False
                state.last_error = "video stream read failed"
                cap.release()
                time.sleep(self.reconnect_interval_seconds)
                continue

            with self._lock:
                state.frame = frame
                state.online = True
                state.last_frame_at = now
                state.last_error = None

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
        if state.last_frame_at and time.time() - state.last_frame_at > self.offline_after_seconds:
            state.online = False
        return None if state.frame is None else state.frame.copy()

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

