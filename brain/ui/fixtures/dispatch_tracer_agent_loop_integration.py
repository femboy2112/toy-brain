"""Phase 3.23 dispatch tracer AgentLoopResult integration fixture.

Drives ``I-DTRACE-08`` (REQUIRED). Audits that ``AgentLoopResult``
carries a bounded ``DispatchTraceReport`` on every interaction (real
on the STREAM_APPEND path, synthetic on the REFUSAL / FAIL / WARN-empty
/ REPL-bridge paths).
"""
from __future__ import annotations

from brain.development.agent_loop import (
    AgentLoopResult,
    make_initial_agent_loop_state,
    run_agent_interaction_step,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.dispatch_tracer import (
    DispatchMutationKind,
    DispatchTraceReport,
)
from brain.invariants import register


@register("I-DTRACE-08", status="REQUIRED")
def check_agent_loop_result_carries_dispatch_trace() -> None:
    """Audit AgentLoopResult.latest_dispatch_trace across loop paths."""

    # STREAM_APPEND path: result.latest_dispatch_trace is the session's
    # latest_dispatch_trace (identity reference) and the mutation kind
    # is STREAM_APPEND.
    state = make_initial_agent_loop_state()
    state, r = run_agent_interaction_step(state, "alpha line one")
    assert isinstance(r, AgentLoopResult)
    assert isinstance(r.latest_dispatch_trace, DispatchTraceReport)
    assert r.latest_dispatch_trace is state.session.latest_dispatch_trace
    assert (
        r.latest_dispatch_trace.mutation_kind
        is DispatchMutationKind.STREAM_APPEND
    )
    stream_digest = r.latest_dispatch_trace.trace_digest_hex16
    assert len(stream_digest) == 16

    # REFUSAL path: synthetic trace, no session dispatch.
    state = make_initial_agent_loop_state()
    pre_session_trace = state.session.latest_dispatch_trace
    carrier = f"a query about {_FORBIDDEN_NON_CLAIM_TERMS[0]}"
    state, r = run_agent_interaction_step(state, carrier)
    assert r.latest_dispatch_trace is not None
    assert r.latest_dispatch_trace.mutation_kind is DispatchMutationKind.NONE
    assert r.latest_dispatch_trace.route_path == "refusal-no-dispatch"
    # The session itself was not dispatched against, so its
    # latest_dispatch_trace stays at its pre-call value.
    assert state.session.latest_dispatch_trace is pre_session_trace

    # FAIL-oversize path.
    state = make_initial_agent_loop_state()
    oversize = "x" * 4096
    state, r = run_agent_interaction_step(state, oversize)
    assert r.latest_dispatch_trace is not None
    assert r.latest_dispatch_trace.mutation_kind is DispatchMutationKind.NONE
    assert r.latest_dispatch_trace.route_path == "fail-no-dispatch"

    # WARN-empty path.
    state = make_initial_agent_loop_state()
    state, r = run_agent_interaction_step(state, "")
    assert r.latest_dispatch_trace is not None
    assert r.latest_dispatch_trace.mutation_kind is DispatchMutationKind.NONE
    assert r.latest_dispatch_trace.route_path == "warn-no-dispatch"

    # REPL-bridge path.
    state = make_initial_agent_loop_state()
    state, r = run_agent_interaction_step(state, "EMIT ALPHA")
    assert r.latest_dispatch_trace is not None
    assert r.latest_dispatch_trace.mutation_kind is DispatchMutationKind.NONE
    assert r.latest_dispatch_trace.route_path == "repl-bridge"

    # Determinism across two fresh sessions.
    sa = make_initial_agent_loop_state()
    sb = make_initial_agent_loop_state()
    sa, ra = run_agent_interaction_step(sa, "alpha line one")
    sb, rb = run_agent_interaction_step(sb, "alpha line one")
    assert (
        ra.latest_dispatch_trace.trace_digest_hex16
        == rb.latest_dispatch_trace.trace_digest_hex16
    )
