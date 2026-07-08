from backend_ai.services.config_client import ConfigClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self):
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        if url.endswith("/streams"):
            return FakeResponse({"data": {"items": [{"stream_id": "classroom_01", "rtmp_url": "rtmp://x", "status": "enabled"}]}})
        if url.endswith("/zones"):
            return FakeResponse({"data": [{"zone_id": 1, "stream_id": params["stream_id"], "enabled": True}]})
        if url.endswith("/rules"):
            return FakeResponse({"data": [{"rule_type": "phone_usage", "enabled": True, "threshold_seconds": 3}]})
        if url.endswith("/students/face-features"):
            return FakeResponse({"data": [{"student_id": "2024001", "feature_vector": [0.1], "enabled": True}]})
        return FakeResponse({})


def test_reload_streams_zones_and_rules():
    client = ConfigClient(base_url="http://spring", session=FakeSession())

    result = client.reload(stream_id="classroom_01", reload_items=["streams", "zones", "rules"])

    assert result["streams_loaded"] == 1
    assert result["zones_loaded"] == 1
    assert result["rules_loaded"] == 1
    assert client.get_stream("classroom_01")["rtmp_url"] == "rtmp://x"
    assert client.get_rule("phone_usage")["threshold_seconds"] == 3


def test_reload_face_features():
    client = ConfigClient(base_url="http://spring", session=FakeSession())

    result = client.reload_face_features()

    assert result["loaded_count"] == 1
    assert "2024001" in client.get_face_features()

