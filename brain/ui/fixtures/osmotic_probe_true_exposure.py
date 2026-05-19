"""Phase 3.25 true-exposure imprinting fixture.

Drives ``I-OSMO-04`` (REQUIRED). Verifies that TRUE_EXPOSURE trials
produce ABSTRACT_PATTERN_ACQUIRED records for the target digest
before the probe.
"""
from __future__ import annotations

from brain.development.agent_loop import (
    make_initial_agent_loop_state,
    run_agent_interaction_step,
)
from brain.development.learning_evidence import (
    LearningEvidenceKind,
    has_acquired_digest,
)
from brain.development.osmotic_learning_probe import (
    OsmoticCondition,
    OsmoticProbeStatus,
    build_osmotic_exposure_plan,
    run_osmotic_probe_trial,
)
from brain.invariants import register


@register("I-OSMO-04", status="REQUIRED")
def check_osmotic_true_exposure_imprints() -> None:
    """TRUE_EXPOSURE trials produce ABSTRACT_PATTERN_ACQUIRED before probe."""

    plan = build_osmotic_exposure_plan()
    true_trials = [
        t for t in plan if t.condition is OsmoticCondition.TRUE_EXPOSURE
    ]
    # T02_true_abab, T03_true_abba, T04_true_abcabc, T07_delayed_abab,
    # T09_renamed_aab.
    assert len(true_trials) == 5

    for trial in true_trials:
        # First verify via the probe-trial runner.
        result = run_osmotic_probe_trial(trial)
        assert result.prior_acquired_observed is True, (
            f"I-OSMO-04 violated: {trial.trial_id!r} prior_acquired_observed "
            f"is False for TRUE_EXPOSURE"
        )
        assert result.status is OsmoticProbeStatus.PASS

        # Second, replay the exposure phase manually and assert that
        # an ABSTRACT_PATTERN_ACQUIRED record exists for the target
        # digest before the probe fires.
        state = make_initial_agent_loop_state()
        for text in trial.exposure_texts:
            state, _ = run_agent_interaction_step(state, text)
        assert has_acquired_digest(
            state.learning_trace, trial.expected_target_digest
        ), (
            f"I-OSMO-04 violated: target digest "
            f"{trial.expected_target_digest!r} not acquired before probe "
            f"for trial {trial.trial_id!r}"
        )
        # ABSTRACT_PATTERN_ACQUIRED record exists for the target digest.
        acquired_for_target = [
            r
            for r in state.learning_trace.records
            if r.kind is LearningEvidenceKind.ABSTRACT_PATTERN_ACQUIRED
            and r.abstract_pattern_digest == trial.expected_target_digest
        ]
        assert len(acquired_for_target) == 1, (
            f"I-OSMO-04 violated: expected exactly 1 acquisition record "
            f"for target digest in trial {trial.trial_id!r}, got "
            f"{len(acquired_for_target)}"
        )
