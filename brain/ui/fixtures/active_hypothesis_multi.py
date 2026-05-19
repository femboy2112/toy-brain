"""Phase 3.26 MULTI_HYPOTHESIS_NARROWS trials fixture.

Drives ``I-AHYP-07`` (REQUIRED).
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


@register("I-AHYP-07", status="REQUIRED")
def check_active_hypothesis_multi() -> None:
    """MULTI_HYPOTHESIS_NARROWS trials yield 2+ survivors with empty winner."""
    trials = {t.trial_id: t for t in build_active_hypothesis_trials()}
    for tid in ("T05_multi_abc", "T06_multi_abab"):
        t = trials[tid]
        assert t.condition is AmbiguityCondition.MULTI_HYPOTHESIS_NARROWS
        r = run_active_hypothesis_trial(t)
        assert r.survivors_count >= 2, (tid, r.survivors_count)
        assert r.winner_id == "", (tid, r.winner_id)
        assert r.no_hypothesis_survives is False
        assert r.verdict is TrialVerdict.PASS
        # No candidate is promoted to SELECTED.
        selected = [
            c for c in r.candidates
            if c.status is ActiveHypothesisStatus.SELECTED
        ]
        assert selected == [], (tid, [c.candidate_id for c in selected])
        # All survivors carry SURVIVING status.
        surviving = [
            c for c in r.candidates
            if c.status is ActiveHypothesisStatus.SURVIVING
        ]
        assert len(surviving) == r.survivors_count
