"""Phase 3.25 live-test runner + benchmark axis green fixture.

Drives ``I-OSMO-12`` (REQUIRED) and ``I-OSMO-13`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.agent_benchmark import (
    BATTERY_VERSION,
    BenchmarkAxis,
    BenchmarkCaseStatus,
    BenchmarkRun,
    run_axis_a12_osmotic_learning,
    run_full_battery,
    run_partial_battery_phase3_25,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.osmotic_learning_probe import (
    OSMOTIC_PROBE_BATTERY_VERSION,
    format_osmotic_live_test_report,
    run_osmotic_live_test,
)
from brain.invariants import register


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-OSMO-12", status="REQUIRED")
def check_osmotic_live_test_determinism() -> None:
    """Live-test report digest is deterministic + bounded + non-claim-clean."""

    report_a = run_osmotic_live_test()
    report_b = run_osmotic_live_test()
    assert report_a.battery_version == OSMOTIC_PROBE_BATTERY_VERSION
    assert report_a.digest_hex16 == report_b.digest_hex16, (
        f"I-OSMO-12 violated: report digest not deterministic: "
        f"{report_a.digest_hex16!r} vs {report_b.digest_hex16!r}"
    )
    assert report_a.trials == report_b.trials

    # v1 plan totals.
    assert len(report_a.trials) == 10
    assert report_a.pass_count == 10
    assert report_a.warn_count == 0
    assert report_a.fail_count == 0
    assert report_a.not_applicable_count == 0
    assert report_a.false_positive_count == 0
    assert report_a.false_negative_count == 0
    assert report_a.transfer_success_count == 7
    assert report_a.real_model_calls == 0
    assert report_a.cache_writes == 0
    assert report_a.forbidden_term_hits == 0

    # format_osmotic_live_test_report returns bounded printable text
    # with no forbidden non-claim terms.
    text = format_osmotic_live_test_report(report_a)
    assert isinstance(text, str) and text
    # The output is multi-line; check every line is printable / non-empty.
    for line in text.splitlines():
        assert line.isprintable() or line == ""
        term = _has_forbidden(line)
        assert term is None, (
            f"I-OSMO-12 violated: report line contains forbidden non-claim "
            f"term {term!r}: {line!r}"
        )


@register("I-OSMO-13", status="REQUIRED")
def check_osmotic_benchmark_axis_green() -> None:
    """A12 osmotic_learning axis is green + extended full battery."""
    assert BATTERY_VERSION == "phase3.31.v1"

    # Axis-only run.
    a12 = run_axis_a12_osmotic_learning()
    assert a12.axis is BenchmarkAxis.OSMOTIC_LEARNING
    assert len(a12.cases) == 14
    expected_ids = tuple(f"A12.{i:02d}" for i in range(1, 15))
    actual_ids = tuple(c.case_id for c in a12.cases)
    assert actual_ids == expected_ids, actual_ids
    for c in a12.cases:
        assert c.status is BenchmarkCaseStatus.PASS, (
            f"I-OSMO-13 violated: {c.case_id} not PASS "
            f"({c.status.value}): {c.summary!r}"
        )

    # Partial-battery (A12 only).
    partial = run_partial_battery_phase3_25()
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

    # Full battery: fifteen axes in canonical order ending with
    # PROTO_SPEECH_ACQUISITION. OSMOTIC_LEARNING is still present but
    # is no longer the last axis (Phase 3.26..3.31 widen the battery).
    run = run_full_battery()
    assert isinstance(run, BenchmarkRun)
    axes_seen = tuple(ax.axis for ax in run.axes)
    assert len(axes_seen) == 15
    assert BenchmarkAxis.OSMOTIC_LEARNING in axes_seen
    assert BenchmarkAxis.ACTIVE_HYPOTHESIS in axes_seen
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
