"""Fixtures for Phase 3.2 output recurrence rows."""
from __future__ import annotations

from fractions import Fraction

from brain.development.output import (
    OutputHistory,
    OutputImpulse,
    OutputPattern,
    OutputProvenance,
    pattern_id_for_output_signature,
    output_signature_from_impulse,
    update_output_pattern,
)
from brain.development.stream import FrameSourceKind
from brain.invariants import register


def _provenance() -> OutputProvenance:
    return OutputProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(4, 5),
        trace_event_ids=("output:pattern-trace",),
    )


def _impulse(suffix: str, *, text: str = "pulse") -> OutputImpulse:
    return OutputImpulse(
        impulse_id=f"out:pattern-{suffix}",
        text=text,
        provenance=_provenance(),
    )


@register("I-OUT-06", status="REQUIRED")
def check_one_off_output_noise_does_not_become_pattern() -> None:
    history, pattern = update_output_pattern(OutputHistory(), _impulse("one"))
    assert pattern is None
    assert len(history.impulses) == 1
    assert history.output_patterns == {}
    assert history.token_candidates == {}
    assert history.learned_tokens == {}


@register("I-OUT-07", status="REQUIRED")
def check_repeated_output_impulses_create_or_update_pattern() -> None:
    first = _impulse("one")
    second = _impulse("two")
    history = OutputHistory()

    history, one_off = update_output_pattern(history, first)
    assert one_off is None

    history, pattern = update_output_pattern(history, second)
    assert isinstance(pattern, OutputPattern)
    assert pattern.support_count == 2
    assert pattern.signature == output_signature_from_impulse(first)
    assert pattern.pattern_id == pattern_id_for_output_signature(pattern.signature)
    assert pattern.impulse_ids == (first.impulse_id, second.impulse_id)
    assert pattern.first_seen_index == 0
    assert pattern.last_seen_index == 1
    assert history.output_patterns[pattern.pattern_id] is pattern
    assert history.token_candidates == {}
    assert history.learned_tokens == {}

    third = _impulse("three")
    history, updated = update_output_pattern(history, third)
    assert isinstance(updated, OutputPattern)
    assert updated.pattern_id == pattern.pattern_id
    assert updated.support_count == 3
    assert updated.impulse_ids == (
        first.impulse_id,
        second.impulse_id,
        third.impulse_id,
    )
    assert updated.last_seen_index == 2
