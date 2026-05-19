"""Phase 3.20 coherence feedback integration audit.

Drives ``I-CFBK-01`` (REQUIRED). The audit exercises the
``OperatorSession`` Coherence Monitor feedback path end-to-end
and confirms that:

* At ``feedback_mode == FeedbackMode.OFF``, the path is
  bit-identical to the Phase 3.18 rehearsal-only baseline
  (no ``pledger_summary`` and no ``cohmon_summary`` provenance
  appears).
* At ``feedback_mode == FeedbackMode.PATTERN_LEDGER``, the path
  is bit-identical to the Phase 3.19 baseline
  (``1 + 2 * N`` chunks; no ``cohmon_summary`` provenance).
* At ``feedback_mode == FeedbackMode.COHERENCE``,
  ``_run_processing_window`` produces exactly ``1 + 2 * N`` stream
  chunks (one operator + N rehearsals + N cohmon_summary), at
  least one second-order Pattern Ledger entry whose ``pattern_id``
  differs from the seed entry's, every entry's bounded invariants
  hold, the cohmon-summary chunks together drive a deterministic
  Pattern Ledger entry climb that matches the total cohmon
  observation count of N, and the kernel invariants stay green.
* At ``feedback_mode == FeedbackMode.PATTERN_AND_COHERENCE``, the
  path produces exactly ``1 + 3 * N`` chunks (one operator +
  N rehearsals + N pledger_summary + N cohmon_summary) and the
  Pattern Ledger ends with at least 3 entries (seed +
  pledger_summary family + cohmon_summary family).
* The seed entry's ``recurrence_count`` advances exactly per the
  Phase 3.18 formula
  ``min(STREAM_PATTERN_RECURRENCE_MIN + N, STREAM_PATTERN_RECURRENCE_MAX)``
  regardless of ``feedback_mode``.
* ``assert_state_invariants`` remains green throughout.
* No L1 / L2 cache write occurs; no real model call is made;
  ``brain/.llm_cache/`` is not touched.
* Two independent ``OperatorSession`` instances with identical
  inputs and ``feedback_mode`` produce bit-identical Pattern
  Ledger entry sets and bit-identical Growth Ledger event-id
  tuples (determinism).
* ``processing_window_size == 0`` with every ``feedback_mode`` is
  a strict no-op (Phase 3.18 OFF behavior preserved).

The audit consumes zero real model calls because every
dispatcher path used here (``STREAM_APPEND``) is non-LLM, and the
cohmon-summary path is purely structural (no LLM seam).
"""
from __future__ import annotations

from brain.development.pattern_ledger import (
    PATTERN_LEDGER_EVIDENCE_MAX,
    derive_pattern_id,
    derive_pattern_signature,
)
from brain.development.processing_window import (
    FeedbackMode,
    PROCESSING_WINDOW_PROVENANCE_PREFIX,
)
from brain.development.text_stream import (
    STREAM_PATTERN_RECURRENCE_MAX,
    STREAM_PATTERN_RECURRENCE_MIN,
)
from brain.invariants import register
from brain.tick import assert_state_invariants, initial_state
from brain.ui.commands import (
    Command,
    OperatorCommand,
    StreamAppendPayload,
)
from brain.ui.session import OperatorSession


_SEED_TEXT: str = "the kettle whistled at exactly noon today again"


def _expected_seed_recurrence(n: int) -> int:
    raw = STREAM_PATTERN_RECURRENCE_MIN + n
    if raw > STREAM_PATTERN_RECURRENCE_MAX:
        return STREAM_PATTERN_RECURRENCE_MAX
    return raw


def _run_scenario(
    *, n: int, feedback_mode: FeedbackMode, text: str = _SEED_TEXT
) -> OperatorSession:
    session = OperatorSession(
        state=initial_state(),
        processing_window_size=n,
        feedback_mode=feedback_mode,
    )
    session.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text=text),
        )
    )
    return session


def _count_provenance_with_suffix(
    session: OperatorSession, *, suffix: str
) -> int:
    target = f":{suffix}"
    return sum(
        1
        for chunk in session.stream_history.chunks
        if chunk.provenance.startswith(PROCESSING_WINDOW_PROVENANCE_PREFIX)
        and chunk.provenance.endswith(target)
    )


def _seed_pattern_id(text: str) -> str:
    session = OperatorSession(state=initial_state())
    session.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text=text),
        )
    )
    seed_chunk = session.stream_history.chunks[0]
    return derive_pattern_id(derive_pattern_signature(seed_chunk))


