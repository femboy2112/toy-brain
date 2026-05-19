"""Phase 3.22 Agent benchmark REPL axis fixture.

Drives ``I-AGENTLOOP-07`` (REQUIRED). Audits axis A4 (REPL coherence)
of the agent benchmark battery: valid command, near-miss with
correction hint, syntax-invalid no-history-mutation, diminishing-
returns sequence, and the bridge summary projection.
"""
from __future__ import annotations

from brain.development.agent_benchmark import (
    BenchmarkAxis,
    BenchmarkCaseStatus,
    run_axis_a4_repl_coherence,
)
from brain.invariants import register


@register("I-AGENTLOOP-07", status="REQUIRED")
def check_agent_benchmark_repl_axes() -> None:
    """Audit the REPL coherence axis (A4)."""
    ax = run_axis_a4_repl_coherence()
    assert ax.axis is BenchmarkAxis.REPL_COHERENCE
    case_ids = tuple(c.case_id for c in ax.cases)
    assert case_ids == ("A4.01", "A4.02", "A4.03", "A4.04", "A4.05"), (
        f"I-AGENTLOOP-07 violated: A4 case ids drifted: {case_ids}"
    )
    for case in ax.cases:
        assert case.status is BenchmarkCaseStatus.PASS, (
            f"I-AGENTLOOP-07 violated: A4 case {case.case_id} not PASS: "
            f"summary={case.summary!r}"
        )
    assert ax.status is BenchmarkCaseStatus.PASS

    # Deterministic re-run.
    ax2 = run_axis_a4_repl_coherence()
    assert ax == ax2, (
        "I-AGENTLOOP-07 violated: axis A4 is not deterministic across runs"
    )
