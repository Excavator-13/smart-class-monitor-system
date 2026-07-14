from backend_ai.services.zone_service import ZoneService


def test_zone_intrusion_and_stay_detection():
    service = ZoneService()
    persons = [{"track_id": "person_1", "bbox": [0.2, 0.1, 0.3, 0.3]}]
    zones = [
        {
            "zone_id": 1,
            "zone_name": "danger",
            "zone_type": "danger",
            "coordinates": [{"x": 0.1, "y": 0.1}, {"x": 0.5, "y": 0.1}, {"x": 0.5, "y": 0.5}, {"x": 0.1, "y": 0.5}],
            "threshold_seconds": 2,
        }
    ]

    detections = service.detect("classroom_01", persons, zones)
    event_types = {item["event_type"] for item in detections}

    assert "danger_zone_intrusion" in event_types
    assert "danger_zone_stay" in event_types
    assert detections[0]["zone"]["zone_id"] == 1


def test_zone_approach_does_not_mark_intrusion():
    service = ZoneService()
    persons = [{"track_id": "person_1", "bbox": [0.51, 0.1, 0.53, 0.3]}]
    zones = [
        {
            "zone_id": 1,
            "zone_name": "danger",
            "zone_type": "danger",
            "coordinates": [{"x": 0.1, "y": 0.1}, {"x": 0.5, "y": 0.1}, {"x": 0.5, "y": 0.5}, {"x": 0.1, "y": 0.5}],
        }
    ]

    detections = service.detect("classroom_01", persons, zones, {"config_json": {"safe_distance": 0.05}})
    event_types = {item["event_type"] for item in detections}

    assert "danger_zone_approach" in event_types
    assert "danger_zone_intrusion" not in event_types


def test_phone_forbidden_zone_does_not_trigger_intrusion():
    service = ZoneService()
    persons = [{"track_id": "person_1", "bbox": [0.2, 0.1, 0.3, 0.3]}]
    zones = [
        {
            "zone_id": 2,
            "zone_name": "手机禁用区",
            "zone_type": "phone_forbidden",
            "coordinates": [{"x": 0.1, "y": 0.1}, {"x": 0.5, "y": 0.1}, {"x": 0.5, "y": 0.5}, {"x": 0.1, "y": 0.5}],
        }
    ]

    detections = service.detect("classroom_01", persons, zones)

    assert len(detections) == 0


def test_mixed_zones_only_danger_triggers_intrusion():
    service = ZoneService()
    persons = [{"track_id": "person_1", "bbox": [0.2, 0.1, 0.3, 0.3]}]
    zones = [
        {
            "zone_id": 1,
            "zone_name": "danger",
            "zone_type": "danger",
            "coordinates": [{"x": 0.1, "y": 0.1}, {"x": 0.5, "y": 0.1}, {"x": 0.5, "y": 0.5}, {"x": 0.1, "y": 0.5}],
            "threshold_seconds": 2,
        },
        {
            "zone_id": 2,
            "zone_name": "手机禁用区",
            "zone_type": "phone_forbidden",
            "coordinates": [{"x": 0.1, "y": 0.1}, {"x": 0.5, "y": 0.1}, {"x": 0.5, "y": 0.5}, {"x": 0.1, "y": 0.5}],
        },
    ]

    detections = service.detect("classroom_01", persons, zones)
    zone_ids = {d["zone"]["zone_id"] for d in detections}

    assert 1 in zone_ids
    assert 2 not in zone_ids