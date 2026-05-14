"""Brain tick orchestrator (post-green only, per README build order).

Brings together io_types + builders + invariants. A ``Brain`` instance
maintains a current (profile, msi, ptcns) triple; each ``tick(events)``
ingests percepts, applies mode dispatch, and emits a ``TickRecord``.

Cross-cutting invariants re-asserted per tick:
  - I-RT-02: profile values in [0, 1].
  - I-RT-03: MSI density holds.
  - I-RT-04: PtCns evaluations remain total over the current domain.
  - I-RT-07: COGITO_ID present at value 1 in every projected profile.

v0 is deliberately minimal: the deterministic IdentityProjectMap means
``project(a, P) == P`` for every action. Real dynamics belong to a later
phase; what matters here is that the tick path obeys the invariants.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from types import MappingProxyType
from typing import Iterable

from brain.io_types import PerceptEvent, TickRecord
from brain.tlica.agency import AgencyContext
from brain.tlica.builders import make_msi, make_ptcns
from brain.tlica.iboundary import boundary
from brain.tlica.modes import ModeOp, from_eval
from brain.tlica.msi import MSI
from brain.tlica.profile import COGITO_ID, ContentID, ScalarProfile
from brain.tlica.ptcns import ConsistencyEval, PtCns


@dataclass
class Brain:
    """v0 brain instance: a (profile, msi, ptcns, ctx) tuple plus a tick log."""

    profile: ScalarProfile
    msi: MSI
    ptcns: PtCns
    ctx: AgencyContext
    tick_log: list[TickRecord] = field(default_factory=list)

    def tick(self, events: Iterable[PerceptEvent]) -> TickRecord:
        events = list(events)
        # Mode dispatch is informational in v0 — we record what was
        # triggered but the identity project map keeps state unchanged.
        triggered: set[ModeOp] = set()
        for e in events:
            if e.eval is not None:
                triggered.add(from_eval(e.eval))

        # Re-assert per-tick invariants (I-RT-02, I-RT-03, I-RT-04, I-RT-07).
        self._assert_invariants()

        record = TickRecord(
            tick_index=len(self.tick_log),
            profile_values=MappingProxyType(dict(self.profile.values)),
            msi_contents=self.msi.contents,
            eval_map=MappingProxyType(dict(self.ptcns.eval_map)),
            boundary=boundary(self.msi, self.ptcns),
            notes=tuple(f"triggered: {m.value}" for m in sorted(triggered, key=lambda x: x.value)),
        )
        self.tick_log.append(record)
        return record

    def _assert_invariants(self) -> None:
        # I-RT-02
        for k, v in self.profile.values.items():
            if not (Fraction(0) <= v <= Fraction(1)):
                raise ValueError(f"I-RT-02 violated: profile[{k!r}] = {v} not in [0, 1]")
        # I-RT-03
        for c in self.msi.contents:
            if c == COGITO_ID:
                continue
            if self.profile.values[c] < self.msi.threshold:
                raise ValueError(
                    f"I-RT-03 violated: MSI member {c!r} dropped below threshold"
                )
        # I-RT-04
        if set(self.ptcns.eval_map.keys()) != set(self.profile.domain):
            raise ValueError(
                "I-RT-04 violated: PtCns.eval_map keys diverged from profile.domain"
            )
        # I-RT-07: identity stub guarantees this; the explicit check below
        # protects against a future ProjectMap that strips the cogito.
        if COGITO_ID not in self.profile.domain or self.profile.values.get(COGITO_ID) != 1:
            raise ValueError(
                "I-RT-07 violated: projected profile does not preserve COGITO_ID at 1"
            )


def reconstruct_ptcns_from_evals(
    msi: MSI, evals: dict[ContentID, ConsistencyEval]
) -> PtCns:
    """Convenience reconstruct helper for upstream callers; uses the builder."""
    return make_ptcns(msi=msi, eval_map=evals)


__all__ = [
    "Brain",
    "PerceptEvent",
    "TickRecord",
    "reconstruct_ptcns_from_evals",
    "make_msi",
]
