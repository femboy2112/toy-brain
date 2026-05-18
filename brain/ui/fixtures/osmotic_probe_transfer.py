"""Phase 3.25 renamed transfer activation fixture.

Drives ``I-OSMO-05`` (REQUIRED). Verifies that renamed probes
trigger ABSTRACT_PATTERN_REUSED + TRANSFER_RECOGNIZED.
"""
from __future__ import annotations

from brain.development.agent_loop import (
    make_initial_agent_loop_state,
    run_agent_interaction_step,
)
from brain.development.learning_evidence import LearningEvidenceKind
from brain.development.osmotic_learning_probe import (
    OsmoticCondition,
    OsmoticProbeStatus,
    build_osmotic_exposure_plan,
    run_osmotic_probe_trial,
)
from brain.invariants import register


@register("I-OSMO-05", status="REQUIRED")
def check_osmotic_renamed_transfer() -> None:
    """Renamed probes trigger ABSTRACT_PATTERN_REUSED + TRANSFER_RECOGNIZED."""

    plan = build_osmotic_exposure_plan()
    true_trials = [
        t for t in plan if t.condition is OsmoticCondition.TRUE_EXPOSURE
    ]
    assert len(true_trials) == 5

    for trial in true_trials:
        # Probe-trial runner reports transfer.
        result = run_osmotic_probe_trial(trial)
        assert result.transfer_observed is True, (
            f"I-OSMO-05 violated: {trial.trial_id!r} transfer_observed "
            f"is False for TRUE_EXPOSURE renamed probe"
        )
        assert result.status is OsmoticProbeStatus.PASS

        # Replay manually and confirm both record kinds appear at the
        # probe step.
        state = make_initial_agent_loop_state()
        for text in trial.exposure_texts:
            state, _ = run_agent_interaction_step(state, text)
        pre_records_len = len(state.learning_trace.records)
        state, _probe_r = run_agent_interaction_step(
            state, trial.probe_text
        )
        new_records = state.learning_trace.records[pre_records_len:]
        reused = [
            r
            for r in new_records
            if r.kind is LearningEvidenceKind.ABSTRACT_PATTERN_REUSED
            and r.abstract_pattern_digest == trial.expected_target_digest
        ]
        transferred = [
            r
            for r in new_records
            if r.kind is LearningEvidenceKind.TRANSFER_RECOGNIZED
            and r.abstract_pattern_digest == trial.expected_target_digest
        ]
        assert len(reused) == 1, (
            f"I-OSMO-05 violated: {trial.trial_id!r} expected exactly 1 "
            f"ABSTRACT_PATTERN_REUSED record at probe; got {len(reused)}"
        )
        assert len(transferred) == 1, (
            f"I-OSMO-05 violated: {trial.trial_id!r} expected exactly 1 "
            f"TRANSFER_RECOGNIZED record at probe; got {len(transferred)}"
        )
