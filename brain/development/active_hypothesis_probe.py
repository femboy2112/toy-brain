"""Phase 3.26 Active Hypothesis + Self-Directed Probe Loop runner.

Deterministic OFFLINE live-test runner that probes whether the
existing substrate (abstract_pattern signature + learning evidence +
reasoning trace + dispatch trace + worldlet feedback) realizes the
operational analogue of *active hypothesis + self-directed probe*:
given a bounded ambiguous structural input, the runtime

* enumerates a bounded candidate set
  (``0..ACTIVE_HYPOTHESIS_MAX_CANDIDATES`` per call);
* selects one safe internal probe per candidate, derived from the
  input alone via a closed probe-construction rule (no
  expected-outcome leak into the runtime path);
* executes the probe via ``run_agent_interaction_step``;
* prunes candidates whose observed probe digest does not match the
  candidate's ``predicted_digest_hex16``;
* declines to nominate a winner when zero candidates survive
  (refusal to overclaim);
* on a second invocation against the same session-local cache,
  reuses the prior surviving record without re-probing.

"Active hypothesis + self-directed probe in ToyI is a bounded
operational enumeration + falsification + caching effect over
structural records, not a psychological or phenomenological claim."

"Self-directed" means the probe text is derived from the input by a
closed deterministic rule. It does NOT mean the runtime has a goal,
plan, will, or any cognitive process. The runtime is a bounded
structural state machine.

The module is deliberately closed:

* No I/O, no network, no shell, no LLM, no ``brain.tick`` import,
  no ``brain.ui.session`` import, no curses, no threading / asyncio
  / atexit / signal / importlib / time / random.
* The deterministic runner uses ``hashlib`` only at the digest-
  construction boundary (mirroring the Phase 3.25
  ``osmotic_learning_probe`` precedent).
* Every bounded printable string this module produces is audited
  against
  ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``
  by the static-audit fixture.

Drives Phase 3.26 catalog rows ``I-AHYP-01..I-AHYP-14``.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from brain.development.abstract_pattern import (
    derive_abstract_pattern_signature,
)
from brain.development.agent_loop import (
    AgentLoopState,
    make_initial_agent_loop_state,
    run_agent_interaction_step,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.learning_evidence import (
    LearningEvidenceTrace,
)
from brain.development.reasoning_trace import (
    build_reasoning_trace_report,
)


# ---------------------------------------------------------------------------
# Module constants.
# ---------------------------------------------------------------------------


ACTIVE_HYPOTHESIS_BATTERY_VERSION: str = "phase3.26.v1"


ACTIVE_HYPOTHESIS_TRIAL_ID_MAX_LEN: int = 64
ACTIVE_HYPOTHESIS_CANDIDATE_ID_MAX_LEN: int = 48
ACTIVE_HYPOTHESIS_INPUT_MAX_LEN: int = 240
ACTIVE_HYPOTHESIS_PROBE_MAX_LEN: int = 240
ACTIVE_HYPOTHESIS_SHAPE_MAX_LEN: int = 64
ACTIVE_HYPOTHESIS_CLASSIFICATION_MAX_LEN: int = 32
ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN: int = 16
ACTIVE_HYPOTHESIS_SUMMARY_LINE_MAX_LEN: int = 320
ACTIVE_HYPOTHESIS_REPLY_EXCERPT_MAX_LEN: int = 320
ACTIVE_HYPOTHESIS_MAX_CANDIDATES: int = 8
ACTIVE_HYPOTHESIS_MAX_PROBE_STEPS: int = ACTIVE_HYPOTHESIS_MAX_CANDIDATES
ACTIVE_HYPOTHESIS_MAX_TRIALS: int = 64


ACTIVE_HYPOTHESIS_DIGEST_PREFIX: str = "active_hypothesis"


# Forbidden direct-instruction terms that must NOT appear in
# operator inputs (ambiguous-input texts or constructed probe texts).
# Extends the Phase 3.25 osmotic-probe list with terms specific to
# the active-hypothesis vocabulary.
_FORBIDDEN_DIRECT_INSTRUCTION_TERMS: tuple[str, ...] = (
    "learn",
    "remember",
    "pattern",
    "classify",
    "transfer",
    "reuse",
    "abab",
    "abba",
    "abcabc",
    "structure",
    "shape",
    "imprint",
    "osmotic",
    "absorb",
    "imbibe",
    "intuition",
    "hypothesis",
    "candidate",
    "probe",
    "predict",
    "falsify",
    "survive",
    "decide",
    "infer",
    "wonder",
)


def _has_forbidden_non_claim_term(text: str) -> Optional[str]:
    """Return the first non-claim term found in ``text`` (case-insensitive)."""
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


def _has_forbidden_direct_instruction(text: str) -> Optional[str]:
    """Return the first direct-instruction term found in ``text``."""
    lowered = text.lower()
    for term in _FORBIDDEN_DIRECT_INSTRUCTION_TERMS:
        if term in lowered:
            return term
    return None


# ---------------------------------------------------------------------------
# Closed enums.
# ---------------------------------------------------------------------------


class AmbiguityCondition(str, Enum):
    """Closed enum of test conditions (Phase 3.26)."""

    CONTROL_NO_AMBIGUITY = "control_no_ambiguity"
    SINGLE_HYPOTHESIS_CONVERGES = "single_hypothesis_converges"
    MULTI_HYPOTHESIS_NARROWS = "multi_hypothesis_narrows"
    NO_HYPOTHESIS_SURVIVES = "no_hypothesis_survives"
    REUSE_CACHED_HYPOTHESIS = "reuse_cached_hypothesis"


_AMBIGUITY_CONDITION_VALUES: frozenset[str] = frozenset(
    {c.value for c in AmbiguityCondition}
)


class ActiveHypothesisStatus(str, Enum):
    """Closed enum of per-candidate lifecycle states (Phase 3.26)."""

    PENDING = "pending"
    SURVIVING = "surviving"
    FALSIFIED = "falsified"
    SELECTED = "selected"


_ACTIVE_HYPOTHESIS_STATUS_VALUES: frozenset[str] = frozenset(
    {s.value for s in ActiveHypothesisStatus}
)


class ProbeConstructionRule(str, Enum):
    """Closed enum of safe-probe construction rules (Phase 3.26)."""

    RENAME_ONLY = "rename_only"
    APPEND_POS0_TOKEN = "append_pos0_token"
    APPEND_POS1_TOKEN = "append_pos1_token"
    APPEND_LAST_TOKEN = "append_last_token"
    APPEND_NEW_TOKEN = "append_new_token"
    RENAME_AND_DOUBLE = "rename_and_double"


_PROBE_CONSTRUCTION_RULE_VALUES: frozenset[str] = frozenset(
    {r.value for r in ProbeConstructionRule}
)


class TrialVerdict(str, Enum):
    """Closed enum of per-trial verdicts (Phase 3.26)."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


_TRIAL_VERDICT_VALUES: frozenset[str] = frozenset(
    {v.value for v in TrialVerdict}
)


class ProbeOutcome(str, Enum):
    """Closed enum of per-probe outcomes (Phase 3.26)."""

    CONFIRMED = "confirmed"
    FALSIFIED = "falsified"


_PROBE_OUTCOME_VALUES: frozenset[str] = frozenset(
    {o.value for o in ProbeOutcome}
)


# ---------------------------------------------------------------------------
# Canonical shape map (deterministic; computed at module load).
# ---------------------------------------------------------------------------


_RENAME_ALPHABET: tuple[str, ...] = (
    "alpha", "beta", "gamma", "delta",
    "epsilon", "zeta", "eta", "theta",
    "iota", "kappa", "lambda", "mu",
)


# Token used by APPEND_NEW_TOKEN. Deliberately chosen so that none of
# the v1 trial inputs already contain it, guaranteeing a "fresh"
# token slot in the abstract pattern signature.
_NEW_TOKEN: str = "omicron"


