"""Phase 3.8 stream snapshot/render determinism + frozen-record fixture.

Drives:

* ``I-UISTRM-09`` (REQUIRED) — Stream snapshots and render output are
  deterministic and read-only.
* ``I-UISTRM-12`` (STRUCTURAL) — Stream UI records are immutable display
  / payload values.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from typing import Any

from brain.development.text_stream import STREAM_PROMOTION_MAX
from brain.invariants import register
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.fixtures._stream_helpers import (
    make_session,
    session_kernel_identity,
)
from brain.ui.render import build_view_model, render
from brain.ui.snapshot import (
    StreamCandidateSnapshot,
    StreamCandidatesSnapshot,
    StreamSummarySnapshot,
    build_brain_snapshot,
    build_development_snapshot,
    build_stream_candidates_snapshot,
    build_stream_summary_snapshot,
)


def _build_views(session):
    return (
        build_stream_summary_snapshot(stream_history=session.stream_history),
        build_stream_candidates_snapshot(
            stream_candidates=session.stream_candidates,
            capacity=STREAM_PROMOTION_MAX,
        ),
    )


def _build_vm(session, view):
    summary, candidates = _build_views(session)
    return build_view_model(
        active_view=view,
        brain=build_brain_snapshot(session.state),
        development=build_development_snapshot(),
        stream_summary=summary,
        stream_candidates=candidates,
    )


def _try_mutate(record: Any, name: str, new_value: Any) -> None:
    try:
        setattr(record, name, new_value)
    except (FrozenInstanceError, AttributeError):
        return
    raise AssertionError(
        f"I-UISTRM-12 violated: {type(record).__name__}.{name} is mutable"
    )


@register("I-UISTRM-09", status="REQUIRED")
def check_I_UISTRM_09_stream_snapshot_render_deterministic() -> None:
    session = make_session()
    session.dispatch(make_command(OperatorCommand.STREAM_APPEND, stream_text="hello"))
    session.dispatch(make_command(OperatorCommand.STREAM_APPEND, stream_text="world"))
    session.dispatch(make_command(OperatorCommand.INSPECT_STREAM_SUMMARY))

    pre_kernel = session_kernel_identity(session)
    pre_history_id = id(session.stream_history)
    pre_chunks = session.stream_history.chunks
    pre_candidates = session.stream_candidates

    # Build snapshots / rendered rows twice; they must compare equal.
    summary1, candidates1 = _build_views(session)
    summary2, candidates2 = _build_views(session)
    assert summary1 == summary2
    assert candidates1 == candidates2

    vm1 = _build_vm(session, "stream_summary")
    vm2 = _build_vm(session, "stream_summary")
    assert render(vm1) == render(vm2), (
        "I-UISTRM-09 violated: stream_summary render not deterministic"
    )

    vm1 = _build_vm(session, "stream_candidates")
    vm2 = _build_vm(session, "stream_candidates")
    assert render(vm1) == render(vm2), (
        "I-UISTRM-09 violated: stream_candidates render not deterministic"
    )

    # Snapshot construction did not mutate session-side state.
    assert session_kernel_identity(session) == pre_kernel
    assert id(session.stream_history) == pre_history_id
    assert session.stream_history.chunks == pre_chunks
    assert session.stream_candidates == pre_candidates


@register("I-UISTRM-12", status="STRUCTURAL")
def check_I_UISTRM_12_stream_records_immutable() -> None:
    session = make_session()
    session.dispatch(make_command(OperatorCommand.STREAM_APPEND, stream_text="hello"))
    summary, candidates = _build_views(session)

    # Snapshot fields are frozen.
    _try_mutate(summary, "chunk_count", 999)
    _try_mutate(candidates, "candidate_count", 999)
    if candidates.candidates:
        snapshot_entry = candidates.candidates[0]
        assert isinstance(snapshot_entry, StreamCandidateSnapshot)
        _try_mutate(snapshot_entry, "candidate_id", "evil")

    # Field declarations are bounded primitives, tuples, or frozen
    # records — no mutable kernel container.
    for record in (summary, candidates):
        for f in fields(record):
            value = getattr(record, f.name)
            assert not callable(value), (
                f"I-UISTRM-12 violated: {type(record).__name__}.{f.name} is callable"
            )
            assert not hasattr(value, "append"), (
                f"I-UISTRM-12 violated: {type(record).__name__}.{f.name} exposes "
                "append (mutable list-like)"
            )

    # Snapshot collections are tuples.
    assert isinstance(candidates.candidates, tuple)
    assert isinstance(summary.source_counts, tuple)
