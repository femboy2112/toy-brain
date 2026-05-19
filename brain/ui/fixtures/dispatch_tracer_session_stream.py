"""Phase 3.23 dispatch tracer session-wiring fixture.

Drives ``I-DTRACE-03`` (OperatorSession.dispatch emits / stores trace
for STREAM_APPEND) and ``I-DTRACE-04`` (trace distinguishes mutation
kinds across the public dispatch routes).
"""
from __future__ import annotations

from brain.development.dispatch_tracer import (
    DispatchMutationKind,
    DispatchTraceReport,
    DispatchTraceStatus,
)
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.commands import (
    AutosaveEnablePayload,
    Command,
    OperatorCommand,
    StreamAppendPayload,
)
from brain.ui.session import OperatorSession, _ALLOWED_SESSION_ATTRS


def _fresh_session() -> OperatorSession:
    return OperatorSession(state=initial_state())


@register("I-DTRACE-03", status="REQUIRED")
def check_session_dispatch_emits_trace() -> None:
    """Audit OperatorSession.dispatch stores latest_dispatch_trace."""

    # Fresh session: no trace yet.
    s = _fresh_session()
    assert s.latest_dispatch_trace is None
    assert "latest_dispatch_trace" in _ALLOWED_SESSION_ATTRS

    # STREAM_APPEND dispatch produces a trace.
    cmd = Command(
        OperatorCommand.STREAM_APPEND,
        payload=StreamAppendPayload(text="alpha line one"),
    )
    out = s.dispatch(cmd)
    assert out is None  # existing return contract unchanged
    trace = s.latest_dispatch_trace
    assert isinstance(trace, DispatchTraceReport)
    assert trace.command_kind == "stream_append"
    assert trace.mutation_kind is DispatchMutationKind.STREAM_APPEND
    assert trace.overall_status is DispatchTraceStatus.PASS
    assert trace.route_path == "stream-append"
    assert trace.step_total >= 5
    assert len(trace.trace_digest_hex16) == 16

    # Two dispatches: latest_dispatch_trace is overwritten (single slot).
    s.dispatch(Command(OperatorCommand.HELP))
    after_help = s.latest_dispatch_trace
    assert after_help.command_kind == "help"
    assert after_help is not trace  # slot replaced

    # Determinism across two fresh sessions.
    sa = _fresh_session()
    sb = _fresh_session()
    sa.dispatch(cmd)
    sb.dispatch(cmd)
    assert (
        sa.latest_dispatch_trace.trace_digest_hex16
        == sb.latest_dispatch_trace.trace_digest_hex16
    )


@register("I-DTRACE-04", status="REQUIRED")
def check_session_dispatch_mutation_kinds() -> None:
    """Audit per-route DispatchMutationKind classification."""

    # Build (command, expected mutation_kind, expected route_label)
    # rows for every safely-runnable command.
    routes: list[tuple[Command, DispatchMutationKind, str]] = []
    routes.append((
        Command(OperatorCommand.INSPECT_STATE),
        DispatchMutationKind.VIEW_CHANGE,
        "inspect-view-change",
    ))
    routes.append((
        Command(OperatorCommand.INSPECT_TICK),
        DispatchMutationKind.VIEW_CHANGE,
        "inspect-view-change",
    ))
    routes.append((
        Command(OperatorCommand.CLEAR_STATUS),
        DispatchMutationKind.UI_ONLY,
        "clear-status",
    ))
    routes.append((
        Command(OperatorCommand.HELP),
        DispatchMutationKind.VIEW_CHANGE,
        "help-view",
    ))
    routes.append((
        Command(OperatorCommand.QUIT),
        DispatchMutationKind.QUIT_FLAG,
        "quit-flag",
    ))
    routes.append((
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text="beta line one"),
        ),
        DispatchMutationKind.STREAM_APPEND,
        "stream-append",
    ))
    routes.append((
        Command(OperatorCommand.SESSION_STATUS),
        DispatchMutationKind.UI_ONLY,
        "session-status",
    ))
    routes.append((
        Command(OperatorCommand.AUTOSAVE_STATUS),
        DispatchMutationKind.UI_ONLY,
        "autosave-status",
    ))
    routes.append((
        Command(OperatorCommand.AUTOSAVE_DISABLE),
        DispatchMutationKind.AUTOSAVE,
        "autosave-config",
    ))

    for cmd, expected_mut, expected_route in routes:
        s = _fresh_session()
        s.dispatch(cmd)
        trace = s.latest_dispatch_trace
        assert isinstance(trace, DispatchTraceReport), (
            f"I-DTRACE-04 violated: no trace after {cmd.kind.value}"
        )
        assert trace.mutation_kind is expected_mut, (
            "I-DTRACE-04 violated: "
            f"{cmd.kind.value} expected mutation_kind={expected_mut.value} "
            f"got {trace.mutation_kind.value}"
        )
        assert expected_route in trace.route_path, (
            "I-DTRACE-04 violated: "
            f"{cmd.kind.value} expected route_label {expected_route!r} in "
            f"route_path={trace.route_path!r}"
        )

    # DispatchMutationKind has exactly the 14 documented values.
    expected_mutation_values = frozenset(
        {
            "none",
            "ui_only",
            "stream_append",
            "stream_window_internal",
            "stream_promote",
            "queue_mutation",
            "step_tick",
            "session_persistence",
            "autosave",
            "db_observe",
            "db_backup",
            "view_change",
            "quit_flag",
            "error_only",
        }
    )
    actual = frozenset(m.value for m in DispatchMutationKind)
    assert actual == expected_mutation_values, (
        f"I-DTRACE-04 violated: DispatchMutationKind drifted: {sorted(actual)!r}"
    )
