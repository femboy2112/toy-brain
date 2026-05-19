"""Phase 3.21 milestone M05_PATTERN_SELF_FEEDBACK fixture.

Drives I-DEVMILE-05 (REQUIRED). The fixture invokes
`run_m05_pattern_self_feedback` from the milestone harness with two distinct
`seed_offset` values and asserts that:

* the returned `MilestoneResult` has `status == MilestoneStatus.PASS`;
* the summary is bounded printable and non-claim-clean;
* the helper is deterministic (two invocations with identical
  `seed_offset` produce bit-identical results).

The fixture imports the helper and asserts the structural marker
defined in PHASE3_21_TEN_MILESTONES.md Section 5.
"""
from __future__ import annotations

from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.milestone_harness import (
    DevelopmentalMilestone,
    MilestoneStatus,
    MILESTONE_SUMMARY_MAX_LEN,
    run_m05_pattern_self_feedback,
)
from brain.invariants import register
from brain.tlica.profile import COGITO_ID


def _has_forbidden_term(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-DEVMILE-05", status="REQUIRED")
def check_developmental_milestone_m05() -> None:
    """Phase 3.21 milestone M05_PATTERN_SELF_FEEDBACK integration audit."""
    for seed_offset in (0, 7):
        result = run_m05_pattern_self_feedback(seed_offset=seed_offset)
        assert result.milestone == (
            DevelopmentalMilestone.M05_PATTERN_SELF_FEEDBACK
        ), (
            "I-DEVMILE-05 violated: milestone mismatch "
            f"(got {result.milestone!r})"
        )
        assert result.status == MilestoneStatus.PASS, (
            "I-DEVMILE-05 violated: status "
            f"{result.status.value!r} != pass (summary: {result.summary!r})"
        )
        assert isinstance(result.summary, str) and result.summary.isprintable(), (
            "I-DEVMILE-05 violated: summary not bounded printable"
        )
        assert len(result.summary) <= MILESTONE_SUMMARY_MAX_LEN, (
            "I-DEVMILE-05 violated: summary length "
            f"{len(result.summary)} exceeds MILESTONE_SUMMARY_MAX_LEN"
        )
        assert COGITO_ID not in result.summary, (
            "I-DEVMILE-05 violated: summary contains COGITO_ID"
        )
        term = _has_forbidden_term(result.summary)
        assert term is None, (
            "I-DEVMILE-05 violated: summary contains forbidden "
            f"non-claim term {term!r}"
        )
        result2 = run_m05_pattern_self_feedback(seed_offset=seed_offset)
        assert result == result2, (
            "I-DEVMILE-05 violated: helper not deterministic for "
            f"seed_offset={seed_offset}"
        )
