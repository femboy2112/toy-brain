"""Fixtures for Phase 3.1 proto-pattern recurrence rows."""
from __future__ import annotations

from fractions import Fraction

from brain.development.history import SubstrateHistory
from brain.development.proto_content import ProtoContent
from brain.development.proto_pattern import (
    ProtoPattern,
    pattern_id_for_signature,
    signature_from_frame,
    update_proto_pattern,
)
from brain.development.stream import FrameSource, FrameSourceKind, PhenomenalFrame
from brain.invariants import register


def _frame(value: Fraction) -> PhenomenalFrame:
    return PhenomenalFrame(
        channels={"warmth": value},
        sources={
            "warmth": FrameSource(
                channel="warmth",
                kind=FrameSourceKind.ENDOGENOUS,
                confidence=Fraction(1),
            )
        },
    )


@register("I-DEV-01", status="REQUIRED")
def check_recurring_signature_creates_or_updates_proto_pattern() -> None:
    first = _frame(Fraction(3, 5))
    second = _frame(Fraction(3, 5))
    history = SubstrateHistory()

    history, one_off = update_proto_pattern(history, first)
    assert one_off is None
    assert history.proto_patterns == {}
    assert history.proto_contents == {}

    history, pattern = update_proto_pattern(history, second)
    assert isinstance(pattern, ProtoPattern)
    assert pattern.support_count == 2
    assert pattern.signature == signature_from_frame(first)
    assert pattern.pattern_id == pattern_id_for_signature(pattern.signature)
    assert history.proto_patterns[pattern.pattern_id] is pattern
    assert not any(isinstance(value, ProtoContent) for value in history.proto_contents.values())

    history, updated = update_proto_pattern(history, second)
    assert isinstance(updated, ProtoPattern)
    assert updated.pattern_id == pattern.pattern_id
    assert updated.support_count == 3
    assert updated.last_seen_index == 2
