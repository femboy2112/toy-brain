"""Phase 3.25 delayed probe retention fixture.

Drives ``I-OSMO-08`` (REQUIRED). A delayed probe within the same
session still recognizes the imprinted structure.
"""
from __future__ import annotations

from brain.development.osmotic_learning_probe import (
    OsmoticProbeStatus,
    build_osmotic_exposure_plan,
    run_osmotic_probe_trial,
)
from brain.invariants import register


@register("I-OSMO-08", status="REQUIRED")
def check_osmotic_delayed_probe() -> None:
    """Delayed probe after unrelated inputs still recognizes target."""

    plan = build_osmotic_exposure_plan()
    delayed = next(
        t for t in plan if t.trial_id == "T07_delayed_abab"
    )

    result = run_osmotic_probe_trial(delayed)
    # T07 has 3 exposures (1 target + 2 unrelated distractors that
    # don't share the ABAB digest).
    assert len(result.exposure_events) == 3
    assert result.prior_acquired_observed is True, (
        f"I-OSMO-08 violated: delayed probe failed to retain imprint; "
        f"prior_acquired_observed=False"
    )
    assert result.transfer_observed is True, (
        f"I-OSMO-08 violated: delayed probe failed to trigger transfer"
    )
    assert result.status is OsmoticProbeStatus.PASS
    # The first exposure event matches the target digest; the others
    # do not (they are distractors).
    assert (
        result.exposure_events[0].abstract_digest_hex16
        == delayed.expected_target_digest
    )
    for ev in result.exposure_events[1:]:
        assert ev.abstract_digest_hex16 != delayed.expected_target_digest
