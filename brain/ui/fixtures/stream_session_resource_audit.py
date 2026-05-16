"""Phase 3.8 stream session resource-free audit fixture.

Drives:

* ``I-UISTRM-11`` (STRUCTURAL) — Stream session state is resource-free
  and local.
"""
from __future__ import annotations

from brain.development.text_stream import (
    STREAM_PROMOTION_MAX,
    StreamPromotionCandidate,
    TextStreamHistory,
)
from brain.invariants import register
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.fixtures._stream_helpers import make_session


_FORBIDDEN_RESOURCE_ATTRS: tuple[str, ...] = (
    "fileno",
    "send_signal",
    "communicate",
    "connect",
    "recv",
    "send",
    "eval_consistency",  # LLM-client duck type
)


def _assert_no_forbidden_resource(label: str, value: object) -> None:
    assert not callable(value), (
        f"I-UISTRM-11 violated: {label} is callable"
    )
    for attr in _FORBIDDEN_RESOURCE_ATTRS:
        assert not hasattr(value, attr), (
            f"I-UISTRM-11 violated: {label} exposes resource-like attribute "
            f"{attr!r}"
        )


@register("I-UISTRM-11", status="STRUCTURAL")
def check_I_UISTRM_11_stream_session_resource_free() -> None:
    session = make_session()

    # Initial state: TextStreamHistory + empty candidate tuple + serial 0.
    assert isinstance(session.stream_history, TextStreamHistory)
    assert isinstance(session.stream_candidates, tuple)
    assert session.stream_chunk_serial == 0
    _assert_no_forbidden_resource("OperatorSession.stream_history", session.stream_history)
    _assert_no_forbidden_resource(
        "OperatorSession.stream_candidates", session.stream_candidates
    )

    # After /stream-* dispatches the session's stream fields remain
    # bounded local records with no forbidden surfaces.
    session.dispatch(make_command(OperatorCommand.STREAM_APPEND, stream_text="abc"))
    session.dispatch(make_command(OperatorCommand.STREAM_APPEND, stream_text="def"))
    for cand in session.stream_candidates:
        assert isinstance(cand, StreamPromotionCandidate)
        _assert_no_forbidden_resource(
            f"OperatorSession.stream_candidates[{cand.candidate_id}]", cand
        )

    # Stream candidate tuple is bounded at STREAM_PROMOTION_MAX.
    assert len(session.stream_candidates) <= STREAM_PROMOTION_MAX

    # Stream history holds no callable / resource handle on any chunk.
    for chunk in session.stream_history.chunks:
        _assert_no_forbidden_resource(
            f"OperatorSession.stream_history.chunks[{chunk.chunk_id}]", chunk
        )
