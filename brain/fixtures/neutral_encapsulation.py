"""Neutral-encapsulation fixture.

Drives: I-MOD-02 (neutral → NEUTRAL).
"""
from __future__ import annotations

from brain.invariants import register
from brain.tlica.modes import ModeOp, from_eval
from brain.tlica.ptcns import ConsistencyEval


@register("I-MOD-02")
def check_I_MOD_02() -> None:
    """from_eval(neutral) == ModeOp.NEUTRAL."""
    assert from_eval(ConsistencyEval.NEUTRAL) is ModeOp.NEUTRAL
