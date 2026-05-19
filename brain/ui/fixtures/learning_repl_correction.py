"""Phase 3.22b REPL correction evidence fixture.

Drives ``I-AGENTLEARN-06`` (REQUIRED). Audits that a near-miss
REPL line followed by a valid REPL line produces a
``REPL_CORRECTION_APPLIED`` learning evidence record.
"""
from __future__ import annotations

from brain.development.agent_loop import (
    make_initial_agent_loop_state,
    run_agent_interaction_step,
)
from brain.development.learning_evidence import LearningEvidenceKind
from brain.invariants import register


@register("I-AGENTLEARN-06", status="REQUIRED")
def check_learning_repl_correction() -> None:
    """Audit REPL correction evidence."""
    state = make_initial_agent_loop_state()
    state, r_near = run_agent_interaction_step(state, "emit alpha")
    assert (
        r_near.repl_line_result is not None
        and r_near.repl_line_result.parse_category_value == "near-miss"
    )
    state, r_valid = run_agent_interaction_step(state, "EMIT ALPHA")
    assert (
        r_valid.repl_line_result is not None
        and r_valid.repl_line_result.parse_category_value == "valid"
    )

    correction = [
        r
        for r in state.learning_trace.records
        if r.kind is LearningEvidenceKind.REPL_CORRECTION_APPLIED
    ]
    assert len(correction) == 1, (
        "I-AGENTLEARN-06 violated: near-miss -> valid sequence must emit "
        "exactly one REPL_CORRECTION_APPLIED record"
    )
    rec = correction[0]
    assert rec.pre_facts and any(k == "hint" for k, _ in rec.pre_facts)
    assert rec.post_facts and any(k == "canonical" for k, _ in rec.post_facts)
    canonical = next(v for k, v in rec.post_facts if k == "canonical")
    assert "verb" in canonical or canonical, (
        "I-AGENTLEARN-06 violated: correction record must reference a "
        "non-empty canonical form"
    )
