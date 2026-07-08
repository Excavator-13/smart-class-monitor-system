from backend_ai.services.alert_client import AlertClient


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"code": 0, "data": {"alert_id": 1}}


class FakeSession:
    def __init__(self):
        self.payload = None

    def post(self, url, json=None, timeout=None):
        self.payload = json
        return FakeResponse()


def test_map_event_to_alert_payload():
    client = AlertClient(base_url="http://spring")
    event = {
        "event_id": "evt_1",
        "stream_id": "classroom_01",
        "event_type": "phone_usage",
        "event_name": "使用手机",
        "level": "warning",
        "confidence": 0.86,
        "occurred_at": "2026-07-08T10:00:00+08:00",
        "duration_seconds": 3.2,
        "target": {"student_id": "2024001", "track_id": "person_1", "bbox": [1, 2, 3, 4]},
        "zone": {"zone_id": 7},
        "snapshot_path": "/snapshots/a.jpg",
    }

    payload = client.map_event_to_alert(event)

    assert payload["alert_type"] == "phone_usage"
    assert payload["alert_name"] == "使用手机"
    assert payload["student_id"] == "2024001"
    assert payload["target_info"] == {"track_id": "person_1", "bbox": [1, 2, 3, 4]}
    assert payload["zone_id"] == 7


def test_push_alert_posts_to_springboot():
    session = FakeSession()
    client = AlertClient(base_url="http://spring", session=session)
    event = {"event_id": "evt_1", "stream_id": "classroom_01", "event_type": "head_down"}

    result = client.push_alert(event)

    assert result["code"] == 0
    assert session.payload["alert_type"] == "head_down"

