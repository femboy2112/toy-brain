"""Phase 3.30 SEQUENTIAL_NONINTERFERING trial fixture.

Drives ``I-CURR-05`` (REQUIRED).
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


@register("I-CURR-05", status="REQUIRED")
def check_curriculum_noninterfering() -> None:
    """SEQUENTIAL_NONINTERFERING trials admit every distinct exposure."""
    trials = {t.trial_id: t for t in build_curriculum_trials()}
    for tid, expected in (
        ("T03_seq_distinct_2", 2),
        ("T04_seq_distinct_3", 3),
    ):
        t = trials[tid]
        assert t.condition is CurriculumCondition.SEQUENTIAL_NONINTERFERING
        r = run_curriculum_trial(t)
        assert r.survived_count == expected, (tid, r.survived_count)
        assert r.decayed_count == 0
        assert r.rejected_count == 0
        assert r.reuse_observed is False
        assert r.verdict is TrialVerdict.PASS
        assert len(r.audit_records) == expected
        for rec in r.audit_records:
            assert rec.disposition is AuditDisposition.SURVIVED, (
                tid, rec.structure_id, rec.disposition
            )
