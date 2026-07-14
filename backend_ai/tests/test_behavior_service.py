from backend_ai.services.behavior_service import BehaviorService


class FakeYoloModel:
    def __init__(self):
        self.predict_kwargs = None

    def predict(self, frame, conf=0.6, verbose=False, **kwargs):
        self.predict_kwargs = {"conf": conf, "verbose": verbose, **kwargs}
        class Box:
            cls = [67]
            conf = [0.91]
            xyxy = [[10, 20, 30, 40]]

        class Result:
            names = {67: "cell phone"}
            boxes = [Box()]

        return [Result()]


def test_behavior_model_missing_weights_sets_status(tmp_path):
    service = BehaviorService()

    service.load_model({"enabled": True, "weights": "models/yolo/missing.pt"}, tmp_path)

    assert service.loaded is False
    assert service.model is None
    assert "weights not found" in service.last_error


def test_detect_objects_uses_yolo_predict_api():
    service = BehaviorService(model=FakeYoloModel(), confidence_threshold=0.7)

    detections = service.detect_objects(frame=object())

    assert detections == [{"class_name": "cell phone", "confidence": 0.91, "bbox": [10.0, 20.0, 30.0, 40.0]}]


def test_detect_objects_passes_cuda_device_to_yolo():
    model = FakeYoloModel()
    service = BehaviorService(model=model, confidence_threshold=0.7, device="cuda")

    service.detect_objects(frame=object())

    assert model.predict_kwargs["device"] == "cuda"


def test_phone_usage_from_mock_objects():
    service = BehaviorService()
    objects = [
        {"class_name": "person", "track_id": "person_1", "bbox": [0.1, 0.1, 0.5, 0.8], "confidence": 0.9},
        {"class_name": "phone", "bbox": [0.2, 0.3, 0.25, 0.35], "confidence": 0.88},
    ]
    phone_forbidden_zones = [
        {
            "zone_id": 1,
            "zone_name": "手机禁用区",
            "zone_type": "phone_forbidden",
            "coordinates": [{"x": 0.1, "y": 0.1}, {"x": 0.5, "y": 0.1}, {"x": 0.5, "y": 0.5}, {"x": 0.1, "y": 0.5}],
        }
    ]

    detections = service.detect_from_objects(
        "classroom_01",
        objects,
        {"phone_usage": {"confidence_threshold": 0.6, "threshold_seconds": 3, "cooldown_seconds": 45}},
        phone_forbidden_zones=phone_forbidden_zones,
    )

    assert len(detections) == 1
    assert detections[0]["event_type"] == "phone_usage"
    assert detections[0]["target"]["track_id"] == "person_1"
    assert detections[0]["zone"]["zone_id"] == 1
    assert detections[0]["zone"]["zone_type"] == "phone_forbidden"
    assert ":1:phone" in detections[0]["track_key"]


def test_phone_usage_outside_forbidden_zone_not_detected():
    service = BehaviorService()
    objects = [
        {"class_name": "person", "track_id": "person_1", "bbox": [0.6, 0.6, 0.9, 0.9], "confidence": 0.9},
        {"class_name": "phone", "bbox": [0.7, 0.7, 0.75, 0.75], "confidence": 0.88},
    ]
    phone_forbidden_zones = [
        {
            "zone_id": 1,
            "zone_name": "手机禁用区",
            "zone_type": "phone_forbidden",
            "coordinates": [{"x": 0.0, "y": 0.0}, {"x": 0.3, "y": 0.0}, {"x": 0.3, "y": 0.3}, {"x": 0.0, "y": 0.3}],
        }
    ]

    detections = service.detect_from_objects(
        "classroom_01",
        objects,
        {"phone_usage": {"confidence_threshold": 0.6, "threshold_seconds": 3, "cooldown_seconds": 45}},
        phone_forbidden_zones=phone_forbidden_zones,
    )

    phone_events = [d for d in detections if d["event_type"] == "phone_usage"]
    assert len(phone_events) == 0


def test_phone_usage_no_forbidden_zones_skips_detection():
    service = BehaviorService()
    objects = [
        {"class_name": "person", "track_id": "person_1", "bbox": [0.1, 0.1, 0.5, 0.8], "confidence": 0.9},
        {"class_name": "phone", "bbox": [0.2, 0.3, 0.25, 0.35], "confidence": 0.88},
    ]

    detections = service.detect_from_objects(
        "classroom_01",
        objects,
        {"phone_usage": {"confidence_threshold": 0.6, "threshold_seconds": 3, "cooldown_seconds": 45}},
        phone_forbidden_zones=None,
    )

    phone_events = [d for d in detections if d["event_type"] == "phone_usage"]
    assert len(phone_events) == 0


def test_phone_usage_empty_forbidden_zones_skips_detection():
    service = BehaviorService()
    objects = [
        {"class_name": "person", "track_id": "person_1", "bbox": [0.1, 0.1, 0.5, 0.8], "confidence": 0.9},
        {"class_name": "phone", "bbox": [0.2, 0.3, 0.25, 0.35], "confidence": 0.88},
    ]

    detections = service.detect_from_objects(
        "classroom_01",
        objects,
        {"phone_usage": {"confidence_threshold": 0.6, "threshold_seconds": 3, "cooldown_seconds": 45}},
        phone_forbidden_zones=[],
    )

    phone_events = [d for d in detections if d["event_type"] == "phone_usage"]
    assert len(phone_events) == 0


def test_head_down_from_mock_person_ratio():
    service = BehaviorService()
    objects = [
        {"class_name": "person", "track_id": "person_1", "bbox": [0.1, 0.1, 0.5, 0.8], "head_down_ratio": 0.7}
    ]

    detections = service.detect_from_objects("classroom_01", objects, {"head_down": {"confidence_threshold": 0.6}})

    assert detections[0]["event_type"] == "head_down"


def test_crowd_gathering_from_mock_person_density():
    service = BehaviorService()
    objects = [
        {"class_name": "person", "bbox": [0.10, 0.1, 0.12, 0.2]},
        {"class_name": "person", "bbox": [0.11, 0.1, 0.13, 0.2]},
        {"class_name": "person", "bbox": [0.12, 0.1, 0.14, 0.2]},
        {"class_name": "person", "bbox": [0.13, 0.1, 0.15, 0.2]},
    ]

    detections = service.detect_from_objects(
        "classroom_01",
        objects,
        {"crowd_gathering": {"config_json": {"min_count": 4, "max_center_distance": 0.1}}},
    )

    assert detections[0]["event_type"] == "crowd_gathering"