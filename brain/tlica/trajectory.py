"""ProfileTrajectory + step distances. Encodes TemporalTrajectory.lean.

Catalog rows owned: I-TRJ-01..04, I-TRJ-08..09 (REQUIRED).
I-TRJ-05..07 are DEFERRED (stochastic, phenomenological duration,
temporal continuity).

Lean source: ``lean_reference/TLICA/TemporalTrajectory.lean``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from brain.tlica.agency import AgencyContext
from brain.tlica.comparison.pointwise import d_inf_shared, d_inf_union
from brain.tlica.profile import ScalarProfile
from brain.tlica.project_map import Act


@dataclass(frozen=True, slots=True)
class ProfileTrajectory:
    """``TemporalTrajectory.lean::ProfileTrajectory``.

    A natural-time-indexed tuple of profiles. ``profile_at(n)`` is the
    n-th element; index out of range raises ``IndexError``.
    """

    profiles: tuple[ScalarProfile, ...]

    def profile_at(self, n: int) -> ScalarProfile:
        return self.profiles[n]

    def __len__(self) -> int:
        return len(self.profiles)


@dataclass(frozen=True, slots=True)
class ActionSchedule:
    """``TemporalTrajectory.lean::ActionSchedule``."""

    actions: tuple[Act, ...]

    def action_at(self, n: int) -> Act:
        return self.actions[n]


def generated_by(
    ctx: AgencyContext,
    traj: ProfileTrajectory,
    sched: ActionSchedule,
    n: int,
) -> bool:
    """``TemporalTrajectory.lean::generatedBy_step`` at index ``n``.

    True iff ``traj.profile_at(n+1) == ctx.proj.project(sched.action_at(n),
    traj.profile_at(n))`` exactly (Fraction == is safe).
    """
    expected = ctx.proj.project(sched.action_at(n), traj.profile_at(n))
    actual = traj.profile_at(n + 1)
    return expected.domain == actual.domain and all(
        expected.values[k] == actual.values[k] for k in expected.domain
    )


def step_union_distance(traj: ProfileTrajectory, n: int):
    """``TemporalTrajectory.lean::stepUnionDistance``."""
    return d_inf_union(traj.profile_at(n), traj.profile_at(n + 1))


def step_shared_distance(traj: ProfileTrajectory, n: int):
    """``TemporalTrajectory.lean::stepSharedDistance``.

    Returns ``math.inf`` when the adjacent shared domain is empty.
    """
    return d_inf_shared(traj.profile_at(n), traj.profile_at(n + 1))


def temporal_affect_intensity(traj: ProfileTrajectory, n: int):
    """``DifferentiatedAffect.lean::temporalAffectIntensity``.

    Equal to ``step_union_distance`` by the catalog's naming bridge; the
    affect module re-exports this name.
    """
    return step_union_distance(traj, n)


# Re-export for math.inf access by fixtures without an extra import line.
INF = math.inf
