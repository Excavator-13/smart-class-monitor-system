from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
import yaml
from dotenv import load_dotenv
from flask import Flask, Response, request

from backend_ai.services.alert_client import AlertClient
from backend_ai.services.dingtalk_service import start_stream, trigger_alert
from backend_ai.services.analysis_service import AnalysisService
from backend_ai.services.anti_spoof_service import AntiSpoofService
from backend_ai.services.audio_service import AudioService
from backend_ai.services.behavior_service import BehaviorService
from backend_ai.services.config_client import ConfigClient
from backend_ai.services.event_service import EVENT_NAMES, EventService
from backend_ai.services.face_service import FaceError, FaceService
from backend_ai.services.fire_service import FireService
from backend_ai.utils import resolve_device
from backend_ai.services.snapshot_push import SnapshotPusher
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


def _restore_dingtalk_settings(spring_base_url: str, internal_token: str | None):
    try:
        headers = {"X-Internal-Token": internal_token} if internal_token else None
        resp = requests.get(f"{spring_base_url}/api/settings", headers=headers, timeout=5)
        if not resp.ok:
            return
        data = resp.json()
        from backend_ai.services import dingtalk_service as ds
        contacts = data.get("contacts", [])
        new_persons = {}
        for c in contacts:
            name = c.get("name", "")
            mobile = c.get("mobile", "")
            if name and mobile:
                new_persons[name] = {"name": name, "mobile": mobile}
        if new_persons:
            ds.PERSONS.clear()
            ds.PERSONS.update(new_persons)
        responsible = data.get("responsible", "")
        if responsible:
            ds.PRIMARY = responsible
        interval = data.get("alertInterval")
        if interval:
            ds.STEP_TIMEOUT = int(interval)
        print(f"[DingTalk] 从 Spring Boot 恢复设置: {len(new_persons)} 联系人, 责任人={responsible}")
    except Exception:
        print("[DingTalk] 从 Spring Boot 恢复设置失败，使用默认值")


