"""Phase 3.22 Agent benchmark session continuity fixture.

Drives ``I-AGENTLOOP-08`` (REQUIRED). Audits axis A6 (session
continuity): cumulative entry climb under 4 distinct texts,
monotonic seed-recurrence climb under 3 repeats, REPL+stream
interleave reply integrity.
"""
from __future__ import annotations

from brain.development.agent_benchmark import (
    BenchmarkAxis,
    BenchmarkCaseStatus,
    run_axis_a6_session_continuity,
)
from brain.invariants import register


@register("I-AGENTLOOP-08", status="REQUIRED")
def check_agent_benchmark_session_continuity() -> None:
    """Audit the session continuity axis (A6)."""
    ax = run_axis_a6_session_continuity()
    assert ax.axis is BenchmarkAxis.SESSION_CONTINUITY
    case_ids = tuple(c.case_id for c in ax.cases)
    assert case_ids == ("A6.01", "A6.02", "A6.03"), (
        f"I-AGENTLOOP-08 violated: A6 case ids drifted: {case_ids}"
    )
    for case in ax.cases:
        assert case.status is BenchmarkCaseStatus.PASS, (
            f"I-AGENTLOOP-08 violated: A6 case {case.case_id} not PASS: "
            f"summary={case.summary!r}"
        )
    assert ax.status is BenchmarkCaseStatus.PASS

    # Deterministic re-run.
    ax2 = run_axis_a6_session_continuity()
    assert ax == ax2, (
        "I-AGENTLOOP-08 violated: axis A6 is not deterministic"
    )
