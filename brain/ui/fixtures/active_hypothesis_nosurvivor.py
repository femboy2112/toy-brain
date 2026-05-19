"""Phase 3.26 NO_HYPOTHESIS_SURVIVES trials fixture.

Drives ``I-AHYP-08`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.active_hypothesis_probe import (
    ActiveHypothesisStatus,
    AmbiguityCondition,
    TrialVerdict,
    build_active_hypothesis_trials,
    run_active_hypothesis_trial,
)
from brain.invariants import register


@register("I-AHYP-08", status="REQUIRED")
def check_active_hypothesis_nosurvivor() -> None:
    """NO_HYPOTHESIS_SURVIVES trials yield zero survivors + empty winner."""
    trials = {t.trial_id: t for t in build_active_hypothesis_trials()}
    for tid in ("T07_nosurv_aa", "T08_nosurv_aab"):
        t = trials[tid]
        assert t.condition is AmbiguityCondition.NO_HYPOTHESIS_SURVIVES
        r = run_active_hypothesis_trial(t)
        assert r.survivors_count == 0, (tid, r.survivors_count)
        assert r.winner_id == "", (tid, r.winner_id)
        assert r.no_hypothesis_survives is True
        assert len(r.candidates) > 0, (tid, r.candidates)
        # Every candidate is FALSIFIED.
        for c in r.candidates:
            assert c.status is ActiveHypothesisStatus.FALSIFIED, (tid, c)
        assert r.verdict is TrialVerdict.PASS
        assert r.false_positive is False
        assert r.false_negative is False
