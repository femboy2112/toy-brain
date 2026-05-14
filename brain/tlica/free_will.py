"""Free-will witness surface (DEFERRED branch semantics).

Catalog rows owned: I-FW-01..04 (all NOT-EXERCISED or DEFERRED in v0).

Lean source: ``lean_reference/TLICA/FreeWill.lean``.

These dataclasses exist so the public surface matches the Lean. No v0
fixture constructs them. Branch semantics are explicitly deferred per
``Agency.lean``'s docstring.
"""
from __future__ import annotations

from dataclasses import dataclass

from brain.tlica.agency import AgencyContext
from brain.tlica.profile import ContentID, ScalarProfile
from brain.tlica.project_map import Act


@dataclass(frozen=True, slots=True)
class FreeWillWitness:
    """``FreeWill.lean::FreeWillWitness`` (surface only; I-FW-01 NOT-EXERCISED)."""

    ctx: AgencyContext
    P: ScalarProfile
    selected: Act
    alternative: Act
    branch_contents_selected: frozenset[ContentID]
    branch_contents_alternative: frozenset[ContentID]


@dataclass(frozen=True, slots=True)
class PCEFreeWillWitness:
    """``FreeWill.lean::PCEFreeWillWitness`` (surface only; I-FW-02 NOT-EXERCISED)."""

    ctx: AgencyContext
    P: ScalarProfile
    selected: Act
    alternative: Act
