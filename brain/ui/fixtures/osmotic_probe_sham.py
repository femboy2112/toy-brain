"""Phase 3.25 sham-exposure rejection fixture.

Drives ``I-OSMO-06`` (REQUIRED). SHAM_EXPOSURE trials must not
falsely claim the target digest was acquired.
"""
from __future__ import annotations

from brain.development.osmotic_learning_probe import (
    OsmoticCondition,
    OsmoticProbeStatus,
    build_osmotic_exposure_plan,
    run_osmotic_probe_trial,
)
from brain.invariants import register


@register("I-OSMO-06", status="REQUIRED")
def check_osmotic_sham_rejects_false_target() -> None:
    """SHAM_EXPOSURE rejects false target acquisition + transfer."""

    plan = build_osmotic_exposure_plan()
    sham_trials = [
        t for t in plan if t.condition is OsmoticCondition.SHAM_EXPOSURE
    ]
    # The v1 plan has 1 sham trial.
    assert len(sham_trials) == 1
    trial = sham_trials[0]

    result = run_osmotic_probe_trial(trial)
    assert result.condition is OsmoticCondition.SHAM_EXPOSURE
    assert result.prior_acquired_observed is False, (
        f"I-OSMO-06 violated: {trial.trial_id!r} prior_acquired_observed "
        f"is True for SHAM_EXPOSURE"
    )
    assert result.transfer_observed is False, (
        f"I-OSMO-06 violated: {trial.trial_id!r} transfer_observed "
        f"is True for SHAM_EXPOSURE"
    )
    assert result.false_positive is False
    assert result.status is OsmoticProbeStatus.PASS
    # The exposure event is recorded but with a different digest.
    assert len(result.exposure_events) == 1
    assert (
        result.exposure_events[0].abstract_digest_hex16
        != trial.expected_target_digest
    )
