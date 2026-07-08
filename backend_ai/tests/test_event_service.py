from backend_ai.services.event_service import EventService


def test_query_filters_events():
    service = EventService()
    service.add_event(service.build_event("classroom_01", "phone_usage", 0.9))
    service.add_event(service.build_event("classroom_02", "head_down", 0.8))

    items = service.query(stream_id="classroom_01", event_type="phone_usage")

    assert len(items) == 1
    assert items[0]["event_type"] == "phone_usage"


def test_observe_confirms_after_threshold_and_cooldown():
    service = EventService(default_cooldown_seconds=10)

    event, confirmed = service.observe(
        stream_id="classroom_01",
        event_type="phone_usage",
        track_key="person_1",
        confidence=0.9,
        threshold_seconds=3,
        cooldown_seconds=10,
        now=100,
    )
    assert not confirmed
    assert event["event_status"] == "candidate"

    event, confirmed = service.observe(
        stream_id="classroom_01",
        event_type="phone_usage",
        track_key="person_1",
        confidence=0.9,
        threshold_seconds=3,
        cooldown_seconds=10,
        now=104,
    )
    assert confirmed
    assert event["event_status"] == "confirmed"


def test_observe_uses_same_event_id_for_same_track():
    service = EventService()
    first, _ = service.observe("classroom_01", "head_down", "person_1", 0.8, now=1)
    second, _ = service.observe("classroom_01", "head_down", "person_1", 0.9, now=2)

    assert first["event_id"] == second["event_id"]

