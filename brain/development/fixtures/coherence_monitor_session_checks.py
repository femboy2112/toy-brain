"""Fixture for I-COHMON-05: operator session coherence checks are read-only.

A healthy default :class:`OperatorSession` yields PASS on every
session coherence check (including the optional
``pattern_ledger`` field added in Step 11). Running the checks
leaves every ``OperatorSession`` slot identity-stable.
"""
from __future__ import annotations

from brain.development.coherence_monitor import (
    CoherenceCheck,
    CoherenceCheckStatus,
    build_session_checks,
    compute_overall_status,
)
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.session import _ALLOWED_SESSION_ATTRS, OperatorSession


def _session_identity(session: OperatorSession) -> dict[str, int]:
    return {name: id(getattr(session, name)) for name in _ALLOWED_SESSION_ATTRS}


@register("I-COHMON-05", status="REQUIRED")
def check_session_coherence_checks_are_read_only() -> None:
    session = OperatorSession(state=initial_state())
    pre_identity = _session_identity(session)
    pre_view = session.active_view
    pre_status = session.status_message
    pre_error = session.error_message
    pre_queue_size = len(session.event_queue)

    checks = build_session_checks(session)
    assert isinstance(checks, tuple), (
        "I-COHMON-05 violated: build_session_checks did not return a tuple"
    )
    assert len(checks) >= 5, (
        f"I-COHMON-05 violated: expected at least 5 session checks, "
        f"got {len(checks)}"
    )
    for c in checks:
        assert isinstance(c, CoherenceCheck), (
            f"I-COHMON-05 violated: session check has wrong type "
            f"{type(c).__name__}"
        )
        assert c.source == "session", (
            f"I-COHMON-05 violated: session check {c.check_id!r} has source "
            f"{c.source!r} != 'session'"
        )

    # Required check_ids appear.
    ids = {c.check_id for c in checks}
    required_ids = {
        "session.no_unsafe_resources",
        "session.active_view_legal",
        "session.event_queue_bounded",
        "session.status_error_bounded",
        "session.pattern_ledger_field",
    }
    missing = required_ids - ids
    assert not missing, (
        f"I-COHMON-05 violated: session checks missing {sorted(missing)!r}"
    )

    # Healthy session: every check is PASS (pattern_ledger present
    # post-Step-11) or NOT_APPLICABLE.
    for c in checks:
        assert c.status in (
            CoherenceCheckStatus.PASS,
            CoherenceCheckStatus.NOT_APPLICABLE,
        ), (
            f"I-COHMON-05 violated: healthy session check {c.check_id!r} "
            f"status={c.status.value}"
        )
    assert compute_overall_status(checks) is CoherenceCheckStatus.PASS

    # Identity-stable: every session slot unchanged.
    post_identity = _session_identity(session)
    assert pre_identity == post_identity, (
        "I-COHMON-05 violated: session slot identity changed"
    )
    assert session.active_view == pre_view
    assert session.status_message == pre_status
    assert session.error_message == pre_error
    assert len(session.event_queue) == pre_queue_size

    # The session.active_view_legal check correctly reports the
    # default "state" view as legal.
    for c in checks:
        if c.check_id == "session.active_view_legal":
            assert c.status is CoherenceCheckStatus.PASS
            assert "state" in c.detail

    # The session.event_queue_bounded check reports correct shape.
    for c in checks:
        if c.check_id == "session.event_queue_bounded":
            assert c.status is CoherenceCheckStatus.PASS
            assert "limit=" in c.detail

    # session.pattern_ledger_field PASSes because Step 11 added the
    # default-empty PatternLedger.
    for c in checks:
        if c.check_id == "session.pattern_ledger_field":
            assert c.status is CoherenceCheckStatus.PASS, (
                f"I-COHMON-05 violated: pattern_ledger_field check "
                f"status={c.status.value} on a Step-11 session"
            )

    # Bounded printable status/error report ok.
    for c in checks:
        if c.check_id == "session.status_error_bounded":
            assert c.status is CoherenceCheckStatus.PASS