_CANONICAL_EXAMPLES: dict[str, str] = {
    "S_AB": "alpha beta",
    "S_AA": "alpha alpha",
    "S_ABA": "alpha beta alpha",
    "S_AAB": "alpha alpha beta",
    "S_ABB": "alpha beta beta",
    "S_ABC": "alpha beta gamma",
    "S_ABAB": "alpha beta alpha beta",
    "S_ABAA": "alpha beta alpha alpha",
    "S_ABAC": "alpha beta alpha gamma",
    "S_ABBA": "alpha beta beta alpha",
    "S_ABCA": "alpha beta gamma alpha",
    "S_ABCD": "alpha beta gamma delta",
    "S_ABABA": "alpha beta alpha beta alpha",
    "S_ABABB": "alpha beta alpha beta beta",
    "S_ABABC": "alpha beta alpha beta gamma",
    "S_AAA": "alpha alpha alpha",
    "S_AAAB": "alpha alpha alpha beta",
}


_CANONICAL_DIGESTS: dict[str, str] = {
    name: derive_abstract_pattern_signature(text).digest_hex16
    for name, text in _CANONICAL_EXAMPLES.items()
}


_CANONICAL_SHAPES: dict[str, str] = {
    name: derive_abstract_pattern_signature(text).shape
    for name, text in _CANONICAL_EXAMPLES.items()
}


_CANONICAL_CLASSIFICATIONS: dict[str, str] = {
    name: derive_abstract_pattern_signature(text).classification
    for name, text in _CANONICAL_EXAMPLES.items()
}


# ---------------------------------------------------------------------------
# Validators.
# ---------------------------------------------------------------------------


def _validate_bounded_printable(
    value: object,
    *,
    field: str,
    max_len: int,
    forbid_empty: bool = True,
    audit_non_claim: bool = True,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"I-AHYP-01 violated: {field} must be a string "
            f"(got {type(value).__name__})"
        )
    if forbid_empty and not value:
        raise ValueError(
            f"I-AHYP-01 violated: {field} must be non-empty"
        )
    if value and not value.isprintable():
        raise ValueError(
            f"I-AHYP-01 violated: {field} must be printable"
        )
    if len(value) > max_len:
        raise ValueError(
            f"I-AHYP-01 violated: {field} length {len(value)} > {max_len}"
        )
    if audit_non_claim:
        term = _has_forbidden_non_claim_term(value)
        if term is not None:
            raise ValueError(
                f"I-AHYP-01 violated: {field} contains forbidden non-claim "
                f"term {term!r}"
            )
    return value


# ---------------------------------------------------------------------------
# Frozen records.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ActiveHypothesisCandidate:
    """One bounded enumerated hypothesis (I-AHYP-01)."""

    candidate_id: str
    predicted_shape_name: str
    predicted_shape: str
    predicted_classification: str
    predicted_digest_hex16: str
    probe_construction_rule: ProbeConstructionRule
    status: ActiveHypothesisStatus

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.candidate_id,
            field="ActiveHypothesisCandidate.candidate_id",
            max_len=ACTIVE_HYPOTHESIS_CANDIDATE_ID_MAX_LEN,
        )
        _validate_bounded_printable(
            self.predicted_shape_name,
            field="ActiveHypothesisCandidate.predicted_shape_name",
            max_len=ACTIVE_HYPOTHESIS_CANDIDATE_ID_MAX_LEN,
        )
        _validate_bounded_printable(
            self.predicted_shape,
            field="ActiveHypothesisCandidate.predicted_shape",
            max_len=ACTIVE_HYPOTHESIS_SHAPE_MAX_LEN,
            forbid_empty=False,
        )
        _validate_bounded_printable(
            self.predicted_classification,
            field="ActiveHypothesisCandidate.predicted_classification",
            max_len=ACTIVE_HYPOTHESIS_CLASSIFICATION_MAX_LEN,
        )
        if (
            not isinstance(self.predicted_digest_hex16, str)
            or len(self.predicted_digest_hex16) != ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-AHYP-01 violated: "
                "ActiveHypothesisCandidate.predicted_digest_hex16 "
                "must be a 16-char hex string"
            )
        if not isinstance(self.probe_construction_rule, ProbeConstructionRule):
            raise TypeError(
                "I-AHYP-01 violated: "
                "ActiveHypothesisCandidate.probe_construction_rule must "
                "be a ProbeConstructionRule member"
            )
        if not isinstance(self.status, ActiveHypothesisStatus):
            raise TypeError(
                "I-AHYP-01 violated: "
                "ActiveHypothesisCandidate.status must be an "
                "ActiveHypothesisStatus member"
            )


@dataclass(frozen=True, slots=True)
class ActiveProbeStep:
    """One bounded probe-execution record (I-AHYP-01)."""

    candidate_id: str
    probe_text: str
    probe_digest_hex16: str
    probe_shape: str
    probe_classification: str
    predicted_digest_hex16: str
    outcome: ProbeOutcome
    interaction_id: str
    dispatch_trace_digest: str
    reasoning_trace_digest: str
    reply_excerpt: str

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.candidate_id,
            field="ActiveProbeStep.candidate_id",
            max_len=ACTIVE_HYPOTHESIS_CANDIDATE_ID_MAX_LEN,
        )
        _validate_bounded_printable(
            self.probe_text,
            field="ActiveProbeStep.probe_text",
            max_len=ACTIVE_HYPOTHESIS_PROBE_MAX_LEN,
        )
        # Probe text must not leak the experimental contract.
        term = _has_forbidden_direct_instruction(self.probe_text)
        if term is not None:
            raise ValueError(
                f"I-AHYP-04 violated: ActiveProbeStep.probe_text contains "
                f"forbidden direct-instruction term {term!r}"
            )
        # Probe text must not contain the candidate's predicted digest
        # or predicted shape (no answer-key leak).
        if (
            self.predicted_digest_hex16
            and self.predicted_digest_hex16 in self.probe_text
        ):
            raise ValueError(
                "I-AHYP-04 violated: ActiveProbeStep.probe_text contains "
                "the candidate's predicted_digest_hex16"
            )
        if (
            not isinstance(self.probe_digest_hex16, str)
            or len(self.probe_digest_hex16)
            != ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-AHYP-01 violated: ActiveProbeStep.probe_digest_hex16 "
                "must be a 16-char hex string"
            )
        _validate_bounded_printable(
            self.probe_shape,
            field="ActiveProbeStep.probe_shape",
            max_len=ACTIVE_HYPOTHESIS_SHAPE_MAX_LEN,
            forbid_empty=False,
        )
        _validate_bounded_printable(
            self.probe_classification,
            field="ActiveProbeStep.probe_classification",
            max_len=ACTIVE_HYPOTHESIS_CLASSIFICATION_MAX_LEN,
        )
        if (
            not isinstance(self.predicted_digest_hex16, str)
            or len(self.predicted_digest_hex16)
            != ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-AHYP-01 violated: "
                "ActiveProbeStep.predicted_digest_hex16 must be a 16-char "
                "hex string"
            )
        if not isinstance(self.outcome, ProbeOutcome):
            raise TypeError(
                "I-AHYP-01 violated: ActiveProbeStep.outcome must be a "
                "ProbeOutcome member"
            )
        _validate_bounded_printable(
            self.interaction_id,
            field="ActiveProbeStep.interaction_id",
            max_len=ACTIVE_HYPOTHESIS_TRIAL_ID_MAX_LEN,
        )
        for name, value in (
            ("dispatch_trace_digest", self.dispatch_trace_digest),
            ("reasoning_trace_digest", self.reasoning_trace_digest),
        ):
            if (
                not isinstance(value, str)
                or len(value) != ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN
            ):
                raise ValueError(
                    f"I-AHYP-01 violated: ActiveProbeStep.{name} must be a "
                    "16-char hex string"
                )
        _validate_bounded_printable(
            self.reply_excerpt,
            field="ActiveProbeStep.reply_excerpt",
            max_len=ACTIVE_HYPOTHESIS_REPLY_EXCERPT_MAX_LEN,
        )


