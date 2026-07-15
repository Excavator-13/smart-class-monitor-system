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

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append((url, params, timeout, headers))
        if url.endswith("/streams"):
            return FakeResponse({"data": {"items": [{"stream_id": "classroom_01", "rtmp_url": "rtmp://x", "status": "enabled"}]}})
        if url.endswith("/zones"):
            return FakeResponse({"data": [{"zone_id": 1, "stream_id": params.get("streamId", params.get("stream_id")), "enabled": True}]})
        if url.endswith("/rules"):
            return FakeResponse({"data": [{"rule_type": "phone_usage", "enabled": True, "threshold_seconds": 3}]})
        if url.endswith("/score-config"):
            return FakeResponse({"data": [{"alert_type": "phone_usage", "level": "info", "score": 62}]})
        if url.endswith("/students/face-features"):
            return FakeResponse({"data": [{"student_id": "2024001", "feature_vector": [0.1], "enabled": True}]})
        return FakeResponse({})


class RulesWithDisabledSession(FakeSession):
    def get(self, url, params=None, headers=None, timeout=None):
        if url.endswith("/rules"):
            return FakeResponse({"data": [
                {"rule_type": "danger_zone", "enabled": True},
                {"rule_type": "deepfake_detected", "enabled": False},
            ]})
        return super().get(url, params=params, headers=headers, timeout=timeout)


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


def test_load_event_configs_and_resolve_level():
    client = ConfigClient(base_url="http://spring", session=FakeSession())

    assert client.load_event_configs() == 1
    assert client.get_event_level("phone_usage", "warning") == "info"
    assert client.get_event_level("unknown", "high") == "high"


def test_internal_token_header_is_sent():
    session = FakeSession()
    client = ConfigClient(base_url="http://spring", session=session, internal_token="secret")

    client.load_streams()

    assert session.calls[0][3] == {"X-Internal-Token": "secret"}


def test_disabled_rules_are_not_exposed_to_detection_services():
    client = ConfigClient(base_url="http://spring", session=RulesWithDisabledSession())

    client.load_rules()

    assert client.get_rule("danger_zone")["enabled"] is True
    assert client.get_rule("deepfake_detected") == {}
