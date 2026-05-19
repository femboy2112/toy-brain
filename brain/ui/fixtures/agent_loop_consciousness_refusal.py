"""Phase 3.22 Agent loop refusal fixture.

Drives ``I-AGENTLOOP-04`` (REQUIRED). Audits the bounded REFUSAL
reply triggered by operator inputs containing any term in the
imported ``_FORBIDDEN_NON_CLAIM_TERMS`` tuple.

Checks:

* Every member of the audit tuple, embedded in a short carrier
  text, triggers a REFUSAL reply.
* The REFUSAL reply has exactly two sections in canonical order
  (LIMITATION_REPORT, NEXT_ACTION_SUGGESTION).
* The REFUSAL reply's section bodies and ``full_text`` themselves
  contain ZERO terms from the audit tuple (the refusal denies
  cognitive-property claims without using forbidden literals).
* REFUSAL does NOT mutate the underlying ``OperatorSession``:
  stream chunk count, pattern ledger entry count, and growth ledger
  event count are unchanged across the REFUSAL.
* REFUSAL is deterministic: two REFUSAL replies for the same
  carrier text are bit-identical.

No real model calls. No tick invocation.
"""
from __future__ import annotations

from brain.development.agent_loop import (
    AgentReplyDisposition,
    AgentReplyStatus,
    make_initial_agent_loop_state,
    run_agent_interaction_step,
    summarize_session_for_agent,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.invariants import register


@register("I-AGENTLOOP-04", status="REQUIRED")
def check_agent_loop_consciousness_refusal() -> None:
    """Audit the REFUSAL trigger and reply-text discipline."""

    # 1. Every audit-tuple term triggers REFUSAL when embedded in
    # a short carrier text.
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        state = make_initial_agent_loop_state()
        pre = summarize_session_for_agent(state.session)
        carrier = f"the operator asks about {term} today"
        new_state, result = run_agent_interaction_step(state, carrier)
        assert result.reply.disposition is AgentReplyDisposition.REFUSAL, (
            f"I-AGENTLOOP-04 violated: term {term!r} did not trigger REFUSAL"
        )
        assert result.reply.section_kinds() == (
            AgentReplyStatus.LIMITATION_REPORT,
            AgentReplyStatus.NEXT_ACTION_SUGGESTION,
        )
        # Reply text contains zero audit-tuple terms (the REFUSAL
        # reply never uses any forbidden literal itself).
        full_lower = result.reply.full_text.lower()
        for forbidden_term in _FORBIDDEN_NON_CLAIM_TERMS:
            assert forbidden_term not in full_lower, (
                "I-AGENTLOOP-04 violated: REFUSAL reply text contains "
                f"forbidden term {forbidden_term!r}"
            )
        # Session state unchanged across the REFUSAL.
        post = summarize_session_for_agent(new_state.session)
        assert post.stream_chunk_count == pre.stream_chunk_count
        assert post.pattern_entry_count == pre.pattern_entry_count
        assert post.growth_event_total == pre.growth_event_total

    # 2. REFUSAL is deterministic.
    sa = make_initial_agent_loop_state()
    sb = make_initial_agent_loop_state()
    sa, ra = run_agent_interaction_step(sa, "what about damage?")
    sb, rb = run_agent_interaction_step(sb, "what about damage?")
    assert ra.reply == rb.reply
    assert ra.reply.disposition is AgentReplyDisposition.REFUSAL
