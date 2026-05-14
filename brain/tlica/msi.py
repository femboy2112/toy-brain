"""MSI (maximally-self-defined I). Encodes MSI.lean.

Catalog rows owned: I-MSI-01..06 (REQUIRED).

Lean source: ``lean_reference/TLICA/MSI.lean``.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from brain.tlica.profile import COGITO_ID, ContentID, ScalarProfile


@dataclass(frozen=True, slots=True)
class MSI:
    """The maximally-self-defined I.

    Mirrors ``TLICA.MSI.MSI`` (MSI.lean §3.2.1).

    Invariants (raised by ``__post_init__`` per corrigenda C1):
      - I-MSI-01 (cogito_value): ``profile.values[COGITO_ID] == 1``.
      - I-MSI-02 (cogito_in / Axiom 3.3.1): ``COGITO_ID in contents``.
      - I-MSI-03 (density / Axiom 3.3.3): every non-cogito member meets
        ``threshold``.
      - I-MSI-04 (threshold_pos + threshold_lt_one): ``0 < threshold < 1``.
      - All ``contents`` are in ``profile.domain``.

    I-MSI-05 (cogito_is_supremum) and I-MSI-06 (mem_msi_positive) follow
    from the construction-time invariants above; the runner re-asserts
    them per fixture.
    """

    profile: ScalarProfile
    contents: frozenset[ContentID]
    threshold: Fraction

    def __post_init__(self) -> None:
        if not isinstance(self.contents, frozenset):
            raise TypeError(
                "MSI.contents must be a frozenset (got "
                f"{type(self.contents).__name__})"
            )
        if not isinstance(self.threshold, Fraction):
            raise TypeError(
                f"MSI.threshold must be Fraction (got {type(self.threshold).__name__})"
            )
        if not (Fraction(0) < self.threshold < Fraction(1)):
            raise ValueError(
                f"I-MSI-04 violated (threshold_pos / threshold_lt_one): "
                f"threshold {self.threshold} must lie strictly in (0, 1)"
            )
        if COGITO_ID not in self.contents:
            raise ValueError(
                "I-MSI-02 violated (cogito_in / Axiom 3.3.1): "
                f"COGITO_ID ({COGITO_ID!r}) not in contents {set(self.contents)!r}"
            )
        if self.profile.values.get(COGITO_ID) != Fraction(1):
            raise ValueError(
                "I-MSI-01 violated (cogito_value): "
                f"profile.values[COGITO_ID] = "
                f"{self.profile.values.get(COGITO_ID)!r}, must be Fraction(1)"
            )
        for c in self.contents:
            if c not in self.profile.domain:
                raise ValueError(
                    f"MSI.contents includes {c!r} which is not in profile.domain"
                )
            if c == COGITO_ID:
                continue
            v = self.profile.values[c]
            if v < self.threshold:
                raise ValueError(
                    "I-MSI-03 violated (density / Axiom 3.3.3): "
                    f"non-cogito member {c!r} has value {v}, "
                    f"below threshold {self.threshold}"
                )
