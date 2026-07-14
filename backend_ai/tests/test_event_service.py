from concurrent.futures import ThreadPoolExecutor

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
        now=102,
    )
    assert not confirmed

    event, confirmed = service.observe(
        stream_id="classroom_01",
        event_type="phone_usage",
        track_key="person_1",
        confidence=0.9,
        threshold_seconds=3,
        cooldown_seconds=10,
        now=103,
    )
    assert confirmed
    assert event["event_status"] == "confirmed"


def test_observe_uses_same_event_id_for_same_track():
    service = EventService()
    first, _ = service.observe("classroom_01", "head_down", "person_1", 0.8, now=1)
    second, _ = service.observe("classroom_01", "head_down", "person_1", 0.9, now=2)

    assert first["event_id"] == second["event_id"]


def test_threshold_restarts_after_detection_gap():
    service = EventService(continuity_gap_seconds=2)

    first, confirmed = service.observe(
        "classroom_01", "phone_usage", "person_1", 0.9,
        threshold_seconds=3, now=100,
    )
    assert not confirmed

    restarted, confirmed = service.observe(
        "classroom_01", "phone_usage", "person_1", 0.9,
        threshold_seconds=3, now=104,
    )

    assert not confirmed
    assert restarted["duration_seconds"] == 0
    assert restarted["event_id"] != first["event_id"]


def test_continuous_episode_only_confirms_once_after_cooldown_elapsed():
    service = EventService(default_cooldown_seconds=10, continuity_gap_seconds=20)

    first, first_confirmed = service.observe(
        "classroom_01", "fall_detected", "person_1", 0.9,
        threshold_seconds=0, now=100,
    )
    repeated, repeated_confirmed = service.observe(
        "classroom_01", "fall_detected", "person_1", 0.9,
        threshold_seconds=0, now=111,
    )

    assert first_confirmed
    assert not repeated_confirmed
    assert repeated["event_id"] == first["event_id"]


def test_cooldown_is_shared_by_same_event_type_across_targets():
    service = EventService(default_cooldown_seconds=10, continuity_gap_seconds=2)

    first, first_confirmed = service.observe(
        "classroom_01", "stranger_detected", "face_1", 0.8,
        threshold_seconds=0, now=100,
    )
    repeated, repeated_confirmed = service.observe(
        "classroom_01", "stranger_detected", "face_2", 0.8,
        threshold_seconds=0, now=101,
    )

    assert first_confirmed
    assert not repeated_confirmed
    assert repeated["event_id"] == first["event_id"]


def test_new_episode_confirms_after_shared_cooldown_and_gets_new_id():
    service = EventService(default_cooldown_seconds=8, continuity_gap_seconds=2)

    first, confirmed = service.observe(
        "classroom_01", "phone_usage", "person_1", 0.9,
        threshold_seconds=0, now=100,
    )
    assert confirmed

    candidate, confirmed = service.observe(
        "classroom_01", "phone_usage", "person_2", 0.9,
        threshold_seconds=0, now=105,
    )
    assert not confirmed
    assert candidate["event_id"] != first["event_id"]

    confirmed_event, confirmed = service.observe(
        "classroom_01", "phone_usage", "person_2", 0.9,
        threshold_seconds=0, now=106,
    )
    assert not confirmed

    confirmed_event, confirmed = service.observe(
        "classroom_01", "phone_usage", "person_2", 0.9,
        threshold_seconds=0, now=108,
    )
    assert confirmed
    assert confirmed_event["event_id"] == candidate["event_id"]


def test_observe_updates_one_event_record_per_episode():
    service = EventService(continuity_gap_seconds=2)

    service.observe("classroom_01", "head_down", "person_1", 0.7, now=100)
    service.observe("classroom_01", "head_down", "person_1", 0.8, now=101)
    service.observe("classroom_01", "head_down", "person_2", 0.9, now=102)

    events = service.query(stream_id="classroom_01", event_type="head_down")
    assert len(events) == 1
    assert events[0]["confidence"] == 0.9


def test_first_observation_is_not_blocked_by_synthetic_clock_value():
    service = EventService(default_cooldown_seconds=45)

    _, confirmed = service.observe(
        "classroom_01", "stream_offline", "classroom_01", 1.0,
        threshold_seconds=0, now=1,
    )

    assert confirmed


def test_concurrent_observations_only_confirm_once():
    service = EventService(default_cooldown_seconds=45)

    def observe_once(index):
        return service.observe(
            "classroom_01", "flame_detected", f"fire_{index}", 0.9,
            threshold_seconds=0, now=100,
        )[1]

    with ThreadPoolExecutor(max_workers=8) as executor:
        confirmations = list(executor.map(observe_once, range(16)))

    assert confirmations.count(True) == 1
    assert len(service.query(event_type="flame_detected")) == 1

