"""Deterministic salience metric for Phase 3.1."""
from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction

from brain.development.drives import SubstrateDrives, clamp_unit, mean
from brain.development.stream import FrameSourceKind, PhenomenalFrame


def _channel_values(frame: PhenomenalFrame) -> tuple[Fraction, ...]:
    values: list[Fraction] = []
    for value in frame.channels.values():
        if isinstance(value, Fraction):
            values.append(value)
        elif isinstance(value, Mapping):
            for nested in value.values():
                if not isinstance(nested, Fraction):
                    raise TypeError(
                        "salience_v1 expects Fraction channel values "
                        f"(got {type(nested).__name__})"
                    )
                values.append(nested)
        else:
            raise TypeError(
                "salience_v1 expects Fraction channel values "
                f"(got {type(value).__name__})"
            )
    return tuple(values)


def salience_v1(frame: PhenomenalFrame, drives: SubstrateDrives) -> Fraction:
    """Compute the Phase 3.1 salience engineering metric."""
    if not isinstance(frame, PhenomenalFrame):
        raise TypeError(f"frame must be PhenomenalFrame (got {type(frame).__name__})")
    if not isinstance(drives, SubstrateDrives):
        raise TypeError(f"drives must be SubstrateDrives (got {type(drives).__name__})")

    channel_energy = mean(tuple(abs(value) for value in _channel_values(frame)))
    source_diversity = Fraction(
        len({source.kind for source in frame.sources.values()}),
        len(FrameSourceKind),
    )
    return clamp_unit(
        Fraction(1, 2) * channel_energy
        + Fraction(1, 4) * source_diversity
        + Fraction(1, 4) * drives.salience_bias
    )

