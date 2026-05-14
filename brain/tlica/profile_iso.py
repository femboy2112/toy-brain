"""Optional profile coherence relation. Encodes ProfileIso.lean.

Catalog rows owned: I-ISO-01..03 (all STRUCTURAL).

Lean source: ``lean_reference/TLICA/ProfileIso.lean``.

The Lean records refl/symm/trans as theorems. In Python we expose builders
that return a witness object; the catalog marks all three rows STRUCTURAL,
meaning their correctness is type-enforced at construction and not
exercised per-tick.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from brain.tlica.profile import ScalarProfile


@dataclass(frozen=True, slots=True)
class ProfileIso:
    """A coherence witness between two profiles. Surface-only in v0."""

    lhs: ScalarProfile
    rhs: ScalarProfile

    @classmethod
    def refl(cls, P: ScalarProfile) -> Self:
        return cls(lhs=P, rhs=P)

    def symm(self) -> "ProfileIso":
        return ProfileIso(lhs=self.rhs, rhs=self.lhs)

    @classmethod
    def trans(cls, h1: "ProfileIso", h2: "ProfileIso") -> "ProfileIso":
        if h1.rhs is not h2.lhs and not (
            h1.rhs.domain == h2.lhs.domain
            and all(h1.rhs.values[k] == h2.lhs.values[k] for k in h1.rhs.domain)
        ):
            raise ValueError(
                "ProfileIso.trans: middle profiles do not match "
                "(h1.rhs vs h2.lhs)"
            )
        return cls(lhs=h1.lhs, rhs=h2.rhs)
