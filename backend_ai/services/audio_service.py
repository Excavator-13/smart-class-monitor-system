from __future__ import annotations

import time
from collections import deque
from typing import Any

import numpy as np


class AudioService:
    """异常声学事件检测"""

    SOUND_TYPES = {
        "scream": {"freq_range": (500, 4000), "energy_ratio": 3.0, "label": "尖叫声"},
        "glass_break": {"freq_range": (3000, 8000), "energy_ratio": 2.5, "label": "玻璃破碎"},
        "gunshot": {"freq_range": (200, 2000), "energy_ratio": 8.0, "label": "疑似枪声"},
        "explosion": {"freq_range": (50, 500), "energy_ratio": 10.0, "label": "疑似爆炸声"},
        "loud_crash": {"freq_range": (100, 2000), "energy_ratio": 4.0, "label": "异常撞击声"},
    }

    def __init__(self, sample_rate: int = 16000, window_ms: int = 1000):
        self.sample_rate = sample_rate
        self.window_ms = window_ms
        self.window_samples = int(sample_rate * window_ms / 1000)
        self._energy_history: deque[float] = deque(maxlen=30)
        self._event_cooldowns: dict[str, float] = {}
        self._total_events = 0
        self._baseline_energy: float = 0.0
        self._baseline_samples = 0

    def process_audio(
        self,
        stream_id: str,
        audio_data: np.ndarray | None,
        sample_rate: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        处理音频数据块

        Args:
            stream_id: 视频流ID
            audio_data: float32 音频数组，shape (samples,) 或 (samples, channels)
                       None 表示无音频输入，返回空列表
            sample_rate: 实际采样率（默认使用初始化时的值）

        Returns:
            list[dict]: 检测到的异常声学事件
        """
        if audio_data is None or len(audio_data) == 0:
            return []

        sr = sample_rate or self.sample_rate

        # 转单声道
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        # 归一化
        audio = audio_data.astype(np.float32)
        max_val = np.abs(audio).max()
        if max_val > 0:
            audio = audio / max_val

        # 计算当前窗口的能量（RMS）
        energy = float(np.sqrt(np.mean(audio[-self.window_samples:] ** 2)))
        self._energy_history.append(energy)

        # 建立基线
        if self._baseline_samples < 50:
            self._baseline_energy = (
                self._baseline_energy * self._baseline_samples + energy
            ) / (self._baseline_samples + 1)
            self._baseline_samples += 1
            return []

        # 能量异常检测
        ratio = energy / max(self._baseline_energy, 1e-9)

        detections: list[dict[str, Any]] = []

        if ratio >= 3.0:  # 能量突然增大3倍以上
            freq_features = self._extract_frequency_features(audio, sr)

            for sound_type, config in self.SOUND_TYPES.items():
                if sound_type in self._event_cooldowns:
                    if time.time() - self._event_cooldowns[sound_type] < 15:
                        continue

                # 频率匹配
                freq_match = 0.0
                nyquist = sr / 2
                low_bin = max(0, int(config["freq_range"][0] / nyquist * len(freq_features)))
                high_bin = min(len(freq_features) - 1, int(config["freq_range"][1] / nyquist * len(freq_features)))

                if high_bin > low_bin:
                    band_energy = np.sum(freq_features[low_bin:high_bin])
                    total_energy = np.sum(freq_features)
                    if total_energy > 0:
                        band_ratio = band_energy / total_energy
                        freq_match = min(1.0, band_ratio * 3)

                # 综合置信度
                energy_match = min(1.0, ratio / config["energy_ratio"])
                confidence = (energy_match * 0.6 + freq_match * 0.4)

                if confidence >= 0.5:
                    self._event_cooldowns[sound_type] = time.time()
                    self._total_events += 1

                    if confidence >= 0.8:
                        level = "high"
                    elif confidence >= 0.65:
                        level = "warning"
                    else:
                        level = "info"

                    detections.append(
                        {
                            "event_type": "abnormal_sound",
                            "confidence": round(confidence, 4),
                            "level": level,
                            "target": {
                                "track_id": f"audio_{sound_type}",
                                "sound_type": sound_type,
                                "sound_label": config["label"],
                                "energy_ratio": round(ratio, 2),
                                "frequency_match": round(freq_match, 4),
                            },
                            "track_key": f"{stream_id}:{sound_type}",
                            "threshold_seconds": 0,
                            "cooldown_seconds": 15,
                        }
                    )

        # 只返回最高置信度的1个事件
        if detections:
            detections.sort(key=lambda d: d["confidence"], reverse=True)
            detections = detections[:1]

        return detections

    def _extract_frequency_features(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """提取频域特征（简化版FFT能量谱）"""
        n = len(audio)
        if n < 2:
            return np.zeros(1, dtype=np.float32)
        fft = np.abs(np.fft.rfft(audio))
        energy = fft ** 2
        energy_sum = energy.sum()
        if energy_sum > 0:
            energy = energy / energy_sum
        return energy.astype(np.float32)

    @property
    def loaded(self) -> bool:
        return True  # 纯信号处理，无需模型加载

    def status(self) -> dict[str, Any]:
        return {
            "loaded": self.loaded,
            "total_events": self._total_events,
            "baseline_energy": round(self._baseline_energy, 6),
            "baseline_samples": self._baseline_samples,
            "window_ms": self.window_ms,
            "sample_rate": self.sample_rate,
        }
