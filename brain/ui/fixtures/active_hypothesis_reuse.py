"""Phase 3.26 REUSE_CACHED_HYPOTHESIS trials fixture.

Drives ``I-AHYP-09`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.active_hypothesis_probe import (
    AmbiguityCondition,
    TrialVerdict,
    build_active_hypothesis_trials,
    run_active_hypothesis_trial,
)
from brain.invariants import register


@register("I-AHYP-09", status="REQUIRED")
def check_active_hypothesis_reuse() -> None:
    """REUSE_CACHED_HYPOTHESIS trials hit the cache without re-probing."""
    trials = {t.trial_id: t for t in build_active_hypothesis_trials()}
    cache = {}

    # First populate cache with T03 + T07 results.
    r03 = run_active_hypothesis_trial(trials["T03_single_aba"], cache=cache)
    assert r03.survivors_count == 1
    assert r03.winner_id == "H_RENAME_S_ABA"

    r07 = run_active_hypothesis_trial(trials["T07_nosurv_aa"], cache=cache)
    assert r07.survivors_count == 0
    assert r07.no_hypothesis_survives is True

    # T09: second visit to T03's input.
    t09 = trials["T09_reuse_aba"]
    assert t09.condition is AmbiguityCondition.REUSE_CACHED_HYPOTHESIS
    r09 = run_active_hypothesis_trial(t09, cache=cache)
    assert r09.second_visit_cache_hit is True
    assert r09.second_visit_probe_count == 0
    assert r09.survivors_count == 1
    assert r09.winner_id == "H_RENAME_S_ABA"
    assert r09.verdict is TrialVerdict.PASS

    # T10: second visit to T07's input.
    t10 = trials["T10_reuse_aa"]
    assert t10.condition is AmbiguityCondition.REUSE_CACHED_HYPOTHESIS
    r10 = run_active_hypothesis_trial(t10, cache=cache)
    assert r10.second_visit_cache_hit is True
    assert r10.second_visit_probe_count == 0
    assert r10.survivors_count == 0
    assert r10.no_hypothesis_survives is True
    assert r10.verdict is TrialVerdict.PASS

    # The cached candidates / probe_steps tuples are reused exactly.
    assert r09.candidates == r03.candidates
    assert r09.probe_steps == r03.probe_steps
    assert r10.candidates == r07.candidates
    assert r10.probe_steps == r07.probe_steps
