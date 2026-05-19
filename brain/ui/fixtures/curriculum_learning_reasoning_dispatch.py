"""Phase 3.30 learning + reasoning + dispatch wiring + determinism fixture.

Drives ``I-CURR-10`` (REQUIRED), ``I-CURR-11`` (REQUIRED),
and ``I-CURR-12`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.curriculum_consolidation_probe import (
    CURRICULUM_DIGEST_HEX_LEN,
    CurriculumConsolidationReport,
    format_curriculum_consolidation_report,
    run_curriculum_consolidation_live_test,
)
from brain.invariants import register


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


def _hex16_ok(value: str) -> bool:
    return isinstance(value, str) and len(value) == CURRICULUM_DIGEST_HEX_LEN


@register("I-CURR-10", status="REQUIRED")
def check_curriculum_learning_reasoning_dispatch_citations() -> None:
    """Each result cites bounded learning / reasoning / dispatch digests; stable."""
    report_a = run_curriculum_consolidation_live_test()
    report_b = run_curriculum_consolidation_live_test()

    assert isinstance(report_a, CurriculumConsolidationReport)
    assert len(report_a.trials) == 10

    # Build a trial-by-id map of expected dispatch tuple length.
    for r_a, r_b in zip(report_a.trials, report_b.trials):
        assert _hex16_ok(r_a.learning_evidence_digest)
        assert _hex16_ok(r_a.reasoning_trace_digest)
        assert isinstance(r_a.dispatch_trace_digests, tuple)
        for d in r_a.dispatch_trace_digests:
            assert _hex16_ok(d)
        # Determinism per trial.
        assert r_a.learning_evidence_digest == r_b.learning_evidence_digest, (
            r_a.trial_id
        )
        assert r_a.reasoning_trace_digest == r_b.reasoning_trace_digest, (
            r_a.trial_id
        )
        assert r_a.dispatch_trace_digests == r_b.dispatch_trace_digests, (
            r_a.trial_id
        )


@register("I-CURR-11", status="REQUIRED")
def check_curriculum_runner_determinism() -> None:
    """run_curriculum_consolidation_live_test digest is bit-identical across runs."""
    report_a = run_curriculum_consolidation_live_test()
    report_b = run_curriculum_consolidation_live_test()
    assert report_a.digest_hex16 == report_b.digest_hex16
    assert report_a.trials == report_b.trials
    assert report_a.real_model_calls == 0
    assert report_a.cache_writes == 0
    assert report_a.forbidden_term_hits == 0


@register("I-CURR-12", status="REQUIRED")
def check_curriculum_runner_non_claim_clean() -> None:
    """Every produced string is non-claim-clean; forbidden_term_hits == 0."""
    report = run_curriculum_consolidation_live_test()
    assert _has_forbidden(report.summary_line) is None
    for r in report.trials:
        assert _has_forbidden(r.summary_line) is None, (r.trial_id, r.summary_line)
        if r.probe_step is not None:
            assert _has_forbidden(r.probe_step.summary_line) is None, (
                r.trial_id, r.probe_step.summary_line
            )
            assert _has_forbidden(r.probe_step.reply_excerpt) is None, (
                r.trial_id, r.probe_step.reply_excerpt
            )
    formatted = format_curriculum_consolidation_report(report)
    assert _has_forbidden(formatted) is None
    assert report.forbidden_term_hits == 0
