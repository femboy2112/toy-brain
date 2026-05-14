"""Projected-PCE + foundation PCE + affect-valence fixture.

Drives:
  I-PCE-01..04 (foundation PCE: nonneg, eq_rank_msi_contents,
    bounded_by_msi_max, all_actions_equal),
  I-APRJ-01..06 (FutureMSIModel domain match; GlobalPreservationRanking
    nonneg + monotone; ProjectedPCE nonneg, eq_of_future_contents_eq,
    monotone_of_future_contents_subset),
  I-AFF-01..04 (pceValence trichotomy + supportive/defeating/neutral iff),
  I-AFF-11..13 (valence mutual exclusions).
"""
from __future__ import annotations

from fractions import Fraction
from itertools import product

from brain.invariants import register
from brain.tlica.action_projection import (
    FutureMSIModel,
    GlobalPreservationRanking,
    future_msi_contents,
    projected_pce,
)
from brain.tlica.affect import (
    pce_defeating,
    pce_neutral,
    pce_supportive,
)
from brain.tlica.agency import AgencyContext, FeasibilityModel
from brain.tlica.builders import make_msi, make_profile_with_cogito
from brain.tlica.pce import PCE
from brain.tlica.preservation import PreservationRanking
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
        "b": "2/3",
    })
    universe = frozenset({COGITO_ID, ContentID("a"), ContentID("b")})
    fam = FutureMSIModel(msi_of=_msi_of)
    gr = GlobalPreservationRanking(universe=universe)
    proj = IdentityProjectMap()
    feasibility = FeasibilityModel(
        feasible_fn=lambda P: frozenset(Act),
        proj=proj,
    )
    ctx = AgencyContext(fam=fam, global_rank=gr, proj=proj, feasibility=feasibility)
    msi = _msi_of(profile)
    pi = PreservationRanking(msi=msi)
    return ctx, profile, msi, pi


# ---- I-PCE-01..04 ----


@register("I-PCE-01")
def check_I_PCE_01() -> None:
    ctx, P, msi, pi = _make_world()
    for a in Act:
        assert PCE(msi, pi, ctx.proj, a) >= 0


@register("I-PCE-02")
def check_I_PCE_02() -> None:
    ctx, P, msi, pi = _make_world()
    expected = pi.rank(msi.contents)
    for a in Act:
        assert PCE(msi, pi, ctx.proj, a) == expected


@register("I-PCE-03")
def check_I_PCE_03() -> None:
    ctx, P, msi, pi = _make_world()
    bound = pi.rank(msi.contents)
    for a in Act:
        assert PCE(msi, pi, ctx.proj, a) <= bound


@register("I-PCE-04")
def check_I_PCE_04() -> None:
    ctx, P, msi, pi = _make_world()
    actions = list(Act)
    for a, b in product(actions, actions):
        assert PCE(msi, pi, ctx.proj, a) == PCE(msi, pi, ctx.proj, b)


# ---- I-APRJ-01..06 ----


@register("I-APRJ-01")
def check_I_APRJ_01() -> None:
    """domain_match: (msi_of P).profile.domain == P.domain for every P queried.

    Corrigenda C3: the stub builds a fresh MSI tied to each P, so domain
    match is guaranteed across all sampled profiles.
    """
    ctx, P, _, _ = _make_world()
    profiles_to_check = [P, ctx.proj.project(Act.NOOP, P), ctx.proj.project(Act.INTEGRATE, P)]
    for Q in profiles_to_check:
        msi_q = ctx.fam.msi_of(Q)
        assert msi_q.profile.domain == Q.domain, (
            f"domain_match failed: msi_of(Q).profile.domain={msi_q.profile.domain!r} "
            f"vs Q.domain={Q.domain!r}"
        )


@register("I-APRJ-02")
def check_I_APRJ_02() -> None:
    """rank_nonneg."""
    ctx, _, _, _ = _make_world()
    samples = [frozenset(), frozenset({COGITO_ID}), ctx.global_rank.universe]
    for S in samples:
        assert ctx.global_rank.rank(S) >= 0


@register("I-APRJ-03")
def check_I_APRJ_03() -> None:
    """GlobalPreservationRanking.monotone."""
    ctx, _, _, _ = _make_world()
    pairs = [
        (frozenset(), frozenset({COGITO_ID})),
        (frozenset({COGITO_ID}), frozenset({COGITO_ID, ContentID("a")})),
        (frozenset({COGITO_ID, ContentID("a")}), ctx.global_rank.universe),
    ]
    for S, T in pairs:
        assert S <= T
        assert ctx.global_rank.rank(S) <= ctx.global_rank.rank(T)


