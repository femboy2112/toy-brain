"""Phase 3.25 distractor / interference robustness fixture.

Drives ``I-OSMO-07`` (REQUIRED). DISTRACTOR_INTERFERENCE trials
still recognize the target digest among distractors.
"""
from __future__ import annotations

from brain.development.osmotic_learning_probe import (
    OsmoticCondition,
    OsmoticProbeStatus,
    build_osmotic_exposure_plan,
    run_osmotic_probe_trial,
)
from brain.invariants import register


@register("I-OSMO-07", status="REQUIRED")
def check_osmotic_distractor_interference() -> None:
    """DISTRACTOR_INTERFERENCE trials recognize target digest."""

    plan = build_osmotic_exposure_plan()
    distractor_trials = [
        t
        for t in plan
        if t.condition is OsmoticCondition.DISTRACTOR_INTERFERENCE
    ]
    # The v1 plan has 2 distractor trials: T06_distractor_abab and
    # T10_distractor_abcabc.
    assert len(distractor_trials) == 2

    for trial in distractor_trials:
        result = run_osmotic_probe_trial(trial)
        assert result.condition is OsmoticCondition.DISTRACTOR_INTERFERENCE
        assert result.prior_acquired_observed is True, (
            f"I-OSMO-07 violated: {trial.trial_id!r} prior_acquired_observed "
            f"is False under DISTRACTOR_INTERFERENCE"
        )
        assert result.transfer_observed is True, (
            f"I-OSMO-07 violated: {trial.trial_id!r} transfer_observed "
            f"is False under DISTRACTOR_INTERFERENCE"
        )
        assert result.status is OsmoticProbeStatus.PASS
        # Multiple exposure events: target + distractors.
        assert len(result.exposure_events) >= 2
        # At least one exposure event's digest matches the target.
        target_exposures = [
            ev
            for ev in result.exposure_events
            if ev.abstract_digest_hex16 == trial.expected_target_digest
        ]
        assert len(target_exposures) >= 1
