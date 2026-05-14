"""Affect-kernel collapse fixture.

Drives: I-AFF-05 (no_affectKernel_of_branch_and_pce_collapse).

Builds a world where, for *every* feasible action pair:
  - branch_profile(ctx, P, a) == branch_profile(ctx, P, b), AND
  - feasible_projected_pce(P, a) == feasible_projected_pce(P, b).

Under the v0 IdentityProjectMap (project(a, P) = P for every a) and the
stub msi_of/global_rank that ignores the action, this collapse holds
universally. The AffectKernelWitness constructor must therefore raise on
any chosen pair (corrigenda D4: local per-pair check).
"""
from __future__ import annotations

from fractions import Fraction

from brain.invariants import register
from brain.tlica.action_projection import (
    FutureMSIModel,
    GlobalPreservationRanking,
)
from brain.tlica.affect import AffectKernelWitness
from brain.tlica.agency import AgencyContext, FeasibilityModel
from brain.tlica.builders import make_msi, make_profile_with_cogito
from brain.tlica.profile import COGITO_ID, ContentID, ScalarProfile
from brain.tlica.project_map import Act, IdentityProjectMap


def _msi_of(P: ScalarProfile):
    threshold = Fraction(1, 2)
    contents = frozenset(
        {COGITO_ID}
        | {x for x in P.domain if x != COGITO_ID and P.values[x] >= threshold}
    )
    return make_msi(profile=P, contents=contents, threshold=threshold)


def _make_world():
    profile = make_profile_with_cogito({
        COGITO_ID: 1,
        "a": "3/4",
    })
    universe = frozenset({COGITO_ID, ContentID("a")})
    fam = FutureMSIModel(msi_of=_msi_of)
    gr = GlobalPreservationRanking(universe=universe)
    proj = IdentityProjectMap()
    feasibility = FeasibilityModel(
        feasible_fn=lambda P: frozenset(Act),
        proj=proj,
    )
    ctx = AgencyContext(fam=fam, global_rank=gr, proj=proj, feasibility=feasibility)
    return ctx, profile


@register("I-AFF-05")
def check_I_AFF_05() -> None:
    """Constructor raises when branch profiles AND projected PCE both collapse.

    Per corrigenda D4: this is a local per-pair check. In a collapsed
    world (IdentityProjectMap + cogito-only MSI), every pair fails the
    structural-perturbation precondition, so *any* attempted witness
    raises ``ValueError`` mentioning I-AFF-05.
    """
    ctx, P = _make_world()
    raised = False
    try:
        AffectKernelWitness(
            ctx=ctx,
            P=P,
            baseline=Act.NOOP,
            action=Act.INTEGRATE,
        )
    except ValueError as exc:
        raised = True
        assert "I-AFF-05" in str(exc), (
            f"AffectKernelWitness raised but message lacks I-AFF-05 tag: {exc}"
        )
    assert raised, (
        "I-AFF-05 violated: AffectKernelWitness did NOT raise in a collapsed world"
    )

    # Sanity: a second distinct pair also collapses.
    try:
        AffectKernelWitness(
            ctx=ctx,
            P=P,
            baseline=Act.DIFFERENTIATE,
            action=Act.ENCAPSULATE,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("second collapsed pair unexpectedly constructed")
