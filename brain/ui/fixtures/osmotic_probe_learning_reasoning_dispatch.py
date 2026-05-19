"""Phase 3.25 learning + reasoning + dispatch trace integration.

Drives ``I-OSMO-09`` (REQUIRED), ``I-OSMO-10`` (REQUIRED),
``I-OSMO-11`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.osmotic_learning_probe import (
    build_osmotic_exposure_plan,
    run_osmotic_probe_trial,
)
from brain.invariants import register


def _trial_by_id(tid: str):
    for t in build_osmotic_exposure_plan():
        if t.trial_id == tid:
            return t
    raise AssertionError(f"trial {tid!r} not found")


@register("I-OSMO-09", status="REQUIRED")
def check_osmotic_learning_evidence_digest() -> None:
    """Learning evidence digest is deterministic + non-empty."""

    trial = _trial_by_id("T02_true_abab")
    r_a = run_osmotic_probe_trial(trial)
    r_b = run_osmotic_probe_trial(trial)
    assert len(r_a.learning_evidence_digest) == 16
    assert r_a.learning_evidence_digest != "0" * 16
    assert r_a.learning_evidence_digest == r_b.learning_evidence_digest, (
        f"I-OSMO-09 violated: learning evidence digest not deterministic: "
        f"{r_a.learning_evidence_digest!r} vs {r_b.learning_evidence_digest!r}"
    )

    # Control trials also have a deterministic digest (no records emitted
    # specifically about target, but the trace digest is well-defined).
    control = _trial_by_id("T01_control_abab")
    c_a = run_osmotic_probe_trial(control)
    c_b = run_osmotic_probe_trial(control)
    assert c_a.learning_evidence_digest == c_b.learning_evidence_digest


@register("I-OSMO-10", status="REQUIRED")
def check_osmotic_reasoning_trace_digest() -> None:
    """Reasoning trace digest is deterministic + non-empty."""

    trial = _trial_by_id("T02_true_abab")
    r_a = run_osmotic_probe_trial(trial)
    r_b = run_osmotic_probe_trial(trial)
    assert len(r_a.reasoning_trace_digest) == 16
    assert r_a.reasoning_trace_digest != "0" * 16
    assert r_a.reasoning_trace_digest == r_b.reasoning_trace_digest, (
        f"I-OSMO-10 violated: reasoning trace digest not deterministic"
    )


@register("I-OSMO-11", status="REQUIRED")
def check_osmotic_dispatch_trace_digests() -> None:
    """Dispatch trace digests present for every exposure + probe step."""

    plan = build_osmotic_exposure_plan()
    for trial in plan:
        result = run_osmotic_probe_trial(trial)
        expected_count = len(trial.exposure_texts) + 1  # +1 for the probe
        assert len(result.dispatch_trace_digests) == expected_count, (
            f"I-OSMO-11 violated: {trial.trial_id!r} expected "
            f"{expected_count} dispatch digests; got "
            f"{len(result.dispatch_trace_digests)}"
        )
        for d in result.dispatch_trace_digests:
            assert isinstance(d, str) and len(d) == 16, (
                f"I-OSMO-11 violated: {trial.trial_id!r} dispatch digest "
                f"{d!r} is not a 16-char hex string"
            )
