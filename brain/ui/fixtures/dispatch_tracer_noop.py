"""Phase 3.23 dispatch tracer NOOP fixture.

Drives ``I-DTRACE-07`` (REQUIRED). Audits that a NOOP dispatch records
a short bounded trace, does not fire the autosave hook or the
post-dispatch resource audit, and reports ``mutation_kind == NONE``.
"""
from __future__ import annotations

from brain.development.dispatch_tracer import (
    DispatchMutationKind,
    DispatchTraceKind,
)
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.commands import Command, OperatorCommand
from brain.ui.session import OperatorSession


@register("I-DTRACE-07", status="REQUIRED")
def check_dispatch_tracer_noop() -> None:
    """Audit NOOP route trace + no autosave / audit step."""
    session = OperatorSession(state=initial_state())
    assert session.last_autosave_status is None

    session.dispatch(Command(OperatorCommand.NOOP))

    trace = session.latest_dispatch_trace
    assert trace is not None
    assert trace.mutation_kind is DispatchMutationKind.NONE
    assert trace.route_path == "noop-early-return"
    assert trace.step_total == 5
    assert trace.command_kind == "noop"

    step_kinds = trace.trace.step_kinds()
    # The canonical NOOP shape:
    assert step_kinds == (
        DispatchTraceKind.COMMAND_RECEIVED,
        DispatchTraceKind.ROUTE_SELECTED,
        DispatchTraceKind.PRE_STATE_SNAPSHOT,
        DispatchTraceKind.NOOP_RECORDED,
        DispatchTraceKind.TRACE_FINALIZED,
    )

    # No MUTATION_CLASSIFIED, AUTOSAVE_CHECKED, RESOURCE_AUDIT_CHECKED.
    assert trace.mutation_classified_count == 0
    assert trace.autosave_checked_count == 0
    assert trace.resource_audit_checked_count == 0
    assert trace.noop_recorded_count == 1
    assert trace.error_recorded_count == 0

    # Autosave state untouched.
    assert session.last_autosave_status is None

    # The NOOP path does not set a status / view / error.
    assert session.error_message == ""
