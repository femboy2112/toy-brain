"""Phase 3.25 Osmotic Learning Live Test probe.

Deterministic OFFLINE live-test runner that probes whether the
existing substrate (abstract_pattern signature + learning evidence +
reasoning trace + dispatch trace) realizes the operational analogue
of osmotic imprinting (unlabeled ambient exposure creates a
session-local structural record) and activation (a later renamed
probe re-activates that record), under four bounded conditions:

* ``CONTROL_NO_EXPOSURE`` -- no exposure; later probe must NOT
  claim acquisition.
* ``TRUE_EXPOSURE`` -- ambient unlabeled exposure to the target
  shape; later probe should reuse the record.
* ``SHAM_EXPOSURE`` -- exposure to a different abstract digest;
  later target probe must NOT falsely claim acquisition.
* ``DISTRACTOR_INTERFERENCE`` -- target appears among distractors;
  later probe should still recognize.

The runtime path does NOT receive the expected target digest. The
``expected_target_digest`` field on ``OsmoticProbeTrial`` is used
only by the benchmark-assertion layer after
``run_osmotic_probe_trial`` returns.

"Osmotic learning is an operational exposure effect over bounded
structural records, not a psychological or phenomenological claim."

The module is deliberately closed:

* No I/O, no network, no shell, no LLM, no ``brain.tick`` import,
  no ``brain.ui.session`` import, no curses, no threading / asyncio
  / atexit / signal / importlib / time / random.
* The deterministic runner uses ``hashlib`` only at the digest-
  construction boundary (mirroring the existing
  ``agent_benchmark`` and ``dispatch_tracer`` precedents).
* Every bounded printable string this module produces is audited
  against
  ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``
  by the static-audit fixture.

Drives Phase 3.25 catalog rows ``I-OSMO-01..I-OSMO-14``.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Optional

from brain.development.abstract_pattern import (
    AbstractPatternSignature,
    derive_abstract_pattern_signature,
)
from brain.development.agent_loop import (
    AgentLoopResult,
    AgentLoopState,
    make_initial_agent_loop_state,
    run_agent_interaction_step,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.learning_evidence import (
    LearningEvidenceKind,
    has_acquired_digest,
)
from brain.development.reasoning_trace import (
    ReasoningStepKind,
    build_reasoning_trace_report,
)


# ---------------------------------------------------------------------------
# Module constants.
# ---------------------------------------------------------------------------


OSMOTIC_PROBE_BATTERY_VERSION: str = "phase3.25.v1"


OSMOTIC_TRIAL_ID_MAX_LEN: int = 64
OSMOTIC_TEXT_MAX_LEN: int = 240
OSMOTIC_DIGEST_HEX_LEN: int = 16
OSMOTIC_SUMMARY_LINE_MAX_LEN: int = 320
OSMOTIC_MAX_EXPOSURES_PER_TRIAL: int = 8
OSMOTIC_MAX_TRIALS: int = 64


# Forbidden direct-instruction terms that must NOT appear in operator
# inputs (exposure texts or probe texts). The exclusion targets terms
# that would leak the experimental contract into the runtime path.
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
)


# Bounded printable digest prefix used in summary lines.
OSMOTIC_DIGEST_PREFIX: str = "osmotic"


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


class OsmoticCondition(str, Enum):
    """Closed enum of test conditions (Phase 3.25)."""

    CONTROL_NO_EXPOSURE = "control_no_exposure"
    TRUE_EXPOSURE = "true_exposure"
    SHAM_EXPOSURE = "sham_exposure"
    DISTRACTOR_INTERFERENCE = "distractor_interference"


_OSMOTIC_CONDITION_VALUES: frozenset[str] = frozenset(
    {c.value for c in OsmoticCondition}
)


class OsmoticProbeStatus(str, Enum):
    """Closed enum of per-trial verdicts (Phase 3.25)."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


_OSMOTIC_PROBE_STATUS_VALUES: frozenset[str] = frozenset(
    {s.value for s in OsmoticProbeStatus}
)


# ---------------------------------------------------------------------------
# Frozen records.
# ---------------------------------------------------------------------------


