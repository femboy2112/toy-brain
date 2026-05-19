"""Phase 3.30 REUSE_AFTER_NEWER trial fixture.

Drives ``I-CURR-08`` (REQUIRED).
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


@register("I-CURR-08", status="REQUIRED")
def check_curriculum_reuse_after_newer() -> None:
    """REUSE_AFTER_NEWER probe returns cached older record; novel returns False."""
    trials = {t.trial_id: t for t in build_curriculum_trials()}

    # Positive: probe matches an older surviving record.
    t09 = trials["T09_reuse_oldest"]
    assert t09.condition is CurriculumCondition.REUSE_AFTER_NEWER
    r09 = run_curriculum_trial(t09)
    assert r09.survived_count == 3
    assert r09.decayed_count == 0
    assert r09.rejected_count == 0
    assert r09.reuse_observed is True
    assert r09.false_positive is False
    assert r09.false_negative is False
    assert r09.verdict is TrialVerdict.PASS
    assert r09.probe_step is not None
    assert r09.probe_step.reuse_observed is True
    assert r09.probe_step.probe_reused_structure_id != ""
    # The bumped entry's last_access_step is past its admitted_at_step.
    matching = [
        rec for rec in r09.audit_records
        if rec.disposition is AuditDisposition.SURVIVED
        and rec.structure_id == r09.probe_step.probe_reused_structure_id
    ]
    assert len(matching) == 1
    bumped = matching[0]
    assert bumped.last_access_step >= len(t09.exposures)

    # Negative: probe with novel digest does not fabricate reuse.
    t10 = trials["T10_reuse_negative"]
    r10 = run_curriculum_trial(t10)
    assert r10.survived_count == 3
    assert r10.decayed_count == 0
    assert r10.rejected_count == 0
    assert r10.reuse_observed is False
    assert r10.false_positive is False
    assert r10.verdict is TrialVerdict.PASS
    assert r10.probe_step is not None
    assert r10.probe_step.reuse_observed is False
    assert r10.probe_step.probe_reused_structure_id == ""
