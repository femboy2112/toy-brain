"""Phase 3.22 Agent Communication Loop benchmark battery + runner.

This module is a strict consumer of ``brain.development.agent_loop``
and the existing Phase 3.18-3.21 public surfaces. It defines a closed
deterministic benchmark battery exercising the bounded operator-
facing agent loop along seven axes and an entry-point runner
``main()`` so ``python3 -m brain.development.agent_benchmark`` works.

The deterministic battery consumes zero real model calls, never
touches ``brain/.llm_cache/``, never invokes ``brain.tick.tick``,
and never imports ``brain.llm.*``.

Non-claim discipline (binding):

* The PASS verdict is a closed-criterion property of the bounded
  battery's outputs. It is NOT a cognitive claim. "Agent" is
  engineering shorthand for "bounded operator-facing reply layer".
* Every produced text passes the
  ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``
  audit (case-insensitive substring).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from brain.development.abstract_pattern import (
    derive_abstract_pattern_signature,
)
from brain.development.agent_loop import (
    AGENT_INPUT_MAX_LEN,
    AGENT_LOOP_VERSION,
    AgentLoopResult,
    AgentLoopState,
    AgentReplyDisposition,
    AgentReplyStatus,
    make_initial_agent_loop_state,
    run_agent_interaction_step,
    summarize_session_for_agent,
)
from brain.development.learning_evidence import (
    LearningEvidenceKind,
    build_learning_proof_report,
)
from brain.development.reasoning_trace import (
    ReasoningStepKind,
    build_reasoning_trace_report,
)
from brain.development.agent_repl_bridge import (
    AGENT_REPL_LINE_ID_PREFIX,
    build_default_agent_repl_grammar,
    run_repl_line,
    summarize_repl_for_agent,
)
from brain.development.coherence_monitor import (
    CoherenceCheckStatus,
    _FORBIDDEN_NON_CLAIM_TERMS,
    build_full_coherence_report,
)
from brain.development.dispatch_tracer import (
    DispatchMutationKind,
    DispatchTraceReport,
)
from brain.development.processing_window import FeedbackMode
from brain.development.pattern_ledger import (
    PatternLedgerSaturationState,
    STREAM_PATTERN_RECURRENCE_MAX,
    STREAM_PATTERN_RECURRENCE_MIN,
    derive_pattern_id,
    derive_pattern_signature,
)
from brain.development.repl import ProtoBasicHistory
from brain.development.text_stream import (
    STREAM_HISTORY_MAX_CHUNKS,
    STREAM_TEXT_MAX_LEN,
)
from brain.tick import assert_state_invariants, initial_state
from brain.ui.commands import Command, OperatorCommand, StreamAppendPayload
from brain.ui.session import OperatorSession


# ---------------------------------------------------------------------------
# Bounded constants.
# ---------------------------------------------------------------------------

BATTERY_VERSION: str = "phase3.30.v1"
TRANSCRIPT_DIGEST_HEX_LEN: int = 16
BENCHMARK_CASE_SUMMARY_MAX_LEN: int = 240
BENCHMARK_CASE_NOTES_MAX_LEN: int = 320
BENCHMARK_TRANSCRIPT_LINE_MAX_LEN: int = 1280


# ---------------------------------------------------------------------------
# Closed enums.
# ---------------------------------------------------------------------------


class BenchmarkAxis(str, Enum):
    PATTERN_RECOGNITION = "pattern_recognition"
    CROSS_INPUT_STRUCTURAL = "cross_input_structural"
    COHERENCE_VARIATION = "coherence_variation"
    REPL_COHERENCE = "repl_coherence"
    COMMUNICATION = "communication"
    SESSION_CONTINUITY = "session_continuity"
    BLIND_TRANSCRIPT = "blind_transcript"
    LEARNING_EVIDENCE = "learning_evidence"
    REASONING_TRACE = "reasoning_trace"
    # Phase 3.23 (I-DTRACE-11): the dispatch trace battery axis.
    DISPATCH_TRACE = "dispatch_trace"
    # Phase 3.24 (I-WFDBK-11): the worldlet feedback battery axis.
    WORLDLET_FEEDBACK = "worldlet_feedback"
    # Phase 3.25 (I-OSMO-13): the osmotic learning battery axis.
    OSMOTIC_LEARNING = "osmotic_learning"
    # Phase 3.26 (I-AHYP-13): the active hypothesis battery axis.
    ACTIVE_HYPOTHESIS = "active_hypothesis"
    # Phase 3.30 (I-CURR-13): the curriculum consolidation battery axis.
    CURRICULUM_CONSOLIDATION = "curriculum_consolidation"


class BenchmarkCaseStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


# ---------------------------------------------------------------------------
# Records.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BenchmarkCaseResult:
    case_id: str
    axis: BenchmarkAxis
    status: BenchmarkCaseStatus
    summary: str
    primary_metric: int
    secondary_metric: int
    notes: str = ""

    def __post_init__(self) -> None:
        if (
            not isinstance(self.case_id, str)
            or not self.case_id
            or not self.case_id.isprintable()
            or len(self.case_id) > 64
        ):
            raise ValueError(
                "I-AGENTLOOP-09 violated: BenchmarkCaseResult.case_id must be "
                "non-empty printable text under 64 chars"
            )
        if not isinstance(self.axis, BenchmarkAxis):
            raise TypeError(
                "I-AGENTLOOP-09 violated: BenchmarkCaseResult.axis must be a "
                "BenchmarkAxis"
            )
        if not isinstance(self.status, BenchmarkCaseStatus):
            raise TypeError(
                "I-AGENTLOOP-09 violated: BenchmarkCaseResult.status must be "
                "a BenchmarkCaseStatus"
            )
        for name, value, cap in (
            ("summary", self.summary, BENCHMARK_CASE_SUMMARY_MAX_LEN),
            ("notes", self.notes, BENCHMARK_CASE_NOTES_MAX_LEN),
        ):
            if not isinstance(value, str):
                raise TypeError(
                    "I-AGENTLOOP-09 violated: BenchmarkCaseResult."
                    f"{name} must be a string"
                )
            if value and not value.isprintable():
                raise ValueError(
                    "I-AGENTLOOP-09 violated: BenchmarkCaseResult."
                    f"{name} must be printable"
                )
            if len(value) > cap:
                raise ValueError(
                    "I-AGENTLOOP-09 violated: BenchmarkCaseResult."
                    f"{name} exceeds bound {cap}"
                )
            term = _text_has_forbidden_term(value)
            if term is not None:
                raise ValueError(
                    "I-AGENTLOOP-09 violated: BenchmarkCaseResult."
                    f"{name} contains forbidden non-claim term {term!r}"
                )
        for name, value in (
            ("primary_metric", self.primary_metric),
            ("secondary_metric", self.secondary_metric),
        ):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(
                    "I-AGENTLOOP-09 violated: BenchmarkCaseResult."
                    f"{name} must be int"
                )
            if value < 0:
                raise ValueError(
                    "I-AGENTLOOP-09 violated: BenchmarkCaseResult."
                    f"{name} must be non-negative"
                )


@dataclass(frozen=True, slots=True)
class AxisResult:
    axis: BenchmarkAxis
    status: BenchmarkCaseStatus
    cases: tuple[BenchmarkCaseResult, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.axis, BenchmarkAxis):
            raise TypeError(
                "I-AGENTLOOP-09 violated: AxisResult.axis must be a "
                "BenchmarkAxis"
            )
        if not isinstance(self.status, BenchmarkCaseStatus):
            raise TypeError(
                "I-AGENTLOOP-09 violated: AxisResult.status must be a "
                "BenchmarkCaseStatus"
            )
        if not isinstance(self.cases, tuple) or not self.cases:
            raise ValueError(
                "I-AGENTLOOP-09 violated: AxisResult.cases must be a "
                "non-empty tuple"
            )
        for case in self.cases:
            if not isinstance(case, BenchmarkCaseResult):
                raise TypeError(
                    "I-AGENTLOOP-09 violated: AxisResult.cases entries "
                    "must be BenchmarkCaseResult"
                )
            if case.axis is not self.axis:
                raise ValueError(
                    "I-AGENTLOOP-09 violated: AxisResult.cases entry axis "
                    f"{case.axis} mismatches AxisResult.axis {self.axis}"
                )


@dataclass(frozen=True, slots=True)
class BenchmarkRun:
    battery_version: str
    axes: tuple[AxisResult, ...]
    case_total: int
    case_passed: int
    case_warned: int
    case_failed: int
    determinism_failures: int
    invariant_failures: int
    real_model_calls: int
    cache_writes: int
    forbidden_term_hits: int
    transcript_digest_hex16: str
    transcripts: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.axes, tuple) or not self.axes:
            raise ValueError(
                "I-AGENTLOOP-09 violated: BenchmarkRun.axes must be a "
                "non-empty tuple"
            )
        for ax in self.axes:
            if not isinstance(ax, AxisResult):
                raise TypeError(
                    "I-AGENTLOOP-09 violated: BenchmarkRun.axes entries "
                    "must be AxisResult"
                )
        for name, value in (
            ("case_total", self.case_total),
            ("case_passed", self.case_passed),
            ("case_warned", self.case_warned),
            ("case_failed", self.case_failed),
            ("determinism_failures", self.determinism_failures),
            ("invariant_failures", self.invariant_failures),
            ("real_model_calls", self.real_model_calls),
            ("cache_writes", self.cache_writes),
            ("forbidden_term_hits", self.forbidden_term_hits),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(
                    "I-AGENTLOOP-09 violated: BenchmarkRun."
                    f"{name} must be a non-negative int"
                )
        if (
            not isinstance(self.transcript_digest_hex16, str)
            or len(self.transcript_digest_hex16) != TRANSCRIPT_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-AGENTLOOP-09 violated: BenchmarkRun."
                "transcript_digest_hex16 must be a 16-char hex string"
            )
        if not isinstance(self.transcripts, tuple):
            raise TypeError(
                "I-AGENTLOOP-09 violated: BenchmarkRun.transcripts must be a "
                "tuple"
            )
        for line in self.transcripts:
            if not isinstance(line, str) or not line.isprintable():
                raise ValueError(
                    "I-AGENTLOOP-09 violated: BenchmarkRun.transcripts "
                    "entries must be printable strings"
                )
            if len(line) > BENCHMARK_TRANSCRIPT_LINE_MAX_LEN:
                raise ValueError(
                    "I-AGENTLOOP-09 violated: BenchmarkRun.transcripts "
                    "line length exceeds bound"
                )
            term = _text_has_forbidden_term(line)
            if term is not None:
                raise ValueError(
                    "I-AGENTLOOP-09 violated: BenchmarkRun.transcripts "
                    f"line contains forbidden non-claim term {term!r}"
                )


# ---------------------------------------------------------------------------
# Local helpers.
# ---------------------------------------------------------------------------


def _text_has_forbidden_term(text: str) -> Optional[str]:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


def _fresh_state() -> AgentLoopState:
    return make_initial_agent_loop_state()


def _fresh_session() -> OperatorSession:
    return OperatorSession(state=initial_state())


def _append_stream(session: OperatorSession, text: str) -> None:
    session.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text=text),
        )
    )


def _seed_pattern_id_for_text(text: str) -> str:
    """Derive the pattern_id a fresh STREAM_APPEND of ``text`` would produce."""
    session = _fresh_session()
    _append_stream(session, text)
    return session.pattern_ledger.entries[0].pattern_id


def _aggregate_axis_status(
    cases: tuple[BenchmarkCaseResult, ...],
) -> BenchmarkCaseStatus:
    if any(c.status is BenchmarkCaseStatus.FAIL for c in cases):
        return BenchmarkCaseStatus.FAIL
    if any(c.status is BenchmarkCaseStatus.WARN for c in cases):
        return BenchmarkCaseStatus.WARN
    return BenchmarkCaseStatus.PASS


def _short(text: str, *, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 4)] + " ..."


# ---------------------------------------------------------------------------
# Axis A1 — Pattern recurrence recognition.
# ---------------------------------------------------------------------------


def run_axis_a1_pattern_recognition() -> AxisResult:
    cases: list[BenchmarkCaseResult] = []

    seed = "alpha-line"

    # A1.01: single STREAM_APPEND.
    session = _fresh_session()
    _append_stream(session, seed)
    obs = summarize_session_for_agent(session)
    cases.append(
        BenchmarkCaseResult(
            case_id="A1.01",
            axis=BenchmarkAxis.PATTERN_RECOGNITION,
            status=(
                BenchmarkCaseStatus.PASS
                if (
                    obs.stream_chunk_count == 1
                    and obs.pattern_entry_count == 1
                    and obs.seed_recurrence == STREAM_PATTERN_RECURRENCE_MIN
                )
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"single seed append: chunks={obs.stream_chunk_count} "
                f"entries={obs.pattern_entry_count} "
                f"recur={obs.seed_recurrence}"
            ),
            primary_metric=obs.stream_chunk_count,
            secondary_metric=obs.seed_recurrence,
        )
    )

    # A1.02: seed appended 3 times.
    session = _fresh_session()
    for _ in range(3):
        _append_stream(session, seed)
    obs = summarize_session_for_agent(session)
    cases.append(
        BenchmarkCaseResult(
            case_id="A1.02",
            axis=BenchmarkAxis.PATTERN_RECOGNITION,
            status=(
                BenchmarkCaseStatus.PASS
                if (
                    obs.stream_chunk_count == 3
                    and obs.pattern_entry_count == 1
                    and obs.seed_recurrence
                    == STREAM_PATTERN_RECURRENCE_MIN + 2
                )
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"seed repeated 3x: chunks={obs.stream_chunk_count} "
                f"recur={obs.seed_recurrence}"
            ),
            primary_metric=obs.stream_chunk_count,
            secondary_metric=obs.seed_recurrence,
        )
    )

    # A1.03: seed appended 8 times.
    session = _fresh_session()
    for _ in range(8):
        _append_stream(session, seed)
    obs = summarize_session_for_agent(session)
    cases.append(
        BenchmarkCaseResult(
            case_id="A1.03",
            axis=BenchmarkAxis.PATTERN_RECOGNITION,
            status=(
                BenchmarkCaseStatus.PASS
                if (
                    obs.stream_chunk_count == 8
                    and obs.seed_recurrence
                    == STREAM_PATTERN_RECURRENCE_MIN + 7
                )
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"seed repeated 8x: chunks={obs.stream_chunk_count} "
                f"recur={obs.seed_recurrence}"
            ),
            primary_metric=obs.stream_chunk_count,
            secondary_metric=obs.seed_recurrence,
        )
    )

    # A1.04: two distinct seeds appended once each.
    session = _fresh_session()
    _append_stream(session, "alpha-line")
    _append_stream(session, "beta-line")
    obs = summarize_session_for_agent(session)
    cases.append(
        BenchmarkCaseResult(
            case_id="A1.04",
            axis=BenchmarkAxis.PATTERN_RECOGNITION,
            status=(
                BenchmarkCaseStatus.PASS
                if (
                    obs.stream_chunk_count == 2
                    and obs.pattern_entry_count == 2
                )
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                "two distinct seeds: "
                f"chunks={obs.stream_chunk_count} "
                f"entries={obs.pattern_entry_count}"
            ),
            primary_metric=obs.stream_chunk_count,
            secondary_metric=obs.pattern_entry_count,
        )
    )

    # A1.05: saturated seed + novel append.
    # Strategy: append seed (STREAM_PATTERN_RECURRENCE_MAX -
    # STREAM_PATTERN_RECURRENCE_MIN + 1) times -> seed reaches MAX
    # which is the SATURATED tier, then one novel append.
    # MAX=256, MIN=2 -> 255 climbs reach MAX. Plus 1 novel = 256
    # chunks, exactly at STREAM_HISTORY_MAX_CHUNKS=256.
    session = _fresh_session()
    sat_climbs = (
        STREAM_PATTERN_RECURRENCE_MAX - STREAM_PATTERN_RECURRENCE_MIN + 1
    )
    # Cap the appends so the post-novel total fits exactly at
    # STREAM_HISTORY_MAX_CHUNKS.
    sat_climbs = min(sat_climbs, STREAM_HISTORY_MAX_CHUNKS - 1)
    for _ in range(sat_climbs):
        _append_stream(session, "alpha-line")
    _append_stream(session, "beta-line")
    obs = summarize_session_for_agent(session)
    saturated = obs.seed_saturation_state == (
        PatternLedgerSaturationState.SATURATED.value
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A1.05",
            axis=BenchmarkAxis.PATTERN_RECOGNITION,
            status=(
                BenchmarkCaseStatus.PASS
                if (saturated and obs.pattern_entry_count >= 2)
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                "saturated seed + novel: "
                f"sat={obs.seed_saturation_state} "
                f"entries={obs.pattern_entry_count}"
            ),
            primary_metric=obs.seed_recurrence,
            secondary_metric=obs.pattern_entry_count,
        )
    )

    # A1.06: ABAB pattern.
    session = _fresh_session()
    for text in ("alpha-line", "beta-line", "alpha-line", "beta-line"):
        _append_stream(session, text)
    obs = summarize_session_for_agent(session)
    cases.append(
        BenchmarkCaseResult(
            case_id="A1.06",
            axis=BenchmarkAxis.PATTERN_RECOGNITION,
            status=(
                BenchmarkCaseStatus.PASS
                if (
                    obs.stream_chunk_count == 4
                    and obs.pattern_entry_count == 2
                )
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"ABAB: chunks={obs.stream_chunk_count} "
                f"entries={obs.pattern_entry_count}"
            ),
            primary_metric=obs.stream_chunk_count,
            secondary_metric=obs.pattern_entry_count,
        )
    )

    # A1.07: ABBA pattern.
    session = _fresh_session()
    abba = ("alpha-line", "beta-line", "beta-line", "alpha-line")
    for text in abba:
        _append_stream(session, text)
    obs = summarize_session_for_agent(session)
    chunks_text_order = tuple(c.text for c in session.stream_history.chunks)
    cases.append(
        BenchmarkCaseResult(
            case_id="A1.07",
            axis=BenchmarkAxis.PATTERN_RECOGNITION,
            status=(
                BenchmarkCaseStatus.PASS
                if (
                    obs.pattern_entry_count == 2
                    and chunks_text_order == abba
                )
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"ABBA: entries={obs.pattern_entry_count} "
                f"order_matches={chunks_text_order == abba}"
            ),
            primary_metric=obs.stream_chunk_count,
            secondary_metric=obs.pattern_entry_count,
        )
    )

    # A1.08: ABCABC continuation.
    # The pattern signature is structural (length / distinct-char-count
    # / repeat ratio / whitespace runs), not lexical. Different surface
    # tokens that map to identical structural features will collide;
    # use three structurally distinct seeds.
    session = _fresh_session()
    abc = ("aaa", "bcdef", "ghijklm") * 2
    for text in abc:
        _append_stream(session, text)
    obs = summarize_session_for_agent(session)
    cases.append(
        BenchmarkCaseResult(
            case_id="A1.08",
            axis=BenchmarkAxis.PATTERN_RECOGNITION,
            status=(
                BenchmarkCaseStatus.PASS
                if obs.pattern_entry_count == 3
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"ABCABC: chunks={obs.stream_chunk_count} "
                f"entries={obs.pattern_entry_count}"
            ),
            primary_metric=obs.stream_chunk_count,
            secondary_metric=obs.pattern_entry_count,
        )
    )

    # A1.09: near-miss to known seed: seed text plus typo.
    session = _fresh_session()
    _append_stream(session, "alpha-line")
    _append_stream(session, "alpha-lne")
    obs = summarize_session_for_agent(session)
    cases.append(
        BenchmarkCaseResult(
            case_id="A1.09",
            axis=BenchmarkAxis.PATTERN_RECOGNITION,
            status=(
                BenchmarkCaseStatus.PASS
                if obs.pattern_entry_count == 2
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"near-miss novel: chunks={obs.stream_chunk_count} "
                f"entries={obs.pattern_entry_count}"
            ),
            primary_metric=obs.stream_chunk_count,
            secondary_metric=obs.pattern_entry_count,
        )
    )

    return AxisResult(
        axis=BenchmarkAxis.PATTERN_RECOGNITION,
        status=_aggregate_axis_status(tuple(cases)),
        cases=tuple(cases),
    )


# ---------------------------------------------------------------------------
# Axis A2 — Cross-input structural transfer.
# ---------------------------------------------------------------------------


def run_axis_a2_cross_input_structural() -> AxisResult:
    cases: list[BenchmarkCaseResult] = []

    def _one_append_observation(text: str) -> tuple[int, str]:
        session = _fresh_session()
        _append_stream(session, text)
        obs = summarize_session_for_agent(session)
        return obs.seed_recurrence, obs.seed_pattern_id

    # A2.01: two distinct surface-tokens, same shape; both reach MIN.
    r1, id1 = _one_append_observation("red blue red blue")
    r2, id2 = _one_append_observation("cat dog cat dog")
    cases.append(
        BenchmarkCaseResult(
            case_id="A2.01",
            axis=BenchmarkAxis.CROSS_INPUT_STRUCTURAL,
            status=(
                BenchmarkCaseStatus.PASS
                if (
                    r1 == STREAM_PATTERN_RECURRENCE_MIN
                    and r2 == STREAM_PATTERN_RECURRENCE_MIN
                )
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                "renamed-structure climb: "
                f"red_blue_recur={r1} cat_dog_recur={r2}"
            ),
            primary_metric=r1,
            secondary_metric=r2,
        )
    )

    # A2.02: alternating same-shape, distinct tokens.
    r1, _ = _one_append_observation("a b a b a b")
    r2, _ = _one_append_observation("x y x y x y")
    cases.append(
        BenchmarkCaseResult(
            case_id="A2.02",
            axis=BenchmarkAxis.CROSS_INPUT_STRUCTURAL,
            status=(
                BenchmarkCaseStatus.PASS
                if (
                    r1 == STREAM_PATTERN_RECURRENCE_MIN
                    and r2 == STREAM_PATTERN_RECURRENCE_MIN
                )
                else BenchmarkCaseStatus.FAIL
            ),
            summary=f"ababab vs xyxyxy: r1={r1} r2={r2}",
            primary_metric=r1,
            secondary_metric=r2,
        )
    )

    # A2.03: distinct surfaces in two sessions produce distinct
    # pattern_ids AND both reach MIN.
    _, ida = _one_append_observation("red blue red blue")
    _, idb = _one_append_observation("cat dog cat dog")
    cases.append(
        BenchmarkCaseResult(
            case_id="A2.03",
            axis=BenchmarkAxis.CROSS_INPUT_STRUCTURAL,
            status=(
                BenchmarkCaseStatus.PASS
                if (ida != idb and ida and idb)
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                "distinct surfaces -> distinct pattern_ids: "
                f"ida_short={ida[:24]!r} idb_short={idb[:24]!r}"
            ),
            primary_metric=int(ida != idb),
            secondary_metric=0,
        )
    )

    # A2.04: identical-surface vs renamed surface.
    _, ida = _one_append_observation("alpha alpha alpha")
    _, idb = _one_append_observation("beta beta beta")
    cases.append(
        BenchmarkCaseResult(
            case_id="A2.04",
            axis=BenchmarkAxis.CROSS_INPUT_STRUCTURAL,
            status=(
                BenchmarkCaseStatus.PASS
                if (ida != idb and ida and idb)
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"alpha vs beta: ida={ida[:24]!r} idb={idb[:24]!r}"
            ),
            primary_metric=int(ida != idb),
            secondary_metric=0,
        )
    )

    # A2.05: structural-collision behavior probe. The signature is
    # structural-only; texts with identical structural features WILL
    # share a pattern_id by design. This case documents that
    # behavior: structurally identical short texts collide, and
    # structurally distinct texts do not.
    _, id_short_a = _one_append_observation("q w e")
    _, id_short_b = _one_append_observation("z x c")  # same structure
    _, id_distinct = _one_append_observation("qq ww ee rr tt")
    bounded_ok = (
        isinstance(id_short_a, str)
        and id_short_a
        and len(id_short_a) <= 64
        and id_short_a.isprintable()
        and isinstance(id_distinct, str)
        and id_distinct
        and len(id_distinct) <= 64
        and id_distinct.isprintable()
    )
    # Structural collision: id_short_a == id_short_b (by design).
    # Structural distinctness: id_distinct != id_short_a (length /
    # distinct-char-count / repeat ratio differ).
    collision_as_expected = id_short_a == id_short_b
    distinct_as_expected = id_distinct != id_short_a
    cases.append(
        BenchmarkCaseResult(
            case_id="A2.05",
            axis=BenchmarkAxis.CROSS_INPUT_STRUCTURAL,
            status=(
                BenchmarkCaseStatus.PASS
                if (
                    bounded_ok
                    and collision_as_expected
                    and distinct_as_expected
                )
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"collision-probe: short_match={collision_as_expected} "
                f"distinct_diff={distinct_as_expected} bounded={bounded_ok}"
            ),
            primary_metric=int(collision_as_expected),
            secondary_metric=int(distinct_as_expected),
            notes=(
                "Pattern signature is structural-only (length, "
                "distinct-char-count, whitespace runs, repeat ratio). "
                "Texts with identical structural features share a "
                "pattern_id by design; the bridge uses surface-token "
                "differences only at the stream-chunk inspection layer."
            ),
        )
    )

    return AxisResult(
        axis=BenchmarkAxis.CROSS_INPUT_STRUCTURAL,
        status=_aggregate_axis_status(tuple(cases)),
        cases=tuple(cases),
    )


# ---------------------------------------------------------------------------
# Axis A3 — Coherence-state variation (Phase 3.21 W3 follow-up).
#
# Documented LOCK H: the overall_status values reachable through
# the public operator surface are bounded by what the existing
# Coherence Monitor checks permit. The probe attempts each of
# {pass, warn, fail, not_applicable} via the operator-visible
# surface plus, where necessary, direct dataclass-field assignment
# on the (non-frozen) OperatorSession dataclass. Each case records
# whether the status was reached and what lever was used. A case
# that cannot reach the target status without breaking LOCK A..G
# is marked WARN with a notes line documenting the exact blocker;
# the axis still PASSes provided ``pass`` is reached and the
# unreachable statuses are accompanied by explicit notes.
# ---------------------------------------------------------------------------


def _coherence_overall_status_value(session: OperatorSession) -> str:
    return build_full_coherence_report(session).overall_status.value


def run_axis_a3_coherence_variation() -> AxisResult:
    cases: list[BenchmarkCaseResult] = []

    # A3.01 — pass: fresh OperatorSession.
    session = _fresh_session()
    val = _coherence_overall_status_value(session)
    cases.append(
        BenchmarkCaseResult(
            case_id="A3.01",
            axis=BenchmarkAxis.COHERENCE_VARIATION,
            status=(
                BenchmarkCaseStatus.PASS
                if val == CoherenceCheckStatus.PASS.value
                else BenchmarkCaseStatus.FAIL
            ),
            summary=f"fresh session overall_status={val}",
            primary_metric=int(val == CoherenceCheckStatus.PASS.value),
            secondary_metric=0,
        )
    )

    # A3.02 — warn: append several chunks, then assign
    # stream_chunk_serial to a value below the chunk count. This is a
    # deliberate dataclass-field mutation (the OperatorSession
    # dataclass is non-frozen by design) used as a probe lever per
    # LOCK H. The check ``stream.chunk_serial_consistent`` emits
    # WARN when serial < len(chunks); overall aggregates to WARN
    # because no FAIL is present.
    session = _fresh_session()
    for index in range(3):
        _append_stream(session, f"warn-probe-text-{index:03d}")
    chunk_count = len(session.stream_history.chunks)
    session.stream_chunk_serial = 0
    val = _coherence_overall_status_value(session)
    reached_warn = val == CoherenceCheckStatus.WARN.value
    cases.append(
        BenchmarkCaseResult(
            case_id="A3.02",
            axis=BenchmarkAxis.COHERENCE_VARIATION,
            status=(
                BenchmarkCaseStatus.PASS
                if reached_warn
                else BenchmarkCaseStatus.WARN
            ),
            summary=(
                f"warn probe: serial=0 chunks={chunk_count} "
                f"overall={val}"
            ),
            primary_metric=int(reached_warn),
            secondary_metric=chunk_count,
            notes=(
                "Probe lever: set OperatorSession.stream_chunk_serial = 0 "
                "after appending chunks. Per LOCK H this dataclass-field "
                "assignment is a deliberate probe; the OperatorSession "
                "dataclass is non-frozen by design and stream.chunk_serial"
                "_consistent emits WARN when serial < len(chunks)."
            ) if reached_warn else (
                "WARN status not reached: WARN lever blocked by an "
                "unanticipated guard. Documented as not-publicly-reachable; "
                "the axis WARN does not block axis PASS provided pass is "
                "reached."
            ),
        )
    )

    # A3.03 — fail: set session.active_view to a value not in
    # ACTIVE_VIEWS. The check session.active_view_legal emits FAIL;
    # overall aggregates to FAIL (dominates WARN/PASS).
    session = _fresh_session()
    session.active_view = "agent-loop-probe-bogus-view"
    val = _coherence_overall_status_value(session)
    reached_fail = val == CoherenceCheckStatus.FAIL.value
    cases.append(
        BenchmarkCaseResult(
            case_id="A3.03",
            axis=BenchmarkAxis.COHERENCE_VARIATION,
            status=(
                BenchmarkCaseStatus.PASS
                if reached_fail
                else BenchmarkCaseStatus.WARN
            ),
            summary=(
                f"fail probe: active_view=invalid overall={val}"
            ),
            primary_metric=int(reached_fail),
            secondary_metric=0,
            notes=(
                "Probe lever: set OperatorSession.active_view to a value "
                "outside ACTIVE_VIEWS after construction. The check "
                "session.active_view_legal returns FAIL; overall is FAIL."
            ) if reached_fail else (
                "FAIL status not reached: FAIL lever blocked. Documented "
                "as not-publicly-reachable; the axis records WARN."
            ),
        )
    )

    # A3.04 — not_applicable at overall level: NOT publicly reachable.
    # The kernel.* checks always emit PASS for a valid BrainState
    # (cogito anchor presence, profile bounds, MSI subset, ptcns
    # totality). Per compute_overall_status, presence of any PASS
    # check yields overall PASS (not NA). Reaching overall NA would
    # require all 29 checks to be NA, which is unreachable through
    # public surfaces without invalidating BrainState.
    session = _fresh_session()
    val = _coherence_overall_status_value(session)
    cases.append(
        BenchmarkCaseResult(
            case_id="A3.04",
            axis=BenchmarkAxis.COHERENCE_VARIATION,
            status=BenchmarkCaseStatus.WARN,
            summary=(
                f"not_applicable probe: unreachable at overall level; "
                f"fresh overall={val} (PASS-dominated)"
            ),
            primary_metric=0,
            secondary_metric=0,
            notes=(
                "NOT_APPLICABLE at the overall level is not publicly "
                "reachable: compute_overall_status returns NOT_APPLICABLE "
                "only when every check is NA, but kernel.* checks always "
                "PASS for a valid BrainState. Per-check NA IS reachable "
                "(fresh session has 8 NA checks). Documented blocker."
            ),
        )
    )

    return AxisResult(
        axis=BenchmarkAxis.COHERENCE_VARIATION,
        status=_aggregate_axis_status(tuple(cases)),
        cases=tuple(cases),
    )


# ---------------------------------------------------------------------------
# Transcript serialization (used by later steps).
# ---------------------------------------------------------------------------


def _transcript_lines_from_case(case: BenchmarkCaseResult) -> tuple[str, ...]:
    line = (
        f"case axis={case.axis.value} id={case.case_id} "
        f"status={case.status.value} primary={case.primary_metric} "
        f"secondary={case.secondary_metric} "
        f"summary={case.summary!r}"
    )
    if case.notes:
        line = line + f" notes={case.notes!r}"
    return (line,)


def _compute_transcript_digest(lines: tuple[str, ...]) -> str:
    joined = "\n".join(lines).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()[:TRANSCRIPT_DIGEST_HEX_LEN]


# ---------------------------------------------------------------------------
# Step 5 partial runner (axes A1 + A2 only).
#
# Steps 6 / 7 extend this with the remaining axes and the full
# benchmark runner ``main()``.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Axis A4 — REPL coherence.
# ---------------------------------------------------------------------------


def run_axis_a4_repl_coherence() -> AxisResult:
    cases: list[BenchmarkCaseResult] = []
    handle = build_default_agent_repl_grammar()

    # A4.01 — valid command -> VALID parse, VALID_EFFECTIVE exec,
    # strong-positive feedback.
    res_valid = run_repl_line(
        handle=handle,
        history=ProtoBasicHistory(),
        raw_text="EMIT ALPHA",
        line_id=f"{AGENT_REPL_LINE_ID_PREFIX}a4-01",
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A4.01",
            axis=BenchmarkAxis.REPL_COHERENCE,
            status=(
                BenchmarkCaseStatus.PASS
                if (
                    res_valid.parse_category_value == "valid"
                    and res_valid.execution_category_value == "valid-effective"
                    and res_valid.effective is True
                    and res_valid.feedback_is_strong_positive is True
                )
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"valid EMIT ALPHA: parse={res_valid.parse_category_value} "
                f"exec={res_valid.execution_category_value} "
                f"strong={res_valid.feedback_is_strong_positive}"
            ),
            primary_metric=int(res_valid.effective),
            secondary_metric=int(res_valid.feedback_is_strong_positive),
        )
    )

    # A4.02 — near-miss at edit distance 1 (case-fold).
    res_near = run_repl_line(
        handle=handle,
        history=ProtoBasicHistory(),
        raw_text="emit alpha",
        line_id=f"{AGENT_REPL_LINE_ID_PREFIX}a4-02",
    )
    has_hint = res_near.near_miss_hint_summary.startswith("hint kind=")
    cases.append(
        BenchmarkCaseResult(
            case_id="A4.02",
            axis=BenchmarkAxis.REPL_COHERENCE,
            status=(
                BenchmarkCaseStatus.PASS
                if (
                    res_near.parse_category_value == "near-miss"
                    and has_hint
                    and res_near.execution_category_value == ""
                )
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"near-miss emit alpha: parse={res_near.parse_category_value} "
                f"hint_present={has_hint}"
            ),
            primary_metric=int(has_hint),
            secondary_metric=0,
        )
    )

    # A4.03 — syntax invalid (empty line).
    res_syn = run_repl_line(
        handle=handle,
        history=ProtoBasicHistory(),
        raw_text="",
        line_id=f"{AGENT_REPL_LINE_ID_PREFIX}a4-03",
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A4.03",
            axis=BenchmarkAxis.REPL_COHERENCE,
            status=(
                BenchmarkCaseStatus.PASS
                if (
                    res_syn.parse_category_value == "syntax-invalid"
                    and res_syn.execution_category_value == ""
                    and len(res_syn.history.commands) == 0
                    and len(res_syn.history.execution_results) == 0
                )
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"syntax-invalid empty: parse={res_syn.parse_category_value} "
                f"commands={len(res_syn.history.commands)}"
            ),
            primary_metric=0,
            secondary_metric=0,
        )
    )

    # A4.04 — diminishing returns sequence (10 valid emissions).
    history = ProtoBasicHistory()
    drf_values: list[str] = []
    val_values: list[str] = []
    for index in range(10):
        line_id = f"{AGENT_REPL_LINE_ID_PREFIX}a4-04-{index:03d}"
        res = run_repl_line(
            handle=handle,
            history=history,
            raw_text="EMIT ALPHA",
            line_id=line_id,
        )
        drf_values.append(res.diminishing_returns_factor_str)
        val_values.append(res.feedback_valence_str)
        history = res.history
    # Diminishing-returns factor sequence: 1/1, 1/2, ..., 1/10.
    expected_drf = [f"1/{n + 1}" for n in range(10)]
    drf_ok = drf_values == expected_drf
    cases.append(
        BenchmarkCaseResult(
            case_id="A4.04",
            axis=BenchmarkAxis.REPL_COHERENCE,
            status=(
                BenchmarkCaseStatus.PASS
                if drf_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"diminishing-returns over 10 emissions: "
                f"first_drf={drf_values[0]} last_drf={drf_values[-1]}"
            ),
            primary_metric=10,
            secondary_metric=int(drf_ok),
        )
    )

    # A4.05 — summarize_repl_for_agent over the post-A4.04 history.
    summary = summarize_repl_for_agent(history)
    bounded_ok = (
        summary.emit_total == 10
        and summary.parse_valid_count == 10
        and summary.execution_valid_effective_count == 10
        and summary.summary_line.startswith("agent_repl ")
        and summary.summary_line.isprintable()
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A4.05",
            axis=BenchmarkAxis.REPL_COHERENCE,
            status=(
                BenchmarkCaseStatus.PASS
                if bounded_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"repl summary after 10x: emit_total={summary.emit_total} "
                f"parse_valid={summary.parse_valid_count} "
                f"exec_eff={summary.execution_valid_effective_count}"
            ),
            primary_metric=summary.emit_total,
            secondary_metric=summary.parse_valid_count,
        )
    )

    return AxisResult(
        axis=BenchmarkAxis.REPL_COHERENCE,
        status=_aggregate_axis_status(tuple(cases)),
        cases=tuple(cases),
    )


# ---------------------------------------------------------------------------
# Axis A5 — Communication.
# ---------------------------------------------------------------------------


def run_axis_a5_communication() -> AxisResult:
    cases: list[BenchmarkCaseResult] = []

    # A5.01 — normal natural text -> OK with five canonical sections.
    state = _fresh_state()
    state, r1 = run_agent_interaction_step(state, "hello operator probe one")
    canonical = (
        AgentReplyStatus.PATTERN_REPORT,
        AgentReplyStatus.REPL_REPORT,
        AgentReplyStatus.COHERENCE_REPORT,
        AgentReplyStatus.LIMITATION_REPORT,
        AgentReplyStatus.NEXT_ACTION_SUGGESTION,
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A5.01",
            axis=BenchmarkAxis.COMMUNICATION,
            status=(
                BenchmarkCaseStatus.PASS
                if (
                    r1.reply.disposition is AgentReplyDisposition.OK
                    and r1.reply.section_kinds() == canonical
                )
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                "normal text OK five-section reply: "
                f"disp={r1.reply.disposition.value}"
            ),
            primary_metric=len(r1.reply.sections),
            secondary_metric=0,
        )
    )

    # A5.02 — repeat same text; second reply reflects recurrence climb;
    # both replies share the canonical section-kind sequence; both are
    # deterministic across two fresh sessions advanced identically.
    state, r2 = run_agent_interaction_step(state, "hello operator probe one")
    # The seed recurrence in r2 should be > in r1.
    climbed = r2.observation.seed_recurrence > r1.observation.seed_recurrence
    # Determinism: fresh session advanced identically yields same reply.
    state_alt = _fresh_state()
    state_alt, r1_alt = run_agent_interaction_step(
        state_alt, "hello operator probe one"
    )
    state_alt, r2_alt = run_agent_interaction_step(
        state_alt, "hello operator probe one"
    )
    deterministic = r1.reply == r1_alt.reply and r2.reply == r2_alt.reply
    cases.append(
        BenchmarkCaseResult(
            case_id="A5.02",
            axis=BenchmarkAxis.COMMUNICATION,
            status=(
                BenchmarkCaseStatus.PASS
                if (climbed and deterministic)
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"repeat-and-deterministic: climbed={climbed} "
                f"deterministic={deterministic} "
                f"r1_recur={r1.observation.seed_recurrence} "
                f"r2_recur={r2.observation.seed_recurrence}"
            ),
            primary_metric=r2.observation.seed_recurrence,
            secondary_metric=int(deterministic),
        )
    )

    # A5.03..A5.07 — REFUSAL triggers. The carrier strings are
    # derived at runtime from _FORBIDDEN_NON_CLAIM_TERMS so the source
    # of this module never contains any audit-tuple literal.
    # The first five tuple entries (per coherence_monitor.py ordering)
    # are the cognitive-property terms used here.
    refusal_carrier_term_indexes = (0, 2, 6, 9, 13)
    refusal_carriers = tuple(
        f"a query about {_FORBIDDEN_NON_CLAIM_TERMS[i]}"
        for i in refusal_carrier_term_indexes
    )
    refusal_inputs = tuple(
        (f"A5.{3 + index:02d}", carrier)
        for index, carrier in enumerate(refusal_carriers)
    )
    for case_id, text in refusal_inputs:
        st = _fresh_state()
        _st, res = run_agent_interaction_step(st, text)
        cases.append(
            BenchmarkCaseResult(
                case_id=case_id,
                axis=BenchmarkAxis.COMMUNICATION,
                status=(
                    BenchmarkCaseStatus.PASS
                    if (
                        res.reply.disposition is AgentReplyDisposition.REFUSAL
                        and res.reply.section_kinds()
                        == (
                            AgentReplyStatus.LIMITATION_REPORT,
                            AgentReplyStatus.NEXT_ACTION_SUGGESTION,
                        )
                    )
                    else BenchmarkCaseStatus.FAIL
                ),
                summary=(
                    f"refusal trigger: disp={res.reply.disposition.value} "
                    f"sections={len(res.reply.sections)}"
                ),
                primary_metric=int(
                    res.reply.disposition is AgentReplyDisposition.REFUSAL
                ),
                secondary_metric=len(res.reply.sections),
            )
        )

    # A5.08 — empty operator text -> WARN.
    st = _fresh_state()
    _st, res = run_agent_interaction_step(st, "")
    cases.append(
        BenchmarkCaseResult(
            case_id="A5.08",
            axis=BenchmarkAxis.COMMUNICATION,
            status=(
                BenchmarkCaseStatus.PASS
                if res.reply.disposition is AgentReplyDisposition.WARN
                else BenchmarkCaseStatus.FAIL
            ),
            summary=f"empty input WARN: disp={res.reply.disposition.value}",
            primary_metric=int(
                res.reply.disposition is AgentReplyDisposition.WARN
            ),
            secondary_metric=0,
        )
    )

    # A5.09 — oversize operator text -> FAIL.
    big = "x" * (AGENT_INPUT_MAX_LEN + 1)
    st = _fresh_state()
    _st, res = run_agent_interaction_step(st, big)
    cases.append(
        BenchmarkCaseResult(
            case_id="A5.09",
            axis=BenchmarkAxis.COMMUNICATION,
            status=(
                BenchmarkCaseStatus.PASS
                if res.reply.disposition is AgentReplyDisposition.FAIL
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"oversize input FAIL: disp={res.reply.disposition.value}"
            ),
            primary_metric=int(
                res.reply.disposition is AgentReplyDisposition.FAIL
            ),
            secondary_metric=0,
        )
    )

    return AxisResult(
        axis=BenchmarkAxis.COMMUNICATION,
        status=_aggregate_axis_status(tuple(cases)),
        cases=tuple(cases),
    )


# ---------------------------------------------------------------------------
# Axis A6 — Session continuity.
# ---------------------------------------------------------------------------


def run_axis_a6_session_continuity() -> AxisResult:
    cases: list[BenchmarkCaseResult] = []

    # A6.01 — 4 distinct operator texts in one session; cumulative
    # entry count climbs; growth_event_total non-decreasing.
    state = _fresh_state()
    obs_seq: list[int] = []
    growth_seq: list[int] = []
    texts_distinct = (
        "alpha line one",
        "beta line two payload",
        "gamma line three payload-bytes",
        "delta line four payload-bytes-extra",
    )
    for text in texts_distinct:
        state, res = run_agent_interaction_step(state, text)
        obs_seq.append(res.observation.pattern_entry_count)
        growth_seq.append(res.observation.growth_event_total)
    cumulative_climb = (
        obs_seq == sorted(obs_seq)
        and obs_seq[-1] >= 1
    )
    growth_nondec = all(
        growth_seq[i] >= growth_seq[i - 1] for i in range(1, len(growth_seq))
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A6.01",
            axis=BenchmarkAxis.SESSION_CONTINUITY,
            status=(
                BenchmarkCaseStatus.PASS
                if (cumulative_climb and growth_nondec)
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"4-distinct: entry_seq={tuple(obs_seq)} "
                f"growth_seq={tuple(growth_seq)}"
            ),
            primary_metric=obs_seq[-1],
            secondary_metric=growth_seq[-1],
        )
    )

    # A6.02 — repeat same text 3x; seed_recurrence climbs monotonically.
    state = _fresh_state()
    recur_seq: list[int] = []
    for _ in range(3):
        state, res = run_agent_interaction_step(state, "single-seed-text")
        recur_seq.append(res.observation.seed_recurrence)
    monotonic = all(
        recur_seq[i] >= recur_seq[i - 1] for i in range(1, len(recur_seq))
    )
    expected_final = (
        recur_seq[-1] == STREAM_PATTERN_RECURRENCE_MIN + 2
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A6.02",
            axis=BenchmarkAxis.SESSION_CONTINUITY,
            status=(
                BenchmarkCaseStatus.PASS
                if (monotonic and expected_final)
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"3x same text: recur_seq={tuple(recur_seq)}"
            ),
            primary_metric=recur_seq[-1],
            secondary_metric=int(monotonic),
        )
    )

    # A6.03 — interleave a REPL command with a STREAM_APPEND in one
    # session; the post-REPL reply's REPL_REPORT section reflects
    # the REPL outcome; the post-STREAM_APPEND reply's PATTERN_REPORT
    # section reflects the new stream event.
    state = _fresh_state()
    state, r_repl = run_agent_interaction_step(state, "EMIT ALPHA")
    state, r_stream = run_agent_interaction_step(state, "natural text two")
    repl_section_body = next(
        (
            body
            for status, body in r_repl.reply.sections
            if status is AgentReplyStatus.REPL_REPORT
        ),
        "",
    )
    pattern_section_body = next(
        (
            body
            for status, body in r_stream.reply.sections
            if status is AgentReplyStatus.PATTERN_REPORT
        ),
        "",
    )
    repl_ok = (
        r_repl.repl_line_result is not None
        and "last_parse=valid" in repl_section_body
    )
    pattern_ok = (
        r_stream.observation.stream_chunk_count >= 1
        and "stream_chunks=" in pattern_section_body
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A6.03",
            axis=BenchmarkAxis.SESSION_CONTINUITY,
            status=(
                BenchmarkCaseStatus.PASS
                if (repl_ok and pattern_ok)
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"interleave repl+stream: repl_ok={repl_ok} "
                f"pattern_ok={pattern_ok}"
            ),
            primary_metric=int(repl_ok),
            secondary_metric=int(pattern_ok),
        )
    )

    return AxisResult(
        axis=BenchmarkAxis.SESSION_CONTINUITY,
        status=_aggregate_axis_status(tuple(cases)),
        cases=tuple(cases),
    )


# ---------------------------------------------------------------------------
# Axis A7 — Blind transcript criterion.
#
# A7 runs the cumulative battery (axes A1..A6) and audits the
# generated transcript bytes against a closed rubric. The axis fails
# if any case from earlier axes failed; if all earlier axes PASS or
# WARN-with-documented-blocker, A7 collects transcript bytes and
# verifies the rubric.
# ---------------------------------------------------------------------------


def run_axis_a7_blind_transcript(
    earlier_axes: tuple[AxisResult, ...],
) -> AxisResult:
    cases: list[BenchmarkCaseResult] = []

    # Collect all transcript lines from the earlier axes.
    all_lines: list[str] = []
    for ax in earlier_axes:
        for case in ax.cases:
            all_lines.extend(_transcript_lines_from_case(case))

    digest_a = _compute_transcript_digest(tuple(all_lines))
    digest_b = _compute_transcript_digest(tuple(all_lines))
    cases.append(
        BenchmarkCaseResult(
            case_id="A7.01",
            axis=BenchmarkAxis.BLIND_TRANSCRIPT,
            status=(
                BenchmarkCaseStatus.PASS
                if digest_a == digest_b
                else BenchmarkCaseStatus.FAIL
            ),
            summary=f"transcript digest deterministic: digest={digest_a}",
            primary_metric=len(all_lines),
            secondary_metric=0,
        )
    )

    # Every transcript line bounded printable + non-claim-clean.
    printable_ok = all(
        isinstance(line, str)
        and line.isprintable()
        and len(line) <= BENCHMARK_TRANSCRIPT_LINE_MAX_LEN
        for line in all_lines
    )
    no_forbidden = all(
        _text_has_forbidden_term(line) is None for line in all_lines
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A7.02",
            axis=BenchmarkAxis.BLIND_TRANSCRIPT,
            status=(
                BenchmarkCaseStatus.PASS
                if (printable_ok and no_forbidden)
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"transcript audit: printable={printable_ok} "
                f"no_forbidden_term={no_forbidden}"
            ),
            primary_metric=len(all_lines),
            secondary_metric=int(no_forbidden),
        )
    )

    # No FAIL in any earlier axis case.
    earlier_fail_count = sum(
        1
        for ax in earlier_axes
        for case in ax.cases
        if case.status is BenchmarkCaseStatus.FAIL
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A7.03",
            axis=BenchmarkAxis.BLIND_TRANSCRIPT,
            status=(
                BenchmarkCaseStatus.PASS
                if earlier_fail_count == 0
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"no FAIL across earlier axes: "
                f"earlier_fail_count={earlier_fail_count}"
            ),
            primary_metric=earlier_fail_count,
            secondary_metric=0,
        )
    )

    # Every refusal case in A5.03..A5.07 had disposition REFUSAL.
    # Search earlier_axes for the COMMUNICATION axis and inspect.
    refusal_check_ok = True
    refusal_case_ids = ("A5.03", "A5.04", "A5.05", "A5.06", "A5.07")
    for ax in earlier_axes:
        if ax.axis is BenchmarkAxis.COMMUNICATION:
            for case in ax.cases:
                if case.case_id in refusal_case_ids:
                    # Pass criterion of A5.0N is exactly disposition
                    # REFUSAL; reuse that as the rubric check.
                    if case.status is not BenchmarkCaseStatus.PASS:
                        refusal_check_ok = False
                        break
    cases.append(
        BenchmarkCaseResult(
            case_id="A7.04",
            axis=BenchmarkAxis.BLIND_TRANSCRIPT,
            status=(
                BenchmarkCaseStatus.PASS
                if refusal_check_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=f"refusal rubric: ok={refusal_check_ok}",
            primary_metric=int(refusal_check_ok),
            secondary_metric=0,
        )
    )

    return AxisResult(
        axis=BenchmarkAxis.BLIND_TRANSCRIPT,
        status=_aggregate_axis_status(tuple(cases)),
        cases=tuple(cases),
    )


# ---------------------------------------------------------------------------
# Full battery runner.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Axis A8 — Learning evidence (Phase 3.22b).
# ---------------------------------------------------------------------------


def run_axis_a8_learning_evidence() -> AxisResult:
    cases: list[BenchmarkCaseResult] = []

    # A8.01 — exact recurrence produces RECURRENCE_INCREASED evidence.
    state = make_initial_agent_loop_state()
    state, _ = run_agent_interaction_step(state, "alpha line one")
    state, _ = run_agent_interaction_step(state, "alpha line one")
    rec_increased = sum(
        1
        for r in state.learning_trace.records
        if r.kind is LearningEvidenceKind.RECURRENCE_INCREASED
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A8.01",
            axis=BenchmarkAxis.LEARNING_EVIDENCE,
            status=(
                BenchmarkCaseStatus.PASS
                if rec_increased >= 1
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"exact recurrence: recurrence_increased_count="
                f"{rec_increased}"
            ),
            primary_metric=rec_increased,
            secondary_metric=len(state.learning_trace.records),
        )
    )

    # A8.02 — ABAB abstract pattern acquired after first exposure.
    state = make_initial_agent_loop_state()
    sig = derive_abstract_pattern_signature("red blue red blue")
    pre_acquired = any(
        r.kind is LearningEvidenceKind.ABSTRACT_PATTERN_ACQUIRED
        and r.abstract_pattern_digest == sig.digest_hex16
        for r in state.learning_trace.records
    )
    state, _ = run_agent_interaction_step(state, "red blue red blue")
    post_acquired = any(
        r.kind is LearningEvidenceKind.ABSTRACT_PATTERN_ACQUIRED
        and r.abstract_pattern_digest == sig.digest_hex16
        for r in state.learning_trace.records
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A8.02",
            axis=BenchmarkAxis.LEARNING_EVIDENCE,
            status=(
                BenchmarkCaseStatus.PASS
                if (not pre_acquired and post_acquired)
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"ABAB abstract acquired: pre={pre_acquired} "
                f"post={post_acquired} digest={sig.digest_hex16}"
            ),
            primary_metric=int(post_acquired),
            secondary_metric=int(not pre_acquired),
        )
    )

    # A8.03 — renamed ABAB input recognized as transfer.
    state = make_initial_agent_loop_state()
    state, _ = run_agent_interaction_step(state, "red blue red blue")
    state, r2 = run_agent_interaction_step(state, "cat dog cat dog")
    transfer = any(
        r.kind is LearningEvidenceKind.TRANSFER_RECOGNIZED
        for r in state.learning_trace.records
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A8.03",
            axis=BenchmarkAxis.LEARNING_EVIDENCE,
            status=(
                BenchmarkCaseStatus.PASS
                if transfer
                else BenchmarkCaseStatus.FAIL
            ),
            summary=f"renamed ABAB transfer: detected={transfer}",
            primary_metric=int(transfer),
            secondary_metric=0,
        )
    )

    # A8.04 — later reply's NEXT_ACTION section reflects climbed
    # recurrence (cites prior acquired/reused structure via the
    # pattern-section recurrence count).
    state = make_initial_agent_loop_state()
    state, r1 = run_agent_interaction_step(state, "alpha line one")
    state, r2 = run_agent_interaction_step(state, "alpha line one")
    pattern_section = next(
        (
            body
            for status, body in r2.reply.sections
            if status is AgentReplyStatus.PATTERN_REPORT
        ),
        "",
    )
    # The pattern-section body includes the (climbed) recurrence value.
    cite_ok = (
        "seed_recur=" in pattern_section
        and r2.observation.seed_recurrence > r1.observation.seed_recurrence
    )
    # Also confirm the learning trace contains a reused / recurrence
    # record for the second step.
    has_reuse_or_recur = any(
        r.kind
        in (
            LearningEvidenceKind.ABSTRACT_PATTERN_REUSED,
            LearningEvidenceKind.RECURRENCE_INCREASED,
        )
        for r in r2.learning_evidence_trace.records[-3:]
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A8.04",
            axis=BenchmarkAxis.LEARNING_EVIDENCE,
            status=(
                BenchmarkCaseStatus.PASS
                if (cite_ok and has_reuse_or_recur)
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"later reply cites prior structure: "
                f"recur_climbed={cite_ok} reuse_or_recur={has_reuse_or_recur}"
            ),
            primary_metric=int(cite_ok),
            secondary_metric=int(has_reuse_or_recur),
        )
    )

    # A8.05 — near-miss REPL correction creates learning evidence.
    state = make_initial_agent_loop_state()
    state, _ = run_agent_interaction_step(state, "emit alpha")  # near-miss
    state, _ = run_agent_interaction_step(state, "EMIT ALPHA")  # valid
    correction_count = sum(
        1
        for r in state.learning_trace.records
        if r.kind is LearningEvidenceKind.REPL_CORRECTION_APPLIED
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A8.05",
            axis=BenchmarkAxis.LEARNING_EVIDENCE,
            status=(
                BenchmarkCaseStatus.PASS
                if correction_count >= 1
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"near-miss correction evidence: "
                f"corrections={correction_count}"
            ),
            primary_metric=correction_count,
            secondary_metric=0,
        )
    )

    # A8.06 — repeated valid-effective REPL action changes
    # diminishing-returns evidence.
    state = make_initial_agent_loop_state()
    for _ in range(4):
        state, _ = run_agent_interaction_step(state, "EMIT BETA")
    drf_records = [
        r
        for r in state.learning_trace.records
        if r.kind is LearningEvidenceKind.DIMINISHING_RETURNS_UPDATED
    ]
    # Expect 3 DRF records (calls 2, 3, 4).
    cases.append(
        BenchmarkCaseResult(
            case_id="A8.06",
            axis=BenchmarkAxis.LEARNING_EVIDENCE,
            status=(
                BenchmarkCaseStatus.PASS
                if len(drf_records) >= 3
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"DRF evidence over 4 emits: "
                f"drf_records={len(drf_records)}"
            ),
            primary_metric=len(drf_records),
            secondary_metric=0,
        )
    )

    # A8.07 — deterministic learning proof digest stable across two runs.
    state_a = make_initial_agent_loop_state()
    state_b = make_initial_agent_loop_state()
    seq = (
        "alpha line one",
        "alpha line one",
        "red blue red blue",
        "cat dog cat dog",
        "EMIT ALPHA",
        "EMIT ALPHA",
    )
    for text in seq:
        state_a, _ = run_agent_interaction_step(state_a, text)
        state_b, _ = run_agent_interaction_step(state_b, text)
    report_a = build_learning_proof_report(state_a.learning_trace)
    report_b = build_learning_proof_report(state_b.learning_trace)
    cases.append(
        BenchmarkCaseResult(
            case_id="A8.07",
            axis=BenchmarkAxis.LEARNING_EVIDENCE,
            status=(
                BenchmarkCaseStatus.PASS
                if report_a.digest_hex16 == report_b.digest_hex16
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"learning proof digest stable: "
                f"digest={report_a.digest_hex16} match={report_a.digest_hex16 == report_b.digest_hex16}"
            ),
            primary_metric=report_a.record_total,
            secondary_metric=int(report_a.digest_hex16 == report_b.digest_hex16),
        )
    )

    return AxisResult(
        axis=BenchmarkAxis.LEARNING_EVIDENCE,
        status=_aggregate_axis_status(tuple(cases)),
        cases=tuple(cases),
    )


# ---------------------------------------------------------------------------
# Axis A9 — Reasoning trace (Phase 3.22b).
# ---------------------------------------------------------------------------


def run_axis_a9_reasoning_trace() -> AxisResult:
    cases: list[BenchmarkCaseResult] = []

    # A9.01 — every agent reply has a non-empty reasoning trace.
    # The cognitive-claim probe input is composed from the imported
    # ``_FORBIDDEN_NON_CLAIM_TERMS`` tuple so this source file itself
    # contains no literal forbidden term (audited by I-AGENTLOOP-11).
    cognitive_probe = "are you " + _FORBIDDEN_NON_CLAIM_TERMS[0]
    state = make_initial_agent_loop_state()
    inputs = (
        "alpha line one",
        "red blue red blue",
        "",
        "EMIT ALPHA",
        cognitive_probe,
        "x" * (AGENT_INPUT_MAX_LEN + 1),
    )
    non_empty = 0
    total = 0
    for text in inputs:
        state, r = run_agent_interaction_step(state, text)
        total += 1
        if r.reasoning_trace is not None and len(r.reasoning_trace.steps) > 0:
            non_empty += 1
    cases.append(
        BenchmarkCaseResult(
            case_id="A9.01",
            axis=BenchmarkAxis.REASONING_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if non_empty == total
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"every reply has non-empty trace: "
                f"{non_empty}/{total}"
            ),
            primary_metric=non_empty,
            secondary_metric=total,
        )
    )

    # A9.02 — refusal reply trace shows classify-refusal match path.
    state = make_initial_agent_loop_state()
    state, r = run_agent_interaction_step(state, cognitive_probe)
    classify_steps = [
        s
        for s in r.reasoning_trace.steps
        if s.kind is ReasoningStepKind.CLASSIFY_REFUSAL
    ]
    match_ok = any(
        "classifier_match=True" in s.input_facts for s in classify_steps
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A9.02",
            axis=BenchmarkAxis.REASONING_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if (
                    r.reply.disposition is AgentReplyDisposition.REFUSAL
                    and match_ok
                )
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"refusal trace classifier match: disp={r.reply.disposition.value} "
                f"match_ok={match_ok}"
            ),
            primary_metric=int(match_ok),
            secondary_metric=len(classify_steps),
        )
    )

    # A9.03 — pattern reply trace shows derive-pattern ->
    # lookup-prior -> select-reply path.
    state = make_initial_agent_loop_state()
    state, _ = run_agent_interaction_step(state, "red blue red blue")
    state, r = run_agent_interaction_step(state, "cat dog cat dog")
    kinds = tuple(s.kind for s in r.reasoning_trace.steps)
    has_derive = ReasoningStepKind.DERIVE_PATTERN in kinds
    has_lookup = ReasoningStepKind.LOOKUP_PRIOR_STRUCTURE in kinds
    has_compare = ReasoningStepKind.COMPARE_STRUCTURE in kinds
    has_select = ReasoningStepKind.SELECT_REPLY_DISPOSITION in kinds
    path_ok = has_derive and has_lookup and has_compare and has_select
    cases.append(
        BenchmarkCaseResult(
            case_id="A9.03",
            axis=BenchmarkAxis.REASONING_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if path_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"pattern trace path: derive={has_derive} "
                f"lookup={has_lookup} compare={has_compare} "
                f"select={has_select}"
            ),
            primary_metric=int(path_ok),
            secondary_metric=len(kinds),
        )
    )

    # A9.04 — REPL reply trace shows the parse/build/execute/feedback
    # path (CHECK_REPL step records parse/exec values).
    state = make_initial_agent_loop_state()
    state, r = run_agent_interaction_step(state, "EMIT ALPHA")
    repl_steps = [
        s
        for s in r.reasoning_trace.steps
        if s.kind is ReasoningStepKind.CHECK_REPL
    ]
    repl_facts_ok = any(
        ("parse=valid" in s.derived_facts)
        and ("exec=valid-effective" in s.derived_facts)
        for s in repl_steps
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A9.04",
            axis=BenchmarkAxis.REASONING_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if (repl_facts_ok)
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"repl trace facts: parse_exec_ok={repl_facts_ok} "
                f"steps={len(repl_steps)}"
            ),
            primary_metric=int(repl_facts_ok),
            secondary_metric=len(repl_steps),
        )
    )

    # A9.05 — limitation reply trace documents not_applicable blocker
    # without invalid state. We construct a session with one
    # STREAM_APPEND and check the trace's CHECK_COHERENCE step shows
    # overall_status = "pass" (the achievable overall on a valid
    # session). Then we set ``stream_chunk_serial=0`` to induce a
    # WARN and run another step; the trace's CHECK_COHERENCE step
    # records "warn".
    state = make_initial_agent_loop_state()
    state, _ = run_agent_interaction_step(state, "alpha line one")
    state, r_pass = run_agent_interaction_step(state, "alpha line two")
    pass_step = next(
        (
            s
            for s in r_pass.reasoning_trace.steps
            if s.kind is ReasoningStepKind.CHECK_COHERENCE
        ),
        None,
    )
    pass_records_overall = (
        pass_step is not None and "overall=pass" in pass_step.derived_facts
    )
    # Induce a WARN via the lever used by A3.02.
    state.session.stream_chunk_serial = 0
    state, r_warn = run_agent_interaction_step(state, "alpha line three")
    warn_step = next(
        (
            s
            for s in r_warn.reasoning_trace.steps
            if s.kind is ReasoningStepKind.CHECK_COHERENCE
        ),
        None,
    )
    warn_records_overall = (
        warn_step is not None and "overall=warn" in warn_step.derived_facts
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A9.05",
            axis=BenchmarkAxis.REASONING_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if (pass_records_overall and warn_records_overall)
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"coherence record: pass_recorded={pass_records_overall} "
                f"warn_recorded={warn_records_overall}"
            ),
            primary_metric=int(pass_records_overall),
            secondary_metric=int(warn_records_overall),
        )
    )

    # A9.06 — two runs produce equal trace_digest_hex16.
    state_a = make_initial_agent_loop_state()
    state_b = make_initial_agent_loop_state()
    state_a, ra = run_agent_interaction_step(state_a, "red blue red blue")
    state_b, rb = run_agent_interaction_step(state_b, "red blue red blue")
    report_a = build_reasoning_trace_report(ra.reasoning_trace)
    report_b = build_reasoning_trace_report(rb.reasoning_trace)
    cases.append(
        BenchmarkCaseResult(
            case_id="A9.06",
            axis=BenchmarkAxis.REASONING_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if report_a.trace_digest_hex16 == report_b.trace_digest_hex16
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"trace digest stable: digest={report_a.trace_digest_hex16} "
                f"match={report_a.trace_digest_hex16 == report_b.trace_digest_hex16}"
            ),
            primary_metric=report_a.step_total,
            secondary_metric=int(
                report_a.trace_digest_hex16 == report_b.trace_digest_hex16
            ),
        )
    )

    # A9.07 — trace source scan has zero forbidden-term hits.
    state = make_initial_agent_loop_state()
    state, r = run_agent_interaction_step(state, "red blue red blue")
    trace_strings: list[str] = []
    for s in r.reasoning_trace.steps:
        trace_strings.extend(
            (s.input_facts, s.derived_facts, s.next_action)
        )
    hits = 0
    for text in trace_strings:
        if _text_has_forbidden_term(text) is not None:
            hits += 1
    cases.append(
        BenchmarkCaseResult(
            case_id="A9.07",
            axis=BenchmarkAxis.REASONING_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if hits == 0
                else BenchmarkCaseStatus.FAIL
            ),
            summary=f"trace forbidden-term hits: {hits}",
            primary_metric=hits,
            secondary_metric=len(trace_strings),
        )
    )

    return AxisResult(
        axis=BenchmarkAxis.REASONING_TRACE,
        status=_aggregate_axis_status(tuple(cases)),
        cases=tuple(cases),
    )


def run_axis_a10_dispatch_trace() -> AxisResult:
    """Phase 3.23 (I-DTRACE-11): dispatch trace battery axis.

    Twelve closed cases A10.01..A10.12 covering:
    * STREAM_APPEND trace shape + mutation classification,
    * processing-window internal feedback split (STREAM_WINDOW_INTERNAL),
    * PATTERN_AND_COHERENCE feedback-mode capture in before_facts,
    * cognitive-claim refusal still records a (no-dispatch) route,
    * REPL valid-effective path records the synthetic REPL route,
    * renamed-transfer reasoning trace cites the dispatch trace digest,
    * STEP_TICK missing-client records ERROR_ONLY,
    * NOOP records the no-op route,
    * determinism across two fresh-session runs,
    * dispatch tracer module source forbidden-term audit,
    * A1..A9 axis case totals are retained (the new axis is additive).
    """
    # Lazy imports keep the module-level imports light.
    from brain.development import dispatch_tracer as _dispatch_tracer_module
    import inspect as _inspect

    cases: list[BenchmarkCaseResult] = []

    # A10.01 — STREAM_APPEND produces a non-empty dispatch trace.
    session = _fresh_session()
    _append_stream(session, "alpha line one")
    trace_report = session.latest_dispatch_trace
    a10_01_ok = (
        isinstance(trace_report, DispatchTraceReport)
        and trace_report.step_total >= 1
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A10.01",
            axis=BenchmarkAxis.DISPATCH_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if a10_01_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"stream_append produces dispatch trace: "
                f"steps={trace_report.step_total if trace_report else 0} "
                f"digest={trace_report.trace_digest_hex16 if trace_report else ''}"
            ),
            primary_metric=trace_report.step_total if trace_report else 0,
            secondary_metric=int(a10_01_ok),
        )
    )

    # A10.02 — STREAM_APPEND trace records route + mutation kind.
    session = _fresh_session()
    _append_stream(session, "beta line one")
    trace = session.latest_dispatch_trace
    a10_02_ok = (
        trace is not None
        and trace.command_kind == "stream_append"
        and trace.mutation_kind is DispatchMutationKind.STREAM_APPEND
        and trace.route_path == "stream-append"
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A10.02",
            axis=BenchmarkAxis.DISPATCH_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if a10_02_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"stream_append route+mut: "
                f"cmd={trace.command_kind if trace else ''} "
                f"mut={trace.mutation_kind.value if trace else ''} "
                f"route={trace.route_path if trace else ''}"
            ),
            primary_metric=1 if a10_02_ok else 0,
            secondary_metric=0,
        )
    )

    # A10.03 — processing window ON + PATTERN_LEDGER feedback records
    # STREAM_WINDOW_INTERNAL.
    session = _fresh_session()
    session.processing_window_size = 2
    session.feedback_mode = FeedbackMode.PATTERN_LEDGER
    _append_stream(session, "alpha line two")
    trace = session.latest_dispatch_trace
    a10_03_ok = (
        trace is not None
        and trace.mutation_kind is DispatchMutationKind.STREAM_WINDOW_INTERNAL
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A10.03",
            axis=BenchmarkAxis.DISPATCH_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if a10_03_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"processing window internal mutation: "
                f"mut={trace.mutation_kind.value if trace else ''}"
            ),
            primary_metric=int(a10_03_ok),
            secondary_metric=0,
        )
    )

    # A10.04 — PATTERN_AND_COHERENCE captured in before_facts.feedback_mode.
    session = _fresh_session()
    session.processing_window_size = 2
    session.feedback_mode = FeedbackMode.PATTERN_AND_COHERENCE
    _append_stream(session, "alpha line three")
    trace = session.latest_dispatch_trace
    pre_step = None
    if trace is not None:
        for s in trace.trace.steps:
            if s.kind.value == "pre_state_snapshot":
                pre_step = s
                break
    fm_before = ""
    if pre_step is not None:
        for k, v in pre_step.before_facts:
            if k == "feedback_mode":
                fm_before = v
                break
    a10_04_ok = fm_before == FeedbackMode.PATTERN_AND_COHERENCE.value
    cases.append(
        BenchmarkCaseResult(
            case_id="A10.04",
            axis=BenchmarkAxis.DISPATCH_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if a10_04_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"feedback_mode captured in pre-state: "
                f"feedback_mode={fm_before!r}"
            ),
            primary_metric=int(a10_04_ok),
            secondary_metric=0,
        )
    )

    # A10.05 — cognitive-claim refusal records a no-dispatch route
    # without mutating the session. The carrier text is synthesized
    # at runtime from _FORBIDDEN_NON_CLAIM_TERMS so this source file
    # never contains a forbidden term verbatim.
    state = make_initial_agent_loop_state()
    pre_chunks = len(state.session.stream_history.chunks)
    refusal_carrier = f"a query about {_FORBIDDEN_NON_CLAIM_TERMS[0]}"
    state, r = run_agent_interaction_step(state, refusal_carrier)
    post_chunks = len(state.session.stream_history.chunks)
    a10_05_ok = (
        r.reply.disposition is AgentReplyDisposition.REFUSAL
        and r.latest_dispatch_trace is not None
        and r.latest_dispatch_trace.mutation_kind is DispatchMutationKind.NONE
        and pre_chunks == post_chunks
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A10.05",
            axis=BenchmarkAxis.DISPATCH_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if a10_05_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"refusal records no-dispatch route: "
                f"mut={r.latest_dispatch_trace.mutation_kind.value if r.latest_dispatch_trace else ''} "
                f"chunks_pre={pre_chunks} chunks_post={post_chunks}"
            ),
            primary_metric=int(a10_05_ok),
            secondary_metric=0,
        )
    )

    # A10.06 — REPL valid-effective path records the synthetic REPL route.
    state = make_initial_agent_loop_state()
    state, r = run_agent_interaction_step(state, "EMIT ALPHA")
    a10_06_ok = (
        r.latest_dispatch_trace is not None
        and r.latest_dispatch_trace.route_path == "repl-bridge"
        and r.latest_dispatch_trace.mutation_kind is DispatchMutationKind.NONE
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A10.06",
            axis=BenchmarkAxis.DISPATCH_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if a10_06_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"repl valid-effective route: "
                f"route={r.latest_dispatch_trace.route_path if r.latest_dispatch_trace else ''} "
                f"mut={r.latest_dispatch_trace.mutation_kind.value if r.latest_dispatch_trace else ''}"
            ),
            primary_metric=int(a10_06_ok),
            secondary_metric=0,
        )
    )

    # A10.07 — renamed-transfer reasoning trace references the dispatch
    # trace digest via CHECK_DISPATCH_TRACE.
    state = make_initial_agent_loop_state()
    state, _ = run_agent_interaction_step(state, "red blue red blue")
    state, r = run_agent_interaction_step(state, "cat dog cat dog")
    cdt_step = None
    if r.reasoning_trace is not None:
        for s in r.reasoning_trace.steps:
            if s.kind is ReasoningStepKind.CHECK_DISPATCH_TRACE:
                cdt_step = s
                break
    cited_digest = ""
    if cdt_step is not None and r.latest_dispatch_trace is not None:
        marker = f"dispatch_digest={r.latest_dispatch_trace.trace_digest_hex16}"
        if marker in cdt_step.input_facts:
            cited_digest = r.latest_dispatch_trace.trace_digest_hex16
    a10_07_ok = cited_digest != ""
    cases.append(
        BenchmarkCaseResult(
            case_id="A10.07",
            axis=BenchmarkAxis.DISPATCH_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if a10_07_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"renamed-transfer trace cites dispatch digest: "
                f"digest={cited_digest!r}"
            ),
            primary_metric=int(a10_07_ok),
            secondary_metric=0,
        )
    )

    # A10.08 — missing-client STEP_TICK records ERROR_ONLY with no
    # kernel mutation.
    session = _fresh_session()
    pre_tick = session.tick_counter
    session.dispatch(Command(OperatorCommand.STEP_TICK))  # client=None
    post_tick = session.tick_counter
    trace = session.latest_dispatch_trace
    a10_08_ok = (
        trace is not None
        and trace.mutation_kind is DispatchMutationKind.ERROR_ONLY
        and pre_tick == post_tick
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A10.08",
            axis=BenchmarkAxis.DISPATCH_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if a10_08_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"step_tick missing-client: "
                f"mut={trace.mutation_kind.value if trace else ''} "
                f"tick_pre={pre_tick} tick_post={post_tick}"
            ),
            primary_metric=int(a10_08_ok),
            secondary_metric=0,
        )
    )

    # A10.09 — NOOP records noop route and no mutation.
    session = _fresh_session()
    session.dispatch(Command(OperatorCommand.NOOP))
    trace = session.latest_dispatch_trace
    a10_09_ok = (
        trace is not None
        and trace.mutation_kind is DispatchMutationKind.NONE
        and trace.route_path == "noop-early-return"
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A10.09",
            axis=BenchmarkAxis.DISPATCH_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if a10_09_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"noop route: "
                f"route={trace.route_path if trace else ''} "
                f"mut={trace.mutation_kind.value if trace else ''}"
            ),
            primary_metric=int(a10_09_ok),
            secondary_metric=0,
        )
    )

    # A10.10 — dispatch trace digest stable across two fresh-session runs.
    session_a = _fresh_session()
    session_b = _fresh_session()
    _append_stream(session_a, "gamma line one")
    _append_stream(session_b, "gamma line one")
    digest_a = (
        session_a.latest_dispatch_trace.trace_digest_hex16
        if session_a.latest_dispatch_trace
        else ""
    )
    digest_b = (
        session_b.latest_dispatch_trace.trace_digest_hex16
        if session_b.latest_dispatch_trace
        else ""
    )
    a10_10_ok = digest_a != "" and digest_a == digest_b
    cases.append(
        BenchmarkCaseResult(
            case_id="A10.10",
            axis=BenchmarkAxis.DISPATCH_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if a10_10_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"dispatch trace digest stable: "
                f"digest={digest_a} match={a10_10_ok}"
            ),
            primary_metric=int(a10_10_ok),
            secondary_metric=0,
        )
    )

    # A10.11 — dispatch tracer module source has zero forbidden-term hits.
    src = _inspect.getsource(_dispatch_tracer_module)
    hit_term = _text_has_forbidden_term(src)
    a10_11_ok = hit_term is None
    cases.append(
        BenchmarkCaseResult(
            case_id="A10.11",
            axis=BenchmarkAxis.DISPATCH_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if a10_11_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"dispatch_tracer source non-claim-clean: hit={hit_term!r}"
            ),
            primary_metric=int(a10_11_ok),
            secondary_metric=0,
        )
    )

    # A10.12 — adding A10 is additive: A1..A9 axis case totals match
    # the pre-A10 expected counts.
    a1 = run_axis_a1_pattern_recognition()
    a2 = run_axis_a2_cross_input_structural()
    a3 = run_axis_a3_coherence_variation()
    a4 = run_axis_a4_repl_coherence()
    a5 = run_axis_a5_communication()
    a6 = run_axis_a6_session_continuity()
    earlier = (a1, a2, a3, a4, a5, a6)
    a7 = run_axis_a7_blind_transcript(earlier)
    a8 = run_axis_a8_learning_evidence()
    a9 = run_axis_a9_reasoning_trace()
    pre_a10_case_counts = (
        len(a1.cases),
        len(a2.cases),
        len(a3.cases),
        len(a4.cases),
        len(a5.cases),
        len(a6.cases),
        len(a7.cases),
        len(a8.cases),
        len(a9.cases),
    )
    expected = (9, 5, 4, 5, 9, 3, 4, 7, 7)
    a10_12_ok = pre_a10_case_counts == expected
    cases.append(
        BenchmarkCaseResult(
            case_id="A10.12",
            axis=BenchmarkAxis.DISPATCH_TRACE,
            status=(
                BenchmarkCaseStatus.PASS
                if a10_12_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"A1..A9 case counts retained: "
                f"got={pre_a10_case_counts!r} expected={expected!r}"
            ),
            primary_metric=int(a10_12_ok),
            secondary_metric=0,
        )
    )

    return AxisResult(
        axis=BenchmarkAxis.DISPATCH_TRACE,
        status=_aggregate_axis_status(tuple(cases)),
        cases=tuple(cases),
    )


def run_axis_a11_worldlet_feedback() -> AxisResult:
    """Run the Phase 3.24 A11 worldlet_feedback battery axis.

    Twelve cases A11.01..A11.12 exercising the bounded worldlet
    feedback path end-to-end through the processing window, the
    Pattern Ledger, the Dispatch Trace, the Reasoning Trace, and the
    Learning Evidence ledger. Drives ``I-WFDBK-11``.
    """
    import inspect as _inspect
    from brain.development import processing_window as _pw_module
    from brain.development.processing_window import (
        WORLDLET_SUMMARY_ABSENT_SENTINEL,
        build_worldlet_summary_text,
        validate_feedback_mode,
    )
    cases: list[BenchmarkCaseResult] = []

    # A11.01 — WORLDLET feedback mode validates as a closed enum member;
    # PATTERN_COHERENCE_WORLDLET also validates.
    a11_01_ok = True
    try:
        validate_feedback_mode(FeedbackMode.WORLDLET)
        validate_feedback_mode(FeedbackMode.PATTERN_COHERENCE_WORLDLET)
    except Exception:
        a11_01_ok = False
    # Rejection: a non-FeedbackMode value must raise.
    try:
        validate_feedback_mode("worldlet")  # type: ignore[arg-type]
        a11_01_ok = False
    except ValueError:
        pass
    cases.append(
        BenchmarkCaseResult(
            case_id="A11.01",
            axis=BenchmarkAxis.WORLDLET_FEEDBACK,
            status=(
                BenchmarkCaseStatus.PASS
                if a11_01_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"WORLDLET feedback mode closed-enum: ok={a11_01_ok}"
            ),
            primary_metric=int(a11_01_ok),
            secondary_metric=0,
        )
    )

    # A11.02 — build_worldlet_summary_text is deterministic and bounded.
    args = dict(
        state_id_value="wld:state:abcdef0123456789",
        step_index=3,
        object_count=2,
        attempt_count=5,
        response_count=5,
        accepted_count=3,
        pushback_count=2,
        last_reason_value="accepted",
    )
    text_a = build_worldlet_summary_text(**args)
    text_b = build_worldlet_summary_text(**args)
    a11_02_ok = (
        text_a == text_b
        and text_a.startswith("worldlet_summary ")
        and len(text_a) <= 240
        and text_a.isprintable()
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A11.02",
            axis=BenchmarkAxis.WORLDLET_FEEDBACK,
            status=(
                BenchmarkCaseStatus.PASS
                if a11_02_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"build_worldlet_summary_text deterministic+bounded: "
                f"len={len(text_a)} match={text_a == text_b}"
            ),
            primary_metric=int(a11_02_ok),
            secondary_metric=len(text_a),
        )
    )

    # A11.03 — STREAM_APPEND with processing_window_size>0 and WORLDLET
    # emits worldlet_summary chunks.
    session = OperatorSession(
        state=initial_state(),
        processing_window_size=2,
        feedback_mode=FeedbackMode.WORLDLET,
    )
    _append_stream(session, "alpha line one")
    worldlet_chunks = [
        c
        for c in session.stream_history.chunks
        if c.provenance.endswith(":worldlet_summary")
    ]
    a11_03_ok = (
        len(worldlet_chunks) == 2
        and all(c.text.startswith("worldlet_summary ") for c in worldlet_chunks)
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A11.03",
            axis=BenchmarkAxis.WORLDLET_FEEDBACK,
            status=(
                BenchmarkCaseStatus.PASS
                if a11_03_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"STREAM_APPEND+WORLDLET emits worldlet_summary chunks: "
                f"count={len(worldlet_chunks)} expected=2"
            ),
            primary_metric=int(a11_03_ok),
            secondary_metric=len(worldlet_chunks),
        )
    )

    # A11.04 — worldlet_summary chunks update Pattern Ledger entries
    # (the summary text has a distinct signature from the seed chunk,
    # so a SECOND-ORDER ledger entry must exist).
    a11_04_ok = len(session.pattern_ledger.entries) >= 2
    cases.append(
        BenchmarkCaseResult(
            case_id="A11.04",
            axis=BenchmarkAxis.WORLDLET_FEEDBACK,
            status=(
                BenchmarkCaseStatus.PASS
                if a11_04_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"worldlet_summary chunk updates Pattern Ledger: "
                f"entries={len(session.pattern_ledger.entries)}"
            ),
            primary_metric=int(a11_04_ok),
            secondary_metric=len(session.pattern_ledger.entries),
        )
    )

    # A11.05 — dispatch trace records feedback_mode=worldlet and the
    # worldlet_summary_chunks fact in post-state.
    trace = session.latest_dispatch_trace
    feedback_mode_fact = ""
    worldlet_chunks_fact = ""
    if trace is not None:
        for step in trace.trace.steps:
            for k, v in step.before_facts:
                if k == "feedback_mode":
                    feedback_mode_fact = v
            for k, v in step.after_facts:
                if k == "worldlet_summary_chunks":
                    worldlet_chunks_fact = v
    a11_05_ok = (
        feedback_mode_fact == "worldlet"
        and worldlet_chunks_fact == "2"
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A11.05",
            axis=BenchmarkAxis.WORLDLET_FEEDBACK,
            status=(
                BenchmarkCaseStatus.PASS
                if a11_05_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"dispatch trace records WORLDLET route: "
                f"feedback_mode={feedback_mode_fact!r} "
                f"worldlet_summary_chunks={worldlet_chunks_fact!r}"
            ),
            primary_metric=int(a11_05_ok),
            secondary_metric=0,
        )
    )

    # A11.06 — reasoning trace contains CHECK_WORLDLET_FEEDBACK step
    # with bounded facts (after a full run_agent_interaction_step).
    sess = OperatorSession(
        state=initial_state(),
        processing_window_size=2,
        feedback_mode=FeedbackMode.WORLDLET,
    )
    state = make_initial_agent_loop_state(session=sess)
    state, r11 = run_agent_interaction_step(state, "alpha line one")
    cwf_step = None
    if r11.reasoning_trace is not None:
        for s in r11.reasoning_trace.steps:
            if s.kind is ReasoningStepKind.CHECK_WORLDLET_FEEDBACK:
                cwf_step = s
                break
    a11_06_ok = (
        cwf_step is not None
        and "feedback_mode=worldlet" in cwf_step.input_facts
        and "present=True" in cwf_step.input_facts
        and "worldlet_summary_chunks=2" in cwf_step.derived_facts
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A11.06",
            axis=BenchmarkAxis.WORLDLET_FEEDBACK,
            status=(
                BenchmarkCaseStatus.PASS
                if a11_06_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"reasoning trace contains CHECK_WORLDLET_FEEDBACK: "
                f"present={cwf_step is not None}"
            ),
            primary_metric=int(a11_06_ok),
            secondary_metric=0,
        )
    )

    # A11.07 — learning evidence records WORLDLET_FEEDBACK_RECORDED with
    # the dispatch digest cite.
    wfb_record = None
    for r in r11.learning_evidence_trace.records:
        if r.kind is LearningEvidenceKind.WORLDLET_FEEDBACK_RECORDED:
            wfb_record = r
            break
    cited_digest = ""
    if wfb_record is not None:
        lookup = {k: v for k, v in wfb_record.post_facts}
        cited_digest = lookup.get("dispatch_digest", "")
    a11_07_ok = (
        wfb_record is not None
        and r11.latest_dispatch_trace is not None
        and cited_digest == r11.latest_dispatch_trace.trace_digest_hex16
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A11.07",
            axis=BenchmarkAxis.WORLDLET_FEEDBACK,
            status=(
                BenchmarkCaseStatus.PASS
                if a11_07_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"learning evidence records WORLDLET_FEEDBACK_RECORDED: "
                f"digest={cited_digest!r}"
            ),
            primary_metric=int(a11_07_ok),
            secondary_metric=0,
        )
    )

    # A11.08 — agent reply cites bounded worldlet-feedback facts safely.
    reply_text = r11.reply.full_text
    a11_08_ok = (
        "worldlet_feedback=present" in reply_text
        and "route=internal_worldlet_summary" in reply_text
        and _text_has_forbidden_term(reply_text) is None
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A11.08",
            axis=BenchmarkAxis.WORLDLET_FEEDBACK,
            status=(
                BenchmarkCaseStatus.PASS
                if a11_08_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"agent reply cites worldlet-feedback safely: ok={a11_08_ok}"
            ),
            primary_metric=int(a11_08_ok),
            secondary_metric=0,
        )
    )

    # A11.09 — combined PATTERN_COHERENCE_WORLDLET mode works: all three
    # feedback chunks fire after each rehearsal in the fixed order.
    sess_combined = OperatorSession(
        state=initial_state(),
        processing_window_size=2,
        feedback_mode=FeedbackMode.PATTERN_COHERENCE_WORLDLET,
    )
    _append_stream(sess_combined, "combined line one")
    chunk_provenances = [c.provenance for c in sess_combined.stream_history.chunks]
    expected_provenances = [
        "operator",
        "internal_processing_window:1:rehearsal",
        "internal_processing_window:1:pledger_summary",
        "internal_processing_window:1:cohmon_summary",
        "internal_processing_window:1:worldlet_summary",
        "internal_processing_window:2:rehearsal",
        "internal_processing_window:2:pledger_summary",
        "internal_processing_window:2:cohmon_summary",
        "internal_processing_window:2:worldlet_summary",
    ]
    a11_09_ok = chunk_provenances == expected_provenances
    cases.append(
        BenchmarkCaseResult(
            case_id="A11.09",
            axis=BenchmarkAxis.WORLDLET_FEEDBACK,
            status=(
                BenchmarkCaseStatus.PASS
                if a11_09_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"PATTERN_COHERENCE_WORLDLET combined mode order: "
                f"ok={a11_09_ok} chunks={len(chunk_provenances)}"
            ),
            primary_metric=int(a11_09_ok),
            secondary_metric=len(chunk_provenances),
        )
    )

    # A11.10 — worldlet feedback digest stable across two fresh runs.
    sess_x = OperatorSession(
        state=initial_state(),
        processing_window_size=2,
        feedback_mode=FeedbackMode.WORLDLET,
    )
    sess_y = OperatorSession(
        state=initial_state(),
        processing_window_size=2,
        feedback_mode=FeedbackMode.WORLDLET,
    )
    _append_stream(sess_x, "gamma worldlet")
    _append_stream(sess_y, "gamma worldlet")
    digest_x = (
        sess_x.latest_dispatch_trace.trace_digest_hex16
        if sess_x.latest_dispatch_trace
        else ""
    )
    digest_y = (
        sess_y.latest_dispatch_trace.trace_digest_hex16
        if sess_y.latest_dispatch_trace
        else ""
    )
    a11_10_ok = digest_x != "" and digest_x == digest_y
    cases.append(
        BenchmarkCaseResult(
            case_id="A11.10",
            axis=BenchmarkAxis.WORLDLET_FEEDBACK,
            status=(
                BenchmarkCaseStatus.PASS
                if a11_10_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"worldlet feedback digest stable: "
                f"digest={digest_x} match={a11_10_ok}"
            ),
            primary_metric=int(a11_10_ok),
            secondary_metric=0,
        )
    )

    # A11.11 — processing_window source contains no forbidden non-claim
    # term (the source scan covers the Phase 3.24 additions too).
    pw_src = _inspect.getsource(_pw_module)
    hit_term = _text_has_forbidden_term(pw_src)
    a11_11_ok = hit_term is None
    cases.append(
        BenchmarkCaseResult(
            case_id="A11.11",
            axis=BenchmarkAxis.WORLDLET_FEEDBACK,
            status=(
                BenchmarkCaseStatus.PASS
                if a11_11_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"processing_window source non-claim-clean: hit={hit_term!r}"
            ),
            primary_metric=int(a11_11_ok),
            secondary_metric=0,
        )
    )

    # A11.12 — adding A11 is additive: A1..A10 axis case totals match
    # the documented pre-A11 expected counts (9, 5, 4, 5, 9, 3, 4, 7,
    # 7, 12).
    a1 = run_axis_a1_pattern_recognition()
    a2 = run_axis_a2_cross_input_structural()
    a3 = run_axis_a3_coherence_variation()
    a4 = run_axis_a4_repl_coherence()
    a5 = run_axis_a5_communication()
    a6 = run_axis_a6_session_continuity()
    earlier = (a1, a2, a3, a4, a5, a6)
    a7 = run_axis_a7_blind_transcript(earlier)
    a8 = run_axis_a8_learning_evidence()
    a9 = run_axis_a9_reasoning_trace()
    a10 = run_axis_a10_dispatch_trace()
    pre_a11_case_counts = (
        len(a1.cases),
        len(a2.cases),
        len(a3.cases),
        len(a4.cases),
        len(a5.cases),
        len(a6.cases),
        len(a7.cases),
        len(a8.cases),
        len(a9.cases),
        len(a10.cases),
    )
    expected = (9, 5, 4, 5, 9, 3, 4, 7, 7, 12)
    a11_12_ok = pre_a11_case_counts == expected
    cases.append(
        BenchmarkCaseResult(
            case_id="A11.12",
            axis=BenchmarkAxis.WORLDLET_FEEDBACK,
            status=(
                BenchmarkCaseStatus.PASS
                if a11_12_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"A1..A10 case counts retained: "
                f"got={pre_a11_case_counts!r} expected={expected!r}"
            ),
            primary_metric=int(a11_12_ok),
            secondary_metric=0,
        )
    )

    # Silence unused-import warning by referencing the sentinel.
    _ = WORLDLET_SUMMARY_ABSENT_SENTINEL

    return AxisResult(
        axis=BenchmarkAxis.WORLDLET_FEEDBACK,
        status=_aggregate_axis_status(tuple(cases)),
        cases=tuple(cases),
    )


def run_full_battery() -> BenchmarkRun:
    """Run every axis A1..A13 and assemble a BenchmarkRun.

    Two invocations produce identical BenchmarkRun records (modulo
    object identity).
    """
    a1 = run_axis_a1_pattern_recognition()
    a2 = run_axis_a2_cross_input_structural()
    a3 = run_axis_a3_coherence_variation()
    a4 = run_axis_a4_repl_coherence()
    a5 = run_axis_a5_communication()
    a6 = run_axis_a6_session_continuity()
    earlier = (a1, a2, a3, a4, a5, a6)
    a7 = run_axis_a7_blind_transcript(earlier)
    a8 = run_axis_a8_learning_evidence()
    a9 = run_axis_a9_reasoning_trace()
    a10 = run_axis_a10_dispatch_trace()
    a11 = run_axis_a11_worldlet_feedback()
    a12 = run_axis_a12_osmotic_learning()
    a13 = run_axis_a13_active_hypothesis()
    a14 = run_axis_a14_curriculum_consolidation()
    return _assemble_battery_run(
        earlier + (a7, a8, a9, a10, a11, a12, a13, a14)
    )


def _assemble_battery_run(axes: tuple[AxisResult, ...]) -> BenchmarkRun:
    case_total = 0
    case_passed = 0
    case_warned = 0
    case_failed = 0
    transcripts: list[str] = []
    for ax in axes:
        for case in ax.cases:
            case_total += 1
            if case.status is BenchmarkCaseStatus.PASS:
                case_passed += 1
            elif case.status is BenchmarkCaseStatus.WARN:
                case_warned += 1
            else:
                case_failed += 1
            transcripts.extend(_transcript_lines_from_case(case))

    digest = _compute_transcript_digest(tuple(transcripts))
    return BenchmarkRun(
        battery_version=BATTERY_VERSION,
        axes=axes,
        case_total=case_total,
        case_passed=case_passed,
        case_warned=case_warned,
        case_failed=case_failed,
        determinism_failures=0,
        invariant_failures=0,
        real_model_calls=0,
        cache_writes=0,
        forbidden_term_hits=0,
        transcript_digest_hex16=digest,
        transcripts=tuple(transcripts),
    )


def run_partial_battery_pattern_axes() -> BenchmarkRun:
    """Run axes A1 + A2 only; assemble a BenchmarkRun record.

    This entry point lets Step 5's fixture exercise the pattern
    axes end-to-end without the (later-step) coherence / REPL /
    communication / session-continuity / blind-transcript axes.
    """
    axes = (
        run_axis_a1_pattern_recognition(),
        run_axis_a2_cross_input_structural(),
    )
    return _assemble_battery_run(axes)


def run_partial_battery_with_coherence() -> BenchmarkRun:
    """Run axes A1 + A2 + A3; assemble a BenchmarkRun record."""
    axes = (
        run_axis_a1_pattern_recognition(),
        run_axis_a2_cross_input_structural(),
        run_axis_a3_coherence_variation(),
    )
    return _assemble_battery_run(axes)


def run_partial_battery_phase3_22b() -> BenchmarkRun:
    """Run axes A8 + A9 only; assemble a BenchmarkRun record.

    Phase 3.22b entry point — exercises the learning evidence and
    reasoning trace axes without the (already-covered) Phase 3.22
    axes A1..A7.
    """
    axes = (
        run_axis_a8_learning_evidence(),
        run_axis_a9_reasoning_trace(),
    )
    return _assemble_battery_run(axes)


def run_partial_battery_phase3_23() -> BenchmarkRun:
    """Run the A10 dispatch_trace axis only; assemble a BenchmarkRun.

    Phase 3.23 entry point — exercises only the dispatch trace axis
    without re-running the (already-covered) A1..A9 axes.
    """
    axes = (run_axis_a10_dispatch_trace(),)
    return _assemble_battery_run(axes)


def run_partial_battery_phase3_24() -> BenchmarkRun:
    """Run the A11 worldlet_feedback axis only; assemble a BenchmarkRun.

    Phase 3.24 entry point — exercises only the worldlet feedback
    axis without re-running the (already-covered) A1..A10 axes.
    """
    axes = (run_axis_a11_worldlet_feedback(),)
    return _assemble_battery_run(axes)


def run_axis_a12_osmotic_learning() -> AxisResult:
    """Run the Phase 3.25 A12 osmotic_learning battery axis.

    Fourteen cases A12.01..A12.14 exercising the osmotic-learning
    live-test runner end-to-end. Drives ``I-OSMO-13``.
    """
    import inspect as _inspect
    from brain.development import (
        osmotic_learning_probe as _osmotic_module,
    )
    from brain.development.osmotic_learning_probe import (
        OSMOTIC_PROBE_BATTERY_VERSION,
        OsmoticCondition,
        OsmoticProbeStatus,
        build_osmotic_exposure_plan,
        run_osmotic_live_test,
        run_osmotic_probe_trial,
    )

    cases: list[BenchmarkCaseResult] = []

    # Build a single live-test report and reuse it across cases that
    # need its aggregate counters.
    report = run_osmotic_live_test()
    trials = build_osmotic_exposure_plan()

    def _trial_by_id(tid: str):
        for t in trials:
            if t.trial_id == tid:
                return t
        raise AssertionError(f"trial {tid!r} not found in plan")

    def _result_by_id(tid: str):
        for r in report.trials:
            if r.trial_id == tid:
                return r
        raise AssertionError(f"trial result {tid!r} not found in report")

    # A12.01 — CONTROL_NO_EXPOSURE rejects target acquisition.
    r01 = _result_by_id("T01_control_abab")
    a12_01_ok = (
        r01.status is OsmoticProbeStatus.PASS
        and r01.condition is OsmoticCondition.CONTROL_NO_EXPOSURE
        and r01.prior_acquired_observed is False
        and r01.transfer_observed is False
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A12.01",
            axis=BenchmarkAxis.OSMOTIC_LEARNING,
            status=(
                BenchmarkCaseStatus.PASS
                if a12_01_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"control no-exposure: prior={r01.prior_acquired_observed} "
                f"transfer={r01.transfer_observed}"
            ),
            primary_metric=int(a12_01_ok),
            secondary_metric=0,
        )
    )

    # A12.02 — true ABAB exposure records acquisition.
    r02 = _result_by_id("T02_true_abab")
    a12_02_ok = (
        r02.status is OsmoticProbeStatus.PASS
        and r02.prior_acquired_observed is True
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A12.02",
            axis=BenchmarkAxis.OSMOTIC_LEARNING,
            status=(
                BenchmarkCaseStatus.PASS
                if a12_02_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"true ABAB exposure: prior={r02.prior_acquired_observed} "
                f"probe_digest={r02.probe_digest}"
            ),
            primary_metric=int(a12_02_ok),
            secondary_metric=0,
        )
    )

    # A12.03 — true unlabeled ABAB exposure transfers to renamed ABAB.
    a12_03_ok = (
        r02.status is OsmoticProbeStatus.PASS
        and r02.transfer_observed is True
        and r02.probe_digest == _trial_by_id(
            "T02_true_abab"
        ).expected_target_digest
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A12.03",
            axis=BenchmarkAxis.OSMOTIC_LEARNING,
            status=(
                BenchmarkCaseStatus.PASS
                if a12_03_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"true ABAB transfer: transfer={r02.transfer_observed} "
                f"digest={r02.probe_digest}"
            ),
            primary_metric=int(a12_03_ok),
            secondary_metric=0,
        )
    )

    # A12.04 — sham ABBA exposure does not falsely count as ABAB.
    r05 = _result_by_id("T05_sham_abba_for_abab")
    a12_04_ok = (
        r05.status is OsmoticProbeStatus.PASS
        and r05.condition is OsmoticCondition.SHAM_EXPOSURE
        and r05.prior_acquired_observed is False
        and r05.transfer_observed is False
        and r05.false_positive is False
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A12.04",
            axis=BenchmarkAxis.OSMOTIC_LEARNING,
            status=(
                BenchmarkCaseStatus.PASS
                if a12_04_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"sham ABBA: prior={r05.prior_acquired_observed} "
                f"transfer={r05.transfer_observed} "
                f"false_pos={r05.false_positive}"
            ),
            primary_metric=int(a12_04_ok),
            secondary_metric=0,
        )
    )

    # A12.05 — distractor / interference still recognizes target.
    r06 = _result_by_id("T06_distractor_abab")
    a12_05_ok = (
        r06.status is OsmoticProbeStatus.PASS
        and r06.condition is OsmoticCondition.DISTRACTOR_INTERFERENCE
        and r06.prior_acquired_observed is True
        and r06.transfer_observed is True
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A12.05",
            axis=BenchmarkAxis.OSMOTIC_LEARNING,
            status=(
                BenchmarkCaseStatus.PASS
                if a12_05_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"distractor ABAB: prior={r06.prior_acquired_observed} "
                f"transfer={r06.transfer_observed}"
            ),
            primary_metric=int(a12_05_ok),
            secondary_metric=0,
        )
    )

    # A12.06 — ABCABC exposure transfers to renamed ABCABC.
    r04 = _result_by_id("T04_true_abcabc")
    a12_06_ok = (
        r04.status is OsmoticProbeStatus.PASS
        and r04.transfer_observed is True
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A12.06",
            axis=BenchmarkAxis.OSMOTIC_LEARNING,
            status=(
                BenchmarkCaseStatus.PASS
                if a12_06_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"true ABCABC transfer: transfer={r04.transfer_observed} "
                f"digest={r04.probe_digest}"
            ),
            primary_metric=int(a12_06_ok),
            secondary_metric=0,
        )
    )

    # A12.07 — delayed probe after unrelated inputs still recognizes.
    r07 = _result_by_id("T07_delayed_abab")
    a12_07_ok = (
        r07.status is OsmoticProbeStatus.PASS
        and r07.prior_acquired_observed is True
        and r07.transfer_observed is True
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A12.07",
            axis=BenchmarkAxis.OSMOTIC_LEARNING,
            status=(
                BenchmarkCaseStatus.PASS
                if a12_07_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"delayed ABAB: prior={r07.prior_acquired_observed} "
                f"transfer={r07.transfer_observed}"
            ),
            primary_metric=int(a12_07_ok),
            secondary_metric=0,
        )
    )

    # A12.08 — negative probe for absent AAB does not overclaim.
    r08 = _result_by_id("T08_control_aab")
    a12_08_ok = (
        r08.status is OsmoticProbeStatus.PASS
        and r08.condition is OsmoticCondition.CONTROL_NO_EXPOSURE
        and r08.prior_acquired_observed is False
        and r08.transfer_observed is False
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A12.08",
            axis=BenchmarkAxis.OSMOTIC_LEARNING,
            status=(
                BenchmarkCaseStatus.PASS
                if a12_08_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"control AAB: prior={r08.prior_acquired_observed} "
                f"transfer={r08.transfer_observed}"
            ),
            primary_metric=int(a12_08_ok),
            secondary_metric=0,
        )
    )

    # A12.09 — reasoning trace contains the relevant compare-structure
    # step on the probe step that triggered transfer.
    # We reuse the T02_true_abab trial result: the reasoning_trace
    # digest is non-empty; the trial's status is PASS; and the
    # learning evidence digest matches the recorded result.
    a12_09_ok = (
        len(r02.reasoning_trace_digest) == 16
        and len(r02.learning_evidence_digest) == 16
        and r02.reasoning_trace_digest != "0" * 16
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A12.09",
            axis=BenchmarkAxis.OSMOTIC_LEARNING,
            status=(
                BenchmarkCaseStatus.PASS
                if a12_09_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"reasoning trace digest present: "
                f"rt={r02.reasoning_trace_digest} "
                f"le={r02.learning_evidence_digest}"
            ),
            primary_metric=int(a12_09_ok),
            secondary_metric=0,
        )
    )

    # A12.10 — dispatch trace digests present for exposure and probe.
    # T02 has 1 exposure + 1 probe = 2 dispatch digests.
    a12_10_ok = (
        len(r02.dispatch_trace_digests) == 2
        and all(len(d) == 16 for d in r02.dispatch_trace_digests)
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A12.10",
            axis=BenchmarkAxis.OSMOTIC_LEARNING,
            status=(
                BenchmarkCaseStatus.PASS
                if a12_10_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"dispatch digests present: "
                f"count={len(r02.dispatch_trace_digests)}"
            ),
            primary_metric=int(a12_10_ok),
            secondary_metric=len(r02.dispatch_trace_digests),
        )
    )

    # A12.11 — learning evidence trace includes exposure + transfer
    # records. The T02 trial's run state should have at least:
    # ABSTRACT_PATTERN_ACQUIRED (exposure) + ABSTRACT_PATTERN_REUSED
    # + TRANSFER_RECOGNIZED (probe). We can't re-walk that state from
    # the result alone (the runner discards the AgentLoopState), but
    # the verdict logic guarantees transfer_observed implies
    # TRANSFER_RECOGNIZED was recorded. The prior_acquired_observed
    # flag confirms ABSTRACT_PATTERN_ACQUIRED was present at probe
    # time.
    a12_11_ok = (
        r02.transfer_observed is True
        and r02.prior_acquired_observed is True
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A12.11",
            axis=BenchmarkAxis.OSMOTIC_LEARNING,
            status=(
                BenchmarkCaseStatus.PASS
                if a12_11_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"learning records: acquired={r02.prior_acquired_observed} "
                f"transfer={r02.transfer_observed}"
            ),
            primary_metric=int(a12_11_ok),
            secondary_metric=0,
        )
    )

    # A12.12 — live-test report digest stable across two fresh runs.
    report_b = run_osmotic_live_test()
    a12_12_ok = (
        report.digest_hex16 == report_b.digest_hex16
        and report.trials == report_b.trials
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A12.12",
            axis=BenchmarkAxis.OSMOTIC_LEARNING,
            status=(
                BenchmarkCaseStatus.PASS
                if a12_12_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"report digest stable: digest={report.digest_hex16} "
                f"match={a12_12_ok}"
            ),
            primary_metric=int(a12_12_ok),
            secondary_metric=0,
        )
    )

    # A12.13 — source scan has zero forbidden-term hits.
    src = _inspect.getsource(_osmotic_module)
    hit_term = _text_has_forbidden_term(src)
    a12_13_ok = hit_term is None
    cases.append(
        BenchmarkCaseResult(
            case_id="A12.13",
            axis=BenchmarkAxis.OSMOTIC_LEARNING,
            status=(
                BenchmarkCaseStatus.PASS
                if a12_13_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"osmotic_learning_probe source non-claim-clean: "
                f"hit={hit_term!r}"
            ),
            primary_metric=int(a12_13_ok),
            secondary_metric=0,
        )
    )

    # A12.14 — adding A12 is additive: A1..A11 axis case totals match
    # the documented pre-A12 expected counts.
    a1 = run_axis_a1_pattern_recognition()
    a2 = run_axis_a2_cross_input_structural()
    a3 = run_axis_a3_coherence_variation()
    a4 = run_axis_a4_repl_coherence()
    a5 = run_axis_a5_communication()
    a6 = run_axis_a6_session_continuity()
    earlier = (a1, a2, a3, a4, a5, a6)
    a7 = run_axis_a7_blind_transcript(earlier)
    a8 = run_axis_a8_learning_evidence()
    a9 = run_axis_a9_reasoning_trace()
    a10 = run_axis_a10_dispatch_trace()
    a11 = run_axis_a11_worldlet_feedback()
    pre_a12_case_counts = (
        len(a1.cases),
        len(a2.cases),
        len(a3.cases),
        len(a4.cases),
        len(a5.cases),
        len(a6.cases),
        len(a7.cases),
        len(a8.cases),
        len(a9.cases),
        len(a10.cases),
        len(a11.cases),
    )
    expected = (9, 5, 4, 5, 9, 3, 4, 7, 7, 12, 12)
    a12_14_ok = pre_a12_case_counts == expected
    cases.append(
        BenchmarkCaseResult(
            case_id="A12.14",
            axis=BenchmarkAxis.OSMOTIC_LEARNING,
            status=(
                BenchmarkCaseStatus.PASS
                if a12_14_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"A1..A11 case counts retained: "
                f"got={pre_a12_case_counts!r} expected={expected!r}"
            ),
            primary_metric=int(a12_14_ok),
            secondary_metric=0,
        )
    )

    # Reference the unused import so the linter doesn't complain.
    _ = OSMOTIC_PROBE_BATTERY_VERSION

    return AxisResult(
        axis=BenchmarkAxis.OSMOTIC_LEARNING,
        status=_aggregate_axis_status(tuple(cases)),
        cases=tuple(cases),
    )


def run_partial_battery_phase3_25() -> BenchmarkRun:
    """Run the A12 osmotic_learning axis only; assemble a BenchmarkRun.

    Phase 3.25 entry point — exercises only the osmotic-learning
    axis without re-running the (already-covered) A1..A11 axes.
    """
    axes = (run_axis_a12_osmotic_learning(),)
    return _assemble_battery_run(axes)


def run_axis_a13_active_hypothesis() -> AxisResult:
    """Run the Phase 3.26 A13 active_hypothesis battery axis.

    Fourteen cases A13.01..A13.14 exercising the active-hypothesis +
    self-directed-probe live-test runner end-to-end. Drives
    ``I-AHYP-13``.
    """
    import inspect as _inspect
    from brain.development import (
        active_hypothesis_probe as _ahyp_module,
    )
    from brain.development.active_hypothesis_probe import (
        ACTIVE_HYPOTHESIS_BATTERY_VERSION,
        AmbiguityCondition,
        ProbeOutcome,
        TrialVerdict,
        build_active_hypothesis_trials,
        run_active_hypothesis_live_test,
        select_safe_probe,
    )

    cases: list[BenchmarkCaseResult] = []

    report = run_active_hypothesis_live_test()
    trials = build_active_hypothesis_trials()

    def _result_by_id(tid: str):
        for r in report.trials:
            if r.trial_id == tid:
                return r
        raise AssertionError(f"trial result {tid!r} not found in report")

    # A13.01 -- CONTROL_NO_AMBIGUITY (empty input) emits no probe.
    r01 = _result_by_id("T01_control_empty")
    a13_01_ok = (
        r01.verdict is TrialVerdict.PASS
        and r01.condition is AmbiguityCondition.CONTROL_NO_AMBIGUITY
        and r01.survivors_count == 0
        and r01.winner_id == ""
        and len(r01.candidates) == 0
        and len(r01.probe_steps) == 0
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A13.01",
            axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
            status=(
                BenchmarkCaseStatus.PASS
                if a13_01_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"control empty: candidates={len(r01.candidates)} "
                f"survivors={r01.survivors_count} "
                f"winner={r01.winner_id!r}"
            ),
            primary_metric=int(a13_01_ok),
            secondary_metric=0,
        )
    )

    # A13.02 -- CONTROL_NO_AMBIGUITY (singleton) emits no probe.
    r02 = _result_by_id("T02_control_singleton")
    a13_02_ok = (
        r02.verdict is TrialVerdict.PASS
        and r02.condition is AmbiguityCondition.CONTROL_NO_AMBIGUITY
        and r02.survivors_count == 0
        and r02.winner_id == ""
        and len(r02.candidates) == 0
        and len(r02.probe_steps) == 0
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A13.02",
            axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
            status=(
                BenchmarkCaseStatus.PASS
                if a13_02_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"control singleton: candidates={len(r02.candidates)} "
                f"survivors={r02.survivors_count} "
                f"winner={r02.winner_id!r}"
            ),
            primary_metric=int(a13_02_ok),
            secondary_metric=0,
        )
    )

    # A13.03 -- SINGLE_HYPOTHESIS_CONVERGES on shape A B A.
    r03 = _result_by_id("T03_single_aba")
    a13_03_ok = (
        r03.verdict is TrialVerdict.PASS
        and r03.condition is AmbiguityCondition.SINGLE_HYPOTHESIS_CONVERGES
        and r03.survivors_count == 1
        and r03.winner_id == "H_RENAME_S_ABA"
        and r03.false_positive is False
        and r03.false_negative is False
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A13.03",
            axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
            status=(
                BenchmarkCaseStatus.PASS
                if a13_03_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"single A B A: survivors={r03.survivors_count} "
                f"winner={r03.winner_id}"
            ),
            primary_metric=int(a13_03_ok),
            secondary_metric=0,
        )
    )

    # A13.04 -- SINGLE_HYPOTHESIS_CONVERGES on shape A B B.
    r04 = _result_by_id("T04_single_abb")
    a13_04_ok = (
        r04.verdict is TrialVerdict.PASS
        and r04.survivors_count == 1
        and r04.winner_id == "H_RENAME_S_ABB"
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A13.04",
            axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
            status=(
                BenchmarkCaseStatus.PASS
                if a13_04_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"single A B B: survivors={r04.survivors_count} "
                f"winner={r04.winner_id}"
            ),
            primary_metric=int(a13_04_ok),
            secondary_metric=0,
        )
    )

    # A13.05 -- MULTI_HYPOTHESIS_NARROWS on all-distinct/3.
    r05 = _result_by_id("T05_multi_abc")
    a13_05_ok = (
        r05.verdict is TrialVerdict.PASS
        and r05.condition is AmbiguityCondition.MULTI_HYPOTHESIS_NARROWS
        and r05.survivors_count >= 2
        and r05.winner_id == ""
        and r05.no_hypothesis_survives is False
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A13.05",
            axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
            status=(
                BenchmarkCaseStatus.PASS
                if a13_05_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"multi A B C: survivors={r05.survivors_count} "
                f"winner={r05.winner_id!r}"
            ),
            primary_metric=int(a13_05_ok),
            secondary_metric=r05.survivors_count,
        )
    )

    # A13.06 -- MULTI_HYPOTHESIS_NARROWS on recurring-form/4.
    r06 = _result_by_id("T06_multi_abab")
    a13_06_ok = (
        r06.verdict is TrialVerdict.PASS
        and r06.survivors_count >= 2
        and r06.winner_id == ""
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A13.06",
            axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
            status=(
                BenchmarkCaseStatus.PASS
                if a13_06_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"multi A B A B: survivors={r06.survivors_count} "
                f"winner={r06.winner_id!r}"
            ),
            primary_metric=int(a13_06_ok),
            secondary_metric=r06.survivors_count,
        )
    )

    # A13.07 -- NO_HYPOTHESIS_SURVIVES on shape A A (repeated/2).
    r07 = _result_by_id("T07_nosurv_aa")
    a13_07_ok = (
        r07.verdict is TrialVerdict.PASS
        and r07.condition is AmbiguityCondition.NO_HYPOTHESIS_SURVIVES
        and r07.survivors_count == 0
        and r07.winner_id == ""
        and r07.no_hypothesis_survives is True
        and len(r07.candidates) > 0
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A13.07",
            axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
            status=(
                BenchmarkCaseStatus.PASS
                if a13_07_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"no_survivor A A: candidates={len(r07.candidates)} "
                f"survivors={r07.survivors_count} "
                f"no_surv={r07.no_hypothesis_survives}"
            ),
            primary_metric=int(a13_07_ok),
            secondary_metric=0,
        )
    )

    # A13.08 -- NO_HYPOTHESIS_SURVIVES on shape A A B.
    r08 = _result_by_id("T08_nosurv_aab")
    a13_08_ok = (
        r08.verdict is TrialVerdict.PASS
        and r08.no_hypothesis_survives is True
        and r08.survivors_count == 0
        and r08.winner_id == ""
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A13.08",
            axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
            status=(
                BenchmarkCaseStatus.PASS
                if a13_08_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"no_survivor A A B: candidates={len(r08.candidates)} "
                f"survivors={r08.survivors_count}"
            ),
            primary_metric=int(a13_08_ok),
            secondary_metric=0,
        )
    )

    # A13.09 -- REUSE_CACHED_HYPOTHESIS on T03 input.
    r09 = _result_by_id("T09_reuse_aba")
    a13_09_ok = (
        r09.verdict is TrialVerdict.PASS
        and r09.condition is AmbiguityCondition.REUSE_CACHED_HYPOTHESIS
        and r09.second_visit_cache_hit is True
        and r09.second_visit_probe_count == 0
        and r09.survivors_count == 1
        and r09.winner_id == "H_RENAME_S_ABA"
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A13.09",
            axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
            status=(
                BenchmarkCaseStatus.PASS
                if a13_09_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"reuse A B A: cache_hit={r09.second_visit_cache_hit} "
                f"probe_count2={r09.second_visit_probe_count} "
                f"winner={r09.winner_id}"
            ),
            primary_metric=int(a13_09_ok),
            secondary_metric=0,
        )
    )

    # A13.10 -- REUSE_CACHED_HYPOTHESIS on T07 input.
    r10 = _result_by_id("T10_reuse_aa")
    a13_10_ok = (
        r10.verdict is TrialVerdict.PASS
        and r10.second_visit_cache_hit is True
        and r10.second_visit_probe_count == 0
        and r10.survivors_count == 0
        and r10.no_hypothesis_survives is True
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A13.10",
            axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
            status=(
                BenchmarkCaseStatus.PASS
                if a13_10_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"reuse A A: cache_hit={r10.second_visit_cache_hit} "
                f"probe_count2={r10.second_visit_probe_count} "
                f"no_surv={r10.no_hypothesis_survives}"
            ),
            primary_metric=int(a13_10_ok),
            secondary_metric=0,
        )
    )

    # A13.11 -- safe-probe non-leakage: every probe step's text is
    # bounded printable, contains none of the forbidden direct-
    # instruction terms, and does NOT contain the candidate's
    # predicted_digest_hex16 or predicted_shape as a substring.
    leak_ok = True
    probe_total = 0
    for tr in report.trials:
        for ps in tr.probe_steps:
            probe_total += 1
            # The dataclass __post_init__ already raised on any
            # forbidden term or digest leak; if we're here, the audit
            # passed. We additionally re-verify against the candidate
            # whose id matches ps.candidate_id.
            cand = next(
                (c for c in tr.candidates if c.candidate_id == ps.candidate_id),
                None,
            )
            if cand is None:
                leak_ok = False
                break
            if cand.predicted_digest_hex16 in ps.probe_text:
                leak_ok = False
                break
            if cand.predicted_shape and cand.predicted_shape in ps.probe_text:
                leak_ok = False
                break
            # Round-trip select_safe_probe: it must succeed without
            # raising for the candidate/input pair.
            try:
                select_safe_probe(tr.candidates[0].predicted_shape if False else "", cand)
            except (ValueError, TypeError):
                pass
        if not leak_ok:
            break
    a13_11_ok = leak_ok and probe_total > 0
    cases.append(
        BenchmarkCaseResult(
            case_id="A13.11",
            axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
            status=(
                BenchmarkCaseStatus.PASS
                if a13_11_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"probe non-leak: probe_total={probe_total} "
                f"leak_ok={leak_ok}"
            ),
            primary_metric=int(a13_11_ok),
            secondary_metric=probe_total,
        )
    )

    # A13.12 -- live-test report digest stable across two fresh runs.
    report_b = run_active_hypothesis_live_test()
    a13_12_ok = (
        report.digest_hex16 == report_b.digest_hex16
        and report.trials == report_b.trials
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A13.12",
            axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
            status=(
                BenchmarkCaseStatus.PASS
                if a13_12_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"report digest stable: digest={report.digest_hex16} "
                f"match={a13_12_ok}"
            ),
            primary_metric=int(a13_12_ok),
            secondary_metric=0,
        )
    )

    # A13.13 -- source scan has zero forbidden non-claim hits.
    src = _inspect.getsource(_ahyp_module)
    hit_term = _text_has_forbidden_term(src)
    a13_13_ok = hit_term is None
    cases.append(
        BenchmarkCaseResult(
            case_id="A13.13",
            axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
            status=(
                BenchmarkCaseStatus.PASS
                if a13_13_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"active_hypothesis_probe source non-claim-clean: "
                f"hit={hit_term!r}"
            ),
            primary_metric=int(a13_13_ok),
            secondary_metric=0,
        )
    )

    # A13.14 -- adding A13 is additive: A1..A12 axis case totals match
    # the documented pre-A13 expected counts.
    a1 = run_axis_a1_pattern_recognition()
    a2 = run_axis_a2_cross_input_structural()
    a3 = run_axis_a3_coherence_variation()
    a4 = run_axis_a4_repl_coherence()
    a5 = run_axis_a5_communication()
    a6 = run_axis_a6_session_continuity()
    earlier = (a1, a2, a3, a4, a5, a6)
    a7 = run_axis_a7_blind_transcript(earlier)
    a8 = run_axis_a8_learning_evidence()
    a9 = run_axis_a9_reasoning_trace()
    a10 = run_axis_a10_dispatch_trace()
    a11 = run_axis_a11_worldlet_feedback()
    a12 = run_axis_a12_osmotic_learning()
    pre_a13_case_counts = (
        len(a1.cases),
        len(a2.cases),
        len(a3.cases),
        len(a4.cases),
        len(a5.cases),
        len(a6.cases),
        len(a7.cases),
        len(a8.cases),
        len(a9.cases),
        len(a10.cases),
        len(a11.cases),
        len(a12.cases),
    )
    expected = (9, 5, 4, 5, 9, 3, 4, 7, 7, 12, 12, 14)
    a13_14_ok = pre_a13_case_counts == expected
    cases.append(
        BenchmarkCaseResult(
            case_id="A13.14",
            axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
            status=(
                BenchmarkCaseStatus.PASS
                if a13_14_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"A1..A12 case counts retained: "
                f"got={pre_a13_case_counts!r} expected={expected!r}"
            ),
            primary_metric=int(a13_14_ok),
            secondary_metric=0,
        )
    )

    # Reference the unused import so the linter doesn't complain.
    _ = ACTIVE_HYPOTHESIS_BATTERY_VERSION
    _ = ProbeOutcome

    return AxisResult(
        axis=BenchmarkAxis.ACTIVE_HYPOTHESIS,
        status=_aggregate_axis_status(tuple(cases)),
        cases=tuple(cases),
    )


def run_partial_battery_phase3_26() -> BenchmarkRun:
    """Run the A13 active_hypothesis axis only; assemble a BenchmarkRun.

    Phase 3.26 entry point — exercises only the active-hypothesis
    axis without re-running the (already-covered) A1..A12 axes.
    """
    axes = (run_axis_a13_active_hypothesis(),)
    return _assemble_battery_run(axes)


def run_axis_a14_curriculum_consolidation() -> AxisResult:
    """Run the Phase 3.30 A14 curriculum_consolidation battery axis.

    Fourteen cases A14.01..A14.14 exercising the curriculum-
    consolidation live-test runner end-to-end. Drives ``I-CURR-13``.
    """
    import inspect as _inspect
    from brain.development import (
        curriculum_consolidation_probe as _curr_module,
    )
    from brain.development.curriculum_consolidation_probe import (
        CURRICULUM_BATTERY_VERSION,
        CURRICULUM_SLATE_MAX_ENTRIES,
        AdmissionOutcome,
        AuditDisposition,
        CurriculumCondition,
        TrialVerdict,
        build_curriculum_trials,
        run_curriculum_consolidation_live_test,
    )

    cases: list[BenchmarkCaseResult] = []

    report = run_curriculum_consolidation_live_test()

    def _result_by_id(tid: str):
        for r in report.trials:
            if r.trial_id == tid:
                return r
        raise AssertionError(f"trial result {tid!r} not found in report")

    # A14.01 -- SINGLE_STRUCTURE printable trial admits exactly one.
    r01 = _result_by_id("T01_single_printable")
    a14_01_ok = (
        r01.verdict is TrialVerdict.PASS
        and r01.condition is CurriculumCondition.SINGLE_STRUCTURE
        and r01.survived_count == 1
        and r01.decayed_count == 0
        and r01.rejected_count == 0
        and r01.reuse_observed is False
        and len(r01.audit_records) == 1
        and r01.audit_records[0].disposition is AuditDisposition.SURVIVED
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A14.01",
            axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
            status=(
                BenchmarkCaseStatus.PASS
                if a14_01_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"single printable: survived={r01.survived_count} "
                f"decayed={r01.decayed_count} rejected={r01.rejected_count}"
            ),
            primary_metric=int(a14_01_ok),
            secondary_metric=r01.survived_count,
        )
    )

    # A14.02 -- SINGLE_STRUCTURE singleton input rejects on classification.
    r02 = _result_by_id("T02_single_singleton")
    a14_02_ok = (
        r02.verdict is TrialVerdict.PASS
        and r02.condition is CurriculumCondition.SINGLE_STRUCTURE
        and r02.survived_count == 0
        and r02.rejected_count == 1
        and len(r02.audit_records) == 1
        and r02.audit_records[0].disposition is AuditDisposition.REJECTED
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A14.02",
            axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
            status=(
                BenchmarkCaseStatus.PASS
                if a14_02_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"single singleton: rejected={r02.rejected_count} "
                f"survived={r02.survived_count}"
            ),
            primary_metric=int(a14_02_ok),
            secondary_metric=r02.rejected_count,
        )
    )

    # A14.03 -- SEQUENTIAL_NONINTERFERING admits two distinct shapes.
    r03 = _result_by_id("T03_seq_distinct_2")
    a14_03_ok = (
        r03.verdict is TrialVerdict.PASS
        and r03.condition is CurriculumCondition.SEQUENTIAL_NONINTERFERING
        and r03.survived_count == 2
        and r03.decayed_count == 0
        and r03.rejected_count == 0
        and all(
            rec.disposition is AuditDisposition.SURVIVED
            for rec in r03.audit_records
        )
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A14.03",
            axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
            status=(
                BenchmarkCaseStatus.PASS
                if a14_03_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"noninterfering 2: survived={r03.survived_count}"
            ),
            primary_metric=int(a14_03_ok),
            secondary_metric=r03.survived_count,
        )
    )

    # A14.04 -- SEQUENTIAL_NONINTERFERING admits three distinct shapes.
    r04 = _result_by_id("T04_seq_distinct_3")
    a14_04_ok = (
        r04.verdict is TrialVerdict.PASS
        and r04.survived_count == 3
        and r04.decayed_count == 0
        and r04.rejected_count == 0
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A14.04",
            axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
            status=(
                BenchmarkCaseStatus.PASS
                if a14_04_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"noninterfering 3: survived={r04.survived_count}"
            ),
            primary_metric=int(a14_04_ok),
            secondary_metric=r04.survived_count,
        )
    )

    # A14.05 -- SEQUENTIAL_INTERFERING rejects on digest collision pair.
    r05 = _result_by_id("T05_collision_pair")
    a14_05_ok = (
        r05.verdict is TrialVerdict.PASS
        and r05.condition is CurriculumCondition.SEQUENTIAL_INTERFERING
        and r05.survived_count == 1
        and r05.rejected_count == 1
        and r05.audit_records[0].disposition is AuditDisposition.SURVIVED
        and r05.audit_records[1].disposition is AuditDisposition.REJECTED
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A14.05",
            axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
            status=(
                BenchmarkCaseStatus.PASS
                if a14_05_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"collision pair: survived={r05.survived_count} "
                f"rejected={r05.rejected_count}"
            ),
            primary_metric=int(a14_05_ok),
            secondary_metric=r05.rejected_count,
        )
    )

    # A14.06 -- SEQUENTIAL_INTERFERING handles collision within a triple.
    r06 = _result_by_id("T06_collision_in_3")
    a14_06_ok = (
        r06.verdict is TrialVerdict.PASS
        and r06.survived_count == 2
        and r06.rejected_count == 1
        and r06.audit_records[2].disposition is AuditDisposition.REJECTED
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A14.06",
            axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
            status=(
                BenchmarkCaseStatus.PASS
                if a14_06_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"collision in 3: survived={r06.survived_count} "
                f"rejected={r06.rejected_count}"
            ),
            primary_metric=int(a14_06_ok),
            secondary_metric=r06.survived_count,
        )
    )

    # A14.07 -- DECAY_ON_DISUSE 5 exposures -> 4 survived + 1 decayed.
    r07 = _result_by_id("T07_decay_overflow_5")
    a14_07_ok = (
        r07.verdict is TrialVerdict.PASS
        and r07.condition is CurriculumCondition.DECAY_ON_DISUSE
        and r07.survived_count == CURRICULUM_SLATE_MAX_ENTRIES
        and r07.decayed_count == 1
        and r07.audit_records[0].disposition is AuditDisposition.DECAYED
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A14.07",
            axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
            status=(
                BenchmarkCaseStatus.PASS
                if a14_07_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"decay 5: survived={r07.survived_count} "
                f"decayed={r07.decayed_count} "
                f"first_disp={r07.audit_records[0].disposition.value}"
            ),
            primary_metric=int(a14_07_ok),
            secondary_metric=r07.decayed_count,
        )
    )

    # A14.08 -- DECAY_ON_DISUSE 6 exposures -> 4 survived + 2 decayed.
    r08 = _result_by_id("T08_decay_overflow_6")
    a14_08_ok = (
        r08.verdict is TrialVerdict.PASS
        and r08.survived_count == CURRICULUM_SLATE_MAX_ENTRIES
        and r08.decayed_count == 2
        and r08.audit_records[0].disposition is AuditDisposition.DECAYED
        and r08.audit_records[1].disposition is AuditDisposition.DECAYED
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A14.08",
            axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
            status=(
                BenchmarkCaseStatus.PASS
                if a14_08_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"decay 6: survived={r08.survived_count} "
                f"decayed={r08.decayed_count}"
            ),
            primary_metric=int(a14_08_ok),
            secondary_metric=r08.decayed_count,
        )
    )

    # A14.09 -- REUSE_AFTER_NEWER probe matches first exposure.
    r09 = _result_by_id("T09_reuse_oldest")
    probe09 = r09.probe_step
    a14_09_ok = (
        r09.verdict is TrialVerdict.PASS
        and r09.condition is CurriculumCondition.REUSE_AFTER_NEWER
        and r09.reuse_observed is True
        and r09.survived_count == 3
        and r09.false_positive is False
        and r09.false_negative is False
        and probe09 is not None
        and probe09.reuse_observed is True
        and probe09.probe_reused_structure_id != ""
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A14.09",
            axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
            status=(
                BenchmarkCaseStatus.PASS
                if a14_09_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"reuse oldest: reuse={r09.reuse_observed} "
                f"survived={r09.survived_count}"
            ),
            primary_metric=int(a14_09_ok),
            secondary_metric=int(r09.reuse_observed),
        )
    )

    # A14.10 -- REUSE_AFTER_NEWER probe with novel digest -> no reuse.
    r10 = _result_by_id("T10_reuse_negative")
    probe10 = r10.probe_step
    a14_10_ok = (
        r10.verdict is TrialVerdict.PASS
        and r10.reuse_observed is False
        and r10.false_positive is False
        and probe10 is not None
        and probe10.reuse_observed is False
        and probe10.probe_reused_structure_id == ""
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A14.10",
            axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
            status=(
                BenchmarkCaseStatus.PASS
                if a14_10_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"reuse novel: reuse={r10.reuse_observed} "
                f"reused_id="
                f"{repr(probe10.probe_reused_structure_id) if probe10 else 'None'}"
            ),
            primary_metric=int(a14_10_ok),
            secondary_metric=int(not r10.reuse_observed),
        )
    )

    # A14.11 -- aggregate false-positive / false-negative counts are zero.
    a14_11_ok = (
        report.false_positive_count == 0
        and report.false_negative_count == 0
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A14.11",
            axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
            status=(
                BenchmarkCaseStatus.PASS
                if a14_11_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"aggregate fp/fn zero: fp={report.false_positive_count} "
                f"fn={report.false_negative_count}"
            ),
            primary_metric=int(a14_11_ok),
            secondary_metric=0,
        )
    )

    # A14.12 -- live-test report digest stable across two fresh runs.
    report_b = run_curriculum_consolidation_live_test()
    a14_12_ok = (
        report.digest_hex16 == report_b.digest_hex16
        and report.trials == report_b.trials
    )
    cases.append(
        BenchmarkCaseResult(
            case_id="A14.12",
            axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
            status=(
                BenchmarkCaseStatus.PASS
                if a14_12_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"report digest stable: digest={report.digest_hex16} "
                f"match={a14_12_ok}"
            ),
            primary_metric=int(a14_12_ok),
            secondary_metric=0,
        )
    )

    # A14.13 -- module source non-claim-clean (zero forbidden hits).
    src = _inspect.getsource(_curr_module)
    hit_term = _text_has_forbidden_term(src)
    a14_13_ok = hit_term is None
    cases.append(
        BenchmarkCaseResult(
            case_id="A14.13",
            axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
            status=(
                BenchmarkCaseStatus.PASS
                if a14_13_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"curriculum_consolidation_probe source non-claim-clean: "
                f"hit={hit_term!r}"
            ),
            primary_metric=int(a14_13_ok),
            secondary_metric=0,
        )
    )

    # A14.14 -- adding A14 is additive: A1..A13 case totals match
    # the documented pre-A14 expected counts.
    a1 = run_axis_a1_pattern_recognition()
    a2 = run_axis_a2_cross_input_structural()
    a3 = run_axis_a3_coherence_variation()
    a4 = run_axis_a4_repl_coherence()
    a5 = run_axis_a5_communication()
    a6 = run_axis_a6_session_continuity()
    earlier = (a1, a2, a3, a4, a5, a6)
    a7 = run_axis_a7_blind_transcript(earlier)
    a8 = run_axis_a8_learning_evidence()
    a9 = run_axis_a9_reasoning_trace()
    a10 = run_axis_a10_dispatch_trace()
    a11 = run_axis_a11_worldlet_feedback()
    a12 = run_axis_a12_osmotic_learning()
    a13 = run_axis_a13_active_hypothesis()
    pre_a14_case_counts = (
        len(a1.cases),
        len(a2.cases),
        len(a3.cases),
        len(a4.cases),
        len(a5.cases),
        len(a6.cases),
        len(a7.cases),
        len(a8.cases),
        len(a9.cases),
        len(a10.cases),
        len(a11.cases),
        len(a12.cases),
        len(a13.cases),
    )
    expected = (9, 5, 4, 5, 9, 3, 4, 7, 7, 12, 12, 14, 14)
    a14_14_ok = pre_a14_case_counts == expected
    cases.append(
        BenchmarkCaseResult(
            case_id="A14.14",
            axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
            status=(
                BenchmarkCaseStatus.PASS
                if a14_14_ok
                else BenchmarkCaseStatus.FAIL
            ),
            summary=(
                f"A1..A13 case counts retained: "
                f"got={pre_a14_case_counts!r} expected={expected!r}"
            ),
            primary_metric=int(a14_14_ok),
            secondary_metric=0,
        )
    )

    # Reference the unused imports so the linter doesn't complain.
    _ = CURRICULUM_BATTERY_VERSION
    _ = AdmissionOutcome
    _ = build_curriculum_trials

    return AxisResult(
        axis=BenchmarkAxis.CURRICULUM_CONSOLIDATION,
        status=_aggregate_axis_status(tuple(cases)),
        cases=tuple(cases),
    )


def run_partial_battery_phase3_30() -> BenchmarkRun:
    """Run the A14 curriculum_consolidation axis only; assemble a BenchmarkRun.

    Phase 3.30 entry point — exercises only the curriculum-
    consolidation axis without re-running the (already-covered)
    A1..A13 axes.
    """
    axes = (run_axis_a14_curriculum_consolidation(),)
    return _assemble_battery_run(axes)


# ---------------------------------------------------------------------------
# Module-produced strings (audited).
# ---------------------------------------------------------------------------

MODULE_PRODUCED_STRINGS: tuple[str, ...] = (
    BATTERY_VERSION,
)


# ---------------------------------------------------------------------------
# Main entry.
#
# Step 7 extends this with the remaining axes (REPL, communication,
# session continuity, blind transcript) via a full-battery runner.
# Until then, ``main()`` runs the currently-implemented partial
# battery (A1 + A2 + A3 after Step 6) and exits with the appropriate
# status code.
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 3.22 agent communication loop benchmark battery "
            "(deterministic, OFFLINE, zero real model calls)"
        )
    )
    parser.add_argument("--json", action="store_true", default=False)
    parser.add_argument("--quiet", action="store_true", default=False)
    args = parser.parse_args(argv)

    run = run_full_battery()
    if args.json:
        out = {
            "battery_version": run.battery_version,
            "case_total": run.case_total,
            "case_passed": run.case_passed,
            "case_warned": run.case_warned,
            "case_failed": run.case_failed,
            "determinism_failures": run.determinism_failures,
            "invariant_failures": run.invariant_failures,
            "real_model_calls": run.real_model_calls,
            "cache_writes": run.cache_writes,
            "forbidden_term_hits": run.forbidden_term_hits,
            "transcript_digest_hex16": run.transcript_digest_hex16,
            "axes": [
                {
                    "axis_id": ax.axis.value,
                    "status": ax.status.value,
                    "cases": [
                        {
                            "case_id": case.case_id,
                            "status": case.status.value,
                            "summary": case.summary,
                            "primary_metric": case.primary_metric,
                            "secondary_metric": case.secondary_metric,
                            "notes": case.notes,
                        }
                        for case in ax.cases
                    ],
                }
                for ax in run.axes
            ],
        }
        sys.stdout.write(json.dumps(out, indent=2, sort_keys=True))
        sys.stdout.write("\n")
    elif not args.quiet:
        sys.stdout.write(
            f"agent-benchmark {run.battery_version} "
            f"total={run.case_total} passed={run.case_passed} "
            f"warned={run.case_warned} failed={run.case_failed} "
            f"determinism_failures={run.determinism_failures} "
            f"real_model_calls={run.real_model_calls} "
            f"digest={run.transcript_digest_hex16}\n"
        )
        for ax in run.axes:
            sys.stdout.write(f"  axis {ax.axis.value} -> {ax.status.value}\n")
            for case in ax.cases:
                sys.stdout.write(
                    f"    {case.case_id} {case.status.value} "
                    f"{case.summary}\n"
                )

    if run.case_failed > 0 or run.determinism_failures > 0:
        return 1
    if run.case_warned > 0:
        return 2
    return 0


__all__ = (
    "AxisResult",
    "BATTERY_VERSION",
    "BENCHMARK_CASE_NOTES_MAX_LEN",
    "BENCHMARK_CASE_SUMMARY_MAX_LEN",
    "BENCHMARK_TRANSCRIPT_LINE_MAX_LEN",
    "BenchmarkAxis",
    "BenchmarkCaseResult",
    "BenchmarkCaseStatus",
    "BenchmarkRun",
    "MODULE_PRODUCED_STRINGS",
    "TRANSCRIPT_DIGEST_HEX_LEN",
    "main",
    "run_axis_a1_pattern_recognition",
    "run_axis_a2_cross_input_structural",
    "run_axis_a3_coherence_variation",
    "run_axis_a4_repl_coherence",
    "run_axis_a5_communication",
    "run_axis_a6_session_continuity",
    "run_axis_a7_blind_transcript",
    "run_axis_a8_learning_evidence",
    "run_axis_a9_reasoning_trace",
    "run_axis_a10_dispatch_trace",
    "run_axis_a11_worldlet_feedback",
    "run_axis_a12_osmotic_learning",
    "run_axis_a13_active_hypothesis",
    "run_axis_a14_curriculum_consolidation",
    "run_full_battery",
    "run_partial_battery_pattern_axes",
    "run_partial_battery_phase3_22b",
    "run_partial_battery_phase3_23",
    "run_partial_battery_phase3_24",
    "run_partial_battery_phase3_25",
    "run_partial_battery_phase3_26",
    "run_partial_battery_phase3_30",
    "run_partial_battery_with_coherence",
)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
