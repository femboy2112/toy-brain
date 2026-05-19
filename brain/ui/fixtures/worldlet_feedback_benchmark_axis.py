"""Phase 3.24 worldlet feedback benchmark axis fixture.

Drives ``I-WFDBK-11`` (REQUIRED). Audits the A11 worldlet_feedback
axis and the extended full battery.
"""
from __future__ import annotations

from brain.development.agent_benchmark import (
    BATTERY_VERSION,
    BenchmarkAxis,
    BenchmarkCaseStatus,
    BenchmarkRun,
    run_axis_a11_worldlet_feedback,
    run_full_battery,
    run_partial_battery_phase3_24,
)
from brain.invariants import register


@register("I-WFDBK-11", status="REQUIRED")
def check_worldlet_feedback_benchmark_green() -> None:
    """Audit the A11 worldlet_feedback axis + the extended full battery."""
    assert BATTERY_VERSION == "phase3.26.v1"

    # Axis-only run.
    a11 = run_axis_a11_worldlet_feedback()
    assert a11.axis is BenchmarkAxis.WORLDLET_FEEDBACK
    assert len(a11.cases) == 12
    expected_ids = tuple(f"A11.{i:02d}" for i in range(1, 13))
    actual_ids = tuple(c.case_id for c in a11.cases)
    assert actual_ids == expected_ids, actual_ids
    for c in a11.cases:
        assert c.status is BenchmarkCaseStatus.PASS, (
            f"I-WFDBK-11 violated: {c.case_id} not PASS ({c.status.value}): "
            f"{c.summary!r}"
        )

    # Partial-battery (A11 only).
    partial = run_partial_battery_phase3_24()
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
    # ACTIVE_HYPOTHESIS axis; WORLDLET_FEEDBACK is still present
    # but is no longer the last axis.
    run = run_full_battery()
    assert isinstance(run, BenchmarkRun)
    axes_seen = tuple(ax.axis for ax in run.axes)
    assert len(axes_seen) == 13
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

    # Determinism: two invocations produce equal transcript digests.
    run2 = run_full_battery()
    assert run.transcript_digest_hex16 == run2.transcript_digest_hex16
    assert run.transcripts == run2.transcripts
