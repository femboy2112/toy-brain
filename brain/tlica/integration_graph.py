"""Integration graph strict ρ-bound. Encodes IntegrationGraph.lean.

Catalog rows owned: I-INT-01..02 (REQUIRED).

Lean source: ``lean_reference/TLICA/IntegrationGraph.lean``.
"""
from __future__ import annotations

from fractions import Fraction


def rho_normalization(C: Fraction) -> Fraction:
    """``IntegrationGraph.lean::strict_rho_bound``: ρ(C) = C / (1 + C).

    Drives I-INT-01 (``C >= 0 ⇒ C / (1 + C) < 1``) and I-INT-02
    (``C >= 0 ⇒ C / (1 + C) >= 0``). Both verified under sampling by the
    ``profile_distance.py`` fixture.
    """
    if C < 0:
        raise ValueError(f"rho_normalization expects C >= 0, got {C}")
    return C / (Fraction(1) + C)
