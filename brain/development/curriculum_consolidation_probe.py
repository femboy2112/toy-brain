"""Phase 3.30 Curriculum Consolidation Live Test runner.

Deterministic OFFLINE live-test runner that probes whether the
existing substrate (abstract_pattern signature + learning evidence
+ reasoning trace + dispatch trace + worldlet feedback + the Phase
3.25 osmotic imprinting+activation surface + the Phase 3.26 active-
hypothesis enumeration+falsification+caching surface) realizes the
operational analogue of *curriculum consolidation*: given a bounded
ordered tuple of structural exposures and a bounded session-local
slate capacity, the runtime

* admits each exposure into the slate under a closed admission
  rule (classification gate + digest-collision gate);
* rejects duplicates without overwriting the first record;
* evicts the least-recently-accessed record once the slate
  capacity is exceeded (LRU decay);
* on a later probe whose digest matches a surviving record,
  returns the prior admitted record without re-admitting;
* declines to fabricate reuse for probes whose digest is novel;
* emits an audit trail tagging every exposure as ``SURVIVED``,
  ``DECAYED``, or ``REJECTED``.

"Curriculum consolidation in ToyI is a bounded operational
accumulation + LRU-decay + caching effect over structural records,
not a psychological or phenomenological claim."

"Accumulation" means bounded ordered admission into a fixed-size
session-local slate. "Consolidation" means closed-rule admission.
"Decay" means closed-rule eviction. "Reuse" means returning a
cached prior admitted record on a later probe whose digest
matches. "Audit trail" means a tuple of
``CurriculumStructureRecord`` entries each tagged with a closed
``AuditDisposition`` value. None of these terms claim cognitive
learning, memory, forgetting, re-learning, deliberation, or any
psychological process. The runtime is a bounded structural state
machine.

The module is deliberately closed:

* No I/O, no network, no shell, no LLM, no ``brain.tick`` import,
  no ``brain.ui.session`` import, no curses, no threading / asyncio
  / atexit / signal / importlib / time / random.
* The deterministic runner uses ``hashlib`` only at the digest-
  construction boundary (mirroring the Phase 3.25
  ``osmotic_learning_probe`` and the Phase 3.26
  ``active_hypothesis_probe`` precedents).
* Every bounded printable string this module produces is audited
  against
  ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``
  by the static-audit fixture.

Drives Phase 3.30 catalog rows ``I-CURR-01..I-CURR-14``.
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


CURRICULUM_BATTERY_VERSION: str = "phase3.30.v1"


CURRICULUM_TRIAL_ID_MAX_LEN: int = 64
CURRICULUM_EXPOSURE_ID_MAX_LEN: int = 48
CURRICULUM_STRUCTURE_ID_MAX_LEN: int = 48
CURRICULUM_INPUT_MAX_LEN: int = 240
CURRICULUM_PROBE_MAX_LEN: int = 240
CURRICULUM_DIGEST_HEX_LEN: int = 16
CURRICULUM_SUMMARY_LINE_MAX_LEN: int = 320
CURRICULUM_REPLY_EXCERPT_MAX_LEN: int = 320
CURRICULUM_MAX_EXPOSURES_PER_TRIAL: int = 8
CURRICULUM_MAX_TRIALS: int = 64
CURRICULUM_SLATE_MAX_ENTRIES: int = 4


CURRICULUM_DIGEST_PREFIX: str = "curriculum_consolidation"


# Forbidden direct-instruction terms that must NOT appear in
# operator inputs (exposure texts or probe texts). Extends the
# Phase 3.26 active-hypothesis list with terms specific to the
# curriculum-consolidation vocabulary.
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
    "imprint",
    "osmotic",
    "absorb",
    "imbibe",
    "intuition",
    "hypothesis",
    "candidate",
    "predict",
    "falsify",
    "decide",
    "infer",
    "wonder",
    "curriculum",
    "accumulate",
    "consolidate",
    "audit",
    "interfere",
    "forget",
)


# Classifications whose admission outcome is REJECTED_NONPRINTABLE.
# These are the closed set of structural classifications that
# indicate the input cannot be meaningfully admitted as a slate
# entry. The set is a pure function of
# ``derive_abstract_pattern_signature(text).classification`` and the
# ``valid`` flag.
_REJECTED_CLASSIFICATIONS: frozenset[str] = frozenset({
    "empty",
    "singleton",
    "overlong",
    "non-printable",
    "too-many-tokens",
})


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


class CurriculumCondition(str, Enum):
    """Closed enum of test conditions (Phase 3.30)."""

    SINGLE_STRUCTURE = "single_structure"
    SEQUENTIAL_NONINTERFERING = "sequential_noninterfering"
    SEQUENTIAL_INTERFERING = "sequential_interfering"
    DECAY_ON_DISUSE = "decay_on_disuse"
    REUSE_AFTER_NEWER = "reuse_after_newer"


_CURRICULUM_CONDITION_VALUES: frozenset[str] = frozenset(
    {c.value for c in CurriculumCondition}
)


class AuditDisposition(str, Enum):
    """Closed enum of audit-trail dispositions (Phase 3.30)."""

    SURVIVED = "survived"
    DECAYED = "decayed"
    REJECTED = "rejected"


_AUDIT_DISPOSITION_VALUES: frozenset[str] = frozenset(
    {d.value for d in AuditDisposition}
)


class AdmissionOutcome(str, Enum):
    """Closed enum of per-exposure admission outcomes (Phase 3.30)."""

    ADMITTED = "admitted"
    REJECTED_COLLISION = "rejected_collision"
    REJECTED_NONPRINTABLE = "rejected_nonprintable"


_ADMISSION_OUTCOME_VALUES: frozenset[str] = frozenset(
    {o.value for o in AdmissionOutcome}
)


class TrialVerdict(str, Enum):
    """Closed enum of per-trial verdicts (Phase 3.30)."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


_TRIAL_VERDICT_VALUES: frozenset[str] = frozenset(
    {v.value for v in TrialVerdict}
)


# ---------------------------------------------------------------------------
# Canonical exposure pool (deterministic; computed at module load).
# ---------------------------------------------------------------------------


