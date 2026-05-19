"""Phase 3.26 active hypothesis runner-green + benchmark axis fixture.

Drives ``I-AHYP-12`` and ``I-AHYP-13`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.active_hypothesis_probe import (
    ACTIVE_HYPOTHESIS_BATTERY_VERSION,
    ActiveHypothesisLiveTestReport,
    TrialVerdict,
    format_active_hypothesis_live_test_report,
    run_active_hypothesis_live_test,
)
from brain.development.agent_benchmark import (
    BATTERY_VERSION,
    BenchmarkAxis,
    BenchmarkCaseStatus,
    BenchmarkRun,
    run_axis_a13_active_hypothesis,
    run_full_battery,
    run_partial_battery_phase3_26,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.invariants import register


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-AHYP-12", status="REQUIRED")
def check_active_hypothesis_runner_green() -> None:
    """run_active_hypothesis_live_test() is deterministic + bounded + clean."""
    report_a = run_active_hypothesis_live_test()
    report_b = run_active_hypothesis_live_test()
    assert isinstance(report_a, ActiveHypothesisLiveTestReport)
    assert report_a.battery_version == ACTIVE_HYPOTHESIS_BATTERY_VERSION
    assert report_a.digest_hex16 == report_b.digest_hex16
    assert report_a.trials == report_b.trials

    assert len(report_a.trials) == 10
    assert report_a.pass_count == 10
    assert report_a.warn_count == 0
    assert report_a.fail_count == 0
    assert report_a.not_applicable_count == 0
    assert report_a.false_positive_count == 0
    assert report_a.false_negative_count == 0
    assert report_a.winner_selected_count == 3
    assert report_a.no_hypothesis_survives_count == 3
    assert report_a.cache_reuse_count == 2
    assert report_a.real_model_calls == 0
    assert report_a.cache_writes == 0
    assert report_a.forbidden_term_hits == 0

    # Every trial verdict is PASS; no forbidden term in any summary.
    for r in report_a.trials:
        assert r.verdict is TrialVerdict.PASS, (r.trial_id, r.verdict)
        assert _has_forbidden(r.summary_line) is None
        for ps in r.probe_steps:
            assert _has_forbidden(ps.reply_excerpt) is None

    formatted = format_active_hypothesis_live_test_report(report_a)
    assert _has_forbidden(formatted) is None


@register("I-AHYP-13", status="REQUIRED")
def check_active_hypothesis_benchmark_green() -> None:
    """A13 axis is green; BATTERY_VERSION bumped; full battery extended."""
    assert BATTERY_VERSION == "phase3.31.v1"

    # Axis-only run.
    a13 = run_axis_a13_active_hypothesis()
    assert a13.axis is BenchmarkAxis.ACTIVE_HYPOTHESIS
    assert len(a13.cases) == 14
    expected_ids = tuple(f"A13.{i:02d}" for i in range(1, 15))
    actual_ids = tuple(c.case_id for c in a13.cases)
    assert actual_ids == expected_ids, actual_ids
    for c in a13.cases:
        assert c.status is BenchmarkCaseStatus.PASS, (
            f"I-AHYP-13 violated: {c.case_id} not PASS ({c.status.value}): "
            f"{c.summary!r}"
        )

    # Partial-battery (A13 only).
    partial = run_partial_battery_phase3_26()
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
    run = run_full_battery()
    assert isinstance(run, BenchmarkRun)
    axes_seen = tuple(ax.axis for ax in run.axes)
    assert len(axes_seen) == 15
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
