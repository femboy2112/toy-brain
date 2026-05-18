"""Phase 3.23 dispatch tracer reasoning + learning integration fixture.

Drives ``I-DTRACE-09`` (REQUIRED) — ReasoningTrace references the
dispatch trace digest via a CHECK_DISPATCH_TRACE step — and
``I-DTRACE-10`` (REQUIRED) — the agent loop appends a
DISPATCH_TRACE_RECORDED evidence record on every interaction.
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
from brain.development.reasoning_trace import (
    ReasoningStepKind,
    build_reasoning_trace_report,
)
from brain.invariants import register


@register("I-DTRACE-09", status="REQUIRED")
def check_reasoning_trace_cites_dispatch_digest() -> None:
    """Audit CHECK_DISPATCH_TRACE step + reasoning-trace determinism."""

    # 1. STREAM_APPEND interaction: CHECK_DISPATCH_TRACE step present,
    # cites the dispatch trace digest, sits immediately before EMIT_REPLY.
    state = make_initial_agent_loop_state()
    state, r = run_agent_interaction_step(state, "alpha line one")
    rt = r.reasoning_trace
    assert rt is not None
    assert len(rt.steps) >= 2

    cdt_step = None
    cdt_index = -1
    for i, step in enumerate(rt.steps):
        if step.kind is ReasoningStepKind.CHECK_DISPATCH_TRACE:
            cdt_step = step
            cdt_index = i
    assert cdt_step is not None
    # immediately before EMIT_REPLY
    assert rt.steps[-1].kind is ReasoningStepKind.EMIT_REPLY
    assert cdt_index == len(rt.steps) - 2

    digest = r.latest_dispatch_trace.trace_digest_hex16
    assert f"dispatch_digest={digest}" in cdt_step.input_facts
    assert "route_path=" in cdt_step.derived_facts
    assert "cmd=" in cdt_step.derived_facts
    assert "mut=" in cdt_step.derived_facts

    # 2. Determinism across two fresh sessions.
    sa = make_initial_agent_loop_state()
    sb = make_initial_agent_loop_state()
    sa, ra = run_agent_interaction_step(sa, "alpha line one")
    sb, rb = run_agent_interaction_step(sb, "alpha line one")
    da = build_reasoning_trace_report(ra.reasoning_trace).trace_digest_hex16
    db = build_reasoning_trace_report(rb.reasoning_trace).trace_digest_hex16
    assert da == db

    # 3. Distinct dispatch paths produce distinct reasoning-trace digests.
    sa = make_initial_agent_loop_state()
    sb = make_initial_agent_loop_state()
    sa, ra = run_agent_interaction_step(sa, "alpha line one")
    sb, rb = run_agent_interaction_step(sb, "EMIT ALPHA")
    da = build_reasoning_trace_report(ra.reasoning_trace).trace_digest_hex16
    db = build_reasoning_trace_report(rb.reasoning_trace).trace_digest_hex16
    assert da != db

    # 4. Renamed-transfer reasoning trace cites the second dispatch's digest.
    state = make_initial_agent_loop_state()
    state, _ = run_agent_interaction_step(state, "red blue red blue")
    state, r2 = run_agent_interaction_step(state, "cat dog cat dog")
    cdt_step = None
    for step in r2.reasoning_trace.steps:
        if step.kind is ReasoningStepKind.CHECK_DISPATCH_TRACE:
            cdt_step = step
    assert cdt_step is not None
    second_digest = r2.latest_dispatch_trace.trace_digest_hex16
    assert f"dispatch_digest={second_digest}" in cdt_step.input_facts

    # 5. ReasoningStepKind has exactly 11 values including check_dispatch_trace.
    expected_values = frozenset(
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
            "check_dispatch_trace",
            "emit_reply",
        }
    )
    actual = frozenset(k.value for k in ReasoningStepKind)
    assert actual == expected_values, sorted(actual)


@register("I-DTRACE-10", status="REQUIRED")
def check_learning_evidence_cites_dispatch_digest() -> None:
    """Audit DISPATCH_TRACE_RECORDED evidence on every interaction."""

    # 1. Single interaction: last record is DISPATCH_TRACE_RECORDED with
    # the expected fact keys.
    state = make_initial_agent_loop_state()
    state, r = run_agent_interaction_step(state, "alpha line one")
    last = state.learning_trace.records[-1]
    assert last.kind is LearningEvidenceKind.DISPATCH_TRACE_RECORDED

    pre_keys = {k for k, _ in last.pre_facts}
    post_keys = {k for k, _ in last.post_facts}
    assert "command_kind" in pre_keys
    assert {"dispatch_digest", "route_path", "mutation_kind"}.issubset(
        post_keys
    )
    post_lookup = {k: v for k, v in last.post_facts}
    assert (
        post_lookup["dispatch_digest"]
        == r.latest_dispatch_trace.trace_digest_hex16
    )

    # 2. After N interactions: dispatch_trace_recorded_count == N.
    state = make_initial_agent_loop_state()
    n = 4
    for _ in range(n):
        state, _ = run_agent_interaction_step(state, "alpha rep")
    report = build_learning_proof_report(state.learning_trace)
    assert report.dispatch_trace_recorded_count == n

    # 3. LearningEvidenceKind has exactly 9 values including the new kind.
    expected_values = frozenset(
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
        }
    )
    actual = frozenset(k.value for k in LearningEvidenceKind)
    assert actual == expected_values, sorted(actual)
