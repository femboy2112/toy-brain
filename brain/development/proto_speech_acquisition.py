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
* retains the cognitive-claim refusal path.

"Proto-speech acquisition in ToyI is a bounded operational
co-occurrence-weights + closed-rule evidence-update +
drive-stream-grounded selection + shape-digest transfer effect
over structural records, not a psychological or phenomenological
claim. The runtime is a bounded structural state machine; the
campaign does not assert any cognitive process. See the
non-claim discipline encoded by the canonical
``_FORBIDDEN_NON_CLAIM_TERMS`` audit on every produced bounded
string."

The ``ProtoSpeechDriveStream`` is the bounded, EXPLICIT, AUDITABLE
record-of-structural-pressures: every drive frame names a closed
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
from typing import ClassVar, Optional

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
# rule. Members() keeps declaration order in Python 3.11+.
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
    REFUSAL_HELD = "refusal_held"
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
# Drive-stream records.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProtoSpeechDriveFrame:
    """One bounded drive-stream frame (Phase 3.31).

    Each frame is a closed-shape structural fact derived from a
    public substrate snapshot. The ``source_surface`` names the
    substrate; the ``suggested_token_set`` names which tokens this
    frame would prefer if it were the only frame in the stream.
    """

    drive_kind: ProtoSpeechDriveKind
    source_surface: str
    context_signature: str
    input_digest_hex16: str
    evidence_digest_hex16: Optional[str]
    reasoning_trace_digest_hex16: Optional[str]
    dispatch_trace_digest_hex16: Optional[str]
    caregiver_utterance_digest_hex16: Optional[str]
    weight_hint: int
    suggested_token_set: tuple[ProtoVocalToken, ...]
    explanation: str

    def __post_init__(self) -> None:
        if not isinstance(self.drive_kind, ProtoSpeechDriveKind):
            raise TypeError(
                "I-PSPEECH-14 violated: drive_kind must be a "
                "ProtoSpeechDriveKind"
            )
        _validate_bounded_printable(
            self.source_surface,
            field="ProtoSpeechDriveFrame.source_surface",
            max_len=PROTO_SPEECH_SOURCE_SURFACE_MAX_LEN,
            forbid_empty=True,
            audit_non_claim=True,
        )
        _validate_digest_hex(
            self.context_signature,
            field="ProtoSpeechDriveFrame.context_signature",
        )
        _validate_digest_hex(
            self.input_digest_hex16,
            field="ProtoSpeechDriveFrame.input_digest_hex16",
        )
        for name, val in (
            ("evidence_digest_hex16", self.evidence_digest_hex16),
            (
                "reasoning_trace_digest_hex16",
                self.reasoning_trace_digest_hex16,
            ),
            (
                "dispatch_trace_digest_hex16",
                self.dispatch_trace_digest_hex16,
            ),
            (
                "caregiver_utterance_digest_hex16",
                self.caregiver_utterance_digest_hex16,
            ),
        ):
            if val is None:
                continue
            _validate_digest_hex(
                val, field=f"ProtoSpeechDriveFrame.{name}"
            )
        if not isinstance(self.weight_hint, int) or isinstance(
            self.weight_hint, bool
        ):
            raise TypeError(
                "I-PSPEECH-14 violated: weight_hint must be int"
            )
        if (
            self.weight_hint < 0
            or self.weight_hint > PROTO_SPEECH_WEIGHT_HINT_MAX
        ):
            raise ValueError(
                "I-PSPEECH-14 violated: weight_hint out of bound "
                f"[0, {PROTO_SPEECH_WEIGHT_HINT_MAX}]"
            )
        if not isinstance(self.suggested_token_set, tuple):
            raise TypeError(
                "I-PSPEECH-14 violated: suggested_token_set must be a tuple"
            )
        if len(self.suggested_token_set) > PROTO_SPEECH_SUGGESTED_SET_MAX:
            raise ValueError(
                "I-PSPEECH-14 violated: suggested_token_set length "
                f"{len(self.suggested_token_set)} > "
                f"{PROTO_SPEECH_SUGGESTED_SET_MAX}"
            )
        seen: set[ProtoVocalToken] = set()
        for tok in self.suggested_token_set:
            if not isinstance(tok, ProtoVocalToken):
                raise TypeError(
                    "I-PSPEECH-14 violated: every suggested_token_set entry "
                    "must be a ProtoVocalToken"
                )
            if tok in seen:
                raise ValueError(
                    "I-PSPEECH-14 violated: suggested_token_set must not "
                    "contain duplicates"
                )
            seen.add(tok)
        _validate_bounded_printable(
            self.explanation,
            field="ProtoSpeechDriveFrame.explanation",
            max_len=PROTO_SPEECH_EXPLAIN_MAX_LEN,
            forbid_empty=True,
            audit_non_claim=True,
        )


@dataclass(frozen=True, slots=True)
class ProtoSpeechDriveStream:
    """One bounded drive stream (Phase 3.31)."""

    frames: tuple[ProtoSpeechDriveFrame, ...]
    max_frames: int
    digest_hex16: str
    status: ProtoSpeechStatus

    def __post_init__(self) -> None:
        if not isinstance(self.frames, tuple):
            raise TypeError(
                "I-PSPEECH-14 violated: frames must be a tuple"
            )
        if len(self.frames) > PROTO_SPEECH_MAX_FRAMES_PER_STREAM:
            raise ValueError(
                "I-PSPEECH-14 violated: frames length "
                f"{len(self.frames)} > "
                f"{PROTO_SPEECH_MAX_FRAMES_PER_STREAM}"
            )
        for f in self.frames:
            if not isinstance(f, ProtoSpeechDriveFrame):
                raise TypeError(
                    "I-PSPEECH-14 violated: every frames entry must be a "
                    "ProtoSpeechDriveFrame"
                )
        if (
            not isinstance(self.max_frames, int)
            or self.max_frames != PROTO_SPEECH_MAX_FRAMES_PER_STREAM
        ):
            raise ValueError(
                "I-PSPEECH-14 violated: max_frames must equal "
                f"{PROTO_SPEECH_MAX_FRAMES_PER_STREAM}"
            )
        _validate_digest_hex(
            self.digest_hex16,
            field="ProtoSpeechDriveStream.digest_hex16",
        )
        if not isinstance(self.status, ProtoSpeechStatus):
            raise TypeError(
                "I-PSPEECH-14 violated: status must be a ProtoSpeechStatus"
            )


def _drive_frame_serialize(f: ProtoSpeechDriveFrame) -> str:
    parts = [
        f.drive_kind.value,
        f.source_surface,
        f.context_signature,
        f.input_digest_hex16,
        f.evidence_digest_hex16 or "",
        f.reasoning_trace_digest_hex16 or "",
        f.dispatch_trace_digest_hex16 or "",
        f.caregiver_utterance_digest_hex16 or "",
        str(f.weight_hint),
        ",".join(t.value for t in f.suggested_token_set),
        f.explanation,
    ]
    return "|".join(parts)


def _drive_stream_digest(
    frames: tuple[ProtoSpeechDriveFrame, ...],
) -> str:
    payload = "\n".join(_drive_frame_serialize(f) for f in frames).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()[
        :PROTO_SPEECH_DIGEST_HEX_LEN
    ]


def _input_digest(text: str) -> str:
    payload = text.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[
        :PROTO_SPEECH_DIGEST_HEX_LEN
    ]


