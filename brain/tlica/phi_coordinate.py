"""φ-coordinate surface module (DEFERRED in v0).

Catalog rows owned: I-PHI-01..03 (all DEFERRED).

Lean source: ``lean_reference/TLICA/PhiCoordinate.lean``.

v0 drops the non-Archimedean δ that PhiCogito requires. This module exists
as documentation; any call into it raises NotImplementedError.
"""
from __future__ import annotations


def phi_cogito() -> None:
    raise NotImplementedError(
        "I-PHI-01 DEFERRED: φ(cogito) = 1 - δ requires the non-Archimedean δ "
        "that v0 drops. See PhiCoordinate.lean and INVARIANT_CATALOG.md."
    )