def create_app(overrides: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)

    @app.after_request
    def add_cors_headers(response: Response) -> Response:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    @app.before_request
    def handle_preflight() -> Response | None:
        if request.method == "OPTIONS":
            return Response(status=204)

    app_config = load_yaml(BASE_DIR / "config" / "app.yaml")
    model_config = load_yaml(BASE_DIR / "config" / "model.yaml")
    if overrides:
        app_config.update(overrides.get("app_config", {}))
        model_config.update(overrides.get("model_config", {}))

    spring = app_config.get("spring", {})
    spring_base_url = os.environ.get("SPRING_BASE_URL") or spring.get("base_url", "http://localhost:8080")
    internal_token = os.environ.get("INTERNAL_TOKEN") or spring.get("internal_token")
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
        default_cooldown_seconds=float(events_cfg.get("default_cooldown_seconds", 10)),
        continuity_gap_seconds=float(events_cfg.get("continuity_gap_seconds", 2)),
    )
    device_config = resolve_device(model_config.get("device"))
    face_settings = (model_config.get("models") or {}).get("face", {})
    face_service = (overrides or {}).get("face_service") if overrides else None
    face_service = face_service or FaceService(
        feature_dim=int(face_settings.get("feature_dim", 512)),
        similarity_threshold=float(face_settings.get("similarity_threshold", 0.45)),
        model_name=str(face_settings.get("name", "buffalo_l")),
        providers=list(face_settings.get("providers") or ["CUDAExecutionProvider"]),
        det_size=tuple(face_settings.get("det_size") or [640, 640]),
        ctx_id=int(face_settings.get("ctx_id", 0)),
        device=device_config,
    )
    if not (overrides or {}).get("face_service"):
        face_service.load_model(face_settings)
        if face_service.loaded:
            print(f"[Face] InsightFace 模型加载成功: {face_service.model_name}, providers={face_service.providers}, ctx_id={face_service.ctx_id}")
        else:
            print(f"[Face] InsightFace 模型加载失败: {face_service.model_name}, error={face_service.last_error}")
    zone_service = (overrides or {}).get("zone_service") if overrides else None
    zone_service = zone_service or ZoneService()
    behavior_service = (overrides or {}).get("behavior_service") if overrides else None
    behavior_settings = model_settings.get("behavior", {})
    behavior_service = behavior_service or BehaviorService(
        confidence_threshold=float(behavior_settings.get("confidence_threshold", 0.6)),
        device=device_config,
    )
    if not (overrides or {}).get("behavior_service"):
        behavior_service.load_model(behavior_settings, BASE_DIR)
        if behavior_service.loaded:
            print(f"[Behavior] YOLOv8 模型加载成功: {behavior_service.weights_path}, device={device_config}")
        else:
            print(f"[Behavior] YOLOv8 模型加载失败: {behavior_service.last_error}")

    fire_settings = (model_config.get("models") or {}).get("fire", {})
    fire_service = (overrides or {}).get("fire_service") if overrides else None
    if fire_service is None and fire_settings.get("enabled", False):
        try:
            from ultralytics import YOLO
            weights = fire_settings.get("weights", "models/yolo/yolo_fire.pt")
            fire_model = YOLO(BASE_DIR / weights if not Path(weights).is_absolute() else Path(weights))
            if device_config:
                fire_model.to(device_config)
            fire_service = FireService(
                model=fire_model,
                confidence_threshold=float(fire_settings.get("confidence_threshold", 0.25)),
                max_detections=int(fire_settings.get("max_detections", 20)),
                min_bbox_area=int(fire_settings.get("min_bbox_area", 1000)),
                device=device_config,
            )
            print(f"[Fire] 明火检测模型加载成功: {weights}, device={device_config}")
        except Exception as exc:
            print(f"[Fire] 明火检测模型加载失败: {exc}")
            fire_service = FireService(model=None)
    elif fire_service is None:
        fire_service = FireService(model=None)

    anti_spoof_settings = (model_config.get("models") or {}).get("anti_spoof", {})
    anti_spoof_service = (overrides or {}).get("anti_spoof_service") if overrides else None
    if anti_spoof_service is None and anti_spoof_settings.get("enabled", False):
        try:
            deepfake_detector = None
            deepfake_weights = str(anti_spoof_settings.get("deepfake_weights") or "").strip()
            if deepfake_weights:
                from backend_ai.services.deepfake_detector import DeepfakeDetector

                weights_path = Path(deepfake_weights)
                if not weights_path.is_absolute():
                    weights_path = BASE_DIR / weights_path
                deepfake_detector = DeepfakeDetector(str(weights_path))
                if deepfake_detector.loaded:
                    print(f"[AntiSpoof] MesoNet CNN loaded: {weights_path}, device={deepfake_detector.device}")
                else:
                    print(f"[AntiSpoof] MesoNet CNN weights not loaded: {weights_path}; using rule fallback")
            anti_spoof_service = AntiSpoofService(
                blink_threshold_seconds=float(anti_spoof_settings.get("blink_threshold_seconds", 5.0)),
                texture_variance_threshold=float(anti_spoof_settings.get("texture_variance_threshold", 8.0)),
                deepfake_detector=deepfake_detector,
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

    snapshot_root = BASE_DIR / "static" / "snapshots"

    snapshot_remote = app_config.get("snapshot_remote", {})
    remote_host = os.environ.get("SNAPSHOT_REMOTE_HOST") or snapshot_remote.get("host", "")
    nginx_base_url = ""
    if remote_host:
        nginx_port = os.environ.get("SNAPSHOT_NGINX_PORT", "9092")
        nginx_base_url = f"http://{remote_host}:{nginx_port}"
    remote_user = os.environ.get("SNAPSHOT_REMOTE_USER") or snapshot_remote.get("user", "root")
    remote_path = os.environ.get("SNAPSHOT_REMOTE_PATH") or snapshot_remote.get("path", "/data/snapshots")
    snapshot_pusher = SnapshotPusher(host=remote_host, user=remote_user, remote_path=remote_path)

    alert_client = (overrides or {}).get("alert_client") if overrides else None
    alert_client = alert_client or AlertClient(base_url=spring_base_url, internal_token=internal_token, dingtalk=trigger_alert, snapshot_root=snapshot_root, nginx_base_url=nginx_base_url)
    _restore_dingtalk_settings(spring_base_url, internal_token)
    start_stream()  # 启动钉钉 Stream 监听
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
        snapshot_root=snapshot_root,
        snapshot_pusher=snapshot_pusher,
        alert_cooldown_seconds=float(events_cfg.get("default_cooldown_seconds", 10)),
        alert_overlay_seconds=float(events_cfg.get("alert_overlay_seconds", 2)),
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
            {"module": "zone", "loaded": True, "model_name": "rule", "version": "v1", "avg_infer_ms": None},
            {"module": "behavior", "loaded": behavior_service.model is not None, "model_name": "ultralytics", "version": "v1", "avg_infer_ms": None},
            {"module": "fire", "loaded": fire_service.loaded, "model_name": "ultralytics", "version": "v1", "avg_infer_ms": analysis_service.avg_latency_ms("fire")},
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

    @app.get("/analysis/summary/<stream_id>")
    def analysis_summary(stream_id: str):
        events = event_service.query(stream_id=stream_id, limit=200)
        counts: dict[str, int] = {}
        for event in events:
            et = event.get("event_type", "unknown")
            counts[et] = counts.get(et, 0) + 1
        high_types = {"danger_zone_stay", "stream_offline", "fall_detected", "flame_detected"}
        warning_types = {"stranger_detected", "danger_zone_intrusion", "danger_zone_approach", "phone_usage", "head_down", "crowd_gathering"}
        risk_score = min(100, sum(counts.get(t, 0) * 25 for t in high_types) + sum(counts.get(t, 0) * 12 for t in warning_types))
        risk_level = "high" if risk_score >= 70 else "warning" if risk_score >= 30 else "low"
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
        summary = "，".join(parts) + "。"
        suggestion = "建议教师优先关注高风险告警并核对实时画面。" if risk_level != "low" else "建议保持巡检，持续观察课堂状态。"
        recent = events[:5]
        timeline = [
            {"time": e.get("occurred_at", "")[11:16], "text": f"{EVENT_NAMES.get(e.get('event_type', ''), e.get('event_type', ''))} 置信度 {e.get('confidence', 0):.0%}"}
            for e in recent
        ]
        return json_response({
            "stream_id": stream_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "title": "当前风险指数低" if risk_level == "low" else "当前风险指数中高" if risk_level == "warning" else "当前风险指数高",
            "summary": summary,
            "actions": ["自动抓拍", "等待人工确认", "保留追踪记录"] if risk_level != "low" else ["持续监控"],
            "counts": counts,
            "stream_status": stream_status,
            "suggestion": suggestion,
            "timeline": timeline,
        })

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
        modules = {"face", "zone", "behavior", "fire", "anti_spoof", "audio"} if modules_param == "all" else {m.strip() for m in modules_param.split(",") if m.strip()}

        def generate():
            while True:
                frame = stream_manager.get_frame(stream_id)
                if frame is None:
                    if stream_manager.should_emit_offline_alert(stream_id):
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

    @app.post("/api/contacts/sync")
    def contacts_sync():
        body = request.get_json(silent=True) or {}
        contacts = body.get("contacts", [])
        new_persons = {}
        for c in contacts:
            if c.get("name") and c.get("mobile"):
                new_persons[c["name"]] = {"name": c["name"], "mobile": c["mobile"]}
        from backend_ai.services import dingtalk_service as ds
        ds.PERSONS = new_persons
        r = body.get("responsible", "")
        if r: ds.PRIMARY = r
        i = body.get("alertInterval")
        if i: ds.STEP_TIMEOUT = int(i)
        return json_response({"ok": True, "count": len(new_persons)})

    return app


app = create_app()


if __name__ == "__main__":
    cfg = load_yaml(BASE_DIR / "config" / "app.yaml").get("service", {})
    app.run(host=cfg.get("host", "0.0.0.0"), port=int(cfg.get("port", 5000)), debug=bool(cfg.get("debug", False)))