"""Source-tagged phenomenal frames for Phase 3.1.

This module is deliberately narrow: it models the deterministic frame/source
boundary needed before later developmental substrate rows can reason about
history, recurrence, probes, or promotion.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from types import MappingProxyType
from typing import Mapping


class FrameSourceKind(str, Enum):
    """Active Phase 3.1 source kinds."""

    ENDOGENOUS = "endogenous"
    OPERATOR_INJECTION = "operator_injection"
    PROBE_ECHO = "probe_echo"
    EXTERNAL = "external"
    GENERATED = "generated"


@dataclass(frozen=True, slots=True)
class FrameSource:
    """Provenance tag for exactly one phenomenal-frame channel."""

    channel: str
    kind: FrameSourceKind
    confidence: Fraction

    def __post_init__(self) -> None:
        if not isinstance(self.channel, str) or not self.channel:
            raise ValueError(
                "I-FRAME-03 violated: FrameSource.channel must be a non-empty string"
            )
        if not isinstance(self.kind, FrameSourceKind):
            raise TypeError(
                "FrameSource.kind must be a FrameSourceKind "
                f"(got {type(self.kind).__name__})"
            )
        if not isinstance(self.confidence, Fraction):
            raise ValueError(
                "I-FRAME-02 violated: FrameSource.confidence must be a Fraction"
            )
        if not (Fraction(0) <= self.confidence <= Fraction(1)):
            raise ValueError(
                "I-FRAME-02 violated: FrameSource.confidence must be in [0, 1]"
            )


@dataclass(frozen=True, slots=True)
class PhenomenalFrame:
    """A deterministic collection of channel values with exact source tags."""

    channels: Mapping[str, object]
    sources: Mapping[str, FrameSource]

    def __post_init__(self) -> None:
        channels = dict(self.channels)
        sources = dict(self.sources)

        if not channels:
            raise ValueError(
                "I-FRAME-03 violated: PhenomenalFrame.channels must be non-empty"
            )
        if any(not isinstance(k, str) or not k for k in channels):
            raise ValueError(
                "I-FRAME-03 violated: every frame channel key must be non-empty"
            )
        if not sources:
            raise ValueError(
                "I-FRAME-03 violated: PhenomenalFrame.sources must be non-empty"
            )
        for key, source in sources.items():
            if not isinstance(key, str) or not key:
                raise ValueError(
                    "I-FRAME-03 violated: every source key must be non-empty"
                )
            if not isinstance(source, FrameSource):
                raise TypeError(
                    "PhenomenalFrame.sources values must be FrameSource "
                    f"(got {type(source).__name__})"
                )
            if source.channel != key:
                raise ValueError(
                    "I-FRAME-03 violated: source key must match source.channel"
                )

        channel_keys = set(channels)
        source_keys = set(sources)
        if channel_keys != source_keys:
            missing = sorted(channel_keys - source_keys)
            extra = sorted(source_keys - channel_keys)
            raise ValueError(
                "I-FRAME-03 violated: frame channels and source tags must match "
                f"exactly (missing={missing}, extra={extra})"
            )

        object.__setattr__(self, "channels", MappingProxyType(channels))
        object.__setattr__(self, "sources", MappingProxyType(sources))