# Each entry maps a stable id to a bounded two- or three- or four-
# token printable input whose ``derive_abstract_pattern_signature``
# yields a distinct shape. Token alphabet is the Greek-letter pool
# used elsewhere; none of these tokens contain a forbidden direct-
# instruction term or a forbidden non-claim term.
_CANONICAL_EXPOSURES: dict[str, str] = {
    "E_AB":   "alpha beta",
    "E_AA":   "gamma gamma",
    "E_ABC":  "delta epsilon zeta",
    "E_AAB":  "eta eta theta",
    "E_ABA":  "iota kappa iota",
    "E_ABB":  "mu nu nu",
    "E_ABCD": "rho sigma tau upsilon",
    "E_ABAB": "phi chi phi chi",
}


_CANONICAL_DIGESTS: dict[str, str] = {
    name: derive_abstract_pattern_signature(text).digest_hex16
    for name, text in _CANONICAL_EXPOSURES.items()
}


_CANONICAL_SHAPES: dict[str, str] = {
    name: derive_abstract_pattern_signature(text).shape
    for name, text in _CANONICAL_EXPOSURES.items()
}


# Sanity: every canonical exposure must be distinct in digest.
# Detected at module load so drift surfaces immediately.
if len(set(_CANONICAL_DIGESTS.values())) != len(_CANONICAL_DIGESTS):
    raise ValueError(
        "I-CURR-03 violated: canonical exposure pool has digest "
        "collisions; the pool must contain only distinct-shape "
        "entries"
    )


# Non-printable / singleton inputs used by SINGLE_STRUCTURE
# rejection trials.
_REJECT_INPUTS: dict[str, str] = {
    "E_SINGLETON": "psi",       # classification == "singleton"
    "E_EMPTY": "",              # valid == False, classification == "empty"
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
            f"I-CURR-01 violated: {field} must be a string "
            f"(got {type(value).__name__})"
        )
    if forbid_empty and not value:
        raise ValueError(
            f"I-CURR-01 violated: {field} must be non-empty"
        )
    if value and not value.isprintable():
        raise ValueError(
            f"I-CURR-01 violated: {field} must be printable"
        )
    if len(value) > max_len:
        raise ValueError(
            f"I-CURR-01 violated: {field} length {len(value)} > {max_len}"
        )
    if audit_non_claim:
        term = _has_forbidden_non_claim_term(value)
        if term is not None:
            raise ValueError(
                f"I-CURR-01 violated: {field} contains forbidden non-claim "
                f"term {term!r}"
            )
    return value


def _validate_digest_hex(value: object, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != CURRICULUM_DIGEST_HEX_LEN
    ):
        raise ValueError(
            f"I-CURR-01 violated: {field} must be a 16-char hex string "
            f"(got {value!r})"
        )
    return value


# ---------------------------------------------------------------------------
# Frozen records.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CurriculumExposure:
    """One bounded curriculum exposure (I-CURR-01)."""

    exposure_id: str
    input_text: str

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.exposure_id,
            field="CurriculumExposure.exposure_id",
            max_len=CURRICULUM_EXPOSURE_ID_MAX_LEN,
        )
        # input_text may be empty (E_EMPTY case) and may be non-
        # printable in pathological cases handled by the runner.
        _validate_bounded_printable(
            self.input_text,
            field="CurriculumExposure.input_text",
            max_len=CURRICULUM_INPUT_MAX_LEN,
            forbid_empty=False,
            audit_non_claim=True,
        )
        # Forbidden direct-instruction guard (no operator-input
        # leak of the experimental contract).
        if self.input_text:
            term = _has_forbidden_direct_instruction(self.input_text)
            if term is not None:
                raise ValueError(
                    f"I-CURR-02 violated: CurriculumExposure.input_text "
                    f"contains forbidden direct-instruction term {term!r}"
                )


@dataclass(frozen=True, slots=True)
class CurriculumStructureRecord:
    """One bounded audit-trail record (I-CURR-01)."""

    structure_id: str
    source_digest_hex16: str
    admitted_at_step: int
    last_access_step: int
    disposition: AuditDisposition

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.structure_id,
            field="CurriculumStructureRecord.structure_id",
            max_len=CURRICULUM_STRUCTURE_ID_MAX_LEN,
        )
        _validate_digest_hex(
            self.source_digest_hex16,
            field="CurriculumStructureRecord.source_digest_hex16",
        )
        if not isinstance(self.admitted_at_step, int):
            raise TypeError(
                "I-CURR-01 violated: "
                "CurriculumStructureRecord.admitted_at_step must be int"
            )
        if self.admitted_at_step < 0:
            raise ValueError(
                "I-CURR-01 violated: "
                "CurriculumStructureRecord.admitted_at_step must be >= 0"
            )
        if not isinstance(self.last_access_step, int):
            raise TypeError(
                "I-CURR-01 violated: "
                "CurriculumStructureRecord.last_access_step must be int"
            )
        if self.last_access_step < self.admitted_at_step:
            raise ValueError(
                "I-CURR-01 violated: last_access_step must be >= "
                "admitted_at_step"
            )
        if not isinstance(self.disposition, AuditDisposition):
            raise TypeError(
                "I-CURR-01 violated: "
                "CurriculumStructureRecord.disposition must be an "
                "AuditDisposition member"
            )


@dataclass(frozen=True, slots=True)
class CurriculumProbeStep:
    """One bounded probe-execution record (I-CURR-01)."""

    probe_input: str
    probe_digest_hex16: str
    reuse_observed: bool
    probe_reused_structure_id: str
    interaction_id: str
    dispatch_trace_digest: str
    reasoning_trace_digest: str
    reply_excerpt: str
    summary_line: str

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.probe_input,
            field="CurriculumProbeStep.probe_input",
            max_len=CURRICULUM_PROBE_MAX_LEN,
            forbid_empty=False,
            audit_non_claim=True,
        )
        if self.probe_input:
            term = _has_forbidden_direct_instruction(self.probe_input)
            if term is not None:
                raise ValueError(
                    f"I-CURR-02 violated: CurriculumProbeStep.probe_input "
                    f"contains forbidden direct-instruction term {term!r}"
                )
        _validate_digest_hex(
            self.probe_digest_hex16,
            field="CurriculumProbeStep.probe_digest_hex16",
        )
        if not isinstance(self.reuse_observed, bool):
            raise TypeError(
                "I-CURR-01 violated: "
                "CurriculumProbeStep.reuse_observed must be bool"
            )
        # probe_reused_structure_id may be empty (no match).
        _validate_bounded_printable(
            self.probe_reused_structure_id,
            field="CurriculumProbeStep.probe_reused_structure_id",
            max_len=CURRICULUM_STRUCTURE_ID_MAX_LEN,
            forbid_empty=False,
        )
        _validate_bounded_printable(
            self.interaction_id,
            field="CurriculumProbeStep.interaction_id",
            max_len=CURRICULUM_STRUCTURE_ID_MAX_LEN,
            forbid_empty=False,
        )
        _validate_digest_hex(
            self.dispatch_trace_digest,
            field="CurriculumProbeStep.dispatch_trace_digest",
        )
        _validate_digest_hex(
            self.reasoning_trace_digest,
            field="CurriculumProbeStep.reasoning_trace_digest",
        )
        _validate_bounded_printable(
            self.reply_excerpt,
            field="CurriculumProbeStep.reply_excerpt",
            max_len=CURRICULUM_REPLY_EXCERPT_MAX_LEN,
            forbid_empty=False,
        )
        _validate_bounded_printable(
            self.summary_line,
            field="CurriculumProbeStep.summary_line",
            max_len=CURRICULUM_SUMMARY_LINE_MAX_LEN,
            forbid_empty=False,
        )


