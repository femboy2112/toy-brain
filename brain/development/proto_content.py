"""Stable proto-content candidates for Phase 3.1."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256

from brain.development.drives import require_unit_fraction
from brain.development.history import (
    DevContentID,
    PatternID,
    SubstrateHistory,
    TraceEventID,
    require_printable_id,
)
from brain.development.prediction_gain import prediction_gain_v1
from brain.development.proto_pattern import ProtoPattern
from brain.development.stability import Signature, stability_v1
from brain.development.stream import FrameSourceKind


def content_id_for_pattern(pattern: ProtoPattern) -> DevContentID:
    if not isinstance(pattern, ProtoPattern):
        raise TypeError(f"pattern must be ProtoPattern (got {type(pattern).__name__})")
    digest = sha256(pattern.pattern_id.encode("utf-8")).hexdigest()[:16]
    return f"dev:{digest}"


@dataclass(frozen=True, slots=True)
class PromotionProvenance:
    """Evidence trail for a proto-content candidate before promotion."""

    pattern_id: PatternID
    source_kinds: frozenset[FrameSourceKind]
    trace_event_ids: tuple[TraceEventID, ...] = ()

    def __post_init__(self) -> None:
        require_printable_id(self.pattern_id, field="PromotionProvenance.pattern_id")
        if not isinstance(self.source_kinds, frozenset) or not self.source_kinds:
            raise ValueError("PromotionProvenance.source_kinds must be a non-empty frozenset")
        for kind in self.source_kinds:
            if not isinstance(kind, FrameSourceKind):
                raise TypeError(
                    "PromotionProvenance.source_kinds must contain FrameSourceKind values"
                )
        if not isinstance(self.trace_event_ids, tuple):
            raise TypeError("PromotionProvenance.trace_event_ids must be a tuple")
        for event_id in self.trace_event_ids:
            require_printable_id(event_id, field="PromotionProvenance.trace_event_id")


@dataclass(frozen=True, slots=True)
class ProtoContent:
    """Stable developmental content candidate below the tick boundary."""

    content_id: DevContentID
    pattern_id: PatternID
    signature: Signature
    salience: Fraction
    stability: Fraction
    prediction_gain: Fraction
    provenance: PromotionProvenance

    def __post_init__(self) -> None:
        require_printable_id(self.content_id, field="ProtoContent.content_id")
        require_printable_id(self.pattern_id, field="ProtoContent.pattern_id")
        if not isinstance(self.signature, tuple) or not self.signature:
            raise ValueError("ProtoContent.signature must be a non-empty tuple")
        require_unit_fraction(self.salience, field="ProtoContent.salience")
        require_unit_fraction(self.stability, field="ProtoContent.stability")
        require_unit_fraction(self.prediction_gain, field="ProtoContent.prediction_gain")
        if not isinstance(self.provenance, PromotionProvenance):
            raise TypeError("ProtoContent.provenance must be PromotionProvenance")
        if self.provenance.pattern_id != self.pattern_id:
            raise ValueError("ProtoContent provenance must reference the same pattern")

    @property
    def eligible_for_promotion(self) -> bool:
        return self.stability > Fraction(0) and self.prediction_gain > Fraction(0)


def maybe_stabilize_proto_content(
    history: SubstrateHistory,
    pattern: ProtoPattern | None,
    *,
    salience: Fraction,
    trace_event_ids: tuple[TraceEventID, ...] = (),
    min_stability: Fraction = Fraction(1, 2),
    min_prediction_gain: Fraction = Fraction(1, 10),
) -> tuple[SubstrateHistory, ProtoContent | None]:
    """Create stable proto-content only when recurrence metrics pass."""
    if not isinstance(history, SubstrateHistory):
        raise TypeError(f"history must be SubstrateHistory (got {type(history).__name__})")
    require_unit_fraction(salience, field="salience")
    require_unit_fraction(min_stability, field="min_stability")
    require_unit_fraction(min_prediction_gain, field="min_prediction_gain")
    if not isinstance(trace_event_ids, tuple):
        raise TypeError("trace_event_ids must be a tuple")
    for event_id in trace_event_ids:
        require_printable_id(event_id, field="trace_event_ids item")
    if pattern is None:
        return history, None
    if not isinstance(pattern, ProtoPattern):
        raise TypeError(f"pattern must be ProtoPattern or None (got {type(pattern).__name__})")

    stability = stability_v1(pattern, history)
    prediction_gain = prediction_gain_v1(pattern, history)
    if stability < min_stability or prediction_gain < min_prediction_gain:
        return history, None

    content = ProtoContent(
        content_id=content_id_for_pattern(pattern),
        pattern_id=pattern.pattern_id,
        signature=pattern.signature,
        salience=salience,
        stability=stability,
        prediction_gain=prediction_gain,
        provenance=PromotionProvenance(
            pattern_id=pattern.pattern_id,
            source_kinds=pattern.source_kinds,
            trace_event_ids=trace_event_ids,
        ),
    )
    contents = dict(history.proto_contents)
    contents[content.content_id] = content
    return (
        SubstrateHistory(
            frames=history.frames,
            proto_patterns=history.proto_patterns,
            proto_contents=contents,
        ),
        content,
    )
