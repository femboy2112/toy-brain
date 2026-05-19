"""Phase 3.31 Caregiver-Scaffolded Proto-Speech Acquisition runner.

Deterministic OFFLINE live-test runner that probes whether the
existing substrate (abstract_pattern signature + learning evidence
+ reasoning trace + dispatch trace + worldlet feedback + the Phase
3.25 osmotic surface + the Phase 3.26 active-hypothesis surface +
the Phase 3.30 curriculum-consolidation surface) realizes the
operational analogue of *caregiver-scaffolded proto-speech
acquisition*: given a bounded structural context and bounded
caregiver ambient utterances + feedback,

* the runtime constructs a bounded explicit
  ``ProtoSpeechDriveStream`` from public substrate snapshots;
* selects a deterministic bounded ``ProtoUtterance`` from the
  drive stream filtered by a session-local
  ``ProtoSpeechEvidenceTable``;
* updates the evidence table by closed-rule integer weights
  driven by a closed ``CaregiverFeedbackKind`` set;
* promotes single-token forms to ``STABLE_SINGLE`` after enough
  reinforcement;
* emits a ``STABLE_COMBINATION`` two-token form only when
  combination pressure and two distinct stable singles exist;
* transfers a stable single only to a same-shape-digest context;
* suppresses forms below the suppression threshold;
* preserves the cognitive-claim refusal path.

"Proto-speech acquisition in ToyI is a bounded operational
co-occurrence-weights + closed-rule evidence-update +
drive-stream-grounded selection + shape-digest transfer effect
over structural records, not a psychological or phenomenological
claim. ToyI does not have language, communicative intent, inner
speech, hidden chain-of-thought, private subjective thought,
agency, will, desire, belief, introspection, or metacognition."

The ``ProtoSpeechDriveStream`` is the bounded, EXPLICIT, AUDITABLE
substitute for inner speech: every drive frame names a closed
``ProtoSpeechDriveKind``, a bounded ``source_surface`` (the public
substrate it derives from), a bounded ``suggested_token_set`` of
closed-inventory tokens, and a bounded printable explanation. The
drive stream is NOT private mutable state; it is constructed
fresh per turn from public substrate snapshots and is included in
every proof artifact.

The module is deliberately closed:

* No I/O, no network, no shell, no LLM, no ``brain.tick`` import,
  no ``brain.ui`` import, no curses, no threading / asyncio /
  atexit / signal / importlib / time / random / pathlib / math /
  os.
* The deterministic runner uses ``hashlib`` only at the digest-
  construction boundary (mirroring the Phase 3.25
  ``osmotic_learning_probe``, the Phase 3.26
  ``active_hypothesis_probe``, and the Phase 3.30
  ``curriculum_consolidation_probe`` precedents).
* Every bounded printable string this module produces is audited
  against
  ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``
  by the static-audit fixture.

Drives Phase 3.31 catalog rows ``I-PSPEECH-01..I-PSPEECH-19``.
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


PROTO_SPEECH_BATTERY_VERSION: str = "phase3.31.v1"


PROTO_SPEECH_TURN_ID_MAX_LEN: int = 64
PROTO_SPEECH_CONTEXT_LABEL_MAX_LEN: int = 64
PROTO_SPEECH_TEXT_MAX_LEN: int = 64
PROTO_SPEECH_EXPLAIN_MAX_LEN: int = 240
PROTO_SPEECH_DIGEST_HEX_LEN: int = 16
PROTO_SPEECH_MAX_TURNS_PER_CONDITION: int = 12
PROTO_SPEECH_MAX_TURNS_PER_REPORT: int = 96
PROTO_SPEECH_MAX_FRAMES_PER_STREAM: int = 12
PROTO_SPEECH_SUGGESTED_SET_MAX: int = 8
PROTO_SPEECH_WEIGHT_HINT_MAX: int = 16
PROTO_SPEECH_WEIGHT_MIN: int = -8
PROTO_SPEECH_WEIGHT_MAX: int = 16
PROTO_SPEECH_EVIDENCE_TABLE_MAX: int = 64
PROTO_SPEECH_SOURCE_SURFACE_MAX_LEN: int = 64

#: Reinforcement / suppression thresholds.
STABLE_SINGLE_THRESHOLD: int = 6
STABLE_COMBINATION_THRESHOLD: int = 8
SUPPRESS_THRESHOLD: int = -3


PROTO_SPEECH_DIGEST_PREFIX: str = "proto_speech_acquisition"


# Forbidden direct-instruction terms that must NOT appear in
# operator-input text (caregiver ambient utterance text or
# context labels). Extends the Phase 3.30 list with proto-speech-
# specific vocabulary so the operator-input path cannot leak the
# experimental contract.
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
    "talk",
    "speak",
    "vocalize",
    "babble",
    "utter",
    "language",
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


class ProtoVocalToken(str, Enum):
    """Closed bounded proto-vocal inventory (Phase 3.31).

    The inventory is uninterpreted at birth. A token becomes
    functionally bound to a context only after evidence
    accumulation.
    """

    BA = "ba"
    MA = "ma"
    DA = "da"
    NA = "na"
    LA = "la"
    SAME = "same"
    MORE = "more"
    AGAIN = "again"
    NO = "no"
    YES = "yes"
    LOOK = "look"
    THIS = "this"
    THAT = "that"
    HELP = "help"
    DONE = "done"


_PROTO_VOCAL_TOKEN_VALUES: frozenset[str] = frozenset(
    {t.value for t in ProtoVocalToken}
)


# Canonical enumeration order used by the deterministic selection
# rule. Members() preserves declaration order in Python 3.11+.
_PROTO_VOCAL_TOKEN_ORDER: tuple[ProtoVocalToken, ...] = tuple(
    list(ProtoVocalToken)
)


def _proto_vocal_token_rank(token: ProtoVocalToken) -> int:
    return _PROTO_VOCAL_TOKEN_ORDER.index(token)


class CaregiverFeedbackKind(str, Enum):
    """Closed enum of caregiver feedback kinds (Phase 3.31)."""

    ACCEPTED = "accepted"
    IGNORED = "ignored"
    ECHO = "echo"
    CORRECTED = "corrected"
    EXPANDED = "expanded"
    AMBIENT_ONLY = "ambient_only"


_CAREGIVER_FEEDBACK_KIND_VALUES: frozenset[str] = frozenset(
    {k.value for k in CaregiverFeedbackKind}
)


class ProtoSpeechContextKind(str, Enum):
    """Closed enum of context kinds (Phase 3.31)."""

    ABSTRACT_PATTERN = "abstract_pattern"
    WORLDLET = "worldlet"
    REPL = "repl"
    DISPATCH_TRACE = "dispatch_trace"
    REASONING_TRACE = "reasoning_trace"
    LEARNING_EVIDENCE = "learning_evidence"
    ACTIVE_HYPOTHESIS = "active_hypothesis"
    CURRICULUM = "curriculum"
    UNKNOWN = "unknown"


_PROTO_SPEECH_CONTEXT_KIND_VALUES: frozenset[str] = frozenset(
    {c.value for c in ProtoSpeechContextKind}
)


class ProtoUtteranceDisposition(str, Enum):
    """Closed enum of evidence-record dispositions (Phase 3.31)."""

    BABBLE = "babble"
    CANDIDATE = "candidate"
    REINFORCED = "reinforced"
    SUPPRESSED = "suppressed"
    STABLE_SINGLE = "stable_single"
    STABLE_COMBINATION = "stable_combination"
    TRANSFERRED = "transferred"
    REJECTED = "rejected"


_PROTO_UTTERANCE_DISPOSITION_VALUES: frozenset[str] = frozenset(
    {d.value for d in ProtoUtteranceDisposition}
)


class ProtoSpeechDriveKind(str, Enum):
    """Closed enum of drive-stream frame kinds (Phase 3.31)."""

    LOW_EVIDENCE = "low_evidence"
    RECURRENCE_PRESSURE = "recurrence_pressure"
    NOVELTY_PRESSURE = "novelty_pressure"
    TRANSFER_PRESSURE = "transfer_pressure"
    UNRESOLVED_HYPOTHESIS = "unresolved_hypothesis"
    WORLDLET_FEEDBACK_PRESENT = "worldlet_feedback_present"
    REPL_FEEDBACK_PRESENT = "repl_feedback_present"
    CAREGIVER_AMBIENT_PRIME = "caregiver_ambient_prime"
    CAREGIVER_FEEDBACK_PRIME = "caregiver_feedback_prime"
    SUPPRESSION_PRESSURE = "suppression_pressure"
    COMBINATION_PRESSURE = "combination_pressure"
    REFUSAL_GUARD = "refusal_guard"


_PROTO_SPEECH_DRIVE_KIND_VALUES: frozenset[str] = frozenset(
    {k.value for k in ProtoSpeechDriveKind}
)


class ProtoSpeechStatus(str, Enum):
    """Closed enum of per-condition / per-report statuses (Phase 3.31)."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