@dataclass(frozen=True, slots=True)
class CurriculumTrial:
    """One bounded trial specification (I-CURR-02)."""

    trial_id: str
    condition: CurriculumCondition
    exposures: tuple[CurriculumExposure, ...]
    probe_input: str
    slate_max_entries: int
    expected_survived_count: int
    expected_decayed_count: int
    expected_rejected_count: int
    expected_reuse_observed: bool

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.trial_id,
            field="CurriculumTrial.trial_id",
            max_len=CURRICULUM_TRIAL_ID_MAX_LEN,
        )
        if not isinstance(self.condition, CurriculumCondition):
            raise TypeError(
                "I-CURR-02 violated: "
                "CurriculumTrial.condition must be a CurriculumCondition "
                "member"
            )
        if not isinstance(self.exposures, tuple):
            raise TypeError(
                "I-CURR-02 violated: "
                "CurriculumTrial.exposures must be a tuple"
            )
        if len(self.exposures) > CURRICULUM_MAX_EXPOSURES_PER_TRIAL:
            raise ValueError(
                "I-CURR-02 violated: "
                f"CurriculumTrial.exposures length {len(self.exposures)} "
                f"> {CURRICULUM_MAX_EXPOSURES_PER_TRIAL}"
            )
        for e in self.exposures:
            if not isinstance(e, CurriculumExposure):
                raise TypeError(
                    "I-CURR-02 violated: every exposures entry must be a "
                    "CurriculumExposure"
                )
        # probe_input may be empty (no probe).
        _validate_bounded_printable(
            self.probe_input,
            field="CurriculumTrial.probe_input",
            max_len=CURRICULUM_PROBE_MAX_LEN,
            forbid_empty=False,
            audit_non_claim=True,
        )
        if self.probe_input:
            term = _has_forbidden_direct_instruction(self.probe_input)
            if term is not None:
                raise ValueError(
                    f"I-CURR-02 violated: CurriculumTrial.probe_input "
                    f"contains forbidden direct-instruction term {term!r}"
                )
        if not isinstance(self.slate_max_entries, int):
            raise TypeError(
                "I-CURR-02 violated: "
                "CurriculumTrial.slate_max_entries must be int"
            )
        if (
            self.slate_max_entries < 1
            or self.slate_max_entries > CURRICULUM_SLATE_MAX_ENTRIES
        ):
            raise ValueError(
                "I-CURR-02 violated: "
                f"CurriculumTrial.slate_max_entries must be in "
                f"[1, {CURRICULUM_SLATE_MAX_ENTRIES}]"
            )
        for name, val in (
            ("expected_survived_count", self.expected_survived_count),
            ("expected_decayed_count", self.expected_decayed_count),
            ("expected_rejected_count", self.expected_rejected_count),
        ):
            if not isinstance(val, int):
                raise TypeError(
                    f"I-CURR-02 violated: CurriculumTrial.{name} must be int"
                )
            if val < 0:
                raise ValueError(
                    f"I-CURR-02 violated: CurriculumTrial.{name} must be "
                    f">= 0"
                )
        if not isinstance(self.expected_reuse_observed, bool):
            raise TypeError(
                "I-CURR-02 violated: "
                "CurriculumTrial.expected_reuse_observed must be bool"
            )


@dataclass(frozen=True, slots=True)
class CurriculumTrialResult:
    """One bounded trial result (I-CURR-02)."""

    trial_id: str
    condition: CurriculumCondition
    verdict: TrialVerdict
    audit_records: tuple[CurriculumStructureRecord, ...]
    probe_step: Optional[CurriculumProbeStep]
    survived_count: int
    decayed_count: int
    rejected_count: int
    reuse_observed: bool
    false_positive: bool
    false_negative: bool
    learning_evidence_digest: str
    reasoning_trace_digest: str
    dispatch_trace_digests: tuple[str, ...]
    summary_line: str

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.trial_id,
            field="CurriculumTrialResult.trial_id",
            max_len=CURRICULUM_TRIAL_ID_MAX_LEN,
        )
        if not isinstance(self.condition, CurriculumCondition):
            raise TypeError(
                "I-CURR-02 violated: "
                "CurriculumTrialResult.condition must be a "
                "CurriculumCondition member"
            )
        if not isinstance(self.verdict, TrialVerdict):
            raise TypeError(
                "I-CURR-02 violated: "
                "CurriculumTrialResult.verdict must be a TrialVerdict "
                "member"
            )
        if not isinstance(self.audit_records, tuple):
            raise TypeError(
                "I-CURR-02 violated: "
                "CurriculumTrialResult.audit_records must be a tuple"
            )
        if len(self.audit_records) > CURRICULUM_MAX_EXPOSURES_PER_TRIAL:
            raise ValueError(
                "I-CURR-02 violated: "
                f"CurriculumTrialResult.audit_records length "
                f"{len(self.audit_records)} > "
                f"{CURRICULUM_MAX_EXPOSURES_PER_TRIAL}"
            )
        for r in self.audit_records:
            if not isinstance(r, CurriculumStructureRecord):
                raise TypeError(
                    "I-CURR-02 violated: every audit_records entry must "
                    "be a CurriculumStructureRecord"
                )
        if self.probe_step is not None and not isinstance(
            self.probe_step, CurriculumProbeStep
        ):
            raise TypeError(
                "I-CURR-02 violated: "
                "CurriculumTrialResult.probe_step must be None or a "
                "CurriculumProbeStep"
            )
        for name, val in (
            ("survived_count", self.survived_count),
            ("decayed_count", self.decayed_count),
            ("rejected_count", self.rejected_count),
        ):
            if not isinstance(val, int) or val < 0:
                raise ValueError(
                    f"I-CURR-02 violated: CurriculumTrialResult.{name} "
                    f"must be a non-negative int"
                )
        if not isinstance(self.reuse_observed, bool):
            raise TypeError(
                "I-CURR-02 violated: "
                "CurriculumTrialResult.reuse_observed must be bool"
            )
        if not isinstance(self.false_positive, bool):
            raise TypeError(
                "I-CURR-02 violated: false_positive must be bool"
            )
        if not isinstance(self.false_negative, bool):
            raise TypeError(
                "I-CURR-02 violated: false_negative must be bool"
            )
        _validate_digest_hex(
            self.learning_evidence_digest,
            field="CurriculumTrialResult.learning_evidence_digest",
        )
        _validate_digest_hex(
            self.reasoning_trace_digest,
            field="CurriculumTrialResult.reasoning_trace_digest",
        )
        if not isinstance(self.dispatch_trace_digests, tuple):
            raise TypeError(
                "I-CURR-02 violated: dispatch_trace_digests must be a tuple"
            )
        for d in self.dispatch_trace_digests:
            _validate_digest_hex(
                d, field="CurriculumTrialResult.dispatch_trace_digests[*]"
            )
        _validate_bounded_printable(
            self.summary_line,
            field="CurriculumTrialResult.summary_line",
            max_len=CURRICULUM_SUMMARY_LINE_MAX_LEN,
        )


