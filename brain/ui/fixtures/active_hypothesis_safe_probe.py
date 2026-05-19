"""Phase 3.26 safe-probe non-leakage fixture.

Drives ``I-AHYP-04`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.active_hypothesis_probe import (
    ACTIVE_HYPOTHESIS_PROBE_MAX_LEN,
    _FORBIDDEN_DIRECT_INSTRUCTION_TERMS,
    build_active_hypothesis_trials,
    enumerate_hypotheses,
    select_safe_probe,
)
from brain.invariants import register


@register("I-AHYP-04", status="REQUIRED")
def check_active_hypothesis_safe_probe() -> None:
    """select_safe_probe is bounded, non-leaking, forbidden-term-clean."""
    probe_total = 0
    for trial in build_active_hypothesis_trials():
        for cand in enumerate_hypotheses(trial.input_text):
            probe = select_safe_probe(trial.input_text, cand)
            probe_total += 1
            assert isinstance(probe, str)
            assert 0 < len(probe) <= ACTIVE_HYPOTHESIS_PROBE_MAX_LEN
            assert probe.isprintable()
            lowered = probe.lower()
            for term in _FORBIDDEN_DIRECT_INSTRUCTION_TERMS:
                assert term not in lowered, (
                    f"I-AHYP-04 violated: probe text {probe!r} contains "
                    f"forbidden direct-instruction term {term!r}"
                )
            assert cand.predicted_digest_hex16 not in probe
            if cand.predicted_shape:
                assert cand.predicted_shape not in probe

    # Probe text is generated for every non-control trial.
    assert probe_total >= 32, probe_total
