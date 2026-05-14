"""PreservationRanking Π. Encodes PreservationRanking.lean.

Catalog rows owned: I-PRES-01..04 (REQUIRED), I-PRES-05 (STRUCTURAL).

Lean source: ``lean_reference/TLICA/PreservationRanking.lean``.

v0 stub signature (cogito-gated) per the README:

    def rank(S: frozenset[ContentID]) -> Fraction:
        if COGITO_ID not in S:
            return Fraction(0)
        return Fraction(len(S & msi.contents), max(1, len(msi.contents)))

This satisfies ``rank_nonneg``, ``cogito_necessity``,
``no_cogito_zero_rank``, ``msi_maximality``, and (by construction over the
simple stub) ``msi_monotonicity``.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from brain.tlica.msi import MSI
from brain.tlica.profile import COGITO_ID, ContentID


@dataclass(frozen=True, slots=True)
class PreservationRanking:
    """Mirrors ``TLICA.PreservationRanking.PreservationRanking``.

    Stub form: rank is cogito-gated and proportional to MSI-share. Per
    catalog: this stub satisfies the foundation axioms by construction
    (4.3.1 cogito necessity, 4.3.2 MSI maximality, 4.3.3 monotonicity).
    """

    msi: MSI

    def rank(self, S: frozenset[ContentID]) -> Fraction:
        """``PreservationRanking.lean::PreservationRanking.rank``.

        Drives I-PRES-01 (rank_nonneg), I-PRES-02 (cogito_necessity, Axiom 4.3.1),
        I-PRES-03 (msi_maximality, Axiom 4.3.2), I-PRES-04 (no_cogito_zero_rank),
        and I-PRES-05 (msi_monotonicity, Axiom 4.3.3 — STRUCTURAL).
        """
        if COGITO_ID not in S:
            return Fraction(0)
        msi_contents = self.msi.contents
        denom = max(1, len(msi_contents))
        return Fraction(len(S & msi_contents), denom)
