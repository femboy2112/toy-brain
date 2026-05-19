"""Phase 3.21 Developmental Trajectory milestone harness.

A bounded deterministic harness that exercises ten distinct
**structural** milestones against the public surfaces of
brain/development/ + brain/ui/session.py. Each milestone has one
pure helper that:

* constructs its own fresh ``OperatorSession(state=initial_state(), ...)``
  (no shared mutable state across helpers);
* dispatches a bounded canonical input sequence through the public
  ``STREAM_APPEND`` path;
* inspects the resulting session to compute the milestone's
  primary and secondary metrics;
* runs ``assert_state_invariants(session.state)``;
* runs the canonical non-claim audit over its produced summary
  string;
* returns a frozen :class:`MilestoneResult` record.

The module is a strict CONSUMER of existing public surfaces. It
does NOT modify any existing module's behavior. It does NOT
import ``brain.llm``, ``curses``, or any I/O / network / shell
surface. It does NOT call ``brain.tick.tick`` (only ``BrainState``
+ ``initial_state`` + ``assert_state_invariants`` are imported
from ``brain.tick`` for type / construction use).

Drives Phase 3.21 catalog rows ``I-DEVMILE-01..I-DEVMILE-11``.

The word "developmental" is used in its **operational** sense
(the runtime *develops a deterministic trajectory across the ten
milestones*), never in the psychological sense. ``PASS / WARN /
FAIL / NOT_APPLICABLE`` are structural status labels only.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from brain.development.coherence_monitor import (
    _FORBIDDEN_NON_CLAIM_TERMS,
    build_full_coherence_report,
)
from brain.development.growth_ledger import GROWTH_LEDGER_MAX_EVENTS
from brain.development.pattern_ledger import (
    derive_pattern_id,
    derive_pattern_signature,
)
from brain.development.processing_window import (
    PROCESSING_WINDOW_PROVENANCE_PREFIX,
    FeedbackMode,
)
from brain.development.text_stream import (
    STREAM_HISTORY_MAX_CHUNKS,
    STREAM_PATTERN_RECURRENCE_MAX,
    STREAM_PATTERN_RECURRENCE_MIN,
)
from brain.tick import (
    BrainState,
    assert_state_invariants,
    initial_state,
)
from brain.tlica.profile import COGITO_ID
from brain.ui.commands import (
    Command,
    OperatorCommand,
    StreamAppendPayload,
)
from brain.ui.session import OperatorSession


# ---------------------------------------------------------------------------
# Bounded constants
# ---------------------------------------------------------------------------


#: Maximum bounded printable length of a ``MilestoneResult.summary``.
MILESTONE_SUMMARY_MAX_LEN: int = 240


# ---------------------------------------------------------------------------
# Closed enums
# ---------------------------------------------------------------------------


class DevelopmentalMilestone(str, Enum):
    """Finite closed enumeration of the ten Phase 3.21 milestones.

    Ordered as the deterministic developmental trajectory of the
    runtime. Each member maps to one helper on this module.
    """

    M01_REFLEXIVE_BASELINE = "m01_reflexive_baseline"
    M02_HABITUATION = "m02_habituation"
    M03_RECOGNITION = "m03_recognition"
    M04_REHEARSAL = "m04_rehearsal"
    M05_PATTERN_SELF_FEEDBACK = "m05_pattern_self_feedback"
    M06_STRUCTURAL_SELF_MONITORING = "m06_structural_self_monitoring"
    M07_MULTI_MODAL_INTEGRATION = "m07_multi_modal_integration"
    M08_SATURATION_NOVELTY = "m08_saturation_novelty"
    M09_CROSS_INPUT_DIFFERENTIATION = "m09_cross_input_differentiation"
    M10_SUSTAINED_BEHAVIOR = "m10_sustained_behavior"


class MilestoneStatus(str, Enum):
    """Finite closed enumeration of per-milestone structural status
    labels. PASS / WARN / FAIL / NOT_APPLICABLE are structural
    labels only; they are not assertions about the running
    system.
    """

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


# ---------------------------------------------------------------------------
# Frozen / slotted milestone result record
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MilestoneResult:
    """Bounded printable per-milestone outcome record (I-DEVMILE-11).

    Fields are all bounded primitives. No callable / handle /
    client / file / socket / path appears here.
    """

    milestone: DevelopmentalMilestone
    status: MilestoneStatus
    summary: str
    primary_metric: int
    secondary_metric: int

    def __post_init__(self) -> None:
        if not isinstance(self.milestone, DevelopmentalMilestone):
            raise ValueError(
                "MilestoneResult.milestone must be a DevelopmentalMilestone "
                f"(got {type(self.milestone).__name__})"
            )
        if not isinstance(self.status, MilestoneStatus):
            raise ValueError(
                "MilestoneResult.status must be a MilestoneStatus "
                f"(got {type(self.status).__name__})"
            )
        if not isinstance(self.summary, str):
            raise ValueError(
                "MilestoneResult.summary must be str "
                f"(got {type(self.summary).__name__})"
            )
        if not self.summary:
            raise ValueError("MilestoneResult.summary must be non-empty")
        if not self.summary.isprintable():
            raise ValueError("MilestoneResult.summary must be printable")
        if len(self.summary) > MILESTONE_SUMMARY_MAX_LEN:
            raise ValueError(
                "MilestoneResult.summary length "
                f"{len(self.summary)} exceeds MILESTONE_SUMMARY_MAX_LEN="
                f"{MILESTONE_SUMMARY_MAX_LEN}"
            )
        if self.summary == COGITO_ID:
            raise ValueError(
                "MilestoneResult.summary must not equal COGITO_ID"
            )
        for field_name, value in (
            ("primary_metric", self.primary_metric),
            ("secondary_metric", self.secondary_metric),
        ):
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(
                    f"MilestoneResult.{field_name} must be int "
                    f"(got {type(value).__name__})"
                )
            if value < 0:
                raise ValueError(
                    f"MilestoneResult.{field_name} must be >= 0 "
                    f"(got {value})"
                )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _has_forbidden_term(text: str) -> Optional[str]:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


def _fresh_session(
    *,
    processing_window_size: int = 0,
    feedback_mode: FeedbackMode = FeedbackMode.OFF,
) -> OperatorSession:
    return OperatorSession(
        state=initial_state(),
        processing_window_size=processing_window_size,
        feedback_mode=feedback_mode,
    )


def _dispatch(session: OperatorSession, *, text: str) -> None:
    session.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text=text),
        )
    )


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


def _entries_with_evidence_provenance_suffix(
    session: OperatorSession, *, suffix: str
) -> list:
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


def _seed_text(prefix: str, seed_offset: int) -> str:
    if not isinstance(seed_offset, int) or isinstance(seed_offset, bool):
        raise ValueError(
            f"milestone_harness: seed_offset must be int "
            f"(got {type(seed_offset).__name__})"
        )
    if seed_offset < 0:
        raise ValueError(
            f"milestone_harness: seed_offset must be >= 0 (got {seed_offset})"
        )
    return f"{prefix}-{seed_offset}"


def _build_result(
    *,
    milestone: DevelopmentalMilestone,
    status: MilestoneStatus,
    summary: str,
    primary_metric: int,
    secondary_metric: int,
) -> MilestoneResult:
    term = _has_forbidden_term(summary)
    if term is not None:
        raise ValueError(
            f"milestone_harness: summary {summary!r} contains "
            f"forbidden non-claim term {term!r}"
        )
    return MilestoneResult(
        milestone=milestone,
        status=status,
        summary=summary,
        primary_metric=primary_metric,
        secondary_metric=secondary_metric,
    )


def _expected_seed_recurrence(n: int) -> int:
    raw = STREAM_PATTERN_RECURRENCE_MIN + n
    if raw > STREAM_PATTERN_RECURRENCE_MAX:
        return STREAM_PATTERN_RECURRENCE_MAX
    return raw


# ---------------------------------------------------------------------------
# Per-milestone helpers
# ---------------------------------------------------------------------------


def run_m01_reflexive_baseline(
    *, seed_offset: int = 0
) -> MilestoneResult:
    """M01 — Reflexive baseline.

    Single STREAM_APPEND with no window and no feedback. The
    bounded substrate produces 1 chunk + 1 Pattern Ledger entry
    whose recurrence_count == STREAM_PATTERN_RECURRENCE_MIN.
    """
    session = _fresh_session()
    _dispatch(session, text=_seed_text("alpha", seed_offset))
    chunks = len(session.stream_history.chunks)
    entries = len(session.pattern_ledger.entries)
    rec = (
        session.pattern_ledger.entries[0].recurrence_count
        if session.pattern_ledger.entries
        else -1
    )
    invariants_ok = True
    try:
        assert_state_invariants(session.state)
    except Exception:
        invariants_ok = False
    ok = (
        chunks == 1
        and entries == 1
        and rec == STREAM_PATTERN_RECURRENCE_MIN
        and invariants_ok
    )
    status = MilestoneStatus.PASS if ok else MilestoneStatus.FAIL
    summary = (
        f"m01 reflexive_baseline chunks={chunks} entries={entries} rec={rec}"
    )
    return _build_result(
        milestone=DevelopmentalMilestone.M01_REFLEXIVE_BASELINE,
        status=status,
        summary=summary,
        primary_metric=chunks,
        secondary_metric=entries,
    )


def run_m02_habituation(*, seed_offset: int = 0) -> MilestoneResult:
    """M02 — Habituation. Repeated STREAM_APPEND with N=10
    rehearsals; recurrence climbs by exactly N."""
    n = 10
    session = _fresh_session(processing_window_size=n)
    _dispatch(session, text=_seed_text("beta", seed_offset))
    chunks = len(session.stream_history.chunks)
    entries = len(session.pattern_ledger.entries)
    rec = (
        session.pattern_ledger.entries[0].recurrence_count
        if session.pattern_ledger.entries
        else -1
    )
    sat = (
        session.pattern_ledger.entries[0].saturation_state.value
        if session.pattern_ledger.entries
        else ""
    )
    invariants_ok = True
    try:
        assert_state_invariants(session.state)
    except Exception:
        invariants_ok = False
    ok = (
        chunks == 1 + n
        and entries == 1
        and rec == _expected_seed_recurrence(n)
        and sat == "open"
        and invariants_ok
    )
    status = MilestoneStatus.PASS if ok else MilestoneStatus.FAIL
    summary = (
        f"m02 habituation chunks={chunks} entries={entries} "
        f"rec={rec} sat={sat}"
    )
    return _build_result(
        milestone=DevelopmentalMilestone.M02_HABITUATION,
        status=status,
        summary=summary,
        primary_metric=chunks,
        secondary_metric=rec,
    )


def run_m03_recognition(*, seed_offset: int = 0) -> MilestoneResult:
    """M03 — Recognition. Two distinct seeds produce two distinct
    Pattern Ledger entries with distinct pattern_ids."""
    session = _fresh_session()
    _dispatch(session, text=_seed_text("gamma", seed_offset))
    _dispatch(session, text=_seed_text("delta", seed_offset))
    chunks = len(session.stream_history.chunks)
    entries = len(session.pattern_ledger.entries)
    distinct_ids = len({e.pattern_id for e in session.pattern_ledger.entries})
    invariants_ok = True
    try:
        assert_state_invariants(session.state)
    except Exception:
        invariants_ok = False
    ok = (
        chunks == 2
        and entries == 2
        and distinct_ids == 2
        and invariants_ok
    )
    status = MilestoneStatus.PASS if ok else MilestoneStatus.FAIL
    summary = (
        f"m03 recognition chunks={chunks} entries={entries} "
        f"distinct_ids={distinct_ids}"
    )
    return _build_result(
        milestone=DevelopmentalMilestone.M03_RECOGNITION,
        status=status,
        summary=summary,
        primary_metric=entries,
        secondary_metric=distinct_ids,
    )


def run_m04_rehearsal(*, seed_offset: int = 0) -> MilestoneResult:
    """M04 — Rehearsal. Processing window N=10 under OFF; N
    rehearsal-provenance chunks plus the operator chunk."""
    n = 10
    session = _fresh_session(processing_window_size=n)
    _dispatch(session, text=_seed_text("epsilon", seed_offset))
    chunks = len(session.stream_history.chunks)
    rehearsal_chunks = _count_provenance_with_suffix(
        session, suffix="rehearsal"
    )
    rec = (
        session.pattern_ledger.entries[0].recurrence_count
        if session.pattern_ledger.entries
        else -1
    )
    invariants_ok = True
    try:
        assert_state_invariants(session.state)
    except Exception:
        invariants_ok = False
    ok = (
        chunks == 1 + n
        and rehearsal_chunks == n
        and rec == _expected_seed_recurrence(n)
        and invariants_ok
    )
    status = MilestoneStatus.PASS if ok else MilestoneStatus.FAIL
    summary = (
        f"m04 rehearsal chunks={chunks} "
        f"rehearsal_chunks={rehearsal_chunks} rec={rec}"
    )
    return _build_result(
        milestone=DevelopmentalMilestone.M04_REHEARSAL,
        status=status,
        summary=summary,
        primary_metric=rehearsal_chunks,
        secondary_metric=rec,
    )


def run_m05_pattern_self_feedback(
    *, seed_offset: int = 0
) -> MilestoneResult:
    """M05 — Pattern self-feedback. PATTERN_LEDGER mode at N=10;
    1 + 2N chunks; pledger-family observation sum equals N."""
    n = 10
    session = _fresh_session(
        processing_window_size=n,
        feedback_mode=FeedbackMode.PATTERN_LEDGER,
    )
    _dispatch(session, text=_seed_text("zeta", seed_offset))
    chunks = len(session.stream_history.chunks)
    pledger_chunks = _count_provenance_with_suffix(
        session, suffix="pledger_summary"
    )
    entries = len(session.pattern_ledger.entries)
    pledger_family = _entries_with_evidence_provenance_suffix(
        session, suffix="pledger_summary"
    )
    obs_sum = sum(
        e.recurrence_count - STREAM_PATTERN_RECURRENCE_MIN + 1
        for e in pledger_family
    )
    invariants_ok = True
    try:
        assert_state_invariants(session.state)
    except Exception:
        invariants_ok = False
    ok = (
        chunks == 1 + 2 * n
        and pledger_chunks == n
        and entries >= 2
        and obs_sum == n
        and invariants_ok
    )
    status = MilestoneStatus.PASS if ok else MilestoneStatus.FAIL
    summary = (
        f"m05 pattern_self_feedback chunks={chunks} "
        f"pledger={pledger_chunks} entries={entries}"
    )
    return _build_result(
        milestone=DevelopmentalMilestone.M05_PATTERN_SELF_FEEDBACK,
        status=status,
        summary=summary,
        primary_metric=pledger_chunks,
        secondary_metric=entries,
    )


def run_m06_structural_self_monitoring(
    *, seed_offset: int = 0
) -> MilestoneResult:
    """M06 — Structural self-monitoring approximation. COHERENCE
    mode at N=10; 1 + 2N chunks; cohmon-family observation sum
    equals N; post-dispatch CoherenceReport overall_status is in
    the closed set."""
    n = 10
    session = _fresh_session(
        processing_window_size=n,
        feedback_mode=FeedbackMode.COHERENCE,
    )
    _dispatch(session, text=_seed_text("eta", seed_offset))
    chunks = len(session.stream_history.chunks)
    cohmon_chunks = _count_provenance_with_suffix(
        session, suffix="cohmon_summary"
    )
    entries = len(session.pattern_ledger.entries)
    cohmon_family = _entries_with_evidence_provenance_suffix(
        session, suffix="cohmon_summary"
    )
    obs_sum = sum(
        e.recurrence_count - STREAM_PATTERN_RECURRENCE_MIN + 1
        for e in cohmon_family
    )
    report = build_full_coherence_report(session, snapshot_id="m06-probe")
    overall = report.overall_status.value
    invariants_ok = True
    try:
        assert_state_invariants(session.state)
    except Exception:
        invariants_ok = False
    ok = (
        chunks == 1 + 2 * n
        and cohmon_chunks == n
        and entries >= 2
        and obs_sum == n
        and overall in {"pass", "warn", "fail", "not_applicable"}
        and invariants_ok
    )
    status = MilestoneStatus.PASS if ok else MilestoneStatus.FAIL
    summary = (
        f"m06 structural_self_monitoring chunks={chunks} "
        f"cohmon={cohmon_chunks} entries={entries} overall={overall}"
    )
    return _build_result(
        milestone=DevelopmentalMilestone.M06_STRUCTURAL_SELF_MONITORING,
        status=status,
        summary=summary,
        primary_metric=cohmon_chunks,
        secondary_metric=entries,
    )


def run_m07_multi_modal_integration(
    *, seed_offset: int = 0
) -> MilestoneResult:
    """M07 — Multi-modal integration. PATTERN_AND_COHERENCE at N=10;
    1 + 3N chunks; both family observation sums equal N
    independently; pledger and cohmon families disjoint."""
    n = 10
    session = _fresh_session(
        processing_window_size=n,
        feedback_mode=FeedbackMode.PATTERN_AND_COHERENCE,
    )
    _dispatch(session, text=_seed_text("theta", seed_offset))
    chunks = len(session.stream_history.chunks)
    rehearsal_chunks = _count_provenance_with_suffix(
        session, suffix="rehearsal"
    )
    pledger_chunks = _count_provenance_with_suffix(
        session, suffix="pledger_summary"
    )
    cohmon_chunks = _count_provenance_with_suffix(
        session, suffix="cohmon_summary"
    )
    entries = len(session.pattern_ledger.entries)
    pledger_family = _entries_with_evidence_provenance_suffix(
        session, suffix="pledger_summary"
    )
    cohmon_family = _entries_with_evidence_provenance_suffix(
        session, suffix="cohmon_summary"
    )
    pledger_obs = sum(
        e.recurrence_count - STREAM_PATTERN_RECURRENCE_MIN + 1
        for e in pledger_family
    )
    cohmon_obs = sum(
        e.recurrence_count - STREAM_PATTERN_RECURRENCE_MIN + 1
        for e in cohmon_family
    )
    pledger_ids = {e.pattern_id for e in pledger_family}
    cohmon_ids = {e.pattern_id for e in cohmon_family}
    disjoint = not (pledger_ids & cohmon_ids)
    invariants_ok = True
    try:
        assert_state_invariants(session.state)
    except Exception:
        invariants_ok = False
    ok = (
        chunks == 1 + 3 * n
        and rehearsal_chunks == n
        and pledger_chunks == n
        and cohmon_chunks == n
        and entries >= 3
        and pledger_obs == n
        and cohmon_obs == n
        and disjoint
        and invariants_ok
    )
    status = MilestoneStatus.PASS if ok else MilestoneStatus.FAIL
    summary = (
        f"m07 multi_modal_integration chunks={chunks} entries={entries}"
    )
    return _build_result(
        milestone=DevelopmentalMilestone.M07_MULTI_MODAL_INTEGRATION,
        status=status,
        summary=summary,
        primary_metric=chunks,
        secondary_metric=entries,
    )


def run_m08_saturation_novelty(
    *, seed_offset: int = 0
) -> MilestoneResult:
    """M08 — Saturation + novelty. Saturating input drives seed
    entry to SATURATED; a subsequent distinct input still creates
    a new entry."""
    session = _fresh_session(processing_window_size=255)
    _dispatch(session, text=_seed_text("iota", seed_offset))
    # Second dispatch with no window to add a single distinct chunk.
    session2 = OperatorSession(
        state=session.state,
        latest_tick=session.latest_tick,
        output_history=session.output_history,
        worldlet_history=session.worldlet_history,
        repl_history=session.repl_history,
        event_queue=session.event_queue,
        active_view=session.active_view,
        status_message=session.status_message,
        error_message=session.error_message,
        quit_flag=session.quit_flag,
        tick_counter=session.tick_counter,
        stream_history=session.stream_history,
        stream_candidates=session.stream_candidates,
        stream_chunk_serial=session.stream_chunk_serial,
        session_store_config=session.session_store_config,
        autosave_config=session.autosave_config,
        last_autosave_status=session.last_autosave_status,
        pattern_ledger=session.pattern_ledger,
        growth_ledger=session.growth_ledger,
        processing_window_size=0,
        processing_window_call_budget=session.processing_window_call_budget,
        feedback_mode=FeedbackMode.OFF,
    )
    _dispatch(session2, text=_seed_text("kappa", seed_offset))
    seed_entry = session2.pattern_ledger.entries[0]
    seed_sat = seed_entry.saturation_state.value
    seed_rec = seed_entry.recurrence_count
    entries = len(session2.pattern_ledger.entries)
    invariants_ok = True
    try:
        assert_state_invariants(session2.state)
    except Exception:
        invariants_ok = False
    ok = (
        seed_sat == "saturated"
        and seed_rec == STREAM_PATTERN_RECURRENCE_MAX
        and entries == 2
        and session2.pattern_ledger.entries[1].recurrence_count
        == STREAM_PATTERN_RECURRENCE_MIN
        and invariants_ok
    )
    status = MilestoneStatus.PASS if ok else MilestoneStatus.FAIL
    summary = (
        f"m08 saturation_novelty seed_sat={seed_sat} entries={entries} "
        f"seed_rec={seed_rec}"
    )
    return _build_result(
        milestone=DevelopmentalMilestone.M08_SATURATION_NOVELTY,
        status=status,
        summary=summary,
        primary_metric=1 if seed_sat == "saturated" else 0,
        secondary_metric=entries,
    )


def run_m09_cross_input_differentiation(
    *, seed_offset: int = 0
) -> MilestoneResult:
    """M09 — Cross-input differentiation under feedback. Two
    distinct inputs each under PATTERN_AND_COHERENCE at N=10
    produce pairwise-disjoint second-order families; entry counts
    add deterministically."""
    n = 10
    session = _fresh_session(
        processing_window_size=n,
        feedback_mode=FeedbackMode.PATTERN_AND_COHERENCE,
    )
    _dispatch(session, text=_seed_text("lambda", seed_offset))
    _dispatch(session, text=_seed_text("mu", seed_offset))
    chunks = len(session.stream_history.chunks)
    entries = len(session.pattern_ledger.entries)
    distinct_ids = len({e.pattern_id for e in session.pattern_ledger.entries})
    invariants_ok = True
    try:
        assert_state_invariants(session.state)
    except Exception:
        invariants_ok = False
    ok = (
        chunks == 2 * (1 + 3 * n)
        and entries >= 4
        and distinct_ids == entries
        and invariants_ok
    )
    status = MilestoneStatus.PASS if ok else MilestoneStatus.FAIL
    summary = (
        f"m09 cross_input_differentiation chunks={chunks} "
        f"entries={entries} distinct={distinct_ids}"
    )
    return _build_result(
        milestone=DevelopmentalMilestone.M09_CROSS_INPUT_DIFFERENTIATION,
        status=status,
        summary=summary,
        primary_metric=entries,
        secondary_metric=distinct_ids,
    )


def run_m10_sustained_behavior(
    *, seed_offset: int = 0
) -> MilestoneResult:
    """M10 — Sustained complex behavior. Three distinct inputs
    each under PATTERN_AND_COHERENCE at N=50 dispatch
    3 * (1 + 3*50) = 453 chunks total. The stream history is
    bounded by STREAM_HISTORY_MAX_CHUNKS = 256 and the growth
    ledger is bounded by GROWTH_LEDGER_MAX_EVENTS = 256 — under
    sustained load both substrates correctly saturate at their
    caps without eviction (no chunk silently disappears beyond
    the documented bound). Invariants stay green throughout.

    Success criterion (LOCK J / PHASE3_21_TEN_MILESTONES.md
    Section 10): chunks observed in stream_history must equal
    the substrate-bounded value
    ``min(expected_dispatched, STREAM_HISTORY_MAX_CHUNKS)``;
    growth events must be bounded by ``GROWTH_LEDGER_MAX_EVENTS``;
    at least 3 pattern entries must exist (one per distinct
    input seed); ``assert_state_invariants`` must stay green
    after every dispatch.
    """
    n = 50
    session = _fresh_session(
        processing_window_size=n,
        feedback_mode=FeedbackMode.PATTERN_AND_COHERENCE,
    )
    invariants_ok = True
    for prefix in ("nu", "xi", "omicron"):
        _dispatch(session, text=_seed_text(prefix, seed_offset))
        try:
            assert_state_invariants(session.state)
        except Exception:
            invariants_ok = False
            break
    chunks = len(session.stream_history.chunks)
    growth = len(session.growth_ledger.events)
    entries = len(session.pattern_ledger.entries)
    expected_dispatched = 3 * (1 + 3 * n)
    expected_stored = min(expected_dispatched, STREAM_HISTORY_MAX_CHUNKS)
    ok = (
        chunks == expected_stored
        and growth <= GROWTH_LEDGER_MAX_EVENTS
        and entries >= 3
        and invariants_ok
    )
    status = MilestoneStatus.PASS if ok else MilestoneStatus.FAIL
    summary = (
        f"m10 sustained_behavior chunks={chunks}/{STREAM_HISTORY_MAX_CHUNKS} "
        f"growth={growth}/{GROWTH_LEDGER_MAX_EVENTS} entries={entries}"
    )
    return _build_result(
        milestone=DevelopmentalMilestone.M10_SUSTAINED_BEHAVIOR,
        status=status,
        summary=summary,
        primary_metric=chunks,
        secondary_metric=growth,
    )


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------


def run_all_milestones() -> tuple[MilestoneResult, ...]:
    """Run the ten milestones in order and return the tuple."""
    return (
        run_m01_reflexive_baseline(),
        run_m02_habituation(),
        run_m03_recognition(),
        run_m04_rehearsal(),
        run_m05_pattern_self_feedback(),
        run_m06_structural_self_monitoring(),
        run_m07_multi_modal_integration(),
        run_m08_saturation_novelty(),
        run_m09_cross_input_differentiation(),
        run_m10_sustained_behavior(),
    )


# ---------------------------------------------------------------------------
# Module-level non-claim audit surface
# ---------------------------------------------------------------------------


#: Every bounded printable string this module produces must avoid
#: every term in ``_FORBIDDEN_NON_CLAIM_TERMS``. The static-audit
#: fixture imports this tuple and scans it plus the module source.
MODULE_PRODUCED_STRINGS: tuple[str, ...] = (
    *(m.value for m in DevelopmentalMilestone),
    *(s.value for s in MilestoneStatus),
)


__all__ = [
    "DevelopmentalMilestone",
    "MILESTONE_SUMMARY_MAX_LEN",
    "MODULE_PRODUCED_STRINGS",
    "MilestoneResult",
    "MilestoneStatus",
    "run_all_milestones",
    "run_m01_reflexive_baseline",
    "run_m02_habituation",
    "run_m03_recognition",
    "run_m04_rehearsal",
    "run_m05_pattern_self_feedback",
    "run_m06_structural_self_monitoring",
    "run_m07_multi_modal_integration",
    "run_m08_saturation_novelty",
    "run_m09_cross_input_differentiation",
    "run_m10_sustained_behavior",
]
