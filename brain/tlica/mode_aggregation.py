"""Mode-aggregation series (NOT-EXERCISED in v0).

Lean source: ``lean_reference/TLICA/ModeAggregation.lean``.

Lean covers Proposition 2.5.1 (convergence of the mode-aggregation series).
v0 commits to finite-at-each-tick; no invariant depends on convergence.
This module exposes a truncated helper for fixture convenience only.
"""
from __future__ import annotations

from fractions import Fraction
from collections.abc import Callable


def finite_mode_aggregation(
    terms: Callable[[int], Fraction], n: int
) -> Fraction:
    """Truncated finite sum ``sum(terms(k) for k in range(n))``.

    Surface-level helper. No catalog row drives this in v0.
    """
    if n < 0:
        raise ValueError(f"finite_mode_aggregation expects n >= 0, got {n}")
    total = Fraction(0)
    for k in range(n):
        total += terms(k)
    return total