def _validate_bounded_printable(
    value: object,
    *,
    field: str,
    max_len: int,
    forbid_empty: bool = True,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"I-OSMO-01 violated: {field} must be a string "
            f"(got {type(value).__name__})"
        )
    if forbid_empty and not value:
        raise ValueError(
            f"I-OSMO-01 violated: {field} must be non-empty"
        )
    if value and not value.isprintable():
        raise ValueError(
            f"I-OSMO-01 violated: {field} must be printable"
        )
    if len(value) > max_len:
        raise ValueError(
            f"I-OSMO-01 violated: {field} length {len(value)} > {max_len}"
        )
    term = _has_forbidden_non_claim_term(value)
    if term is not None:
        raise ValueError(
            f"I-OSMO-01 violated: {field} contains forbidden non-claim "
            f"term {term!r}"
        )
    return value


@dataclass(frozen=True, slots=True)
class OsmoticExposureEvent:
    """One bounded exposure step within a trial (I-OSMO-01)."""

    text: str
    interaction_id: str
    abstract_digest_hex16: str
    classification: str
    shape: str

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.text, field="OsmoticExposureEvent.text",
            max_len=OSMOTIC_TEXT_MAX_LEN,
        )
        _validate_bounded_printable(
            self.interaction_id,
            field="OsmoticExposureEvent.interaction_id",
            max_len=OSMOTIC_TRIAL_ID_MAX_LEN,
        )
        if (
            not isinstance(self.abstract_digest_hex16, str)
            or len(self.abstract_digest_hex16) != OSMOTIC_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-OSMO-01 violated: OsmoticExposureEvent."
                "abstract_digest_hex16 must be a 16-char hex string"
            )
        _validate_bounded_printable(
            self.classification,
            field="OsmoticExposureEvent.classification",
            max_len=OSMOTIC_TEXT_MAX_LEN,
        )
        _validate_bounded_printable(
            self.shape,
            field="OsmoticExposureEvent.shape",
            max_len=OSMOTIC_TEXT_MAX_LEN,
            forbid_empty=False,
        )


@dataclass(frozen=True, slots=True)
class OsmoticProbeTrial:
    """One bounded trial specification (I-OSMO-02)."""

    trial_id: str
    condition: OsmoticCondition
    exposure_texts: tuple[str, ...]
    probe_text: str
    expected_target_digest: str
    expected_target_shape: str
    expected_prior_acquired: bool
    expected_transfer: bool

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.trial_id,
            field="OsmoticProbeTrial.trial_id",
            max_len=OSMOTIC_TRIAL_ID_MAX_LEN,
        )
        if not isinstance(self.condition, OsmoticCondition):
            raise TypeError(
                "I-OSMO-02 violated: OsmoticProbeTrial.condition must be a "
                "OsmoticCondition member"
            )
        if not isinstance(self.exposure_texts, tuple):
            raise TypeError(
                "I-OSMO-02 violated: OsmoticProbeTrial.exposure_texts must "
                "be a tuple"
            )
        if len(self.exposure_texts) > OSMOTIC_MAX_EXPOSURES_PER_TRIAL:
            raise ValueError(
                "I-OSMO-02 violated: OsmoticProbeTrial.exposure_texts "
                f"length {len(self.exposure_texts)} exceeds "
                f"{OSMOTIC_MAX_EXPOSURES_PER_TRIAL}"
            )
        for i, t in enumerate(self.exposure_texts):
            _validate_bounded_printable(
                t,
                field=f"OsmoticProbeTrial.exposure_texts[{i}]",
                max_len=OSMOTIC_TEXT_MAX_LEN,
            )
            term = _has_forbidden_direct_instruction(t)
            if term is not None:
                raise ValueError(
                    "I-OSMO-02 violated: exposure text "
                    f"contains forbidden direct-instruction term {term!r}"
                )
        _validate_bounded_printable(
            self.probe_text,
            field="OsmoticProbeTrial.probe_text",
            max_len=OSMOTIC_TEXT_MAX_LEN,
        )
        term = _has_forbidden_direct_instruction(self.probe_text)
        if term is not None:
            raise ValueError(
                "I-OSMO-02 violated: probe text contains forbidden "
                f"direct-instruction term {term!r}"
            )
        if (
            not isinstance(self.expected_target_digest, str)
            or len(self.expected_target_digest) != OSMOTIC_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-OSMO-02 violated: OsmoticProbeTrial."
                "expected_target_digest must be a 16-char hex string"
            )
        _validate_bounded_printable(
            self.expected_target_shape,
            field="OsmoticProbeTrial.expected_target_shape",
            max_len=OSMOTIC_TEXT_MAX_LEN,
            forbid_empty=False,
        )
        for name, value in (
            ("expected_prior_acquired", self.expected_prior_acquired),
            ("expected_transfer", self.expected_transfer),
        ):
            if not isinstance(value, bool):
                raise TypeError(
                    f"I-OSMO-02 violated: OsmoticProbeTrial.{name} must "
                    f"be bool (got {type(value).__name__})"
                )


