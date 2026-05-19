"""Phase 3.23 dispatch tracer STEP_TICK error fixture.

Drives ``I-DTRACE-06`` (REQUIRED). Audits that a STEP_TICK dispatch
with a missing client records ``ERROR_RECORDED`` and
``MUTATION_CLASSIFIED`` with ``mutation_kind == ERROR_ONLY`` and
that no kernel-side substrate mutates.
"""
from __future__ import annotations

from brain.development.dispatch_tracer import (
    DispatchMutationKind,
    DispatchTraceKind,
    DispatchTraceStatus,
)
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.commands import Command, OperatorCommand
from brain.ui.session import OperatorSession


@register("I-DTRACE-06", status="REQUIRED")
def check_dispatch_tracer_step_tick_error() -> None:
    """Audit STEP_TICK missing-client error-only trace + no kernel mutation."""
    session = OperatorSession(state=initial_state())

    pre_tick = session.tick_counter
    pre_state = session.state
    pre_latest_tick = session.latest_tick
    pre_queue_size = len(session.event_queue)

    session.dispatch(Command(OperatorCommand.STEP_TICK))  # client=None

    trace = session.latest_dispatch_trace
    assert trace is not None
    assert trace.mutation_kind is DispatchMutationKind.ERROR_ONLY
    assert trace.overall_status is DispatchTraceStatus.FAIL

    # The trace contains an ERROR_RECORDED step.
    step_kinds = trace.trace.step_kinds()
    assert DispatchTraceKind.ERROR_RECORDED in step_kinds

    # Kernel-side substrate is untouched (drives I-UI-06 spirit).
    assert session.tick_counter == pre_tick
    assert session.state is pre_state
    assert session.latest_tick is pre_latest_tick
    assert len(session.event_queue) == pre_queue_size

    # Error message is bounded printable text.
    assert session.error_message != ""
    assert session.error_message.isprintable()