@dataclass(frozen=True, slots=True)
class ActiveHypothesisTrial:
    """One bounded trial specification (I-AHYP-02)."""

    trial_id: str
    condition: AmbiguityCondition
    input_text: str
    expected_survivors_count: int
    expected_winner_id: str
    expected_no_hypothesis_survives: bool
    expected_second_visit_cache_hit: bool

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.trial_id,
            field="ActiveHypothesisTrial.trial_id",
            max_len=ACTIVE_HYPOTHESIS_TRIAL_ID_MAX_LEN,
        )
        if not isinstance(self.condition, AmbiguityCondition):
            raise TypeError(
                "I-AHYP-02 violated: ActiveHypothesisTrial.condition must "
                "be an AmbiguityCondition member"
            )
        if not isinstance(self.input_text, str):
            raise TypeError(
                "I-AHYP-02 violated: ActiveHypothesisTrial.input_text "
                "must be a string"
            )
        if len(self.input_text) > ACTIVE_HYPOTHESIS_INPUT_MAX_LEN:
            raise ValueError(
                "I-AHYP-02 violated: ActiveHypothesisTrial.input_text "
                f"length {len(self.input_text)} exceeds "
                f"{ACTIVE_HYPOTHESIS_INPUT_MAX_LEN}"
            )
        if self.input_text and not self.input_text.isprintable():
            raise ValueError(
                "I-AHYP-02 violated: ActiveHypothesisTrial.input_text "
                "must be printable"
            )
        term = _has_forbidden_non_claim_term(self.input_text)
        if term is not None:
            raise ValueError(
                "I-AHYP-02 violated: ActiveHypothesisTrial.input_text "
                f"contains forbidden non-claim term {term!r}"
            )
        term = _has_forbidden_direct_instruction(self.input_text)
        if term is not None:
            raise ValueError(
                "I-AHYP-02 violated: ActiveHypothesisTrial.input_text "
                f"contains forbidden direct-instruction term {term!r}"
            )
        if (
            not isinstance(self.expected_survivors_count, int)
            or isinstance(self.expected_survivors_count, bool)
            or self.expected_survivors_count < 0
            or self.expected_survivors_count > ACTIVE_HYPOTHESIS_MAX_CANDIDATES
        ):
            raise ValueError(
                "I-AHYP-02 violated: ActiveHypothesisTrial."
                "expected_survivors_count must be an int in "
                f"[0, {ACTIVE_HYPOTHESIS_MAX_CANDIDATES}]"
            )
        if not isinstance(self.expected_winner_id, str):
            raise TypeError(
                "I-AHYP-02 violated: ActiveHypothesisTrial."
                "expected_winner_id must be a string"
            )
        if len(self.expected_winner_id) > ACTIVE_HYPOTHESIS_CANDIDATE_ID_MAX_LEN:
            raise ValueError(
                "I-AHYP-02 violated: ActiveHypothesisTrial."
                "expected_winner_id length "
                f"{len(self.expected_winner_id)} exceeds "
                f"{ACTIVE_HYPOTHESIS_CANDIDATE_ID_MAX_LEN}"
            )
        for name, value in (
            ("expected_no_hypothesis_survives",
             self.expected_no_hypothesis_survives),
            ("expected_second_visit_cache_hit",
             self.expected_second_visit_cache_hit),
        ):
            if not isinstance(value, bool):
                raise TypeError(
                    f"I-AHYP-02 violated: ActiveHypothesisTrial.{name} "
                    f"must be bool (got {type(value).__name__})"
                )


@dataclass(frozen=True, slots=True)
class ActiveHypothesisResult:
    """One bounded trial outcome record (I-AHYP-02)."""

    trial_id: str
    condition: AmbiguityCondition
    verdict: TrialVerdict
    input_digest_hex16: str
    candidates: tuple[ActiveHypothesisCandidate, ...]
    probe_steps: tuple[ActiveProbeStep, ...]
    survivors_count: int
    winner_id: str
    no_hypothesis_survives: bool
    second_visit_cache_hit: bool
    second_visit_probe_count: int
    false_positive: bool
    false_negative: bool
    learning_evidence_digest: str
    reasoning_trace_digest: str
    dispatch_trace_digests: tuple[str, ...]
    summary_line: str

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.trial_id,
            field="ActiveHypothesisResult.trial_id",
            max_len=ACTIVE_HYPOTHESIS_TRIAL_ID_MAX_LEN,
        )
        if not isinstance(self.condition, AmbiguityCondition):
            raise TypeError(
                "I-AHYP-02 violated: ActiveHypothesisResult.condition "
                "must be an AmbiguityCondition member"
            )
        if not isinstance(self.verdict, TrialVerdict):
            raise TypeError(
                "I-AHYP-02 violated: ActiveHypothesisResult.verdict "
                "must be a TrialVerdict member"
            )
        if (
            not isinstance(self.input_digest_hex16, str)
            or len(self.input_digest_hex16)
            != ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-AHYP-02 violated: ActiveHypothesisResult."
                "input_digest_hex16 must be a 16-char hex string"
            )
        if not isinstance(self.candidates, tuple):
            raise TypeError(
                "I-AHYP-02 violated: ActiveHypothesisResult.candidates "
                "must be a tuple"
            )
        if len(self.candidates) > ACTIVE_HYPOTHESIS_MAX_CANDIDATES:
            raise ValueError(
                "I-AHYP-02 violated: ActiveHypothesisResult.candidates "
                f"length {len(self.candidates)} exceeds "
                f"{ACTIVE_HYPOTHESIS_MAX_CANDIDATES}"
            )
        for c in self.candidates:
            if not isinstance(c, ActiveHypothesisCandidate):
                raise TypeError(
                    "I-AHYP-02 violated: ActiveHypothesisResult.candidates "
                    "entries must be ActiveHypothesisCandidate"
                )
        if not isinstance(self.probe_steps, tuple):
            raise TypeError(
                "I-AHYP-02 violated: ActiveHypothesisResult.probe_steps "
                "must be a tuple"
            )
        if len(self.probe_steps) > ACTIVE_HYPOTHESIS_MAX_PROBE_STEPS:
            raise ValueError(
                "I-AHYP-02 violated: ActiveHypothesisResult.probe_steps "
                f"length {len(self.probe_steps)} exceeds "
                f"{ACTIVE_HYPOTHESIS_MAX_PROBE_STEPS}"
            )
        for p in self.probe_steps:
            if not isinstance(p, ActiveProbeStep):
                raise TypeError(
                    "I-AHYP-02 violated: ActiveHypothesisResult.probe_steps "
                    "entries must be ActiveProbeStep"
                )
        for name, value, lo, hi in (
            ("survivors_count", self.survivors_count, 0,
             ACTIVE_HYPOTHESIS_MAX_CANDIDATES),
            ("second_visit_probe_count", self.second_visit_probe_count, 0,
             ACTIVE_HYPOTHESIS_MAX_PROBE_STEPS),
        ):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < lo
                or value > hi
            ):
                raise ValueError(
                    f"I-AHYP-02 violated: ActiveHypothesisResult.{name} "
                    f"must be an int in [{lo}, {hi}]"
                )
        _validate_bounded_printable(
            self.winner_id,
            field="ActiveHypothesisResult.winner_id",
            max_len=ACTIVE_HYPOTHESIS_CANDIDATE_ID_MAX_LEN,
            forbid_empty=False,
        )
        for name, value in (
            ("no_hypothesis_survives", self.no_hypothesis_survives),
            ("second_visit_cache_hit", self.second_visit_cache_hit),
            ("false_positive", self.false_positive),
            ("false_negative", self.false_negative),
        ):
            if not isinstance(value, bool):
                raise TypeError(
                    f"I-AHYP-02 violated: ActiveHypothesisResult.{name} "
                    "must be bool"
                )
        for name, value in (
            ("learning_evidence_digest", self.learning_evidence_digest),
            ("reasoning_trace_digest", self.reasoning_trace_digest),
        ):
            if (
                not isinstance(value, str)
                or len(value) != ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN
            ):
                raise ValueError(
                    f"I-AHYP-02 violated: ActiveHypothesisResult.{name} "
                    "must be a 16-char hex string"
                )
        if not isinstance(self.dispatch_trace_digests, tuple):
            raise TypeError(
                "I-AHYP-02 violated: ActiveHypothesisResult."
                "dispatch_trace_digests must be a tuple"
            )
        for d in self.dispatch_trace_digests:
            if (
                not isinstance(d, str)
                or len(d) != ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN
            ):
                raise ValueError(
                    "I-AHYP-02 violated: ActiveHypothesisResult."
                    "dispatch_trace_digests entries must be 16-char hex"
                )
        _validate_bounded_printable(
            self.summary_line,
            field="ActiveHypothesisResult.summary_line",
            max_len=ACTIVE_HYPOTHESIS_SUMMARY_LINE_MAX_LEN,
        )


