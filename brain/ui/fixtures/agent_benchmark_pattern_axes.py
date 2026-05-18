"""Phase 3.22 Agent benchmark pattern axes fixture.

Drives ``I-AGENTLOOP-05`` (REQUIRED). Audits the pattern-recognition
benchmark axes (A1 and A2) and the partial-battery runner.

Checks:

* ``run_axis_a1_pattern_recognition()`` produces a PASS AxisResult
  whose cases include the documented A1.01..A1.09 ids.
* ``run_axis_a2_cross_input_structural()`` produces a PASS AxisResult
  whose cases include the documented A2.01..A2.05 ids.
* The partial-battery runner produces a BenchmarkRun with
  ``case_total == 14``, ``case_passed == 14``, zero failures, zero
  real model calls, zero cache writes, zero forbidden-term hits.
* The transcript digest is deterministic: two runs yield identical
  ``transcript_digest_hex16``.
* Every produced transcript line is bounded printable and passes
  the forbidden-term audit.

No real model calls. No tick invocation. No filesystem / network.
"""
from __future__ import annotations

from brain.development.agent_benchmark import (
    BATTERY_VERSION,
    AxisResult,
    BenchmarkAxis,
    BenchmarkCaseStatus,
    BenchmarkRun,
    run_axis_a1_pattern_recognition,
    run_axis_a2_cross_input_structural,
    run_partial_battery_pattern_axes,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.invariants import register


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-AGENTLOOP-05", status="REQUIRED")
def check_agent_benchmark_pattern_axes() -> None:
    """Audit the pattern-axis battery (A1 + A2)."""

    # 1. A1 axis.
    ax1 = run_axis_a1_pattern_recognition()
    assert isinstance(ax1, AxisResult)
    assert ax1.axis is BenchmarkAxis.PATTERN_RECOGNITION
    a1_case_ids = tuple(c.case_id for c in ax1.cases)
    assert a1_case_ids == (
        "A1.01",
        "A1.02",
        "A1.03",
        "A1.04",
        "A1.05",
        "A1.06",
        "A1.07",
        "A1.08",
        "A1.09",
    ), f"I-AGENTLOOP-05 violated: A1 case ids drifted: {a1_case_ids}"
    for case in ax1.cases:
        assert case.status is BenchmarkCaseStatus.PASS, (
            f"I-AGENTLOOP-05 violated: A1 case {case.case_id} not PASS: "
            f"status={case.status.value} summary={case.summary!r}"
        )
    assert ax1.status is BenchmarkCaseStatus.PASS

    # 2. A2 axis.
    ax2 = run_axis_a2_cross_input_structural()
    assert isinstance(ax2, AxisResult)
    assert ax2.axis is BenchmarkAxis.CROSS_INPUT_STRUCTURAL
    a2_case_ids = tuple(c.case_id for c in ax2.cases)
    assert a2_case_ids == (
        "A2.01",
        "A2.02",
        "A2.03",
        "A2.04",
        "A2.05",
    ), f"I-AGENTLOOP-05 violated: A2 case ids drifted: {a2_case_ids}"
    for case in ax2.cases:
        assert case.status is BenchmarkCaseStatus.PASS, (
            f"I-AGENTLOOP-05 violated: A2 case {case.case_id} not PASS: "
            f"status={case.status.value} summary={case.summary!r}"
        )
    assert ax2.status is BenchmarkCaseStatus.PASS

    # 3. Partial battery runner.
    run = run_partial_battery_pattern_axes()
    assert isinstance(run, BenchmarkRun)
    assert run.battery_version == BATTERY_VERSION
    assert run.case_total == 14
    assert run.case_passed == 14
    assert run.case_warned == 0
    assert run.case_failed == 0
    assert run.determinism_failures == 0
    assert run.invariant_failures == 0
    assert run.real_model_calls == 0
    assert run.cache_writes == 0
    assert run.forbidden_term_hits == 0
    assert len(run.transcript_digest_hex16) == 16
    assert all(c in "0123456789abcdef" for c in run.transcript_digest_hex16)

    # 4. Transcript determinism: two runs produce equal digests.
    run2 = run_partial_battery_pattern_axes()
    assert (
        run.transcript_digest_hex16 == run2.transcript_digest_hex16
    ), (
        "I-AGENTLOOP-05 violated: partial-battery transcript digest "
        "is not deterministic"
    )
    assert run.transcripts == run2.transcripts

    # 5. Every transcript line is bounded printable + non-claim-clean.
    for line in run.transcripts:
        assert isinstance(line, str) and line.isprintable()
        term = _has_forbidden(line)
        assert term is None, (
            "I-AGENTLOOP-05 violated: transcript line contains "
            f"forbidden non-claim term {term!r}: {line!r}"
        )
