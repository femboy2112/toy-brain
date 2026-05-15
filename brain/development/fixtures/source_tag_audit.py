"""Phase 3.1 source-tag fixture.

Drives:
  - I-FRAME-01: every frame channel has exactly one source tag.
  - I-FRAME-02: source confidence is an exact Fraction in [0, 1].
  - I-FRAME-03: invalid source coverage raises at construction.
  - I-FRAME-04: active source kinds are the Phase 3.1 set only.
"""
from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction

from brain.development.stream import (
    FrameSource,
    FrameSourceKind,
    PhenomenalFrame,
)
from brain.invariants import register


def _source(
    channel: str,
    kind: FrameSourceKind,
    confidence: Fraction = Fraction(1),
) -> FrameSource:
    return FrameSource(channel=channel, kind=kind, confidence=confidence)


def _valid_frame() -> PhenomenalFrame:
    return PhenomenalFrame(
        channels={
            "visual": "red point",
            "interoceptive": "steady pulse",
            "probe": "similarity echo",
        },
        sources={
            "visual": _source("visual", FrameSourceKind.EXTERNAL, Fraction(4, 5)),
            "interoceptive": _source(
                "interoceptive",
                FrameSourceKind.ENDOGENOUS,
                Fraction(1),
            ),
            "probe": _source("probe", FrameSourceKind.PROBE_ECHO, Fraction(1, 2)),
        },
    )


def _assert_raises_i_frame_03(call: Callable[[], object]) -> None:
    try:
        call()
    except ValueError as exc:
        assert "I-FRAME-03" in str(exc), (
            f"source-tag construction failure did not name I-FRAME-03: {exc!r}"
        )
    else:
        raise AssertionError("I-FRAME-03 violated: invalid frame construction passed")


def _assert_raises_i_frame_02(call: Callable[[], object]) -> None:
    try:
        call()
    except ValueError as exc:
        assert "I-FRAME-02" in str(exc), (
            f"confidence validation failure did not name I-FRAME-02: {exc!r}"
        )
    else:
        raise AssertionError("I-FRAME-02 violated: invalid confidence passed")


@register("I-FRAME-01", status="STRUCTURAL")
def check_I_FRAME_01() -> None:
    """Every channel in a valid frame has exactly one source tag."""
    frame = _valid_frame()
    assert set(frame.channels) == set(frame.sources), (
        "I-FRAME-01 violated: channel/source key sets differ"
    )
    assert len(frame.channels) == len(frame.sources), (
        "I-FRAME-01 violated: source tag count differs from channel count"
    )
    for channel, source in frame.sources.items():
        assert source.channel == channel, (
            f"I-FRAME-01 violated: source for {channel!r} points at "
            f"{source.channel!r}"
        )


@register("I-FRAME-02", status="STRUCTURAL")
def check_I_FRAME_02() -> None:
    """Source confidence stays exact and normalized."""
    frame = _valid_frame()
    for source in frame.sources.values():
        assert isinstance(source.confidence, Fraction), (
            "I-FRAME-02 violated: source confidence is not a Fraction"
        )
        assert Fraction(0) <= source.confidence <= Fraction(1), (
            f"I-FRAME-02 violated: confidence out of range: {source.confidence}"
        )

    _assert_raises_i_frame_02(
        lambda: FrameSource(
            channel="bad",
            kind=FrameSourceKind.EXTERNAL,
            confidence=0.5,
        )
    )
    _assert_raises_i_frame_02(
        lambda: FrameSource(
            channel="bad",
            kind=FrameSourceKind.EXTERNAL,
            confidence=Fraction(-1, 3),
        )
    )
    _assert_raises_i_frame_02(
        lambda: FrameSource(
            channel="bad",
            kind=FrameSourceKind.EXTERNAL,
            confidence=Fraction(4, 3),
        )
    )


@register("I-FRAME-03", status="REQUIRED")
def check_I_FRAME_03() -> None:
    """Missing, extra, empty, and mismatched source tags are rejected."""
    _assert_raises_i_frame_03(
        lambda: PhenomenalFrame(
            channels={"visual": "red point", "audio": "tone"},
            sources={"visual": _source("visual", FrameSourceKind.EXTERNAL)},
        )
    )
    _assert_raises_i_frame_03(
        lambda: PhenomenalFrame(
            channels={"visual": "red point"},
            sources={
                "visual": _source("visual", FrameSourceKind.EXTERNAL),
                "extra": _source("extra", FrameSourceKind.GENERATED),
            },
        )
    )
    _assert_raises_i_frame_03(
        lambda: PhenomenalFrame(
            channels={"visual": "red point"},
            sources={},
        )
    )
    _assert_raises_i_frame_03(
        lambda: PhenomenalFrame(
            channels={"visual": "red point"},
            sources={"visual": _source("audio", FrameSourceKind.EXTERNAL)},
        )
    )
    _assert_raises_i_frame_03(
        lambda: FrameSource(
            channel="",
            kind=FrameSourceKind.EXTERNAL,
            confidence=Fraction(1),
        )
    )


@register("I-FRAME-04", status="STRUCTURAL")
def check_I_FRAME_04() -> None:
    """The active source-kind enum is exactly the Phase 3.1 set."""
    assert {kind.name for kind in FrameSourceKind} == {
        "ENDOGENOUS",
        "OPERATOR_INJECTION",
        "PROBE_ECHO",
        "EXTERNAL",
        "GENERATED",
    }, "I-FRAME-04 violated: active source-kind names drifted"
    assert {kind.value for kind in FrameSourceKind} == {
        "endogenous",
        "operator_injection",
        "probe_echo",
        "external",
        "generated",
    }, "I-FRAME-04 violated: active source-kind values drifted"
