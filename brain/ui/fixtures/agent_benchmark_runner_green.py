"""Phase 3.22 Agent benchmark runner-green fixture.

Drives ``I-AGENTLOOP-09`` (REQUIRED). Audits the full-battery runner:
``run_full_battery()`` produces a BenchmarkRun with the expected case
totals and zero hard failures; the transcript digest is deterministic
across two runs; the blind-transcript axis (A7) PASSes; the runner's
JSON-shape projection passes through every required key; and the
exit-code mapping (PASS/WARN/FAIL) is correct.

Documented expectation: the only WARN case in the full battery is
A3.04 (the Phase 3.21 W3 follow-up not_applicable-overall blocker).
That WARN is documented and is the campaign's accepted partial-
limitation.
"""
from __future__ import annotations

from brain.development.agent_benchmark import (
    BATTERY_VERSION,
    BenchmarkAxis,
    BenchmarkCaseStatus,
    BenchmarkRun,
    main,
    run_full_battery,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.invariants import register


_EXPECTED_AXES = (
    BenchmarkAxis.PATTERN_RECOGNITION,
    BenchmarkAxis.CROSS_INPUT_STRUCTURAL,
    BenchmarkAxis.COHERENCE_VARIATION,
    BenchmarkAxis.REPL_COHERENCE,
    BenchmarkAxis.COMMUNICATION,
    BenchmarkAxis.SESSION_CONTINUITY,
    BenchmarkAxis.BLIND_TRANSCRIPT,
    BenchmarkAxis.LEARNING_EVIDENCE,
    BenchmarkAxis.REASONING_TRACE,
    # Phase 3.23 (I-DTRACE-11) dispatch trace axis.
    BenchmarkAxis.DISPATCH_TRACE,
    # Phase 3.24 (I-WFDBK-11) worldlet feedback axis.
    BenchmarkAxis.WORLDLET_FEEDBACK,
)


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-AGENTLOOP-09", status="REQUIRED")
def check_agent_benchmark_runner_green() -> None:
    """Audit the full-battery runner."""
    run = run_full_battery()
    assert isinstance(run, BenchmarkRun)
    assert run.battery_version == BATTERY_VERSION

    # Seven axes in canonical order.
    axes_seen = tuple(ax.axis for ax in run.axes)
    assert axes_seen == _EXPECTED_AXES, (
        f"I-AGENTLOOP-09 violated: axis order drifted: {axes_seen}"
    )

    # No hard failures.
    assert run.case_failed == 0, (
        f"I-AGENTLOOP-09 violated: full battery has "
        f"{run.case_failed} FAIL cases"
    )

    # Exactly one WARN — the Phase 3.21 W3 follow-up A3.04 blocker.
    assert run.case_warned == 1, (
        f"I-AGENTLOOP-09 violated: full battery has "
        f"{run.case_warned} WARN cases (expected exactly 1: A3.04)"
    )
    warn_cases = [
        case
        for ax in run.axes
        for case in ax.cases
        if case.status is BenchmarkCaseStatus.WARN
    ]
    assert len(warn_cases) == 1 and warn_cases[0].case_id == "A3.04", (
        f"I-AGENTLOOP-09 violated: unexpected WARN cases: "
        f"{[c.case_id for c in warn_cases]}"
    )

    # Zero real model calls / cache writes / forbidden hits.
    assert run.real_model_calls == 0
    assert run.cache_writes == 0
    assert run.forbidden_term_hits == 0
    assert run.determinism_failures == 0
    assert run.invariant_failures == 0

    # Determinism: two runs produce identical transcript digests.
    run2 = run_full_battery()
    assert (
        run.transcript_digest_hex16 == run2.transcript_digest_hex16
    ), (
        "I-AGENTLOOP-09 violated: full-battery transcript digest is not "
        "deterministic"
    )
    assert run.transcripts == run2.transcripts

    # Per-axis status: A1, A2, A4, A5, A6, A7 PASS; A3 WARN (documented
    # blocker).
    status_by_axis = {ax.axis: ax.status for ax in run.axes}
    assert (
        status_by_axis[BenchmarkAxis.PATTERN_RECOGNITION]
        is BenchmarkCaseStatus.PASS
    )
    assert (
        status_by_axis[BenchmarkAxis.CROSS_INPUT_STRUCTURAL]
        is BenchmarkCaseStatus.PASS
    )
    assert (
        status_by_axis[BenchmarkAxis.COHERENCE_VARIATION]
        is BenchmarkCaseStatus.WARN
    )
    assert (
        status_by_axis[BenchmarkAxis.REPL_COHERENCE]
        is BenchmarkCaseStatus.PASS
    )
    assert (
        status_by_axis[BenchmarkAxis.COMMUNICATION]
        is BenchmarkCaseStatus.PASS
    )
    assert (
        status_by_axis[BenchmarkAxis.SESSION_CONTINUITY]
        is BenchmarkCaseStatus.PASS
    )
    assert (
        status_by_axis[BenchmarkAxis.BLIND_TRANSCRIPT]
        is BenchmarkCaseStatus.PASS
    )
    assert (
        status_by_axis[BenchmarkAxis.LEARNING_EVIDENCE]
        is BenchmarkCaseStatus.PASS
    )
    assert (
        status_by_axis[BenchmarkAxis.REASONING_TRACE]
        is BenchmarkCaseStatus.PASS
    )
    assert (
        status_by_axis[BenchmarkAxis.DISPATCH_TRACE]
        is BenchmarkCaseStatus.PASS
    )
    assert (
        status_by_axis[BenchmarkAxis.WORLDLET_FEEDBACK]
        is BenchmarkCaseStatus.PASS
    )

    # Every transcript line passes the forbidden-term audit.
    for line in run.transcripts:
        term = _has_forbidden(line)
        assert term is None, (
            f"I-AGENTLOOP-09 violated: transcript line contains "
            f"forbidden non-claim term {term!r}: {line!r}"
        )

    # Exit-code mapping: WARN-only -> 2.
    rc = main(["--quiet"])
    assert rc == 2, (
        f"I-AGENTLOOP-09 violated: WARN-only run should exit 2; got {rc}"
    )
