"""Mode-C dispatch fixture.

Drives: I-MOD-03 (preserve → MODE_C).
"""
from __future__ import annotations

from brain.invariants import register
from brain.tlica.modes import ModeOp, from_eval
from brain.tlica.ptcns import ConsistencyEval


@register("I-MOD-03")
def check_I_MOD_03() -> None:
    """from_eval(preserve) == MODE_C."""
    assert from_eval(ConsistencyEval.PRESERVE) is ModeOp.MODE_C