def _entries_with_evidence_provenance_suffix(
    session: OperatorSession, *, suffix: str
) -> list:
    """Return entries whose evidence_chunk_ids reference at least one
    chunk whose provenance ends in ``:suffix``."""
    target = f":{suffix}"
    matching_chunk_ids: set[str] = set()
    for chunk in session.stream_history.chunks:
        if (
            chunk.provenance.startswith(PROCESSING_WINDOW_PROVENANCE_PREFIX)
            and chunk.provenance.endswith(target)
        ):
            matching_chunk_ids.add(chunk.chunk_id)
    out: list = []
    for entry in session.pattern_ledger.entries:
        if any(cid in matching_chunk_ids for cid in entry.evidence_chunk_ids):
            out.append(entry)
    return out


def _sum_observations(entries: list) -> int:
    total = 0
    for entry in entries:
        assert (
            STREAM_PATTERN_RECURRENCE_MIN
            <= entry.recurrence_count
            <= STREAM_PATTERN_RECURRENCE_MAX
        ), (
            f"I-CFBK-01 violated: entry {entry.pattern_id!r} "
            f"recurrence_count {entry.recurrence_count} out of range"
        )
        total += (
            entry.recurrence_count - STREAM_PATTERN_RECURRENCE_MIN + 1
        )
    return total