@dataclass(frozen=True, slots=True)
class CurriculumConsolidationReport:
    """One bounded live-test report (I-CURR-02)."""

    battery_version: str
    trials: tuple[CurriculumTrialResult, ...]
    pass_count: int
    warn_count: int
    fail_count: int
    not_applicable_count: int
    false_positive_count: int
    false_negative_count: int
    total_survived_count: int
    total_decayed_count: int
    total_rejected_count: int
    reuse_observed_count: int
    real_model_calls: int
    cache_writes: int
    forbidden_term_hits: int
    digest_hex16: str
    summary_line: str

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.battery_version,
            field="CurriculumConsolidationReport.battery_version",
            max_len=CURRICULUM_TRIAL_ID_MAX_LEN,
        )
        if not isinstance(self.trials, tuple):
            raise TypeError(
                "I-CURR-02 violated: "
                "CurriculumConsolidationReport.trials must be a tuple"
            )
        if len(self.trials) > CURRICULUM_MAX_TRIALS:
            raise ValueError(
                "I-CURR-02 violated: "
                f"CurriculumConsolidationReport.trials length "
                f"{len(self.trials)} > {CURRICULUM_MAX_TRIALS}"
            )
        for r in self.trials:
            if not isinstance(r, CurriculumTrialResult):
                raise TypeError(
                    "I-CURR-02 violated: every trials entry must be a "
                    "CurriculumTrialResult"
                )
        for name, val in (
            ("pass_count", self.pass_count),
            ("warn_count", self.warn_count),
            ("fail_count", self.fail_count),
            ("not_applicable_count", self.not_applicable_count),
            ("false_positive_count", self.false_positive_count),
            ("false_negative_count", self.false_negative_count),
            ("total_survived_count", self.total_survived_count),
            ("total_decayed_count", self.total_decayed_count),
            ("total_rejected_count", self.total_rejected_count),
            ("reuse_observed_count", self.reuse_observed_count),
            ("real_model_calls", self.real_model_calls),
            ("cache_writes", self.cache_writes),
            ("forbidden_term_hits", self.forbidden_term_hits),
        ):
            if not isinstance(val, int) or val < 0:
                raise ValueError(
                    f"I-CURR-02 violated: "
                    f"CurriculumConsolidationReport.{name} must be "
                    f"a non-negative int"
                )
        _validate_digest_hex(
            self.digest_hex16,
            field="CurriculumConsolidationReport.digest_hex16",
        )
        _validate_bounded_printable(
            self.summary_line,
            field="CurriculumConsolidationReport.summary_line",
            max_len=CURRICULUM_SUMMARY_LINE_MAX_LEN,
        )


# ---------------------------------------------------------------------------
# Helper: bounded text excerpt + digest helpers.
# ---------------------------------------------------------------------------


def _bounded_excerpt(text: str, *, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 4)] + " ..."


def _zero_digest() -> str:
    return "0" * CURRICULUM_DIGEST_HEX_LEN


def _learning_evidence_digest(trace: LearningEvidenceTrace) -> str:
    payload = b""
    for r in trace.records:
        payload += (
            f"{r.kind.value}|{r.interaction_id}|"
            f"{r.abstract_pattern_digest}|{r.pattern_id}"
        ).encode("utf-8")
        payload += b"\n"
    return hashlib.sha256(payload).hexdigest()[
        :CURRICULUM_DIGEST_HEX_LEN
    ]


def _classify_admission(
    input_text: str,
) -> tuple[AdmissionOutcome, str]:
    """Return ``(outcome, source_digest_hex16)`` for an exposure.

    Pure deterministic; consults only ``derive_abstract_pattern_signature``.
    """
    sig = derive_abstract_pattern_signature(input_text)
    digest = sig.digest_hex16
    if not sig.valid:
        return AdmissionOutcome.REJECTED_NONPRINTABLE, digest
    if sig.classification in _REJECTED_CLASSIFICATIONS:
        return AdmissionOutcome.REJECTED_NONPRINTABLE, digest
    return AdmissionOutcome.ADMITTED, digest


# ---------------------------------------------------------------------------
# Curriculum plan builders.
# ---------------------------------------------------------------------------


