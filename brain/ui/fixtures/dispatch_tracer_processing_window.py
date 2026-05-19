"""Phase 3.23 dispatch tracer processing-window fixture.

Drives ``I-DTRACE-05`` (REQUIRED). Audits that the dispatch trace
records ``STREAM_WINDOW_INTERNAL`` mutation_kind when the Phase 3.18
processing window fires and that ``feedback_mode`` is captured in
``before_facts``.
"""
from __future__ import annotations

from brain.development.dispatch_tracer import (
    DispatchMutationKind,
    DispatchTraceKind,
    DispatchTraceReport,
)
from brain.development.processing_window import FeedbackMode
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.commands import Command, OperatorCommand, StreamAppendPayload
from brain.ui.session import OperatorSession


def _fresh_session() -> OperatorSession:
    return OperatorSession(state=initial_state())


def _pre_state_step(trace: DispatchTraceReport):
    for s in trace.trace.steps:
        if s.kind is DispatchTraceKind.PRE_STATE_SNAPSHOT:
            return s
    return None


def _fact(step, key: str) -> str:
    for k, v in step.before_facts:
        if k == key:
            return v
    return ""


@register("I-DTRACE-05", status="REQUIRED")
def check_dispatch_tracer_processing_window() -> None:
    """Audit STREAM_WINDOW_INTERNAL mutation classification + feedback_mode capture."""

    # 1. processing_window_size == 0 keeps the mutation classification
    # at STREAM_APPEND regardless of feedback_mode. With window == 0,
    # _run_processing_window is a no-op, so no internal chunks fire.
    s = _fresh_session()
    s.processing_window_size = 0
    s.feedback_mode = FeedbackMode.OFF
    s.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text="alpha w0"),
        )
    )
    trace = s.latest_dispatch_trace
    assert trace.mutation_kind is DispatchMutationKind.STREAM_APPEND, (
        "I-DTRACE-05 violated: window=0 should keep STREAM_APPEND, got "
        f"{trace.mutation_kind.value}"
    )

    # 1b. Even with FeedbackMode.OFF, processing_window_size > 0 fires
    # internal rehearsal chunks (Phase 3.18 architecture A), so the
    # mutation classification reflects the multi-chunk window.
    s = _fresh_session()
    s.processing_window_size = 2
    s.feedback_mode = FeedbackMode.OFF
    s.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text="alpha off"),
        )
    )
    trace = s.latest_dispatch_trace
    assert trace.mutation_kind is DispatchMutationKind.STREAM_WINDOW_INTERNAL, (
        "I-DTRACE-05 violated: window>0+OFF should produce "
        f"STREAM_WINDOW_INTERNAL, got {trace.mutation_kind.value}"
    )

    # 2. FeedbackMode.PATTERN_LEDGER + window 2 -> STREAM_WINDOW_INTERNAL.
    s = _fresh_session()
    s.processing_window_size = 2
    s.feedback_mode = FeedbackMode.PATTERN_LEDGER
    s.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text="alpha pl"),
        )
    )
    trace = s.latest_dispatch_trace
    assert trace.mutation_kind is DispatchMutationKind.STREAM_WINDOW_INTERNAL, (
        "I-DTRACE-05 violated: PATTERN_LEDGER+window should produce "
        f"STREAM_WINDOW_INTERNAL, got {trace.mutation_kind.value}"
    )
    pre = _pre_state_step(trace)
    assert pre is not None
    assert _fact(pre, "feedback_mode") == FeedbackMode.PATTERN_LEDGER.value

    # 3. FeedbackMode.PATTERN_AND_COHERENCE -> STREAM_WINDOW_INTERNAL and
    # the before_facts feedback_mode is the multimodal value.
    s = _fresh_session()
    s.processing_window_size = 2
    s.feedback_mode = FeedbackMode.PATTERN_AND_COHERENCE
    s.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text="alpha pac"),
        )
    )
    trace = s.latest_dispatch_trace
    assert trace.mutation_kind is DispatchMutationKind.STREAM_WINDOW_INTERNAL
    pre = _pre_state_step(trace)
    assert pre is not None
    assert (
        _fact(pre, "feedback_mode")
        == FeedbackMode.PATTERN_AND_COHERENCE.value
    )
    # processing_window_size also captured.
    assert _fact(pre, "processing_window_size") == "2"

    # 4. FeedbackMode.COHERENCE + window 2 also produces internal mutation.
    s = _fresh_session()
    s.processing_window_size = 2
    s.feedback_mode = FeedbackMode.COHERENCE
    s.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text="alpha coh"),
        )
    )
    trace = s.latest_dispatch_trace
    assert trace.mutation_kind is DispatchMutationKind.STREAM_WINDOW_INTERNAL
