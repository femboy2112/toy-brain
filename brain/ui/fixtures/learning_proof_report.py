"""Phase 3.22b learning proof report fixture.

Drives ``I-AGENTLEARN-04`` (REQUIRED). Audits
``build_learning_proof_report`` for deterministic digest production
and bounded printable summary.
"""
from __future__ import annotations

from brain.development.agent_loop import (
    make_initial_agent_loop_state,
    run_agent_interaction_step,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.learning_evidence import (
    LEARNING_DIGEST_HEX_LEN,
    LearningProofReport,
    build_learning_proof_report,
)
from brain.invariants import register


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-AGENTLEARN-04", status="REQUIRED")
def check_learning_proof_report() -> None:
    """Audit LearningProofReport determinism + audit."""

    # Build identical traces in two fresh sessions.
    seq = (
        "alpha line one",
        "alpha line one",
        "red blue red blue",
        "cat dog cat dog",
        "EMIT ALPHA",
        "EMIT ALPHA",
    )
    state_a = make_initial_agent_loop_state()
    state_b = make_initial_agent_loop_state()
    for text in seq:
        state_a, _ = run_agent_interaction_step(state_a, text)
        state_b, _ = run_agent_interaction_step(state_b, text)
    report_a = build_learning_proof_report(state_a.learning_trace)
    report_b = build_learning_proof_report(state_b.learning_trace)

    assert isinstance(report_a, LearningProofReport)
    assert len(report_a.digest_hex16) == LEARNING_DIGEST_HEX_LEN
    assert report_a.digest_hex16 == report_b.digest_hex16, (
        "I-AGENTLEARN-04 violated: proof digest must be deterministic"
    )
    assert report_a.record_total >= 5
    assert report_a.summary_line.startswith("learning-proof")
    assert report_a.summary_line.isprintable()
    term = _has_forbidden(report_a.summary_line)
    assert term is None, (
        f"I-AGENTLEARN-04 violated: summary contains forbidden term {term!r}"
    )

    # Per-kind counts sum to record_total.
    counts_sum = (
        report_a.observed_count
        + report_a.recurrence_increased_count
        + report_a.abstract_pattern_acquired_count
        + report_a.abstract_pattern_reused_count
        + report_a.transfer_recognized_count
        + report_a.repl_correction_applied_count
        + report_a.diminishing_returns_updated_count
        + report_a.limitation_recorded_count
        + report_a.dispatch_trace_recorded_count
    )
    assert counts_sum == report_a.record_total

    # The full battery seq is expected to produce some of each kind.
    assert report_a.abstract_pattern_acquired_count >= 1
    assert report_a.transfer_recognized_count >= 1
    assert report_a.recurrence_increased_count >= 1
    assert report_a.diminishing_returns_updated_count >= 1
