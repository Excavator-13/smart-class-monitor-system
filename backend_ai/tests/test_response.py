import numpy as np
from flask import Flask

from backend_ai.utils.response import envelope, json_response


def test_json_response_converts_numpy_values():
    app = Flask(__name__)
    with app.app_context():
        response, status = json_response({"bbox": np.array([1, 2]), "confidence": np.float32(0.5)})

    assert status == 200
    assert response.get_json()["data"]["bbox"] == [1, 2]


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

