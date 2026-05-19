"""Phase 3.30 SINGLE_STRUCTURE trial fixture.

Drives ``I-CURR-04`` (REQUIRED).
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


@register("I-CURR-04", status="REQUIRED")
def check_curriculum_single_structure() -> None:
    """SINGLE_STRUCTURE printable admits 1; SINGLE_STRUCTURE singleton rejects."""
    trials = {t.trial_id: t for t in build_curriculum_trials()}

    # Printable case: admits exactly one record with disposition SURVIVED.
    t01 = trials["T01_single_printable"]
    assert t01.condition is CurriculumCondition.SINGLE_STRUCTURE
    r01 = run_curriculum_trial(t01)
    assert r01.condition is CurriculumCondition.SINGLE_STRUCTURE
    assert r01.survived_count == 1
    assert r01.decayed_count == 0
    assert r01.rejected_count == 0
    assert r01.reuse_observed is False
    assert r01.false_positive is False
    assert r01.false_negative is False
    assert r01.verdict is TrialVerdict.PASS
    assert len(r01.audit_records) == 1
    assert r01.audit_records[0].disposition is AuditDisposition.SURVIVED

    # Singleton case: classification gate rejects.
    t02 = trials["T02_single_singleton"]
    assert t02.condition is CurriculumCondition.SINGLE_STRUCTURE
    r02 = run_curriculum_trial(t02)
    assert r02.survived_count == 0
    assert r02.decayed_count == 0
    assert r02.rejected_count == 1
    assert r02.reuse_observed is False
    assert r02.verdict is TrialVerdict.PASS
    assert len(r02.audit_records) == 1
    assert r02.audit_records[0].disposition is AuditDisposition.REJECTED
