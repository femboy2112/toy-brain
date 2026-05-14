"""Profile-distance fixture.

Drives:
  I-PROF-03..07 (zero-extension laws + pointwise difference bound),
  I-PWS-01..10 (dInfUnion + dInfShared properties),
  I-INT-01..02 (strict ρ-bound + non-negativity).
"""
from __future__ import annotations

import math
from fractions import Fraction

from brain.invariants import register
from brain.tlica.builders import make_profile_with_cogito
from brain.tlica.comparison.pointwise import d_inf_shared, d_inf_union
from brain.tlica.integration_graph import rho_normalization
from brain.tlica.profile import COGITO_ID, ContentID


def _profiles():
    """Three profiles plus one with an empty-shared partner.

    p: domain {cogito, a, b}, values {1, 3/4, 1/2}
    q: domain {cogito, a, c}, values {1, 1/2, 1/3}     (shared {cogito, a})
    r: domain {cogito, b, c}, values {1, 3/4, 1/3}     (shared with p: {cogito, b})
    disjoint: domain {cogito, d}, values {1, 1/2}      (shared with p: only {cogito})

    Plus a truly-disjoint pair to exercise the inf branch.
    """
    p = make_profile_with_cogito({
        COGITO_ID: 1,
        "a": "3/4",
        "b": "1/2",
    })
    q = make_profile_with_cogito({
        COGITO_ID: 1,
        "a": "1/2",
        "c": "1/3",
    })
    r = make_profile_with_cogito({
        COGITO_ID: 1,
        "b": "3/4",
        "c": "1/3",
    })
    return p, q, r


def _universe() -> frozenset[ContentID]:
    return frozenset({COGITO_ID, ContentID("a"), ContentID("b"), ContentID("c"), ContentID("d")})


def _disjoint_pair():
    """Two profiles with NO shared domain — for the ⊤ branch of dInfShared.

    Note: we cannot use COGITO_ID in both halves because then they share cogito;
    so we use a stripped 'profile-like' object. But every ScalarProfile must
    have cogito at 1 — that's enforced by make_profile_with_cogito. To get
    truly disjoint domains, we construct two profiles each containing cogito
    but with otherwise disjoint domains; the shared set is {COGITO_ID}.
    For the strictly-empty-intersection case, we bypass make_profile_with_cogito
    and construct ScalarProfile directly with cogito-free domains. This is
    legal (ScalarProfile itself doesn't require cogito; only make_profile_with_cogito
    does), and it lets us exercise I-PWS-09 (empty intersection ⇒ ⊤).
    """
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
    return left, right


# ---- I-PROF-03..07 zero-extension laws ----


@register("I-PROF-03")
def check_I_PROF_03() -> None:
    """zeroExtend_of_mem: zero_extend(x) == values[x] for x in domain."""
    p, _, _ = _profiles()
    for x in p.domain:
        assert p.zero_extend(x) == p.values[x], f"zero_extend({x!r}) drift"


@register("I-PROF-04")
def check_I_PROF_04() -> None:
    """zeroExtend_of_not_mem: zero_extend(x) == 0 for x not in domain."""
    p, _, _ = _profiles()
    for x in _universe() - p.domain:
        assert p.zero_extend(x) == Fraction(0), f"zero_extend({x!r}) != 0"


@register("I-PROF-05")
def check_I_PROF_05() -> None:
    """zeroExtend_nonneg over the universe."""
    p, _, _ = _profiles()
    for x in _universe():
        assert p.zero_extend(x) >= 0


@register("I-PROF-06")
def check_I_PROF_06() -> None:
    """zeroExtend_le_one over the universe."""
    p, _, _ = _profiles()
    for x in _universe():
        assert p.zero_extend(x) <= 1


@register("I-PROF-07")
def check_I_PROF_07() -> None:
    """abs_sub_zeroExtend_le_one across f.domain | g.domain."""
    p, q, _ = _profiles()
    for x in p.domain | q.domain:
        assert abs(p.zero_extend(x) - q.zero_extend(x)) <= 1


# ---- I-PWS-01..10 pointwise distance laws ----


@register("I-PWS-01")
def check_I_PWS_01() -> None:
    """dInfUnion_nonneg."""
    p, q, _ = _profiles()
    assert d_inf_union(p, q) >= 0


@register("I-PWS-02")
def check_I_PWS_02() -> None:
    """dInfUnion_symm."""
    p, q, _ = _profiles()
    assert d_inf_union(p, q) == d_inf_union(q, p)


@register("I-PWS-03")
def check_I_PWS_03() -> None:
    """dInfUnion_self == 0."""
    p, _, _ = _profiles()
    assert d_inf_union(p, p) == 0


@register("I-PWS-04")
def check_I_PWS_04() -> None:
    """dInfUnion_le_one."""
    p, q, _ = _profiles()
    assert d_inf_union(p, q) <= 1


@register("I-PWS-05")
def check_I_PWS_05() -> None:
    """dInfUnion_triangle across three profiles."""
    p, q, r = _profiles()
    assert d_inf_union(p, r) <= d_inf_union(p, q) + d_inf_union(q, r)


@register("I-PWS-06")
def check_I_PWS_06() -> None:
    """dInfShared_nonneg — treats math.inf as >= 0."""
    p, q, _ = _profiles()
    val = d_inf_shared(p, q)
    assert val == math.inf or val >= 0


@register("I-PWS-07")
def check_I_PWS_07() -> None:
    """dInfShared_symm."""
    p, q, _ = _profiles()
    assert d_inf_shared(p, q) == d_inf_shared(q, p)
    left, right = _disjoint_pair()
    assert d_inf_shared(left, right) == d_inf_shared(right, left)


@register("I-PWS-08")
def check_I_PWS_08() -> None:
    """dInfShared_self_of_nonempty: domain non-empty ⇒ d_inf_shared(f, f) == 0."""
    p, _, _ = _profiles()
    assert p.domain  # precondition
    assert d_inf_shared(p, p) == 0


@register("I-PWS-09")
def check_I_PWS_09() -> None:
    """dInfShared_top_iff: empty intersection ⇔ ⊤."""
    p, q, _ = _profiles()
    # p, q share {COGITO_ID, 'a'} — non-empty, must not be inf
    val = d_inf_shared(p, q)
    assert val != math.inf, "non-empty shared but got inf"
    # disjoint pair — must be inf
    left, right = _disjoint_pair()
    assert (left.domain & right.domain) == set()
    assert d_inf_shared(left, right) == math.inf


@register("I-PWS-10")
def check_I_PWS_10() -> None:
    """dInfShared_le_one_of_nonempty."""
    p, q, _ = _profiles()
    val = d_inf_shared(p, q)
    assert val <= 1, f"shared distance {val} > 1"


# ---- I-INT-01..02 integration-graph strict ρ-bound ----


_RHO_SAMPLES = [
    Fraction(0),
    Fraction(1, 10),
    Fraction(1),
    Fraction(10),
    Fraction(1000),
]


@register("I-INT-01")
def check_I_INT_01() -> None:
    """C / (1 + C) < 1 for sampled C >= 0."""
    for C in _RHO_SAMPLES:
        rho = rho_normalization(C)
        assert rho < 1, f"rho({C}) = {rho}, must be < 1"


@register("I-INT-02")
def check_I_INT_02() -> None:
    """C / (1 + C) >= 0 for sampled C >= 0."""
    for C in _RHO_SAMPLES:
        rho = rho_normalization(C)
        assert rho >= 0, f"rho({C}) = {rho}, must be >= 0"
