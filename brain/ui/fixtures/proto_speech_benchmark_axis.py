"""Phase 3.31 benchmark axis A15 green fixture.

Drives ``I-PSPEECH-18`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.agent_benchmark import (
    BATTERY_VERSION,
    BenchmarkAxis,
    BenchmarkCaseStatus,
    run_axis_a15_proto_speech_acquisition,
    run_full_battery,
    run_partial_battery_phase3_31,
)
from brain.invariants import register


_EXPECTED_CASE_IDS = tuple(f"A15.{i:02d}" for i in range(1, 19))


@register("I-PSPEECH-18", status="REQUIRED")
def check_proto_speech_benchmark_axis_green() -> None:
    """A15 proto_speech_acquisition battery is green."""
    assert BATTERY_VERSION == "phase3.31.v1", BATTERY_VERSION

    axis = run_axis_a15_proto_speech_acquisition()
    assert axis.axis is BenchmarkAxis.PROTO_SPEECH_ACQUISITION
    case_ids = tuple(c.case_id for c in axis.cases)
    assert case_ids == _EXPECTED_CASE_IDS, case_ids
    for c in axis.cases:
        assert c.status is BenchmarkCaseStatus.PASS, (
            f"{c.case_id} -> {c.status.value}: {c.summary}"
        )

    partial = run_partial_battery_phase3_31()
    assert partial.case_total == 18
    assert partial.case_passed == 18
    assert partial.case_failed == 0
    assert partial.case_warned == 0
    assert partial.real_model_calls == 0
    assert partial.cache_writes == 0
    assert partial.forbidden_term_hits == 0
    assert partial.determinism_failures == 0

    full = run_full_battery()
    assert len(full.axes) == 15
    assert full.axes[-1].axis is BenchmarkAxis.PROTO_SPEECH_ACQUISITION
    assert full.case_total == 137
    assert full.case_warned == 1  # A3.04 carry-over
    assert full.case_failed == 0
    assert full.real_model_calls == 0

    # Two invocations produce equal transcript_digest_hex16.
    full_b = run_full_battery()
    assert full.transcript_digest_hex16 == full_b.transcript_digest_hex16
