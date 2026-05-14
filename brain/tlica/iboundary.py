"""I/not-I boundary. Encodes IBoundary.lean.

Catalog rows owned: I-IBND-01..04 (REQUIRED); I-IBND-05 (DEFERRED).

Lean source: ``lean_reference/TLICA/IBoundary.lean``.
"""
from __future__ import annotations

from brain.tlica.msi import MSI
from brain.tlica.profile import ContentID
from brain.tlica.ptcns import PtCnsLike


def boundary(msi: MSI, ptcns: PtCnsLike) -> frozenset[ContentID]:
    """``IBoundary.lean::boundary``.

    The PtCns-positive ∪ PtCns-negative content, i.e. contents that elicit
    either Mode A or Mode C. Drives:
      - I-IBND-01 (boundary_excludes_neutral),
      - I-IBND-02 (cogito_in_boundary; cogito is always positive ⇒ in boundary),
      - I-IBND-03 (mem_boundary_iff),
      - I-IBND-04 (boundary_not_neutral).
    """
    del msi  # unused in the foundation default; boundary is PtCns-derived
    return ptcns.positive_contents | ptcns.negative_contents


def contestable_boundary(msi: MSI, ptcns: PtCnsLike) -> frozenset[ContentID]:
    """``IBoundary.lean::contestableBoundary``.

    DEFERRED in v0 (I-IBND-05): aliased to ``boundary``. The refined
    "region of contestable PtCns assignment" sense requires additional
    structure not in the v0 spec.
    """
    return boundary(msi, ptcns)
