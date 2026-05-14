"""Foundation-default PCE (action-constant). Encodes PCE.lean.

Catalog rows owned: I-PCE-01..04 (REQUIRED), I-PCE-05 (STRUCTURAL —
import-graph audit).

Lean source: ``lean_reference/TLICA/PCE.lean``.

By Lean theorem ``PCE.lean::PCE.all_actions_equal``, the foundation PCE is
action-constant. Action selection must therefore route through
``feasibleProjectedPCE`` (``brain.tlica.action_projection``), not this
module. ``brain/tlica/agency.py`` enforces this by not importing
``brain.tlica.pce``; ``brain._import_audit`` audits the rule.
"""
from __future__ import annotations

from fractions import Fraction

from brain.tlica.msi import MSI
from brain.tlica.preservation import PreservationRanking
from brain.tlica.project_map import Act, ProjectMap


def PCE(msi: MSI, pi: PreservationRanking, proj: ProjectMap, a: Act) -> Fraction:
    """``PCE.lean::PCE``.

    Returns ``pi.rank(msi.contents)``, independent of ``proj`` or ``a``.
    Drives I-PCE-01..04 directly:
      - nonneg: rank is non-negative by ``PreservationRanking``.
      - eq_rank_msi_contents: by definition.
      - bounded_by_msi_max: equality is the trivial bound.
      - all_actions_equal: action-constant by construction.
    """
    del proj, a  # action-constant by Lean theorem
    return pi.rank(msi.contents)
