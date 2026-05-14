"""Trajectory-step fixture.

Drives:
  I-PMAP-02 (project(no_action, P) == natural_dynamics(P)),
  I-TRJ-01 (generatedBy_step),
  I-TRJ-02 (stepUnionDistance_nonneg),
  I-TRJ-03 (stepUnionDistance_le_one),
  I-TRJ-04 (stepSharedDistance_top_iff),
  I-TRJ-08 (stepSharedDistance_nonneg, treating math.inf >= 0),
  I-TRJ-09 (stepSharedDistance_le_one_of_nonempty),
  I-AFF-06 (temporalAffectIntensity_le_one).
"""
from __future__ import annotations

import math
from fractions import Fraction

from brain.invariants import register
from brain.tlica.action_projection import FutureMSIModel, GlobalPreservationRanking
from brain.tlica.agency import AgencyContext, FeasibilityModel
from brain.tlica.builders import make_msi, make_profile_with_cogito
from brain.tlica.profile import COGITO_ID, ContentID, ScalarProfile
from brain.tlica.project_map import Act, IdentityProjectMap
from brain.tlica.trajectory import (
    ActionSchedule,
    ProfileTrajectory,
    generated_by,
    step_shared_distance,
    step_union_distance,
    temporal_affect_intensity,
)
from brain.validation import profile_equiv


def _msi_of(P: ScalarProfile):
    threshold = Fraction(1, 2)
    contents = frozenset(
        {COGITO_ID}
        | {x for x in P.domain if x != COGITO_ID and P.values[x] >= threshold}
    )
    return make_msi(profile=P, contents=contents, threshold=threshold)


def _make_world():
    P0 = make_profile_with_cogito({COGITO_ID: 1, "a": "3/4"})
    universe = frozenset({COGITO_ID, ContentID("a")})
    fam = FutureMSIModel(msi_of=_msi_of)
    gr = GlobalPreservationRanking(universe=universe)
    proj = IdentityProjectMap()
    feasibility = FeasibilityModel(
        feasible_fn=lambda P: frozenset(Act),
        proj=proj,
    )
    ctx = AgencyContext(fam=fam, global_rank=gr, proj=proj, feasibility=feasibility)

    # Three-tick trajectory under NOOP; identity projection makes every
    # profile identical to P0.
    sched = ActionSchedule(actions=(Act.NOOP, Act.NOOP, Act.NOOP))
    traj = ProfileTrajectory(profiles=(P0, P0, P0))
    return ctx, P0, sched, traj


@register("I-PMAP-02")
def check_I_PMAP_02() -> None:
    """project(NOOP, P) equals natural_dynamics(P) under the v0 stub."""
    ctx, P, _, _ = _make_world()
    via_project = ctx.proj.project(ctx.proj.no_action, P)
    via_natural = ctx.proj.natural_dynamics(P)
    assert profile_equiv(via_project, via_natural)


@register("I-TRJ-01")
def check_I_TRJ_01() -> None:
    """generatedBy_step at each adjacent index."""
    ctx, _, sched, traj = _make_world()
    for n in range(len(traj) - 1):
        assert generated_by(ctx, traj, sched, n), f"step n={n} not generated"


@register("I-TRJ-02")
def check_I_TRJ_02() -> None:
    """stepUnionDistance >= 0."""
    _, _, _, traj = _make_world()
    for n in range(len(traj) - 1):
        assert step_union_distance(traj, n) >= 0


@register("I-TRJ-03")
def check_I_TRJ_03() -> None:
    """stepUnionDistance <= 1."""
    _, _, _, traj = _make_world()
    for n in range(len(traj) - 1):
        assert step_union_distance(traj, n) <= 1


@register("I-TRJ-04")
def check_I_TRJ_04() -> None:
    """stepSharedDistance == math.inf iff adjacent domains have empty intersection.

    The identity-stub trajectory has identical domains at every tick, so
    the shared intersection is never empty and the distance is never inf.
    Verifying both directions:
      - non-empty domain ⇒ not inf.
      - and we synthesize a side-trajectory with a disjoint successor to
        confirm the ⇒ inf direction. We do it with a manual ProfileTrajectory
        (not via generated_by) because the identity stub cannot produce a
        disjoint successor.
    """
    _, _, _, traj = _make_world()
    for n in range(len(traj) - 1):
        d_n = traj.profile_at(n).domain
        d_n1 = traj.profile_at(n + 1).domain
        shared = d_n & d_n1
        val = step_shared_distance(traj, n)
        if shared:
            assert val != math.inf
        else:
            assert val == math.inf

    # Manual disjoint-domain trajectory to exercise the inf branch.
    from types import MappingProxyType
    from brain.tlica.profile import ScalarProfile
    left = ScalarProfile(
        domain=frozenset({ContentID("x")}),
        values=MappingProxyType({ContentID("x"): Fraction(1, 4)}),
    )
    right = ScalarProfile(
        domain=frozenset({ContentID("y")}),
        values=MappingProxyType({ContentID("y"): Fraction(3, 4)}),
    )
    manual = ProfileTrajectory(profiles=(left, right))
    assert step_shared_distance(manual, 0) == math.inf


@register("I-TRJ-08")
def check_I_TRJ_08() -> None:
    """stepSharedDistance is non-negative (treating math.inf >= 0)."""
    _, _, _, traj = _make_world()
    for n in range(len(traj) - 1):
        val = step_shared_distance(traj, n)
        assert val == math.inf or val >= 0


@register("I-TRJ-09")
def check_I_TRJ_09() -> None:
    """stepSharedDistance <= 1 when adjacent domains share something."""
    _, _, _, traj = _make_world()
    for n in range(len(traj) - 1):
        if traj.profile_at(n).domain & traj.profile_at(n + 1).domain:
            val = step_shared_distance(traj, n)
            assert val <= 1


@register("I-AFF-06")
def check_I_AFF_06() -> None:
    """temporal_affect_intensity <= 1."""
    _, _, _, traj = _make_world()
    for n in range(len(traj) - 1):
        assert temporal_affect_intensity(traj, n) <= 1