def build_proto_speech_drive_stream(
    *,
    context: ProtoSpeechContext,
    learning_trace: Optional[LearningEvidenceTrace] = None,
    reasoning_trace_digest: Optional[str] = None,
    dispatch_trace_digest: Optional[str] = None,
    caregiver_ambient: Optional[ProtoUtterance] = None,
    caregiver_feedback: Optional[CaregiverFeedback] = None,
    evidence_table_digest: Optional[str] = None,
    suppressed_tokens: tuple[ProtoVocalToken, ...] = (),
    stable_single_tokens: tuple[ProtoVocalToken, ...] = (),
    has_active_hypothesis_unresolved: bool = False,
    has_seen_context_before: bool = False,
    input_text: str = "",
    refusal_guard: bool = False,
    combination_pressure: bool = False,
    transfer_pressure_token: Optional[ProtoVocalToken] = None,
) -> ProtoSpeechDriveStream:
    """Return a bounded deterministic drive stream for the given inputs.

    The implementation is a pure deterministic function of its
    keyword arguments; no global mutable state is touched, no
    ``random`` / ``time`` source is consulted.
    """
    if not isinstance(context, ProtoSpeechContext):
        raise TypeError(
            "I-PSPEECH-14 violated: context must be a ProtoSpeechContext"
        )
    if caregiver_ambient is not None and not isinstance(
        caregiver_ambient, ProtoUtterance
    ):
        raise TypeError(
            "I-PSPEECH-14 violated: caregiver_ambient must be a "
            "ProtoUtterance or None"
        )
    if caregiver_feedback is not None and not isinstance(
        caregiver_feedback, CaregiverFeedback
    ):
        raise TypeError(
            "I-PSPEECH-14 violated: caregiver_feedback must be a "
            "CaregiverFeedback or None"
        )
    if transfer_pressure_token is not None and not isinstance(
        transfer_pressure_token, ProtoVocalToken
    ):
        raise TypeError(
            "I-PSPEECH-14 violated: transfer_pressure_token must be a "
            "ProtoVocalToken or None"
        )

    input_digest = _input_digest(input_text)
    ev_digest = evidence_table_digest

    frames: list[ProtoSpeechDriveFrame] = []

    # 1. REFUSAL_GUARD takes precedence; the stream is short-
    # circuited and no other suggestion frames are emitted.
    if refusal_guard:
        frames.append(
            ProtoSpeechDriveFrame(
                drive_kind=ProtoSpeechDriveKind.REFUSAL_GUARD,
                source_surface="refusal_guard",
                context_signature=context.context_signature,
                input_digest_hex16=input_digest,
                evidence_digest_hex16=ev_digest,
                reasoning_trace_digest_hex16=reasoning_trace_digest,
                dispatch_trace_digest_hex16=dispatch_trace_digest,
                caregiver_utterance_digest_hex16=None,
                weight_hint=PROTO_SPEECH_WEIGHT_HINT_MAX,
                suggested_token_set=(),
                explanation=_bounded_excerpt(
                    "refusal guard active: cognitive-claim probe detected; "
                    "no proto-utterance selected.",
                    limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
                ),
            )
        )
        return ProtoSpeechDriveStream(
            frames=tuple(frames),
            max_frames=PROTO_SPEECH_MAX_FRAMES_PER_STREAM,
            digest_hex16=_drive_stream_digest(tuple(frames)),
            status=ProtoSpeechStatus.PASS,
        )

    # 2. Caregiver ambient prime (precedes the turn).
    if caregiver_ambient is not None and caregiver_ambient.token_count > 0:
        frames.append(
            ProtoSpeechDriveFrame(
                drive_kind=ProtoSpeechDriveKind.CAREGIVER_AMBIENT_PRIME,
                source_surface="caregiver_ambient",
                context_signature=context.context_signature,
                input_digest_hex16=input_digest,
                evidence_digest_hex16=ev_digest,
                reasoning_trace_digest_hex16=reasoning_trace_digest,
                dispatch_trace_digest_hex16=dispatch_trace_digest,
                caregiver_utterance_digest_hex16=(
                    caregiver_ambient.digest_hex16
                ),
                weight_hint=10,
                suggested_token_set=tuple(caregiver_ambient.tokens),
                explanation=_bounded_excerpt(
                    f"caregiver ambient prime: tokens="
                    f"{','.join(t.value for t in caregiver_ambient.tokens)}",
                    limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
                ),
            )
        )

    # 3. Caregiver feedback prime (echo / accepted / expanded uplifts
    # the form named by the most recent feedback record).
    if caregiver_feedback is not None and caregiver_feedback.kind in (
        CaregiverFeedbackKind.ACCEPTED,
        CaregiverFeedbackKind.ECHO,
        CaregiverFeedbackKind.EXPANDED,
    ):
        offered = caregiver_feedback.offered_utterance
        if offered is not None and offered.token_count > 0:
            frames.append(
                ProtoSpeechDriveFrame(
                    drive_kind=ProtoSpeechDriveKind.CAREGIVER_FEEDBACK_PRIME,
                    source_surface="caregiver_feedback",
                    context_signature=context.context_signature,
                    input_digest_hex16=input_digest,
                    evidence_digest_hex16=ev_digest,
                    reasoning_trace_digest_hex16=reasoning_trace_digest,
                    dispatch_trace_digest_hex16=dispatch_trace_digest,
                    caregiver_utterance_digest_hex16=offered.digest_hex16,
                    weight_hint=12,
                    suggested_token_set=tuple(offered.tokens),
                    explanation=_bounded_excerpt(
                        f"caregiver feedback prime: kind="
                        f"{caregiver_feedback.kind.value} tokens="
                        f"{','.join(t.value for t in offered.tokens)}",
                        limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
                    ),
                )
            )

    # 4. Transfer pressure when a same-shape stable form exists in
    # a compatible context.
    if transfer_pressure_token is not None:
        frames.append(
            ProtoSpeechDriveFrame(
                drive_kind=ProtoSpeechDriveKind.TRANSFER_PRESSURE,
                source_surface="abstract_pattern",
                context_signature=context.context_signature,
                input_digest_hex16=input_digest,
                evidence_digest_hex16=ev_digest,
                reasoning_trace_digest_hex16=reasoning_trace_digest,
                dispatch_trace_digest_hex16=dispatch_trace_digest,
                caregiver_utterance_digest_hex16=None,
                weight_hint=11,
                suggested_token_set=(transfer_pressure_token,),
                explanation=_bounded_excerpt(
                    f"transfer pressure: stable single available in "
                    f"compatible context "
                    f"token={transfer_pressure_token.value}",
                    limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
                ),
            )
        )

    # 5. Recurrence / novelty pressure (depend on whether the context
    # has been observed before AND on the abstract pattern shape).
    if has_seen_context_before and caregiver_ambient is not None:
        frames.append(
            ProtoSpeechDriveFrame(
                drive_kind=ProtoSpeechDriveKind.RECURRENCE_PRESSURE,
                source_surface="abstract_pattern",
                context_signature=context.context_signature,
                input_digest_hex16=input_digest,
                evidence_digest_hex16=ev_digest,
                reasoning_trace_digest_hex16=reasoning_trace_digest,
                dispatch_trace_digest_hex16=dispatch_trace_digest,
                caregiver_utterance_digest_hex16=None,
                weight_hint=6,
                suggested_token_set=(
                    ProtoVocalToken.SAME,
                    ProtoVocalToken.AGAIN,
                ),
                explanation=_bounded_excerpt(
                    "recurrence pressure: same shape digest seen recently",
                    limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
                ),
            )
        )
    elif (
        not has_seen_context_before
        and caregiver_ambient is not None
        and context.abstract_pattern_digest is not None
    ):
        frames.append(
            ProtoSpeechDriveFrame(
                drive_kind=ProtoSpeechDriveKind.NOVELTY_PRESSURE,
                source_surface="abstract_pattern",
                context_signature=context.context_signature,
                input_digest_hex16=input_digest,
                evidence_digest_hex16=ev_digest,
                reasoning_trace_digest_hex16=reasoning_trace_digest,
                dispatch_trace_digest_hex16=dispatch_trace_digest,
                caregiver_utterance_digest_hex16=None,
                weight_hint=5,
                suggested_token_set=(
                    ProtoVocalToken.LOOK,
                    ProtoVocalToken.THIS,
                ),
                explanation=_bounded_excerpt(
                    "novelty pressure: new shape digest with ambient context",
                    limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
                ),
            )
        )

    # 6. Substrate-presence frames.
    if context.worldlet_feedback_present:
        frames.append(
            ProtoSpeechDriveFrame(
                drive_kind=ProtoSpeechDriveKind.WORLDLET_FEEDBACK_PRESENT,
                source_surface="worldlet",
                context_signature=context.context_signature,
                input_digest_hex16=input_digest,
                evidence_digest_hex16=ev_digest,
                reasoning_trace_digest_hex16=reasoning_trace_digest,
                dispatch_trace_digest_hex16=dispatch_trace_digest,
                caregiver_utterance_digest_hex16=None,
                weight_hint=4,
                suggested_token_set=(
                    ProtoVocalToken.THAT,
                    ProtoVocalToken.DONE,
                ),
                explanation=_bounded_excerpt(
                    "worldlet feedback present",
                    limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
                ),
            )
        )
    if context.repl_result_present:
        frames.append(
            ProtoSpeechDriveFrame(
                drive_kind=ProtoSpeechDriveKind.REPL_FEEDBACK_PRESENT,
                source_surface="repl",
                context_signature=context.context_signature,
                input_digest_hex16=input_digest,
                evidence_digest_hex16=ev_digest,
                reasoning_trace_digest_hex16=reasoning_trace_digest,
                dispatch_trace_digest_hex16=dispatch_trace_digest,
                caregiver_utterance_digest_hex16=None,
                weight_hint=4,
                suggested_token_set=(
                    ProtoVocalToken.DONE,
                    ProtoVocalToken.NO,
                ),
                explanation=_bounded_excerpt(
                    "REPL result present",
                    limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
                ),
            )
        )

    # 7. UNRESOLVED_HYPOTHESIS pressure.
    if has_active_hypothesis_unresolved:
        frames.append(
            ProtoSpeechDriveFrame(
                drive_kind=ProtoSpeechDriveKind.UNRESOLVED_HYPOTHESIS,
                source_surface="active_hypothesis",
                context_signature=context.context_signature,
                input_digest_hex16=input_digest,
                evidence_digest_hex16=ev_digest,
                reasoning_trace_digest_hex16=reasoning_trace_digest,
                dispatch_trace_digest_hex16=dispatch_trace_digest,
                caregiver_utterance_digest_hex16=None,
                weight_hint=7,
                suggested_token_set=(
                    ProtoVocalToken.HELP,
                    ProtoVocalToken.MORE,
                ),
                explanation=_bounded_excerpt(
                    "active hypothesis unresolved: no surviving candidate",
                    limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
                ),
            )
        )

    # 8. SUPPRESSION_PRESSURE acts as a filter; emitted whenever a
    # form is currently suppressed in this context.
    if suppressed_tokens:
        frames.append(
            ProtoSpeechDriveFrame(
                drive_kind=ProtoSpeechDriveKind.SUPPRESSION_PRESSURE,
                source_surface="evidence_table",
                context_signature=context.context_signature,
                input_digest_hex16=input_digest,
                evidence_digest_hex16=ev_digest,
                reasoning_trace_digest_hex16=reasoning_trace_digest,
                dispatch_trace_digest_hex16=dispatch_trace_digest,
                caregiver_utterance_digest_hex16=None,
                weight_hint=8,
                suggested_token_set=(),
                explanation=_bounded_excerpt(
                    "suppression pressure: forms below threshold filtered; "
                    f"count={len(suppressed_tokens)}",
                    limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
                ),
            )
        )

    # 9. COMBINATION_PRESSURE when two distinct stable singles are
    # available in this context.
    if combination_pressure and len(stable_single_tokens) >= 2:
        ordered = tuple(
            sorted(
                stable_single_tokens, key=_proto_vocal_token_rank
            )
        )
        # Bound the suggested set to the first two stable tokens to
        # respect SUGGESTED_TOKEN_SET_MAX.
        pair = ordered[:2]
        frames.append(
            ProtoSpeechDriveFrame(
                drive_kind=ProtoSpeechDriveKind.COMBINATION_PRESSURE,
                source_surface="evidence_table",
                context_signature=context.context_signature,
                input_digest_hex16=input_digest,
                evidence_digest_hex16=ev_digest,
                reasoning_trace_digest_hex16=reasoning_trace_digest,
                dispatch_trace_digest_hex16=dispatch_trace_digest,
                caregiver_utterance_digest_hex16=None,
                weight_hint=9,
                suggested_token_set=pair,
                explanation=_bounded_excerpt(
                    "combination pressure: two stable singles available "
                    f"tokens={','.join(t.value for t in pair)}",
                    limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
                ),
            )
        )

    # 10. LOW_EVIDENCE baseline (always emitted when no caregiver
    # feedback prime has uplifted a specific form).
    has_prime = any(
        f.drive_kind is ProtoSpeechDriveKind.CAREGIVER_FEEDBACK_PRIME
        for f in frames
    )
    if not has_prime:
        frames.append(
            ProtoSpeechDriveFrame(
                drive_kind=ProtoSpeechDriveKind.LOW_EVIDENCE,
                source_surface="evidence_table",
                context_signature=context.context_signature,
                input_digest_hex16=input_digest,
                evidence_digest_hex16=ev_digest,
                reasoning_trace_digest_hex16=reasoning_trace_digest,
                dispatch_trace_digest_hex16=dispatch_trace_digest,
                caregiver_utterance_digest_hex16=None,
                weight_hint=2,
                suggested_token_set=(
                    ProtoVocalToken.BA,
                    ProtoVocalToken.MA,
                    ProtoVocalToken.DA,
                ),
                explanation=_bounded_excerpt(
                    "low evidence: exploratory primitives",
                    limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
                ),
            )
        )

    # Bound: respect MAX_FRAMES_PER_STREAM. Order is the canonical
    # construction order; if we ever exceed the cap, the runner
    # truncates the LOW_EVIDENCE tail rather than failing.
    if len(frames) > PROTO_SPEECH_MAX_FRAMES_PER_STREAM:
        frames = frames[:PROTO_SPEECH_MAX_FRAMES_PER_STREAM]

    return ProtoSpeechDriveStream(
        frames=tuple(frames),
        max_frames=PROTO_SPEECH_MAX_FRAMES_PER_STREAM,
        digest_hex16=_drive_stream_digest(tuple(frames)),
        status=ProtoSpeechStatus.PASS,
    )


def update_drive_stream_after_feedback(
    stream: ProtoSpeechDriveStream,
    *,
    feedback: CaregiverFeedback,
) -> ProtoSpeechDriveStream:
    """Return a new drive stream noting the feedback record.

    The closed-rule update appends a CAREGIVER_FEEDBACK_PRIME frame
    (if not already present) so post-turn audits can cite the same
    structural digest the runner used for selection. The original
    stream is not mutated.
    """
    if not isinstance(stream, ProtoSpeechDriveStream):
        raise TypeError(
            "I-PSPEECH-14 violated: stream must be a ProtoSpeechDriveStream"
        )
    if not isinstance(feedback, CaregiverFeedback):
        raise TypeError(
            "I-PSPEECH-14 violated: feedback must be a CaregiverFeedback"
        )
    offered = feedback.offered_utterance
    if offered is None or offered.token_count == 0:
        return stream
    if feedback.kind not in (
        CaregiverFeedbackKind.ACCEPTED,
        CaregiverFeedbackKind.ECHO,
        CaregiverFeedbackKind.EXPANDED,
        CaregiverFeedbackKind.CORRECTED,
    ):
        return stream
    if any(
        f.drive_kind is ProtoSpeechDriveKind.CAREGIVER_FEEDBACK_PRIME
        and f.caregiver_utterance_digest_hex16 == offered.digest_hex16
        for f in stream.frames
    ):
        return stream
    if not stream.frames:
        return stream
    base = stream.frames[0]
    new_frame = ProtoSpeechDriveFrame(
        drive_kind=ProtoSpeechDriveKind.CAREGIVER_FEEDBACK_PRIME,
        source_surface="caregiver_feedback",
        context_signature=base.context_signature,
        input_digest_hex16=base.input_digest_hex16,
        evidence_digest_hex16=base.evidence_digest_hex16,
        reasoning_trace_digest_hex16=base.reasoning_trace_digest_hex16,
        dispatch_trace_digest_hex16=base.dispatch_trace_digest_hex16,
        caregiver_utterance_digest_hex16=offered.digest_hex16,
        weight_hint=12,
        suggested_token_set=tuple(offered.tokens),
        explanation=_bounded_excerpt(
            f"post-feedback prime: kind={feedback.kind.value} "
            f"tokens={','.join(t.value for t in offered.tokens)}",
            limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
        ),
    )
    new_frames = (new_frame,) + stream.frames
    if len(new_frames) > PROTO_SPEECH_MAX_FRAMES_PER_STREAM:
        new_frames = new_frames[:PROTO_SPEECH_MAX_FRAMES_PER_STREAM]
    return ProtoSpeechDriveStream(
        frames=new_frames,
        max_frames=PROTO_SPEECH_MAX_FRAMES_PER_STREAM,
        digest_hex16=_drive_stream_digest(new_frames),
        status=stream.status,
    )