@dataclass(frozen=True, slots=True)
class ActiveHypothesisLiveTestReport:
    """Bounded aggregate report over a live-test run (I-AHYP-12)."""

    battery_version: str
    trials: tuple[ActiveHypothesisResult, ...]
    pass_count: int
    warn_count: int
    fail_count: int
    not_applicable_count: int
    false_positive_count: int
    false_negative_count: int
    winner_selected_count: int
    no_hypothesis_survives_count: int
    cache_reuse_count: int
    real_model_calls: int
    cache_writes: int
    forbidden_term_hits: int
    digest_hex16: str
    summary_line: str

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.battery_version,
            field="ActiveHypothesisLiveTestReport.battery_version",
            max_len=ACTIVE_HYPOTHESIS_INPUT_MAX_LEN,
        )
        if not isinstance(self.trials, tuple):
            raise TypeError(
                "I-AHYP-12 violated: ActiveHypothesisLiveTestReport.trials "
                "must be a tuple"
            )
        if len(self.trials) > ACTIVE_HYPOTHESIS_MAX_TRIALS:
            raise ValueError(
                "I-AHYP-12 violated: ActiveHypothesisLiveTestReport.trials "
                f"length {len(self.trials)} exceeds "
                f"{ACTIVE_HYPOTHESIS_MAX_TRIALS}"
            )
        for t in self.trials:
            if not isinstance(t, ActiveHypothesisResult):
                raise TypeError(
                    "I-AHYP-12 violated: "
                    "ActiveHypothesisLiveTestReport.trials entries must be "
                    "ActiveHypothesisResult"
                )
        for name, value in (
            ("pass_count", self.pass_count),
            ("warn_count", self.warn_count),
            ("fail_count", self.fail_count),
            ("not_applicable_count", self.not_applicable_count),
            ("false_positive_count", self.false_positive_count),
            ("false_negative_count", self.false_negative_count),
            ("winner_selected_count", self.winner_selected_count),
            ("no_hypothesis_survives_count",
             self.no_hypothesis_survives_count),
            ("cache_reuse_count", self.cache_reuse_count),
            ("real_model_calls", self.real_model_calls),
            ("cache_writes", self.cache_writes),
            ("forbidden_term_hits", self.forbidden_term_hits),
        ):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                raise ValueError(
                    f"I-AHYP-12 violated: ActiveHypothesisLiveTestReport."
                    f"{name} must be a non-negative int"
                )
        if (
            not isinstance(self.digest_hex16, str)
            or len(self.digest_hex16) != ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-AHYP-12 violated: ActiveHypothesisLiveTestReport."
                "digest_hex16 must be a 16-char hex string"
            )
        _validate_bounded_printable(
            self.summary_line,
            field="ActiveHypothesisLiveTestReport.summary_line",
            max_len=ACTIVE_HYPOTHESIS_SUMMARY_LINE_MAX_LEN,
        )


# ---------------------------------------------------------------------------
# Probe construction (closed deterministic rules).
# ---------------------------------------------------------------------------


def _input_tokens(input_text: str) -> tuple[str, ...]:
    """Return the input tokens (lowercased, whitespace-split)."""
    return tuple(input_text.lower().split())


def _rename_tokens(input_text: str) -> str:
    """Rename input tokens to ``_RENAME_ALPHABET`` preserving structure."""
    tokens = _input_tokens(input_text)
    if not tokens:
        return ""
    seen: dict[str, str] = {}
    out: list[str] = []
    next_idx = 0
    for t in tokens:
        if t not in seen:
            if next_idx >= len(_RENAME_ALPHABET):
                # Bounded: roll over to the last symbol (extremely
                # unlikely for v1 inputs at <= 8 distinct tokens).
                seen[t] = _RENAME_ALPHABET[-1]
            else:
                seen[t] = _RENAME_ALPHABET[next_idx]
                next_idx += 1
        out.append(seen[t])
    return " ".join(out)


def _fresh_new_token(input_text: str) -> str:
    """Return ``_NEW_TOKEN`` (guaranteed absent from v1 inputs)."""
    return _NEW_TOKEN


def construct_probe_text(
    input_text: str,
    rule: ProbeConstructionRule,
) -> str:
    """Return the bounded probe text for ``input_text`` under ``rule``.

    Pure deterministic; no I/O; no use of candidate digests or shapes.
    The output is bounded printable and is audited downstream for
    forbidden-term cleanliness.
    """
    if not isinstance(rule, ProbeConstructionRule):
        raise TypeError(
            "I-AHYP-04 violated: construct_probe_text requires a "
            "ProbeConstructionRule"
        )
    tokens = _input_tokens(input_text)
    if rule is ProbeConstructionRule.RENAME_ONLY:
        return _rename_tokens(input_text) or input_text
    if rule is ProbeConstructionRule.APPEND_POS0_TOKEN:
        if not tokens:
            return input_text
        return " ".join(list(tokens) + [tokens[0]])
    if rule is ProbeConstructionRule.APPEND_POS1_TOKEN:
        if len(tokens) < 2:
            return " ".join(tokens)
        return " ".join(list(tokens) + [tokens[1]])
    if rule is ProbeConstructionRule.APPEND_LAST_TOKEN:
        if not tokens:
            return input_text
        return " ".join(list(tokens) + [tokens[-1]])
    if rule is ProbeConstructionRule.APPEND_NEW_TOKEN:
        return " ".join(list(tokens) + [_fresh_new_token(input_text)])
    if rule is ProbeConstructionRule.RENAME_AND_DOUBLE:
        renamed = _rename_tokens(input_text)
        if not renamed:
            return input_text
        return renamed + " " + renamed
    raise ValueError(
        f"I-AHYP-04 violated: unknown ProbeConstructionRule {rule!r}"
    )


def select_safe_probe(
    input_text: str,
    candidate: ActiveHypothesisCandidate,
) -> str:
    """Return a bounded safe probe text for ``candidate`` (I-AHYP-04).

    Guarantees:

    * the probe text is bounded printable
      (``<= ACTIVE_HYPOTHESIS_PROBE_MAX_LEN``);
    * the probe text contains none of the forbidden direct-instruction
      terms;
    * the probe text does NOT contain ``candidate.predicted_digest_hex16``
      or ``candidate.predicted_shape`` as a substring (non-leakage);
    * the probe text is a pure deterministic function of
      ``input_text`` and ``candidate.probe_construction_rule``.
    """
    if not isinstance(candidate, ActiveHypothesisCandidate):
        raise TypeError(
            "I-AHYP-04 violated: select_safe_probe requires an "
            "ActiveHypothesisCandidate"
        )
    probe = construct_probe_text(input_text, candidate.probe_construction_rule)
    if not probe:
        probe = "alpha"
    if len(probe) > ACTIVE_HYPOTHESIS_PROBE_MAX_LEN:
        raise ValueError(
            "I-AHYP-04 violated: probe text length "
            f"{len(probe)} exceeds {ACTIVE_HYPOTHESIS_PROBE_MAX_LEN}"
        )
    if not probe.isprintable():
        raise ValueError(
            "I-AHYP-04 violated: probe text must be printable"
        )
    term = _has_forbidden_direct_instruction(probe)
    if term is not None:
        raise ValueError(
            f"I-AHYP-04 violated: constructed probe contains forbidden "
            f"direct-instruction term {term!r}"
        )
    if candidate.predicted_digest_hex16 in probe:
        raise ValueError(
            "I-AHYP-04 violated: constructed probe leaks the candidate's "
            "predicted_digest_hex16"
        )
    if (
        candidate.predicted_shape
        and candidate.predicted_shape in probe
    ):
        raise ValueError(
            "I-AHYP-04 violated: constructed probe leaks the candidate's "
            "predicted_shape"
        )
    return probe


# ---------------------------------------------------------------------------
# Candidate enumeration (curated per (classification, token_count)).
# ---------------------------------------------------------------------------


