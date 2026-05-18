"""Phase 3.22b agent loop citation fixture.

Drives ``I-AGENTLEARN-05`` (REQUIRED). Audits that the agent loop
exposes the learning evidence trace in ``AgentLoopResult`` and that
later replies' pattern section reflects climbed recurrence (i.e.,
later reply cites prior accumulated structural state).
"""
from __future__ import annotations

from brain.development.agent_loop import (
    AgentReplyStatus,
    make_initial_agent_loop_state,
    run_agent_interaction_step,
)
from brain.development.learning_evidence import LearningEvidenceTrace
from brain.invariants import register


@register("I-AGENTLEARN-05", status="REQUIRED")
def check_learning_agent_loop_citation() -> None:
    """Audit AgentLoopResult learning trace + reply citation."""
    state = make_initial_agent_loop_state()
    state, r1 = run_agent_interaction_step(state, "alpha line one")
    assert isinstance(r1.learning_evidence_trace, LearningEvidenceTrace)
    assert len(r1.learning_evidence_trace.records) >= 2

    state, r2 = run_agent_interaction_step(state, "alpha line one")
    pattern_section = next(
        (
            body
            for status, body in r2.reply.sections
            if status is AgentReplyStatus.PATTERN_REPORT
        ),
        "",
    )
    # The pattern section reflects the climbed seed_recurrence (i.e.,
    # cites the prior accumulated state).
    assert "seed_recur=" in pattern_section
    assert r2.observation.seed_recurrence > r1.observation.seed_recurrence

    # AgentLoopState carries the accumulated trace.
    assert isinstance(state.learning_trace, LearningEvidenceTrace)
    # Trace must grow across interactions.
    state, r3 = run_agent_interaction_step(state, "novel input three")
    assert (
        len(r3.learning_evidence_trace.records)
        > len(r2.learning_evidence_trace.records)
    )