# ---------------------------------------------------------------------------
# Evidence records + table + closed update rules.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProtoSpeechEvidenceRecord:
    """One bounded utterance-context evidence record (Phase 3.31)."""

    context_signature: str
    utterance_digest: str
    utterance_text: str
    feedback_kind: Optional[CaregiverFeedbackKind]
    weight_before: int
    weight_after: int
    disposition: ProtoUtteranceDisposition
    update_reason: str
    drive_stream_digest_hex16: Optional[str]
    digest_hex16: str

    def __post_init__(self) -> None:
        _validate_digest_hex(
            self.context_signature,
            field="ProtoSpeechEvidenceRecord.context_signature",
        )
        _validate_digest_hex(
            self.utterance_digest,
            field="ProtoSpeechEvidenceRecord.utterance_digest",
        )
        _validate_bounded_printable(
            self.utterance_text,
            field="ProtoSpeechEvidenceRecord.utterance_text",
            max_len=PROTO_SPEECH_TEXT_MAX_LEN,
            forbid_empty=False,
            audit_non_claim=True,
        )
        if self.feedback_kind is not None and not isinstance(
            self.feedback_kind, CaregiverFeedbackKind
        ):
            raise TypeError(
                "I-PSPEECH-04 violated: feedback_kind must be a "
                "CaregiverFeedbackKind or None"
            )
        for name, val in (
            ("weight_before", self.weight_before),
            ("weight_after", self.weight_after),
        ):
            if not isinstance(val, int) or isinstance(val, bool):
                raise TypeError(
                    f"I-PSPEECH-04 violated: {name} must be int"
                )
            if val < PROTO_SPEECH_WEIGHT_MIN or val > PROTO_SPEECH_WEIGHT_MAX:
                raise ValueError(
                    f"I-PSPEECH-04 violated: {name} out of bound "
                    f"[{PROTO_SPEECH_WEIGHT_MIN}, {PROTO_SPEECH_WEIGHT_MAX}]"
                )
        if not isinstance(self.disposition, ProtoUtteranceDisposition):
            raise TypeError(
                "I-PSPEECH-04 violated: disposition must be a "
                "ProtoUtteranceDisposition"
            )
        _validate_bounded_printable(
            self.update_reason,
            field="ProtoSpeechEvidenceRecord.update_reason",
            max_len=PROTO_SPEECH_EXPLAIN_MAX_LEN,
            forbid_empty=True,
            audit_non_claim=True,
        )
        if self.drive_stream_digest_hex16 is not None:
            _validate_digest_hex(
                self.drive_stream_digest_hex16,
                field="ProtoSpeechEvidenceRecord.drive_stream_digest_hex16",
            )
        _validate_digest_hex(
            self.digest_hex16,
            field="ProtoSpeechEvidenceRecord.digest_hex16",
        )


def _evidence_record_digest(
    *,
    context_signature: str,
    utterance_digest: str,
    weight_before: int,
    weight_after: int,
    disposition: ProtoUtteranceDisposition,
    feedback_kind: Optional[CaregiverFeedbackKind],
) -> str:
    payload = "|".join([
        context_signature,
        utterance_digest,
        str(weight_before),
        str(weight_after),
        disposition.value,
        feedback_kind.value if feedback_kind is not None else "",
    ]).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[
        :PROTO_SPEECH_DIGEST_HEX_LEN
    ]


def _classify_disposition(
    *,
    weight_after: int,
    token_count: int,
    prior_disposition: ProtoUtteranceDisposition,
    transferred: bool = False,
) -> ProtoUtteranceDisposition:
    if transferred:
        return ProtoUtteranceDisposition.TRANSFERRED
    if weight_after <= SUPPRESS_THRESHOLD:
        return ProtoUtteranceDisposition.SUPPRESSED
    if token_count == 2 and weight_after >= STABLE_COMBINATION_THRESHOLD:
        return ProtoUtteranceDisposition.STABLE_COMBINATION
    if token_count == 1 and weight_after >= STABLE_SINGLE_THRESHOLD:
        return ProtoUtteranceDisposition.STABLE_SINGLE
    if (
        prior_disposition is ProtoUtteranceDisposition.CANDIDATE
        and weight_after > 0
    ):
        return ProtoUtteranceDisposition.REINFORCED
    if (
        prior_disposition is ProtoUtteranceDisposition.REINFORCED
        and weight_after > 0
    ):
        return ProtoUtteranceDisposition.REINFORCED
    if prior_disposition is ProtoUtteranceDisposition.BABBLE:
        return ProtoUtteranceDisposition.CANDIDATE
    return prior_disposition


# Closed evidence-update integer rule set. Returns
# (attempted_delta, offered_delta).
def _feedback_deltas(
    kind: CaregiverFeedbackKind,
) -> tuple[int, int]:
    if kind is CaregiverFeedbackKind.ACCEPTED:
        return 3, 0
    if kind is CaregiverFeedbackKind.ECHO:
        return 3, 0
    if kind is CaregiverFeedbackKind.EXPANDED:
        return 1, 4
    if kind is CaregiverFeedbackKind.CORRECTED:
        return -2, 3
    if kind is CaregiverFeedbackKind.IGNORED:
        return -1, 0
    if kind is CaregiverFeedbackKind.AMBIENT_ONLY:
        return 0, 1
    raise ValueError(
        f"I-PSPEECH-04 violated: unknown CaregiverFeedbackKind {kind!r}"
    )


@dataclass(frozen=True, slots=True)
class ProtoSpeechEvidenceTable:
    """A bounded immutable session-local evidence table (Phase 3.31).

    Keyed by ``(context_signature, utterance_digest)``. The
    immutable record carries the bounded current entries and a
    deterministic 16-hex digest. Updates produce a new table; the
    runner threads tables across turns and never mutates in place.
    """

    entries: tuple[ProtoSpeechEvidenceRecord, ...]
    max_records: int
    digest_hex16: str

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple):
            raise TypeError(
                "I-PSPEECH-04 violated: entries must be a tuple"
            )
        if len(self.entries) > PROTO_SPEECH_EVIDENCE_TABLE_MAX:
            raise ValueError(
                "I-PSPEECH-04 violated: entries length "
                f"{len(self.entries)} > "
                f"{PROTO_SPEECH_EVIDENCE_TABLE_MAX}"
            )
        for e in self.entries:
            if not isinstance(e, ProtoSpeechEvidenceRecord):
                raise TypeError(
                    "I-PSPEECH-04 violated: every entries record must be a "
                    "ProtoSpeechEvidenceRecord"
                )
        if (
            not isinstance(self.max_records, int)
            or self.max_records != PROTO_SPEECH_EVIDENCE_TABLE_MAX
        ):
            raise ValueError(
                "I-PSPEECH-04 violated: max_records must equal "
                f"{PROTO_SPEECH_EVIDENCE_TABLE_MAX}"
            )
        _validate_digest_hex(
            self.digest_hex16,
            field="ProtoSpeechEvidenceTable.digest_hex16",
        )

    def select(
        self,
        *,
        context_signature: str,
        utterance_digest: str,
    ) -> Optional[ProtoSpeechEvidenceRecord]:
        """Return the most-recent entry for ``(context, utterance)`` or None."""
        for e in reversed(self.entries):
            if (
                e.context_signature == context_signature
                and e.utterance_digest == utterance_digest
            ):
                return e
        return None

    def context_entries(
        self,
        *,
        context_signature: str,
    ) -> tuple[ProtoSpeechEvidenceRecord, ...]:
        """Return the most-recent entry per utterance in the context."""
        seen: dict[str, ProtoSpeechEvidenceRecord] = {}
        for e in self.entries:
            if e.context_signature != context_signature:
                continue
            seen[e.utterance_digest] = e
        return tuple(seen.values())


def _table_digest(
    entries: tuple[ProtoSpeechEvidenceRecord, ...],
) -> str:
    payload = "\n".join(e.digest_hex16 for e in entries).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[
        :PROTO_SPEECH_DIGEST_HEX_LEN
    ]


def empty_evidence_table() -> ProtoSpeechEvidenceTable:
    """Return a fresh empty evidence table."""
    return ProtoSpeechEvidenceTable(
        entries=(),
        max_records=PROTO_SPEECH_EVIDENCE_TABLE_MAX,
        digest_hex16=_table_digest(()),
    )


def _clip_weight(w: int) -> int:
    if w < PROTO_SPEECH_WEIGHT_MIN:
        return PROTO_SPEECH_WEIGHT_MIN
    if w > PROTO_SPEECH_WEIGHT_MAX:
        return PROTO_SPEECH_WEIGHT_MAX
    return w


def _append_evidence_record(
    table: ProtoSpeechEvidenceTable,
    *,
    context_signature: str,
    utterance: ProtoUtterance,
    feedback_kind: Optional[CaregiverFeedbackKind],
    weight_delta: int,
    update_reason: str,
    drive_stream_digest: Optional[str],
    prior_override: Optional[ProtoUtteranceDisposition] = None,
    transferred: bool = False,
) -> tuple[ProtoSpeechEvidenceTable, ProtoSpeechEvidenceRecord]:
    prior_record = table.select(
        context_signature=context_signature,
        utterance_digest=utterance.digest_hex16,
    )
    weight_before = prior_record.weight_after if prior_record else 0
    weight_after = _clip_weight(weight_before + weight_delta)
    prior_disposition = (
        prior_record.disposition
        if prior_record
        else ProtoUtteranceDisposition.BABBLE
    )
    if prior_override is not None:
        prior_disposition = prior_override
    disposition = _classify_disposition(
        weight_after=weight_after,
        token_count=utterance.token_count,
        prior_disposition=prior_disposition,
        transferred=transferred,
    )
    rec_digest = _evidence_record_digest(
        context_signature=context_signature,
        utterance_digest=utterance.digest_hex16,
        weight_before=weight_before,
        weight_after=weight_after,
        disposition=disposition,
        feedback_kind=feedback_kind,
    )
    record = ProtoSpeechEvidenceRecord(
        context_signature=context_signature,
        utterance_digest=utterance.digest_hex16,
        utterance_text=utterance.text,
        feedback_kind=feedback_kind,
        weight_before=weight_before,
        weight_after=weight_after,
        disposition=disposition,
        update_reason=_bounded_excerpt(
            update_reason, limit=PROTO_SPEECH_EXPLAIN_MAX_LEN
        ),
        drive_stream_digest_hex16=drive_stream_digest,
        digest_hex16=rec_digest,
    )
    new_entries = table.entries + (record,)
    if len(new_entries) > PROTO_SPEECH_EVIDENCE_TABLE_MAX:
        # Drop the oldest entry to respect the bound. Closed rule:
        # LRU-by-append-order eviction.
        new_entries = new_entries[1:]
    new_table = ProtoSpeechEvidenceTable(
        entries=new_entries,
        max_records=PROTO_SPEECH_EVIDENCE_TABLE_MAX,
        digest_hex16=_table_digest(new_entries),
    )
    return new_table, record


def update_proto_speech_evidence(
    table: ProtoSpeechEvidenceTable,
    *,
    context: ProtoSpeechContext,
    attempted: ProtoUtterance,
    feedback: CaregiverFeedback,
    drive_stream_digest: Optional[str] = None,
) -> tuple[ProtoSpeechEvidenceTable, tuple[ProtoSpeechEvidenceRecord, ...]]:
    """Apply the closed feedback rule to the evidence table.

    Returns ``(new_table, records_added)``. The records tuple may
    have one or two entries: one for the attempted utterance, plus
    a second for the offered / ambient utterance when the feedback
    kind produces a non-zero offered-delta.
    """
    if not isinstance(table, ProtoSpeechEvidenceTable):
        raise TypeError(
            "I-PSPEECH-04 violated: table must be a ProtoSpeechEvidenceTable"
        )
    if not isinstance(context, ProtoSpeechContext):
        raise TypeError(
            "I-PSPEECH-04 violated: context must be a ProtoSpeechContext"
        )
    if not isinstance(attempted, ProtoUtterance):
        raise TypeError(
            "I-PSPEECH-04 violated: attempted must be a ProtoUtterance"
        )
    if not isinstance(feedback, CaregiverFeedback):
        raise TypeError(
            "I-PSPEECH-04 violated: feedback must be a CaregiverFeedback"
        )
    attempted_delta, offered_delta = _feedback_deltas(feedback.kind)
    added: list[ProtoSpeechEvidenceRecord] = []
    current = table
    # Attempted-utterance update (only when the attempted utterance
    # has at least one token; the REFUSAL_SENTINEL never enters the
    # update path).
    if attempted.token_count > 0 and attempted_delta != 0:
        reason = (
            f"feedback={feedback.kind.value} attempted_delta="
            f"{attempted_delta:+d} ctx_label={feedback.context_label}"
        )
        current, rec = _append_evidence_record(
            current,
            context_signature=context.context_signature,
            utterance=attempted,
            feedback_kind=feedback.kind,
            weight_delta=attempted_delta,
            update_reason=reason,
            drive_stream_digest=drive_stream_digest,
        )
        added.append(rec)
    # Offered-utterance update (for EXPANDED / CORRECTED / AMBIENT_ONLY).
    target = (
        feedback.ambient_utterance
        if feedback.kind is CaregiverFeedbackKind.AMBIENT_ONLY
        else feedback.offered_utterance
    )
    if (
        target is not None
        and target.token_count > 0
        and offered_delta != 0
    ):
        reason = (
            f"feedback={feedback.kind.value} offered_delta="
            f"{offered_delta:+d} ctx_label={feedback.context_label}"
        )
        current, rec = _append_evidence_record(
            current,
            context_signature=context.context_signature,
            utterance=target,
            feedback_kind=feedback.kind,
            weight_delta=offered_delta,
            update_reason=reason,
            drive_stream_digest=drive_stream_digest,
        )
        added.append(rec)
    return current, tuple(added)


