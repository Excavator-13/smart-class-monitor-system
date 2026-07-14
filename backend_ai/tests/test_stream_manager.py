from concurrent.futures import ThreadPoolExecutor
import time

import numpy as np

from backend_ai.services.stream_manager import StreamManager


class EmptyConfigClient:
    def get_stream(self, stream_id):
        return None


def make_manager(offline_after_seconds=10, recovery_after_seconds=3):
    return StreamManager(
        EmptyConfigClient(),
        offline_after_seconds=offline_after_seconds,
        reconnect_interval_seconds=0,
        recovery_after_seconds=recovery_after_seconds,
    )


def mark_failed(manager, stream_id, failed_at):
    state = manager._states[stream_id]
    manager._mark_unavailable(state, "test read failure", now=failed_at)


def test_transient_failure_does_not_emit_offline_alert():
    manager = make_manager()
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    manager.set_frame_for_test("classroom_01", frame)

    mark_failed(manager, "classroom_01", failed_at=100)

    assert manager.get_frame("classroom_01") is None
    assert not manager.should_emit_offline_alert("classroom_01", now=109.9)

    manager.set_frame_for_test("classroom_01", frame)

    assert manager.get_frame("classroom_01") is not None
    assert not manager.should_emit_offline_alert("classroom_01", now=200)


def test_continuous_failure_emits_once_after_timeout():
    manager = make_manager()
    manager.set_frame_for_test("classroom_01", np.zeros((4, 4, 3), dtype=np.uint8))
    mark_failed(manager, "classroom_01", failed_at=100)

    assert not manager.should_emit_offline_alert("classroom_01", now=109.9)
    assert manager.should_emit_offline_alert("classroom_01", now=110)
    assert not manager.should_emit_offline_alert("classroom_01", now=120)


def test_concurrent_consumers_emit_one_offline_transition():
    manager = make_manager()
    manager.set_frame_for_test("classroom_01", np.zeros((4, 4, 3), dtype=np.uint8))
    mark_failed(manager, "classroom_01", failed_at=100)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(
                lambda _: manager.should_emit_offline_alert("classroom_01", now=110),
                range(16),
            )
        )

    assert results.count(True) == 1


def test_recovery_allows_a_new_offline_episode():
    manager = make_manager()
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    manager.set_frame_for_test("classroom_01", frame)
    mark_failed(manager, "classroom_01", failed_at=100)
    assert manager.should_emit_offline_alert("classroom_01", now=110)

    manager.set_frame_for_test("classroom_01", frame)
    mark_failed(manager, "classroom_01", failed_at=200)

    assert not manager.should_emit_offline_alert("classroom_01", now=209.9)
    assert manager.should_emit_offline_alert("classroom_01", now=210)


def test_stale_cached_frame_is_not_returned_for_analysis():
    manager = make_manager(offline_after_seconds=1)
    frame = np.ones((4, 4, 3), dtype=np.uint8)
    manager.set_frame_for_test("classroom_01", frame)
    manager._states["classroom_01"].last_frame_at = time.time() - 2

    assert manager.get_frame("classroom_01") is None
    assert manager.should_emit_offline_alert("classroom_01")


def test_each_frame_sequence_can_be_claimed_for_analysis_once():
    manager = make_manager()
    manager.set_frame_for_test("classroom_01", np.zeros((4, 4, 3), dtype=np.uint8))

    frame, sequence = manager.get_frame_with_sequence("classroom_01")

    assert frame is not None
    assert sequence == 1
    assert manager.claim_frame_for_analysis("classroom_01", sequence)
    assert not manager.claim_frame_for_analysis("classroom_01", sequence)


def test_concurrent_consumers_claim_one_analysis():
    manager = make_manager()
    manager.set_frame_for_test("classroom_01", np.zeros((4, 4, 3), dtype=np.uint8))
    _frame, sequence = manager.get_frame_with_sequence("classroom_01")

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: manager.claim_frame_for_analysis("classroom_01", sequence), range(16)))

    assert results.count(True) == 1


def test_buffered_recovery_candidate_does_not_reset_offline_episode():
    manager = make_manager(recovery_after_seconds=3)
    manager.set_frame_for_test("classroom_01", np.zeros((4, 4, 3), dtype=np.uint8))
    state = manager._states["classroom_01"]
    manager._mark_unavailable(state, "failed", now=100)
    state.recovery_started_at = 101

    manager._mark_unavailable(state, "failed again", now=102)

    assert state.failure_started_at == 100
    assert state.recovery_started_at is None
    assert manager.should_emit_offline_alert("classroom_01", now=110)
