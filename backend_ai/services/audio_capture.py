"""从 RTMP 流提取音频（FFmpeg 子进程）"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from backend_ai.utils.logger import get_logger


logger = get_logger(__name__)


class AudioCapture:
    """通过 FFmpeg 从 RTMP 流提取 PCM 音频数据"""

    def __init__(
        self,
        rtmp_url: str,
        sample_rate: int = 16000,
        ffmpeg_executable: str | None = None,
        restart_interval_seconds: float = 3.0,
    ):
        self.rtmp_url = rtmp_url
        self.sample_rate = sample_rate
        self.ffmpeg_executable = ffmpeg_executable
        self.restart_interval_seconds = max(0.0, restart_interval_seconds)
        self._proc: subprocess.Popen | None = None
        self._next_start_at = 0.0
        self.last_error: str | None = None
        self.chunks_read = 0
        self.last_chunk_at: float | None = None

    def start(self) -> bool:
        """启动 FFmpeg 子进程，将音频以 float32 PCM 格式 pipe 输出"""
        if self.running:
            return True
        self._discard_finished_process()
        now = time.monotonic()
        if now < self._next_start_at:
            return False

        executable = self._resolve_ffmpeg_executable()
        if not executable:
            self.last_error = "ffmpeg executable not found"
            self._next_start_at = now + self.restart_interval_seconds
            logger.error("Audio capture unavailable: %s", self.last_error)
            return False

        try:
            self._proc = subprocess.Popen(
                [
                    executable,
                    "-nostdin",
                    "-loglevel", "error",
                    "-rw_timeout", "5000000",
                    "-i", self.rtmp_url,
                    "-f", "f32le",           # float32 PCM
                    "-ar", str(self.sample_rate),  # 采样率
                    "-ac", "1",              # 单声道
                    "-vn",                   # 不要视频
                    "pipe:1",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            self.last_error = None
            logger.info("Audio capture process started pid=%s", self._proc.pid)
            return True
        except OSError as exc:
            self._proc = None
            self.last_error = f"ffmpeg start failed: {exc}"
            self._next_start_at = now + self.restart_interval_seconds
            logger.error("Audio capture unavailable: %s", self.last_error)
            return False

    def read_chunk(self, chunk_ms: int = 1000) -> np.ndarray | None:
        """读取一段音频数据，返回 float32 numpy 数组
        
        Args:
            chunk_ms: 读取的音频时长（毫秒），默认 1000ms。
                     与 AudioService 的 window_ms 配置保持一致。
        """
        if not self.running and not self.start():
            return None
        if self._proc is None or self._proc.stdout is None:
            return None
        n_samples = int(self.sample_rate * chunk_ms / 1000)
        n_bytes = n_samples * 4  # float32 = 4 bytes
        raw = self._proc.stdout.read(n_bytes)
        if not raw or len(raw) < 256:
            if not self.running:
                return_code = self._proc.poll() if self._proc is not None else None
                self.last_error = f"ffmpeg exited with code {return_code}"
                self._next_start_at = time.monotonic() + self.restart_interval_seconds
                logger.warning("Audio capture stopped: %s", self.last_error)
                self._discard_finished_process()
            return None
        self.chunks_read += 1
        self.last_chunk_at = time.time()
        if self.chunks_read == 1:
            logger.info("Audio PCM capture confirmed: received %s bytes", len(raw))
        return np.frombuffer(raw, dtype=np.float32)

    def stop(self) -> None:
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception:
                self._proc.kill()
            self._proc = None

    def _resolve_ffmpeg_executable(self) -> str | None:
        if self.ffmpeg_executable:
            return self.ffmpeg_executable
        executable = shutil.which("ffmpeg")
        if executable:
            return executable
        candidates = [
            Path(sys.prefix) / "Library" / "bin" / "ffmpeg.exe",
            Path(sys.prefix) / "bin" / "ffmpeg",
        ]
        return next((str(path) for path in candidates if path.is_file()), None)

    def _discard_finished_process(self) -> None:
        if self._proc is None or self._proc.poll() is None:
            return
        if self._proc.stdout is not None:
            try:
                self._proc.stdout.close()
            except Exception:
                pass
        self._proc = None

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None
