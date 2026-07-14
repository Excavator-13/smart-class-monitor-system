import numpy as np

from backend_ai.services.analysis_service import AnalysisService
from backend_ai.services.event_service import EventService


class FakeFaceService:
    def recognize_frame(self, frame, feature_cache):
        return []


class FakeBehaviorService:
    loaded = False

    def __init__(self):
        self.detect_called = False

    def detect_objects(self, frame):
        self.detect_called = True
        return [{"class_name": "person", "track_id": "p1", "bbox": [10, 10, 30, 40], "confidence": 0.9}]

    def detect_from_objects(self, stream_id, objects, rules, phone_forbidden_zones=None, frame_size=(1, 1)):
        return []


class FakeZoneService:
    def detect(self, stream_id, persons, zones, rule=None, frame_size=(1, 1)):
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


def test_draw_detections_accepts_numpy_bbox():
    service = AnalysisService(
        face_service=FakeFaceService(),
        zone_service=FakeZoneService(),
        behavior_service=FakeBehaviorService(),
        event_service=EventService(),
        config_client=FakeConfigClient(),
    )
    frame = np.zeros((80, 120, 3), dtype=np.uint8)
    detections = [
        {
            "event_type": "face_recognized",
            "target": {"bbox": np.array([10, 10, 30, 40])},
        }
    ]

    service._draw_detections(frame, detections, color=(80, 220, 80))

    assert frame.sum() > 0


def test_recognized_face_label_uses_registered_student_number():
    service = AnalysisService(
        face_service=FakeFaceService(),
        zone_service=FakeZoneService(),
        behavior_service=FakeBehaviorService(),
        event_service=EventService(),
        config_client=FakeConfigClient(),
    )
    labels = []
    service._draw_bbox = lambda frame, bbox, label, color: labels.append(label)

    service._draw_detections(
        np.zeros((80, 120, 3), dtype=np.uint8),
        [{
            "event_type": "face_recognized",
            "target": {"student_id": "TEST-001", "student_name": "Test User", "bbox": [10, 10, 30, 40]},
        }],
        color=(80, 220, 80),
    )

    assert labels == ["TEST-001"]


def test_security_and_fire_detection_labels_are_visible():
    service = AnalysisService(
        face_service=FakeFaceService(),
        zone_service=FakeZoneService(),
        behavior_service=FakeBehaviorService(),
        event_service=EventService(),
        config_client=FakeConfigClient(),
    )
    labels = []
    service._draw_bbox = lambda frame, bbox, label, color: labels.append((label, color))
    frame = np.zeros((80, 120, 3), dtype=np.uint8)

    service._draw_detections(
        frame,
        [
            {"event_type": "spoof_detected", "target": {"bbox": [10, 10, 30, 40]}},
            {"event_type": "deepfake_detected", "target": {"bbox": [10, 10, 30, 40]}},
        ],
        color=(0, 0, 255),
    )
    service._draw_detections(
        frame,
        [{"event_type": "flame_detected", "target": {"bbox": [40, 10, 60, 40]}}],
        color=(0, 80, 255),
    )

    assert labels == [
        ("Spoof detected", (0, 0, 255)),
        ("Deepfake detected", (0, 0, 255)),
        ("Fire", (0, 80, 255)),
    ]


def test_alert_overlay_is_drawn_for_two_seconds_then_removed():
    service = AnalysisService(
        face_service=FakeFaceService(),
        zone_service=FakeZoneService(),
        behavior_service=FakeBehaviorService(),
        event_service=EventService(),
        config_client=FakeConfigClient(),
        alert_overlay_seconds=2,
    )
    service._add_alert_overlay(
        "classroom_01",
        {"event_id": "evt_fire", "event_type": "flame_detected"},
        now=10,
    )
    visible_frame = np.zeros((80, 240, 3), dtype=np.uint8)
    service._draw_alert_overlays(visible_frame, "classroom_01", now=11.99)

    expired_frame = np.zeros((80, 240, 3), dtype=np.uint8)
    service._draw_alert_overlays(expired_frame, "classroom_01", now=12)

    assert visible_frame.sum() > 0
    assert expired_frame.sum() == 0
    assert len(service._alert_overlays["classroom_01"]) == 0


def test_person_phone_zone_and_recognized_faces_are_visible():
    service = AnalysisService(
        face_service=FakeFaceService(),
        zone_service=FakeZoneService(),
        behavior_service=FakeBehaviorService(),
        event_service=EventService(),
        config_client=FakeConfigClient(),
    )
    frame = np.zeros((80, 120, 3), dtype=np.uint8)

    service._draw_objects(
        frame,
        [
            {"class_name": "cell phone", "bbox": [10, 10, 30, 40]},
            {"class_name": "chair", "bbox": [40, 10, 60, 40]},
        ],
    )
    service._draw_detections(
        frame,
        [
            {"event_type": "stranger_detected", "target": {"bbox": [10, 10, 30, 40]}},
            {"event_type": "head_down", "target": {"bbox": [10, 10, 30, 40]}},
            {"event_type": "danger_zone_intrusion", "target": {"bbox": [10, 10, 30, 40]}},
        ],
        color=(80, 180, 255),
    )

    assert frame.sum() > 0

    service._draw_detections(
        frame,
        [{"event_type": "phone_usage", "target": {"bbox": [10, 10, 30, 40]}}],
        color=(0, 255, 255),
    )

    assert np.any(np.all(frame == [0, 255, 255], axis=2))

    service._draw_objects(frame, [{"class_name": "person", "bbox": [10, 10, 30, 40]}])
    service._draw_detections(
        frame,
        [{"event_type": "face_recognized", "target": {"bbox": [40, 10, 60, 40]}}],
        color=(80, 220, 80),
    )

    assert frame.sum() > 0


class ConfirmingEventService:
    def __init__(self, event_type):
        self.event_type = event_type

    def observe(self, **kwargs):
        return {
            "event_id": f"evt_{self.event_type}",
            "event_type": self.event_type,
            "stream_id": kwargs["stream_id"],
            "snapshot_path": None,
        }, True

    def mark_confirmed(self, event_id):
        return None


class CapturingAlertClient:
    def __init__(self):
        self.events = []

    def push_alert(self, event, record_path=None, event_time_offset=None):
        self.events.append(dict(event))


class EventFaceService:
    def __init__(self, event_type):
        self.event_type = event_type

    def recognize_frame(self, frame, feature_cache):
        return [{
            "event_type": self.event_type,
            "confidence": 0.9,
            "target": {"track_id": "face_1", "bbox": [10, 10, 30, 40]},
        }]


def _analyze_confirmed_event(tmp_path, event_type):
    alert_client = CapturingAlertClient()
    service = AnalysisService(
        face_service=EventFaceService(event_type),
        zone_service=FakeZoneService(),
        behavior_service=FakeBehaviorService(),
        event_service=ConfirmingEventService(event_type),
        config_client=FakeConfigClient(),
        alert_client=alert_client,
        snapshot_root=tmp_path,
    )
    service.analyze_frame("classroom_01", np.zeros((80, 120, 3), dtype=np.uint8), modules={"face"})
    return alert_client.events[0]


def test_snapshot_event_types_save_snapshots(tmp_path):
    intrusion = _analyze_confirmed_event(tmp_path, "danger_zone_intrusion")
    phone = _analyze_confirmed_event(tmp_path, "phone_usage")

    assert intrusion["snapshot_path"].startswith("/snapshots/")
    assert phone["snapshot_path"].startswith("/snapshots/")
    assert len(list(tmp_path.rglob("*.jpg"))) == 2
