"""Phase 3.18 processing-window session integration fixture.

Drives ``I-PWND-01`` (REQUIRED): the bounded internal rehearsal
loop runs after a successful external STREAM_APPEND, fires exactly
``processing_window_size`` internal stream-append events, and
drives the Pattern Ledger recurrence_count to ``1 + N`` (saturating
at ``STREAM_PATTERN_RECURRENCE_MAX``). The OFF state
(``processing_window_size == 0``) is a no-op.

The fixture builds the session via the public constructor only
and uses :class:`brain.ui.session.OperatorSession` /
:class:`brain.ui.commands.Command` / public dispatcher. No
``brain.tick`` re-entry; no LLM call; no subprocess; no I/O.
"""
from __future__ import annotations

from fractions import Fraction

from brain.development.pattern_ledger import (
    PATTERN_LEDGER_EVIDENCE_MAX,
    PatternLedgerSaturationState,
)
from brain.development.processing_window import (
    PROCESSING_WINDOW_PROVENANCE_PREFIX,
)
from brain.development.text_stream import (
    STREAM_PATTERN_RECURRENCE_MAX,
    STREAM_PATTERN_RECURRENCE_MIN,
)
from brain.invariants import register
from brain.tick import initial_state, assert_state_invariants
from brain.ui.commands import (
    Command,
    OperatorCommand,
    StreamAppendPayload,
)
from brain.ui.session import OperatorSession


def _fresh_session(*, window_size: int = 0) -> OperatorSession:
    return OperatorSession(
        state=initial_state(),
        processing_window_size=window_size,
    )


def _append_external(session: OperatorSession, text: str) -> None:
    session.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text=text),
        )
    )