@dataclass(frozen=True, slots=True)
class OsmoticProbeResult:
    """One bounded probe-result record (I-OSMO-02)."""

    trial_id: str
    condition: OsmoticCondition
    status: OsmoticProbeStatus
    exposure_events: tuple[OsmoticExposureEvent, ...]
    probe_digest: str
    probe_shape: str
    probe_classification: str
    prior_acquired_observed: bool
    transfer_observed: bool
    expected_prior_acquired: bool
    expected_transfer: bool
    false_positive: bool
    false_negative: bool
    learning_evidence_digest: str
    reasoning_trace_digest: str
    dispatch_trace_digests: tuple[str, ...]
    reply_excerpt: str
    summary_line: str

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.trial_id,
            field="OsmoticProbeResult.trial_id",
            max_len=OSMOTIC_TRIAL_ID_MAX_LEN,
        )
        if not isinstance(self.condition, OsmoticCondition):
            raise TypeError(
                "I-OSMO-02 violated: OsmoticProbeResult.condition must be "
                "a OsmoticCondition member"
            )
        if not isinstance(self.status, OsmoticProbeStatus):
            raise TypeError(
                "I-OSMO-02 violated: OsmoticProbeResult.status must be a "
                "OsmoticProbeStatus member"
            )
        if not isinstance(self.exposure_events, tuple):
            raise TypeError(
                "I-OSMO-02 violated: OsmoticProbeResult.exposure_events "
                "must be a tuple"
            )
        for ev in self.exposure_events:
            if not isinstance(ev, OsmoticExposureEvent):
                raise TypeError(
                    "I-OSMO-02 violated: OsmoticProbeResult."
                    "exposure_events entries must be OsmoticExposureEvent"
                )
        if (
            not isinstance(self.probe_digest, str)
            or len(self.probe_digest) != OSMOTIC_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-OSMO-02 violated: OsmoticProbeResult.probe_digest "
                "must be a 16-char hex string"
            )
        _validate_bounded_printable(
            self.probe_shape,
            field="OsmoticProbeResult.probe_shape",
            max_len=OSMOTIC_TEXT_MAX_LEN,
            forbid_empty=False,
        )
        _validate_bounded_printable(
            self.probe_classification,
            field="OsmoticProbeResult.probe_classification",
            max_len=OSMOTIC_TEXT_MAX_LEN,
        )
        for name, value in (
            ("prior_acquired_observed", self.prior_acquired_observed),
            ("transfer_observed", self.transfer_observed),
            ("expected_prior_acquired", self.expected_prior_acquired),
            ("expected_transfer", self.expected_transfer),
            ("false_positive", self.false_positive),
            ("false_negative", self.false_negative),
        ):
            if not isinstance(value, bool):
                raise TypeError(
                    f"I-OSMO-02 violated: OsmoticProbeResult.{name} must "
                    "be bool"
                )
        for name, value in (
            (
                "learning_evidence_digest",
                self.learning_evidence_digest,
            ),
            (
                "reasoning_trace_digest",
                self.reasoning_trace_digest,
            ),
        ):
            if (
                not isinstance(value, str)
                or len(value) != OSMOTIC_DIGEST_HEX_LEN
            ):
                raise ValueError(
                    f"I-OSMO-02 violated: OsmoticProbeResult.{name} must "
                    "be a 16-char hex string"
                )
        if not isinstance(self.dispatch_trace_digests, tuple):
            raise TypeError(
                "I-OSMO-02 violated: OsmoticProbeResult."
                "dispatch_trace_digests must be a tuple"
            )
        for d in self.dispatch_trace_digests:
            if not isinstance(d, str) or len(d) != OSMOTIC_DIGEST_HEX_LEN:
                raise ValueError(
                    "I-OSMO-02 violated: OsmoticProbeResult."
                    "dispatch_trace_digests entries must be 16-char hex"
                )
        _validate_bounded_printable(
            self.reply_excerpt,
            field="OsmoticProbeResult.reply_excerpt",
            max_len=OSMOTIC_SUMMARY_LINE_MAX_LEN,
        )
        _validate_bounded_printable(
            self.summary_line,
            field="OsmoticProbeResult.summary_line",
            max_len=OSMOTIC_SUMMARY_LINE_MAX_LEN,
        )