_PROTO_SPEECH_STATUS_VALUES: frozenset[str] = frozenset(
    {s.value for s in ProtoSpeechStatus}
)


class ProtoSpeechCondition(str, Enum):
    """Closed enum of test conditions (Phase 3.31)."""

    BABBLE_BASELINE = "babble_baseline"
    AMBIENT_IMPRINTING = "ambient_imprinting"
    FEEDBACK_REINFORCEMENT = "feedback_reinforcement"
    CORRECTION_SHAPING = "correction_shaping"
    HOLOPHRASE_TRANSFER = "holophrase_transfer"
    TWO_TOKEN_COMBINATION = "two_token_combination"
    SUPPRESSION = "suppression"
    TURN_TAKING = "turn_taking"
    REFUSAL_PRESERVED = "refusal_preserved"
    DRIVE_STREAM_PRESSURE = "drive_stream_pressure"


_PROTO_SPEECH_CONDITION_VALUES: frozenset[str] = frozenset(
    {c.value for c in ProtoSpeechCondition}
)


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
            f"I-PSPEECH-01 violated: {field} must be a string "
            f"(got {type(value).__name__})"
        )
    if forbid_empty and not value:
        raise ValueError(
            f"I-PSPEECH-01 violated: {field} must be non-empty"
        )
    if value and not value.isprintable():
        raise ValueError(
            f"I-PSPEECH-01 violated: {field} must be printable"
        )
    if len(value) > max_len:
        raise ValueError(
            f"I-PSPEECH-01 violated: {field} length {len(value)} > {max_len}"
        )
    if audit_non_claim:
        term = _has_forbidden_non_claim_term(value)
        if term is not None:
            raise ValueError(
                f"I-PSPEECH-01 violated: {field} contains forbidden non-claim "
                f"term {term!r}"
            )
    return value


