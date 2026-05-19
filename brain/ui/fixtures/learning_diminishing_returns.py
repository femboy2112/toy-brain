"""Phase 3.22b diminishing-returns evidence fixture.

Drives ``I-AGENTLEARN-07`` (REQUIRED). Audits that repeated
valid-effective REPL commands produce
``DIMINISHING_RETURNS_UPDATED`` evidence records with monotonically
shrinking diminishing-returns factors.
"""
from __future__ import annotations

from brain.development.agent_loop import (
    make_initial_agent_loop_state,
    run_agent_interaction_step,
)
from brain.development.learning_evidence import LearningEvidenceKind
from brain.invariants import register


@register("I-AGENTLEARN-07", status="REQUIRED")
def check_learning_diminishing_returns() -> None:
    """Audit diminishing-returns evidence."""
    state = make_initial_agent_loop_state()
    for _ in range(5):
        state, _ = run_agent_interaction_step(state, "EMIT ALPHA")

    drf_records = [
        r
        for r in state.learning_trace.records
        if r.kind is LearningEvidenceKind.DIMINISHING_RETURNS_UPDATED
    ]
    # Expect 4 records (calls 2, 3, 4, 5).
    assert len(drf_records) == 4, (
        f"I-AGENTLEARN-07 violated: expected 4 DRF records over 5 emits, "
        f"got {len(drf_records)}"
    )

    # Verify the DRF strings shrink: 1/1 -> 1/2 -> 1/3 -> 1/4 -> 1/5.
    expected_pairs = (
        ("1/1", "1/2"),
        ("1/2", "1/3"),
        ("1/3", "1/4"),
        ("1/4", "1/5"),
    )
    for idx, (prior, current) in enumerate(expected_pairs):
        rec = drf_records[idx]
        prior_val = next(v for k, v in rec.pre_facts if k == "drf_before")
        current_val = next(v for k, v in rec.post_facts if k == "drf_after")
        assert prior_val == prior, (
            f"I-AGENTLEARN-07 violated: DRF record {idx} prior expected "
            f"{prior!r}, got {prior_val!r}"
        )
        assert current_val == current, (
            f"I-AGENTLEARN-07 violated: DRF record {idx} current expected "
            f"{current!r}, got {current_val!r}"
        )
