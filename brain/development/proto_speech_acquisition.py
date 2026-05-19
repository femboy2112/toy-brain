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
    "ProtoSpeechStatus",
    "ProtoUtterance",
    "ProtoUtteranceDisposition",
    "ProtoVocalToken",
    "build_proto_speech_context",
    "build_proto_speech_drive_stream",
    "build_proto_utterance",
    "update_drive_stream_after_feedback",
)
