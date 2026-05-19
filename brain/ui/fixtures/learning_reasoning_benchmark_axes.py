"""Phase 3.22b benchmark axes A8 + A9 fixture.

Drives ``I-AGENTLEARN-10`` (REQUIRED). Audits the partial-battery
runner ``run_partial_battery_phase3_22b`` and the per-axis case
counts for A8 learning_evidence and A9 reasoning_trace.
"""
from __future__ import annotations

from brain.development.agent_benchmark import (
    BATTERY_VERSION,
    BenchmarkAxis,
    BenchmarkCaseStatus,
    BenchmarkRun,
    run_axis_a8_learning_evidence,
    run_axis_a9_reasoning_trace,
    run_partial_battery_phase3_22b,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.invariants import register


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-AGENTLEARN-10", status="REQUIRED")
def check_learning_reasoning_benchmark_axes() -> None:
    """Audit A8 + A9 benchmark axes."""

    a8 = run_axis_a8_learning_evidence()
    assert a8.axis is BenchmarkAxis.LEARNING_EVIDENCE
    a8_ids = tuple(c.case_id for c in a8.cases)
    assert a8_ids == (
        "A8.01",
        "A8.02",
        "A8.03",
        "A8.04",
        "A8.05",
        "A8.06",
        "A8.07",
    )
    assert all(c.status is BenchmarkCaseStatus.PASS for c in a8.cases)

    a9 = run_axis_a9_reasoning_trace()
    assert a9.axis is BenchmarkAxis.REASONING_TRACE
    a9_ids = tuple(c.case_id for c in a9.cases)
    assert a9_ids == (
        "A9.01",
        "A9.02",
        "A9.03",
        "A9.04",
        "A9.05",
        "A9.06",
        "A9.07",
    )
    assert all(c.status is BenchmarkCaseStatus.PASS for c in a9.cases)

    run = run_partial_battery_phase3_22b()
    assert isinstance(run, BenchmarkRun)
    assert run.battery_version == BATTERY_VERSION
    assert run.case_total == 14
    assert run.case_passed == 14
    assert run.case_failed == 0
    assert run.case_warned == 0
    assert run.real_model_calls == 0
    assert run.cache_writes == 0
    assert run.forbidden_term_hits == 0
    assert run.determinism_failures == 0
    assert run.invariant_failures == 0

    # Determinism.
    run2 = run_partial_battery_phase3_22b()
    assert run.transcript_digest_hex16 == run2.transcript_digest_hex16
    assert run.transcripts == run2.transcripts

    # No transcript line contains a forbidden non-claim term.
    for line in run.transcripts:
        term = _has_forbidden(line)
        assert term is None, (
            "I-AGENTLEARN-10 violated: transcript line contains "
            f"forbidden term {term!r}: {line!r}"
        )
