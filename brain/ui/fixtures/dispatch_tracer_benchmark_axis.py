"""Phase 3.23 dispatch tracer benchmark axis fixture.

Drives ``I-DTRACE-11`` (REQUIRED). Audits that the A10 dispatch_trace
axis is green and that the full-battery runner reports the documented
totals.
"""
from __future__ import annotations

from brain.development.agent_benchmark import (
    BATTERY_VERSION,
    BenchmarkAxis,
    BenchmarkCaseStatus,
    BenchmarkRun,
    run_axis_a10_dispatch_trace,
    run_full_battery,
    run_partial_battery_phase3_23,
)
from brain.invariants import register


@register("I-DTRACE-11", status="REQUIRED")
def check_dispatch_tracer_benchmark_green() -> None:
    """Audit the A10 dispatch_trace axis and the extended full battery."""
    assert BATTERY_VERSION == "phase3.26.v1"

    # Axis-only run.
    a10 = run_axis_a10_dispatch_trace()
    assert a10.axis is BenchmarkAxis.DISPATCH_TRACE
    assert len(a10.cases) == 12
    expected_ids = tuple(f"A10.{i:02d}" for i in range(1, 13))
    actual_ids = tuple(c.case_id for c in a10.cases)
    assert actual_ids == expected_ids, actual_ids
    for c in a10.cases:
        assert c.status is BenchmarkCaseStatus.PASS, (
            f"I-DTRACE-11 violated: {c.case_id} not PASS ({c.status.value}): "
            f"{c.summary!r}"
        )

    # Partial-battery (A10 only).
    partial = run_partial_battery_phase3_23()
    assert isinstance(partial, BenchmarkRun)
    assert partial.case_total == 12
    assert partial.case_passed == 12
    assert partial.case_warned == 0
    assert partial.case_failed == 0
    assert partial.real_model_calls == 0
    assert partial.cache_writes == 0
    assert partial.forbidden_term_hits == 0
    assert partial.determinism_failures == 0
    assert partial.invariant_failures == 0

    # Full battery: thirteen axes in canonical order. Phase 3.26
    # widens the battery beyond OSMOTIC_LEARNING with the
    # ACTIVE_HYPOTHESIS axis; the ACTIVE_HYPOTHESIS axis is the last
    # axis in the tuple.
    run = run_full_battery()
    assert isinstance(run, BenchmarkRun)
    axes_seen = tuple(ax.axis for ax in run.axes)
    assert len(axes_seen) == 13
    assert BenchmarkAxis.DISPATCH_TRACE in axes_seen
    assert BenchmarkAxis.WORLDLET_FEEDBACK in axes_seen
    assert BenchmarkAxis.OSMOTIC_LEARNING in axes_seen
    assert axes_seen[-1] is BenchmarkAxis.ACTIVE_HYPOTHESIS
    assert run.case_total == 105
    assert run.case_warned == 1  # documented A3.04
    assert run.case_failed == 0
    assert run.real_model_calls == 0
    assert run.cache_writes == 0
    assert run.forbidden_term_hits == 0
    assert run.determinism_failures == 0
    assert run.invariant_failures == 0

    # Determinism: two invocations of run_full_battery produce equal
    # transcript digests and equal axis-case shapes.
    run2 = run_full_battery()
    assert run.transcript_digest_hex16 == run2.transcript_digest_hex16
    assert run.transcripts == run2.transcripts