def build_curriculum_plan(
    condition: CurriculumCondition,
) -> tuple[CurriculumExposure, ...]:
    """Return the deterministic exposure tuple for ``condition`` (I-CURR-03).

    Deterministic across two invocations on the same condition. The
    returned tuple length is bounded by
    ``CURRICULUM_MAX_EXPOSURES_PER_TRIAL``.

    This is a *default* plan used by trials whose explicit
    ``exposures`` argument is empty; the v1 battery builds its own
    trial-specific exposure tuples directly via
    :func:`build_curriculum_trials`.
    """
    if not isinstance(condition, CurriculumCondition):
        raise TypeError(
            "I-CURR-03 violated: build_curriculum_plan requires a "
            "CurriculumCondition"
        )
    if condition is CurriculumCondition.SINGLE_STRUCTURE:
        return (
            CurriculumExposure(
                exposure_id="X01",
                input_text=_CANONICAL_EXPOSURES["E_AB"],
            ),
        )
    if condition is CurriculumCondition.SEQUENTIAL_NONINTERFERING:
        return (
            CurriculumExposure(
                exposure_id="X01",
                input_text=_CANONICAL_EXPOSURES["E_AB"],
            ),
            CurriculumExposure(
                exposure_id="X02",
                input_text=_CANONICAL_EXPOSURES["E_AA"],
            ),
        )
    if condition is CurriculumCondition.SEQUENTIAL_INTERFERING:
        return (
            CurriculumExposure(
                exposure_id="X01",
                input_text=_CANONICAL_EXPOSURES["E_AB"],
            ),
            CurriculumExposure(
                exposure_id="X02",
                input_text=_CANONICAL_EXPOSURES["E_AB"],
            ),
        )
    if condition is CurriculumCondition.DECAY_ON_DISUSE:
        return (
            CurriculumExposure(
                exposure_id="X01",
                input_text=_CANONICAL_EXPOSURES["E_AB"],
            ),
            CurriculumExposure(
                exposure_id="X02",
                input_text=_CANONICAL_EXPOSURES["E_AA"],
            ),
            CurriculumExposure(
                exposure_id="X03",
                input_text=_CANONICAL_EXPOSURES["E_ABC"],
            ),
            CurriculumExposure(
                exposure_id="X04",
                input_text=_CANONICAL_EXPOSURES["E_AAB"],
            ),
            CurriculumExposure(
                exposure_id="X05",
                input_text=_CANONICAL_EXPOSURES["E_ABA"],
            ),
        )
    if condition is CurriculumCondition.REUSE_AFTER_NEWER:
        return (
            CurriculumExposure(
                exposure_id="X01",
                input_text=_CANONICAL_EXPOSURES["E_AB"],
            ),
            CurriculumExposure(
                exposure_id="X02",
                input_text=_CANONICAL_EXPOSURES["E_AA"],
            ),
            CurriculumExposure(
                exposure_id="X03",
                input_text=_CANONICAL_EXPOSURES["E_ABC"],
            ),
        )
    raise ValueError(
        f"I-CURR-03 violated: unknown CurriculumCondition {condition!r}"
    )


# ---------------------------------------------------------------------------
# Per-trial runner.
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class _SlateEntry:
    """Mutable in-runner bookkeeping (not exposed)."""

    structure_id: str
    source_digest_hex16: str
    admitted_at_step: int
    last_access_step: int
    exposure_index: int


def _evaluate_verdict(
    trial: CurriculumTrial,
    *,
    survived_count: int,
    decayed_count: int,
    rejected_count: int,
    reuse_observed: bool,
) -> tuple[TrialVerdict, bool, bool]:
    """Return ``(verdict, false_positive, false_negative)``."""
    survived_ok = survived_count == trial.expected_survived_count
    decayed_ok = decayed_count == trial.expected_decayed_count
    rejected_ok = rejected_count == trial.expected_rejected_count
    reuse_ok = reuse_observed == trial.expected_reuse_observed
    false_positive = reuse_observed and not trial.expected_reuse_observed
    false_negative = (not reuse_observed) and trial.expected_reuse_observed
    if survived_ok and decayed_ok and rejected_ok and reuse_ok:
        return TrialVerdict.PASS, false_positive, false_negative
    return TrialVerdict.FAIL, false_positive, false_negative


def _run_exposure(
    state: AgentLoopState,
    exposure: CurriculumExposure,
) -> tuple[AgentLoopState, str]:
    """Run one exposure through the agent loop; return new state + dispatch digest."""
    # Empty input is normalized by the runtime; the runner does
    # not skip the runtime path even for rejected exposures.
    state, r = run_agent_interaction_step(state, exposure.input_text)
    if r.latest_dispatch_trace is not None:
        digest = r.latest_dispatch_trace.trace_digest_hex16
    else:
        digest = _zero_digest()
    return state, digest


def _run_probe(
    state: AgentLoopState,
    trial: CurriculumTrial,
    slate: list[_SlateEntry],
    step_index: int,
) -> tuple[
    AgentLoopState,
    Optional[CurriculumProbeStep],
    bool,
    str,
]:
    """Run the optional probe; return new state, probe step, reuse_observed,
    reused_structure_id."""
    if not trial.probe_input:
        return state, None, False, ""

    state, r = run_agent_interaction_step(state, trial.probe_input)
    probe_sig = derive_abstract_pattern_signature(trial.probe_input)

    reused_structure_id = ""
    reuse_observed = False
    for entry in slate:
        if entry.source_digest_hex16 == probe_sig.digest_hex16:
            entry.last_access_step = step_index
            reused_structure_id = entry.structure_id
            reuse_observed = True
            break

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
        r.reply.full_text, limit=CURRICULUM_REPLY_EXCERPT_MAX_LEN
    )
    summary_line = _bounded_excerpt(
        (
            f"curriculum_probe digest={probe_sig.digest_hex16} "
            f"reuse={reuse_observed} "
            f"reused_id={reused_structure_id or '<none>'}"
        ),
        limit=CURRICULUM_SUMMARY_LINE_MAX_LEN,
    )

    step = CurriculumProbeStep(
        probe_input=trial.probe_input,
        probe_digest_hex16=probe_sig.digest_hex16,
        reuse_observed=reuse_observed,
        probe_reused_structure_id=reused_structure_id,
        interaction_id=r.input.input_id,
        dispatch_trace_digest=dispatch_digest,
        reasoning_trace_digest=reasoning_digest,
        reply_excerpt=reply_excerpt,
        summary_line=summary_line,
    )
    return state, step, reuse_observed, reused_structure_id


