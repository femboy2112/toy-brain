"""Phase 3.30 curriculum plan builder fixture.

Drives ``I-CURR-03`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.curriculum_consolidation_probe import (
    CURRICULUM_INPUT_MAX_LEN,
    CURRICULUM_MAX_EXPOSURES_PER_TRIAL,
    CurriculumCondition,
    CurriculumExposure,
    build_curriculum_plan,
)
from brain.invariants import register


_FORBIDDEN_DIRECT_INSTRUCTION_TERMS: tuple[str, ...] = (
    "learn", "remember", "pattern", "classify", "transfer", "reuse",
    "abab", "abba", "abcabc", "structure", "imprint", "osmotic",
    "absorb", "imbibe", "intuition", "hypothesis", "candidate",
    "predict", "falsify", "decide", "infer", "wonder",
    "curriculum", "accumulate", "consolidate", "audit", "interfere",
    "forget",
)


def _has_forbidden_direct(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_DIRECT_INSTRUCTION_TERMS:
        if term in lowered:
            return term
    return None


def _has_forbidden_non_claim(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-CURR-03", status="REQUIRED")
def check_curriculum_enumerator() -> None:
    """build_curriculum_plan is deterministic, bounded, non-claim clean."""
    expected_lengths = {
        CurriculumCondition.SINGLE_STRUCTURE: 1,
        CurriculumCondition.SEQUENTIAL_NONINTERFERING: 2,
        CurriculumCondition.SEQUENTIAL_INTERFERING: 2,
        CurriculumCondition.DECAY_ON_DISUSE: 5,
        CurriculumCondition.REUSE_AFTER_NEWER: 3,
    }
    for cond, expected_len in expected_lengths.items():
        plan_a = build_curriculum_plan(cond)
        plan_b = build_curriculum_plan(cond)
        # Determinism: bit-identical tuple.
        assert plan_a == plan_b, (cond, plan_a, plan_b)
        # Bound: tuple length within v1 design.
        assert isinstance(plan_a, tuple)
        assert len(plan_a) == expected_len, (cond, len(plan_a))
        assert len(plan_a) <= CURRICULUM_MAX_EXPOSURES_PER_TRIAL
        # Every exposure is a bounded printable CurriculumExposure.
        for e in plan_a:
            assert isinstance(e, CurriculumExposure)
            assert e.input_text and e.input_text.isprintable()
            assert len(e.input_text) <= CURRICULUM_INPUT_MAX_LEN
            # Non-claim and direct-instruction clean.
            assert _has_forbidden_non_claim(e.input_text) is None, (
                cond, e.input_text
            )
            assert _has_forbidden_direct(e.input_text) is None, (
                cond, e.input_text
            )
