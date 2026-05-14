"""ModeOp + from_eval. Encodes Modes.lean.

Catalog rows owned: I-MOD-01..05 (REQUIRED).

Lean source: ``lean_reference/TLICA/Modes.lean``.

Note: ``ModeOp`` and ``Act`` are disjoint namespaces. ``ModeOp`` enumerates
the four apparatus operations triggered by PtCns evaluation (or, for Mode
B, by reflective capacity); ``Act`` enumerates the four candidate actions
fed to ``ProjectMap.project``. The mapping from ``ModeOp`` to a default
``Act`` is a lookup in higher layers, not an identity.
"""
from __future__ import annotations

from enum import Enum

from brain.tlica.ptcns import ConsistencyEval


class ModeOp(str, Enum):
    """Mirrors ``TLICA.Modes.ModeOp`` (Modes.lean §8.2)."""

    MODE_A = "modeA"
    MODE_B = "modeB"
    MODE_C = "modeC"
    NEUTRAL = "neutral"


# Lookup table for ``Modes.lean::ModeOp.fromEval``. Mode B is parallel and
# is intentionally absent — I-MOD-05 enforces that ``from_eval`` never
# returns ``MODE_B``.
_FROM_EVAL: dict[ConsistencyEval, ModeOp] = {
    ConsistencyEval.DAMAGE: ModeOp.MODE_A,
    ConsistencyEval.NEUTRAL: ModeOp.NEUTRAL,
    ConsistencyEval.PRESERVE: ModeOp.MODE_C,
}


def from_eval(e: ConsistencyEval) -> ModeOp:
    """``Modes.lean::ModeOp.fromEval``.

    Drives I-MOD-01 (damage→MODE_A), I-MOD-02 (neutral→NEUTRAL),
    I-MOD-03 (preserve→MODE_C), and I-MOD-05 (never returns MODE_B).
    """
    return _FROM_EVAL[e]