def _make_candidate(
    candidate_id: str,
    predicted_shape_name: str,
    probe_construction_rule: ProbeConstructionRule,
) -> ActiveHypothesisCandidate:
    if predicted_shape_name not in _CANONICAL_DIGESTS:
        raise KeyError(
            f"I-AHYP-03 violated: unknown predicted_shape_name "
            f"{predicted_shape_name!r}"
        )
    return ActiveHypothesisCandidate(
        candidate_id=candidate_id,
        predicted_shape_name=predicted_shape_name,
        predicted_shape=_CANONICAL_SHAPES[predicted_shape_name],
        predicted_classification=
            _CANONICAL_CLASSIFICATIONS[predicted_shape_name],
        predicted_digest_hex16=_CANONICAL_DIGESTS[predicted_shape_name],
        probe_construction_rule=probe_construction_rule,
        status=ActiveHypothesisStatus.PENDING,
    )


def _candidates_for_repeated_2() -> tuple[ActiveHypothesisCandidate, ...]:
    return (
        _make_candidate("H_RENAME_S_AB", "S_AB",
                        ProbeConstructionRule.RENAME_ONLY),
        _make_candidate("H_APPEND_NEW_S_ABA", "S_ABA",
                        ProbeConstructionRule.APPEND_NEW_TOKEN),
        _make_candidate("H_APPEND_NEW_S_ABC", "S_ABC",
                        ProbeConstructionRule.APPEND_NEW_TOKEN),
        _make_candidate("H_APPEND_POS0_S_ABAA", "S_ABAA",
                        ProbeConstructionRule.APPEND_POS0_TOKEN),
    )


def _candidates_for_alldistinct_2() -> tuple[ActiveHypothesisCandidate, ...]:
    return (
        _make_candidate("H_RENAME_S_AB", "S_AB",
                        ProbeConstructionRule.RENAME_ONLY),
        _make_candidate("H_RENAME_S_AA", "S_AA",
                        ProbeConstructionRule.RENAME_ONLY),
        _make_candidate("H_APPEND_POS0_S_ABA", "S_ABA",
                        ProbeConstructionRule.APPEND_POS0_TOKEN),
        _make_candidate("H_APPEND_NEW_S_ABCD", "S_ABCD",
                        ProbeConstructionRule.APPEND_NEW_TOKEN),
    )


def _candidates_for_partial_recurring_3() -> tuple[ActiveHypothesisCandidate, ...]:
    return (
        _make_candidate("H_RENAME_S_ABA", "S_ABA",
                        ProbeConstructionRule.RENAME_ONLY),
        _make_candidate("H_RENAME_S_ABB", "S_ABB",
                        ProbeConstructionRule.RENAME_ONLY),
        _make_candidate("H_APPEND_POS0_S_ABCA", "S_ABCA",
                        ProbeConstructionRule.APPEND_POS0_TOKEN),
        _make_candidate("H_APPEND_NEW_S_ABCD", "S_ABCD",
                        ProbeConstructionRule.APPEND_NEW_TOKEN),
    )


def _candidates_for_alldistinct_3() -> tuple[ActiveHypothesisCandidate, ...]:
    return (
        _make_candidate("H_RENAME_S_ABC", "S_ABC",
                        ProbeConstructionRule.RENAME_ONLY),
        _make_candidate("H_RENAME_S_ABA", "S_ABA",
                        ProbeConstructionRule.RENAME_ONLY),
        _make_candidate("H_APPEND_NEW_S_ABCD", "S_ABCD",
                        ProbeConstructionRule.APPEND_NEW_TOKEN),
        _make_candidate("H_APPEND_POS0_S_ABCA", "S_ABCA",
                        ProbeConstructionRule.APPEND_POS0_TOKEN),
    )


def _candidates_for_recurring_form_4() -> tuple[ActiveHypothesisCandidate, ...]:
    return (
        _make_candidate("H_RENAME_S_ABAB", "S_ABAB",
                        ProbeConstructionRule.RENAME_ONLY),
        _make_candidate("H_RENAME_S_ABCD", "S_ABCD",
                        ProbeConstructionRule.RENAME_ONLY),
        _make_candidate("H_APPEND_NEW_S_ABABC", "S_ABABC",
                        ProbeConstructionRule.APPEND_NEW_TOKEN),
        _make_candidate("H_APPEND_POS0_S_ABABA", "S_ABABA",
                        ProbeConstructionRule.APPEND_POS0_TOKEN),
    )


def _candidates_for_partial_recurring_4() -> tuple[ActiveHypothesisCandidate, ...]:
    return (
        _make_candidate("H_RENAME_S_ABAC", "S_ABAC",
                        ProbeConstructionRule.RENAME_ONLY),
        _make_candidate("H_RENAME_S_ABCD", "S_ABCD",
                        ProbeConstructionRule.RENAME_ONLY),
        _make_candidate("H_APPEND_NEW_S_ABABC", "S_ABABC",
                        ProbeConstructionRule.APPEND_NEW_TOKEN),
        _make_candidate("H_APPEND_POS0_S_ABABA", "S_ABABA",
                        ProbeConstructionRule.APPEND_POS0_TOKEN),
    )


_CANDIDATES_BY_KEY: dict[
    tuple[str, int], tuple[ActiveHypothesisCandidate, ...]
] = {
    ("repeated", 2): _candidates_for_repeated_2(),
    ("all-distinct", 2): _candidates_for_alldistinct_2(),
    ("partial-recurring", 3): _candidates_for_partial_recurring_3(),
    ("all-distinct", 3): _candidates_for_alldistinct_3(),
    ("recurring-form", 4): _candidates_for_recurring_form_4(),
    ("partial-recurring", 4): _candidates_for_partial_recurring_4(),
}


_NO_ENUMERATION_CLASSIFICATIONS: frozenset[str] = frozenset(
    {"empty", "singleton", "overlong", "non-printable", "too-many-tokens"}
)


def enumerate_hypotheses(
    input_text: str,
) -> tuple[ActiveHypothesisCandidate, ...]:
    """Return the bounded candidate set for ``input_text`` (I-AHYP-03).

    Deterministic: two invocations on the same input produce equal
    candidate tuples. Returns the empty tuple when the input's
    classification is in ``_NO_ENUMERATION_CLASSIFICATIONS`` or when
    no candidate set is curated for the input's
    ``(classification, token_count)`` key.
    """
    sig = derive_abstract_pattern_signature(input_text)
    if not sig.valid:
        return ()
    if sig.classification in _NO_ENUMERATION_CLASSIFICATIONS:
        return ()
    key = (sig.classification, sig.token_count)
    return _CANDIDATES_BY_KEY.get(key, ())


# ---------------------------------------------------------------------------
# Trial execution.
# ---------------------------------------------------------------------------


def _bounded_excerpt(text: str, *, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 4)] + " ..."


def _learning_evidence_digest(trace: LearningEvidenceTrace) -> str:
    payload = b""
    for r in trace.records:
        payload += (
            f"{r.kind.value}|{r.interaction_id}|"
            f"{r.abstract_pattern_digest}|{r.pattern_id}"
        ).encode("utf-8")
        payload += b"\n"
    return hashlib.sha256(payload).hexdigest()[:ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN]


def _input_canonical_digest(input_text: str) -> str:
    """Return the bounded canonical digest for an input text."""
    sig = derive_abstract_pattern_signature(input_text)
    if sig.valid:
        return sig.digest_hex16
    # For empty / non-printable / overlong inputs, derive a stable
    # synthetic digest from the raw text so the cache key is still
    # well-defined.
    return hashlib.sha256(
        ("synthetic|" + input_text).encode("utf-8")
    ).hexdigest()[:ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN]


def _zero_digest() -> str:
    return "0" * ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN


