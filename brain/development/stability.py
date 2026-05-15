"""Deterministic stability metric for Phase 3.1."""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from brain.development.drives import clamp_unit
from brain.development.history import SubstrateHistory
from brain.development.stream import FrameSourceKind, PhenomenalFrame

Signature = tuple[tuple[str, str], ...]


def frame_matches_signature(frame: PhenomenalFrame, signature: Signature) -> bool:
    """Return whether a frame contains every signature channel/value pair."""
    if not signature:
        return False
    for channel, expected in signature:
        if channel not in frame.channels:
            return False
        if str(frame.channels[channel]) != expected:
            return False
    return True


def count_frames_matching(
    signature: Signature,
    frames: tuple[PhenomenalFrame, ...],
) -> int:
    return sum(1 for frame in frames if frame_matches_signature(frame, signature))


def _pattern_signature(pattern: Any) -> Signature:
    signature = getattr(pattern, "signature", None)
    if not isinstance(signature, tuple):
        raise TypeError("pattern.signature must be a tuple")
    for item in signature:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not isinstance(item[1], str)
        ):
            raise TypeError("pattern.signature entries must be (channel, value) pairs")
    return signature


def _pattern_source_kinds(pattern: Any) -> frozenset[FrameSourceKind]:
    source_kinds = getattr(pattern, "source_kinds", frozenset())
    if not isinstance(source_kinds, frozenset):
        raise TypeError("pattern.source_kinds must be a frozenset")
    for kind in source_kinds:
        if not isinstance(kind, FrameSourceKind):
            raise TypeError("pattern.source_kinds must contain FrameSourceKind values")
    return source_kinds


def _matching_source_kind_sets(
    pattern: Any,
    frames: tuple[PhenomenalFrame, ...],
    signature: Signature,
) -> int:
    expected_kinds = _pattern_source_kinds(pattern)
    if not expected_kinds:
        return 0
    matches = 0
    for frame in frames:
        if not frame_matches_signature(frame, signature):
            continue
        frame_kinds = frozenset(source.kind for source in frame.sources.values())
        if frame_kinds == expected_kinds:
            matches += 1
    return matches


def stability_v1(pattern: Any, history: SubstrateHistory) -> Fraction:
    """Compute the Phase 3.1 recurrence/source-consistency metric."""
    if not isinstance(history, SubstrateHistory):
        raise TypeError(f"history must be SubstrateHistory (got {type(history).__name__})")

    signature = _pattern_signature(pattern)
    window = history.recent_frames(n=5)
    support = count_frames_matching(signature, window)
    recurrence = Fraction(support, max(1, len(window)))
    source_consistency = Fraction(
        _matching_source_kind_sets(pattern, window, signature),
        max(1, support),
    )
    return clamp_unit(
        Fraction(2, 3) * recurrence
        + Fraction(1, 3) * source_consistency
    )

