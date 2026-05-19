"""Phase 3.24 reasoning trace + learning evidence worldlet feedback fixture.

Drives ``I-WFDBK-08`` (REQUIRED) and ``I-WFDBK-09`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.agent_loop import (
    make_initial_agent_loop_state,
    run_agent_interaction_step,
)
from brain.development.learning_evidence import (
    LearningEvidenceKind,
    build_learning_proof_report,
)
from brain.development.processing_window import FeedbackMode
from brain.development.reasoning_trace import (
    ReasoningStepKind,
    build_reasoning_trace_report,
)
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.session import OperatorSession


_EXPECTED_REASONING_STEP_KIND_VALUES = frozenset(
    {
        "observe_input",
        "classify_refusal",
        "derive_pattern",
        "lookup_prior_structure",
        "compare_structure",
        "check_coherence",
        "check_repl",
        "select_reply_disposition",
        "check_limitation",
        "check_worldlet_feedback",
        "check_dispatch_trace",
        "emit_reply",
    }
)


_EXPECTED_LEARNING_EVIDENCE_KIND_VALUES = frozenset(
    {
        "observed",
        "recurrence_increased",
        "abstract_pattern_acquired",
        "abstract_pattern_reused",
        "transfer_recognized",
        "repl_correction_applied",
        "diminishing_returns_updated",
        "limitation_recorded",
        "dispatch_trace_recorded",
        "worldlet_feedback_recorded",
    }
)


def _fresh_state_worldlet():
    session = OperatorSession(
        state=initial_state(),
        processing_window_size=2,
        feedback_mode=FeedbackMode.WORLDLET,
    )
    return make_initial_agent_loop_state(session=session)


@register("I-WFDBK-08", status="REQUIRED")
def check_reasoning_trace_worldlet_step() -> None:
    """Audit reasoning trace CHECK_WORLDLET_FEEDBACK step."""

    # Closed enum membership.
    actual = frozenset(k.value for k in ReasoningStepKind)
    assert actual == _EXPECTED_REASONING_STEP_KIND_VALUES, (
        "I-WFDBK-08 violated: ReasoningStepKind value set drifted "
        f"(got {sorted(actual)!r})"
    )

    state = _fresh_state_worldlet()
    state, r = run_agent_interaction_step(state, "alpha line one")
    assert r.reasoning_trace is not None
    kinds = [s.kind for s in r.reasoning_trace.steps]
    assert ReasoningStepKind.CHECK_WORLDLET_FEEDBACK in kinds, (
        f"I-WFDBK-08 violated: reasoning trace missing "
        f"CHECK_WORLDLET_FEEDBACK; got {[k.value for k in kinds]}"
    )
    # CHECK_WORLDLET_FEEDBACK comes immediately before CHECK_DISPATCH_TRACE.
    wfb_idx = kinds.index(ReasoningStepKind.CHECK_WORLDLET_FEEDBACK)
    cdt_idx = kinds.index(ReasoningStepKind.CHECK_DISPATCH_TRACE)
    assert wfb_idx + 1 == cdt_idx, (
        f"I-WFDBK-08 violated: CHECK_WORLDLET_FEEDBACK must precede "
        f"CHECK_DISPATCH_TRACE; got wfb={wfb_idx}, cdt={cdt_idx}"
    )

    wfb_step = r.reasoning_trace.steps[wfb_idx]
    assert "feedback_mode=worldlet" in wfb_step.input_facts, (
        f"I-WFDBK-08 violated: CHECK_WORLDLET_FEEDBACK input_facts missing "
        f"feedback_mode=worldlet: {wfb_step.input_facts!r}"
    )
    assert "present=True" in wfb_step.input_facts
    assert "worldlet_summary_chunks=2" in wfb_step.derived_facts, (
        f"I-WFDBK-08 violated: CHECK_WORLDLET_FEEDBACK derived_facts missing "
        f"worldlet_summary_chunks=2: {wfb_step.derived_facts!r}"
    )

    # Reasoning trace digest is deterministic across two fresh sessions.
    state_a = _fresh_state_worldlet()
    state_b = _fresh_state_worldlet()
    state_a, ra = run_agent_interaction_step(state_a, "delta same input")
    state_b, rb = run_agent_interaction_step(state_b, "delta same input")
    digest_a = build_reasoning_trace_report(ra.reasoning_trace).trace_digest_hex16
    digest_b = build_reasoning_trace_report(rb.reasoning_trace).trace_digest_hex16
    assert digest_a == digest_b, (
        f"I-WFDBK-08 violated: reasoning trace digest not deterministic: "
        f"{digest_a!r} vs {digest_b!r}"
    )

    # Report includes the new check_worldlet_feedback_count field.
    report = build_reasoning_trace_report(r.reasoning_trace)
    assert report.check_worldlet_feedback_count == 1


@register("I-WFDBK-09", status="REQUIRED")
def check_learning_evidence_worldlet_record() -> None:
    """Audit learning evidence WORLDLET_FEEDBACK_RECORDED record."""

    # Closed enum membership.
    actual = frozenset(k.value for k in LearningEvidenceKind)
    assert actual == _EXPECTED_LEARNING_EVIDENCE_KIND_VALUES, (
        "I-WFDBK-09 violated: LearningEvidenceKind value set drifted "
        f"(got {sorted(actual)!r})"
    )

    state = _fresh_state_worldlet()
    state, r = run_agent_interaction_step(state, "alpha worldlet record")
    wfb_records = [
        rec
        for rec in r.learning_evidence_trace.records
        if rec.kind is LearningEvidenceKind.WORLDLET_FEEDBACK_RECORDED
    ]
    assert len(wfb_records) == 1, (
        f"I-WFDBK-09 violated: expected exactly 1 WORLDLET_FEEDBACK_RECORDED "
        f"record, got {len(wfb_records)}"
    )
    rec = wfb_records[0]
    pre_lookup = {k: v for k, v in rec.pre_facts}
    post_lookup = {k: v for k, v in rec.post_facts}
    assert "feedback_mode" in pre_lookup
    assert pre_lookup["feedback_mode"] == "worldlet"
    assert "worldlet_summary_chunks" in post_lookup
    assert "stream_chunks" in post_lookup
    assert "dispatch_digest" in post_lookup
    # Cited digest matches the result's latest_dispatch_trace.
    assert (
        post_lookup["dispatch_digest"]
        == r.latest_dispatch_trace.trace_digest_hex16
    )

    # After N interactions, worldlet_feedback_recorded_count == N.
    state = _fresh_state_worldlet()
    n = 3
    for _ in range(n):
        state, _ = run_agent_interaction_step(state, "alpha rep worldlet")
    report = build_learning_proof_report(state.learning_trace)
    assert report.worldlet_feedback_recorded_count == n, (
        f"I-WFDBK-09 violated: worldlet_feedback_recorded_count "
        f"{report.worldlet_feedback_recorded_count} != {n}"
    )

    # When feedback_mode is OFF, no WORLDLET_FEEDBACK_RECORDED record fires.
    sess_off = OperatorSession(
        state=initial_state(),
        processing_window_size=2,
        feedback_mode=FeedbackMode.OFF,
    )
    state_off = make_initial_agent_loop_state(session=sess_off)
    state_off, r_off = run_agent_interaction_step(
        state_off, "alpha no worldlet"
    )
    wfb_off = [
        rec
        for rec in r_off.learning_evidence_trace.records
        if rec.kind is LearningEvidenceKind.WORLDLET_FEEDBACK_RECORDED
    ]
    assert len(wfb_off) == 0, (
        "I-WFDBK-09 violated: WORLDLET_FEEDBACK_RECORDED emitted when "
        "feedback_mode is OFF"
    )