def _validate_digest_hex(value: object, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != PROTO_SPEECH_DIGEST_HEX_LEN
    ):
        raise ValueError(
            f"I-PSPEECH-01 violated: {field} must be a 16-char hex string "
            f"(got {value!r})"
        )
    return value


def _zero_digest() -> str:
    return "0" * PROTO_SPEECH_DIGEST_HEX_LEN


def _bounded_excerpt(text: str, *, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 4)] + " ..."


# ---------------------------------------------------------------------------
# Frozen records (Step 2): ProtoUtterance, CaregiverFeedback,
# ProtoSpeechContext.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProtoUtterance:
    """One bounded 1- or 2-token proto-utterance (Phase 3.31).

    The token tuple is drawn from the closed ``ProtoVocalToken``
    inventory. A length-0 ``tokens`` tuple is permitted only for
    the canonical REFUSAL_GUARD sentinel.
    """

    tokens: tuple[ProtoVocalToken, ...]
    text: str
    token_count: int
    reduplicated: bool
    digest_hex16: str

    def __post_init__(self) -> None:
        if not isinstance(self.tokens, tuple):
            raise TypeError(
                "I-PSPEECH-02 violated: ProtoUtterance.tokens must be a tuple"
            )
        if len(self.tokens) > 2:
            raise ValueError(
                "I-PSPEECH-02 violated: ProtoUtterance.tokens length must "
                "be 0, 1, or 2"
            )
        for tok in self.tokens:
            if not isinstance(tok, ProtoVocalToken):
                raise TypeError(
                    "I-PSPEECH-02 violated: every tokens entry must be a "
                    "ProtoVocalToken"
                )
        # text may be empty for the sentinel.
        _validate_bounded_printable(
            self.text,
            field="ProtoUtterance.text",
            max_len=PROTO_SPEECH_TEXT_MAX_LEN,
            forbid_empty=False,
            audit_non_claim=True,
        )
        if not isinstance(self.token_count, int) or isinstance(
            self.token_count, bool
        ):
            raise TypeError(
                "I-PSPEECH-02 violated: token_count must be int"
            )
        if self.token_count != len(self.tokens):
            raise ValueError(
                "I-PSPEECH-02 violated: token_count must equal len(tokens)"
            )
        if self.token_count not in (0, 1, 2):
            raise ValueError(
                "I-PSPEECH-02 violated: token_count must be 0, 1, or 2"
            )
        if not isinstance(self.reduplicated, bool):
            raise TypeError(
                "I-PSPEECH-02 violated: reduplicated must be bool"
            )
        if self.token_count == 2:
            same = self.tokens[0] is self.tokens[1]
            if same != self.reduplicated:
                raise ValueError(
                    "I-PSPEECH-02 violated: reduplicated flag must reflect "
                    "tokens equality for 2-token utterances"
                )
        elif self.reduplicated:
            raise ValueError(
                "I-PSPEECH-02 violated: reduplicated can only be True for "
                "2-token utterances"
            )
        _validate_digest_hex(
            self.digest_hex16, field="ProtoUtterance.digest_hex16"
        )


