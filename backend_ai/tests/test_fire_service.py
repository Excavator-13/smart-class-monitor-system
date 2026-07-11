from __future__ import annotations

import numpy as np

from backend_ai.services.fire_service import FireService


class FakeFireModel:
    """模拟 YOLO 火焰检测模型"""

    def __init__(self, fake_boxes: list | None = None):
        self._boxes = fake_boxes or []

    def __call__(self, frame, verbose=False):
        # 返回一个具有 .boxes 属性的对象列表
        return [self]

    @property
    def boxes(self):
        return FakeBoxes(self._boxes)


class FakeBoxes:
    def __init__(self, boxes_data: list):
        self._data = boxes_data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


class FakeBox:
    def __init__(self, xyxy: list, conf: float):
        self.xyxy = [np.array(xyxy)]
        self.conf = [conf]
        self.cls = [0]


def test_fire_service_loaded():
    """有模型时 loaded 属性为 True"""
    model = FakeFireModel()
    service = FireService(model=model)
    assert service.loaded is True


def test_fire_service_not_loaded():
    """无模型时 loaded 属性为 False"""
    service = FireService(model=None)
    assert service.loaded is False


def test_detect_returns_empty_when_no_model():
    """无模型时 detect 返回空列表"""
    service = FireService(model=None)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = service.detect("test_stream", frame)
    assert detections == []


def test_detect_finds_flame():
    """有模型且置信度超阈值时应检测到火焰"""
    fake_boxes = [
        FakeBox(xyxy=[100, 100, 300, 400], conf=0.6),
    ]
    service = FireService(model=FakeFireModel(fake_boxes), confidence_threshold=0.5)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = service.detect("test_stream", frame)

    assert len(detections) == 1
    assert detections[0]["event_type"] == "flame_detected"
    assert detections[0]["confidence"] == 0.6
    assert detections[0]["level"] == "warning"


def test_detect_filters_low_confidence():
    """低置信度的检测应被过滤"""
    fake_boxes = [
        FakeBox(xyxy=[100, 100, 300, 400], conf=0.3),
    ]
    service = FireService(model=FakeFireModel(fake_boxes), confidence_threshold=0.5)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = service.detect("test_stream", frame)

    assert len(detections) == 0


def test_detect_filters_small_area():
    """面积低于 min_bbox_area 的检测框应被过滤"""
    fake_boxes = [
        FakeBox(xyxy=[100, 100, 110, 110], conf=0.8),  # area = 100
    ]
    service = FireService(model=FakeFireModel(fake_boxes), confidence_threshold=0.5, min_bbox_area=500)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = service.detect("test_stream", frame)

    assert len(detections) == 0


def test_classify_level():
    """告警等级划分正确"""
    assert FireService._classify_level(0.9) == "high"
    assert FireService._classify_level(0.7) == "warning"
    assert FireService._classify_level(0.5) == "info"


def test_detect_sorted_by_confidence():
    """检测结果按置信度降序排列"""
    fake_boxes = [
        FakeBox(xyxy=[100, 100, 200, 200], conf=0.5),
        FakeBox(xyxy=[300, 300, 400, 400], conf=0.9),
    ]
    service = FireService(model=FakeFireModel(fake_boxes), confidence_threshold=0.4)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = service.detect("test_stream", frame)

    assert len(detections) == 2
    assert detections[0]["confidence"] == 0.9
    assert detections[1]["confidence"] == 0.5


def test_status():
    """status 方法返回正确信息"""
    service = FireService(model=None, confidence_threshold=0.3)
    status = service.status()
    assert status["loaded"] is False
    assert status["confidence_threshold"] == 0.3