def run_curriculum_trial(
    trial: CurriculumTrial,
) -> CurriculumTrialResult:
    """Run one trial; return a bounded :class:`CurriculumTrialResult`.

    Pure-deterministic: two invocations on the same trial produce
    bit-identical results. The session-local slate is allocated
    inside the function and does NOT outlive the trial.
    """
    if not isinstance(trial, CurriculumTrial):
        raise TypeError(
            "I-CURR-03 violated: run_curriculum_trial requires a "
            "CurriculumTrial"
        )
    state = make_initial_agent_loop_state()
    slate: list[_SlateEntry] = []
    dispatch_digests: list[str] = []
    # Per-exposure tracking: index -> (admission outcome, source digest,
    # structure_id_or_empty, admitted_at_step_or_minus_one,
    # decayed_at_step_or_minus_one).
    n = len(trial.exposures)
    final_disposition: list[Optional[AuditDisposition]] = [None] * n
    admitted_at: list[int] = [-1] * n
    last_access: list[int] = [-1] * n
    source_digests: list[str] = [""] * n
    structure_ids: list[str] = [""] * n

    for i, exposure in enumerate(trial.exposures):
        outcome, source_digest = _classify_admission(exposure.input_text)
        source_digests[i] = source_digest
        state, dispatch_digest = _run_exposure(state, exposure)
        dispatch_digests.append(dispatch_digest)
        if outcome is AdmissionOutcome.REJECTED_NONPRINTABLE:
            final_disposition[i] = AuditDisposition.REJECTED
            continue
        # Collision check against the live slate.
        collision = False
        for entry in slate:
            if entry.source_digest_hex16 == source_digest:
                collision = True
                break
        if collision:
            final_disposition[i] = AuditDisposition.REJECTED
            continue
        # Admit. Evict LRU if at capacity.
        if len(slate) >= trial.slate_max_entries:
            evicted = slate.pop(0)
            final_disposition[evicted.exposure_index] = (
                AuditDisposition.DECAYED
            )
        structure_id = f"S{i + 1:02d}_{source_digest[:8]}"
        structure_ids[i] = structure_id
        admitted_at[i] = i
        last_access[i] = i
        slate.append(
            _SlateEntry(
                structure_id=structure_id,
                source_digest_hex16=source_digest,
                admitted_at_step=i,
                last_access_step=i,
                exposure_index=i,
            )
        )

    # Optional probe.
    probe_step_index = n
    state, probe_step, reuse_observed, _reused_id = _run_probe(
        state, trial, slate, probe_step_index
    )
    if probe_step is not None:
        dispatch_digests.append(probe_step.dispatch_trace_digest)

    # Survivors are entries still in the slate at end.
    for entry in slate:
        i = entry.exposure_index
        last_access[i] = entry.last_access_step
        final_disposition[i] = AuditDisposition.SURVIVED

    # Build audit records in original exposure order.
    audit_records: list[CurriculumStructureRecord] = []
    for i in range(n):
        disp = final_disposition[i]
        if disp is None:
            # Defensive: every exposure must have a disposition.
            disp = AuditDisposition.REJECTED
        if disp is AuditDisposition.REJECTED:
            # Synthesize a stable structure_id for the audit row.
            structure_id = f"R{i + 1:02d}_{source_digests[i][:8]}"
            admitted_step = 0
            last_step = 0
        else:
            structure_id = structure_ids[i] or f"S{i + 1:02d}_{source_digests[i][:8]}"
            admitted_step = max(0, admitted_at[i])
            last_step = max(admitted_step, last_access[i])
        audit_records.append(
            CurriculumStructureRecord(
                structure_id=structure_id,
                source_digest_hex16=source_digests[i],
                admitted_at_step=admitted_step,
                last_access_step=last_step,
                disposition=disp,
            )
        )

    survived_count = sum(
        1 for r in audit_records
        if r.disposition is AuditDisposition.SURVIVED
    )
    decayed_count = sum(
        1 for r in audit_records
        if r.disposition is AuditDisposition.DECAYED
    )
    rejected_count = sum(
        1 for r in audit_records
        if r.disposition is AuditDisposition.REJECTED
    )

    learning_digest = _learning_evidence_digest(state.learning_trace)
    if probe_step is not None:
        last_reasoning_digest = probe_step.reasoning_trace_digest
    else:
        last_reasoning_digest = _zero_digest()

    verdict, false_positive, false_negative = _evaluate_verdict(
        trial,
        survived_count=survived_count,
        decayed_count=decayed_count,
        rejected_count=rejected_count,
        reuse_observed=reuse_observed,
    )

    summary_line = _bounded_excerpt(
        (
            f"curriculum_trial id={trial.trial_id} "
            f"cond={trial.condition.value} "
            f"exposures={n} survived={survived_count} "
            f"decayed={decayed_count} rejected={rejected_count} "
            f"reuse={reuse_observed} verdict={verdict.value}"
        ),
        limit=CURRICULUM_SUMMARY_LINE_MAX_LEN,
    )

    return CurriculumTrialResult(
        trial_id=trial.trial_id,
        condition=trial.condition,
        verdict=verdict,
        audit_records=tuple(audit_records),
        probe_step=probe_step,
        survived_count=survived_count,
        decayed_count=decayed_count,
        rejected_count=rejected_count,
        reuse_observed=reuse_observed,
        false_positive=false_positive,
        false_negative=false_negative,
        learning_evidence_digest=learning_digest,
        reasoning_trace_digest=last_reasoning_digest,
        dispatch_trace_digests=tuple(dispatch_digests),
        summary_line=summary_line,
    )


# ---------------------------------------------------------------------------
# Trial battery.
# ---------------------------------------------------------------------------


