"""Pointwise (L^∞) profile distances. Encodes Pointwise.lean.

Catalog rows owned: I-PWS-01..10 (REQUIRED).

Lean source: ``lean_reference/TLICA/ProfileComparison/Pointwise.lean``.

Per catalog: ``math.inf`` (the single permitted float) represents Lean's
``⊤`` for empty-shared-domain ``dInfShared``. All other distance values
remain ``Fraction``.
"""
from __future__ import annotations

import math
from fractions import Fraction

from brain.tlica.profile import ScalarProfile


def d_inf_union(f: ScalarProfile, g: ScalarProfile) -> Fraction:
    """``Pointwise.lean::dInfUnion``.

    Supremum of |f - g| over ``f.domain ∪ g.domain`` using zero-extension.
    Always ``Fraction``-valued; empty union yields ``Fraction(0)``.
    """
    universe = f.domain | g.domain
    if not universe:
        return Fraction(0)
    return max(abs(f.zero_extend(x) - g.zero_extend(x)) for x in universe)


def d_inf_shared(f: ScalarProfile, g: ScalarProfile) -> Fraction | float:
    """``Pointwise.lean::dInfShared``.

    Supremum of |f - g| over the shared domain. Empty shared domain
    returns ``math.inf`` (Lean's ``⊤``); otherwise a ``Fraction``.
    """
    shared = f.domain & g.domain
    if not shared:
        return math.inf
    return max(abs(f.zero_extend(x) - g.zero_extend(x)) for x in shared)
