"""Phase 3.30 SEQUENTIAL_INTERFERING trial fixture.

Drives ``I-CURR-06`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.curriculum_consolidation_probe import (
    AuditDisposition,
    CurriculumCondition,
    TrialVerdict,
    build_curriculum_trials,
    run_curriculum_trial,
)
from brain.invariants import register


@register("I-CURR-06", status="REQUIRED")
def check_curriculum_interfering() -> None:
    """SEQUENTIAL_INTERFERING trials reject digest-collision duplicates."""
    trials = {t.trial_id: t for t in build_curriculum_trials()}

    # Pair: second occurrence rejected; first survives.
    t05 = trials["T05_collision_pair"]
    assert t05.condition is CurriculumCondition.SEQUENTIAL_INTERFERING
    r05 = run_curriculum_trial(t05)
    assert r05.survived_count == 1
    assert r05.decayed_count == 0
    assert r05.rejected_count == 1
    assert r05.verdict is TrialVerdict.PASS
    assert r05.audit_records[0].disposition is AuditDisposition.SURVIVED
    assert r05.audit_records[1].disposition is AuditDisposition.REJECTED

    # Trio: collision at index 2; index 0 + 1 survive.
    t06 = trials["T06_collision_in_3"]
    r06 = run_curriculum_trial(t06)
    assert r06.survived_count == 2
    assert r06.decayed_count == 0
    assert r06.rejected_count == 1
    assert r06.verdict is TrialVerdict.PASS
    assert r06.audit_records[0].disposition is AuditDisposition.SURVIVED
    assert r06.audit_records[1].disposition is AuditDisposition.SURVIVED
    assert r06.audit_records[2].disposition is AuditDisposition.REJECTED