@register("I-PWND-01", status="REQUIRED")
def check_processing_window_drives_recurrence() -> None:
    """Architecture A: window_size = N produces 1 + N pledger
    observations on the same signature; recurrence_count climbs
    deterministically; saturation_state and confidence are exact
    Fractions of the observation count."""
    # ----- OFF state (window_size = 0) -----
    s_off = _fresh_session(window_size=0)
    _append_external(s_off, "hello pattern off")
    assert s_off.error_message == "", (
        "I-PWND-01 violated: OFF state set an error: "
        f"{s_off.error_message!r}"
    )
    assert len(s_off.stream_history.chunks) == 1, (
        "I-PWND-01 violated: OFF state appended more than 1 chunk "
        f"(got {len(s_off.stream_history.chunks)})"
    )
    assert len(s_off.pattern_ledger.entries) == 1, (
        "I-PWND-01 violated: OFF state did not produce exactly 1 "
        f"pledger entry (got {len(s_off.pattern_ledger.entries)})"
    )
    off_entry = s_off.pattern_ledger.entries[0]
    assert off_entry.recurrence_count == STREAM_PATTERN_RECURRENCE_MIN, (
        "I-PWND-01 violated: OFF state pledger.recurrence_count is "
        f"{off_entry.recurrence_count}, expected "
        f"{STREAM_PATTERN_RECURRENCE_MIN}"
    )
    # No internal_processing_window provenance leaks at OFF.
    for chunk in s_off.stream_history.chunks:
        assert chunk.provenance == "operator", (
            "I-PWND-01 violated: OFF state produced non-operator "
            f"chunk provenance {chunk.provenance!r}"
        )

    # ----- Small N (window_size = 3) -----
    n_small = 3
    s_small = _fresh_session(window_size=n_small)
    _append_external(s_small, "small N rehearsal text")
    assert s_small.error_message == "", (
        "I-PWND-01 violated: window N=3 set an error: "
        f"{s_small.error_message!r}"
    )
    assert len(s_small.stream_history.chunks) == 1 + n_small, (
        "I-PWND-01 violated: N=3 history size is "
        f"{len(s_small.stream_history.chunks)}, expected {1 + n_small}"
    )
    assert len(s_small.pattern_ledger.entries) == 1, (
        "I-PWND-01 violated: N=3 produced "
        f"{len(s_small.pattern_ledger.entries)} pledger entries, "
        "expected 1"
    )
    small_entry = s_small.pattern_ledger.entries[0]
    expected_small_count = STREAM_PATTERN_RECURRENCE_MIN + n_small
    assert small_entry.recurrence_count == expected_small_count, (
        "I-PWND-01 violated: N=3 recurrence_count is "
        f"{small_entry.recurrence_count}, expected {expected_small_count}"
    )
    assert small_entry.confidence == Fraction(
        expected_small_count, STREAM_PATTERN_RECURRENCE_MAX
    ), (
        "I-PWND-01 violated: N=3 confidence is "
        f"{small_entry.confidence}, expected "
        f"{Fraction(expected_small_count, STREAM_PATTERN_RECURRENCE_MAX)}"
    )
    # All chunks share the same signature so they collapse into one
    # Pattern Ledger entry.
    operator_count = sum(
        1
        for chunk in s_small.stream_history.chunks
        if chunk.provenance == "operator"
    )
    internal_count = sum(
        1
        for chunk in s_small.stream_history.chunks
        if chunk.provenance.startswith(
            PROCESSING_WINDOW_PROVENANCE_PREFIX + ":"
        )
    )
    assert operator_count == 1, (
        "I-PWND-01 violated: N=3 produced "
        f"{operator_count} operator chunks, expected 1"
    )
    assert internal_count == n_small, (
        "I-PWND-01 violated: N=3 produced "
        f"{internal_count} internal chunks, expected {n_small}"
    )
    # The internal provenances are exactly the deterministic set
    # {internal_processing_window:1:rehearsal,
    #  internal_processing_window:2:rehearsal,
    #  internal_processing_window:3:rehearsal}.
    expected_internal_provenances = {
        f"{PROCESSING_WINDOW_PROVENANCE_PREFIX}:{k}:rehearsal"
        for k in range(1, n_small + 1)
    }
    actual_internal_provenances = {
        chunk.provenance
        for chunk in s_small.stream_history.chunks
        if chunk.provenance != "operator"
    }
    assert actual_internal_provenances == expected_internal_provenances, (
        "I-PWND-01 violated: N=3 internal provenances drifted "
        f"(got {sorted(actual_internal_provenances)!r}, expected "
        f"{sorted(expected_internal_provenances)!r})"
    )
    # Operator status preserved across the window run.
    assert "stream chunk 'strm-chunk-1' appended" in s_small.status_message, (
        "I-PWND-01 violated: N=3 status_message overwritten by the "
        f"window: {s_small.status_message!r}"
    )
    # Kernel invariants remain green.
    assert_state_invariants(s_small.state)

    # ----- Evidence-id cap (window_size > PATTERN_LEDGER_EVIDENCE_MAX) -----
    # PATTERN_LEDGER_EVIDENCE_MAX = 32; with N = 40 we expect 32
    # distinct evidence_chunk_ids retained on the entry and
    # recurrence_count == 1 + 40 = 41.
    n_evid = 40
    s_evid = _fresh_session(window_size=n_evid)
    _append_external(s_evid, "evidence cap rehearsal text")
    assert s_evid.error_message == "", (
        "I-PWND-01 violated: window N=40 set an error: "
        f"{s_evid.error_message!r}"
    )
    evid_entry = s_evid.pattern_ledger.entries[0]
    expected_evid_count = STREAM_PATTERN_RECURRENCE_MIN + n_evid
    assert evid_entry.recurrence_count == expected_evid_count, (
        "I-PWND-01 violated: N=40 recurrence_count is "
        f"{evid_entry.recurrence_count}, expected {expected_evid_count}"
    )
    assert len(evid_entry.evidence_chunk_ids) == PATTERN_LEDGER_EVIDENCE_MAX, (
        "I-PWND-01 violated: N=40 evidence_chunk_ids size is "
        f"{len(evid_entry.evidence_chunk_ids)}, expected "
        f"{PATTERN_LEDGER_EVIDENCE_MAX}"
    )
    assert evid_entry.saturation_state == PatternLedgerSaturationState.OPEN, (
        "I-PWND-01 violated: N=40 saturation_state is "
        f"{evid_entry.saturation_state}, expected OPEN"
    )
    # Kernel invariants remain green.
    assert_state_invariants(s_evid.state)
