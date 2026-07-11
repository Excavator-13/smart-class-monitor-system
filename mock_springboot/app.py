from __future__ import annotations

import json
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from flask import Flask, jsonify, request

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def _replace_env_vars(obj, env: dict):
    if isinstance(obj, str):
        for key, val in env.items():
            obj = obj.replace(f"${{{key}}}", val)
        return obj
    if isinstance(obj, dict):
        return {k: _replace_env_vars(v, env) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_replace_env_vars(item, env) for item in obj]
    return obj


def load_mock_data() -> dict:
    path = BASE_DIR / "mock_data.yaml"
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    return _replace_env_vars(raw, dict(os.environ))


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
    host = os.environ.get("MOCK_HOST", "0.0.0.0")
    port = int(os.environ.get("MOCK_PORT", "8080"))
    debug = os.environ.get("MOCK_DEBUG", "true").lower() in ("true", "1", "yes")
    app.run(host=host, port=port, debug=debug)