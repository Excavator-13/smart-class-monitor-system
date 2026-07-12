from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from flask import Flask, Response, request

from backend_ai.services.alert_client import AlertClient
from backend_ai.services.analysis_service import AnalysisService
from backend_ai.services.anti_spoof_service import AntiSpoofService
from backend_ai.services.audio_service import AudioService
from backend_ai.services.behavior_service import BehaviorService
from backend_ai.services.config_client import ConfigClient
from backend_ai.services.event_service import EventService
from backend_ai.services.face_service import FaceError, FaceService
from backend_ai.services.fire_service import FireService
from backend_ai.services.stream_manager import StreamManager
from backend_ai.services.zone_service import ZoneService
from backend_ai.utils.image_utils import blank_frame, encode_jpeg
from backend_ai.utils.response import error_response, json_response


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def create_app(overrides: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app_config = load_yaml(BASE_DIR / "config" / "app.yaml")
    model_config = load_yaml(BASE_DIR / "config" / "model.yaml")
    if overrides:
        app_config.update(overrides.get("app_config", {}))
        model_config.update(overrides.get("model_config", {}))

    spring = app_config.get("spring", {})
    spring_base_url = os.environ.get("SPRING_BASE_URL") or spring.get("base_url", "http://localhost:8080")
    stream_cfg = app_config.get("stream", {})
    events_cfg = app_config.get("events", {})

    config_client = (overrides or {}).get("config_client") if overrides else None
    config_client = config_client or ConfigClient(
        base_url=spring_base_url,
        timeout=float(spring.get("timeout_seconds", 5)),
    )
    event_service = (overrides or {}).get("event_service") if overrides else None
    event_service = event_service or EventService(
        max_items=int(events_cfg.get("max_items", 500)),
        default_cooldown_seconds=float(events_cfg.get("default_cooldown_seconds", 45)),
    )
    face_settings = (model_config.get("models") or {}).get("face", {})
    face_service = (overrides or {}).get("face_service") if overrides else None
    face_service = face_service or FaceService(
        feature_dim=int(face_settings.get("feature_dim", 512)),
        similarity_threshold=float(face_settings.get("similarity_threshold", 0.45)),
    )
    zone_service = (overrides or {}).get("zone_service") if overrides else None
    zone_service = zone_service or ZoneService()
    behavior_service = (overrides or {}).get("behavior_service") if overrides else None
    behavior_service = behavior_service or BehaviorService()

    fire_settings = (model_config.get("models") or {}).get("fire", {})
    fire_service = (overrides or {}).get("fire_service") if overrides else None
    if fire_service is None and fire_settings.get("enabled", False):
        try:
            from ultralytics import YOLO
            weights = fire_settings.get("weights", "models/yolo/yolo_fire.pt")
            fire_model = YOLO(BASE_DIR / weights if not Path(weights).is_absolute() else Path(weights))
            fire_service = FireService(
                model=fire_model,
                confidence_threshold=float(fire_settings.get("confidence_threshold", 0.25)),
                max_detections=int(fire_settings.get("max_detections", 20)),
                min_bbox_area=int(fire_settings.get("min_bbox_area", 1000)),
            )
            print(f"[Fire] 明火检测模型加载成功: {weights}")
        except Exception as exc:
            print(f"[Fire] 明火检测模型加载失败: {exc}")
            fire_service = FireService(model=None)
    elif fire_service is None:
        fire_service = FireService(model=None)

    anti_spoof_settings = (model_config.get("models") or {}).get("anti_spoof", {})
    anti_spoof_service = (overrides or {}).get("anti_spoof_service") if overrides else None
    if anti_spoof_service is None and anti_spoof_settings.get("enabled", False):
        try:
            anti_spoof_service = AntiSpoofService(
                blink_threshold_seconds=float(anti_spoof_settings.get("blink_threshold_seconds", 5.0)),
                texture_variance_threshold=float(anti_spoof_settings.get("texture_variance_threshold", 8.0)),
            )
            print("[AntiSpoof] 活体检测模块已启用")
        except Exception as exc:
            print(f"[AntiSpoof] 活体检测模块加载失败: {exc}")
            anti_spoof_service = None
    elif anti_spoof_service is None and not anti_spoof_settings.get("enabled", False):
        anti_spoof_service = None

    audio_settings = (model_config.get("models") or {}).get("audio", {})
    audio_service = (overrides or {}).get("audio_service") if overrides else None
    if audio_service is None and audio_settings.get("enabled", False):
        try:
            audio_service = AudioService(
                sample_rate=int(audio_settings.get("sample_rate", 16000)),
                window_ms=int(audio_settings.get("window_ms", 1000)),
            )
            print("[Audio] 异常声学检测模块已启用")
        except Exception as exc:
            print(f"[Audio] 异常声学检测模块加载失败: {exc}")
            audio_service = None
    elif audio_service is None and not audio_settings.get("enabled", False):
        audio_service = None

    alert_client = (overrides or {}).get("alert_client") if overrides else None
    alert_client = alert_client or AlertClient(base_url=spring_base_url)
    stream_manager = (overrides or {}).get("stream_manager") if overrides else None
    stream_manager = stream_manager or StreamManager(
        config_client=config_client,
        offline_after_seconds=float(stream_cfg.get("offline_after_seconds", 10)),
        reconnect_interval_seconds=float(stream_cfg.get("reconnect_interval_seconds", 3)),
    )
    analysis_service = AnalysisService(
        face_service=face_service,
        zone_service=zone_service,
        behavior_service=behavior_service,
        event_service=event_service,
        config_client=config_client,
        fire_service=fire_service,
        anti_spoof_service=anti_spoof_service,
        audio_service=audio_service,
        alert_client=alert_client,
    )

    app.extensions["ai_services"] = {
        "config_client": config_client,
        "event_service": event_service,
        "face_service": face_service,
        "zone_service": zone_service,
        "behavior_service": behavior_service,
        "fire_service": fire_service,
        "anti_spoof_service": anti_spoof_service,
        "audio_service": audio_service,
        "alert_client": alert_client,
        "stream_manager": stream_manager,
        "analysis_service": analysis_service,
    }

    @app.get("/model/status")
    def model_status():
        models = [
            {
                "module": "face",
                "loaded": bool(face_service.loaded),
                "model_name": "insightface",
                "version": "v1",
                "avg_infer_ms": None,
            },
            {"module": "zone", "loaded": True, "model_name": "rule", "version": "v1", "avg_infer_ms": None},
            {"module": "behavior", "loaded": behavior_service.model is not None, "model_name": "ultralytics", "version": "v1", "avg_infer_ms": None},
            {"module": "fire", "loaded": fire_service.loaded, "model_name": "ultralytics", "version": "v1", "avg_infer_ms": None},
            {"module": "anti_spoof", "loaded": anti_spoof_service is not None, "model_name": "rule", "version": "v1", "avg_infer_ms": None},
            {"module": "audio", "loaded": audio_service is not None, "model_name": "signal", "version": "v1", "avg_infer_ms": None},
        ]
        return json_response({"service_status": "running", "models": models, "streams": stream_manager.status()})

    @app.get("/analysis/events")
    def analysis_events():
        limit = request.args.get("limit", default=events_cfg.get("default_limit", 20), type=int)
        items = event_service.query(
            stream_id=request.args.get("stream_id"),
            event_type=request.args.get("event_type"),
            level=request.args.get("level"),
            limit=max(1, min(limit or 20, 200)),
            since=request.args.get("since"),
        )
        return json_response({"items": items})

    @app.post("/face/feature/extract")
    def face_feature_extract():
        body = request.get_json(silent=True) or {}
        try:
            result = face_service.extract_feature_from_base64(body.get("image", ""))
        except FaceError as exc:
            return error_response(exc.code, exc.message, status=400)
        if body.get("student_id"):
            result["student_id"] = body["student_id"]
        return json_response(result)

    @app.post("/face/features/reload")
    def face_features_reload():
        body = request.get_json(silent=True) or {}
        result = config_client.reload_face_features(scope=body.get("scope", "all"), student_id=body.get("student_id"))
        return json_response(result)

    @app.post("/config/reload")
    def config_reload():
        body = request.get_json(silent=True) or {}
        result = config_client.reload(stream_id=body.get("stream_id"), reload_items=body.get("reload_items"))
        return json_response(result)

    @app.get("/video_feed/<stream_id>")
    def video_feed(stream_id: str):
        if not config_client.get_stream(stream_id):
            return error_response(40401, "stream not found", status=404)
        annotate = request.args.get("annotate", "true").lower() != "false"
        modules_param = request.args.get("modules", "all")
        modules = {"face", "zone", "behavior", "fire", "anti_spoof", "audio"} if modules_param == "all" else {m.strip() for m in modules_param.split(",") if m.strip()}

        def generate():
            while True:
                frame = stream_manager.get_frame(stream_id)
                if frame is None:
                    frame = blank_frame(text="stream offline")
                elif annotate:
                    analysis_service.analyze_frame(stream_id, frame, modules=modules)
                try:
                    payload = encode_jpeg(frame)
                except ValueError:
                    payload = encode_jpeg(blank_frame(text="jpeg encode failed"))
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + payload + b"\r\n"

        return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

    return app


app = create_app()


if __name__ == "__main__":
    cfg = load_yaml(BASE_DIR / "config" / "app.yaml").get("service", {})
    app.run(host=cfg.get("host", "0.0.0.0"), port=int(cfg.get("port", 5000)), debug=bool(cfg.get("debug", False)))