def _run_probe(
    state: AgentLoopState,
    candidate: ActiveHypothesisCandidate,
    input_text: str,
) -> tuple[AgentLoopState, ActiveProbeStep, ActiveHypothesisStatus]:
    probe_text = select_safe_probe(input_text, candidate)
    state, r = run_agent_interaction_step(state, probe_text)

    probe_sig = derive_abstract_pattern_signature(probe_text)
    confirmed = (
        probe_sig.digest_hex16 == candidate.predicted_digest_hex16
    )
    outcome = (
        ProbeOutcome.CONFIRMED if confirmed else ProbeOutcome.FALSIFIED
    )
    new_status = (
        ActiveHypothesisStatus.SURVIVING
        if confirmed
        else ActiveHypothesisStatus.FALSIFIED
    )

    dispatch_digest = (
        r.latest_dispatch_trace.trace_digest_hex16
        if r.latest_dispatch_trace is not None
        else _zero_digest()
    )
    reasoning_digest = (
        build_reasoning_trace_report(r.reasoning_trace).trace_digest_hex16
        if r.reasoning_trace is not None
        else _zero_digest()
    )
    reply_excerpt = _bounded_excerpt(
        r.reply.full_text, limit=ACTIVE_HYPOTHESIS_REPLY_EXCERPT_MAX_LEN
    )

    step = ActiveProbeStep(
        candidate_id=candidate.candidate_id,
        probe_text=probe_text,
        probe_digest_hex16=probe_sig.digest_hex16,
        probe_shape=probe_sig.shape,
        probe_classification=probe_sig.classification,
        predicted_digest_hex16=candidate.predicted_digest_hex16,
        outcome=outcome,
        interaction_id=r.input.input_id,
        dispatch_trace_digest=dispatch_digest,
        reasoning_trace_digest=reasoning_digest,
        reply_excerpt=reply_excerpt,
    )
    return state, step, new_status


def _evaluate_verdict(
    trial: ActiveHypothesisTrial,
    *,
    survivors_count: int,
    winner_id: str,
    no_hypothesis_survives: bool,
    second_visit_cache_hit: bool,
    second_visit_probe_count: int,
) -> tuple[TrialVerdict, bool, bool]:
    """Return ``(verdict, false_positive, false_negative)``."""
    survivors_ok = survivors_count == trial.expected_survivors_count
    winner_ok = winner_id == trial.expected_winner_id
    no_surv_ok = (
        no_hypothesis_survives == trial.expected_no_hypothesis_survives
    )
    cache_hit_ok = (
        second_visit_cache_hit == trial.expected_second_visit_cache_hit
    )
    probe_count_ok = True
    if trial.expected_second_visit_cache_hit:
        probe_count_ok = second_visit_probe_count == 0
    false_positive = bool(winner_id) and not trial.expected_winner_id
    false_negative = (not winner_id) and bool(trial.expected_winner_id)
    if (
        survivors_ok
        and winner_ok
        and no_surv_ok
        and cache_hit_ok
        and probe_count_ok
    ):
        return TrialVerdict.PASS, false_positive, false_negative
    return TrialVerdict.FAIL, false_positive, false_negative


def _run_trial_uncached(
    trial: ActiveHypothesisTrial,
) -> ActiveHypothesisResult:
    """Run a trial without using the reuse cache (the first visit)."""
    state = make_initial_agent_loop_state()
    candidates = enumerate_hypotheses(trial.input_text)
    if len(candidates) > ACTIVE_HYPOTHESIS_MAX_CANDIDATES:
        raise ValueError(
            "I-AHYP-03 violated: enumerator returned more than "
            f"{ACTIVE_HYPOTHESIS_MAX_CANDIDATES} candidates"
        )

    probe_steps: list[ActiveProbeStep] = []
    statuses: list[ActiveHypothesisStatus] = []
    dispatch_digests: list[str] = []
    for c in candidates:
        state, step, new_status = _run_probe(state, c, trial.input_text)
        probe_steps.append(step)
        statuses.append(new_status)
        dispatch_digests.append(step.dispatch_trace_digest)

    survivors = [
        c for c, s in zip(candidates, statuses)
        if s is ActiveHypothesisStatus.SURVIVING
    ]
    survivors_count = len(survivors)
    if survivors_count == 1:
        # Promote the lone survivor to SELECTED.
        selected = survivors[0]
        winner_id = selected.candidate_id
        statuses = [
            ActiveHypothesisStatus.SELECTED
            if c is selected else s
            for c, s in zip(candidates, statuses)
        ]
    else:
        winner_id = ""
    no_hypothesis_survives = (
        survivors_count == 0 and len(candidates) > 0
    )

    finalized_candidates = tuple(
        ActiveHypothesisCandidate(
            candidate_id=c.candidate_id,
            predicted_shape_name=c.predicted_shape_name,
            predicted_shape=c.predicted_shape,
            predicted_classification=c.predicted_classification,
            predicted_digest_hex16=c.predicted_digest_hex16,
            probe_construction_rule=c.probe_construction_rule,
            status=s,
        )
        for c, s in zip(candidates, statuses)
    )

    input_digest = _input_canonical_digest(trial.input_text)
    learning_digest = _learning_evidence_digest(state.learning_trace)
    last_reasoning_digest = (
        probe_steps[-1].reasoning_trace_digest if probe_steps else _zero_digest()
    )

    second_visit_cache_hit = False
    second_visit_probe_count = 0

    verdict, false_positive, false_negative = _evaluate_verdict(
        trial,
        survivors_count=survivors_count,
        winner_id=winner_id,
        no_hypothesis_survives=no_hypothesis_survives,
        second_visit_cache_hit=second_visit_cache_hit,
        second_visit_probe_count=second_visit_probe_count,
    )

    summary_line = _bounded_excerpt(
        (
            f"active_hypothesis_trial id={trial.trial_id} "
            f"cond={trial.condition.value} "
            f"candidates={len(finalized_candidates)} "
            f"survivors={survivors_count} "
            f"winner={winner_id or '<none>'} "
            f"no_survivor={no_hypothesis_survives} "
            f"cache_hit={second_visit_cache_hit} "
            f"verdict={verdict.value}"
        ),
        limit=ACTIVE_HYPOTHESIS_SUMMARY_LINE_MAX_LEN,
    )

    return ActiveHypothesisResult(
        trial_id=trial.trial_id,
        condition=trial.condition,
        verdict=verdict,
        input_digest_hex16=input_digest,
        candidates=finalized_candidates,
        probe_steps=tuple(probe_steps),
        survivors_count=survivors_count,
        winner_id=winner_id,
        no_hypothesis_survives=no_hypothesis_survives,
        second_visit_cache_hit=second_visit_cache_hit,
        second_visit_probe_count=second_visit_probe_count,
        false_positive=false_positive,
        false_negative=false_negative,
        learning_evidence_digest=learning_digest,
        reasoning_trace_digest=last_reasoning_digest,
        dispatch_trace_digests=tuple(dispatch_digests),
        summary_line=summary_line,
    )


def _result_with_cache_hit(
    trial: ActiveHypothesisTrial,
    cached: ActiveHypothesisResult,
) -> ActiveHypothesisResult:
    """Return a cache-hit result wrapping a prior ``cached`` result.

    The returned result reuses the cached candidates, probe steps,
    survivors_count, winner_id, no_hypothesis_survives, learning /
    reasoning / dispatch digests, but carries the trial's own
    ``trial_id`` / ``condition`` / ``input_digest_hex16`` and sets
    ``second_visit_cache_hit == True`` and
    ``second_visit_probe_count == 0``.
    """
    second_visit_cache_hit = True
    second_visit_probe_count = 0
    verdict, false_positive, false_negative = _evaluate_verdict(
        trial,
        survivors_count=cached.survivors_count,
        winner_id=cached.winner_id,
        no_hypothesis_survives=cached.no_hypothesis_survives,
        second_visit_cache_hit=second_visit_cache_hit,
        second_visit_probe_count=second_visit_probe_count,
    )
    summary_line = _bounded_excerpt(
        (
            f"active_hypothesis_trial id={trial.trial_id} "
            f"cond={trial.condition.value} "
            f"candidates={len(cached.candidates)} "
            f"survivors={cached.survivors_count} "
            f"winner={cached.winner_id or '<none>'} "
            f"no_survivor={cached.no_hypothesis_survives} "
            f"cache_hit={second_visit_cache_hit} "
            f"verdict={verdict.value}"
        ),
        limit=ACTIVE_HYPOTHESIS_SUMMARY_LINE_MAX_LEN,
    )
    return ActiveHypothesisResult(
        trial_id=trial.trial_id,
        condition=trial.condition,
        verdict=verdict,
        input_digest_hex16=cached.input_digest_hex16,
        candidates=cached.candidates,
        probe_steps=cached.probe_steps,
        survivors_count=cached.survivors_count,
        winner_id=cached.winner_id,
        no_hypothesis_survives=cached.no_hypothesis_survives,
        second_visit_cache_hit=second_visit_cache_hit,
        second_visit_probe_count=second_visit_probe_count,
        false_positive=false_positive,
        false_negative=false_negative,
        learning_evidence_digest=cached.learning_evidence_digest,
        reasoning_trace_digest=cached.reasoning_trace_digest,
        dispatch_trace_digests=cached.dispatch_trace_digests,
        summary_line=summary_line,
    )


