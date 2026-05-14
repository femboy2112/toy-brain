"""PtCns + ConsistencyEval. Encodes PtCns.lean.

Catalog rows owned: I-PTC-01..05 (REQUIRED).

Lean source: ``lean_reference/TLICA/PtCns.lean``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from brain.tlica.msi import MSI
from brain.tlica.profile import COGITO_ID, ContentID


class ConsistencyEval(Enum):
    """Three-element consistency-evaluation space.

    Mirrors ``TLICA.PtCns.ConsistencyEval``:
      - ``DAMAGE``   ↔ ``-1`` ↔ Mode A (differentiation).
      - ``NEUTRAL``  ↔  ``0`` ↔ Neutral encapsulation.
      - ``PRESERVE`` ↔ ``+1`` ↔ Mode C (integration).
    """

    DAMAGE = "damage"
    NEUTRAL = "neutral"
    PRESERVE = "preserve"


@dataclass(frozen=True, slots=True)
class PtCns:
    """Prerogative of consistency.

    Mirrors ``TLICA.PtCns.PtCns`` (PtCns.lean §7.2.1).

    Invariants (raised by ``__post_init__`` per corrigenda C1):
      - I-PTC-01 (cogito_invariance / Axiom 7.3.1):
        ``eval_map[COGITO_ID] == PRESERVE``.
      - ``set(eval_map) == set(msi.profile.domain)`` — eval is a total
        function over the profile's domain (also drives I-RT-04 at tick
        time).
    """

    msi: MSI
    eval_map: Mapping[ContentID, ConsistencyEval]

    def __post_init__(self) -> None:
        if not isinstance(self.eval_map, MappingProxyType):
            object.__setattr__(
                self, "eval_map", MappingProxyType(dict(self.eval_map))
            )
        if set(self.eval_map.keys()) != self.msi.profile.domain:
            raise ValueError(
                "PtCns.eval_map keys must equal msi.profile.domain "
                f"(got keys {set(self.eval_map)!r}, "
                f"domain {set(self.msi.profile.domain)!r})"
            )
        for x, e in self.eval_map.items():
            if not isinstance(e, ConsistencyEval):
                raise TypeError(
                    f"PtCns.eval_map[{x!r}] must be ConsistencyEval "
                    f"(got {type(e).__name__})"
                )
        if self.eval_map.get(COGITO_ID) is not ConsistencyEval.PRESERVE:
            raise ValueError(
                "I-PTC-01 violated (cogito_invariance / Axiom 7.3.1): "
                f"eval_map[COGITO_ID] = {self.eval_map.get(COGITO_ID)!r}, "
                "must be ConsistencyEval.PRESERVE"
            )

    def eval(self, x: ContentID) -> ConsistencyEval:
        return self.eval_map[x]

    @property
    def positive_contents(self) -> frozenset[ContentID]:
        return frozenset(x for x, e in self.eval_map.items() if e is ConsistencyEval.PRESERVE)

    @property
    def negative_contents(self) -> frozenset[ContentID]:
        return frozenset(x for x, e in self.eval_map.items() if e is ConsistencyEval.DAMAGE)

    @property
    def neutral_contents(self) -> frozenset[ContentID]:
        return frozenset(x for x, e in self.eval_map.items() if e is ConsistencyEval.NEUTRAL)
