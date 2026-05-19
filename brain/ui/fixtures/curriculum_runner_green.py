"""Phase 3.30 curriculum runner-green + benchmark axis fixture.

Drives ``I-CURR-13`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.agent_benchmark import (
    BATTERY_VERSION,
    BenchmarkAxis,
    BenchmarkCaseStatus,
    BenchmarkRun,
    run_axis_a14_curriculum_consolidation,
    run_full_battery,
    run_partial_battery_phase3_30,
)
from brain.invariants import register


@register("I-CURR-13", status="REQUIRED")
def check_curriculum_benchmark_green() -> None:
    """A14 axis green; BATTERY_VERSION bumped; full battery extended."""
    assert BATTERY_VERSION == "phase3.31.v1"

    # Axis-only run.
    a14 = run_axis_a14_curriculum_consolidation()
    assert a14.axis is BenchmarkAxis.CURRICULUM_CONSOLIDATION
    assert len(a14.cases) == 14
    expected_ids = tuple(f"A14.{i:02d}" for i in range(1, 15))
    actual_ids = tuple(c.case_id for c in a14.cases)
    assert actual_ids == expected_ids, actual_ids
    for c in a14.cases:
        assert c.status is BenchmarkCaseStatus.PASS, (
            f"I-CURR-13 violated: {c.case_id} not PASS ({c.status.value}): "
            f"{c.summary!r}"
        )

    # Partial-battery (A14 only).
    partial = run_partial_battery_phase3_30()
    assert isinstance(partial, BenchmarkRun)
    assert partial.case_total == 14
    assert partial.case_passed == 14
    assert partial.case_warned == 0
    assert partial.case_failed == 0
    assert partial.real_model_calls == 0
    assert partial.cache_writes == 0
    assert partial.forbidden_term_hits == 0
    assert partial.determinism_failures == 0
    assert partial.invariant_failures == 0

    # Full battery: fifteen axes ending with PROTO_SPEECH_ACQUISITION.
    # CURRICULUM_CONSOLIDATION is still present but is no longer the
    # last axis (Phase 3.31 widens the battery).
    run = run_full_battery()
    assert isinstance(run, BenchmarkRun)
    axes_seen = tuple(ax.axis for ax in run.axes)
    assert len(axes_seen) == 15
    assert BenchmarkAxis.CURRICULUM_CONSOLIDATION in axes_seen
    assert axes_seen[-1] is BenchmarkAxis.PROTO_SPEECH_ACQUISITION
    assert run.case_total == 137
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
