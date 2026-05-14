"""ScalarProfile + zero-extension. Encodes Profile.lean.

Catalog rows owned: I-PROF-01..07 (REQUIRED).

Lean source: ``lean_reference/TLICA/Profile.lean``.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Mapping, NewType

ContentID = NewType("ContentID", str)
Rho = Fraction

# Reserved sentinel for the cogito. Chosen so that user input — which
# normalizes through `brain.io_types.PerceptEvent` — cannot collide with it
# (I-RT-01 refuses any percept event whose ``content_id`` equals COGITO_ID).
COGITO_ID: ContentID = ContentID("__cogito__")


@dataclass(frozen=True, slots=True)
class ScalarProfile:
    """A scalar identity-correlation profile on a content domain.

    Mirrors ``TLICA.Profile.ScalarProfile`` (Profile.lean §4.1.1): a
    ``Set α`` domain together with a value function into ``[0, 1]``.

    Invariants (raised by ``__post_init__``):
      - ``domain == set(values)`` — keys agree with the declared domain.
      - Every ``v in values.values()`` is a ``Fraction`` in ``[0, 1]``.
        This is the construction-time encoding of
        ``Profile.lean::ScalarProfile.toFun_nonneg`` (I-PROF-01) and
        ``toFun_le_one`` (I-PROF-02). The runtime runner re-asserts the
        same predicates per fixture; both layers must pass.

    Values are stored behind a ``MappingProxyType`` so callers cannot mutate
    the underlying dict.
    """

    domain: frozenset[ContentID]
    values: Mapping[ContentID, Fraction]

    def __post_init__(self) -> None:
        if not isinstance(self.domain, frozenset):
            raise TypeError(
                "ScalarProfile.domain must be a frozenset (got "
                f"{type(self.domain).__name__})"
            )
        if not isinstance(self.values, MappingProxyType):
            object.__setattr__(self, "values", MappingProxyType(dict(self.values)))
        if set(self.values.keys()) != self.domain:
            raise ValueError(
                f"ScalarProfile: values keys {set(self.values)!r} do not match "
                f"domain {set(self.domain)!r}"
            )
        for k, v in self.values.items():
            if not isinstance(v, Fraction):
                raise TypeError(
                    f"ScalarProfile: value for {k!r} must be Fraction "
                    f"(got {type(v).__name__})"
                )
            if v < 0:
                raise ValueError(
                    f"I-PROF-01 violated (toFun_nonneg): "
                    f"value for {k!r} is {v}, must be >= 0"
                )
            if v > 1:
                raise ValueError(
                    f"I-PROF-02 violated (toFun_le_one): "
                    f"value for {k!r} is {v}, must be <= 1"
                )

    def zero_extend(self, x: ContentID) -> Fraction:
        """Zero-extension to the universal content domain (Profile.lean §5.2bis).

        Returns ``self.values[x]`` if ``x ∈ domain``, otherwise ``Fraction(0)``.
        Drives I-PROF-03 (zeroExtend_of_mem) and I-PROF-04 (zeroExtend_of_not_mem).
        """
        if x in self.domain:
            return self.values[x]
        return Fraction(0)
