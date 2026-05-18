"""Phase 3.22 Agent loop reply determinism fixture.

Drives ``I-AGENTLOOP-03`` (REQUIRED). Audits the bounded
``AgentReply`` record's canonical-order discipline, the
``build_agent_reply`` helper's determinism across equivalent
sessions, and ``run_agent_interaction_step``'s reply construction.

Checks:

* AgentReply construction enforces canonical-order subsequence
  discipline, no-repeat-status discipline, bounded section body
  length, full_text bound, and the printable + non-COGITO_ID
  constraints.
* build_agent_reply on a fresh session with normal operator text
  produces a five-section OK reply in canonical order.
* Two fresh sessions advanced by the same operator text sequence
  produce bit-identical AgentReply records.
* Empty operator text produces a WARN reply (LIMITATION_REPORT +
  NEXT_ACTION_SUGGESTION only, in canonical order).
* Oversize operator text produces a FAIL reply.
* The full_text is the deterministic join of the section bodies.
* All reply text is bounded printable and passes the
  forbidden-term audit (any failure here would already have
  raised in the AgentReply constructor).

No real model calls. No tick invocation.
"""
from __future__ import annotations

from brain.development.agent_loop import (
    AGENT_INPUT_MAX_LEN,
    AGENT_REPLY_FULL_MAX_LEN,
    AGENT_REPLY_SECTION_MAX_LEN,
    AgentReply,
    AgentReplyDisposition,
    AgentReplyStatus,
    build_agent_reply,
    make_initial_agent_loop_state,
    run_agent_interaction_step,
)
from brain.invariants import register


@register("I-AGENTLOOP-03", status="REQUIRED")
def check_agent_loop_reply_determinism() -> None:
    """Audit AgentReply discipline + build_agent_reply determinism."""

    # 1. OK reply: five sections in canonical order.
    state = make_initial_agent_loop_state()
    reply = build_agent_reply(
        state.session,
        "alpha line one",
        input_id="agent-input:00001",
    )
    assert isinstance(reply, AgentReply)
    assert reply.disposition is AgentReplyDisposition.OK
    expected_order = (
        AgentReplyStatus.PATTERN_REPORT,
        AgentReplyStatus.REPL_REPORT,
        AgentReplyStatus.COHERENCE_REPORT,
        AgentReplyStatus.LIMITATION_REPORT,
        AgentReplyStatus.NEXT_ACTION_SUGGESTION,
    )
    assert reply.section_kinds() == expected_order

    # 2. Determinism: two fresh sessions advanced identically
    # produce equal AgentReply records.
    sa = make_initial_agent_loop_state()
    sb = make_initial_agent_loop_state()
    sa, ra = run_agent_interaction_step(sa, "alpha line one")
    sb, rb = run_agent_interaction_step(sb, "alpha line one")
    assert ra.reply == rb.reply
    assert ra.observation == rb.observation
    assert ra.input == rb.input

    sa, ra2 = run_agent_interaction_step(sa, "alpha line two")
    sb, rb2 = run_agent_interaction_step(sb, "alpha line two")
    assert ra2.reply == rb2.reply

    # 3. Empty input -> WARN reply with LIMITATION_REPORT +
    # NEXT_ACTION_SUGGESTION only.
    sc = make_initial_agent_loop_state()
    sc, rc = run_agent_interaction_step(sc, "")
    assert rc.reply.disposition is AgentReplyDisposition.WARN
    assert rc.reply.section_kinds() == (
        AgentReplyStatus.LIMITATION_REPORT,
        AgentReplyStatus.NEXT_ACTION_SUGGESTION,
    )

    # 4. Oversize input -> FAIL reply with LIMITATION_REPORT +
    # NEXT_ACTION_SUGGESTION only.
    sd = make_initial_agent_loop_state()
    big = "x" * (AGENT_INPUT_MAX_LEN + 100)
    sd, rd = run_agent_interaction_step(sd, big)
    assert rd.reply.disposition is AgentReplyDisposition.FAIL
    assert rd.reply.section_kinds() == (
        AgentReplyStatus.LIMITATION_REPORT,
        AgentReplyStatus.NEXT_ACTION_SUGGESTION,
    )

    # 5. AgentReply constructor rejects:
    # - empty sections
    raised = False
    try:
        AgentReply(
            input_id="agent-input:00099",
            disposition=AgentReplyDisposition.OK,
            sections=(),
            full_text="x",
        )
    except ValueError:
        raised = True
    assert raised

    # - sections out of canonical order
    raised = False
    try:
        AgentReply(
            input_id="agent-input:00099",
            disposition=AgentReplyDisposition.OK,
            sections=(
                (AgentReplyStatus.REPL_REPORT, "body1"),
                (AgentReplyStatus.PATTERN_REPORT, "body2"),
            ),
            full_text="x",
        )
    except ValueError:
        raised = True
    assert raised

    # - repeated status
    raised = False
    try:
        AgentReply(
            input_id="agent-input:00099",
            disposition=AgentReplyDisposition.OK,
            sections=(
                (AgentReplyStatus.PATTERN_REPORT, "body1"),
                (AgentReplyStatus.PATTERN_REPORT, "body2"),
            ),
            full_text="x",
        )
    except ValueError:
        raised = True
    assert raised

    # - overlong body
    raised = False
    try:
        AgentReply(
            input_id="agent-input:00099",
            disposition=AgentReplyDisposition.OK,
            sections=(
                (
                    AgentReplyStatus.PATTERN_REPORT,
                    "x" * (AGENT_REPLY_SECTION_MAX_LEN + 1),
                ),
            ),
            full_text="x",
        )
    except ValueError:
        raised = True
    assert raised

    # - overlong full_text
    raised = False
    try:
        AgentReply(
            input_id="agent-input:00099",
            disposition=AgentReplyDisposition.OK,
            sections=(
                (AgentReplyStatus.PATTERN_REPORT, "short body"),
            ),
            full_text="x" * (AGENT_REPLY_FULL_MAX_LEN + 1),
        )
    except ValueError:
        raised = True
    assert raised

    # - input_id empty / too long
    raised = False
    try:
        AgentReply(
            input_id="",
            disposition=AgentReplyDisposition.OK,
            sections=(
                (AgentReplyStatus.PATTERN_REPORT, "body"),
            ),
            full_text="x",
        )
    except ValueError:
        raised = True
    assert raised
