"""Output Ladder primitives for Phase 3.2.

The v0.7 output surface is deliberately below language, agency, and runtime
state mutation. It records source-tagged output attempts and echo provenance in
copy-on-write developmental history only.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from types import MappingProxyType
from typing import Mapping

from brain.development.drives import require_unit_fraction
from brain.development.history import TraceEventID, require_printable_id
from brain.development.stream import FrameSourceKind
from brain.tlica.profile import COGITO_ID

OutputEchoID = str
OutputImpulseID = str
OutputPatternID = str
OutputSignature = tuple[tuple[str, str], ...]
OutputTokenID = str


@dataclass(frozen=True, slots=True)
class OutputProvenance:
    """Exact source metadata for an output impulse or echo."""

    source_kind: FrameSourceKind
    confidence: Fraction
    trace_event_ids: tuple[TraceEventID, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source_kind, FrameSourceKind):
            raise TypeError(
                "I-OUT-02 violated: OutputProvenance.source_kind must be a FrameSourceKind "
                f"(got {type(self.source_kind).__name__})"
            )
        try:
            require_unit_fraction(
                self.confidence,
                field="OutputProvenance.confidence",
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-OUT-02 violated: OutputProvenance.confidence must be a "
                "Fraction in [0, 1]"
            ) from exc
        if not isinstance(self.trace_event_ids, tuple):
            raise TypeError("OutputProvenance.trace_event_ids must be a tuple")
        for event_id in self.trace_event_ids:
            require_printable_id(
                event_id,
                field="OutputProvenance.trace_event_id",
            )


@dataclass(frozen=True, slots=True)
class OutputImpulse:
    """One bounded printable output attempt below language and agency."""

    impulse_id: OutputImpulseID
    text: str
    provenance: OutputProvenance
    target_id: str | None = None

    def __post_init__(self) -> None:
        try:
            require_printable_id(self.impulse_id, field="OutputImpulse.impulse_id")
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-OUT-01 violated: OutputImpulse.impulse_id must be "
                "non-empty and printable"
            ) from exc
        if not isinstance(self.text, str):
            raise TypeError(
                f"OutputImpulse.text must be a string (got {type(self.text).__name__})"
            )
        if not self.text or not self.text.strip() or not self.text.isprintable():
            raise ValueError(
                "I-OUT-01 violated: OutputImpulse.text must be non-empty and printable"
            )
        if not isinstance(self.provenance, OutputProvenance):
            raise TypeError("OutputImpulse.provenance must be OutputProvenance")
        if self.target_id is not None:
            try:
                require_printable_id(self.target_id, field="OutputImpulse.target_id")
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "I-OUT-01 violated: OutputImpulse.target_id must be "
                    "non-empty and printable"
                ) from exc
            if self.target_id == COGITO_ID:
                raise ValueError(
                    "I-OUT-01 violated: OutputImpulse cannot target COGITO_ID"
                )


@dataclass(frozen=True, slots=True)
class OutputEcho:
    """Inspectable history record that an output impulse was echoed."""

    echo_id: OutputEchoID
    impulse: OutputImpulse
    provenance: OutputProvenance

    def __post_init__(self) -> None:
        require_printable_id(self.echo_id, field="OutputEcho.echo_id")
        if not isinstance(self.impulse, OutputImpulse):
            raise TypeError("OutputEcho.impulse must be OutputImpulse")
        if not isinstance(self.provenance, OutputProvenance):
            raise TypeError("OutputEcho.provenance must be OutputProvenance")


def output_signature_from_impulse(impulse: OutputImpulse) -> OutputSignature:
    """Build the exact-match signature for recurrence-backed output."""
    if not isinstance(impulse, OutputImpulse):
        raise TypeError(
            f"impulse must be OutputImpulse (got {type(impulse).__name__})"
        )
    return (("text", impulse.text),)


def pattern_id_for_output_signature(signature: OutputSignature) -> OutputPatternID:
    if not isinstance(signature, tuple) or not signature:
        raise ValueError("I-OUT-07 violated: OutputPattern signature must be non-empty")
    digest = sha256(repr(signature).encode("utf-8")).hexdigest()[:16]
    return f"out-pattern:{digest}"


def token_id_for_output_pattern(pattern: "OutputPattern") -> OutputTokenID:
    if not isinstance(pattern, OutputPattern):
        raise TypeError(
            f"pattern must be OutputPattern (got {type(pattern).__name__})"
        )
    digest = sha256(pattern.pattern_id.encode("utf-8")).hexdigest()[:16]
    return f"out-token:{digest}"


def _require_source_kinds(
    source_kinds: frozenset[FrameSourceKind],
    *,
    field: str,
    row_id: str,
) -> None:
    if not isinstance(source_kinds, frozenset) or not source_kinds:
        raise ValueError(f"{row_id} violated: {field} must be a non-empty frozenset")
    for kind in source_kinds:
        if not isinstance(kind, FrameSourceKind):
            raise TypeError(f"{field} must contain FrameSourceKind values")


@dataclass(frozen=True, slots=True)
class OutputPattern:
    """A recurrent exact output form below language and agency."""

    pattern_id: OutputPatternID
    signature: OutputSignature
    text: str
    support_count: int
    source_kinds: frozenset[FrameSourceKind]
    impulse_ids: tuple[OutputImpulseID, ...]
    first_seen_index: int
    last_seen_index: int

    def __post_init__(self) -> None:
        require_printable_id(self.pattern_id, field="OutputPattern.pattern_id")
        if not isinstance(self.signature, tuple) or not self.signature:
            raise ValueError("I-OUT-07 violated: OutputPattern.signature must be non-empty")
        for key, value in self.signature:
            require_printable_id(key, field="OutputPattern.signature key")
            require_printable_id(value, field="OutputPattern.signature value")
        if not isinstance(self.text, str) or not self.text or not self.text.strip():
            raise ValueError("I-OUT-07 violated: OutputPattern.text must be non-empty")
        if not self.text.isprintable():
            raise ValueError("I-OUT-07 violated: OutputPattern.text must be printable")
        if not isinstance(self.support_count, int) or self.support_count < 2:
            raise ValueError("I-OUT-07 violated: OutputPattern.support_count must be >= 2")
        _require_source_kinds(
            self.source_kinds,
            field="OutputPattern.source_kinds",
            row_id="I-OUT-07",
        )
        if not isinstance(self.impulse_ids, tuple):
            raise TypeError("OutputPattern.impulse_ids must be a tuple")
        if len(self.impulse_ids) != self.support_count:
            raise ValueError(
                "I-OUT-07 violated: OutputPattern.impulse_ids must match support_count"
            )
        for impulse_id in self.impulse_ids:
            require_printable_id(impulse_id, field="OutputPattern.impulse_id")
        if (
            not isinstance(self.first_seen_index, int)
            or not isinstance(self.last_seen_index, int)
            or self.first_seen_index < 0
            or self.last_seen_index < self.first_seen_index
        ):
            raise ValueError(
                "I-OUT-07 violated: OutputPattern seen indices must be ordered"
            )

    def with_observation(
        self,
        *,
        support_count: int,
        source_kinds: frozenset[FrameSourceKind],
        impulse_ids: tuple[OutputImpulseID, ...],
        last_seen_index: int,
    ) -> "OutputPattern":
        return OutputPattern(
            pattern_id=self.pattern_id,
            signature=self.signature,
            text=self.text,
            support_count=support_count,
            source_kinds=source_kinds,
            impulse_ids=impulse_ids,
            first_seen_index=self.first_seen_index,
            last_seen_index=last_seen_index,
        )


@dataclass(frozen=True, slots=True)
class OutputTokenCandidate:
    """Stable output-token candidate requiring recurrence and echo provenance."""

    token_id: OutputTokenID
    pattern_id: OutputPatternID
    text: str
    support_count: int
    impulse_ids: tuple[OutputImpulseID, ...]
    echo_ids: tuple[OutputEchoID, ...]
    source_kinds: frozenset[FrameSourceKind]

    def __post_init__(self) -> None:
        require_printable_id(self.token_id, field="OutputTokenCandidate.token_id")
        require_printable_id(self.pattern_id, field="OutputTokenCandidate.pattern_id")
        if self.token_id == COGITO_ID or self.pattern_id == COGITO_ID:
            raise ValueError(
                "I-OUT-08 violated: OutputTokenCandidate cannot use reserved COGITO_ID"
            )
        if not isinstance(self.text, str) or not self.text or not self.text.strip():
            raise ValueError(
                "I-OUT-08 violated: OutputTokenCandidate.text must be non-empty"
            )
        if not self.text.isprintable() or self.text == COGITO_ID:
            raise ValueError(
                "I-OUT-08 violated: OutputTokenCandidate.text must be printable "
                "and non-reserved"
            )
        if not isinstance(self.support_count, int) or self.support_count < 2:
            raise ValueError(
                "I-OUT-08 violated: OutputTokenCandidate requires recurrent support"
            )
        if not isinstance(self.impulse_ids, tuple) or len(self.impulse_ids) < 2:
            raise ValueError(
                "I-OUT-08 violated: OutputTokenCandidate requires recurrent impulses"
            )
        if len(self.impulse_ids) != self.support_count:
            raise ValueError(
                "I-OUT-08 violated: OutputTokenCandidate impulse support mismatch"
            )
        if not isinstance(self.echo_ids, tuple) or len(self.echo_ids) < self.support_count:
            raise ValueError(
                "I-OUT-08 violated: OutputTokenCandidate requires echo provenance"
            )
        for impulse_id in self.impulse_ids:
            require_printable_id(impulse_id, field="OutputTokenCandidate.impulse_id")
            if impulse_id == COGITO_ID:
                raise ValueError(
                    "I-OUT-08 violated: OutputTokenCandidate cannot reference COGITO_ID"
                )
        for echo_id in self.echo_ids:
            require_printable_id(echo_id, field="OutputTokenCandidate.echo_id")
            if echo_id == COGITO_ID:
                raise ValueError(
                    "I-OUT-08 violated: OutputTokenCandidate cannot reference COGITO_ID"
                )
        _require_source_kinds(
            self.source_kinds,
            field="OutputTokenCandidate.source_kinds",
            row_id="I-OUT-08",
        )


@dataclass(frozen=True, slots=True)
class LearnedOutputToken:
    """A learned output token below language, syntax, and world reference."""

    token_id: OutputTokenID
    candidate: OutputTokenCandidate

    def __post_init__(self) -> None:
        require_printable_id(self.token_id, field="LearnedOutputToken.token_id")
        if self.token_id == COGITO_ID:
            raise ValueError("I-OUT-10 violated: learned token cannot use COGITO_ID")
        if not isinstance(self.candidate, OutputTokenCandidate):
            raise ValueError(
                "I-OUT-10 violated: learned token requires OutputTokenCandidate support"
            )
        if self.token_id != self.candidate.token_id:
            raise ValueError(
                "I-OUT-10 violated: learned token must preserve candidate token_id"
            )

    @property
    def text(self) -> str:
        return self.candidate.text

    @property
    def pattern_id(self) -> OutputPatternID:
        return self.candidate.pattern_id

    @property
    def support_count(self) -> int:
        return self.candidate.support_count

    @property
    def source_kinds(self) -> frozenset[FrameSourceKind]:
        return self.candidate.source_kinds


@dataclass(frozen=True, slots=True)
class ProtoOutputActionReadiness:
    """Local observation that output history is mature enough to inspect."""

    token_id: OutputTokenID
    pattern_id: OutputPatternID
    support_count: int
    echo_count: int
    source_kinds: frozenset[FrameSourceKind]
    ready: bool
    reason: str

    def __post_init__(self) -> None:
        require_printable_id(self.token_id, field="ProtoOutputActionReadiness.token_id")
        require_printable_id(self.pattern_id, field="ProtoOutputActionReadiness.pattern_id")
        if self.token_id == COGITO_ID or self.pattern_id == COGITO_ID:
            raise ValueError(
                "I-OUT-11 violated: proto-output-action readiness cannot use COGITO_ID"
            )
        if not isinstance(self.support_count, int) or self.support_count < 0:
            raise ValueError(
                "I-OUT-11 violated: support_count must be a non-negative integer"
            )
        if not isinstance(self.echo_count, int) or self.echo_count < 0:
            raise ValueError(
                "I-OUT-11 violated: echo_count must be a non-negative integer"
            )
        _require_source_kinds(
            self.source_kinds,
            field="ProtoOutputActionReadiness.source_kinds",
            row_id="I-OUT-11",
        )
        if not isinstance(self.ready, bool):
            raise TypeError("ProtoOutputActionReadiness.ready must be bool")
        require_printable_id(self.reason, field="ProtoOutputActionReadiness.reason")


@dataclass(frozen=True, slots=True)
class OutputHistory:
    """Immutable output-ladder store below the tick boundary."""

    impulses: tuple[OutputImpulse, ...] = ()
    echoes: tuple[OutputEcho, ...] = ()
    output_patterns: Mapping[OutputPatternID, OutputPattern] | None = None
    token_candidates: Mapping[OutputTokenID, OutputTokenCandidate] | None = None
    learned_tokens: Mapping[OutputTokenID, LearnedOutputToken] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.impulses, tuple):
            raise TypeError("OutputHistory.impulses must be a tuple")
        for impulse in self.impulses:
            if not isinstance(impulse, OutputImpulse):
                raise TypeError(
                    "OutputHistory.impulses must contain OutputImpulse values "
                    f"(got {type(impulse).__name__})"
                )

        if not isinstance(self.echoes, tuple):
            raise TypeError("OutputHistory.echoes must be a tuple")
        for echo in self.echoes:
            if not isinstance(echo, OutputEcho):
                raise TypeError(
                    "OutputHistory.echoes must contain OutputEcho values "
                    f"(got {type(echo).__name__})"
                )

        patterns = dict(self.output_patterns or {})
        candidates = dict(self.token_candidates or {})
        learned = dict(self.learned_tokens or {})
        for key in patterns:
            require_printable_id(key, field="OutputHistory.output_patterns key")
            if not isinstance(patterns[key], OutputPattern):
                raise TypeError(
                    "OutputHistory.output_patterns values must be OutputPattern"
                )
        for key in candidates:
            require_printable_id(key, field="OutputHistory.token_candidates key")
            if not isinstance(candidates[key], OutputTokenCandidate):
                raise TypeError(
                    "OutputHistory.token_candidates values must be OutputTokenCandidate"
                )
        for key in learned:
            require_printable_id(key, field="OutputHistory.learned_tokens key")
            if not isinstance(learned[key], LearnedOutputToken):
                raise TypeError(
                    "OutputHistory.learned_tokens values must be LearnedOutputToken"
                )

        object.__setattr__(self, "output_patterns", MappingProxyType(patterns))
        object.__setattr__(self, "token_candidates", MappingProxyType(candidates))
        object.__setattr__(self, "learned_tokens", MappingProxyType(learned))


def append_output_impulse(
    history: OutputHistory,
    impulse: OutputImpulse,
) -> OutputHistory:
    """Append one source-tagged impulse without mutating prior history."""
    if not isinstance(history, OutputHistory):
        raise TypeError(
            f"history must be OutputHistory (got {type(history).__name__})"
        )
    if not isinstance(impulse, OutputImpulse):
        raise TypeError(
            f"impulse must be OutputImpulse (got {type(impulse).__name__})"
        )
    return OutputHistory(
        impulses=history.impulses + (impulse,),
        echoes=history.echoes,
        output_patterns=history.output_patterns,
        token_candidates=history.token_candidates,
        learned_tokens=history.learned_tokens,
    )


def echo_output_impulse(
    history: OutputHistory,
    *,
    impulse_id: OutputImpulseID,
    echo_id: OutputEchoID,
    provenance: OutputProvenance | None = None,
) -> OutputHistory:
    """Record that an existing output impulse was echoed into history."""
    if not isinstance(history, OutputHistory):
        raise TypeError(
            f"history must be OutputHistory (got {type(history).__name__})"
        )
    require_printable_id(impulse_id, field="impulse_id")
    matched = tuple(i for i in history.impulses if i.impulse_id == impulse_id)
    if not matched:
        raise ValueError(f"unknown OutputImpulse {impulse_id!r}")
    if len(matched) > 1:
        raise ValueError(f"ambiguous OutputImpulse {impulse_id!r}")

    impulse = matched[0]
    echo = OutputEcho(
        echo_id=echo_id,
        impulse=impulse,
        provenance=provenance or impulse.provenance,
    )
    return OutputHistory(
        impulses=history.impulses,
        echoes=history.echoes + (echo,),
        output_patterns=history.output_patterns,
        token_candidates=history.token_candidates,
        learned_tokens=history.learned_tokens,
    )


def update_output_pattern(
    history: OutputHistory,
    impulse: OutputImpulse,
    *,
    min_support: int = 2,
) -> tuple[OutputHistory, OutputPattern | None]:
    """Append an impulse and create/update a pattern only after recurrence."""
    if not isinstance(history, OutputHistory):
        raise TypeError(
            f"history must be OutputHistory (got {type(history).__name__})"
        )
    if not isinstance(impulse, OutputImpulse):
        raise TypeError(
            f"impulse must be OutputImpulse (got {type(impulse).__name__})"
        )
    if not isinstance(min_support, int) or min_support < 2:
        raise ValueError("min_support must be an integer >= 2")

    next_history = append_output_impulse(history, impulse)
    signature = output_signature_from_impulse(impulse)
    matches = tuple(
        (index, candidate)
        for index, candidate in enumerate(next_history.impulses)
        if output_signature_from_impulse(candidate) == signature
    )
    support = len(matches)
    if support < min_support:
        return next_history, None

    pattern_id = pattern_id_for_output_signature(signature)
    impulse_ids = tuple(candidate.impulse_id for _, candidate in matches)
    source_kinds = frozenset(candidate.provenance.source_kind for _, candidate in matches)
    first_seen = matches[0][0]
    last_seen = matches[-1][0]
    existing = next_history.output_patterns.get(pattern_id)
    if isinstance(existing, OutputPattern):
        pattern = existing.with_observation(
            support_count=support,
            source_kinds=source_kinds,
            impulse_ids=impulse_ids,
            last_seen_index=last_seen,
        )
    else:
        pattern = OutputPattern(
            pattern_id=pattern_id,
            signature=signature,
            text=impulse.text,
            support_count=support,
            source_kinds=source_kinds,
            impulse_ids=impulse_ids,
            first_seen_index=first_seen,
            last_seen_index=last_seen,
        )

    patterns = dict(next_history.output_patterns)
    patterns[pattern.pattern_id] = pattern
    return (
        OutputHistory(
            impulses=next_history.impulses,
            echoes=next_history.echoes,
            output_patterns=patterns,
            token_candidates=next_history.token_candidates,
            learned_tokens=next_history.learned_tokens,
        ),
        pattern,
    )


def maybe_create_output_token_candidate(
    history: OutputHistory,
    pattern: OutputPattern | None,
) -> tuple[OutputHistory, OutputTokenCandidate | None]:
    """Create a token candidate only from recurrence plus echo provenance."""
    if not isinstance(history, OutputHistory):
        raise TypeError(
            f"history must be OutputHistory (got {type(history).__name__})"
        )
    if pattern is None:
        return history, None
    if not isinstance(pattern, OutputPattern):
        raise TypeError(
            f"pattern must be OutputPattern or None (got {type(pattern).__name__})"
        )
    if pattern.pattern_id not in history.output_patterns:
        return history, None

    support_ids = frozenset(pattern.impulse_ids)
    echoed_by_impulse = {
        echo.impulse.impulse_id: echo.echo_id
        for echo in history.echoes
        if echo.impulse.impulse_id in support_ids
    }
    if support_ids - frozenset(echoed_by_impulse):
        return history, None

    candidate = OutputTokenCandidate(
        token_id=token_id_for_output_pattern(pattern),
        pattern_id=pattern.pattern_id,
        text=pattern.text,
        support_count=pattern.support_count,
        impulse_ids=pattern.impulse_ids,
        echo_ids=tuple(echoed_by_impulse[impulse_id] for impulse_id in pattern.impulse_ids),
        source_kinds=pattern.source_kinds,
    )
    candidates = dict(history.token_candidates)
    candidates[candidate.token_id] = candidate
    return (
        OutputHistory(
            impulses=history.impulses,
            echoes=history.echoes,
            output_patterns=history.output_patterns,
            token_candidates=candidates,
            learned_tokens=history.learned_tokens,
        ),
        candidate,
    )


def learn_output_token(
    history: OutputHistory,
    candidate: OutputTokenCandidate,
) -> OutputHistory:
    """Learn a stable token from an accepted candidate without runtime mutation."""
    if not isinstance(history, OutputHistory):
        raise TypeError(
            f"history must be OutputHistory (got {type(history).__name__})"
        )
    if not isinstance(candidate, OutputTokenCandidate):
        raise TypeError(
            f"candidate must be OutputTokenCandidate (got {type(candidate).__name__})"
        )
    if history.token_candidates.get(candidate.token_id) is not candidate:
        raise ValueError(
            "I-OUT-10 violated: learned output token requires registered "
            "OutputTokenCandidate support"
        )

    token = LearnedOutputToken(token_id=candidate.token_id, candidate=candidate)
    learned = dict(history.learned_tokens)
    learned[token.token_id] = token
    return OutputHistory(
        impulses=history.impulses,
        echoes=history.echoes,
        output_patterns=history.output_patterns,
        token_candidates=history.token_candidates,
        learned_tokens=learned,
    )


def observe_proto_output_action_readiness(
    history: OutputHistory,
    candidate: OutputTokenCandidate,
) -> ProtoOutputActionReadiness:
    """Observe local readiness without constructing agency or world semantics."""
    if not isinstance(history, OutputHistory):
        raise TypeError(
            f"history must be OutputHistory (got {type(history).__name__})"
        )
    if not isinstance(candidate, OutputTokenCandidate):
        raise TypeError(
            f"candidate must be OutputTokenCandidate (got {type(candidate).__name__})"
        )

    registered_candidate = history.token_candidates.get(candidate.token_id)
    learned_token = history.learned_tokens.get(candidate.token_id)
    has_recurrence = candidate.support_count >= 2
    has_echo_support = len(candidate.echo_ids) >= candidate.support_count
    ready = (
        registered_candidate is candidate
        and isinstance(learned_token, LearnedOutputToken)
        and learned_token.candidate is candidate
        and has_recurrence
        and has_echo_support
    )
    reason = "local-history-ready" if ready else "local-history-incomplete"

    return ProtoOutputActionReadiness(
        token_id=candidate.token_id,
        pattern_id=candidate.pattern_id,
        support_count=candidate.support_count,
        echo_count=len(candidate.echo_ids),
        source_kinds=candidate.source_kinds,
        ready=ready,
        reason=reason,
    )
