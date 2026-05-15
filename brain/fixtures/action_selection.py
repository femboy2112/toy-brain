"""Action-selection fixture.

Drives:
  I-PMAP-01 (proj.no_action is Act.NOOP) — STRUCTURAL,
  I-AGN-01..06 (FeasibilityModel, AgencyContext, AgencyWitness).

Uses the v0 identity ProjectMap stub plus a feasibility function that
admits every member of the ``Act`` enum.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Callable

from brain.invariants import register
from brain.tlica.action_projection import (
    FutureMSIModel,
    GlobalPreservationRanking,
    projected_pce,
)
from brain.tlica.agency import AgencyContext, AgencyWitness, FeasibilityModel, select
from brain.tlica.builders import make_msi, make_profile_with_cogito
from brain.tlica.profile import COGITO_ID, ContentID, ScalarProfile
from brain.tlica.project_map import Act, IdentityProjectMap


def _make_world():
    profile = make_profile_with_cogito({
        COGITO_ID: 1,
        "a": "3/4",
    })
    universe = frozenset({COGITO_ID, ContentID("a")})

    def msi_of(P: ScalarProfile):
        """Corrigenda C3: fresh MSI per call, tied to the supplied P."""
        threshold = Fraction(1, 2)
        contents = frozenset(
            {COGITO_ID}
            | {x for x in P.domain if x != COGITO_ID and P.values[x] >= threshold}
        )
        return make_msi(profile=P, contents=contents, threshold=threshold)

    fam = FutureMSIModel(msi_of=msi_of)
    gr = GlobalPreservationRanking(universe=universe)
    proj = IdentityProjectMap()
    feasibility = FeasibilityModel(
        feasible_fn=lambda P: frozenset(Act),  # all four actions are feasible
        proj=proj,
    )
    ctx = AgencyContext(fam=fam, global_rank=gr, proj=proj, feasibility=feasibility)
    return ctx, profile


@register("I-PMAP-01", status="STRUCTURAL")
def check_I_PMAP_01() -> None:
    """proj.no_action is Act.NOOP."""
    proj = IdentityProjectMap()
    assert proj.no_action is Act.NOOP


@register("I-PMAP-03", status="STRUCTURAL")
def check_I_PMAP_03() -> None:
    """ProjectMap.project is total: project(no_action, P) returns a profile."""
    _, P = _make_world()
    proj = IdentityProjectMap()
    result = proj.project(proj.no_action, P)
    # Total-function semantics: the call returns; the result is a profile.
    assert result.domain == P.domain, (
        f"I-PMAP-03 violated: project(no_action, P) returned a profile with "
        f"a different domain ({sorted(result.domain)} vs {sorted(P.domain)})"
    )


@register("I-AGN-01")
def check_I_AGN_01() -> None:
    """noAction_feasible: proj.no_action in ctx.feasible(P)."""
    ctx, P = _make_world()
    assert ctx.proj.no_action in ctx.feasible(P)


@register("I-AGN-02")
def check_I_AGN_02() -> None:
    """selected_feasible: selected action is feasible."""
    ctx, P = _make_world()
    w = select(ctx, P)
    assert w.selected in ctx.feasible(P)


@register("I-AGN-03")
def check_I_AGN_03() -> None:
    """selected_max: selected maximizes feasibleProjectedPCE."""
    ctx, P = _make_world()
    w = select(ctx, P)
    sel_score = ctx.feasible_projected_pce(P, w.selected)
    for b in ctx.feasible(P):
        assert ctx.feasible_projected_pce(P, b) <= sel_score


@register("I-AGN-04")
def check_I_AGN_04() -> None:
    """No feasible alternative strictly beats the selection (consequence of I-AGN-03)."""
    ctx, P = _make_world()
    w = select(ctx, P)
    sel_score = ctx.feasible_projected_pce(P, w.selected)
    for b in ctx.feasible(P):
        b_score = ctx.feasible_projected_pce(P, b)
        assert not (sel_score < b_score), (
            f"alternative {b!r} beats selection: {b_score} > {sel_score}"
        )


@register("I-AGN-05")
def check_I_AGN_05() -> None:
    """exists_selectsFeasibleAction_of_finite_feasible: select() returns a witness."""
    ctx, P = _make_world()
    w = select(ctx, P)
    assert isinstance(w, AgencyWitness)
    assert len(ctx.feasible(P)) > 0


@register("I-AGN-06")
def check_I_AGN_06() -> None:
    """feasibleProjectedPCE_eq_projectedPCE: agency-context value equals direct call."""
    ctx, P = _make_world()
    for a in ctx.feasible(P):
        via_ctx = ctx.feasible_projected_pce(P, a)
        via_direct = projected_pce(ctx.fam, ctx.global_rank, ctx.proj, P, a)
        assert via_ctx == via_direct, (
            f"agency-context PCE {via_ctx} != direct PCE {via_direct} for action {a!r}"
        )
