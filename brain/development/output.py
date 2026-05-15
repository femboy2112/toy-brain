"""Output Ladder primitives for Phase 3.2.

The v0.7 output surface is deliberately below language, agency, and runtime
state mutation. It records source-tagged output attempts and echo provenance in
copy-on-write developmental history only.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Mapping

from brain.development.drives import require_unit_fraction
from brain.development.history import TraceEventID, require_printable_id
from brain.development.stream import FrameSourceKind
from brain.tlica.profile import COGITO_ID

OutputEchoID = str
OutputImpulseID = str
OutputPatternID = str
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


@dataclass(frozen=True, slots=True)
class OutputHistory:
    """Immutable output-ladder store below the tick boundary."""

    impulses: tuple[OutputImpulse, ...] = ()
    echoes: tuple[OutputEcho, ...] = ()
    output_patterns: Mapping[OutputPatternID, object] | None = None
    token_candidates: Mapping[OutputTokenID, object] | None = None
    learned_tokens: Mapping[OutputTokenID, object] | None = None

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
        for key in candidates:
            require_printable_id(key, field="OutputHistory.token_candidates key")
        for key in learned:
            require_printable_id(key, field="OutputHistory.learned_tokens key")

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
