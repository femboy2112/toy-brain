"""Phase 3.25 control-no-exposure rejection fixture.

Drives ``I-OSMO-03`` (REQUIRED). Verifies that CONTROL_NO_EXPOSURE
trials do not produce false acquisition or transfer claims.
"""
from __future__ import annotations

from brain.development.osmotic_learning_probe import (
    OsmoticCondition,
    OsmoticProbeStatus,
    build_osmotic_exposure_plan,
    run_osmotic_probe_trial,
)
from brain.invariants import register


@register("I-OSMO-03", status="REQUIRED")
def check_osmotic_control_no_exposure() -> None:
    """CONTROL_NO_EXPOSURE trials must reject target acquisition."""

    plan = build_osmotic_exposure_plan()
    control_trials = [
        t for t in plan if t.condition is OsmoticCondition.CONTROL_NO_EXPOSURE
    ]
    # The v1 plan has 2 control trials (T01_control_abab, T08_control_aab).
    assert len(control_trials) == 2

    for trial in control_trials:
        result = run_osmotic_probe_trial(trial)
        assert result.condition is OsmoticCondition.CONTROL_NO_EXPOSURE
        assert result.prior_acquired_observed is False, (
            f"I-OSMO-03 violated: {trial.trial_id!r} prior_acquired_observed "
            f"is True for CONTROL_NO_EXPOSURE"
        )
        assert result.transfer_observed is False, (
            f"I-OSMO-03 violated: {trial.trial_id!r} transfer_observed "
            f"is True for CONTROL_NO_EXPOSURE"
        )
        assert result.false_positive is False
        assert result.status is OsmoticProbeStatus.PASS, (
            f"I-OSMO-03 violated: {trial.trial_id!r} status is "
            f"{result.status.value} (expected pass)"
        )
        # No exposure events recorded.
        assert len(result.exposure_events) == 0
        # Exactly one dispatch digest (the probe).
        assert len(result.dispatch_trace_digests) == 1
