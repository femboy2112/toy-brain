"""Phase 3.26 SINGLE_HYPOTHESIS_CONVERGES trials fixture.

Drives ``I-AHYP-06`` (REQUIRED).
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


@register("I-AHYP-06", status="REQUIRED")
def check_active_hypothesis_single() -> None:
    """SINGLE_HYPOTHESIS_CONVERGES trials yield exactly one SELECTED winner."""
    trials = {t.trial_id: t for t in build_active_hypothesis_trials()}
    for tid, expected_winner in (
        ("T03_single_aba", "H_RENAME_S_ABA"),
        ("T04_single_abb", "H_RENAME_S_ABB"),
    ):
        t = trials[tid]
        assert t.condition is AmbiguityCondition.SINGLE_HYPOTHESIS_CONVERGES
        r = run_active_hypothesis_trial(t)
        assert r.condition is AmbiguityCondition.SINGLE_HYPOTHESIS_CONVERGES
        assert r.survivors_count == 1, (tid, r.survivors_count)
        assert r.winner_id == expected_winner, (tid, r.winner_id)
        assert r.no_hypothesis_survives is False
        assert r.false_positive is False
        assert r.false_negative is False
        assert r.verdict is TrialVerdict.PASS

        # Exactly one candidate carries SELECTED status; the rest are
        # FALSIFIED.
        selected = [
            c for c in r.candidates
            if c.status is ActiveHypothesisStatus.SELECTED
        ]
        falsified = [
            c for c in r.candidates
            if c.status is ActiveHypothesisStatus.FALSIFIED
        ]
        assert len(selected) == 1, (tid, [c.candidate_id for c in selected])
        assert selected[0].candidate_id == expected_winner
        assert len(falsified) + len(selected) == len(r.candidates)
