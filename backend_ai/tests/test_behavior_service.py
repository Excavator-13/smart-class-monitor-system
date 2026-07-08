from backend_ai.services.behavior_service import BehaviorService


def test_phone_usage_from_mock_objects():
    service = BehaviorService()
    objects = [
        {"class_name": "person", "track_id": "person_1", "bbox": [0.1, 0.1, 0.5, 0.8], "confidence": 0.9},
        {"class_name": "phone", "bbox": [0.2, 0.3, 0.25, 0.35], "confidence": 0.88},
    ]

    detections = service.detect_from_objects(
        "classroom_01",
        objects,
        {"phone_usage": {"confidence_threshold": 0.6, "threshold_seconds": 3, "cooldown_seconds": 45}},
    )

    assert detections[0]["event_type"] == "phone_usage"
    assert detections[0]["target"]["track_id"] == "person_1"


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

