"""ProjectMap Protocol + v0 identity stub. Encodes ProjectMap.lean.

Catalog rows owned: I-PMAP-01..03 (I-PMAP-01 STRUCTURAL, I-PMAP-02 REQUIRED,
I-PMAP-03 STRUCTURAL).

Lean source: ``lean_reference/TLICA/ProjectMap.lean``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from brain.tlica.profile import COGITO_ID, ScalarProfile


class Act(str, Enum):
    """Catalog convention: ``Act`` is an ``enum.Enum``, not a Literal."""

    NOOP = "noop"
    INTEGRATE = "integrate"
    DIFFERENTIATE = "differentiate"
    ENCAPSULATE = "encapsulate"


@runtime_checkable
class ProjectMap(Protocol):
    """``TLICA.ProjectMap.ProjectMap``.

    Per catalog convention: ``natural_dynamics`` is exposed explicitly
    (rather than as a Lean-style existential) so the
    ``identity_action_natural`` witness is testable in Python.
    """

    no_action: Act

    def project(self, action: Act, profile: ScalarProfile) -> ScalarProfile:
        ...

    def natural_dynamics(self, profile: ScalarProfile) -> ScalarProfile:
        ...


@dataclass(frozen=True, slots=True)
class IdentityProjectMap:
    """v0 deterministic stub: identity for every action.

    Trivially preserves COGITO_ID at value 1 (I-RT-07) since it returns
    the input profile unchanged, and satisfies
    ``project(NOOP, P) == natural_dynamics(P)`` (I-PMAP-02).
    """

    no_action: Act = Act.NOOP

    def project(self, action: Act, profile: ScalarProfile) -> ScalarProfile:
        # The cogito-preservation invariant is upheld by the input profile
        # itself; we re-check defensively per I-RT-07.
        if COGITO_ID not in profile.domain or profile.values.get(COGITO_ID) != 1:
            raise ValueError(
                "I-RT-07 violated: input profile does not preserve COGITO_ID at 1; "
                "the projection cannot restore it."
            )
        return profile

    def natural_dynamics(self, profile: ScalarProfile) -> ScalarProfile:
        return profile
