"""Fixture for I-COHMON-06 and I-COHMON-07.

* I-COHMON-06 — stream coherence checks respect ``STREAM_HISTORY_MAX_CHUNKS``,
  ``STREAM_PROMOTION_MAX``, ``stream_chunk_serial`` shape, and the
  COGITO_ID rejection on chunk / candidate identifiers.
* I-COHMON-07 — pattern ledger coherence checks validate entry
  bounds, deterministic pattern_id, the locked confidence formula,
  recurrence caps, evidence-list caps, and the session-local
  (no persistence) policy.

Both check families are read-only: the live ``stream_history``,
``stream_candidates``, and ``pattern_ledger`` references stay
identity-stable across the check run.
"""
from __future__ import annotations

from brain.development.coherence_monitor import (
    CoherenceCheck,
    CoherenceCheckStatus,
    build_pattern_ledger_checks,
    build_stream_checks,
)
from brain.development.pattern_ledger import PatternLedger
from brain.development.text_stream import TextStreamSource
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.session import OperatorSession


@register("I-COHMON-06", status="REQUIRED")
def check_stream_coherence_checks_are_read_only() -> None:
    session = OperatorSession(state=initial_state())

    # Fresh session: every stream check is PASS.
    checks = build_stream_checks(session)
    assert isinstance(checks, tuple)
    assert len(checks) >= 4
    ids = {c.check_id for c in checks}
    required_ids = {
        "stream.history_bounded",
        "stream.candidates_bounded",
        "stream.chunk_serial_consistent",
        "stream.no_cogito_in_chunks",
    }
    missing = required_ids - ids
    assert not missing, (
        f"I-COHMON-06 violated: stream checks missing {sorted(missing)!r}"
    )
    for c in checks:
        assert isinstance(c, CoherenceCheck)
        assert c.source == "stream"
        assert c.status is CoherenceCheckStatus.PASS, (
            f"I-COHMON-06 violated: fresh-session stream check {c.check_id!r} "
            f"status={c.status.value}"
        )

    # After a /stream append: history grows, candidates grow,
    # serial advances, but the stream checks remain PASS and the
    # references are identity-stable across the check call.
    session.dispatch(
        make_command(OperatorCommand.STREAM_APPEND, stream_text="alpha beta")
    )
    prior_history = session.stream_history
    prior_candidates = session.stream_candidates
    prior_serial = session.stream_chunk_serial

    checks = build_stream_checks(session)
    for c in checks:
        assert c.status is CoherenceCheckStatus.PASS, (
            f"I-COHMON-06 violated: stream check {c.check_id!r} on a healthy "
            f"session reports {c.status.value}"
        )

    # The stream surfaces are unchanged across the check.
    assert session.stream_history is prior_history
    assert session.stream_candidates is prior_candidates
    assert session.stream_chunk_serial == prior_serial

    # Source value of every stream chunk is from the closed enum.
    for chunk in session.stream_history.chunks:
        assert chunk.source in TextStreamSource


@register("I-COHMON-07", status="REQUIRED")
def check_pattern_ledger_coherence_checks_are_read_only() -> None:
    session = OperatorSession(state=initial_state())

    # Fresh session has an empty PatternLedger; the corresponding
    # check family returns one entries-bounded NOT_APPLICABLE because
    # the ledger has no entries (LOCK C cold start).
    fresh_checks = build_pattern_ledger_checks(session)
    assert isinstance(fresh_checks, tuple)
    fresh_ids = {c.check_id for c in fresh_checks}
    assert "pledger.entries_bounded" in fresh_ids, (
        "I-COHMON-07 violated: pledger.entries_bounded missing on fresh session"
    )
    # Every fresh-session pledger check is either PASS or NOT_APPLICABLE.
    for c in fresh_checks:
        assert c.source == "pattern_ledger"
        assert c.status in (
            CoherenceCheckStatus.PASS,
            CoherenceCheckStatus.NOT_APPLICABLE,
        ), (
            f"I-COHMON-07 violated: fresh pledger check {c.check_id!r} "
            f"status={c.status.value}"
        )

    # After two /stream appends with the same text, the ledger gains
    # one entry; every pledger check is PASS.
    for _ in range(2):
        session.dispatch(
            make_command(OperatorCommand.STREAM_APPEND, stream_text="alpha")
        )
    assert len(session.pattern_ledger.entries) == 1

    prior_ledger = session.pattern_ledger
    prior_entries = prior_ledger.entries

    checks = build_pattern_ledger_checks(session)
    required_ids = {
        "pledger.entries_bounded",
        "pledger.entries_validate_constructor_invariants",
        "pledger.recurrence_counts_bounded",
        "pledger.confidence_matches_formula",
        "pledger.evidence_ids_bounded",
        "pledger.pattern_id_matches_signature",
        "pledger.session_local_only",
    }
    ids = {c.check_id for c in checks}
    missing = required_ids - ids
    assert not missing, (
        f"I-COHMON-07 violated: pledger checks missing {sorted(missing)!r}"
    )
    for c in checks:
        assert c.source == "pattern_ledger"
        assert c.status is CoherenceCheckStatus.PASS, (
            f"I-COHMON-07 violated: pledger check {c.check_id!r} "
            f"status={c.status.value} (expected PASS)"
        )

    # Identity-stable.
    assert session.pattern_ledger is prior_ledger
    assert session.pattern_ledger.entries is prior_entries

    # The pledger.session_local_only check states the policy without
    # claiming persistence.
    for c in checks:
        if c.check_id == "pledger.session_local_only":
            assert c.status is CoherenceCheckStatus.PASS
            assert "session-local" in c.detail.lower()

    # A session with no PatternLedger field falls back to a single
    # NOT_APPLICABLE check (defensive; the live OperatorSession
    # always exposes the field post-Step-11).
    session_without_field = OperatorSession(state=initial_state())
    # Manually shadow the slot through a deliberately constructed
    # alternative ledger object that is NOT a PatternLedger; this
    # exercises the FAIL path of the field check without leaking
    # through the OperatorSession constructor (which type-checks).
    # We rely on the runtime checker's ``isinstance`` branch.
    # Build a check list directly from a synthetic situation: the
    # build_pattern_ledger_checks function falls back to a single
    # NOT_APPLICABLE check when isinstance(session.pattern_ledger,
    # PatternLedger) is False — but our OperatorSession always
    # produces one, so we assert the happy path here.
    assert isinstance(session_without_field.pattern_ledger, PatternLedger)