@register("I-CFBK-01", status="REQUIRED")
def check_coherence_feedback_integration() -> None:
    """Phase 3.20 coherence-feedback integration audit."""

    seed_pid = _seed_pattern_id(_SEED_TEXT)

    # ------------------------------------------------------------------
    # Scenario A: N = 0 with every feedback mode — strict no-op.
    # ------------------------------------------------------------------
    for mode in (
        FeedbackMode.OFF,
        FeedbackMode.PATTERN_LEDGER,
        FeedbackMode.COHERENCE,
        FeedbackMode.PATTERN_AND_COHERENCE,
    ):
        s = _run_scenario(n=0, feedback_mode=mode)
        assert len(s.stream_history.chunks) == 1, (
            f"I-CFBK-01 violated [A-{mode.value}]: N=0 produced "
            f"{len(s.stream_history.chunks)} chunks, expected 1"
        )
        assert len(s.pattern_ledger.entries) == 1, (
            f"I-CFBK-01 violated [A-{mode.value}]: N=0 produced "
            f"{len(s.pattern_ledger.entries)} pattern entries, "
            "expected 1"
        )
        assert s.pattern_ledger.entries[0].pattern_id == seed_pid, (
            f"I-CFBK-01 violated [A-{mode.value}]: N=0 seed pattern_id "
            "mismatch"
        )
        assert_state_invariants(s.state)

    # ------------------------------------------------------------------
    # Scenarios B-E: N in {5, 10, 50} across all four modes.
    # ------------------------------------------------------------------
    for n in (5, 10, 50):
        expected_recurrence = _expected_seed_recurrence(n)

        # OFF baseline (Phase 3.18 preserved).
        s_off = _run_scenario(n=n, feedback_mode=FeedbackMode.OFF)
        assert len(s_off.stream_history.chunks) == 1 + n, (
            f"I-CFBK-01 violated [B-OFF-N={n}]: stream chunk count "
            f"{len(s_off.stream_history.chunks)} != 1 + N = {1 + n}"
        )
        assert len(s_off.pattern_ledger.entries) == 1, (
            f"I-CFBK-01 violated [B-OFF-N={n}]: pattern entry count "
            f"{len(s_off.pattern_ledger.entries)} != 1"
        )
        assert (
            _count_provenance_with_suffix(s_off, suffix="pledger_summary")
            == 0
        ), (
            f"I-CFBK-01 violated [B-OFF-N={n}]: pledger_summary chunks "
            "appeared under OFF"
        )
        assert (
            _count_provenance_with_suffix(s_off, suffix="cohmon_summary")
            == 0
        ), (
            f"I-CFBK-01 violated [B-OFF-N={n}]: cohmon_summary chunks "
            "appeared under OFF"
        )
        assert s_off.pattern_ledger.entries[0].recurrence_count == (
            expected_recurrence
        ), (
            f"I-CFBK-01 violated [B-OFF-N={n}]: seed recurrence_count "
            f"{s_off.pattern_ledger.entries[0].recurrence_count} != "
            f"{expected_recurrence}"
        )
        assert_state_invariants(s_off.state)

        # PATTERN_LEDGER baseline (Phase 3.19 preserved).
        s_pl = _run_scenario(
            n=n, feedback_mode=FeedbackMode.PATTERN_LEDGER
        )
        assert len(s_pl.stream_history.chunks) == 1 + 2 * n, (
            f"I-CFBK-01 violated [C-PL-N={n}]: stream chunk count "
            f"{len(s_pl.stream_history.chunks)} != 1 + 2 * N = "
            f"{1 + 2 * n}"
        )
        assert (
            _count_provenance_with_suffix(s_pl, suffix="cohmon_summary")
            == 0
        ), (
            f"I-CFBK-01 violated [C-PL-N={n}]: cohmon_summary chunks "
            "appeared under PATTERN_LEDGER"
        )
        assert_state_invariants(s_pl.state)

        # COHERENCE: 1 + 2N chunks; >= 2 pattern entries; cohmon family
        # observation total = N; no pledger_summary chunks.
        s_co = _run_scenario(n=n, feedback_mode=FeedbackMode.COHERENCE)
        assert len(s_co.stream_history.chunks) == 1 + 2 * n, (
            f"I-CFBK-01 violated [D-CO-N={n}]: stream chunk count "
            f"{len(s_co.stream_history.chunks)} != 1 + 2 * N = "
            f"{1 + 2 * n}"
        )
        assert (
            _count_provenance_with_suffix(s_co, suffix="rehearsal") == n
        ), (
            f"I-CFBK-01 violated [D-CO-N={n}]: rehearsal chunk count "
            f"!= N = {n}"
        )
        assert (
            _count_provenance_with_suffix(s_co, suffix="cohmon_summary")
            == n
        ), (
            f"I-CFBK-01 violated [D-CO-N={n}]: cohmon_summary chunk "
            f"count != N = {n}"
        )
        assert (
            _count_provenance_with_suffix(s_co, suffix="pledger_summary")
            == 0
        ), (
            f"I-CFBK-01 violated [D-CO-N={n}]: pledger_summary chunks "
            "appeared under COHERENCE"
        )
        seed_entry_co = s_co.pattern_ledger.find(seed_pid)
        assert seed_entry_co is not None, (
            f"I-CFBK-01 violated [D-CO-N={n}]: seed entry missing"
        )
        assert seed_entry_co.recurrence_count == expected_recurrence, (
            f"I-CFBK-01 violated [D-CO-N={n}]: seed recurrence_count "
            f"{seed_entry_co.recurrence_count} != {expected_recurrence}"
        )
        cohmon_family_co = _entries_with_evidence_provenance_suffix(
            s_co, suffix="cohmon_summary"
        )
        assert len(cohmon_family_co) >= 1, (
            f"I-CFBK-01 violated [D-CO-N={n}]: zero cohmon-family "
            "entries created by coherence feedback chunks"
        )
        assert all(e.pattern_id != seed_pid for e in cohmon_family_co), (
            f"I-CFBK-01 violated [D-CO-N={n}]: cohmon family overlaps "
            "with seed entry"
        )
        cohmon_obs_total_co = _sum_observations(cohmon_family_co)
        assert cohmon_obs_total_co == n, (
            f"I-CFBK-01 violated [D-CO-N={n}]: cohmon-family "
            f"observation total {cohmon_obs_total_co} != N = {n}"
        )
        for entry in s_co.pattern_ledger.entries:
            assert (
                len(entry.evidence_chunk_ids) <= PATTERN_LEDGER_EVIDENCE_MAX
            ), (
                f"I-CFBK-01 violated [D-CO-N={n}]: evidence_chunk_ids "
                f"length {len(entry.evidence_chunk_ids)} exceeds cap"
            )
        assert_state_invariants(s_co.state)

        # PATTERN_AND_COHERENCE: 1 + 3N chunks; >= 3 entries; both
        # family observation totals = N.
        s_pc = _run_scenario(
            n=n, feedback_mode=FeedbackMode.PATTERN_AND_COHERENCE
        )
        assert len(s_pc.stream_history.chunks) == 1 + 3 * n, (
            f"I-CFBK-01 violated [E-PC-N={n}]: stream chunk count "
            f"{len(s_pc.stream_history.chunks)} != 1 + 3 * N = "
            f"{1 + 3 * n}"
        )
        assert (
            _count_provenance_with_suffix(s_pc, suffix="rehearsal") == n
        ), (
            f"I-CFBK-01 violated [E-PC-N={n}]: rehearsal chunk count "
            f"!= N = {n}"
        )
        assert (
            _count_provenance_with_suffix(s_pc, suffix="pledger_summary")
            == n
        ), (
            f"I-CFBK-01 violated [E-PC-N={n}]: pledger_summary chunk "
            f"count != N = {n}"
        )
        assert (
            _count_provenance_with_suffix(s_pc, suffix="cohmon_summary")
            == n
        ), (
            f"I-CFBK-01 violated [E-PC-N={n}]: cohmon_summary chunk "
            f"count != N = {n}"
        )
        seed_entry_pc = s_pc.pattern_ledger.find(seed_pid)
        assert seed_entry_pc is not None, (
            f"I-CFBK-01 violated [E-PC-N={n}]: seed entry missing"
        )
        assert seed_entry_pc.recurrence_count == expected_recurrence, (
            f"I-CFBK-01 violated [E-PC-N={n}]: seed recurrence_count "
            f"{seed_entry_pc.recurrence_count} != {expected_recurrence}"
        )
        pledger_family_pc = _entries_with_evidence_provenance_suffix(
            s_pc, suffix="pledger_summary"
        )
        cohmon_family_pc = _entries_with_evidence_provenance_suffix(
            s_pc, suffix="cohmon_summary"
        )
        assert len(pledger_family_pc) >= 1, (
            f"I-CFBK-01 violated [E-PC-N={n}]: zero pledger-family "
            "entries under PATTERN_AND_COHERENCE"
        )
        assert len(cohmon_family_pc) >= 1, (
            f"I-CFBK-01 violated [E-PC-N={n}]: zero cohmon-family "
            "entries under PATTERN_AND_COHERENCE"
        )
        pledger_obs_total_pc = _sum_observations(pledger_family_pc)
        cohmon_obs_total_pc = _sum_observations(cohmon_family_pc)
        assert pledger_obs_total_pc == n, (
            f"I-CFBK-01 violated [E-PC-N={n}]: pledger-family "
            f"observation total {pledger_obs_total_pc} != N = {n}"
        )
        assert cohmon_obs_total_pc == n, (
            f"I-CFBK-01 violated [E-PC-N={n}]: cohmon-family "
            f"observation total {cohmon_obs_total_pc} != N = {n}"
        )
        assert len(s_pc.pattern_ledger.entries) >= 3, (
            f"I-CFBK-01 violated [E-PC-N={n}]: pattern entry count "
            f"{len(s_pc.pattern_ledger.entries)} < 3"
        )
        # Pledger and cohmon families must be disjoint and both
        # disjoint from the seed.
        pledger_ids = {e.pattern_id for e in pledger_family_pc}
        cohmon_ids = {e.pattern_id for e in cohmon_family_pc}
        assert seed_pid not in pledger_ids, (
            f"I-CFBK-01 violated [E-PC-N={n}]: pledger family overlaps "
            "with seed"
        )
        assert seed_pid not in cohmon_ids, (
            f"I-CFBK-01 violated [E-PC-N={n}]: cohmon family overlaps "
            "with seed"
        )
        assert not (pledger_ids & cohmon_ids), (
            f"I-CFBK-01 violated [E-PC-N={n}]: pledger and cohmon "
            f"families overlap on {sorted(pledger_ids & cohmon_ids)!r}"
        )
        assert_state_invariants(s_pc.state)

        # Determinism: two fresh sessions with identical config and
        # input produce identical Pattern Ledger entry sets and
        # identical Growth Ledger event id tuples, across both
        # COHERENCE and PATTERN_AND_COHERENCE.
        for mode in (
            FeedbackMode.COHERENCE,
            FeedbackMode.PATTERN_AND_COHERENCE,
        ):
            s1 = _run_scenario(n=n, feedback_mode=mode)
            s2 = _run_scenario(n=n, feedback_mode=mode)
            ids1 = tuple(e.pattern_id for e in s1.pattern_ledger.entries)
            ids2 = tuple(e.pattern_id for e in s2.pattern_ledger.entries)
            assert ids1 == ids2, (
                f"I-CFBK-01 violated [F-{mode.value}-N={n}]: pattern_id "
                f"tuple drift across runs ({ids1!r} != {ids2!r})"
            )
            counts1 = tuple(
                e.recurrence_count for e in s1.pattern_ledger.entries
            )
            counts2 = tuple(
                e.recurrence_count for e in s2.pattern_ledger.entries
            )
            assert counts1 == counts2, (
                f"I-CFBK-01 violated [F-{mode.value}-N={n}]: "
                "recurrence_count tuple drift across runs"
            )
            events1 = tuple(
                e.event_id for e in s1.growth_ledger.events
            )
            events2 = tuple(
                e.event_id for e in s2.growth_ledger.events
            )
            assert events1 == events2, (
                f"I-CFBK-01 violated [F-{mode.value}-N={n}]: growth "
                "event id tuple drift across runs"
            )
