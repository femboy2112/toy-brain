"""Developmental substrate history for Phase 3.1."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from brain.development.stream import PhenomenalFrame

DevContentID = str
FrameID = str
PatternID = str
TraceEventID = str


def require_printable_id(value: str, *, field: str) -> str:
    """Validate non-empty printable developmental identifiers."""
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string (got {type(value).__name__})")
    if not value or not value.strip() or not value.isprintable():
        raise ValueError(f"{field} must be non-empty and printable")
    return value


@dataclass(frozen=True, slots=True)
class SubstrateHistory:
    """Immutable frame/proto-pattern/proto-content store below promotion."""

    frames: tuple[PhenomenalFrame, ...] = ()
    proto_patterns: Mapping[PatternID, object] | None = None
    proto_contents: Mapping[DevContentID, object] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.frames, tuple):
            raise TypeError("SubstrateHistory.frames must be a tuple")
        for frame in self.frames:
            if not isinstance(frame, PhenomenalFrame):
                raise TypeError(
                    "SubstrateHistory.frames must contain PhenomenalFrame values "
                    f"(got {type(frame).__name__})"
                )

        patterns = dict(self.proto_patterns or {})
        contents = dict(self.proto_contents or {})
        for key in patterns:
            require_printable_id(key, field="SubstrateHistory.proto_patterns key")
        for key in contents:
            require_printable_id(key, field="SubstrateHistory.proto_contents key")

        object.__setattr__(self, "proto_patterns", MappingProxyType(patterns))
        object.__setattr__(self, "proto_contents", MappingProxyType(contents))

    def with_frame(self, frame: PhenomenalFrame) -> "SubstrateHistory":
        if not isinstance(frame, PhenomenalFrame):
            raise TypeError(
                f"SubstrateHistory.with_frame expects PhenomenalFrame (got {type(frame).__name__})"
            )
        return SubstrateHistory(
            frames=self.frames + (frame,),
            proto_patterns=self.proto_patterns,
            proto_contents=self.proto_contents,
        )

    def recent_frames(self, *, n: int = 5) -> tuple[PhenomenalFrame, ...]:
        if not isinstance(n, int) or n <= 0:
            raise ValueError("recent frame count must be a positive integer")
        return self.frames[-n:]

