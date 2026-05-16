"""Phase 3.8 /stream-promote queue-only fixture.

Drives:

* ``I-UISTRM-06`` (REQUIRED) — ``/stream-promote`` queues exactly one
  validated candidate and does not tick.
"""
from __future__ import annotations

from brain.invariants import register
from brain.ui.commands import OperatorCommand, QueuePerceptPayload, make_command
from brain.ui.fixtures._stream_helpers import (
    make_session,
    state_identity,
)


def _prime_session():
    session = make_session()
    session.dispatch(make_command(OperatorCommand.STREAM_APPEND, stream_text="hello"))
    session.dispatch(make_command(OperatorCommand.STREAM_APPEND, stream_text="world"))
    return session


@register("I-UISTRM-06", status="REQUIRED")
def check_I_UISTRM_06_stream_promote_queue_only() -> None:
    session = _prime_session()
    candidate_id = session.stream_candidates[0].candidate_id
    candidate = session.stream_candidates[0]
    prior_state_id = state_identity(session.state)
    prior_tick_counter = session.tick_counter
    prior_latest_tick = session.latest_tick
    prior_queue_size = len(session.event_queue)
    prior_history_id = id(session.stream_history)
    prior_chunks = session.stream_history.chunks
    prior_candidates = session.stream_candidates

    session.dispatch(
        make_command(OperatorCommand.STREAM_PROMOTE, candidate_id=candidate_id)
    )

    # Queue grew by exactly one validated QueuePerceptPayload.
    assert len(session.event_queue) == prior_queue_size + 1, (
        "I-UISTRM-06 violated: event_queue length delta != 1 "
        f"(prior={prior_queue_size}, now={len(session.event_queue)})"
    )
    queued = session.event_queue.peek()
    assert isinstance(queued, QueuePerceptPayload), (
        "I-UISTRM-06 violated: queued head is not a QueuePerceptPayload"
    )
    assert queued.content_id == candidate.target_content_id
    assert queued.text == candidate.text

    # No tick fired and no dequeue happened beyond the explicit enqueue.
    assert session.tick_counter == prior_tick_counter, (
        "I-UISTRM-06 violated: tick_counter changed"
    )
    assert session.latest_tick is prior_latest_tick, (
        "I-UISTRM-06 violated: latest_tick changed"
    )
    # BrainState identity preserved.
    assert state_identity(session.state) == prior_state_id, (
        "I-UISTRM-06 violated: BrainState identity changed"
    )

    # Stream substrate state untouched: history identity and candidate
    # tuple preserved.
    assert id(session.stream_history) == prior_history_id
    assert session.stream_history.chunks == prior_chunks
    assert session.stream_candidates == prior_candidates

    # Unknown candidate_id does not change queue size.
    queue_before = len(session.event_queue)
    session.dispatch(
        make_command(
            OperatorCommand.STREAM_PROMOTE, candidate_id="promo-does-not-exist"
        )
    )
    assert len(session.event_queue) == queue_before, (
        "I-UISTRM-06 violated: unknown candidate changed queue"
    )
    assert session.error_message != ""
