from backend_ai.utils.response import envelope


def test_envelope_success_shape():
    result = envelope({"ok": True}, trace_id="req_test")

    assert result["code"] == 0
    assert result["message"] == "success"
    assert result["data"] == {"ok": True}
    assert result["trace_id"] == "req_test"
    assert "timestamp" in result


def test_envelope_error_default_message():
    result = envelope(None, code=40002, trace_id="req_test")

    assert result["message"] == "no face detected"
    assert result["data"] is None

