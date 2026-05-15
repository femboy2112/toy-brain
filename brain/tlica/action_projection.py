"""FutureMSIModel + GlobalPreservationRanking + ProjectedPCE.

Encodes ``ActionProjection.lean``. This is the action-sensitive PCE layer;
action selection in ``agency.py`` routes through here (I-PCE-05).

Catalog rows owned: I-APRJ-01..06 (REQUIRED).

Lean source: ``lean_reference/TLICA/ActionProjection.lean``.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable

from brain.tlica.msi import MSI
from brain.tlica.profile import ContentID, ScalarProfile
from brain.tlica.project_map import Act, ProjectMap


class FutureMSIModel:
    """``ActionProjection.lean::FutureMSIModel``.

    Per corrigenda C3: callers must supply an ``msi_of`` that returns an
    MSI whose profile is the supplied ``P`` (so ``(msi_of P).profile.domain
    == P.domain`` holds for *every* ``P``, not just one fixed instance).

    Phase 2 v1.2 (P5): this class wraps the supplied callable and
    enforces ``domain_match`` at runtime so a non-conforming stub
    cannot silently drift. The v0 stub satisfies the invariant by
    construction; this wrapper makes the runtime check explicit.
    """

    __slots__ = ("_inner",)

    def __init__(self, msi_of: Callable[[ScalarProfile], MSI]) -> None:
        # Public constructor keyword is ``msi_of`` for backward
        # compatibility with v0/v1 fixtures that build the model via
        # ``FutureMSIModel(msi_of=fn)``. Internally we expose the
        # ``msi_of`` *method* below; the raw callable is stored as
        # ``_inner`` to avoid shadowing.
        self._inner = msi_of

    def msi_of(self, P: ScalarProfile) -> MSI:
        result = self._inner(P)
        if result.profile.domain != P.domain:
            raise ValueError(
                "I-APRJ-01 violated at runtime: msi_of(P).profile.domain "
                f"({sorted(result.profile.domain)}) != P.domain "
                f"({sorted(P.domain)}). The supplied stub must return an "
                "MSI whose profile.domain equals the input profile's domain."
            )
        return result


@dataclass(frozen=True, slots=True)
class GlobalPreservationRanking:
    """``ActionProjection.lean::GlobalPreservationRanking``.

    v0 stub: ``rank(S) = Fraction(len(S), max(1, |universe|))``.
    Non-negative and monotone by construction.
    No cogito gating (catalog: "only PreservationRanking over an MSI domain
    carries cogito necessity").
    """

    universe: frozenset[ContentID]

    def rank(self, S: frozenset[ContentID]) -> Fraction:
        denom = max(1, len(self.universe))
        return Fraction(len(S), denom)


def projected_profile(proj: ProjectMap, P: ScalarProfile, a: Act) -> ScalarProfile:
    """``ActionProjection.lean::projectedProfile``."""
    return proj.project(a, P)


def future_msi(fam: FutureMSIModel, proj: ProjectMap, P: ScalarProfile, a: Act) -> MSI:
    """``ActionProjection.lean::futureMSI``."""
    return fam.msi_of(projected_profile(proj, P, a))


def future_msi_contents(
    fam: FutureMSIModel, proj: ProjectMap, P: ScalarProfile, a: Act
) -> frozenset[ContentID]:
    """``ActionProjection.lean::futureMSIContents``.

    Lifts the future MSI's contents into the universal content type. In
    Python both live in ``ContentID``, so the lift is the identity.
    """
    return future_msi(fam, proj, P, a).contents


def projected_pce(
    fam: FutureMSIModel,
    gr: GlobalPreservationRanking,
    proj: ProjectMap,
    P: ScalarProfile,
    a: Act,
) -> Fraction:
    """``ActionProjection.lean::ProjectedPCE``.

    Action-sensitive PCE: rank of the lifted future MSI contents.
    Drives I-APRJ-04 (nonneg), I-APRJ-05 (eq_of_future_contents_eq),
    and I-APRJ-06 (monotone_of_future_contents_subset).
    """
    return gr.rank(future_msi_contents(fam, proj, P, a))
