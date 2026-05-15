"""Deterministic positive-delta prediction gain for Phase 3.1."""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from brain.development.drives import clamp_unit
from brain.development.history import SubstrateHistory
from brain.development.stability import (
    Signature,
    _pattern_signature,
    frame_matches_signature,
)
from brain.development.stream import PhenomenalFrame


def count_predicted_signature_hits(
    signature: Signature,
    frames: tuple[PhenomenalFrame, ...],
) -> int:
    """Count frames matching the predicted signature."""
    return sum(1 for frame in frames if frame_matches_signature(frame, signature))


def count_predicted_signature_misses(
    signature: Signature,
    frames: tuple[PhenomenalFrame, ...],
) -> int:
    """Count recent frames that do not match a non-empty predicted signature."""
    if not signature:
        return len(frames)
    return sum(1 for frame in frames if not frame_matches_signature(frame, signature))


def prediction_gain_v1(pattern: Any, history: SubstrateHistory) -> Fraction:
    """Compute positive predictive gain above recent-window baseline."""
    if not isinstance(history, SubstrateHistory):
        raise TypeError(f"history must be SubstrateHistory (got {type(history).__name__})")

    signature = _pattern_signature(pattern)
    recent = history.recent_frames(n=5)
    expected_hits = count_predicted_signature_hits(signature, recent)
    false_hits = count_predicted_signature_misses(signature, recent)
    raw_gain = Fraction(expected_hits, max(1, expected_hits + false_hits))
    baseline = Fraction(1, max(1, len(recent)))
    return clamp_unit(raw_gain - baseline)

