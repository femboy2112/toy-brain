"""Phase 3.26 CONTROL_NO_AMBIGUITY trials fixture.

Drives ``I-AHYP-05`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.active_hypothesis_probe import (
    AmbiguityCondition,
    TrialVerdict,
    build_active_hypothesis_trials,
    run_active_hypothesis_trial,
)
from brain.invariants import register


@register("I-AHYP-05", status="REQUIRED")
def check_active_hypothesis_control() -> None:
    """CONTROL_NO_AMBIGUITY trials emit zero probes."""
    trials = {t.trial_id: t for t in build_active_hypothesis_trials()}
    for tid in ("T01_control_empty", "T02_control_singleton"):
        t = trials[tid]
        assert t.condition is AmbiguityCondition.CONTROL_NO_AMBIGUITY
        r = run_active_hypothesis_trial(t)
        assert r.condition is AmbiguityCondition.CONTROL_NO_AMBIGUITY
        assert len(r.candidates) == 0, (tid, r.candidates)
        assert len(r.probe_steps) == 0, (tid, r.probe_steps)
        assert r.survivors_count == 0
        assert r.winner_id == ""
        assert r.no_hypothesis_survives is False
        assert r.verdict is TrialVerdict.PASS
        assert r.false_positive is False
        assert r.false_negative is False
