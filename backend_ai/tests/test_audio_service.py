from __future__ import annotations

import numpy as np

from backend_ai.services.audio_service import AudioService


def _make_tone(freq: float, duration: float = 1.0, sr: int = 16000, amplitude: float = 1.0) -> np.ndarray:
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return (np.sin(2 * np.pi * freq * t) * amplitude).astype(np.float32)


def test_loaded_always_true():
    service = AudioService()
    assert service.loaded is True


def test_no_audio_no_detection():
    service = AudioService()
    detections = service.process_audio("s1", None)
    assert detections == []


def test_empty_audio_no_detection():
    service = AudioService()
    detections = service.process_audio("s1", np.array([], dtype=np.float32))
    assert detections == []


def test_baseline_building_no_detection():
    """基线建立期间不产生事件"""
    service = AudioService(sample_rate=16000, window_ms=100)
    silence = np.zeros(1600, dtype=np.float32)  # 100ms
    for _ in range(10):
        dets = service.process_audio("s1", silence)
    for _ in range(40):
        dets = service.process_audio("s1", silence)
        assert dets == []


def test_high_energy_triggers_detection():
    """高能量音频应触发异常声学事件"""
    service = AudioService(sample_rate=16000, window_ms=100)

    # 建立基线（安静环境）
    silence = np.zeros(1600, dtype=np.float32)
    for _ in range(60):
        service.process_audio("s1", silence)

    # 突然大声（模拟尖叫）
    scream = _make_tone(2000, 0.1, 16000, 0.95) + np.random.randn(1600).astype(np.float32) * 0.05
    dets = service.process_audio("s1", scream)

    assert len(dets) > 0
    assert dets[0]["event_type"] == "abnormal_sound"
    assert "sound_type" in dets[0]["target"]
    assert dets[0]["confidence"] > 0


def test_real_amplitude_jump_triggers_scream_detection():
    """相同频率下的音量突增也必须被检测。

    这覆盖真实采集中“普通背景声 -> 高音量尖叫”的基础场景，
    防止每块峰值归一化把音量差异抹掉。
    """
    service = AudioService(sample_rate=16000, window_ms=100)
    background = _make_tone(1000, 0.1, 16000, 0.01)
    for _ in range(50):
        service.process_audio("s1", background)

    scream = _make_tone(2000, 0.1, 16000, 0.50)
    dets = service.process_audio("s1", scream)

    assert len(dets) == 1
    assert dets[0]["event_type"] == "abnormal_sound"
    assert dets[0]["target"]["sound_type"] == "scream"


def test_tiny_noise_after_silent_baseline_does_not_trigger():
    service = AudioService(sample_rate=16000, window_ms=100)
    silence = np.zeros(1600, dtype=np.float32)
    for _ in range(50):
        service.process_audio("s1", silence)

    tiny_noise = np.random.default_rng(42).normal(0, 0.0001, 1600).astype(np.float32)
    assert service.process_audio("s1", tiny_noise) == []


def test_cooldown_prevents_repeat():
    """冷却时间内不重复触发"""
    service = AudioService(sample_rate=16000, window_ms=100)

    silence = np.zeros(1600, dtype=np.float32)
    for _ in range(60):
        service.process_audio("s1", silence)

    noise = _make_tone(2000, 0.1, 16000, 0.95)
    dets1 = service.process_audio("s1", noise)
    dets2 = service.process_audio("s1", noise)

    assert len(dets2) == 0


def test_status():
    service = AudioService()
    status = service.status()
    assert status["loaded"] is True
    assert "total_events" in status
    assert "window_ms" in status