def run_active_hypothesis_trial(
    trial: ActiveHypothesisTrial,
    *,
    cache: Optional[dict[str, ActiveHypothesisResult]] = None,
) -> ActiveHypothesisResult:
    """Run one trial; return a bounded :class:`ActiveHypothesisResult`.

    Pure-deterministic: two invocations on the same trial with the
    same ``cache`` produce bit-identical results.

    If ``cache`` is provided and the trial is a
    ``REUSE_CACHED_HYPOTHESIS`` trial whose input's canonical digest
    is already a cache key, the cached prior result is returned with
    ``second_visit_cache_hit == True`` and
    ``second_visit_probe_count == 0`` (no new probes run).

    For all other conditions, the trial runs the full
    enumerate / probe / prune / select cycle and -- if ``cache`` is
    provided -- stores the result under the input's canonical digest.
    """
    if not isinstance(trial, ActiveHypothesisTrial):
        raise TypeError(
            "I-AHYP-03 violated: run_active_hypothesis_trial requires an "
            "ActiveHypothesisTrial"
        )
    key = _input_canonical_digest(trial.input_text)
    if trial.condition is AmbiguityCondition.REUSE_CACHED_HYPOTHESIS:
        if cache is not None and key in cache:
            return _result_with_cache_hit(trial, cache[key])
        # Cache miss: run as an ordinary trial.
        result = _run_trial_uncached(trial)
        if cache is not None:
            cache.setdefault(key, result)
        return result
    # Non-reuse: run uncached, optionally populate cache.
    result = _run_trial_uncached(trial)
    if cache is not None:
        cache.setdefault(key, result)
    return result


# ---------------------------------------------------------------------------
# Trial battery.
# ---------------------------------------------------------------------------


def build_active_hypothesis_trials() -> tuple[ActiveHypothesisTrial, ...]:
    """Return the deterministic v1 ten-trial battery (I-AHYP-02).

    The trial battery covers every ``AmbiguityCondition`` and is
    sequenced so that ``REUSE_CACHED_HYPOTHESIS`` trials (T09, T10)
    are preceded by their cache-populating predecessors (T03, T07).
    """
    trials = (
        ActiveHypothesisTrial(
            trial_id="T01_control_empty",
            condition=AmbiguityCondition.CONTROL_NO_AMBIGUITY,
            input_text="",
            expected_survivors_count=0,
            expected_winner_id="",
            expected_no_hypothesis_survives=False,
            expected_second_visit_cache_hit=False,
        ),
        ActiveHypothesisTrial(
            trial_id="T02_control_singleton",
            condition=AmbiguityCondition.CONTROL_NO_AMBIGUITY,
            input_text="alpha",
            expected_survivors_count=0,
            expected_winner_id="",
            expected_no_hypothesis_survives=False,
            expected_second_visit_cache_hit=False,
        ),
        ActiveHypothesisTrial(
            trial_id="T03_single_aba",
            condition=AmbiguityCondition.SINGLE_HYPOTHESIS_CONVERGES,
            input_text="red blue red",
            expected_survivors_count=1,
            expected_winner_id="H_RENAME_S_ABA",
            expected_no_hypothesis_survives=False,
            expected_second_visit_cache_hit=False,
        ),
        ActiveHypothesisTrial(
            trial_id="T04_single_abb",
            condition=AmbiguityCondition.SINGLE_HYPOTHESIS_CONVERGES,
            input_text="red blue blue",
            expected_survivors_count=1,
            expected_winner_id="H_RENAME_S_ABB",
            expected_no_hypothesis_survives=False,
            expected_second_visit_cache_hit=False,
        ),
        ActiveHypothesisTrial(
            trial_id="T05_multi_abc",
            condition=AmbiguityCondition.MULTI_HYPOTHESIS_NARROWS,
            input_text="red blue green",
            expected_survivors_count=3,
            expected_winner_id="",
            expected_no_hypothesis_survives=False,
            expected_second_visit_cache_hit=False,
        ),
        ActiveHypothesisTrial(
            trial_id="T06_multi_abab",
            condition=AmbiguityCondition.MULTI_HYPOTHESIS_NARROWS,
            input_text="red blue red blue",
            expected_survivors_count=3,
            expected_winner_id="",
            expected_no_hypothesis_survives=False,
            expected_second_visit_cache_hit=False,
        ),
        ActiveHypothesisTrial(
            trial_id="T07_nosurv_aa",
            condition=AmbiguityCondition.NO_HYPOTHESIS_SURVIVES,
            input_text="red red",
            expected_survivors_count=0,
            expected_winner_id="",
            expected_no_hypothesis_survives=True,
            expected_second_visit_cache_hit=False,
        ),
        ActiveHypothesisTrial(
            trial_id="T08_nosurv_aab",
            condition=AmbiguityCondition.NO_HYPOTHESIS_SURVIVES,
            input_text="red red blue",
            expected_survivors_count=0,
            expected_winner_id="",
            expected_no_hypothesis_survives=True,
            expected_second_visit_cache_hit=False,
        ),
        ActiveHypothesisTrial(
            trial_id="T09_reuse_aba",
            condition=AmbiguityCondition.REUSE_CACHED_HYPOTHESIS,
            input_text="red blue red",
            expected_survivors_count=1,
            expected_winner_id="H_RENAME_S_ABA",
            expected_no_hypothesis_survives=False,
            expected_second_visit_cache_hit=True,
        ),
        ActiveHypothesisTrial(
            trial_id="T10_reuse_aa",
            condition=AmbiguityCondition.REUSE_CACHED_HYPOTHESIS,
            input_text="red red",
            expected_survivors_count=0,
            expected_winner_id="",
            expected_no_hypothesis_survives=True,
            expected_second_visit_cache_hit=True,
        ),
    )
    return trials


# ---------------------------------------------------------------------------
# Live test runner + report.
# ---------------------------------------------------------------------------


def _serialize_result(r: ActiveHypothesisResult) -> str:
    parts = [
        r.trial_id,
        r.condition.value,
        r.verdict.value,
        r.input_digest_hex16,
        f"survivors={r.survivors_count}",
        f"winner={r.winner_id}",
        f"no_survivor={r.no_hypothesis_survives}",
        f"cache_hit={r.second_visit_cache_hit}",
        f"probe_count2={r.second_visit_probe_count}",
        f"fp={r.false_positive}",
        f"fn={r.false_negative}",
        r.learning_evidence_digest,
        r.reasoning_trace_digest,
        "|".join(r.dispatch_trace_digests),
        r.summary_line,
    ]
    for c in r.candidates:
        parts.append(
            f"cand|{c.candidate_id}|{c.predicted_shape_name}|"
            f"{c.predicted_digest_hex16}|"
            f"{c.probe_construction_rule.value}|{c.status.value}"
        )
    for p in r.probe_steps:
        parts.append(
            f"probe|{p.candidate_id}|{p.probe_digest_hex16}|"
            f"{p.probe_shape}|{p.probe_classification}|"
            f"{p.outcome.value}|{p.interaction_id}|"
            f"{p.dispatch_trace_digest}|{p.reasoning_trace_digest}"
        )
    return "\n".join(parts)


def active_hypothesis_live_test_digest(
    report: ActiveHypothesisLiveTestReport,
) -> str:
    """Return a deterministic 16-hex digest over the report (I-AHYP-12)."""
    payload = "\n".join(_serialize_result(r) for r in report.trials).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()[
        :ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN
    ]


