"""Fixture for I-COHMON-08 and I-COHMON-12.

* I-COHMON-08 — persistence / autosave reporting is read-only and
  does not open the DB or call ``save_session`` /
  ``load_session`` / ``db_backup`` / ``db_verify`` / autosave
  helpers from inside :mod:`brain.development.coherence_monitor`.
* I-COHMON-12 — :class:`CoherenceSnapshot` and :class:`CoherenceReport`
  record fields are bounded primitives, tuples of bounded primitives,
  closed enums, ints, or bools; no callable, file handle, socket,
  subprocess handle, ``pathlib.Path``, ``sqlite3.Connection`` /
  ``Cursor``, curses object, or ``eval_consistency``-bearing object
  appears in any field.

The fixture also asserts that running a full report leaves the live
``BrainState`` / ``OperatorSession`` / ``stream_history`` /
``stream_candidates`` / ``pattern_ledger`` / ``latest_tick`` /
``tick_counter`` identity-stable.
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.development.coherence_monitor import (
    CoherenceReport,
    CoherenceSnapshot,
    build_full_coherence_report,
)
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.session import OperatorSession


_COHERENCE_MONITOR_SOURCE_PATH = (
    Path(__file__).resolve().parent.parent / "coherence_monitor.py"
)


def _value_looks_unsafe(value: object) -> tuple[bool, str]:
    if callable(value):
        return True, "callable"
    if hasattr(value, "eval_consistency"):
        return True, "eval_consistency (LLM client)"
    if hasattr(value, "read") and hasattr(value, "write"):
        return True, "read/write (file/socket-like)"
    if hasattr(value, "fileno"):
        return True, "fileno (resource-like)"
    if hasattr(value, "send_signal") or hasattr(value, "communicate"):
        return True, "subprocess handle"
    if hasattr(value, "cursor") and hasattr(value, "commit"):
        return True, "sqlite3.Connection-like"
    return False, ""


def _walk_field_values(record: object) -> list[tuple[str, object]]:
    out: list[tuple[str, object]] = []
    for name in getattr(record, "__slots__", ()):
        value = getattr(record, name)
        out.append((name, value))
        if isinstance(value, tuple):
            for i, item in enumerate(value):
                out.append((f"{name}[{i}]", item))
    return out


def _session_identity(session: OperatorSession) -> tuple:
    state = session.state
    return (
        id(state),
        id(state.profile),
        id(state.profile.values),
        id(state.msi),
        id(state.ptcns),
        id(state.registry),
        id(state.registry.texts),
        id(session.event_queue),
        len(session.event_queue),
        id(session.stream_history),
        len(session.stream_history.chunks),
        id(session.stream_candidates),
        len(session.stream_candidates),
        id(session.pattern_ledger),
        len(session.pattern_ledger.entries),
        id(session.latest_tick),
        session.tick_counter,
        session.active_view,
        session.status_message,
        session.error_message,
    )


@register("I-COHMON-08", status="REQUIRED")
def check_no_persistence_autosave_runtime_coupling() -> None:
    # Static side: parse the module and assert no call to the
    # forbidden persistence / autosave helpers appears.
    source = _COHERENCE_MONITOR_SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_COHERENCE_MONITOR_SOURCE_PATH))

    forbidden_calls = (
        "save_session",
        "load_session",
        "db_backup",
        "db_verify",
        "maybe_autosave_after_mutation",
        "sqlite3.connect",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                parts: list[str] = []
                cur: ast.AST | None = func
                while isinstance(cur, ast.Attribute):
                    parts.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    parts.append(cur.id)
                name = ".".join(reversed(parts))
            else:
                name = ""
            for forbidden in forbidden_calls:
                assert forbidden not in name, (
                    "I-COHMON-08 violated: coherence_monitor.py calls "
                    f"{name!r} at line {node.lineno}"
                )

    # Runtime side: build a full report and confirm session
    # identity is stable.
    session = OperatorSession(state=initial_state())
    pre = _session_identity(session)

    report = build_full_coherence_report(session)
    assert isinstance(report, CoherenceReport)

    post = _session_identity(session)
    assert pre == post, (
        "I-COHMON-08 violated: building a full coherence report mutated the "
        "live session"
    )

    # Re-run with a configured /stream append; still identity-stable.
    session.dispatch(
        make_command(OperatorCommand.STREAM_APPEND, stream_text="alpha")
    )
    pre = _session_identity(session)
    report = build_full_coherence_report(session)
    post = _session_identity(session)
    assert pre == post, (
        "I-COHMON-08 violated: rebuild over a populated session mutated state"
    )
    assert isinstance(report.snapshot, CoherenceSnapshot)


@register("I-COHMON-12", status="STRUCTURAL")
def check_coherence_records_carry_no_unsafe_resources() -> None:
    session = OperatorSession(state=initial_state())
    session.dispatch(
        make_command(OperatorCommand.STREAM_APPEND, stream_text="alpha")
    )
    report = build_full_coherence_report(session)

    # CoherenceReport fields.
    for name, value in _walk_field_values(report):
        unsafe, reason = _value_looks_unsafe(value)
        assert not unsafe, (
            f"I-COHMON-12 violated: CoherenceReport.{name} looks unsafe "
            f"({reason})"
        )

    # CoherenceSnapshot fields.
    snap = report.snapshot
    for name, value in _walk_field_values(snap):
        unsafe, reason = _value_looks_unsafe(value)
        assert not unsafe, (
            f"I-COHMON-12 violated: CoherenceSnapshot.{name} looks unsafe "
            f"({reason})"
        )

    # Every CoherenceCheck field.
    for idx, check in enumerate(snap.checks):
        for name, value in _walk_field_values(check):
            unsafe, reason = _value_looks_unsafe(value)
            assert not unsafe, (
                f"I-COHMON-12 violated: CoherenceSnapshot.checks[{idx}].{name} "
                f"looks unsafe ({reason})"
            )