def _utterance_text(tokens: tuple[ProtoVocalToken, ...]) -> str:
    return " ".join(t.value for t in tokens)


def _utterance_digest(tokens: tuple[ProtoVocalToken, ...]) -> str:
    payload = ("|".join(t.value for t in tokens)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[
        :PROTO_SPEECH_DIGEST_HEX_LEN
    ]


def build_proto_utterance(
    tokens: tuple[ProtoVocalToken, ...],
) -> ProtoUtterance:
    """Construct a bounded ``ProtoUtterance`` from a closed-inventory tuple."""
    if not isinstance(tokens, tuple):
        raise TypeError(
            "I-PSPEECH-02 violated: build_proto_utterance tokens must be a "
            "tuple"
        )
    for tok in tokens:
        if not isinstance(tok, ProtoVocalToken):
            raise TypeError(
                "I-PSPEECH-02 violated: every token must be a ProtoVocalToken"
            )
    text = _utterance_text(tokens)
    digest = _utterance_digest(tokens) if tokens else _zero_digest()
    reduplicated = (
        len(tokens) == 2 and tokens[0] is tokens[1]
    )
    return ProtoUtterance(
        tokens=tokens,
        text=text,
        token_count=len(tokens),
        reduplicated=reduplicated,
        digest_hex16=digest,
    )


#: Sentinel returned by ``select_babble_from_drive_stream`` when a
#: ``REFUSAL_GUARD`` frame is present. Length-0 tokens; the runner
#: takes the canonical refusal path instead of emitting an
#: utterance.
REFUSAL_SENTINEL: ProtoUtterance = ProtoUtterance(
    tokens=(),
    text="",
    token_count=0,
    reduplicated=False,
    digest_hex16=_zero_digest(),
)


@dataclass(frozen=True, slots=True)
class CaregiverFeedback:
    """One bounded caregiver feedback record (Phase 3.31)."""

    kind: CaregiverFeedbackKind
    offered_utterance: Optional[ProtoUtterance]
    ambient_utterance: Optional[ProtoUtterance]
    context_label: str
    evidence_delta: int

    def __post_init__(self) -> None:
        if not isinstance(self.kind, CaregiverFeedbackKind):
            raise TypeError(
                "I-PSPEECH-03 violated: CaregiverFeedback.kind must be a "
                "CaregiverFeedbackKind"
            )
        if self.offered_utterance is not None and not isinstance(
            self.offered_utterance, ProtoUtterance
        ):
            raise TypeError(
                "I-PSPEECH-03 violated: offered_utterance must be a "
                "ProtoUtterance or None"
            )
        if self.ambient_utterance is not None and not isinstance(
            self.ambient_utterance, ProtoUtterance
        ):
            raise TypeError(
                "I-PSPEECH-03 violated: ambient_utterance must be a "
                "ProtoUtterance or None"
            )
        _validate_bounded_printable(
            self.context_label,
            field="CaregiverFeedback.context_label",
            max_len=PROTO_SPEECH_CONTEXT_LABEL_MAX_LEN,
            forbid_empty=True,
            audit_non_claim=True,
        )
        term = _has_forbidden_direct_instruction(self.context_label)
        if term is not None:
            raise ValueError(
                "I-PSPEECH-03 violated: CaregiverFeedback.context_label "
                f"contains forbidden direct-instruction term {term!r}"
            )
        if not isinstance(self.evidence_delta, int) or isinstance(
            self.evidence_delta, bool
        ):
            raise TypeError(
                "I-PSPEECH-03 violated: evidence_delta must be int"
            )
        if abs(self.evidence_delta) > 8:
            raise ValueError(
                "I-PSPEECH-03 violated: evidence_delta out of bound [-8, 8]"
            )


@dataclass(frozen=True, slots=True)
class ProtoSpeechContext:
    """One bounded active-context signature (Phase 3.31)."""

    context_kind: ProtoSpeechContextKind
    abstract_pattern_digest: Optional[str]
    abstract_pattern_shape: Optional[str]
    worldlet_feedback_present: bool
    repl_result_present: bool
    dispatch_trace_digest: Optional[str]
    reasoning_trace_digest: Optional[str]
    learning_evidence_digest: Optional[str]
    active_hypothesis_digest: Optional[str]
    curriculum_digest: Optional[str]
    context_signature: str

    def __post_init__(self) -> None:
        if not isinstance(self.context_kind, ProtoSpeechContextKind):
            raise TypeError(
                "I-PSPEECH-01 violated: context_kind must be a "
                "ProtoSpeechContextKind"
            )
        for name, val in (
            ("abstract_pattern_digest", self.abstract_pattern_digest),
            ("dispatch_trace_digest", self.dispatch_trace_digest),
            ("reasoning_trace_digest", self.reasoning_trace_digest),
            ("learning_evidence_digest", self.learning_evidence_digest),
            ("active_hypothesis_digest", self.active_hypothesis_digest),
            ("curriculum_digest", self.curriculum_digest),
        ):
            if val is None:
                continue
            _validate_digest_hex(val, field=f"ProtoSpeechContext.{name}")
        if self.abstract_pattern_shape is not None:
            _validate_bounded_printable(
                self.abstract_pattern_shape,
                field="ProtoSpeechContext.abstract_pattern_shape",
                max_len=PROTO_SPEECH_EXPLAIN_MAX_LEN,
                forbid_empty=False,
                audit_non_claim=True,
            )
        if not isinstance(self.worldlet_feedback_present, bool):
            raise TypeError(
                "I-PSPEECH-01 violated: worldlet_feedback_present must be bool"
            )
        if not isinstance(self.repl_result_present, bool):
            raise TypeError(
                "I-PSPEECH-01 violated: repl_result_present must be bool"
            )
        _validate_digest_hex(
            self.context_signature,
            field="ProtoSpeechContext.context_signature",
        )


def _context_signature_digest(
    *,
    context_kind: ProtoSpeechContextKind,
    abstract_pattern_digest: Optional[str],
    abstract_pattern_shape: Optional[str],
    worldlet_feedback_present: bool,
    repl_result_present: bool,
    dispatch_trace_digest: Optional[str],
    reasoning_trace_digest: Optional[str],
    learning_evidence_digest: Optional[str],
    active_hypothesis_digest: Optional[str],
    curriculum_digest: Optional[str],
) -> str:
    parts = [
        context_kind.value,
        abstract_pattern_digest or "",
        abstract_pattern_shape or "",
        "1" if worldlet_feedback_present else "0",
        "1" if repl_result_present else "0",
        dispatch_trace_digest or "",
        reasoning_trace_digest or "",
        learning_evidence_digest or "",
        active_hypothesis_digest or "",
        curriculum_digest or "",
    ]
    payload = "|".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[
        :PROTO_SPEECH_DIGEST_HEX_LEN
    ]


def build_proto_speech_context(
    *,
    context_kind: ProtoSpeechContextKind = ProtoSpeechContextKind.ABSTRACT_PATTERN,
    abstract_pattern_digest: Optional[str] = None,
    abstract_pattern_shape: Optional[str] = None,
    worldlet_feedback_present: bool = False,
    repl_result_present: bool = False,
    dispatch_trace_digest: Optional[str] = None,
    reasoning_trace_digest: Optional[str] = None,
    learning_evidence_digest: Optional[str] = None,
    active_hypothesis_digest: Optional[str] = None,
    curriculum_digest: Optional[str] = None,
) -> ProtoSpeechContext:
    """Construct a bounded ``ProtoSpeechContext`` whose signature is closed."""
    signature = _context_signature_digest(
        context_kind=context_kind,
        abstract_pattern_digest=abstract_pattern_digest,
        abstract_pattern_shape=abstract_pattern_shape,
        worldlet_feedback_present=worldlet_feedback_present,
        repl_result_present=repl_result_present,
        dispatch_trace_digest=dispatch_trace_digest,
        reasoning_trace_digest=reasoning_trace_digest,
        learning_evidence_digest=learning_evidence_digest,
        active_hypothesis_digest=active_hypothesis_digest,
        curriculum_digest=curriculum_digest,
    )
    return ProtoSpeechContext(
        context_kind=context_kind,
        abstract_pattern_digest=abstract_pattern_digest,
        abstract_pattern_shape=abstract_pattern_shape,
        worldlet_feedback_present=worldlet_feedback_present,
        repl_result_present=repl_result_present,
        dispatch_trace_digest=dispatch_trace_digest,
        reasoning_trace_digest=reasoning_trace_digest,
        learning_evidence_digest=learning_evidence_digest,
        active_hypothesis_digest=active_hypothesis_digest,
        curriculum_digest=curriculum_digest,
        context_signature=signature,
    )


# ---------------------------------------------------------------------------
# Module-produced strings (audited by the static-audit fixture). Populated
# fully in later steps; the values below cover Step 2 enums.
# ---------------------------------------------------------------------------


MODULE_PRODUCED_STRINGS: tuple[str, ...] = (
    PROTO_SPEECH_BATTERY_VERSION,
    PROTO_SPEECH_DIGEST_PREFIX,
    *(t.value for t in ProtoVocalToken),
    *(k.value for k in CaregiverFeedbackKind),
    *(c.value for c in ProtoSpeechContextKind),
    *(d.value for d in ProtoUtteranceDisposition),
    *(k.value for k in ProtoSpeechDriveKind),
    *(s.value for s in ProtoSpeechStatus),
    *(c.value for c in ProtoSpeechCondition),
)


__all__ = (
    "MODULE_PRODUCED_STRINGS",
    "PROTO_SPEECH_BATTERY_VERSION",
    "PROTO_SPEECH_DIGEST_HEX_LEN",
    "PROTO_SPEECH_EVIDENCE_TABLE_MAX",
    "PROTO_SPEECH_MAX_FRAMES_PER_STREAM",
    "PROTO_SPEECH_MAX_TURNS_PER_CONDITION",
    "PROTO_SPEECH_MAX_TURNS_PER_REPORT",
    "PROTO_SPEECH_SUGGESTED_SET_MAX",
    "PROTO_SPEECH_WEIGHT_HINT_MAX",
    "PROTO_SPEECH_WEIGHT_MAX",
    "PROTO_SPEECH_WEIGHT_MIN",
    "REFUSAL_SENTINEL",
    "STABLE_COMBINATION_THRESHOLD",
    "STABLE_SINGLE_THRESHOLD",
    "SUPPRESS_THRESHOLD",
    "CaregiverFeedback",
    "CaregiverFeedbackKind",
    "ProtoSpeechCondition",
    "ProtoSpeechContext",
    "ProtoSpeechContextKind",
    "ProtoSpeechDriveKind",
    "ProtoSpeechStatus",
    "ProtoUtterance",
    "ProtoUtteranceDisposition",
    "ProtoVocalToken",
    "build_proto_speech_context",
    "build_proto_utterance",
)
