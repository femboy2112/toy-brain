"""Phase 3.22b learning evidence transfer fixture.

Drives ``I-AGENTLEARN-02`` (REQUIRED). Audits renamed-structure
transfer recognition through the agent loop's session-local
learning trace.
"""
from __future__ import annotations

from brain.development.agent_loop import (
    make_initial_agent_loop_state,
    run_agent_interaction_step,
)
from brain.development.learning_evidence import (
    LearningEvidenceKind,
)
from brain.invariants import register


@register("I-AGENTLEARN-02", status="REQUIRED")
def check_learning_evidence_transfer() -> None:
    """Audit renamed-structure transfer recognition."""
    state = make_initial_agent_loop_state()
    state, r1 = run_agent_interaction_step(state, "red blue red blue")
    state, r2 = run_agent_interaction_step(state, "cat dog cat dog")

    # ABAB digest was acquired on the first call.
    acquired = [
        r
        for r in state.learning_trace.records
        if r.kind is LearningEvidenceKind.ABSTRACT_PATTERN_ACQUIRED
    ]
    assert len(acquired) >= 1, (
        "I-AGENTLEARN-02 violated: first ABAB exposure must produce "
        "ABSTRACT_PATTERN_ACQUIRED record"
    )

    # Second call produced REUSED + TRANSFER_RECOGNIZED.
    reused = [
        r
        for r in state.learning_trace.records
        if r.kind is LearningEvidenceKind.ABSTRACT_PATTERN_REUSED
    ]
    transfer = [
        r
        for r in state.learning_trace.records
        if r.kind is LearningEvidenceKind.TRANSFER_RECOGNIZED
    ]
    assert len(reused) >= 1
    assert len(transfer) >= 1, (
        "I-AGENTLEARN-02 violated: renamed ABAB input must produce "
        "TRANSFER_RECOGNIZED record"
    )

    # The transfer record's abstract_pattern_digest matches the
    # acquired record's digest.
    assert transfer[0].abstract_pattern_digest == acquired[0].abstract_pattern_digest

    # Transfer's prior_pid and new_pid are distinct.
    assert transfer[0].pre_facts and transfer[0].post_facts
    prior_pid = next(v for k, v in transfer[0].pre_facts if k == "prior_pid")
    new_pid = next(v for k, v in transfer[0].post_facts if k == "new_pid")
    assert prior_pid and new_pid and prior_pid != new_pid

    # Determinism: another fresh state produces equal trace.
    state_b = make_initial_agent_loop_state()
    state_b, _ = run_agent_interaction_step(state_b, "red blue red blue")
    state_b, _ = run_agent_interaction_step(state_b, "cat dog cat dog")
    assert state.learning_trace.records == state_b.learning_trace.records, (
        "I-AGENTLEARN-02 violated: transfer evidence must be deterministic"
    )
