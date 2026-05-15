"""Fixtures for unstable one-off noise rejection."""
from __future__ import annotations

from fractions import Fraction

from brain.development.history import SubstrateHistory
from brain.development.proto_content import ProtoContent, maybe_stabilize_proto_content
from brain.development.proto_pattern import update_proto_pattern
from brain.development.stream import FrameSource, FrameSourceKind, PhenomenalFrame
from brain.invariants import register


def _noise_frame() -> PhenomenalFrame:
    return PhenomenalFrame(
        channels={"flash": Fraction(9, 10)},
        sources={
            "flash": FrameSource(
                channel="flash",
                kind=FrameSourceKind.EXTERNAL,
                confidence=Fraction(1, 2),
            )
        },
    )


@register("I-DEV-02", status="REQUIRED")
def check_unstable_one_off_noise_does_not_become_stable_proto_content() -> None:
    history = SubstrateHistory()
    history, pattern = update_proto_pattern(history, _noise_frame())
    history, content = maybe_stabilize_proto_content(
        history,
        pattern,
        salience=Fraction(1),
    )

    assert pattern is None
    assert content is None
    assert history.proto_patterns == {}
    assert history.proto_contents == {}
    assert not any(isinstance(value, ProtoContent) for value in history.proto_contents.values())
