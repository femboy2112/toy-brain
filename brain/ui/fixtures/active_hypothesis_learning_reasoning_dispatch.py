"""Phase 3.26 learning + reasoning + dispatch citation fixture.

Drives ``I-AHYP-10`` and ``I-AHYP-11`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.active_hypothesis_probe import (
    ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN,
    run_active_hypothesis_live_test,
)
from brain.invariants import register


_HEX_CHARS = frozenset("0123456789abcdef")


def _is_16hex(s: str) -> bool:
    return (
        isinstance(s, str)
        and len(s) == ACTIVE_HYPOTHESIS_DIGEST_HEX_LEN
        and all(ch in _HEX_CHARS for ch in s)
    )


@register("I-AHYP-10", status="REQUIRED")
def check_active_hypothesis_learning_digest() -> None:
    """Every result cites a bounded deterministic learning digest."""
    report_a = run_active_hypothesis_live_test()
    report_b = run_active_hypothesis_live_test()
    assert report_a.digest_hex16 == report_b.digest_hex16
    for ra, rb in zip(report_a.trials, report_b.trials):
        assert _is_16hex(ra.learning_evidence_digest), ra.trial_id
        assert ra.learning_evidence_digest == rb.learning_evidence_digest, ra.trial_id


@register("I-AHYP-11", status="REQUIRED")
def check_active_hypothesis_reasoning_dispatch_digests() -> None:
    """Every result cites a bounded reasoning digest + dispatch digests tuple."""
    report = run_active_hypothesis_live_test()
    for r in report.trials:
        assert _is_16hex(r.reasoning_trace_digest), (r.trial_id, r.reasoning_trace_digest)
        assert isinstance(r.dispatch_trace_digests, tuple), r.trial_id
        # One dispatch digest per executed probe step.
        assert len(r.dispatch_trace_digests) == len(r.probe_steps), (
            r.trial_id,
            len(r.dispatch_trace_digests),
            len(r.probe_steps),
        )
        for d in r.dispatch_trace_digests:
            assert _is_16hex(d), (r.trial_id, d)
        for ps in r.probe_steps:
            assert _is_16hex(ps.reasoning_trace_digest), (r.trial_id, ps.candidate_id)
            assert _is_16hex(ps.dispatch_trace_digest), (r.trial_id, ps.candidate_id)
