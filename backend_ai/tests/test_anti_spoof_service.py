from __future__ import annotations

import time

import numpy as np

from backend_ai.services.anti_spoof_service import AntiSpoofService


def _make_face(track_id: str, bbox: list[float]) -> dict:
    return {"track_id": track_id, "bbox": bbox, "landmarks": None}


def _make_face_with_eyes(track_id: str, bbox: list[float], eyes_open: bool = True) -> dict:
    """生成带伪造眼部关键点的人脸"""
    eye_y = 2 if eyes_open else 0.2
    left_eye = [
        np.array([10, eye_y]),
        np.array([11, eye_y + 1]),
        np.array([12, eye_y + 2]),
        np.array([13, eye_y + 1]),
        np.array([14, eye_y + 1]),
        np.array([15, eye_y]),
    ]
    right_eye = [
        np.array([20, eye_y]),
        np.array([21, eye_y + 1]),
        np.array([22, eye_y + 2]),
        np.array([23, eye_y + 1]),
        np.array([24, eye_y + 1]),
        np.array([25, eye_y]),
    ]
    landmarks = list(range(36)) + left_eye + right_eye + list(range(48, 68))
    return {"track_id": track_id, "bbox": bbox, "landmarks": landmarks}


def _make_open_eye_landmarks() -> list:
    # EAR ≈ 0.53
    eye = [np.array([30.0, 50.0]), np.array([35.0, 54.0]), np.array([40.0, 54.0]),
           np.array([45.0, 50.0]), np.array([40.0, 46.0]), np.array([35.0, 46.0])]
    return list(range(36)) + eye + eye + list(range(48, 68))


def _make_closed_eye_landmarks() -> list:
    # EAR ≈ 0.13
    eye = [np.array([30.0, 50.0]), np.array([35.0, 51.0]), np.array([40.0, 51.0]),
           np.array([45.0, 50.0]), np.array([40.0, 49.0]), np.array([35.0, 49.0])]
    return list(range(36)) + eye + eye + list(range(48, 68))


def test_loaded_always_true():
    service = AntiSpoofService()
    assert service.loaded is True


def test_no_faces_no_detection():
    service = AntiSpoofService()
    detections = service.detect("stream_1", [])
    assert detections == []


def test_detect_accepts_numpy_bbox_with_frame():
    service = AntiSpoofService()
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    face = {"track_id": "track_1", "bbox": np.array([10, 10, 100, 100]), "landmarks": None}

    detections = service.detect("stream_1", [face], frame)

    assert detections == []


def test_eye_aspect_ratio_open():
    # 睁眼：眼宽15px，眼高8px → EAR ≈ 0.53
    eye_open = [
        np.array([30.0, 50.0]), np.array([35.0, 54.0]), np.array([40.0, 54.0]),
        np.array([45.0, 50.0]), np.array([40.0, 46.0]), np.array([35.0, 46.0]),
    ]
    ear = AntiSpoofService._eye_aspect_ratio(eye_open)
    assert ear > 0.3


def test_eye_aspect_ratio_closed():
    # 闭眼：眼宽15px，眼高2px → EAR ≈ 0.13
    eye_closed = [
        np.array([30.0, 50.0]), np.array([35.0, 51.0]), np.array([40.0, 51.0]),
        np.array([45.0, 50.0]), np.array([40.0, 49.0]), np.array([35.0, 49.0]),
    ]
    ear = AntiSpoofService._eye_aspect_ratio(eye_closed)
    assert ear < 0.2


def test_detect_blink_from_pattern():
    # 眨眼：开→闭→开  (EAR < 0.18 表示闭眼)
    pattern = [0.53, 0.50, 0.13, 0.52]
    assert AntiSpoofService._detect_blink(pattern) is True


def test_no_blink_from_stable():
    pattern = [0.53, 0.52, 0.51, 0.53]
    assert AntiSpoofService._detect_blink(pattern) is False


def test_spoof_triggered_with_no_blink():
    """长时间不眨眼应触发欺骗告警"""
    service = AntiSpoofService(blink_threshold_seconds=0.01)  # 快速触发
    face = _make_face_with_eyes("track_1", [10, 10, 100, 100], eyes_open=True)

    # 先喂几帧睁眼数据
    for _ in range(8):
        face["landmarks"] = _make_open_eye_landmarks()
        dets = service.detect("s1", [face])
        if dets:
            break

    # 过段时间应该触发
    time.sleep(0.02)
    face["landmarks"] = _make_open_eye_landmarks()
    dets = service.detect("s1", [face])
    assert len(dets) >= 1
    assert dets[0]["event_type"] == "spoof_detected"


def test_status():
    service = AntiSpoofService()
    status = service.status()
    assert status["loaded"] is True
    assert "active_tracks" in status
    assert "blink_threshold_seconds" in status
