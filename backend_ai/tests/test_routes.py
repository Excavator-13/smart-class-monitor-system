import base64

import cv2
import numpy as np

from backend_ai.app import create_app
from backend_ai.services.config_client import ConfigCache
from backend_ai.services.event_service import EventService


class FakeConfigClient:
    def __init__(self):
        self.cache = ConfigCache(
            streams={"classroom_01": {"stream_id": "classroom_01", "rtmp_url": "mock://stream"}},
            rules={},
            zones_by_stream={},
            face_features={},
        )

    def get_stream(self, stream_id):
        return self.cache.streams.get(stream_id)

    def reload(self, stream_id=None, reload_items=None):
        return {"stream_id": stream_id, "streams_loaded": 1, "zones_loaded": 0, "rules_loaded": 0}

    def reload_face_features(self, scope="all", student_id=None):
        return {"loaded_count": 0}

    def get_face_features(self):
        return {}

    def get_zones(self, stream_id):
        return []

    def get_rule(self, rule_type):
        return {}


class FakeFaceService:
    loaded = True

    def extract_feature_from_base64(self, image):
        return {"face_count": 1, "feature_dim": 512, "feature_vector": [0.0] * 512, "bbox": [1, 2, 3, 4]}

    def recognize_frame(self, frame, feature_cache):
        return []


class FakeStreamManager:
    def status(self):
        return [{"stream_id": "classroom_01", "online": True, "fps": 12.5, "last_frame_at": 1}]

    def get_frame(self, stream_id):
        return np.zeros((20, 20, 3), dtype=np.uint8)


class FakeBehaviorService:
    model = None

    def detect_objects(self, frame):
        return []

    def detect_from_objects(self, stream_id, objects, rules):
        return []


class FakeZoneService:
    def detect(self, stream_id, persons, zones, rule=None):
        return []


class FakeAlertClient:
    def push_alert(self, event):
        return {"code": 0}


def app_client():
    app = create_app(
        {
            "config_client": FakeConfigClient(),
            "event_service": EventService(),
            "face_service": FakeFaceService(),
            "stream_manager": FakeStreamManager(),
            "behavior_service": FakeBehaviorService(),
            "zone_service": FakeZoneService(),
            "alert_client": FakeAlertClient(),
        }
    )
    return app.test_client()


def test_model_status_route():
    response = app_client().get("/model/status")

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["code"] == 0
    assert payload["data"]["service_status"] == "running"


def test_analysis_events_route_empty():
    response = app_client().get("/analysis/events?stream_id=classroom_01")

    payload = response.get_json()
    assert payload["data"]["items"] == []


def test_face_feature_extract_route():
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    ok, buffer = cv2.imencode(".jpg", image)
    assert ok
    encoded = base64.b64encode(buffer.tobytes()).decode("ascii")

    response = app_client().post("/face/feature/extract", json={"student_id": "2024001", "image": encoded})

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["data"]["student_id"] == "2024001"
    assert payload["data"]["feature_dim"] == 512


def test_video_feed_unknown_stream():
    response = app_client().get("/video_feed/unknown")

    payload = response.get_json()
    assert response.status_code == 404
    assert payload["code"] == 40401


def test_video_feed_known_stream_returns_mjpeg_chunk():
    response = app_client().get("/video_feed/classroom_01", buffered=False)

    first_chunk = next(response.response)
    assert response.status_code == 200
    assert response.mimetype == "multipart/x-mixed-replace"
    assert first_chunk.startswith(b"--frame")
    assert b"Content-Type: image/jpeg" in first_chunk
