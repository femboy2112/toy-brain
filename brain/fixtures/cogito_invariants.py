"""Cogito-anchor fixture.

Drives (per catalog roster):
  I-MSI-01, I-MSI-02, I-MSI-05,
  I-PTC-01, I-PTC-04, I-PTC-05,
  I-MOD-04, I-IBND-02.

All eight rows turn on the cogito's special status: value 1, membership in
the MSI, eval as PRESERVE, exclusion from negative/neutral, and mode-C
dispatch.
"""
from __future__ import annotations

from fractions import Fraction

from brain.invariants import register
from brain.tlica.builders import make_msi, make_profile_with_cogito, make_ptcns
from brain.tlica.iboundary import boundary
from brain.tlica.modes import ModeOp, from_eval
from brain.tlica.profile import COGITO_ID, ContentID
from brain.tlica.ptcns import ConsistencyEval


def _make_world():
    profile = make_profile_with_cogito({
        COGITO_ID: 1,
        "a": "3/4",
    })
    msi = make_msi(
        profile=profile,
        contents={COGITO_ID, ContentID("a")},
        threshold=Fraction(1, 2),
    )
    ptcns = make_ptcns(
        msi=msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "a": ConsistencyEval.PRESERVE,
        },
    )
    return profile, msi, ptcns


@register("I-MSI-01")
def check_I_MSI_01() -> None:
    """cogito_value: profile.toFun cogito = 1."""
    profile, _, _ = _make_world()
    assert profile.values[COGITO_ID] == 1, (
        f"COGITO_ID value is {profile.values[COGITO_ID]}, must be 1"
    )


@register("I-MSI-02")
def check_I_MSI_02() -> None:
    """cogito_in (Axiom 3.3.1): COGITO_ID ∈ msi.contents."""
    _, msi, _ = _make_world()
    assert COGITO_ID in msi.contents, "COGITO_ID not in msi.contents"


@register("I-MSI-05")
def check_I_MSI_05() -> None:
    """cogito_is_supremum: cogito is the ρ-profile supremum."""
    profile, _, _ = _make_world()
    cogito_val = profile.values[COGITO_ID]
    for x in profile.domain:
        assert profile.values[x] <= cogito_val, (
            f"value for {x!r} = {profile.values[x]} > cogito value {cogito_val}"
        )


@register("I-PTC-01")
def check_I_PTC_01() -> None:
    """cogito_invariance (Axiom 7.3.1): eval(cogito) == PRESERVE."""
    _, _, ptcns = _make_world()
    assert ptcns.eval(COGITO_ID) is ConsistencyEval.PRESERVE, (
        f"eval(COGITO_ID) = {ptcns.eval(COGITO_ID)!r}, must be PRESERVE"
    )


@register("I-PTC-04")
def check_I_PTC_04() -> None:
    """cogito_in_positive: COGITO_ID ∈ positive_contents."""
    _, _, ptcns = _make_world()
    assert COGITO_ID in ptcns.positive_contents, (
        "COGITO_ID not in ptcns.positive_contents"
    )


@register("I-PTC-05")
def check_I_PTC_05() -> None:
    """cogito_not_negative + cogito_not_neutral."""
    _, _, ptcns = _make_world()
    assert COGITO_ID not in ptcns.negative_contents, (
        "COGITO_ID is in negative_contents"
    )
    assert COGITO_ID not in ptcns.neutral_contents, (
        "COGITO_ID is in neutral_contents"
    )


@register("I-MOD-04")
def check_I_MOD_04() -> None:
    """cogito_triggers_modeC: from_eval(ptcns.eval(COGITO_ID)) == MODE_C."""
    _, _, ptcns = _make_world()
    triggered = from_eval(ptcns.eval(COGITO_ID))
    assert triggered is ModeOp.MODE_C, (
        f"from_eval(eval(COGITO_ID)) = {triggered!r}, must be MODE_C"
    )


@register("I-IBND-02")
def check_I_IBND_02() -> None:
    """cogito_in_boundary: COGITO_ID ∈ boundary(msi, ptcns)."""
    _, msi, ptcns = _make_world()
    b = boundary(msi, ptcns)
    assert COGITO_ID in b, f"COGITO_ID not in boundary {b!r}"