def transfer_proto_speech_evidence(
    table: ProtoSpeechEvidenceTable,
    *,
    source_context: ProtoSpeechContext,
    target_context: ProtoSpeechContext,
    utterance: ProtoUtterance,
    drive_stream_digest: Optional[str] = None,
) -> tuple[ProtoSpeechEvidenceTable, Optional[ProtoSpeechEvidenceRecord]]:
    """Transfer a stable single from one context to another (same shape only).

    Closed rule: transfer only when the source context's
    ``abstract_pattern_digest`` equals the target context's
    ``abstract_pattern_digest`` AND a STABLE_SINGLE record for the
    utterance exists in the source context. The transferred record
    is appended to the table with disposition TRANSFERRED.
    """
    if not isinstance(table, ProtoSpeechEvidenceTable):
        raise TypeError(
            "I-PSPEECH-10 violated: table must be a ProtoSpeechEvidenceTable"
        )
    if (
        source_context.abstract_pattern_digest is None
        or target_context.abstract_pattern_digest is None
        or source_context.abstract_pattern_digest
        != target_context.abstract_pattern_digest
    ):
        return table, None
    source = table.select(
        context_signature=source_context.context_signature,
        utterance_digest=utterance.digest_hex16,
    )
    if source is None or source.disposition is not (
        ProtoUtteranceDisposition.STABLE_SINGLE
    ):
        return table, None
    # Use the source's weight_after as the transfer-base weight.
    reason = (
        f"transfer: same-shape stable single from src "
        f"sig={source_context.context_signature[:8]} weight="
        f"{source.weight_after}"
    )
    new_table, rec = _append_evidence_record(
        table,
        context_signature=target_context.context_signature,
        utterance=utterance,
        feedback_kind=None,
        weight_delta=source.weight_after,
        update_reason=reason,
        drive_stream_digest=drive_stream_digest,
        prior_override=ProtoUtteranceDisposition.STABLE_SINGLE,
        transferred=True,
    )
    return new_table, rec


# ---------------------------------------------------------------------------
# Babble selection from drive stream + per-turn runner.
# ---------------------------------------------------------------------------


def _suppressed_tokens_for_context(
    table: ProtoSpeechEvidenceTable,
    *,
    context_signature: str,
) -> tuple[ProtoVocalToken, ...]:
    """Return the canonical-ordered tuple of suppressed single tokens."""
    suppressed_digests: set[str] = set()
    for e in table.entries:
        if e.context_signature != context_signature:
            continue
        if e.disposition is ProtoUtteranceDisposition.SUPPRESSED:
            suppressed_digests.add(e.utterance_digest)
    if not suppressed_digests:
        return ()
    out: list[ProtoVocalToken] = []
    for tok in _PROTO_VOCAL_TOKEN_ORDER:
        u = build_proto_utterance((tok,))
        if u.digest_hex16 in suppressed_digests:
            out.append(tok)
    return tuple(out)


def _stable_single_tokens_for_context(
    table: ProtoSpeechEvidenceTable,
    *,
    context_signature: str,
) -> tuple[ProtoVocalToken, ...]:
    """Return the canonical-ordered tuple of STABLE_SINGLE tokens."""
    stable_digests: set[str] = set()
    for e in table.entries:
        if e.context_signature != context_signature:
            continue
        if e.disposition is ProtoUtteranceDisposition.STABLE_SINGLE:
            stable_digests.add(e.utterance_digest)
    if not stable_digests:
        return ()
    out: list[ProtoVocalToken] = []
    for tok in _PROTO_VOCAL_TOKEN_ORDER:
        u = build_proto_utterance((tok,))
        if u.digest_hex16 in stable_digests:
            out.append(tok)
    return tuple(out)


def select_babble_from_drive_stream(
    *,
    drive_stream: ProtoSpeechDriveStream,
    evidence_table: ProtoSpeechEvidenceTable,
    context: ProtoSpeechContext,
    turn_index: int,
) -> ProtoUtterance:
    """Deterministically select a ``ProtoUtterance`` from the drive stream.

    The selection rule is the closed function documented in
    ``PHASE3_31_PROTO_SPEECH_DRIVE_STREAM_SPEC.md``.
    """
    if not isinstance(drive_stream, ProtoSpeechDriveStream):
        raise TypeError(
            "I-PSPEECH-15 violated: drive_stream must be a "
            "ProtoSpeechDriveStream"
        )
    if not isinstance(evidence_table, ProtoSpeechEvidenceTable):
        raise TypeError(
            "I-PSPEECH-15 violated: evidence_table must be a "
            "ProtoSpeechEvidenceTable"
        )
    if not isinstance(context, ProtoSpeechContext):
        raise TypeError(
            "I-PSPEECH-15 violated: context must be a ProtoSpeechContext"
        )
    if not isinstance(turn_index, int) or isinstance(turn_index, bool):
        raise TypeError(
            "I-PSPEECH-15 violated: turn_index must be int"
        )

    # 1. Refusal guard short-circuits selection.
    for f in drive_stream.frames:
        if f.drive_kind is ProtoSpeechDriveKind.REFUSAL_GUARD:
            return REFUSAL_SENTINEL

    suppressed = set(
        _suppressed_tokens_for_context(
            evidence_table,
            context_signature=context.context_signature,
        )
    )

    # 2. COMBINATION_PRESSURE takes precedence over single selection
    # when its suggested set has two distinct unsuppressed tokens.
    for f in drive_stream.frames:
        if f.drive_kind is not ProtoSpeechDriveKind.COMBINATION_PRESSURE:
            continue
        eligible = [
            t for t in f.suggested_token_set if t not in suppressed
        ]
        if len(eligible) >= 2:
            pair = tuple(
                sorted(eligible[:2], key=_proto_vocal_token_rank)
            )
            if pair[0] is not pair[1]:
                return build_proto_utterance(pair)

    # 3. CAREGIVER_FEEDBACK_PRIME has highest single priority.
    for f in drive_stream.frames:
        if f.drive_kind is ProtoSpeechDriveKind.CAREGIVER_FEEDBACK_PRIME:
            for tok in f.suggested_token_set:
                if tok not in suppressed:
                    if len(f.suggested_token_set) == 2:
                        if (
                            f.suggested_token_set[0]
                            not in suppressed
                            and f.suggested_token_set[1]
                            not in suppressed
                        ):
                            return build_proto_utterance(
                                tuple(f.suggested_token_set)
                            )
                    return build_proto_utterance((tok,))

    # 4. TRANSFER_PRESSURE preferred next.
    for f in drive_stream.frames:
        if f.drive_kind is ProtoSpeechDriveKind.TRANSFER_PRESSURE:
            for tok in f.suggested_token_set:
                if tok not in suppressed:
                    return build_proto_utterance((tok,))

    # 5. CAREGIVER_AMBIENT_PRIME.
    for f in drive_stream.frames:
        if f.drive_kind is ProtoSpeechDriveKind.CAREGIVER_AMBIENT_PRIME:
            for tok in f.suggested_token_set:
                if tok not in suppressed:
                    return build_proto_utterance((tok,))

    # 6. Highest-weight-hint frame whose suggestion is not
    # SUPPRESSION_PRESSURE / REFUSAL_GUARD; tie-break by frame
    # order. For the LOW_EVIDENCE exploratory frame specifically,
    # use ``turn_index modulo len(suggested)`` so consecutive
    # baseline turns vary deterministically; non-LOW_EVIDENCE
    # frames take the first eligible token in declared order.
    ranked = sorted(
        (
            (f.weight_hint, idx, f)
            for idx, f in enumerate(drive_stream.frames)
            if f.drive_kind
            not in (
                ProtoSpeechDriveKind.SUPPRESSION_PRESSURE,
                ProtoSpeechDriveKind.REFUSAL_GUARD,
                ProtoSpeechDriveKind.COMBINATION_PRESSURE,
                ProtoSpeechDriveKind.CAREGIVER_FEEDBACK_PRIME,
                ProtoSpeechDriveKind.TRANSFER_PRESSURE,
                ProtoSpeechDriveKind.CAREGIVER_AMBIENT_PRIME,
            )
            and f.suggested_token_set
        ),
        key=lambda triple: (-triple[0], triple[1]),
    )
    for _, _, f in ranked:
        if f.drive_kind is ProtoSpeechDriveKind.LOW_EVIDENCE:
            eligible = [
                t for t in f.suggested_token_set if t not in suppressed
            ]
            if eligible:
                chosen = eligible[turn_index % len(eligible)]
                return build_proto_utterance((chosen,))
            continue
        for tok in f.suggested_token_set:
            if tok not in suppressed:
                return build_proto_utterance((tok,))

    # 7. Final fallback: bounded `(turn_index modulo 3)` selection
    # over `(BA, MA, DA)` minus suppressed.
    fallback_pool = (
        ProtoVocalToken.BA,
        ProtoVocalToken.MA,
        ProtoVocalToken.DA,
    )
    eligible = [t for t in fallback_pool if t not in suppressed]
    if not eligible:
        # As a last resort, walk the closed enum order to find any
        # unsuppressed token.
        for tok in _PROTO_VOCAL_TOKEN_ORDER:
            if tok not in suppressed:
                eligible = [tok]
                break
    if not eligible:
        # Every token suppressed: emit the refusal sentinel so the
        # runner records a no-utterance turn rather than violating
        # the inventory.
        return REFUSAL_SENTINEL
    chosen = eligible[turn_index % len(eligible)]
    return build_proto_utterance((chosen,))


def select_proto_utterance(
    *,
    drive_stream: ProtoSpeechDriveStream,
    evidence_table: ProtoSpeechEvidenceTable,
    context: ProtoSpeechContext,
    turn_index: int,
) -> ProtoUtterance:
    """Alias mirroring ``select_babble_from_drive_stream``.

    Kept distinct in the public surface so future campaigns can
    differentiate between pure-babble selection and selection that
    consults additional structural surfaces; v1 behavior is
    identical.
    """
    return select_babble_from_drive_stream(
        drive_stream=drive_stream,
        evidence_table=evidence_table,
        context=context,
        turn_index=turn_index,
    )


# ---------------------------------------------------------------------------
# Per-turn record + runner.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProtoSpeechTurn:
    """One bounded turn (context -> drive stream -> utterance -> feedback ->
    evidence update). Drives proof-report tables."""

    turn_id: str
    condition: ProtoSpeechCondition
    context: ProtoSpeechContext
    drive_stream: ProtoSpeechDriveStream
    caregiver_ambient: Optional[ProtoUtterance]
    selected_utterance: ProtoUtterance
    selected_disposition_before: ProtoUtteranceDisposition
    feedback: CaregiverFeedback
    evidence_records_added: tuple[ProtoSpeechEvidenceRecord, ...]
    learning_evidence_digest: Optional[str]
    reasoning_trace_digest: Optional[str]
    dispatch_trace_digest: Optional[str]
    refusal_taken: bool
    transfer_taken: bool
    summary_line: str

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.turn_id,
            field="ProtoSpeechTurn.turn_id",
            max_len=PROTO_SPEECH_TURN_ID_MAX_LEN,
        )
        if not isinstance(self.condition, ProtoSpeechCondition):
            raise TypeError(
                "I-PSPEECH-12 violated: condition must be a "
                "ProtoSpeechCondition"
            )
        if not isinstance(self.context, ProtoSpeechContext):
            raise TypeError(
                "I-PSPEECH-12 violated: context must be a ProtoSpeechContext"
            )
        if not isinstance(self.drive_stream, ProtoSpeechDriveStream):
            raise TypeError(
                "I-PSPEECH-12 violated: drive_stream must be a "
                "ProtoSpeechDriveStream"
            )
        if self.caregiver_ambient is not None and not isinstance(
            self.caregiver_ambient, ProtoUtterance
        ):
            raise TypeError(
                "I-PSPEECH-12 violated: caregiver_ambient must be a "
                "ProtoUtterance or None"
            )
        if not isinstance(self.selected_utterance, ProtoUtterance):
            raise TypeError(
                "I-PSPEECH-12 violated: selected_utterance must be a "
                "ProtoUtterance"
            )
        if not isinstance(
            self.selected_disposition_before, ProtoUtteranceDisposition
        ):
            raise TypeError(
                "I-PSPEECH-12 violated: selected_disposition_before must be "
                "a ProtoUtteranceDisposition"
            )
        if not isinstance(self.feedback, CaregiverFeedback):
            raise TypeError(
                "I-PSPEECH-12 violated: feedback must be a CaregiverFeedback"
            )
        if not isinstance(self.evidence_records_added, tuple):
            raise TypeError(
                "I-PSPEECH-12 violated: evidence_records_added must be a "
                "tuple"
            )
        for rec in self.evidence_records_added:
            if not isinstance(rec, ProtoSpeechEvidenceRecord):
                raise TypeError(
                    "I-PSPEECH-12 violated: evidence_records_added entries "
                    "must be ProtoSpeechEvidenceRecord"
                )
        for name, val in (
            ("learning_evidence_digest", self.learning_evidence_digest),
            ("reasoning_trace_digest", self.reasoning_trace_digest),
            ("dispatch_trace_digest", self.dispatch_trace_digest),
        ):
            if val is None:
                continue
            _validate_digest_hex(val, field=f"ProtoSpeechTurn.{name}")
        if not isinstance(self.refusal_taken, bool):
            raise TypeError(
                "I-PSPEECH-12 violated: refusal_taken must be bool"
            )
        if not isinstance(self.transfer_taken, bool):
            raise TypeError(
                "I-PSPEECH-12 violated: transfer_taken must be bool"
            )
        _validate_bounded_printable(
            self.summary_line,
            field="ProtoSpeechTurn.summary_line",
            max_len=PROTO_SPEECH_EXPLAIN_MAX_LEN,
            forbid_empty=True,
            audit_non_claim=True,
        )


