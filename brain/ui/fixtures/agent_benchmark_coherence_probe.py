"""Phase 3.22 Agent benchmark coherence variation fixture.

Drives ``I-AGENTLOOP-06`` (REQUIRED). Audits the Phase 3.21 W3
follow-up: a deliberately-tilted CoherenceReport probe that
exercises the WARN / FAIL paths through public + bounded
dataclass-field-assignment levers.

Checks:

* ``run_axis_a3_coherence_variation()`` produces an AxisResult with
  the documented A3.01..A3.04 case ids.
* A3.01 reaches overall_status == "pass" on a fresh session.
* A3.02 reaches overall_status == "warn" via the
  ``stream_chunk_serial = 0`` lever.
* A3.03 reaches overall_status == "fail" via the
  ``active_view = "<not-in-set>"`` lever.
* A3.04 is recorded as WARN with a documented blocker line stating
  that overall NOT_APPLICABLE is not publicly reachable.
* Case notes are bounded printable and pass the forbidden-term audit.
* The axis aggregate status is WARN (because A3.04 is WARN with a
  documented blocker); the axis result still satisfies the Phase 3.21
  W3 follow-up criterion (pass + warn + fail demonstrated).
* ``run_partial_battery_with_coherence()`` produces 18 cases with
  case_failed == 0 (the only WARN is A3.04 with its documented
  blocker note).

No real model calls. No tick invocation.
"""
from __future__ import annotations

from brain.development.agent_benchmark import (
    BenchmarkAxis,
    BenchmarkCaseStatus,
    run_axis_a3_coherence_variation,
    run_partial_battery_with_coherence,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.invariants import register


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-AGENTLOOP-06", status="REQUIRED")
def check_agent_benchmark_coherence_probe() -> None:
    """Audit the coherence-variation probe (A3) end-to-end."""

    ax = run_axis_a3_coherence_variation()
    assert ax.axis is BenchmarkAxis.COHERENCE_VARIATION
    case_ids = tuple(c.case_id for c in ax.cases)
    assert case_ids == ("A3.01", "A3.02", "A3.03", "A3.04"), (
        f"I-AGENTLOOP-06 violated: A3 case ids drifted: {case_ids}"
    )

    by_id = {c.case_id: c for c in ax.cases}

    # A3.01 — pass reached.
    a3_01 = by_id["A3.01"]
    assert a3_01.status is BenchmarkCaseStatus.PASS
    assert "overall_status=pass" in a3_01.summary

    # A3.02 — warn reached via the documented lever.
    a3_02 = by_id["A3.02"]
    assert a3_02.status is BenchmarkCaseStatus.PASS, (
        f"I-AGENTLOOP-06 violated: A3.02 (warn lever) did not PASS: "
        f"summary={a3_02.summary!r}"
    )
    assert "overall=warn" in a3_02.summary

    # A3.03 — fail reached via the documented lever.
    a3_03 = by_id["A3.03"]
    assert a3_03.status is BenchmarkCaseStatus.PASS, (
        f"I-AGENTLOOP-06 violated: A3.03 (fail lever) did not PASS: "
        f"summary={a3_03.summary!r}"
    )
    assert "overall=fail" in a3_03.summary

    # A3.04 — not_applicable at overall level documented as not
    # publicly reachable. Recorded as WARN with a documented
    # blocker notes line.
    a3_04 = by_id["A3.04"]
    assert a3_04.status is BenchmarkCaseStatus.WARN, (
        f"I-AGENTLOOP-06 violated: A3.04 expected WARN, got "
        f"{a3_04.status.value}"
    )
    assert "not publicly reachable" in a3_04.notes.lower(), (
        f"I-AGENTLOOP-06 violated: A3.04 notes missing blocker text: "
        f"{a3_04.notes!r}"
    )

    # All notes and summaries non-claim-clean.
    for c in ax.cases:
        for text in (c.summary, c.notes):
            term = _has_forbidden(text)
            assert term is None, (
                f"I-AGENTLOOP-06 violated: A3 case {c.case_id} text "
                f"contains forbidden non-claim term {term!r}"
            )

    # 2. The axis status is WARN (because of A3.04 documented blocker).
    assert ax.status is BenchmarkCaseStatus.WARN, (
        f"I-AGENTLOOP-06 violated: A3 axis status expected WARN, got "
        f"{ax.status.value}"
    )

    # 3. Partial battery with coherence: 18 cases total, no FAIL,
    # the only WARN is A3.04 with documented blocker.
    run = run_partial_battery_with_coherence()
    assert run.case_total == 18
    assert run.case_failed == 0, (
        f"I-AGENTLOOP-06 violated: partial battery with coherence had "
        f"{run.case_failed} FAIL cases"
    )
    assert run.case_warned == 1, (
        f"I-AGENTLOOP-06 violated: partial battery with coherence had "
        f"{run.case_warned} WARN cases (expected exactly 1 — A3.04)"
    )
    assert run.case_passed == 17
    assert run.real_model_calls == 0
    assert run.cache_writes == 0
    assert run.forbidden_term_hits == 0
    assert run.determinism_failures == 0

    # 4. Determinism: two runs of the partial battery produce equal
    # transcript digests.
    run2 = run_partial_battery_with_coherence()
    assert run.transcript_digest_hex16 == run2.transcript_digest_hex16
