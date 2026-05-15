"""Deterministic proto-pattern recurrence for Phase 3.1."""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256

from brain.development.history import PatternID, SubstrateHistory, require_printable_id
from brain.development.stability import Signature, count_frames_matching
from brain.development.stream import FrameSourceKind, PhenomenalFrame


def signature_from_frame(frame: PhenomenalFrame) -> Signature:
    """Build a stable signature from a frame's channel/value pairs."""
    if not isinstance(frame, PhenomenalFrame):
        raise TypeError(f"frame must be PhenomenalFrame (got {type(frame).__name__})")
    return tuple(sorted((channel, str(value)) for channel, value in frame.channels.items()))


def pattern_id_for_signature(signature: Signature) -> PatternID:
    if not signature:
        raise ValueError("ProtoPattern signature must be non-empty")
    digest = sha256(repr(signature).encode("utf-8")).hexdigest()[:16]
    return f"pattern:{digest}"


def source_kinds_for_frame(frame: PhenomenalFrame) -> frozenset[FrameSourceKind]:
    if not isinstance(frame, PhenomenalFrame):
        raise TypeError(f"frame must be PhenomenalFrame (got {type(frame).__name__})")
    return frozenset(source.kind for source in frame.sources.values())


@dataclass(frozen=True, slots=True)
class ProtoPattern:
    """A recurring pre-content signature below the TLICA promotion boundary."""

    pattern_id: PatternID
    signature: Signature
    support_count: int
    source_kinds: frozenset[FrameSourceKind]
    first_seen_index: int
    last_seen_index: int

    def __post_init__(self) -> None:
        require_printable_id(self.pattern_id, field="ProtoPattern.pattern_id")
        if not isinstance(self.signature, tuple) or not self.signature:
            raise ValueError("ProtoPattern.signature must be a non-empty tuple")
        for channel, value in self.signature:
            require_printable_id(channel, field="ProtoPattern.signature channel")
            require_printable_id(value, field="ProtoPattern.signature value")
        if not isinstance(self.support_count, int) or self.support_count < 1:
            raise ValueError("ProtoPattern.support_count must be a positive integer")
        if not isinstance(self.source_kinds, frozenset) or not self.source_kinds:
            raise ValueError("ProtoPattern.source_kinds must be a non-empty frozenset")
        for kind in self.source_kinds:
            if not isinstance(kind, FrameSourceKind):
                raise TypeError("ProtoPattern.source_kinds must contain FrameSourceKind values")
        if (
            not isinstance(self.first_seen_index, int)
            or not isinstance(self.last_seen_index, int)
            or self.first_seen_index < 0
            or self.last_seen_index < self.first_seen_index
        ):
            raise ValueError("ProtoPattern seen indices must be ordered non-negative integers")

    def with_observation(
        self,
        *,
        support_count: int,
        source_kinds: frozenset[FrameSourceKind],
        last_seen_index: int,
    ) -> "ProtoPattern":
        return replace(
            self,
            support_count=support_count,
            source_kinds=source_kinds,
            last_seen_index=last_seen_index,
        )


def update_proto_pattern(
    history: SubstrateHistory,
    frame: PhenomenalFrame,
    *,
    min_support: int = 2,
) -> tuple[SubstrateHistory, ProtoPattern | None]:
    """Append a frame and create/update a pattern only after recurrence."""
    if not isinstance(history, SubstrateHistory):
        raise TypeError(f"history must be SubstrateHistory (got {type(history).__name__})")
    if not isinstance(min_support, int) or min_support < 2:
        raise ValueError("min_support must be an integer >= 2")

    next_history = history.with_frame(frame)
    signature = signature_from_frame(frame)
    support = count_frames_matching(signature, next_history.frames)
    if support < min_support:
        return next_history, None

    pattern_id = pattern_id_for_signature(signature)
    last_seen = len(next_history.frames) - 1
    first_seen = next(
        index
        for index, candidate in enumerate(next_history.frames)
        if signature_from_frame(candidate) == signature
    )
    source_kinds = source_kinds_for_frame(frame)
    existing = next_history.proto_patterns.get(pattern_id)
    if isinstance(existing, ProtoPattern):
        pattern = existing.with_observation(
            support_count=support,
            source_kinds=source_kinds,
            last_seen_index=last_seen,
        )
    else:
        pattern = ProtoPattern(
            pattern_id=pattern_id,
            signature=signature,
            support_count=support,
            source_kinds=source_kinds,
            first_seen_index=first_seen,
            last_seen_index=last_seen,
        )

    patterns = dict(next_history.proto_patterns)
    patterns[pattern_id] = pattern
    return (
        SubstrateHistory(
            frames=next_history.frames,
            proto_patterns=patterns,
            proto_contents=next_history.proto_contents,
        ),
        pattern,
    )
