"""Phase 3.22b reasoning trace agent loop integration fixture.

Drives ``I-AGENTLEARN-09`` (REQUIRED). Audits that the agent loop
populates ``AgentLoopResult.reasoning_trace`` on every interaction,
with deterministic step composition and a stable digest.
"""
from __future__ import annotations

from brain.development.agent_loop import (
    AGENT_INPUT_MAX_LEN,
    AgentReplyDisposition,
    make_initial_agent_loop_state,
    run_agent_interaction_step,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.reasoning_trace import (
    ReasoningStepKind,
    ReasoningTrace,
    build_reasoning_trace_report,
)
from brain.invariants import register


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-AGENTLEARN-09", status="REQUIRED")
def check_reasoning_trace_in_agent_loop() -> None:
    """Audit ReasoningTrace integration into AgentLoopResult."""

    # 1. Every disposition produces a non-empty reasoning trace.
    cognitive_probe = "are you " + _FORBIDDEN_NON_CLAIM_TERMS[0]
    cases = (
        "red blue red blue",
        "",
        cognitive_probe,
        "x" * (AGENT_INPUT_MAX_LEN + 1),
        "EMIT ALPHA",
    )
    state = make_initial_agent_loop_state()
    for text in cases:
        state, r = run_agent_interaction_step(state, text)
        assert isinstance(r.reasoning_trace, ReasoningTrace)
        assert len(r.reasoning_trace.steps) >= 3, (
            "I-AGENTLEARN-09 violated: every reply must carry a "
            "non-empty reasoning trace"
        )
        # OBSERVE_INPUT and EMIT_REPLY always present.
        kinds = tuple(s.kind for s in r.reasoning_trace.steps)
        assert ReasoningStepKind.OBSERVE_INPUT in kinds
        assert ReasoningStepKind.EMIT_REPLY in kinds

    # 2. Deterministic digest across two fresh sessions.
    state_a = make_initial_agent_loop_state()
    state_b = make_initial_agent_loop_state()
    state_a, ra = run_agent_interaction_step(state_a, "red blue red blue")
    state_b, rb = run_agent_interaction_step(state_b, "red blue red blue")
    report_a = build_reasoning_trace_report(ra.reasoning_trace)
    report_b = build_reasoning_trace_report(rb.reasoning_trace)
    assert report_a.trace_digest_hex16 == report_b.trace_digest_hex16
    assert ra.reasoning_trace == rb.reasoning_trace

    # 3. Pattern reply trace has DERIVE_PATTERN -> LOOKUP_PRIOR ->
    # COMPARE_STRUCTURE -> SELECT_REPLY_DISPOSITION ordering.
    kinds = tuple(s.kind for s in ra.reasoning_trace.steps)
    derive_idx = kinds.index(ReasoningStepKind.DERIVE_PATTERN)
    lookup_idx = kinds.index(ReasoningStepKind.LOOKUP_PRIOR_STRUCTURE)
    compare_idx = kinds.index(ReasoningStepKind.COMPARE_STRUCTURE)
    select_idx = kinds.index(ReasoningStepKind.SELECT_REPLY_DISPOSITION)
    assert derive_idx < lookup_idx < compare_idx < select_idx

    # 4. Refusal trace records classifier match.
    state_c = make_initial_agent_loop_state()
    state_c, r_refusal = run_agent_interaction_step(state_c, cognitive_probe)
    assert r_refusal.reply.disposition is AgentReplyDisposition.REFUSAL
    classify_step = next(
        (
            s
            for s in r_refusal.reasoning_trace.steps
            if s.kind is ReasoningStepKind.CLASSIFY_REFUSAL
        ),
        None,
    )
    assert classify_step is not None
    assert "classifier_match=True" in classify_step.input_facts
