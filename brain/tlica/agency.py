"""FeasibilityModel + AgencyContext + AgencyWitness + select.

Encodes ``Agency.lean``. Catalog rows owned: I-AGN-01..06 (REQUIRED).

Lean source: ``lean_reference/TLICA/Agency.lean``.

I-PCE-05 (STRUCTURAL): **this module must not import** ``brain.tlica.pce``.
The foundation PCE is action-constant by Lean theorem; using it for action
selection would make every action equivalent. Selection routes through
``feasible_projected_pce`` (which goes via
``brain.tlica.action_projection.projected_pce``). The
``brain._import_audit`` audit re-asserts this at runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable

# DELIBERATELY no import of brain.tlica.pce — I-PCE-05.
from brain.tlica.action_projection import (
    FutureMSIModel,
    GlobalPreservationRanking,
    projected_pce,
)
from brain.tlica.profile import ScalarProfile
from brain.tlica.project_map import Act, ProjectMap


@dataclass(frozen=True, slots=True)
class FeasibilityModel:
    """``Agency.lean::FeasibilityModel``.

    ``no_action_feasible`` invariant raised at construction: ``proj.no_action
    ∈ feasible(P)`` for every ``P`` the user later asks about. Since we can't
    pre-validate every possible ``P``, the dataclass stores the callable and
    each call site (e.g., ``AgencyContext.feasible``) is expected to be sanity-
    checked by a fixture. I-AGN-01 verifies this empirically.
    """

    feasible_fn: Callable[[ScalarProfile], frozenset[Act]]
    proj: ProjectMap

    def feasible(self, P: ScalarProfile) -> frozenset[Act]:
        s = self.feasible_fn(P)
        if self.proj.no_action not in s:
            raise ValueError(
                "I-AGN-01 violated (noAction_feasible): "
                f"proj.no_action {self.proj.no_action!r} not in feasible(P) {s!r}"
            )
        return s


@dataclass(frozen=True, slots=True)
class AgencyContext:
    """``Agency.lean::AgencyContext``."""

    fam: FutureMSIModel
    global_rank: GlobalPreservationRanking
    proj: ProjectMap
    feasibility: FeasibilityModel

    def feasible(self, P: ScalarProfile) -> frozenset[Act]:
        return self.feasibility.feasible(P)

    def feasible_projected_pce(self, P: ScalarProfile, a: Act) -> Fraction:
        """``Agency.lean::feasibleProjectedPCE``.

        Drives I-AGN-06 (feasibleProjectedPCE_eq_projectedPCE): definitional
        equality with the direct ProjectedPCE call.
        """
        return projected_pce(self.fam, self.global_rank, self.proj, P, a)


@dataclass(frozen=True, slots=True)
class AgencyWitness:
    """``Agency.lean::AgencyWitness``.

    Per corrigenda C1, ``__post_init__`` raises on invariant violation:
    I-AGN-02 (``selected ∈ feasible``) and I-AGN-03 (``selected``
    maximizes feasible projected PCE).
    """

    ctx: AgencyContext
    P: ScalarProfile
    selected: Act

    def __post_init__(self) -> None:
        feasible = self.ctx.feasible(self.P)
        if self.selected not in feasible:
            raise ValueError(
                "I-AGN-02 violated (selected_feasible): "
                f"selected {self.selected!r} not in feasible {feasible!r}"
            )
        sel_score = self.ctx.feasible_projected_pce(self.P, self.selected)
        for b in feasible:
            b_score = self.ctx.feasible_projected_pce(self.P, b)
            if not (b_score <= sel_score):
                raise ValueError(
                    "I-AGN-03 violated (selected_max): "
                    f"alternative {b!r} scores {b_score} > selected score {sel_score}"
                )


def select(ctx: AgencyContext, P: ScalarProfile) -> AgencyWitness:
    """``Agency.lean::exists_selectsFeasibleAction_of_finite_feasible``.

    Drives I-AGN-05: finite non-empty feasible set ⇒ a maximizer exists.
    Picks any action that ties for the max score; the witness's
    ``__post_init__`` re-asserts I-AGN-02 and I-AGN-03.
    """
    feasible = ctx.feasible(P)
    if not feasible:
        raise ValueError(
            "I-AGN-05 unreachable: feasible set is empty (Lean precondition violated)"
        )
    best_action = max(feasible, key=lambda a: ctx.feasible_projected_pce(P, a))
    return AgencyWitness(ctx=ctx, P=P, selected=best_action)
