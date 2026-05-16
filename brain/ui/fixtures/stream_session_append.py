"""Phase 3.8 /stream session-append fixture.

Drives:

* ``I-UISTRM-03`` (REQUIRED) — ``/stream`` appends to session-local
  ``TextStreamHistory`` only.
"""
from __future__ import annotations

from brain.development.text_stream import TextStreamHistory, TextStreamSource
from brain.invariants import register
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.fixtures._stream_helpers import (
    make_session,
    session_kernel_identity,
)


@register("I-UISTRM-03", status="REQUIRED")
def check_I_UISTRM_03_stream_append_local_only() -> None:
    session = make_session()
    prior_state_id = id(session.state)
    prior_state_repr = repr(session.state)
    prior_history = session.stream_history
    prior_candidates = session.stream_candidates
    prior_tick_counter = session.tick_counter
    prior_latest_tick = session.latest_tick
    prior_event_queue_id = id(session.event_queue)
    prior_event_queue_size = len(session.event_queue)
    prior_kernel = session_kernel_identity(session)

    cmd = make_command(OperatorCommand.STREAM_APPEND, stream_text="hello world")
    session.dispatch(cmd)

    # Kernel-side state untouched.
    assert id(session.state) == prior_state_id, (
        "I-UISTRM-03 violated: BrainState identity changed"
    )
    assert repr(session.state) == prior_state_repr, (
        "I-UISTRM-03 violated: BrainState repr changed"
    )
    assert session.tick_counter == prior_tick_counter, (
        "I-UISTRM-03 violated: tick_counter changed"
    )
    assert session.latest_tick is prior_latest_tick, (
        "I-UISTRM-03 violated: latest_tick changed"
    )
    assert id(session.event_queue) == prior_event_queue_id, (
        "I-UISTRM-03 violated: event_queue identity changed"
    )
    assert len(session.event_queue) == prior_event_queue_size, (
        "I-UISTRM-03 violated: event_queue length changed"
    )
    assert session_kernel_identity(session) == prior_kernel, (
        "I-UISTRM-03 violated: aggregate kernel identity changed"
    )

    # Stream history grew by exactly one chunk; prior history reference
    # is unchanged (copy-on-write).
    assert isinstance(session.stream_history, TextStreamHistory)
    assert len(session.stream_history.chunks) == len(prior_history.chunks) + 1
    assert prior_history.chunks == ()
    chunk = session.stream_history.chunks[-1]
    assert chunk.source is TextStreamSource.OPERATOR
    assert chunk.text == "hello world"
    assert chunk.chunk_id == "strm-chunk-1"

    # One new candidate was derived from the chunk.
    assert len(session.stream_candidates) == len(prior_candidates) + 1
    candidate = session.stream_candidates[-1]
    assert candidate.candidate_id == "promo-strm-chunk-1"
    assert candidate.target_content_id == "strm-strm-chunk-1"

    # No source histories were created or mutated by /stream.
    assert session.output_history is None
    assert session.worldlet_history is None
    assert session.repl_history is None

    # Second append continues the deterministic id sequence.
    session.dispatch(make_command(OperatorCommand.STREAM_APPEND, stream_text="again"))
    assert session.stream_history.chunks[-1].chunk_id == "strm-chunk-2"
