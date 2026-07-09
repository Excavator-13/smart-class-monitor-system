from __future__ import annotations

import json
from pathlib import Path

import yaml
from flask import Flask, jsonify, request

BASE_DIR = Path(__file__).resolve().parent


def load_mock_data() -> dict:
    path = BASE_DIR / "mock_data.yaml"
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def create_app() -> Flask:
    app = Flask(__name__)
    data = load_mock_data()

    @app.get("/streams")
    def streams():
        return jsonify({"code": 0, "data": {"items": data.get("streams", [])}})

    @app.get("/zones")
    def zones():
        stream_id = request.args.get("stream_id")
        items = data.get("zones", [])
        if stream_id:
            items = [z for z in items if z.get("stream_id") == stream_id]
        return jsonify({"code": 0, "data": {"items": items}})

    @app.get("/rules")
    def rules():
        return jsonify({"code": 0, "data": {"items": data.get("rules", [])}})

    @app.get("/students/face-features")
    def face_features():
        return jsonify({"code": 0, "data": {"items": []}})

    @app.post("/alerts/ai")
    def alert():
        payload = request.get_json(silent=True) or {}
        print(f"[MockSpring] 收到告警: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        return jsonify({"code": 0, "message": "ok"})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=True)