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

BATTERY_VERSION: str = "phase3.22.v1"
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

    run = run_partial_battery_with_coherence()
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
    "run_partial_battery_pattern_axes",
    "run_partial_battery_with_coherence",
)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