@dataclass(frozen=True, slots=True)
class OsmoticLiveTestReport:
    """Bounded aggregate report over a live-test run (I-OSMO-12)."""

    module_name: ClassVar[str] = "osmotic_learning_probe"

    battery_version: str
    trials: tuple[OsmoticProbeResult, ...]
    pass_count: int
    warn_count: int
    fail_count: int
    not_applicable_count: int
    false_positive_count: int
    false_negative_count: int
    transfer_success_count: int
    real_model_calls: int
    cache_writes: int
    forbidden_term_hits: int
    digest_hex16: str
    summary_line: str

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.battery_version,
            field="OsmoticLiveTestReport.battery_version",
            max_len=OSMOTIC_TEXT_MAX_LEN,
        )
        if not isinstance(self.trials, tuple):
            raise TypeError(
                "I-OSMO-12 violated: OsmoticLiveTestReport.trials must be "
                "a tuple"
            )
        if len(self.trials) > OSMOTIC_MAX_TRIALS:
            raise ValueError(
                "I-OSMO-12 violated: OsmoticLiveTestReport.trials length "
                f"{len(self.trials)} exceeds {OSMOTIC_MAX_TRIALS}"
            )
        for t in self.trials:
            if not isinstance(t, OsmoticProbeResult):
                raise TypeError(
                    "I-OSMO-12 violated: OsmoticLiveTestReport.trials "
                    "entries must be OsmoticProbeResult"
                )
        for name, value in (
            ("pass_count", self.pass_count),
            ("warn_count", self.warn_count),
            ("fail_count", self.fail_count),
            ("not_applicable_count", self.not_applicable_count),
            ("false_positive_count", self.false_positive_count),
            ("false_negative_count", self.false_negative_count),
            ("transfer_success_count", self.transfer_success_count),
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
                    f"I-OSMO-12 violated: OsmoticLiveTestReport.{name} "
                    "must be a non-negative int"
                )
        if (
            not isinstance(self.digest_hex16, str)
            or len(self.digest_hex16) != OSMOTIC_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-OSMO-12 violated: OsmoticLiveTestReport.digest_hex16 "
                "must be a 16-char hex string"
            )
        _validate_bounded_printable(
            self.summary_line,
            field="OsmoticLiveTestReport.summary_line",
            max_len=OSMOTIC_SUMMARY_LINE_MAX_LEN,
        )


# ---------------------------------------------------------------------------
# Exposure plan + runner.
# ---------------------------------------------------------------------------


