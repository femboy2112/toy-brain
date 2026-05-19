"""Phase 3.30 curriculum aggregate false-positive / false-negative fixture.

Drives ``I-CURR-09`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.curriculum_consolidation_probe import (
    run_curriculum_consolidation_live_test,
)
from brain.invariants import register


@register("I-CURR-09", status="REQUIRED")
def check_curriculum_false_pos_neg() -> None:
    """v1 battery has zero false positives, zero false negatives, expected reuse."""
    report = run_curriculum_consolidation_live_test()
    assert report.false_positive_count == 0
    assert report.false_negative_count == 0
    assert report.reuse_observed_count == 1
    assert report.total_survived_count == 23
    assert report.total_decayed_count == 3
    assert report.total_rejected_count == 3
    assert report.pass_count == 10
    assert report.warn_count == 0
    assert report.fail_count == 0
    assert report.not_applicable_count == 0
    # Per-trial: no trial flips its false_positive / false_negative flag.
    for r in report.trials:
        assert r.false_positive is False, (r.trial_id, r.false_positive)
        assert r.false_negative is False, (r.trial_id, r.false_negative)
