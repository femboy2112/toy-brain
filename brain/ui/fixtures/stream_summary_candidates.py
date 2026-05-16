"""Phase 3.8 /stream-summary and /stream-candidates fixtures.

Drives:

* ``I-UISTRM-04`` (REQUIRED) — ``/stream-summary`` is read-only.
* ``I-UISTRM-05`` (REQUIRED) — ``/stream-candidates`` is read-only.
"""
from __future__ import annotations

from brain.development.text_stream import STREAM_PROMOTION_MAX
from brain.invariants import register
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.fixtures._stream_helpers import (
    make_session,
    session_kernel_identity,
)
from brain.ui.snapshot import (
    StreamCandidatesSnapshot,
    StreamSummarySnapshot,
    build_stream_candidates_snapshot,
    build_stream_summary_snapshot,
)


def _prime_session():
    session = make_session()
    session.dispatch(make_command(OperatorCommand.STREAM_APPEND, stream_text="hello world"))
    session.dispatch(make_command(OperatorCommand.STREAM_APPEND, stream_text="goodbye"))
    return session


def _full_snapshot(session) -> tuple:
    return (
        session_kernel_identity(session),
        session.stream_history.chunks,
        session.stream_candidates,
        session.active_view,
        session.tick_counter,
        len(session.event_queue),
    )


@register("I-UISTRM-04", status="REQUIRED")
def check_I_UISTRM_04_stream_summary_read_only() -> None:
    session = _prime_session()
    before_state_repr = repr(session.state)
    before_history_id = id(session.stream_history)
    before_chunks = session.stream_history.chunks
    before_candidates = session.stream_candidates
    before_kernel = session_kernel_identity(session)
    before_view = session.active_view

    # Reset view to something other than the target so the dispatch
    # transition is observable.
    session.set_active_view("state")
    before_view = session.active_view

    session.dispatch(make_command(OperatorCommand.INSPECT_STREAM_SUMMARY))

    # Stream substrate state untouched.
    assert id(session.stream_history) == before_history_id
    assert session.stream_history.chunks == before_chunks
    assert session.stream_candidates == before_candidates
    assert session_kernel_identity(session) == before_kernel
    assert repr(session.state) == before_state_repr

    # Active view selected.
    assert session.active_view == "stream_summary"
    assert before_view != "stream_summary"

    # Snapshot is deterministic across repeated builds and is a frozen
    # immutable record.
    snap1 = build_stream_summary_snapshot(stream_history=session.stream_history)
    snap2 = build_stream_summary_snapshot(stream_history=session.stream_history)
    assert isinstance(snap1, StreamSummarySnapshot)
    assert snap1 == snap2
    assert snap1.chunk_count == 2
    assert snap1.total_text_length == len("hello world") + len("goodbye")
    assert snap1.distinct_chunk_ids == 2
    # Verify immutability.
    try:
        snap1.chunk_count = 99  # type: ignore[misc]
    except Exception:
        pass
    else:
        raise AssertionError("I-UISTRM-04 violated: StreamSummarySnapshot mutable")

    # No tick fired.
    assert session.tick_counter == before_kernel[1]


@register("I-UISTRM-05", status="REQUIRED")
def check_I_UISTRM_05_stream_candidates_read_only() -> None:
    session = _prime_session()
    before_state_repr = repr(session.state)
    before_history_id = id(session.stream_history)
    before_chunks = session.stream_history.chunks
    before_candidates = session.stream_candidates
    before_kernel = session_kernel_identity(session)
    before_view = session.active_view

    session.set_active_view("state")
    before_view = session.active_view

    session.dispatch(make_command(OperatorCommand.INSPECT_STREAM_CANDIDATES))

    assert id(session.stream_history) == before_history_id
    assert session.stream_history.chunks == before_chunks
    assert session.stream_candidates == before_candidates
    assert session_kernel_identity(session) == before_kernel
    assert repr(session.state) == before_state_repr

    assert session.active_view == "stream_candidates"
    assert before_view != "stream_candidates"

    snap1 = build_stream_candidates_snapshot(
        stream_candidates=session.stream_candidates,
        capacity=STREAM_PROMOTION_MAX,
    )
    snap2 = build_stream_candidates_snapshot(
        stream_candidates=session.stream_candidates,
        capacity=STREAM_PROMOTION_MAX,
    )
    assert isinstance(snap1, StreamCandidatesSnapshot)
    assert snap1 == snap2
    assert snap1.candidate_count == 2
    assert snap1.candidate_capacity == STREAM_PROMOTION_MAX
    assert tuple(c.candidate_id for c in snap1.candidates) == (
        "promo-strm-chunk-1",
        "promo-strm-chunk-2",
    )

    # No tick fired.
    assert session.tick_counter == before_kernel[1]