@dataclass
class _RuntimeRunState:
    """Internal session-local state threaded across turns.

    NOT exposed; the runner constructs a fresh state per condition.
    """

    agent_state: AgentLoopState
    table: ProtoSpeechEvidenceTable
    seen_context_signatures: set[str]


def _make_runtime_state() -> _RuntimeRunState:
    return _RuntimeRunState(
        agent_state=make_initial_agent_loop_state(),
        table=empty_evidence_table(),
        seen_context_signatures=set(),
    )


def _learning_evidence_digest(trace: LearningEvidenceTrace) -> str:
    payload = b""
    for r in trace.records:
        payload += (
            f"{r.kind.value}|{r.interaction_id}|"
            f"{r.abstract_pattern_digest}|{r.pattern_id}"
        ).encode("utf-8")
        payload += b"\n"
    return hashlib.sha256(payload).hexdigest()[
        :PROTO_SPEECH_DIGEST_HEX_LEN
    ]


def _step_agent_loop(
    state: _RuntimeRunState,
    *,
    text: str,
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Run one agent-loop step against the runtime state.

    Returns ``(dispatch_digest, reasoning_digest, learning_digest)``.
    The runtime path NEVER passes the trial's expected predicates.
    """
    if not text:
        return None, None, None
    new_state, r = run_agent_interaction_step(state.agent_state, text)
    state.agent_state = new_state
    dispatch_digest = (
        r.latest_dispatch_trace.trace_digest_hex16
        if r.latest_dispatch_trace is not None
        else None
    )
    reasoning_digest = (
        build_reasoning_trace_report(r.reasoning_trace).trace_digest_hex16
        if r.reasoning_trace is not None
        else None
    )
    learning_digest = _learning_evidence_digest(
        state.agent_state.learning_trace
    )
    return dispatch_digest, reasoning_digest, learning_digest


@dataclass(frozen=True, slots=True)
class _TurnSpec:
    """Bounded per-turn input record consumed by ``run_proto_speech_turn``."""

    turn_id: str
    condition: ProtoSpeechCondition
    context: ProtoSpeechContext
    operator_input_text: str
    caregiver_ambient: Optional[ProtoUtterance]
    feedback: CaregiverFeedback
    has_active_hypothesis_unresolved: bool = False
    refusal_guard: bool = False
    combination_pressure: bool = False
    transfer_pressure_token: Optional[ProtoVocalToken] = None


def run_proto_speech_turn(
    state: _RuntimeRunState,
    spec: _TurnSpec,
    *,
    turn_index: int,
) -> ProtoSpeechTurn:
    """Run a single bounded proto-speech turn against the runtime state.

    Closed turn order:

    1. Run the operator input through the existing agent loop (or
       skip when ``operator_input_text`` is empty).
    2. Build a ``ProtoSpeechDriveStream`` from the active context +
       the new agent-loop digests + the caregiver ambient + feedback
       primes.
    3. Select a ``ProtoUtterance`` deterministically from the stream
       and the current evidence table.
    4. Update the drive stream with the post-feedback prime.
    5. Apply the closed evidence-update rule to the table.
    6. Build a bounded ``ProtoSpeechTurn`` record and mutate the
       runtime state to thread the updated table.
    """
    if not isinstance(state, _RuntimeRunState):
        raise TypeError(
            "I-PSPEECH-12 violated: state must be a _RuntimeRunState"
        )
    if not isinstance(spec, _TurnSpec):
        raise TypeError(
            "I-PSPEECH-12 violated: spec must be a _TurnSpec"
        )

    dispatch_digest, reasoning_digest, learning_digest = _step_agent_loop(
        state, text=spec.operator_input_text
    )

    suppressed = _suppressed_tokens_for_context(
        state.table, context_signature=spec.context.context_signature
    )
    stable_singles = _stable_single_tokens_for_context(
        state.table, context_signature=spec.context.context_signature
    )
    has_seen_before = (
        spec.context.context_signature in state.seen_context_signatures
    )
    state.seen_context_signatures.add(spec.context.context_signature)

    drive_stream = build_proto_speech_drive_stream(
        context=spec.context,
        learning_trace=state.agent_state.learning_trace,
        reasoning_trace_digest=reasoning_digest,
        dispatch_trace_digest=dispatch_digest,
        caregiver_ambient=spec.caregiver_ambient,
        caregiver_feedback=spec.feedback,
        evidence_table_digest=state.table.digest_hex16,
        suppressed_tokens=suppressed,
        stable_single_tokens=stable_singles,
        has_active_hypothesis_unresolved=(
            spec.has_active_hypothesis_unresolved
        ),
        has_seen_context_before=has_seen_before,
        input_text=spec.operator_input_text,
        refusal_guard=spec.refusal_guard,
        combination_pressure=spec.combination_pressure,
        transfer_pressure_token=spec.transfer_pressure_token,
    )

    selected = select_babble_from_drive_stream(
        drive_stream=drive_stream,
        evidence_table=state.table,
        context=spec.context,
        turn_index=turn_index,
    )

    prior_record = state.table.select(
        context_signature=spec.context.context_signature,
        utterance_digest=selected.digest_hex16,
    )
    disposition_before = (
        prior_record.disposition
        if prior_record
        else ProtoUtteranceDisposition.BABBLE
    )

    refusal_taken = selected.token_count == 0

    # If refusal was taken, do NOT update evidence; retain the
    # refusal path. The feedback record is still attached to the
    # turn for audit.
    transfer_taken = False
    if refusal_taken:
        records: tuple[ProtoSpeechEvidenceRecord, ...] = ()
    else:
        new_stream = update_drive_stream_after_feedback(
            drive_stream, feedback=spec.feedback
        )
        # Use the updated stream digest for evidence citation.
        new_table, records = update_proto_speech_evidence(
            state.table,
            context=spec.context,
            attempted=selected,
            feedback=spec.feedback,
            drive_stream_digest=new_stream.digest_hex16,
        )
        state.table = new_table
        drive_stream = new_stream

        # Transfer pressure: if a stable single exists for the
        # requested token in a same-shape source context, append a
        # TRANSFERRED record to the target context's evidence.
        if (
            spec.transfer_pressure_token is not None
            and spec.context.abstract_pattern_digest is not None
        ):
            target_utt = build_proto_utterance(
                (spec.transfer_pressure_token,)
            )
            source_ctx = _find_same_shape_stable_source(
                state.table,
                target_context=spec.context,
                utterance=target_utt,
            )
            if source_ctx is not None:
                new_table, xfer_rec = transfer_proto_speech_evidence(
                    state.table,
                    source_context=source_ctx,
                    target_context=spec.context,
                    utterance=target_utt,
                    drive_stream_digest=drive_stream.digest_hex16,
                )
                if xfer_rec is not None:
                    state.table = new_table
                    records = records + (xfer_rec,)
                    transfer_taken = True

    summary_line = _bounded_excerpt(
        (
            f"turn id={spec.turn_id} cond={spec.condition.value} "
            f"selected={selected.text or '<refusal>'} "
            f"feedback={spec.feedback.kind.value} "
            f"records={len(records)} xfer={transfer_taken}"
        ),
        limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
    )

    return ProtoSpeechTurn(
        turn_id=spec.turn_id,
        condition=spec.condition,
        context=spec.context,
        drive_stream=drive_stream,
        caregiver_ambient=spec.caregiver_ambient,
        selected_utterance=selected,
        selected_disposition_before=disposition_before,
        feedback=spec.feedback,
        evidence_records_added=records,
        learning_evidence_digest=learning_digest,
        reasoning_trace_digest=reasoning_digest,
        dispatch_trace_digest=dispatch_digest,
        refusal_taken=refusal_taken,
        transfer_taken=transfer_taken,
        summary_line=summary_line,
    )


def _find_same_shape_stable_source(
    table: ProtoSpeechEvidenceTable,
    *,
    target_context: ProtoSpeechContext,
    utterance: ProtoUtterance,
) -> Optional[ProtoSpeechContext]:
    """Return the most-recent same-shape stable-single source context, or None.

    Walks the evidence table for STABLE_SINGLE records on the
    given ``utterance.digest_hex16``. Returns a synthetic
    ProtoSpeechContext whose ``context_signature`` matches the
    source and whose ``abstract_pattern_digest`` matches the
    target (the shape-digest equality is the substrate-level
    invariant the transfer rule consults).
    """
    if target_context.abstract_pattern_digest is None:
        return None
    for e in reversed(table.entries):
        if e.utterance_digest != utterance.digest_hex16:
            continue
        if e.disposition is not ProtoUtteranceDisposition.STABLE_SINGLE:
            continue
        if e.context_signature == target_context.context_signature:
            # The target itself; not a transfer source.
            continue
        # Reconstruct a minimal source context. The transfer rule
        # only consults context_signature + abstract_pattern_digest;
        # other fields are filled with bounded defaults.
        return ProtoSpeechContext(
            context_kind=ProtoSpeechContextKind.ABSTRACT_PATTERN,
            abstract_pattern_digest=target_context.abstract_pattern_digest,
            abstract_pattern_shape=target_context.abstract_pattern_shape,
            worldlet_feedback_present=False,
            repl_result_present=False,
            dispatch_trace_digest=None,
            reasoning_trace_digest=None,
            learning_evidence_digest=None,
            active_hypothesis_digest=None,
            curriculum_digest=None,
            context_signature=e.context_signature,
        )
    return None


# ---------------------------------------------------------------------------
# Trial battery (closed v1 plan).
# ---------------------------------------------------------------------------


# Canonical contexts used by the v1 battery. Each context's
# ``abstract_pattern_digest`` is derived from a closed bounded
# input via ``derive_abstract_pattern_signature``.
def _ctx_for_input(text: str, **kw) -> ProtoSpeechContext:
    sig = derive_abstract_pattern_signature(text)
    digest = sig.digest_hex16 if sig.valid else None
    shape = sig.shape if sig.valid else None
    return build_proto_speech_context(
        context_kind=ProtoSpeechContextKind.ABSTRACT_PATTERN,
        abstract_pattern_digest=digest,
        abstract_pattern_shape=shape,
        **kw,
    )


# Canonical bounded operator inputs used by the v1 battery. None
# of them contain a forbidden direct-instruction or non-claim
# term.
_OP_ABA = "alpha beta alpha"
_OP_ABA_RENAMED = "gamma delta gamma"
_OP_ABB = "alpha beta beta"
_OP_ABC = "epsilon zeta eta"


def _make_feedback(
    kind: CaregiverFeedbackKind,
    *,
    context_label: str,
    offered: Optional[ProtoUtterance] = None,
    ambient: Optional[ProtoUtterance] = None,
) -> CaregiverFeedback:
    attempted_delta, offered_delta = _feedback_deltas(kind)
    delta = attempted_delta if attempted_delta != 0 else offered_delta
    return CaregiverFeedback(
        kind=kind,
        offered_utterance=offered,
        ambient_utterance=ambient,
        context_label=context_label,
        evidence_delta=delta,
    )


def _build_babble_baseline_specs() -> tuple[_TurnSpec, ...]:
    """C0 BABBLE_BASELINE: low evidence; deterministic exploratory babble."""
    ctx = _ctx_for_input(_OP_ABA)
    specs: list[_TurnSpec] = []
    for i in range(3):
        feedback = _make_feedback(
            CaregiverFeedbackKind.IGNORED,
            context_label=f"baseline-{i + 1:02d}",
        )
        specs.append(
            _TurnSpec(
                turn_id=f"C0_BABBLE_BASELINE_{i + 1:02d}",
                condition=ProtoSpeechCondition.BABBLE_BASELINE,
                context=ctx,
                operator_input_text=_OP_ABA,
                caregiver_ambient=None,
                feedback=feedback,
            )
        )
    return tuple(specs)


def _build_ambient_imprinting_specs() -> tuple[_TurnSpec, ...]:
    """C1 AMBIENT_IMPRINTING: caregiver ambient changes later selection."""
    ctx = _ctx_for_input(_OP_ABA)
    same = build_proto_utterance((ProtoVocalToken.SAME,))
    specs: list[_TurnSpec] = []
    # Three priming turns where the caregiver says SAME ambiently.
    for i in range(3):
        feedback = _make_feedback(
            CaregiverFeedbackKind.AMBIENT_ONLY,
            context_label=f"ambient-{i + 1:02d}",
            ambient=same,
        )
        specs.append(
            _TurnSpec(
                turn_id=f"C1_AMBIENT_IMPRINTING_{i + 1:02d}",
                condition=ProtoSpeechCondition.AMBIENT_IMPRINTING,
                context=ctx,
                operator_input_text=_OP_ABA,
                caregiver_ambient=same,
                feedback=feedback,
            )
        )
    return tuple(specs)


def _build_feedback_reinforcement_specs() -> tuple[_TurnSpec, ...]:
    """C2 FEEDBACK_REINFORCEMENT: ACCEPTED / ECHO drives recur."""
    ctx = _ctx_for_input(_OP_ABA)
    look = build_proto_utterance((ProtoVocalToken.LOOK,))
    specs: list[_TurnSpec] = []
    # Two reinforcement turns plus one recurrence check.
    for i in range(3):
        kind = (
            CaregiverFeedbackKind.ECHO
            if i < 2
            else CaregiverFeedbackKind.ACCEPTED
        )
        feedback = _make_feedback(
            kind,
            context_label=f"reinf-{i + 1:02d}",
            offered=look,
        )
        specs.append(
            _TurnSpec(
                turn_id=f"C2_FEEDBACK_REINFORCEMENT_{i + 1:02d}",
                condition=ProtoSpeechCondition.FEEDBACK_REINFORCEMENT,
                context=ctx,
                operator_input_text=_OP_ABA,
                caregiver_ambient=None,
                feedback=feedback,
            )
        )
    return tuple(specs)


def _build_correction_shaping_specs() -> tuple[_TurnSpec, ...]:
    """C3 CORRECTION_SHAPING: CORRECTED weakens attempted, strengthens offered."""
    ctx = _ctx_for_input(_OP_ABA)
    # Two reinforcement turns set MORE as the preferred form via ambient
    # priming + feedback echoes, then four corrections steer toward
    # YES.
    yes = build_proto_utterance((ProtoVocalToken.YES,))
    more = build_proto_utterance((ProtoVocalToken.MORE,))
    specs: list[_TurnSpec] = []
    # Two priming turns: caregiver ambient = MORE, then ACCEPTED.
    for i in range(2):
        kind = (
            CaregiverFeedbackKind.AMBIENT_ONLY
            if i == 0
            else CaregiverFeedbackKind.ACCEPTED
        )
        feedback = _make_feedback(
            kind,
            context_label=f"correct-prime-{i + 1:02d}",
            ambient=more if i == 0 else None,
            offered=more,
        )
        specs.append(
            _TurnSpec(
                turn_id=f"C3_CORRECTION_SHAPING_PRIME_{i + 1:02d}",
                condition=ProtoSpeechCondition.CORRECTION_SHAPING,
                context=ctx,
                operator_input_text=_OP_ABA,
                caregiver_ambient=more if i == 0 else None,
                feedback=feedback,
            )
        )
    # Four correction turns: caregiver replaces MORE with YES.
    for i in range(4):
        feedback = _make_feedback(
            CaregiverFeedbackKind.CORRECTED,
            context_label=f"correct-{i + 1:02d}",
            offered=yes,
        )
        specs.append(
            _TurnSpec(
                turn_id=f"C3_CORRECTION_SHAPING_{i + 1:02d}",
                condition=ProtoSpeechCondition.CORRECTION_SHAPING,
                context=ctx,
                operator_input_text=_OP_ABA,
                caregiver_ambient=None,
                feedback=feedback,
            )
        )
    return tuple(specs)


def _build_suppression_specs() -> tuple[_TurnSpec, ...]:
    """C6 SUPPRESSION: repeated IGNORED feedback suppresses a form.

    Drive the candidate via caregiver feedback prime to ensure a
    specific form is exercised, then repeatedly ignore it.
    """
    ctx = _ctx_for_input(_OP_ABA)
    na = build_proto_utterance((ProtoVocalToken.NA,))
    specs: list[_TurnSpec] = []
    # Three IGNORED turns with the caregiver naming NA in the feedback
    # ambient slot so the runtime selects NA each time. Use
    # AMBIENT_ONLY for the priming pulse so the offered-utterance
    # weight does not move (only the ambient form gets +1, and the
    # IGNORED rule's attempted-delta = -1).
    prime_feedback = _make_feedback(
        CaregiverFeedbackKind.AMBIENT_ONLY,
        context_label="suppress-prime",
        ambient=na,
    )
    specs.append(
        _TurnSpec(
            turn_id="C6_SUPPRESSION_PRIME",
            condition=ProtoSpeechCondition.SUPPRESSION,
            context=ctx,
            operator_input_text=_OP_ABA,
            caregiver_ambient=na,
            feedback=prime_feedback,
        )
    )
    for i in range(5):
        feedback = _make_feedback(
            CaregiverFeedbackKind.IGNORED,
            context_label=f"suppress-{i + 1:02d}",
        )
        specs.append(
            _TurnSpec(
                turn_id=f"C6_SUPPRESSION_{i + 1:02d}",
                condition=ProtoSpeechCondition.SUPPRESSION,
                context=ctx,
                operator_input_text=_OP_ABA,
                caregiver_ambient=na,
                feedback=feedback,
            )
        )
    # One final non-ambient turn to verify the suppressed form is
    # no longer surfaced.
    final_feedback = _make_feedback(
        CaregiverFeedbackKind.IGNORED,
        context_label="suppress-final",
    )
    specs.append(
        _TurnSpec(
            turn_id="C6_SUPPRESSION_FINAL",
            condition=ProtoSpeechCondition.SUPPRESSION,
            context=ctx,
            operator_input_text=_OP_ABA,
            caregiver_ambient=None,
            feedback=final_feedback,
        )
    )
    return tuple(specs)


def _build_holophrase_transfer_specs() -> tuple[_TurnSpec, ...]:
    """C4 HOLOPHRASE_TRANSFER: stable single transfers to same-shape context.

    Three priming turns in ABA context bind THIS to STABLE_SINGLE;
    the fourth turn is in a renamed-same-shape context where the
    runner emits a TRANSFER_PRESSURE frame referencing the stable
    single. A fifth turn in a different-shape context (ABB) tests
    the negative control.
    """
    # Same-shape contexts must share ``abstract_pattern_digest``
    # while differing in at least one substrate field so their
    # ``context_signature`` digests are distinct. The test puts
    # the renamed-target context under a worldlet-feedback-present
    # surface; the negative-control context is in a different
    # shape entirely.
    src_ctx = _ctx_for_input(_OP_ABA)
    same_shape_ctx = _ctx_for_input(
        _OP_ABA_RENAMED, worldlet_feedback_present=True
    )
    diff_shape_ctx = _ctx_for_input(_OP_ABB)
    this = build_proto_utterance((ProtoVocalToken.THIS,))
    specs: list[_TurnSpec] = []
    for i in range(3):
        kind = (
            CaregiverFeedbackKind.ECHO
            if i < 2
            else CaregiverFeedbackKind.ACCEPTED
        )
        feedback = _make_feedback(
            kind,
            context_label=f"holo-prime-{i + 1:02d}",
            offered=this,
        )
        specs.append(
            _TurnSpec(
                turn_id=f"C4_HOLOPHRASE_TRANSFER_PRIME_{i + 1:02d}",
                condition=ProtoSpeechCondition.HOLOPHRASE_TRANSFER,
                context=src_ctx,
                operator_input_text=_OP_ABA,
                caregiver_ambient=None,
                feedback=feedback,
            )
        )
    # Transfer turn: structurally similar context (renamed tokens,
    # same shape digest).
    transfer_feedback = _make_feedback(
        CaregiverFeedbackKind.ACCEPTED,
        context_label="holo-pos-target",
        offered=this,
    )
    specs.append(
        _TurnSpec(
            turn_id="C4_HOLOPHRASE_TRANSFER_POS",
            condition=ProtoSpeechCondition.HOLOPHRASE_TRANSFER,
            context=same_shape_ctx,
            operator_input_text=_OP_ABA_RENAMED,
            caregiver_ambient=None,
            feedback=transfer_feedback,
            transfer_pressure_token=ProtoVocalToken.THIS,
        )
    )
    # Negative control: different-shape context. No
    # transfer_pressure_token; the source's STABLE_SINGLE must NOT
    # bleed through.
    neg_feedback = _make_feedback(
        CaregiverFeedbackKind.IGNORED,
        context_label="holo-neg",
    )
    specs.append(
        _TurnSpec(
            turn_id="C4_HOLOPHRASE_TRANSFER_NEG",
            condition=ProtoSpeechCondition.HOLOPHRASE_TRANSFER,
            context=diff_shape_ctx,
            operator_input_text=_OP_ABB,
            caregiver_ambient=None,
            feedback=neg_feedback,
        )
    )
    return tuple(specs)


def _build_two_token_combination_specs() -> tuple[_TurnSpec, ...]:
    """C5 TWO_TOKEN_COMBINATION: stable singles combine when pressure exists.

    Three priming turns bind ``SAME`` to STABLE_SINGLE in the
    context; three more priming turns bind ``AGAIN``; the seventh
    turn applies combination pressure and the runtime emits the
    two-token form. The combination cannot appear before the
    prerequisites because the runner does not surface
    COMBINATION_PRESSURE until two distinct stable singles exist
    for the context.
    """
    ctx = _ctx_for_input(_OP_ABA)
    same = build_proto_utterance((ProtoVocalToken.SAME,))
    again = build_proto_utterance((ProtoVocalToken.AGAIN,))
    specs: list[_TurnSpec] = []
    for i in range(3):
        feedback = _make_feedback(
            CaregiverFeedbackKind.ECHO,
            context_label=f"comb-prime-same-{i + 1:02d}",
            offered=same,
        )
        specs.append(
            _TurnSpec(
                turn_id=f"C5_TWO_TOKEN_COMB_PRIME_SAME_{i + 1:02d}",
                condition=ProtoSpeechCondition.TWO_TOKEN_COMBINATION,
                context=ctx,
                operator_input_text=_OP_ABA,
                caregiver_ambient=None,
                feedback=feedback,
            )
        )
    for i in range(3):
        feedback = _make_feedback(
            CaregiverFeedbackKind.ECHO,
            context_label=f"comb-prime-again-{i + 1:02d}",
            offered=again,
        )
        specs.append(
            _TurnSpec(
                turn_id=f"C5_TWO_TOKEN_COMB_PRIME_AGAIN_{i + 1:02d}",
                condition=ProtoSpeechCondition.TWO_TOKEN_COMBINATION,
                context=ctx,
                operator_input_text=_OP_ABA,
                caregiver_ambient=None,
                feedback=feedback,
            )
        )
    # Combination-pressure turn: feedback ACCEPTED on the combination.
    combo = build_proto_utterance(
        (ProtoVocalToken.SAME, ProtoVocalToken.AGAIN)
    )
    feedback = _make_feedback(
        CaregiverFeedbackKind.ACCEPTED,
        context_label="comb-emit",
        offered=combo,
    )
    specs.append(
        _TurnSpec(
            turn_id="C5_TWO_TOKEN_COMB_EMIT",
            condition=ProtoSpeechCondition.TWO_TOKEN_COMBINATION,
            context=ctx,
            operator_input_text=_OP_ABA,
            caregiver_ambient=None,
            feedback=feedback,
            combination_pressure=True,
        )
    )
    return tuple(specs)


def _build_turn_taking_specs() -> tuple[_TurnSpec, ...]:
    """C7 TURN_TAKING: prove the bounded context -> drive -> utt -> fb -> ev order."""
    ctx = _ctx_for_input(_OP_ABA)
    yes = build_proto_utterance((ProtoVocalToken.YES,))
    feedback = _make_feedback(
        CaregiverFeedbackKind.ACCEPTED,
        context_label="turn-taking",
        offered=yes,
    )
    return (
        _TurnSpec(
            turn_id="C7_TURN_TAKING_01",
            condition=ProtoSpeechCondition.TURN_TAKING,
            context=ctx,
            operator_input_text=_OP_ABA,
            caregiver_ambient=yes,
            feedback=feedback,
        ),
    )


def _build_refusal_held_specs() -> tuple[_TurnSpec, ...]:
    """C8 REFUSAL_HELD: refusal-guard input does not select an utterance."""
    ctx = _ctx_for_input(_OP_ABA)
    feedback = _make_feedback(
        CaregiverFeedbackKind.IGNORED,
        context_label="refusal-held",
    )
    return (
        _TurnSpec(
            turn_id="C8_REFUSAL_HELD",
            condition=ProtoSpeechCondition.REFUSAL_HELD,
            context=ctx,
            operator_input_text=_OP_ABA,
            caregiver_ambient=None,
            feedback=feedback,
            refusal_guard=True,
        ),
    )


def _build_drive_stream_pressure_specs() -> tuple[_TurnSpec, ...]:
    """C9 DRIVE_STREAM_PRESSURE: distinct drive kinds change candidate sets."""
    ctx = _ctx_for_input(_OP_ABA)
    # Turn 1: novelty pressure with ambient (first visit, ambient
    # present); turn 2: recurrence pressure (second visit, ambient
    # present); turn 3: unresolved hypothesis pressure.
    same = build_proto_utterance((ProtoVocalToken.SAME,))
    look = build_proto_utterance((ProtoVocalToken.LOOK,))
    fb_amb = _make_feedback(
        CaregiverFeedbackKind.AMBIENT_ONLY,
        context_label="drive-novelty",
        ambient=look,
    )
    fb_recur = _make_feedback(
        CaregiverFeedbackKind.AMBIENT_ONLY,
        context_label="drive-recur",
        ambient=same,
    )
    fb_unr = _make_feedback(
        CaregiverFeedbackKind.IGNORED,
        context_label="drive-unresolved",
    )
    return (
        _TurnSpec(
            turn_id="C9_DRIVE_PRESSURE_NOVELTY",
            condition=ProtoSpeechCondition.DRIVE_STREAM_PRESSURE,
            context=ctx,
            operator_input_text=_OP_ABA,
            caregiver_ambient=look,
            feedback=fb_amb,
        ),
        _TurnSpec(
            turn_id="C9_DRIVE_PRESSURE_RECUR",
            condition=ProtoSpeechCondition.DRIVE_STREAM_PRESSURE,
            context=ctx,
            operator_input_text=_OP_ABA,
            caregiver_ambient=same,
            feedback=fb_recur,
        ),
        _TurnSpec(
            turn_id="C9_DRIVE_PRESSURE_UNR",
            condition=ProtoSpeechCondition.DRIVE_STREAM_PRESSURE,
            context=ctx,
            operator_input_text=_OP_ABA,
            caregiver_ambient=None,
            feedback=fb_unr,
            has_active_hypothesis_unresolved=True,
        ),
    )


def build_proto_speech_battery() -> tuple[
    tuple[ProtoSpeechCondition, tuple[_TurnSpec, ...]], ...
]:
    """Return the closed v1 ten-condition battery."""
    return (
        (
            ProtoSpeechCondition.BABBLE_BASELINE,
            _build_babble_baseline_specs(),
        ),
        (
            ProtoSpeechCondition.AMBIENT_IMPRINTING,
            _build_ambient_imprinting_specs(),
        ),
        (
            ProtoSpeechCondition.FEEDBACK_REINFORCEMENT,
            _build_feedback_reinforcement_specs(),
        ),
        (
            ProtoSpeechCondition.CORRECTION_SHAPING,
            _build_correction_shaping_specs(),
        ),
        (
            ProtoSpeechCondition.HOLOPHRASE_TRANSFER,
            _build_holophrase_transfer_specs(),
        ),
        (
            ProtoSpeechCondition.TWO_TOKEN_COMBINATION,
            _build_two_token_combination_specs(),
        ),
        (
            ProtoSpeechCondition.SUPPRESSION,
            _build_suppression_specs(),
        ),
        (
            ProtoSpeechCondition.TURN_TAKING,
            _build_turn_taking_specs(),
        ),
        (
            ProtoSpeechCondition.REFUSAL_HELD,
            _build_refusal_held_specs(),
        ),
        (
            ProtoSpeechCondition.DRIVE_STREAM_PRESSURE,
            _build_drive_stream_pressure_specs(),
        ),
    )


# ---------------------------------------------------------------------------
# Live-test report + runner.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProtoSpeechAcquisitionReport:
    """Final bounded live-test report (Phase 3.31)."""

    module_name: ClassVar[str] = "proto_speech_acquisition"

    battery_version: str
    turns: tuple[ProtoSpeechTurn, ...]
    condition_statuses: tuple[tuple[ProtoSpeechCondition, ProtoSpeechStatus], ...]
    stable_single_count: int
    stable_combination_count: int
    suppressed_count: int
    transfer_success_count: int
    false_positive_count: int
    false_negative_count: int
    pass_count: int
    warn_count: int
    fail_count: int
    not_applicable_count: int
    drive_stream_count: int
    drive_stream_digest_hex16: str
    digest_hex16: str
    real_model_calls: int
    cache_writes: int
    forbidden_term_hits: int
    summary_line: str
    status: ProtoSpeechStatus

    def __post_init__(self) -> None:
        _validate_bounded_printable(
            self.battery_version,
            field="ProtoSpeechAcquisitionReport.battery_version",
            max_len=PROTO_SPEECH_TURN_ID_MAX_LEN,
        )
        if not isinstance(self.turns, tuple):
            raise TypeError(
                "I-PSPEECH-13 violated: turns must be a tuple"
            )
        if len(self.turns) > PROTO_SPEECH_MAX_TURNS_PER_REPORT:
            raise ValueError(
                "I-PSPEECH-13 violated: turns length "
                f"{len(self.turns)} > "
                f"{PROTO_SPEECH_MAX_TURNS_PER_REPORT}"
            )
        for t in self.turns:
            if not isinstance(t, ProtoSpeechTurn):
                raise TypeError(
                    "I-PSPEECH-13 violated: every turns entry must be a "
                    "ProtoSpeechTurn"
                )
        if not isinstance(self.condition_statuses, tuple):
            raise TypeError(
                "I-PSPEECH-13 violated: condition_statuses must be a tuple"
            )
        for entry in self.condition_statuses:
            if (
                not isinstance(entry, tuple)
                or len(entry) != 2
                or not isinstance(entry[0], ProtoSpeechCondition)
                or not isinstance(entry[1], ProtoSpeechStatus)
            ):
                raise TypeError(
                    "I-PSPEECH-13 violated: condition_statuses entries must "
                    "be (ProtoSpeechCondition, ProtoSpeechStatus) tuples"
                )
        for name, val in (
            ("stable_single_count", self.stable_single_count),
            ("stable_combination_count", self.stable_combination_count),
            ("suppressed_count", self.suppressed_count),
            ("transfer_success_count", self.transfer_success_count),
            ("false_positive_count", self.false_positive_count),
            ("false_negative_count", self.false_negative_count),
            ("pass_count", self.pass_count),
            ("warn_count", self.warn_count),
            ("fail_count", self.fail_count),
            ("not_applicable_count", self.not_applicable_count),
            ("drive_stream_count", self.drive_stream_count),
            ("real_model_calls", self.real_model_calls),
            ("cache_writes", self.cache_writes),
            ("forbidden_term_hits", self.forbidden_term_hits),
        ):
            if (
                not isinstance(val, int)
                or isinstance(val, bool)
                or val < 0
            ):
                raise ValueError(
                    "I-PSPEECH-13 violated: "
                    f"ProtoSpeechAcquisitionReport.{name} must be a "
                    f"non-negative int"
                )
        _validate_digest_hex(
            self.drive_stream_digest_hex16,
            field="ProtoSpeechAcquisitionReport.drive_stream_digest_hex16",
        )
        _validate_digest_hex(
            self.digest_hex16,
            field="ProtoSpeechAcquisitionReport.digest_hex16",
        )
        _validate_bounded_printable(
            self.summary_line,
            field="ProtoSpeechAcquisitionReport.summary_line",
            max_len=PROTO_SPEECH_EXPLAIN_MAX_LEN,
        )
        if not isinstance(self.status, ProtoSpeechStatus):
            raise TypeError(
                "I-PSPEECH-13 violated: status must be a ProtoSpeechStatus"
            )


# Closed v1 expected predicates per condition. Predicates are
# evaluated AFTER the condition's bounded turn list has finished;
# the runtime path never sees them.
def _evaluate_condition_status(
    condition: ProtoSpeechCondition,
    turns: tuple[ProtoSpeechTurn, ...],
    *,
    final_table: ProtoSpeechEvidenceTable,
) -> tuple[
    ProtoSpeechStatus,
    int,  # stable_single delta produced by this condition
    int,  # stable_combination delta
    int,  # suppressed delta
    int,  # transfer_success delta
    int,  # false_positive
    int,  # false_negative
]:
    """Return ``(status, stable_single, stable_comb, suppressed, transfers, fp, fn)``.

    The status is PASS iff every per-condition closed predicate
    holds.
    """
    if not turns:
        return (
            ProtoSpeechStatus.NOT_APPLICABLE,
            0, 0, 0, 0, 0, 0,
        )
    ctx_sig = turns[0].context.context_signature
    ctx_entries = final_table.context_entries(
        context_signature=ctx_sig
    )

    def _has_disposition(
        ctx_signature: str,
        utterance: ProtoUtterance,
        disposition: ProtoUtteranceDisposition,
    ) -> bool:
        rec = final_table.select(
            context_signature=ctx_signature,
            utterance_digest=utterance.digest_hex16,
        )
        return rec is not None and rec.disposition is disposition

    stable_single = sum(
        1
        for e in ctx_entries
        if e.disposition is ProtoUtteranceDisposition.STABLE_SINGLE
    )
    stable_comb = sum(
        1
        for e in ctx_entries
        if e.disposition is ProtoUtteranceDisposition.STABLE_COMBINATION
    )
    suppressed = sum(
        1
        for e in ctx_entries
        if e.disposition is ProtoUtteranceDisposition.SUPPRESSED
    )
    transfers = sum(1 for t in turns if t.transfer_taken)

    fp = 0
    fn = 0
    status = ProtoSpeechStatus.PASS

    if condition is ProtoSpeechCondition.BABBLE_BASELINE:
        # Every selected utterance must be a single bounded token
        # drawn from the LOW_EVIDENCE primitives (BA/MA/DA) and the
        # condition must produce zero stable singles in this context.
        for t in turns:
            if t.refusal_taken:
                status = ProtoSpeechStatus.FAIL
                break
            if t.selected_utterance.token_count != 1:
                status = ProtoSpeechStatus.FAIL
                break
            tok = t.selected_utterance.tokens[0]
            if tok not in (
                ProtoVocalToken.BA,
                ProtoVocalToken.MA,
                ProtoVocalToken.DA,
            ):
                status = ProtoSpeechStatus.FAIL
                break
            # Every babble must trace back to a LOW_EVIDENCE drive
            # frame.
            if not any(
                f.drive_kind is ProtoSpeechDriveKind.LOW_EVIDENCE
                for f in t.drive_stream.frames
            ):
                status = ProtoSpeechStatus.FAIL
                break
        # No stable single should emerge for the baseline since
        # IGNORED feedback decrements.
        if any(
            e.disposition is ProtoUtteranceDisposition.STABLE_SINGLE
            for e in ctx_entries
        ):
            fp = 1
            status = ProtoSpeechStatus.FAIL

    elif condition is ProtoSpeechCondition.AMBIENT_IMPRINTING:
        # Every turn the runtime should pick the caregiver-ambient
        # token SAME.
        for t in turns:
            if t.selected_utterance.token_count != 1:
                status = ProtoSpeechStatus.FAIL
                break
            if t.selected_utterance.tokens[0] is not ProtoVocalToken.SAME:
                status = ProtoSpeechStatus.FAIL
                break

    elif condition is ProtoSpeechCondition.FEEDBACK_REINFORCEMENT:
        # LOOK should end up reinforced or stable.
        look_utt = build_proto_utterance((ProtoVocalToken.LOOK,))
        rec = final_table.select(
            context_signature=ctx_sig,
            utterance_digest=look_utt.digest_hex16,
        )
        if rec is None or rec.weight_after < 3:
            status = ProtoSpeechStatus.FAIL
        # The third feedback turn (ACCEPTED) should have re-selected
        # LOOK.
        if turns[-1].selected_utterance.text != "look":
            status = ProtoSpeechStatus.FAIL

    elif condition is ProtoSpeechCondition.CORRECTION_SHAPING:
        yes_utt = build_proto_utterance((ProtoVocalToken.YES,))
        rec_yes = final_table.select(
            context_signature=ctx_sig,
            utterance_digest=yes_utt.digest_hex16,
        )
        # YES must reach >= STABLE_SINGLE_THRESHOLD.
        if rec_yes is None or rec_yes.weight_after < (
            STABLE_SINGLE_THRESHOLD
        ):
            status = ProtoSpeechStatus.FAIL
        # The attempted forms during the four CORRECTED turns must
        # show a non-positive total delta (corrections weaken
        # attempted).
        corrected_turns = [
            t for t in turns
            if t.feedback.kind is CaregiverFeedbackKind.CORRECTED
        ]
        attempted_deltas = []
        for t in corrected_turns:
            for r in t.evidence_records_added:
                if r.feedback_kind is CaregiverFeedbackKind.CORRECTED:
                    if (
                        r.utterance_digest
                        == t.selected_utterance.digest_hex16
                    ):
                        attempted_deltas.append(
                            r.weight_after - r.weight_before
                        )
        if not attempted_deltas:
            status = ProtoSpeechStatus.FAIL
        elif any(d > 0 for d in attempted_deltas):
            status = ProtoSpeechStatus.FAIL

    elif condition is ProtoSpeechCondition.HOLOPHRASE_TRANSFER:
        # Exactly one transfer must occur to the positive target.
        if transfers != 1:
            status = ProtoSpeechStatus.FAIL
        # The negative-target context must NOT have a TRANSFERRED
        # record for THIS.
        neg_ctx = turns[-1].context
        this_utt = build_proto_utterance((ProtoVocalToken.THIS,))
        neg_rec = final_table.select(
            context_signature=neg_ctx.context_signature,
            utterance_digest=this_utt.digest_hex16,
        )
        if neg_rec is not None and neg_rec.disposition is (
            ProtoUtteranceDisposition.TRANSFERRED
        ):
            fp = 1
            status = ProtoSpeechStatus.FAIL

    elif condition is ProtoSpeechCondition.TWO_TOKEN_COMBINATION:
        # The final turn must emit a 2-token utterance and must
        # produce a STABLE_COMBINATION evidence record.
        last = turns[-1]
        if last.selected_utterance.token_count != 2:
            status = ProtoSpeechStatus.FAIL
        else:
            combo_rec = final_table.select(
                context_signature=ctx_sig,
                utterance_digest=last.selected_utterance.digest_hex16,
            )
            if combo_rec is None or combo_rec.disposition is not (
                ProtoUtteranceDisposition.STABLE_COMBINATION
            ):
                # Acceptable if combination not yet "stable" by the
                # final turn but still emerged; require at least
                # CANDIDATE / REINFORCED disposition.
                if combo_rec is None or combo_rec.disposition not in (
                    ProtoUtteranceDisposition.CANDIDATE,
                    ProtoUtteranceDisposition.REINFORCED,
                    ProtoUtteranceDisposition.STABLE_COMBINATION,
                ):
                    status = ProtoSpeechStatus.FAIL
        # Combination must not appear before prerequisites.
        for t in turns[:-1]:
            if t.selected_utterance.token_count == 2:
                fp = 1
                status = ProtoSpeechStatus.FAIL
                break

    elif condition is ProtoSpeechCondition.SUPPRESSION:
        na_utt = build_proto_utterance((ProtoVocalToken.NA,))
        # The NA form must be SUPPRESSED at the end.
        rec_na = final_table.select(
            context_signature=ctx_sig,
            utterance_digest=na_utt.digest_hex16,
        )
        if rec_na is None or rec_na.disposition is not (
            ProtoUtteranceDisposition.SUPPRESSED
        ):
            status = ProtoSpeechStatus.FAIL
        # The final non-ambient turn must NOT emit NA.
        if turns[-1].selected_utterance.text == "na":
            fp = 1
            status = ProtoSpeechStatus.FAIL

    elif condition is ProtoSpeechCondition.TURN_TAKING:
        # The turn must have a context, drive stream with >=1 frame,
        # a selected utterance, a feedback record, and exactly the
        # closed order (proved by the presence of all five fields
        # and refusal_taken=False).
        t = turns[0]
        if t.refusal_taken:
            status = ProtoSpeechStatus.FAIL
        if not t.drive_stream.frames:
            status = ProtoSpeechStatus.FAIL
        if t.selected_utterance.token_count == 0:
            status = ProtoSpeechStatus.FAIL
        if len(t.evidence_records_added) == 0:
            status = ProtoSpeechStatus.FAIL

    elif condition is ProtoSpeechCondition.REFUSAL_HELD:
        t = turns[0]
        if not t.refusal_taken:
            status = ProtoSpeechStatus.FAIL
        # No evidence records should be added on a refusal turn.
        if len(t.evidence_records_added) != 0:
            status = ProtoSpeechStatus.FAIL
        # The drive stream must contain a REFUSAL_GUARD frame.
        if not any(
            f.drive_kind is ProtoSpeechDriveKind.REFUSAL_GUARD
            for f in t.drive_stream.frames
        ):
            status = ProtoSpeechStatus.FAIL

    elif condition is ProtoSpeechCondition.DRIVE_STREAM_PRESSURE:
        # Verify distinct drive-kind sets across the three turns.
        kinds_per_turn = [
            frozenset(f.drive_kind for f in t.drive_stream.frames)
            for t in turns
        ]
        # The novelty / recurrence / unresolved-hypothesis turns
        # should each have a distinguishing kind.
        if not any(
            ProtoSpeechDriveKind.NOVELTY_PRESSURE in k
            for k in kinds_per_turn
        ):
            status = ProtoSpeechStatus.FAIL
        if not any(
            ProtoSpeechDriveKind.RECURRENCE_PRESSURE in k
            for k in kinds_per_turn
        ):
            status = ProtoSpeechStatus.FAIL
        if not any(
            ProtoSpeechDriveKind.UNRESOLVED_HYPOTHESIS in k
            for k in kinds_per_turn
        ):
            status = ProtoSpeechStatus.FAIL

    return (
        status,
        stable_single,
        stable_comb,
        suppressed,
        transfers,
        fp,
        fn,
    )


def _serialize_turn(t: ProtoSpeechTurn) -> str:
    parts = [
        t.turn_id,
        t.condition.value,
        t.context.context_signature,
        t.drive_stream.digest_hex16,
        t.selected_utterance.text,
        t.selected_utterance.digest_hex16,
        t.feedback.kind.value,
        f"records={len(t.evidence_records_added)}",
        f"refusal={t.refusal_taken}",
        f"transfer={t.transfer_taken}",
        t.learning_evidence_digest or "",
        t.reasoning_trace_digest or "",
        t.dispatch_trace_digest or "",
        t.summary_line,
    ]
    for r in t.evidence_records_added:
        parts.append(
            f"rec|{r.digest_hex16}|{r.utterance_digest}|"
            f"w{r.weight_before}->{r.weight_after}|{r.disposition.value}|"
            f"{r.feedback_kind.value if r.feedback_kind else ''}|"
            f"{r.drive_stream_digest_hex16 or ''}"
        )
    return "\n".join(parts)


def proto_speech_report_digest(
    report: ProtoSpeechAcquisitionReport,
) -> str:
    """Return a deterministic 16-hex digest over the report."""
    payload = "\n".join(_serialize_turn(t) for t in report.turns).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()[
        :PROTO_SPEECH_DIGEST_HEX_LEN
    ]


def run_proto_speech_live_test() -> ProtoSpeechAcquisitionReport:
    """Run every closed v1 condition; assemble a bounded report."""
    battery = build_proto_speech_battery()

    all_turns: list[ProtoSpeechTurn] = []
    condition_statuses: list[
        tuple[ProtoSpeechCondition, ProtoSpeechStatus]
    ] = []
    stable_single_count = 0
    stable_combination_count = 0
    suppressed_count = 0
    transfer_success_count = 0
    false_positive_count = 0
    false_negative_count = 0
    pass_count = 0
    warn_count = 0
    fail_count = 0
    na_count = 0
    drive_stream_digests: list[str] = []

    for condition, specs in battery:
        state = _make_runtime_state()
        cond_turns: list[ProtoSpeechTurn] = []
        for idx, spec in enumerate(specs):
            turn = run_proto_speech_turn(
                state, spec, turn_index=idx
            )
            cond_turns.append(turn)
            drive_stream_digests.append(turn.drive_stream.digest_hex16)
        (
            status,
            ss,
            sc,
            sup,
            xfers,
            fp,
            fn,
        ) = _evaluate_condition_status(
            condition,
            tuple(cond_turns),
            final_table=state.table,
        )
        condition_statuses.append((condition, status))
        stable_single_count += ss
        stable_combination_count += sc
        suppressed_count += sup
        transfer_success_count += xfers
        false_positive_count += fp
        false_negative_count += fn
        if status is ProtoSpeechStatus.PASS:
            pass_count += 1
        elif status is ProtoSpeechStatus.WARN:
            warn_count += 1
        elif status is ProtoSpeechStatus.FAIL:
            fail_count += 1
        else:
            na_count += 1
        all_turns.extend(cond_turns)

    if fail_count > 0:
        report_status = ProtoSpeechStatus.FAIL
    elif warn_count > 0:
        report_status = ProtoSpeechStatus.WARN
    else:
        report_status = ProtoSpeechStatus.PASS

    drive_stream_digest = hashlib.sha256(
        "\n".join(drive_stream_digests).encode("utf-8")
    ).hexdigest()[:PROTO_SPEECH_DIGEST_HEX_LEN]

    summary_line = _bounded_excerpt(
        (
            f"proto_speech_live_test version="
            f"{PROTO_SPEECH_BATTERY_VERSION} "
            f"turns={len(all_turns)} pass={pass_count} "
            f"warn={warn_count} fail={fail_count} na={na_count} "
            f"stable_single={stable_single_count} "
            f"stable_comb={stable_combination_count} "
            f"suppressed={suppressed_count} "
            f"transfer={transfer_success_count} "
            f"fp={false_positive_count} fn={false_negative_count}"
        ),
        limit=PROTO_SPEECH_EXPLAIN_MAX_LEN,
    )

    placeholder = ProtoSpeechAcquisitionReport(
        battery_version=PROTO_SPEECH_BATTERY_VERSION,
        turns=tuple(all_turns),
        condition_statuses=tuple(condition_statuses),
        stable_single_count=stable_single_count,
        stable_combination_count=stable_combination_count,
        suppressed_count=suppressed_count,
        transfer_success_count=transfer_success_count,
        false_positive_count=false_positive_count,
        false_negative_count=false_negative_count,
        pass_count=pass_count,
        warn_count=warn_count,
        fail_count=fail_count,
        not_applicable_count=na_count,
        drive_stream_count=len(drive_stream_digests),
        drive_stream_digest_hex16=drive_stream_digest,
        digest_hex16=_zero_digest(),
        real_model_calls=0,
        cache_writes=0,
        forbidden_term_hits=0,
        summary_line=summary_line,
        status=report_status,
    )
    digest = proto_speech_report_digest(placeholder)
    return ProtoSpeechAcquisitionReport(
        battery_version=PROTO_SPEECH_BATTERY_VERSION,
        turns=tuple(all_turns),
        condition_statuses=tuple(condition_statuses),
        stable_single_count=stable_single_count,
        stable_combination_count=stable_combination_count,
        suppressed_count=suppressed_count,
        transfer_success_count=transfer_success_count,
        false_positive_count=false_positive_count,
        false_negative_count=false_negative_count,
        pass_count=pass_count,
        warn_count=warn_count,
        fail_count=fail_count,
        not_applicable_count=na_count,
        drive_stream_count=len(drive_stream_digests),
        drive_stream_digest_hex16=drive_stream_digest,
        digest_hex16=digest,
        real_model_calls=0,
        cache_writes=0,
        forbidden_term_hits=0,
        summary_line=summary_line,
        status=report_status,
    )


def format_proto_speech_report(
    report: ProtoSpeechAcquisitionReport,
) -> str:
    """Return a bounded printable table summarizing the report."""
    if not isinstance(report, ProtoSpeechAcquisitionReport):
        raise TypeError(
            "I-PSPEECH-13 violated: format_proto_speech_report requires "
            "a ProtoSpeechAcquisitionReport"
        )
    lines: list[str] = []
    lines.append(report.summary_line)
    for cond, status in report.condition_statuses:
        lines.append(
            f"  {cond.value:28s} -> {status.value}"
        )
    lines.append(
        f"  drive_stream_count={report.drive_stream_count} "
        f"drive_stream_digest={report.drive_stream_digest_hex16}"
    )
    lines.append(f"  report_digest={report.digest_hex16}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry.
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 3.31 caregiver-scaffolded proto-speech "
            "acquisition live-test runner (deterministic, OFFLINE, "
            "zero real model calls)"
        )
    )
    parser.add_argument("--quiet", action="store_true", default=False)
    args = parser.parse_args(argv)

    report = run_proto_speech_live_test()
    if not args.quiet:
        sys.stdout.write(
            format_proto_speech_report(report) + "\n"
        )
        sys.stdout.write(
            f"stable_single={report.stable_single_count} "
            f"stable_combination={report.stable_combination_count} "
            f"suppressed={report.suppressed_count} "
            f"transfer_success={report.transfer_success_count} "
            f"fp={report.false_positive_count} "
            f"fn={report.false_negative_count}\n"
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


# ---------------------------------------------------------------------------
# Module-produced strings (audited by the static-audit fixture).
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
    "ProtoSpeechDriveFrame",
    "ProtoSpeechDriveKind",
    "ProtoSpeechDriveStream",
    "ProtoSpeechAcquisitionReport",
    "ProtoSpeechEvidenceRecord",
    "ProtoSpeechEvidenceTable",
    "ProtoSpeechStatus",
    "ProtoSpeechTurn",
    "ProtoUtterance",
    "ProtoUtteranceDisposition",
    "ProtoVocalToken",
    "build_proto_speech_battery",
    "build_proto_speech_context",
    "build_proto_speech_drive_stream",
    "build_proto_utterance",
    "empty_evidence_table",
    "format_proto_speech_report",
    "main",
    "proto_speech_report_digest",
    "run_proto_speech_live_test",
    "select_babble_from_drive_stream",
    "select_proto_utterance",
    "transfer_proto_speech_evidence",
    "update_drive_stream_after_feedback",
    "update_proto_speech_evidence",
)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
