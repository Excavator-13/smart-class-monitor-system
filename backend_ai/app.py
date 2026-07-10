from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from flask import Flask, Response, request

from backend_ai.services.alert_client import AlertClient
from backend_ai.services.analysis_service import AnalysisService
from backend_ai.services.behavior_service import BehaviorService
from backend_ai.services.config_client import ConfigClient
from backend_ai.services.event_service import EventService
from backend_ai.services.face_service import FaceError, FaceService
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
    internal_token = os.environ.get("AI_INTERNAL_TOKEN") or spring.get("internal_token")
    stream_cfg = app_config.get("stream", {})
    events_cfg = app_config.get("events", {})
    cache_cfg = app_config.get("cache", {})
    model_settings = model_config.get("models") or {}

    config_client = (overrides or {}).get("config_client") if overrides else None
    config_client = config_client or ConfigClient(
        base_url=spring_base_url,
        timeout=float(spring.get("timeout_seconds", 5)),
        internal_token=internal_token,
    )
    event_service = (overrides or {}).get("event_service") if overrides else None
    event_service = event_service or EventService(
        max_items=int(events_cfg.get("max_items", 500)),
        default_cooldown_seconds=float(events_cfg.get("default_cooldown_seconds", 45)),
    )
    face_settings = model_settings.get("face", {})
    face_service = (overrides or {}).get("face_service") if overrides else None
    face_service = face_service or FaceService(
        feature_dim=int(face_settings.get("feature_dim", 512)),
        similarity_threshold=float(face_settings.get("similarity_threshold", 0.45)),
        model_name=str(face_settings.get("name", "buffalo_l")),
        providers=list(face_settings.get("providers") or ["CUDAExecutionProvider"]),
        det_size=tuple(face_settings.get("det_size") or [640, 640]),
        ctx_id=int(face_settings.get("ctx_id", 0)),
    )
    if not (overrides or {}).get("face_service"):
        face_service.load_model(face_settings)
    zone_service = (overrides or {}).get("zone_service") if overrides else None
    zone_service = zone_service or ZoneService()
    behavior_service = (overrides or {}).get("behavior_service") if overrides else None
    behavior_settings = model_settings.get("behavior", {})
    behavior_service = behavior_service or BehaviorService(
        confidence_threshold=float(behavior_settings.get("confidence_threshold", 0.6))
    )
    if not (overrides or {}).get("behavior_service"):
        behavior_service.load_model(behavior_settings, BASE_DIR)
    alert_client = (overrides or {}).get("alert_client") if overrides else None
    alert_client = alert_client or AlertClient(base_url=spring_base_url, internal_token=internal_token)
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
        alert_client=alert_client,
        snapshot_root=BASE_DIR / "static" / "snapshots",
    )

    app.extensions["ai_services"] = {
        "config_client": config_client,
        "event_service": event_service,
        "face_service": face_service,
        "zone_service": zone_service,
        "behavior_service": behavior_service,
        "alert_client": alert_client,
        "stream_manager": stream_manager,
        "analysis_service": analysis_service,
    }

    if not overrides:
        config_client.bootstrap()
        config_client.start_polling(cache_cfg)

    @app.get("/model/status")
    def model_status():
        models = [
            {
                "module": "face",
                "loaded": bool(face_service.loaded),
                "model_name": getattr(face_service, "model_name", "insightface"),
                "version": getattr(face_service, "model_version", "v1"),
                "providers": getattr(face_service, "providers", None),
                "avg_infer_ms": analysis_service.avg_latency_ms("face"),
                "last_error": getattr(face_service, "last_error", None),
            },
            {"module": "zone", "loaded": True, "model_name": "rule", "version": "v1", "avg_infer_ms": analysis_service.avg_latency_ms("zone")},
            {
                "module": "behavior",
                "loaded": bool(getattr(behavior_service, "loaded", behavior_service.model is not None)),
                "model_name": getattr(behavior_service, "model_name", "ultralytics"),
                "version": getattr(behavior_service, "model_version", "v1"),
                "weights_path": getattr(behavior_service, "weights_path", None),
                "avg_infer_ms": analysis_service.avg_latency_ms("behavior"),
                "last_error": getattr(behavior_service, "last_error", None),
            },
            {"module": "fire", "loaded": False, "model_name": "reserved", "version": "not_in_scope", "avg_infer_ms": None},
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

    @app.get("/analysis/summary/<stream_id>")
    def analysis_summary(stream_id: str):
        counts = event_service.counts(stream_id=stream_id)
        high_types = {"danger_zone_stay", "stream_offline", "fall_detected", "flame_detected"}
        warning_types = {"stranger_detected", "danger_zone_intrusion", "danger_zone_approach", "phone_usage", "head_down", "crowd_gathering"}
        risk_score = min(100, sum(counts.get(t, 0) * 25 for t in high_types) + sum(counts.get(t, 0) * 12 for t in warning_types))
        risk_level = "high" if risk_score >= 70 else "warning" if risk_score >= 30 else "normal"
        stream_status = next((item for item in stream_manager.status() if item.get("stream_id") == stream_id), None)
        parts = []
        if counts.get("phone_usage"):
            parts.append(f"检测到 {counts['phone_usage']} 起使用手机行为")
        if counts.get("danger_zone_intrusion") or counts.get("danger_zone_stay"):
            parts.append("危险区域存在人员异常")
        if counts.get("stream_offline"):
            parts.append("视频流存在中断")
        if not parts:
            parts.append("当前未检测到明显异常")
        suggestion = "建议教师优先关注高风险告警并核对实时画面。" if risk_level != "normal" else "建议保持巡检，持续观察课堂状态。"
        return json_response(
            {
                "stream_id": stream_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "summary": "，".join(parts) + "。",
                "counts": counts,
                "stream_status": stream_status,
                "suggestion": suggestion,
            }
        )

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
            try:
                config_client.reload(stream_id=stream_id, reload_items=["streams", "zones", "rules"])
            except Exception:
                pass
        if not config_client.get_stream(stream_id):
            return error_response(40401, "stream not found", status=404)
        annotate = request.args.get("annotate", "true").lower() != "false"
        modules_param = request.args.get("modules", "all")
        modules = {"face", "zone", "behavior"} if modules_param == "all" else {m.strip() for m in modules_param.split(",") if m.strip()}

        def generate():
            while True:
                frame = stream_manager.get_frame(stream_id)
                if frame is None:
                    analysis_service.observe_stream_offline(stream_id)
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
