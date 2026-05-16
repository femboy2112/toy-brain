"""Phase 3.8 stream command failure isolation fixture.

Drives:

* ``I-UISTRM-08`` (REQUIRED) — Stream command failure paths are local UI
  status/error only.
"""
from __future__ import annotations

from brain.development.text_stream import STREAM_TEXT_MAX_LEN
from brain.invariants import register
from brain.ui.command_line import LocalCommandError, LocalCommandLine
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.fixtures._stream_helpers import (
    make_session,
    session_kernel_identity,
    state_identity,
)
from brain.ui.session import DEFAULT_EVENT_QUEUE_LIMIT, OperatorEventQueue


_PARSER = LocalCommandLine()


def _kernel_snapshot(session) -> tuple:
    return (
        state_identity(session.state),
        session.tick_counter,
        id(session.latest_tick),
        len(session.event_queue),
        len(session.stream_history.chunks),
        session.stream_candidates,
    )


@register("I-UISTRM-08", status="REQUIRED")
def check_I_UISTRM_08_failure_isolation() -> None:
    # Malformed /stream: empty body.
    session = make_session()
    snapshot = _kernel_snapshot(session)
    result = _PARSER.parse("/stream  ")
    assert isinstance(result, LocalCommandError)
    assert _kernel_snapshot(session) == snapshot, (
        "I-UISTRM-08 violated: kernel snapshot changed after parse error"
    )

    # Over-bound /stream text.
    too_long = "x" * (STREAM_TEXT_MAX_LEN + 1)
    result = _PARSER.parse(f"/stream {too_long}")
    assert isinstance(result, LocalCommandError)
    assert _kernel_snapshot(session) == snapshot

    # Unknown candidate_id for /stream-promote.
    snapshot = _kernel_snapshot(session)
    session.dispatch(
        make_command(
            OperatorCommand.STREAM_PROMOTE, candidate_id="promo-does-not-exist"
        )
    )
    assert session.error_message != ""
    assert _kernel_snapshot(session) == snapshot, (
        "I-UISTRM-08 violated: kernel snapshot changed on unknown candidate"
    )

    # Full event queue rejects /stream-promote.
    session = make_session()
    # Append a stream chunk to obtain a real candidate_id.
    session.dispatch(make_command(OperatorCommand.STREAM_APPEND, stream_text="abc"))
    cand_id = session.stream_candidates[0].candidate_id
    # Saturate the queue with fake QueuePerceptPayload entries via valid
    # /queue dispatches. We don't have a parser path that fills the queue
    # cheaply, so use direct enqueue on the bounded queue.
    from brain.ui.commands import QueuePerceptPayload
    from brain.toce_core import ContentState
    from fractions import Fraction

    for i in range(DEFAULT_EVENT_QUEUE_LIMIT):
        session.event_queue.enqueue(
            QueuePerceptPayload(
                content_id=f"filler-{i}",
                text=f"filler text {i}",
                content_state=ContentState(
                    available=True,
                    verification_path=True,
                    retrievable=True,
                    operative=True,
                ),
                initial_rho=Fraction(1, 2),
            )
        )
    assert session.event_queue.is_full()
    snapshot = _kernel_snapshot(session)
    session.dispatch(
        make_command(OperatorCommand.STREAM_PROMOTE, candidate_id=cand_id)
    )
    assert session.error_message != ""
    assert _kernel_snapshot(session) == snapshot, (
        "I-UISTRM-08 violated: full-queue promote changed kernel snapshot"
    )

    # Successful promotion increments queue size by exactly one.
    session = make_session()
    session.dispatch(make_command(OperatorCommand.STREAM_APPEND, stream_text="abc"))
    cand_id = session.stream_candidates[0].candidate_id
    before_size = len(session.event_queue)
    session.dispatch(
        make_command(OperatorCommand.STREAM_PROMOTE, candidate_id=cand_id)
    )
    assert len(session.event_queue) == before_size + 1, (
        "I-UISTRM-08 violated: successful promote did not increase queue by 1"
    )