@register("I-APRJ-04")
def check_I_APRJ_04() -> None:
    """ProjectedPCE.nonneg."""
    ctx, P, _, _ = _make_world()
    for a in Act:
        assert projected_pce(ctx.fam, ctx.global_rank, ctx.proj, P, a) >= 0


@register("I-APRJ-05")
def check_I_APRJ_05() -> None:
    """eq_of_future_contents_eq: equal lifted future contents ⇒ equal projected PCE.

    Under the identity stub, every action's future contents are identical;
    we verify the implication holds pairwise.
    """
    ctx, P, _, _ = _make_world()
    actions = list(Act)
    for a, b in product(actions, actions):
        fa = future_msi_contents(ctx.fam, ctx.proj, P, a)
        fb = future_msi_contents(ctx.fam, ctx.proj, P, b)
        if fa == fb:
            pa = projected_pce(ctx.fam, ctx.global_rank, ctx.proj, P, a)
            pb = projected_pce(ctx.fam, ctx.global_rank, ctx.proj, P, b)
            assert pa == pb, (
                f"future contents equal for ({a!r}, {b!r}) but projected PCE differs"
            )


@register("I-APRJ-06")
def check_I_APRJ_06() -> None:
    """monotone_of_future_contents_subset: subset ⇒ <= projected PCE."""
    ctx, P, _, _ = _make_world()
    actions = list(Act)
    for a, b in product(actions, actions):
        fa = future_msi_contents(ctx.fam, ctx.proj, P, a)
        fb = future_msi_contents(ctx.fam, ctx.proj, P, b)
        if fb <= fa:
            pa = projected_pce(ctx.fam, ctx.global_rank, ctx.proj, P, a)
            pb = projected_pce(ctx.fam, ctx.global_rank, ctx.proj, P, b)
            assert pb <= pa, (
                f"subset future contents but PCE order wrong: pa={pa} pb={pb}"
            )


# ---- I-AFF-01..04, I-AFF-11..13 ----


@register("I-AFF-01")
def check_I_AFF_01() -> None:
    """pceValence_trichotomy: every (baseline, action) is one of the three."""
    ctx, P, _, _ = _make_world()
    actions = list(Act)
    for baseline, action in product(actions, actions):
        s = pce_supportive(ctx, P, baseline, action)
        n = pce_neutral(ctx, P, baseline, action)
        d = pce_defeating(ctx, P, baseline, action)
        assert s or n or d, (
            f"({baseline!r}, {action!r}): no valence predicate holds"
        )


@register("I-AFF-02")
def check_I_AFF_02() -> None:
    """pceSupportive iff baseline < action."""
    ctx, P, _, _ = _make_world()
    actions = list(Act)
    for baseline, action in product(actions, actions):
        s = pce_supportive(ctx, P, baseline, action)
        strict = (
            ctx.feasible_projected_pce(P, baseline)
            < ctx.feasible_projected_pce(P, action)
        )
        assert s == strict


@register("I-AFF-03")
def check_I_AFF_03() -> None:
    """pceDefeating iff action < baseline."""
    ctx, P, _, _ = _make_world()
    actions = list(Act)
    for baseline, action in product(actions, actions):
        d = pce_defeating(ctx, P, baseline, action)
        strict = (
            ctx.feasible_projected_pce(P, action)
            < ctx.feasible_projected_pce(P, baseline)
        )
        assert d == strict


@register("I-AFF-04")
def check_I_AFF_04() -> None:
    """pceNeutral iff projected PCE values equal."""
    ctx, P, _, _ = _make_world()
    actions = list(Act)
    for baseline, action in product(actions, actions):
        n = pce_neutral(ctx, P, baseline, action)
        eq = (
            ctx.feasible_projected_pce(P, action)
            == ctx.feasible_projected_pce(P, baseline)
        )
        assert n == eq


@register("I-AFF-11")
def check_I_AFF_11() -> None:
    """pceSupportive excludes neutral."""
    ctx, P, _, _ = _make_world()
    actions = list(Act)
    for b, a in product(actions, actions):
        if pce_supportive(ctx, P, b, a):
            assert not pce_neutral(ctx, P, b, a)


@register("I-AFF-12")
def check_I_AFF_12() -> None:
    """pceSupportive excludes defeating."""
    ctx, P, _, _ = _make_world()
    actions = list(Act)
    for b, a in product(actions, actions):
        if pce_supportive(ctx, P, b, a):
            assert not pce_defeating(ctx, P, b, a)


@register("I-AFF-13")
def check_I_AFF_13() -> None:
    """pceDefeating excludes neutral."""
    ctx, P, _, _ = _make_world()
    actions = list(Act)
    for b, a in product(actions, actions):
        if pce_defeating(ctx, P, b, a):
            assert not pce_neutral(ctx, P, b, a)