def build_osmotic_exposure_plan() -> tuple[OsmoticProbeTrial, ...]:
    """Return the deterministic v1 ten-trial battery (I-OSMO-02).

    The trial battery covers every condition + every target shape
    documented in
    ``docs/campaigns/phase3_25/PHASE3_25_OSMOTIC_LEARNING_TEST_DESIGN.md``.
    """
    # Precompute target digests by running derive over a canonical
    # example. This is structural; no answer key leaks into the
    # runtime path because the digests are inputs to the assertion
    # layer only.
    abab_digest = derive_abstract_pattern_signature("red blue red blue").digest_hex16
    abba_digest = derive_abstract_pattern_signature("copper tin tin copper").digest_hex16
    aab_digest = derive_abstract_pattern_signature("red red blue").digest_hex16
    abcabc_digest = derive_abstract_pattern_signature(
        "red blue green red blue green"
    ).digest_hex16

    trials = (
        OsmoticProbeTrial(
            trial_id="T01_control_abab",
            condition=OsmoticCondition.CONTROL_NO_EXPOSURE,
            exposure_texts=(),
            probe_text="cat dog cat dog",
            expected_target_digest=abab_digest,
            expected_target_shape="A B A B",
            expected_prior_acquired=False,
            expected_transfer=False,
        ),
        OsmoticProbeTrial(
            trial_id="T02_true_abab",
            condition=OsmoticCondition.TRUE_EXPOSURE,
            exposure_texts=("red blue red blue",),
            probe_text="cat dog cat dog",
            expected_target_digest=abab_digest,
            expected_target_shape="A B A B",
            expected_prior_acquired=True,
            expected_transfer=True,
        ),
        OsmoticProbeTrial(
            trial_id="T03_true_abba",
            condition=OsmoticCondition.TRUE_EXPOSURE,
            exposure_texts=("copper tin tin copper",),
            probe_text="moon sun sun moon",
            expected_target_digest=abba_digest,
            expected_target_shape="A B B A",
            expected_prior_acquired=True,
            expected_transfer=True,
        ),
        OsmoticProbeTrial(
            trial_id="T04_true_abcabc",
            condition=OsmoticCondition.TRUE_EXPOSURE,
            exposure_texts=("red blue green red blue green",),
            probe_text="cat dog bird cat dog bird",
            expected_target_digest=abcabc_digest,
            expected_target_shape="A B C A B C",
            expected_prior_acquired=True,
            expected_transfer=True,
        ),
        OsmoticProbeTrial(
            trial_id="T05_sham_abba_for_abab",
            condition=OsmoticCondition.SHAM_EXPOSURE,
            exposure_texts=("red blue blue red",),
            probe_text="cat dog cat dog",
            expected_target_digest=abab_digest,
            expected_target_shape="A B A B",
            expected_prior_acquired=False,
            expected_transfer=False,
        ),
        OsmoticProbeTrial(
            trial_id="T06_distractor_abab",
            condition=OsmoticCondition.DISTRACTOR_INTERFERENCE,
            exposure_texts=(
                "red blue red blue",
                "kettle pot kettle pot",
                "moss fern moss fern",
            ),
            probe_text="cat dog cat dog",
            expected_target_digest=abab_digest,
            expected_target_shape="A B A B",
            expected_prior_acquired=True,
            expected_transfer=True,
        ),
        OsmoticProbeTrial(
            trial_id="T07_delayed_abab",
            condition=OsmoticCondition.TRUE_EXPOSURE,
            exposure_texts=(
                "red blue red blue",
                "kettle pot",
                "moss fern",
            ),
            probe_text="cat dog cat dog",
            expected_target_digest=abab_digest,
            expected_target_shape="A B A B",
            expected_prior_acquired=True,
            expected_transfer=True,
        ),
        OsmoticProbeTrial(
            trial_id="T08_control_aab",
            condition=OsmoticCondition.CONTROL_NO_EXPOSURE,
            exposure_texts=(),
            probe_text="cat cat dog",
            expected_target_digest=aab_digest,
            expected_target_shape="A A B",
            expected_prior_acquired=False,
            expected_transfer=False,
        ),
        OsmoticProbeTrial(
            trial_id="T09_renamed_aab",
            condition=OsmoticCondition.TRUE_EXPOSURE,
            exposure_texts=("red red blue",),
            probe_text="cat cat dog",
            expected_target_digest=aab_digest,
            expected_target_shape="A A B",
            expected_prior_acquired=True,
            expected_transfer=True,
        ),
        OsmoticProbeTrial(
            trial_id="T10_distractor_abcabc",
            condition=OsmoticCondition.DISTRACTOR_INTERFERENCE,
            exposure_texts=(
                "red blue green red blue green",
                "kettle pot kettle pot",
                "moss fern moss fern",
            ),
            probe_text="cat dog bird cat dog bird",
            expected_target_digest=abcabc_digest,
            expected_target_shape="A B C A B C",
            expected_prior_acquired=True,
            expected_transfer=True,
        ),
    )
    return trials


def _bounded_excerpt(text: str, *, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 4)] + " ..."


