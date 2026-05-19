"""Phase 3.24 AgentObservationSummary + AgentReply worldlet feedback.

Drives ``I-WFDBK-10`` (REQUIRED). Audits the bounded
worldlet-feedback observation fields and the safe reply citation.
"""
from __future__ import annotations

from brain.development.agent_loop import (
    AgentObservationSummary,
    AgentReplyDisposition,
    build_agent_reply,
    make_initial_agent_loop_state,
    run_agent_interaction_step,
    summarize_session_for_agent,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.processing_window import FeedbackMode
from brain.development.text_stream import STREAM_HISTORY_MAX_CHUNKS
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.commands import Command, OperatorCommand, StreamAppendPayload
from brain.ui.session import OperatorSession


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-WFDBK-10", status="REQUIRED")
def check_agent_observation_worldlet_fields() -> None:
    """Audit AgentObservationSummary + reply citation."""

    # 1. Defaults: a fresh AgentObservationSummary defaults the new
    # fields to False / 0 / "off".
    obs_default = AgentObservationSummary(
        stream_chunk_count=0,
        pattern_entry_count=0,
        seed_pattern_id="",
        seed_recurrence=0,
        seed_saturation_state="none",
        growth_event_total=0,
        coherence_overall_status="pass",
        coherence_check_total=1,
        repl_emit_total=0,
        forbidden_term_hits=0,
    )
    assert obs_default.worldlet_feedback_present is False
    assert obs_default.worldlet_summary_count == 0
    assert obs_default.feedback_mode_value == "off"

    # 2. After a single STREAM_APPEND under WORLDLET mode, the
    # observation carries the worldlet-feedback facts.
    session = OperatorSession(
        state=initial_state(),
        processing_window_size=2,
        feedback_mode=FeedbackMode.WORLDLET,
    )
    session.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text="alpha obs"),
        )
    )
    obs = summarize_session_for_agent(session)
    assert obs.worldlet_feedback_present is True
    assert obs.worldlet_summary_count == 2
    assert obs.feedback_mode_value == "worldlet"

    # 3. Constructor rejects out-of-range / inconsistent inputs.
    rejection_cases = (
        (
            "non-bool present",
            dict(
                stream_chunk_count=0,
                pattern_entry_count=0,
                seed_pattern_id="",
                seed_recurrence=0,
                seed_saturation_state="none",
                growth_event_total=0,
                coherence_overall_status="pass",
                coherence_check_total=1,
                repl_emit_total=0,
                forbidden_term_hits=0,
                worldlet_feedback_present="True",
            ),
            TypeError,
        ),
        (
            "over-cap count",
            dict(
                stream_chunk_count=0,
                pattern_entry_count=0,
                seed_pattern_id="",
                seed_recurrence=0,
                seed_saturation_state="none",
                growth_event_total=0,
                coherence_overall_status="pass",
                coherence_check_total=1,
                repl_emit_total=0,
                forbidden_term_hits=0,
                worldlet_summary_count=STREAM_HISTORY_MAX_CHUNKS + 1,
            ),
            ValueError,
        ),
        (
            "present=True + count=0",
            dict(
                stream_chunk_count=0,
                pattern_entry_count=0,
                seed_pattern_id="",
                seed_recurrence=0,
                seed_saturation_state="none",
                growth_event_total=0,
                coherence_overall_status="pass",
                coherence_check_total=1,
                repl_emit_total=0,
                forbidden_term_hits=0,
                worldlet_feedback_present=True,
                worldlet_summary_count=0,
            ),
            ValueError,
        ),
        (
            "non-str feedback_mode",
            dict(
                stream_chunk_count=0,
                pattern_entry_count=0,
                seed_pattern_id="",
                seed_recurrence=0,
                seed_saturation_state="none",
                growth_event_total=0,
                coherence_overall_status="pass",
                coherence_check_total=1,
                repl_emit_total=0,
                forbidden_term_hits=0,
                feedback_mode_value=1,
            ),
            TypeError,
        ),
        (
            "non-member feedback_mode",
            dict(
                stream_chunk_count=0,
                pattern_entry_count=0,
                seed_pattern_id="",
                seed_recurrence=0,
                seed_saturation_state="none",
                growth_event_total=0,
                coherence_overall_status="pass",
                coherence_check_total=1,
                repl_emit_total=0,
                forbidden_term_hits=0,
                feedback_mode_value="not_a_mode",
            ),
            ValueError,
        ),
    )
    for tag, kwargs, exc in rejection_cases:
        raised = False
        try:
            AgentObservationSummary(**kwargs)
        except exc:
            raised = True
        assert raised, (
            f"I-WFDBK-10 violated: AgentObservationSummary accepted invalid "
            f"input ({tag})"
        )

    # 4. build_agent_reply: OK path cites worldlet-feedback when present.
    reply = build_agent_reply(
        session,
        "alpha obs",
        input_id="agent-input:00001",
    )
    assert reply.disposition is AgentReplyDisposition.OK
    full_text = reply.full_text
    assert "worldlet_feedback=present" in full_text
    assert "worldlet_summary_chunks=2" in full_text
    assert "route=internal_worldlet_summary" in full_text
    term = _has_forbidden(full_text)
    assert term is None, (
        f"I-WFDBK-10 violated: agent reply contains forbidden non-claim "
        f"term {term!r}: {full_text!r}"
    )

    # 5. OK path with NO worldlet feedback reports worldlet_feedback=absent.
    sess_off = OperatorSession(state=initial_state())
    sess_off.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text="alpha no worldlet"),
        )
    )
    reply_off = build_agent_reply(
        sess_off,
        "alpha no worldlet",
        input_id="agent-input:00002",
    )
    assert reply_off.disposition is AgentReplyDisposition.OK
    assert "worldlet_feedback=absent" in reply_off.full_text
    assert "worldlet_feedback=present" not in reply_off.full_text
    term = _has_forbidden(reply_off.full_text)
    assert term is None

    # 6. End-to-end run_agent_interaction_step propagates the obs fields.
    sess_wf = OperatorSession(
        state=initial_state(),
        processing_window_size=2,
        feedback_mode=FeedbackMode.WORLDLET,
    )
    state = make_initial_agent_loop_state(session=sess_wf)
    state, result = run_agent_interaction_step(state, "alpha line one")
    assert result.observation.worldlet_feedback_present is True
    assert result.observation.worldlet_summary_count == 2
    assert result.observation.feedback_mode_value == "worldlet"
