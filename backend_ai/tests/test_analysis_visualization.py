import numpy as np

from backend_ai.services.analysis_service import AnalysisService
from backend_ai.services.event_service import EventService


class FakeFaceService:
    def recognize_frame(self, frame, feature_cache):
        return []


class FakeBehaviorService:
    def __init__(self):
        self.detect_called = False

    def detect_objects(self, frame):
        self.detect_called = True
        return [{"class_name": "person", "track_id": "p1", "bbox": [10, 10, 30, 40], "confidence": 0.9}]

    def detect_from_objects(self, stream_id, objects, rules):
        return []


class FakeZoneService:
    def detect(self, stream_id, persons, zones, rule=None):
        return []


class FakeConfigClient:
    class Cache:
        rules = {}

    cache = Cache()

    def get_face_features(self):
        return {}

    def get_zones(self, stream_id):
        return []

    def get_rule(self, rule_type):
        return {}


def test_zone_only_analysis_detects_objects_and_draws_missing_zone_status():
    behavior_service = FakeBehaviorService()
    service = AnalysisService(
        face_service=FakeFaceService(),
        zone_service=FakeZoneService(),
        behavior_service=behavior_service,
        event_service=EventService(),
        config_client=FakeConfigClient(),
    )
    frame = np.zeros((80, 120, 3), dtype=np.uint8)

    service.analyze_frame("classroom_01", frame, modules={"zone"})

    assert behavior_service.detect_called
    assert frame.sum() > 0