def _signature_for(text: str) -> AbstractPatternSignature:
    return derive_abstract_pattern_signature(text)


def _new_state() -> AgentLoopState:
    return make_initial_agent_loop_state()


def _learning_evidence_digest(records: tuple) -> str:
    payload = b""
    for r in records:
        payload += f"{r.kind.value}|{r.interaction_id}|{r.abstract_pattern_digest}|{r.pattern_id}".encode("utf-8")
        payload += b"\n"
    return hashlib.sha256(payload).hexdigest()[:OSMOTIC_DIGEST_HEX_LEN]


def _step_for_kind(trace, kind: ReasoningStepKind):
    for s in trace.steps:
        if s.kind is kind:
            return s
    return None


def run_osmotic_probe_trial(trial: OsmoticProbeTrial) -> OsmoticProbeResult:
    """Run one trial; return a bounded :class:`OsmoticProbeResult`.

    Pure-deterministic: two invocations on the same trial produce
    bit-identical results.

    The runtime path (``run_agent_interaction_step``) is fed only
    operator text. The expected target digest from ``trial`` is used
    only to compute the verdict and the bounded ``summary_line``;
    it never enters the agent loop's input.
    """
    if not isinstance(trial, OsmoticProbeTrial):
        raise TypeError(
            "I-OSMO-03 violated: run_osmotic_probe_trial requires a "
            "OsmoticProbeTrial"
        )

    state = _new_state()
    exposure_events: list[OsmoticExposureEvent] = []
    exposure_dispatch_digests: list[str] = []

    for i, text in enumerate(trial.exposure_texts):
        state, r = run_agent_interaction_step(state, text)
        sig = _signature_for(text)
        exposure_events.append(
            OsmoticExposureEvent(
                text=text,
                interaction_id=r.input.input_id,
                abstract_digest_hex16=sig.digest_hex16,
                classification=sig.classification,
                shape=sig.shape,
            )
        )
        if r.latest_dispatch_trace is not None:
            exposure_dispatch_digests.append(
                r.latest_dispatch_trace.trace_digest_hex16
            )

    # Snapshot whether the target digest is acquired BEFORE the probe.
    prior_acquired_observed = has_acquired_digest(
        state.learning_trace, trial.expected_target_digest
    )

    # Run the probe step.
    pre_probe_records_len = len(state.learning_trace.records)
    state, probe_r = run_agent_interaction_step(state, trial.probe_text)
    probe_sig = _signature_for(trial.probe_text)
    probe_dispatch_digest = (
        probe_r.latest_dispatch_trace.trace_digest_hex16
        if probe_r.latest_dispatch_trace is not None
        else ""
    )

    # Did the probe step emit TRANSFER_RECOGNIZED for the target digest?
    new_records = state.learning_trace.records[pre_probe_records_len:]
    transfer_observed = any(
        r.kind is LearningEvidenceKind.TRANSFER_RECOGNIZED
        and r.abstract_pattern_digest == trial.expected_target_digest
        for r in new_records
    )

    # Derive verdict.
    false_positive = transfer_observed and not trial.expected_transfer
    false_negative = (not transfer_observed) and trial.expected_transfer
    prior_acquired_match = (
        prior_acquired_observed == trial.expected_prior_acquired
    )
    status = (
        OsmoticProbeStatus.PASS
        if (not false_positive and not false_negative and prior_acquired_match)
        else OsmoticProbeStatus.FAIL
    )

    # Bounded summary line.
    summary_line = (
        f"osmotic_trial id={trial.trial_id} cond={trial.condition.value} "
        f"prior_acquired={prior_acquired_observed} "
        f"expected_prior={trial.expected_prior_acquired} "
        f"transfer={transfer_observed} "
        f"expected_transfer={trial.expected_transfer} "
        f"status={status.value}"
    )
    summary_line = _bounded_excerpt(
        summary_line, limit=OSMOTIC_SUMMARY_LINE_MAX_LEN
    )

    # Reasoning + learning digests.
    reasoning_digest = (
        build_reasoning_trace_report(probe_r.reasoning_trace).trace_digest_hex16
        if probe_r.reasoning_trace is not None
        else "0" * OSMOTIC_DIGEST_HEX_LEN
    )
    learning_digest = _learning_evidence_digest(state.learning_trace.records)

    reply_excerpt = _bounded_excerpt(
        probe_r.reply.full_text, limit=OSMOTIC_SUMMARY_LINE_MAX_LEN
    )

    dispatch_digests: tuple[str, ...] = tuple(
        list(exposure_dispatch_digests) + ([probe_dispatch_digest] if probe_dispatch_digest else [])
    )

    return OsmoticProbeResult(
        trial_id=trial.trial_id,
        condition=trial.condition,
        status=status,
        exposure_events=tuple(exposure_events),
        probe_digest=probe_sig.digest_hex16,
        probe_shape=probe_sig.shape,
        probe_classification=probe_sig.classification,
        prior_acquired_observed=prior_acquired_observed,
        transfer_observed=transfer_observed,
        expected_prior_acquired=trial.expected_prior_acquired,
        expected_transfer=trial.expected_transfer,
        false_positive=false_positive,
        false_negative=false_negative,
        learning_evidence_digest=learning_digest,
        reasoning_trace_digest=reasoning_digest,
        dispatch_trace_digests=dispatch_digests,
        reply_excerpt=reply_excerpt,
        summary_line=summary_line,
    )


