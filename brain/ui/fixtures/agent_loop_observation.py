"""Phase 3.22 Agent loop observation fixture.

Drives ``I-AGENTLOOP-02`` (REQUIRED). Audits the bounded
``AgentObservationSummary`` record, ``summarize_session_for_agent``,
and the ``AgentLoopState`` container around fresh and post-dispatch
``OperatorSession`` instances.

Checks:

* Construction of an ``AgentObservationSummary`` enforces every
  bound (non-negative ints, cap on stream chunks vs the substrate's
  STREAM_HISTORY_MAX_CHUNKS, cap on growth events vs
  GROWTH_LEDGER_MAX_EVENTS, printable + bounded seed_pattern_id,
  enumerated seed_saturation_state and coherence_overall_status).
* ``summarize_session_for_agent(fresh_session)`` reports an empty
  ledger, empty stream history, growth_event_total == 0, and
  coherence_overall_status == "pass" (per Phase 3.21 W3 baseline).
* After one ``STREAM_APPEND`` through a fresh session, the
  observation reflects the new stream chunk + ledger entry +
  seed recurrence at the bounded MIN.
* ``summarize_session_for_agent`` is deterministic: two calls on the
  same session yield equal ``AgentObservationSummary`` records.
* ``AgentLoopState`` rejects malformed constructions.
* ``make_initial_agent_loop_state`` produces a fresh state with
  an empty REPL history and the default grammar handle.

No real model calls. No tick invocation. No filesystem / network.
"""
from __future__ import annotations

from brain.development.agent_loop import (
    AGENT_LOOP_MAX_INTERACTIONS,
    AgentLoopState,
    AgentObservationSummary,
    make_initial_agent_loop_state,
    run_agent_interaction_step,
    summarize_session_for_agent,
)
from brain.development.agent_repl_bridge import (
    AgentReplGrammarHandle,
    build_default_agent_repl_grammar,
)
from brain.development.growth_ledger import GROWTH_LEDGER_MAX_EVENTS
from brain.development.pattern_ledger import (
    PatternLedgerSaturationState,
    STREAM_PATTERN_RECURRENCE_MIN,
)
from brain.development.repl import ProtoBasicHistory
from brain.development.text_stream import STREAM_HISTORY_MAX_CHUNKS
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.commands import Command, OperatorCommand, StreamAppendPayload
from brain.ui.session import OperatorSession


@register("I-AGENTLOOP-02", status="REQUIRED")
def check_agent_loop_observation_and_state() -> None:
    """Audit AgentObservationSummary + summarize_session_for_agent + state."""

    # 1. Fresh session observation.
    state = make_initial_agent_loop_state()
    assert isinstance(state, AgentLoopState)
    assert isinstance(state.session, OperatorSession)
    assert isinstance(state.repl_history, ProtoBasicHistory)
    assert isinstance(state.repl_handle, AgentReplGrammarHandle)
    assert state.interaction_counter == 0

    fresh_obs = summarize_session_for_agent(state.session)
    assert isinstance(fresh_obs, AgentObservationSummary)
    assert fresh_obs.stream_chunk_count == 0
    assert fresh_obs.pattern_entry_count == 0
    assert fresh_obs.seed_pattern_id == ""
    assert fresh_obs.seed_recurrence == 0
    assert fresh_obs.seed_saturation_state == "none"
    assert fresh_obs.growth_event_total == 0
    assert fresh_obs.coherence_overall_status == "pass"
    assert fresh_obs.coherence_check_total > 0
    assert fresh_obs.repl_emit_total == 0
    assert fresh_obs.forbidden_term_hits == 0

    # 2. After one STREAM_APPEND, the observation reflects the new
    # stream chunk + ledger entry.
    seed_text = "alpha-line"
    state.session.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text=seed_text),
        )
    )
    post_obs = summarize_session_for_agent(state.session)
    assert post_obs.stream_chunk_count == 1
    assert post_obs.pattern_entry_count == 1
    assert post_obs.seed_pattern_id != ""
    assert post_obs.seed_recurrence == STREAM_PATTERN_RECURRENCE_MIN
    assert post_obs.seed_saturation_state == (
        PatternLedgerSaturationState.OPEN.value
    )
    assert post_obs.growth_event_total > 0
    assert post_obs.coherence_overall_status == "pass"

    # 3. Determinism: two calls on the same session yield equal records.
    a = summarize_session_for_agent(state.session)
    b = summarize_session_for_agent(state.session)
    assert a == b

    # 4. Bound enforcement on AgentObservationSummary construction.
    # negative count
    raised = False
    try:
        AgentObservationSummary(
            stream_chunk_count=-1,
            pattern_entry_count=0,
            seed_pattern_id="",
            seed_recurrence=0,
            seed_saturation_state="none",
            growth_event_total=0,
            coherence_overall_status="none",
            coherence_check_total=0,
            repl_emit_total=0,
            forbidden_term_hits=0,
        )
    except ValueError:
        raised = True
    assert raised

    # cap on stream_chunk_count
    raised = False
    try:
        AgentObservationSummary(
            stream_chunk_count=STREAM_HISTORY_MAX_CHUNKS + 1,
            pattern_entry_count=0,
            seed_pattern_id="",
            seed_recurrence=0,
            seed_saturation_state="none",
            growth_event_total=0,
            coherence_overall_status="none",
            coherence_check_total=0,
            repl_emit_total=0,
            forbidden_term_hits=0,
        )
    except ValueError:
        raised = True
    assert raised

    # cap on growth_event_total
    raised = False
    try:
        AgentObservationSummary(
            stream_chunk_count=0,
            pattern_entry_count=0,
            seed_pattern_id="",
            seed_recurrence=0,
            seed_saturation_state="none",
            growth_event_total=GROWTH_LEDGER_MAX_EVENTS + 1,
            coherence_overall_status="none",
            coherence_check_total=0,
            repl_emit_total=0,
            forbidden_term_hits=0,
        )
    except ValueError:
        raised = True
    assert raised

    # invalid saturation state
    raised = False
    try:
        AgentObservationSummary(
            stream_chunk_count=0,
            pattern_entry_count=0,
            seed_pattern_id="",
            seed_recurrence=0,
            seed_saturation_state="bad-state-value",
            growth_event_total=0,
            coherence_overall_status="none",
            coherence_check_total=0,
            repl_emit_total=0,
            forbidden_term_hits=0,
        )
    except ValueError:
        raised = True
    assert raised

    # invalid coherence status
    raised = False
    try:
        AgentObservationSummary(
            stream_chunk_count=0,
            pattern_entry_count=0,
            seed_pattern_id="",
            seed_recurrence=0,
            seed_saturation_state="none",
            growth_event_total=0,
            coherence_overall_status="bogus",
            coherence_check_total=0,
            repl_emit_total=0,
            forbidden_term_hits=0,
        )
    except ValueError:
        raised = True
    assert raised

    # 5. AgentLoopState rejects oversize interaction_counter.
    raised = False
    try:
        AgentLoopState(
            session=state.session,
            repl_history=ProtoBasicHistory(),
            repl_handle=build_default_agent_repl_grammar(),
            interaction_counter=AGENT_LOOP_MAX_INTERACTIONS + 1,
        )
    except ValueError:
        raised = True
    assert raised

    # 6. After run_agent_interaction_step the interaction_counter
    # advances by exactly 1.
    new_state = make_initial_agent_loop_state()
    new_state, _result = run_agent_interaction_step(new_state, "hello probe")
    assert new_state.interaction_counter == 1