def build_curriculum_trials() -> tuple[CurriculumTrial, ...]:
    """Return the deterministic v1 ten-trial battery (I-CURR-02)."""
    # Reusable exposure constructors.
    def x(eid: str, key: str) -> CurriculumExposure:
        return CurriculumExposure(
            exposure_id=eid,
            input_text=_CANONICAL_EXPOSURES[key],
        )

    def xr(eid: str, key: str) -> CurriculumExposure:
        # Rejected-input exposure (singleton or empty).
        return CurriculumExposure(
            exposure_id=eid,
            input_text=_REJECT_INPUTS[key],
        )

    trials = (
        CurriculumTrial(
            trial_id="T01_single_printable",
            condition=CurriculumCondition.SINGLE_STRUCTURE,
            exposures=(x("X01", "E_AB"),),
            probe_input="",
            slate_max_entries=CURRICULUM_SLATE_MAX_ENTRIES,
            expected_survived_count=1,
            expected_decayed_count=0,
            expected_rejected_count=0,
            expected_reuse_observed=False,
        ),
        CurriculumTrial(
            trial_id="T02_single_singleton",
            condition=CurriculumCondition.SINGLE_STRUCTURE,
            exposures=(xr("X01", "E_SINGLETON"),),
            probe_input="",
            slate_max_entries=CURRICULUM_SLATE_MAX_ENTRIES,
            expected_survived_count=0,
            expected_decayed_count=0,
            expected_rejected_count=1,
            expected_reuse_observed=False,
        ),
        CurriculumTrial(
            trial_id="T03_seq_distinct_2",
            condition=CurriculumCondition.SEQUENTIAL_NONINTERFERING,
            exposures=(x("X01", "E_AB"), x("X02", "E_AA")),
            probe_input="",
            slate_max_entries=CURRICULUM_SLATE_MAX_ENTRIES,
            expected_survived_count=2,
            expected_decayed_count=0,
            expected_rejected_count=0,
            expected_reuse_observed=False,
        ),
        CurriculumTrial(
            trial_id="T04_seq_distinct_3",
            condition=CurriculumCondition.SEQUENTIAL_NONINTERFERING,
            exposures=(
                x("X01", "E_AB"),
                x("X02", "E_AA"),
                x("X03", "E_ABC"),
            ),
            probe_input="",
            slate_max_entries=CURRICULUM_SLATE_MAX_ENTRIES,
            expected_survived_count=3,
            expected_decayed_count=0,
            expected_rejected_count=0,
            expected_reuse_observed=False,
        ),
        CurriculumTrial(
            trial_id="T05_collision_pair",
            condition=CurriculumCondition.SEQUENTIAL_INTERFERING,
            exposures=(x("X01", "E_AB"), x("X02", "E_AB")),
            probe_input="",
            slate_max_entries=CURRICULUM_SLATE_MAX_ENTRIES,
            expected_survived_count=1,
            expected_decayed_count=0,
            expected_rejected_count=1,
            expected_reuse_observed=False,
        ),
        CurriculumTrial(
            trial_id="T06_collision_in_3",
            condition=CurriculumCondition.SEQUENTIAL_INTERFERING,
            exposures=(
                x("X01", "E_AB"),
                x("X02", "E_AA"),
                x("X03", "E_AB"),
            ),
            probe_input="",
            slate_max_entries=CURRICULUM_SLATE_MAX_ENTRIES,
            expected_survived_count=2,
            expected_decayed_count=0,
            expected_rejected_count=1,
            expected_reuse_observed=False,
        ),
        CurriculumTrial(
            trial_id="T07_decay_overflow_5",
            condition=CurriculumCondition.DECAY_ON_DISUSE,
            exposures=(
                x("X01", "E_AB"),
                x("X02", "E_AA"),
                x("X03", "E_ABC"),
                x("X04", "E_AAB"),
                x("X05", "E_ABA"),
            ),
            probe_input="",
            slate_max_entries=CURRICULUM_SLATE_MAX_ENTRIES,
            expected_survived_count=4,
            expected_decayed_count=1,
            expected_rejected_count=0,
            expected_reuse_observed=False,
        ),
        CurriculumTrial(
            trial_id="T08_decay_overflow_6",
            condition=CurriculumCondition.DECAY_ON_DISUSE,
            exposures=(
                x("X01", "E_AB"),
                x("X02", "E_AA"),
                x("X03", "E_ABC"),
                x("X04", "E_AAB"),
                x("X05", "E_ABA"),
                x("X06", "E_ABB"),
            ),
            probe_input="",
            slate_max_entries=CURRICULUM_SLATE_MAX_ENTRIES,
            expected_survived_count=4,
            expected_decayed_count=2,
            expected_rejected_count=0,
            expected_reuse_observed=False,
        ),
        CurriculumTrial(
            trial_id="T09_reuse_oldest",
            condition=CurriculumCondition.REUSE_AFTER_NEWER,
            exposures=(
                x("X01", "E_AB"),
                x("X02", "E_AA"),
                x("X03", "E_ABC"),
            ),
            probe_input=_CANONICAL_EXPOSURES["E_AB"],
            slate_max_entries=CURRICULUM_SLATE_MAX_ENTRIES,
            expected_survived_count=3,
            expected_decayed_count=0,
            expected_rejected_count=0,
            expected_reuse_observed=True,
        ),
        CurriculumTrial(
            trial_id="T10_reuse_negative",
            condition=CurriculumCondition.REUSE_AFTER_NEWER,
            exposures=(
                x("X01", "E_AB"),
                x("X02", "E_AA"),
                x("X03", "E_ABC"),
            ),
            probe_input=_CANONICAL_EXPOSURES["E_AAB"],
            slate_max_entries=CURRICULUM_SLATE_MAX_ENTRIES,
            expected_survived_count=3,
            expected_decayed_count=0,
            expected_rejected_count=0,
            expected_reuse_observed=False,
        ),
    )
    return trials


# ---------------------------------------------------------------------------
# Live test runner + report.
# ---------------------------------------------------------------------------


def _serialize_result(r: CurriculumTrialResult) -> str:
    parts = [
        r.trial_id,
        r.condition.value,
        r.verdict.value,
        f"survived={r.survived_count}",
        f"decayed={r.decayed_count}",
        f"rejected={r.rejected_count}",
        f"reuse={r.reuse_observed}",
        f"fp={r.false_positive}",
        f"fn={r.false_negative}",
        r.learning_evidence_digest,
        r.reasoning_trace_digest,
        "|".join(r.dispatch_trace_digests),
        r.summary_line,
    ]
    for rec in r.audit_records:
        parts.append(
            f"rec|{rec.structure_id}|{rec.source_digest_hex16}|"
            f"a{rec.admitted_at_step}|l{rec.last_access_step}|"
            f"{rec.disposition.value}"
        )
    if r.probe_step is not None:
        p = r.probe_step
        parts.append(
            f"probe|{p.probe_digest_hex16}|{p.reuse_observed}|"
            f"{p.probe_reused_structure_id}|{p.interaction_id}|"
            f"{p.dispatch_trace_digest}|{p.reasoning_trace_digest}"
        )
    return "\n".join(parts)


def curriculum_consolidation_digest(
    report: CurriculumConsolidationReport,
) -> str:
    """Return a deterministic 16-hex digest over the report (I-CURR-11)."""
    payload = "\n".join(_serialize_result(r) for r in report.trials).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()[
        :CURRICULUM_DIGEST_HEX_LEN
    ]