def _serialize_result(r: OsmoticProbeResult) -> str:
    parts = [
        r.trial_id,
        r.condition.value,
        r.status.value,
        r.probe_digest,
        r.probe_shape,
        r.probe_classification,
        f"prior={r.prior_acquired_observed}",
        f"transfer={r.transfer_observed}",
        f"fp={r.false_positive}",
        f"fn={r.false_negative}",
        r.learning_evidence_digest,
        r.reasoning_trace_digest,
        "|".join(r.dispatch_trace_digests),
        r.summary_line,
    ]
    for ev in r.exposure_events:
        parts.append(
            f"ev|{ev.interaction_id}|{ev.abstract_digest_hex16}|"
            f"{ev.classification}|{ev.shape}"
        )
    return "\n".join(parts)


def osmotic_live_test_digest(report: OsmoticLiveTestReport) -> str:
    """Return a deterministic 16-hex digest over the report (I-OSMO-12)."""
    payload = "\n".join(_serialize_result(r) for r in report.trials).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()[:OSMOTIC_DIGEST_HEX_LEN]


def run_osmotic_live_test(
    trials: Optional[tuple[OsmoticProbeTrial, ...]] = None,
) -> OsmoticLiveTestReport:
    """Run every trial in the battery and assemble a report (I-OSMO-12).

    Two invocations on the same trial battery produce bit-identical
    reports.
    """
    if trials is None:
        trials = build_osmotic_exposure_plan()
    if not isinstance(trials, tuple):
        raise TypeError(
            "I-OSMO-03 violated: run_osmotic_live_test trials must be a "
            "tuple"
        )

    results: list[OsmoticProbeResult] = []
    for t in trials:
        results.append(run_osmotic_probe_trial(t))

    pass_count = sum(
        1 for r in results if r.status is OsmoticProbeStatus.PASS
    )
    warn_count = sum(
        1 for r in results if r.status is OsmoticProbeStatus.WARN
    )
    fail_count = sum(
        1 for r in results if r.status is OsmoticProbeStatus.FAIL
    )
    na_count = sum(
        1 for r in results if r.status is OsmoticProbeStatus.NOT_APPLICABLE
    )
    fp_count = sum(1 for r in results if r.false_positive)
    fn_count = sum(1 for r in results if r.false_negative)
    transfer_success_count = sum(
        1
        for r in results
        if r.transfer_observed and r.expected_transfer
    )

    summary_line = _bounded_excerpt(
        (
            f"osmotic_live_test version={OSMOTIC_PROBE_BATTERY_VERSION} "
            f"trials={len(results)} pass={pass_count} warn={warn_count} "
            f"fail={fail_count} na={na_count} fp={fp_count} fn={fn_count} "
            f"transfer_success={transfer_success_count}"
        ),
        limit=OSMOTIC_SUMMARY_LINE_MAX_LEN,
    )

    # Build the report with a placeholder digest, then attach the
    # canonical digest. We compute the digest from the tuple of
    # results (independent of summary_line).
    placeholder_digest = "0" * OSMOTIC_DIGEST_HEX_LEN
    placeholder = OsmoticLiveTestReport(
        battery_version=OSMOTIC_PROBE_BATTERY_VERSION,
        trials=tuple(results),
        pass_count=pass_count,
        warn_count=warn_count,
        fail_count=fail_count,
        not_applicable_count=na_count,
        false_positive_count=fp_count,
        false_negative_count=fn_count,
        transfer_success_count=transfer_success_count,
        real_model_calls=0,
        cache_writes=0,
        forbidden_term_hits=0,
        digest_hex16=placeholder_digest,
        summary_line=summary_line,
    )
    digest = osmotic_live_test_digest(placeholder)
    return OsmoticLiveTestReport(
        battery_version=OSMOTIC_PROBE_BATTERY_VERSION,
        trials=tuple(results),
        pass_count=pass_count,
        warn_count=warn_count,
        fail_count=fail_count,
        not_applicable_count=na_count,
        false_positive_count=fp_count,
        false_negative_count=fn_count,
        transfer_success_count=transfer_success_count,
        real_model_calls=0,
        cache_writes=0,
        forbidden_term_hits=0,
        digest_hex16=digest,
        summary_line=summary_line,
    )


