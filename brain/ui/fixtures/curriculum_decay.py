"""Phase 3.30 DECAY_ON_DISUSE trial fixture.

Drives ``I-CURR-07`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.curriculum_consolidation_probe import (
    CURRICULUM_SLATE_MAX_ENTRIES,
    AuditDisposition,
    CurriculumCondition,
    TrialVerdict,
    build_curriculum_trials,
    run_curriculum_trial,
)
from brain.invariants import register


@register("I-CURR-07", status="REQUIRED")
def check_curriculum_decay_on_disuse() -> None:
    """DECAY_ON_DISUSE trials evict the LRU entries past slate capacity."""
    trials = {t.trial_id: t for t in build_curriculum_trials()}

    t07 = trials["T07_decay_overflow_5"]
    assert t07.condition is CurriculumCondition.DECAY_ON_DISUSE
    r07 = run_curriculum_trial(t07)
    assert r07.survived_count == CURRICULUM_SLATE_MAX_ENTRIES
    assert r07.decayed_count == 1
    assert r07.rejected_count == 0
    assert r07.verdict is TrialVerdict.PASS
    # Earliest exposure decays; the remaining four survive.
    assert r07.audit_records[0].disposition is AuditDisposition.DECAYED
    for i in range(1, 5):
        assert r07.audit_records[i].disposition is AuditDisposition.SURVIVED

    t08 = trials["T08_decay_overflow_6"]
    r08 = run_curriculum_trial(t08)
    assert r08.survived_count == CURRICULUM_SLATE_MAX_ENTRIES
    assert r08.decayed_count == 2
    assert r08.rejected_count == 0
    assert r08.verdict is TrialVerdict.PASS
    assert r08.audit_records[0].disposition is AuditDisposition.DECAYED
    assert r08.audit_records[1].disposition is AuditDisposition.DECAYED
    for i in range(2, 6):
        assert r08.audit_records[i].disposition is AuditDisposition.SURVIVED
