"""Mode-A dispatch fixture.

Drives:
  I-MOD-01 (damage → MODE_A),
  I-MOD-05 (from_eval never returns MODE_B),
  I-IBND-01 (boundary ∩ neutral = ∅),
  I-IBND-03 (boundary ⇔ eval ∈ {preserve, damage}),
  I-IBND-04 (boundary ⇒ eval ≠ neutral).
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
    """A world that exercises all three eval classes simultaneously."""
    profile = make_profile_with_cogito({
        COGITO_ID: 1,
        "preserve_item": "3/4",
        "damage_item": "2/5",
        "neutral_item": "1/3",
    })
    msi = make_msi(
        profile=profile,
        contents={COGITO_ID, ContentID("preserve_item")},
        threshold=Fraction(1, 2),
    )
    ptcns = make_ptcns(
        msi=msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "preserve_item": ConsistencyEval.PRESERVE,
            "damage_item": ConsistencyEval.DAMAGE,
            "neutral_item": ConsistencyEval.NEUTRAL,
        },
    )
    return profile, msi, ptcns


@register("I-MOD-01")
def check_I_MOD_01() -> None:
    """from_eval(damage) == MODE_A."""
    assert from_eval(ConsistencyEval.DAMAGE) is ModeOp.MODE_A


@register("I-MOD-05")
def check_I_MOD_05() -> None:
    """from_eval never returns MODE_B (Lean has no theorem; plan convention)."""
    for e in ConsistencyEval:
        triggered = from_eval(e)
        assert triggered is not ModeOp.MODE_B, (
            f"from_eval({e!r}) returned MODE_B, forbidden by I-MOD-05"
        )


@register("I-IBND-01")
def check_I_IBND_01() -> None:
    """boundary ∩ neutral_contents == ∅."""
    _, msi, ptcns = _make_world()
    b = boundary(msi, ptcns)
    overlap = b & ptcns.neutral_contents
    assert not overlap, f"boundary ∩ neutral = {overlap!r}"


@register("I-IBND-03")
def check_I_IBND_03() -> None:
    """x ∈ boundary ⇔ eval(x) ∈ {PRESERVE, DAMAGE}."""
    _, msi, ptcns = _make_world()
    b = boundary(msi, ptcns)
    for x in ptcns.msi.profile.domain:
        eval_in_boundary = ptcns.eval(x) in (ConsistencyEval.PRESERVE, ConsistencyEval.DAMAGE)
        in_b = x in b
        assert in_b == eval_in_boundary, (
            f"mem_boundary_iff broken for {x!r}: in_b={in_b} eval={ptcns.eval(x)!r}"
        )


@register("I-IBND-04")
def check_I_IBND_04() -> None:
    """x ∈ boundary ⇒ eval(x) != NEUTRAL (consequence of I-IBND-03)."""
    _, msi, ptcns = _make_world()
    b = boundary(msi, ptcns)
    for x in b:
        assert ptcns.eval(x) is not ConsistencyEval.NEUTRAL