def format_osmotic_live_test_report(report: OsmoticLiveTestReport) -> str:
    """Return a bounded printable table over the report (I-OSMO-12)."""
    if not isinstance(report, OsmoticLiveTestReport):
        raise TypeError(
            "I-OSMO-12 violated: format_osmotic_live_test_report requires "
            "a OsmoticLiveTestReport"
        )
    lines: list[str] = []
    lines.append(report.summary_line)
    for r in report.trials:
        lines.append(
            f"  {r.trial_id:32s} {r.status.value:6s} "
            f"cond={r.condition.value:24s} "
            f"prior={r.prior_acquired_observed} "
            f"transfer={r.transfer_observed} "
            f"probe_digest={r.probe_digest}"
        )
    lines.append(f"  digest={report.digest_hex16}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-produced strings (audited).
# ---------------------------------------------------------------------------


MODULE_PRODUCED_STRINGS: tuple[str, ...] = (
    OSMOTIC_PROBE_BATTERY_VERSION,
    OSMOTIC_DIGEST_PREFIX,
    OsmoticCondition.CONTROL_NO_EXPOSURE.value,
    OsmoticCondition.TRUE_EXPOSURE.value,
    OsmoticCondition.SHAM_EXPOSURE.value,
    OsmoticCondition.DISTRACTOR_INTERFERENCE.value,
    OsmoticProbeStatus.PASS.value,
    OsmoticProbeStatus.WARN.value,
    OsmoticProbeStatus.FAIL.value,
    OsmoticProbeStatus.NOT_APPLICABLE.value,
)


# ---------------------------------------------------------------------------
# CLI entry point.
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 3.25 osmotic learning live-test runner "
            "(deterministic, OFFLINE, zero real model calls)"
        )
    )
    parser.add_argument("--quiet", action="store_true", default=False)
    args = parser.parse_args(argv)

    report = run_osmotic_live_test()
    if not args.quiet:
        sys.stdout.write(format_osmotic_live_test_report(report) + "\n")
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
    "MODULE_PRODUCED_STRINGS",
    "OSMOTIC_DIGEST_HEX_LEN",
    "OSMOTIC_DIGEST_PREFIX",
    "OSMOTIC_MAX_EXPOSURES_PER_TRIAL",
    "OSMOTIC_MAX_TRIALS",
    "OSMOTIC_PROBE_BATTERY_VERSION",
    "OSMOTIC_SUMMARY_LINE_MAX_LEN",
    "OSMOTIC_TEXT_MAX_LEN",
    "OSMOTIC_TRIAL_ID_MAX_LEN",
    "OsmoticCondition",
    "OsmoticExposureEvent",
    "OsmoticLiveTestReport",
    "OsmoticProbeResult",
    "OsmoticProbeStatus",
    "OsmoticProbeTrial",
    "build_osmotic_exposure_plan",
    "format_osmotic_live_test_report",
    "main",
    "osmotic_live_test_digest",
    "run_osmotic_live_test",
    "run_osmotic_probe_trial",
)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
