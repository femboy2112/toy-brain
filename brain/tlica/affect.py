"""Affect kernel. Encodes DifferentiatedAffect.lean.

Catalog rows owned:
  - REQUIRED: I-AFF-01..06, I-AFF-11..13.
  - DEFERRED: I-AFF-07..10 (named taxonomy, love, substrate pathway,
    source-opacity).

Lean source: ``lean_reference/TLICA/DifferentiatedAffect.lean``.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from brain.tlica.agency import AgencyContext
from brain.tlica.profile import ScalarProfile
from brain.tlica.project_map import Act
from brain.tlica.trajectory import (  # noqa: F401  re-export for fixture convenience
    ProfileTrajectory,
    temporal_affect_intensity,
)


def relative_pce_delta(
    ctx: AgencyContext, P: ScalarProfile, baseline: Act, action: Act
) -> Fraction:
    """``DifferentiatedAffect.lean::relativePCEDelta``."""
    return ctx.feasible_projected_pce(P, action) - ctx.feasible_projected_pce(P, baseline)


def pce_supportive(
    ctx: AgencyContext, P: ScalarProfile, baseline: Act, action: Act
) -> bool:
    """``DifferentiatedAffect.lean::pceSupportive`` ⇔ baseline < action."""
    return relative_pce_delta(ctx, P, baseline, action) > 0


def pce_neutral(
    ctx: AgencyContext, P: ScalarProfile, baseline: Act, action: Act
) -> bool:
    """``DifferentiatedAffect.lean::pceNeutral`` ⇔ values equal."""
    return relative_pce_delta(ctx, P, baseline, action) == 0


def pce_defeating(
    ctx: AgencyContext, P: ScalarProfile, baseline: Act, action: Act
) -> bool:
    """``DifferentiatedAffect.lean::pceDefeating`` ⇔ action < baseline."""
    return relative_pce_delta(ctx, P, baseline, action) < 0


def branch_profile(ctx: AgencyContext, P: ScalarProfile, a: Act) -> ScalarProfile:
    """One-step deterministic branch profile under action ``a``.

    Used by ``AffectKernelWitness`` to check whether two action branches
    yield distinct profiles. Mirrors ``branchProfile`` in
    ``TLICA.TemporalTrajectory``.
    """
    return ctx.proj.project(a, P)


@dataclass(frozen=True, slots=True)
class AffectKernelWitness:
    """``DifferentiatedAffect.lean::AffectKernelWitness`` (per corrigenda D4).

    Constructor performs a **local** check: this baseline/action pair must
    exhibit *some* structural perturbation — either a branch-profile shift
    or a projected-PCE delta. Drives I-AFF-05
    (``no_affectKernel_of_branch_and_pce_collapse``): in a globally-collapsed
    world, every pair fails this local check, so no witness exists.
    """

    ctx: AgencyContext
    P: ScalarProfile
    baseline: Act
    action: Act

    def __post_init__(self) -> None:
        feasible = self.ctx.feasible(self.P)
        if self.baseline not in feasible:
            raise ValueError(
                f"AffectKernelWitness: baseline {self.baseline!r} not feasible"
            )
        if self.action not in feasible:
            raise ValueError(
                f"AffectKernelWitness: action {self.action!r} not feasible"
            )
        branch_b = branch_profile(self.ctx, self.P, self.baseline)
        branch_a = branch_profile(self.ctx, self.P, self.action)
        profiles_differ = (
            branch_b.domain != branch_a.domain
            or any(branch_b.values[k] != branch_a.values[k] for k in branch_b.domain)
        )
        pce_b = self.ctx.feasible_projected_pce(self.P, self.baseline)
        pce_a = self.ctx.feasible_projected_pce(self.P, self.action)
        pce_differs = pce_b != pce_a
        if not (profiles_differ or pce_differs):
            raise ValueError(
                "I-AFF-05 violated (no_affectKernel_of_branch_and_pce_collapse): "
                f"structural_perturbation empty — branch profiles and projected "
                f"PCE both collapse for the pair ({self.baseline!r}, {self.action!r})."
            )


# Surface-only witnesses (catalog: only I-AFF-05 has a v0 fixture). Their
# existence and field shape ensure parity with the Lean public surface.
@dataclass(frozen=True, slots=True)
class PCESupportAffectWitness:
    ctx: AgencyContext
    P: ScalarProfile
    baseline: Act
    action: Act


@dataclass(frozen=True, slots=True)
class PCEDefeatAffectWitness:
    ctx: AgencyContext
    P: ScalarProfile
    baseline: Act
    action: Act


@dataclass(frozen=True, slots=True)
class PCENeutralAffectWitness:
    ctx: AgencyContext
    P: ScalarProfile
    baseline: Act
    action: Act


@dataclass(frozen=True, slots=True)
class ProfileShiftAffectWitness:
    ctx: AgencyContext
    P: ScalarProfile
    baseline: Act
    action: Act
