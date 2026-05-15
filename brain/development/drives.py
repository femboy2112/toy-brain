"""Deterministic substrate drives for Phase 3.1."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction


def require_unit_fraction(value: Fraction, *, field: str) -> Fraction:
    """Validate a supplied normalized score.

    Constructors use this helper to reject invalid state. Metric functions may
    clamp their computed outputs, but object construction should not silently
    repair caller-supplied scores.
    """
    if not isinstance(value, Fraction):
        raise TypeError(f"{field} must be a Fraction (got {type(value).__name__})")
    if not (Fraction(0) <= value <= Fraction(1)):
        raise ValueError(f"{field} must be in [0, 1] (got {value})")
    return value


def clamp_unit(value: Fraction) -> Fraction:
    """Clamp a computed metric output into the normalized unit interval."""
    if not isinstance(value, Fraction):
        raise TypeError(
            f"computed metric value must be a Fraction (got {type(value).__name__})"
        )
    if value < 0:
        return Fraction(0)
    if value > 1:
        return Fraction(1)
    return value


def mean(values: tuple[Fraction, ...]) -> Fraction:
    """Exact mean with empty input treated as zero."""
    if any(not isinstance(v, Fraction) for v in values):
        raise TypeError("mean expects only Fraction values")
    return sum(values, Fraction(0)) / max(1, len(values))


@dataclass(frozen=True, slots=True)
class SubstrateDrives:
    """Normalized deterministic drives used by Phase 3.1 metrics."""

    salience_bias: Fraction
    novelty_bias: Fraction
    stability_bias: Fraction
    focus_bias: Fraction

    def __post_init__(self) -> None:
        for field in (
            "salience_bias",
            "novelty_bias",
            "stability_bias",
            "focus_bias",
        ):
            require_unit_fraction(getattr(self, field), field=f"SubstrateDrives.{field}")

    @classmethod
    def neutral(cls) -> "SubstrateDrives":
        return cls(
            salience_bias=Fraction(0),
            novelty_bias=Fraction(0),
            stability_bias=Fraction(0),
            focus_bias=Fraction(0),
        )