def run_curriculum_consolidation_live_test(
    trials: Optional[tuple[CurriculumTrial, ...]] = None,
) -> CurriculumConsolidationReport:
    """Run every trial in the battery and assemble a report (I-CURR-11)."""
    if trials is None:
        trials = build_curriculum_trials()
    if not isinstance(trials, tuple):
        raise TypeError(
            "I-CURR-03 violated: "
            "run_curriculum_consolidation_live_test trials must be a tuple"
        )

    results: list[CurriculumTrialResult] = [
        run_curriculum_trial(t) for t in trials
    ]

    pass_count = sum(1 for r in results if r.verdict is TrialVerdict.PASS)
    warn_count = sum(1 for r in results if r.verdict is TrialVerdict.WARN)
    fail_count = sum(1 for r in results if r.verdict is TrialVerdict.FAIL)
    na_count = sum(
        1 for r in results if r.verdict is TrialVerdict.NOT_APPLICABLE
    )
    fp_count = sum(1 for r in results if r.false_positive)
    fn_count = sum(1 for r in results if r.false_negative)
    total_survived = sum(r.survived_count for r in results)
    total_decayed = sum(r.decayed_count for r in results)
    total_rejected = sum(r.rejected_count for r in results)
    reuse_observed_count = sum(1 for r in results if r.reuse_observed)

    summary_line = _bounded_excerpt(
        (
            f"curriculum_consolidation_live_test "
            f"version={CURRICULUM_BATTERY_VERSION} "
            f"trials={len(results)} pass={pass_count} warn={warn_count} "
            f"fail={fail_count} na={na_count} fp={fp_count} fn={fn_count} "
            f"survived={total_survived} decayed={total_decayed} "
            f"rejected={total_rejected} reuse={reuse_observed_count}"
        ),
        limit=CURRICULUM_SUMMARY_LINE_MAX_LEN,
    )

    placeholder = CurriculumConsolidationReport(
        battery_version=CURRICULUM_BATTERY_VERSION,
        trials=tuple(results),
        pass_count=pass_count,
        warn_count=warn_count,
        fail_count=fail_count,
        not_applicable_count=na_count,
        false_positive_count=fp_count,
        false_negative_count=fn_count,
        total_survived_count=total_survived,
        total_decayed_count=total_decayed,
        total_rejected_count=total_rejected,
        reuse_observed_count=reuse_observed_count,
        real_model_calls=0,
        cache_writes=0,
        forbidden_term_hits=0,
        digest_hex16=_zero_digest(),
        summary_line=summary_line,
    )
    digest = curriculum_consolidation_digest(placeholder)
    return CurriculumConsolidationReport(
        battery_version=CURRICULUM_BATTERY_VERSION,
        trials=tuple(results),
        pass_count=pass_count,
        warn_count=warn_count,
        fail_count=fail_count,
        not_applicable_count=na_count,
        false_positive_count=fp_count,
        false_negative_count=fn_count,
        total_survived_count=total_survived,
        total_decayed_count=total_decayed,
        total_rejected_count=total_rejected,
        reuse_observed_count=reuse_observed_count,
        real_model_calls=0,
        cache_writes=0,
        forbidden_term_hits=0,
        digest_hex16=digest,
        summary_line=summary_line,
    )


def format_curriculum_consolidation_report(
    report: CurriculumConsolidationReport,
) -> str:
    """Return a bounded printable table over the report (I-CURR-11)."""
    if not isinstance(report, CurriculumConsolidationReport):
        raise TypeError(
            "I-CURR-11 violated: format_curriculum_consolidation_report "
            "requires a CurriculumConsolidationReport"
        )
    lines: list[str] = []
    lines.append(report.summary_line)
    for r in report.trials:
        lines.append(
            f"  {r.trial_id:30s} {r.verdict.value:6s} "
            f"cond={r.condition.value:30s} "
            f"survived={r.survived_count} "
            f"decayed={r.decayed_count} "
            f"rejected={r.rejected_count} "
            f"reuse={r.reuse_observed}"
        )
    lines.append(f"  digest={report.digest_hex16}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-produced strings (audited by the static-audit fixture).
# ---------------------------------------------------------------------------


MODULE_PRODUCED_STRINGS: tuple[str, ...] = (
    CURRICULUM_BATTERY_VERSION,
    CURRICULUM_DIGEST_PREFIX,
    CurriculumCondition.SINGLE_STRUCTURE.value,
    CurriculumCondition.SEQUENTIAL_NONINTERFERING.value,
    CurriculumCondition.SEQUENTIAL_INTERFERING.value,
    CurriculumCondition.DECAY_ON_DISUSE.value,
    CurriculumCondition.REUSE_AFTER_NEWER.value,
    AuditDisposition.SURVIVED.value,
    AuditDisposition.DECAYED.value,
    AuditDisposition.REJECTED.value,
    AdmissionOutcome.ADMITTED.value,
    AdmissionOutcome.REJECTED_COLLISION.value,
    AdmissionOutcome.REJECTED_NONPRINTABLE.value,
    TrialVerdict.PASS.value,
    TrialVerdict.WARN.value,
    TrialVerdict.FAIL.value,
    TrialVerdict.NOT_APPLICABLE.value,
)


# ---------------------------------------------------------------------------
# CLI entry point.
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 3.30 curriculum consolidation live-test runner "
            "(deterministic, OFFLINE, zero real model calls)"
        )
    )
    parser.add_argument("--quiet", action="store_true", default=False)
    args = parser.parse_args(argv)

    report = run_curriculum_consolidation_live_test()
    if not args.quiet:
        sys.stdout.write(
            format_curriculum_consolidation_report(report) + "\n"
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
    "CURRICULUM_BATTERY_VERSION",
    "CURRICULUM_DIGEST_HEX_LEN",
    "CURRICULUM_DIGEST_PREFIX",
    "CURRICULUM_EXPOSURE_ID_MAX_LEN",
    "CURRICULUM_INPUT_MAX_LEN",
    "CURRICULUM_MAX_EXPOSURES_PER_TRIAL",
    "CURRICULUM_MAX_TRIALS",
    "CURRICULUM_PROBE_MAX_LEN",
    "CURRICULUM_REPLY_EXCERPT_MAX_LEN",
    "CURRICULUM_SLATE_MAX_ENTRIES",
    "CURRICULUM_STRUCTURE_ID_MAX_LEN",
    "CURRICULUM_SUMMARY_LINE_MAX_LEN",
    "CURRICULUM_TRIAL_ID_MAX_LEN",
    "AdmissionOutcome",
    "AuditDisposition",
    "CurriculumCondition",
    "CurriculumConsolidationReport",
    "CurriculumExposure",
    "CurriculumProbeStep",
    "CurriculumStructureRecord",
    "CurriculumTrial",
    "CurriculumTrialResult",
    "MODULE_PRODUCED_STRINGS",
    "TrialVerdict",
    "build_curriculum_plan",
    "build_curriculum_trials",
    "curriculum_consolidation_digest",
    "format_curriculum_consolidation_report",
    "main",
    "run_curriculum_consolidation_live_test",
    "run_curriculum_trial",
)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
