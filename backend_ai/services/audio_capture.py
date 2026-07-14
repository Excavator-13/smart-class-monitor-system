"""从 RTMP 流提取音频（FFmpeg 子进程）"""

from __future__ import annotations

import subprocess
from typing import Any

import numpy as np


class AudioCapture:
    """通过 FFmpeg 从 RTMP 流提取 PCM 音频数据"""

    def __init__(self, rtmp_url: str, sample_rate: int = 16000):
        self.rtmp_url = rtmp_url
        self.sample_rate = sample_rate
        self._proc: subprocess.Popen | None = None

    def start(self) -> None:
        """启动 FFmpeg 子进程，将音频以 float32 PCM 格式 pipe 输出"""
        if self._proc is not None:
            return
        try:
            self._proc = subprocess.Popen(
                [
                    "ffmpeg", "-i", self.rtmp_url,
                    "-f", "f32le",           # float32 PCM
                    "-ar", str(self.sample_rate),  # 采样率
                    "-ac", "1",              # 单声道
                    "-vn",                   # 不要视频
                    "-loglevel", "quiet",    # 不输出日志
                    "pipe:1",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            self._proc = None

    def read_chunk(self, chunk_ms: int = 1000) -> np.ndarray | None:
        """读取一段音频数据，返回 float32 numpy 数组"""
        if self._proc is None or self._proc.stdout is None:
            return None
        n_samples = int(self.sample_rate * chunk_ms / 1000)
        n_bytes = n_samples * 4  # float32 = 4 bytes
        raw = self._proc.stdout.read(n_bytes)
        if not raw or len(raw) < 256:
            return None
        return np.frombuffer(raw, dtype=np.float32)

    def stop(self) -> None:
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception:
                self._proc.kill()
            self._proc = None

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None