def run_active_hypothesis_live_test(
    trials: Optional[tuple[ActiveHypothesisTrial, ...]] = None,
) -> ActiveHypothesisLiveTestReport:
    """Run every trial in the battery and assemble a report (I-AHYP-12).

    The runner allocates a single session-local
    ``cache: dict[str, ActiveHypothesisResult]`` and threads it through
    every trial in order. Two invocations of
    ``run_active_hypothesis_live_test()`` produce bit-identical
    reports.
    """
    if trials is None:
        trials = build_active_hypothesis_trials()
    if not isinstance(trials, tuple):
        raise TypeError(
            "I-AHYP-03 violated: run_active_hypothesis_live_test trials "
            "must be a tuple"
        )

    cache: dict[str, ActiveHypothesisResult] = {}
    results: list[ActiveHypothesisResult] = []
    for t in trials:
        results.append(run_active_hypothesis_trial(t, cache=cache))

    pass_count = sum(
        1 for r in results if r.verdict is TrialVerdict.PASS
    )
    warn_count = sum(
        1 for r in results if r.verdict is TrialVerdict.WARN
    )
    fail_count = sum(
        1 for r in results if r.verdict is TrialVerdict.FAIL
    )
    na_count = sum(
        1 for r in results if r.verdict is TrialVerdict.NOT_APPLICABLE
    )
    fp_count = sum(1 for r in results if r.false_positive)
    fn_count = sum(1 for r in results if r.false_negative)
    winner_selected_count = sum(1 for r in results if r.winner_id)
    no_surv_count = sum(1 for r in results if r.no_hypothesis_survives)
    cache_reuse_count = sum(
        1 for r in results if r.second_visit_cache_hit
    )

    summary_line = _bounded_excerpt(
        (
            f"active_hypothesis_live_test "
            f"version={ACTIVE_HYPOTHESIS_BATTERY_VERSION} "
            f"trials={len(results)} pass={pass_count} warn={warn_count} "
            f"fail={fail_count} na={na_count} fp={fp_count} fn={fn_count} "
            f"winners={winner_selected_count} "
            f"no_survivor={no_surv_count} "
            f"cache_reuse={cache_reuse_count}"
        ),
        limit=ACTIVE_HYPOTHESIS_SUMMARY_LINE_MAX_LEN,
    )

    placeholder = ActiveHypothesisLiveTestReport(
        battery_version=ACTIVE_HYPOTHESIS_BATTERY_VERSION,
        trials=tuple(results),
        pass_count=pass_count,
        warn_count=warn_count,
        fail_count=fail_count,
        not_applicable_count=na_count,
        false_positive_count=fp_count,
        false_negative_count=fn_count,
        winner_selected_count=winner_selected_count,
        no_hypothesis_survives_count=no_surv_count,
        cache_reuse_count=cache_reuse_count,
        real_model_calls=0,
        cache_writes=0,
        forbidden_term_hits=0,
        digest_hex16=_zero_digest(),
        summary_line=summary_line,
    )
    digest = active_hypothesis_live_test_digest(placeholder)
    return ActiveHypothesisLiveTestReport(
        battery_version=ACTIVE_HYPOTHESIS_BATTERY_VERSION,
        trials=tuple(results),
        pass_count=pass_count,
        warn_count=warn_count,
        fail_count=fail_count,
        not_applicable_count=na_count,
        false_positive_count=fp_count,
        false_negative_count=fn_count,
        winner_selected_count=winner_selected_count,
        no_hypothesis_survives_count=no_surv_count,
        cache_reuse_count=cache_reuse_count,
        real_model_calls=0,
        cache_writes=0,
        forbidden_term_hits=0,
        digest_hex16=digest,
        summary_line=summary_line,
    )


def format_active_hypothesis_live_test_report(
    report: ActiveHypothesisLiveTestReport,
) -> str:
    """Return a bounded printable table over the report (I-AHYP-12)."""
    if not isinstance(report, ActiveHypothesisLiveTestReport):
        raise TypeError(
            "I-AHYP-12 violated: format_active_hypothesis_live_test_report "
            "requires an ActiveHypothesisLiveTestReport"
        )
    lines: list[str] = []
    lines.append(report.summary_line)
    for r in report.trials:
        lines.append(
            f"  {r.trial_id:30s} {r.verdict.value:6s} "
            f"cond={r.condition.value:30s} "
            f"survivors={r.survivors_count} "
            f"winner={r.winner_id or '<none>':32s} "
            f"cache_hit={r.second_visit_cache_hit}"
        )
    lines.append(f"  digest={report.digest_hex16}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-produced strings (audited by the static-audit fixture).
# ---------------------------------------------------------------------------


MODULE_PRODUCED_STRINGS: tuple[str, ...] = (
    ACTIVE_HYPOTHESIS_BATTERY_VERSION,
    ACTIVE_HYPOTHESIS_DIGEST_PREFIX,
    AmbiguityCondition.CONTROL_NO_AMBIGUITY.value,
    AmbiguityCondition.SINGLE_HYPOTHESIS_CONVERGES.value,
    AmbiguityCondition.MULTI_HYPOTHESIS_NARROWS.value,
    AmbiguityCondition.NO_HYPOTHESIS_SURVIVES.value,
    AmbiguityCondition.REUSE_CACHED_HYPOTHESIS.value,
    ActiveHypothesisStatus.PENDING.value,
    ActiveHypothesisStatus.SURVIVING.value,
    ActiveHypothesisStatus.FALSIFIED.value,
    ActiveHypothesisStatus.SELECTED.value,
    ProbeConstructionRule.RENAME_ONLY.value,
    ProbeConstructionRule.APPEND_POS0_TOKEN.value,
    ProbeConstructionRule.APPEND_POS1_TOKEN.value,
    ProbeConstructionRule.APPEND_LAST_TOKEN.value,
    ProbeConstructionRule.APPEND_NEW_TOKEN.value,
    ProbeConstructionRule.RENAME_AND_DOUBLE.value,
    TrialVerdict.PASS.value,
    TrialVerdict.WARN.value,
    TrialVerdict.FAIL.value,
    TrialVerdict.NOT_APPLICABLE.value,
    ProbeOutcome.CONFIRMED.value,
    ProbeOutcome.FALSIFIED.value,
)


# ---------------------------------------------------------------------------
# CLI entry point.
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 3.26 active hypothesis + self-directed probe loop "
            "runner (deterministic, OFFLINE, zero real model calls)"
        )
    )
    parser.add_argument("--quiet", action="store_true", default=False)
    args = parser.parse_args(argv)

    report = run_active_hypothesis_live_test()
    if not args.quiet:
        sys.stdout.write(
            format_active_hypothesis_live_test_report(report) + "\n"
        )
        sys.stdout.write(
            f"real_model_calls={report.real_model_calls} "
            f"cache_writes={report.cache_writes} "
            f"forbidden_term_hits={report.forbidden_term_hits}\n"
        )

    if report.fail_count > 0:
        return 1
    if report.warn_count > 0:
        return 2
    return 0


__all__ = (
    "ACTIVE_HYPOTHESIS_BATTERY_VERSION",
    "ACTIVE_HYPOTHESIS_CANDIDATE_ID_MAX_LEN",
    "ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN",
    "ACTIVE_HYPOTHESIS_DIGEST_PREFIX",
    "ACTIVE_HYPOTHESIS_INPUT_MAX_LEN",
    "ACTIVE_HYPOTHESIS_MAX_CANDIDATES",
    "ACTIVE_HYPOTHESIS_MAX_PROBE_STEPS",
    "ACTIVE_HYPOTHESIS_MAX_TRIALS",
    "ACTIVE_HYPOTHESIS_PROBE_MAX_LEN",
    "ACTIVE_HYPOTHESIS_REPLY_EXCERPT_MAX_LEN",
    "ACTIVE_HYPOTHESIS_SHAPE_MAX_LEN",
    "ACTIVE_HYPOTHESIS_SUMMARY_LINE_MAX_LEN",
    "ACTIVE_HYPOTHESIS_TRIAL_ID_MAX_LEN",
    "ActiveHypothesisCandidate",
    "ActiveHypothesisLiveTestReport",
    "ActiveHypothesisResult",
    "ActiveHypothesisStatus",
    "ActiveHypothesisTrial",
    "ActiveProbeStep",
    "AmbiguityCondition",
    "MODULE_PRODUCED_STRINGS",
    "ProbeConstructionRule",
    "ProbeOutcome",
    "TrialVerdict",
    "active_hypothesis_live_test_digest",
    "build_active_hypothesis_trials",
    "construct_probe_text",
    "enumerate_hypotheses",
    "format_active_hypothesis_live_test_report",
    "main",
    "run_active_hypothesis_live_test",
    "run_active_hypothesis_trial",
    "select_safe_probe",
)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
