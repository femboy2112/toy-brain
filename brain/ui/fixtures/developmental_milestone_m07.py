"""Phase 3.21 milestone M07_MULTI_MODAL_INTEGRATION fixture.

Drives I-DEVMILE-07 (REQUIRED). The fixture invokes
`run_m07_multi_modal_integration` from the milestone harness with two distinct
`seed_offset` values and asserts that:

* the returned `MilestoneResult` has `status == MilestoneStatus.PASS`;
* the summary is bounded printable and non-claim-clean;
* the helper is deterministic (two invocations with identical
  `seed_offset` produce bit-identical results).

The fixture imports the helper and asserts the structural marker
defined in PHASE3_21_TEN_MILESTONES.md Section 7.
"""
from __future__ import annotations

from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.milestone_harness import (
    DevelopmentalMilestone,
    MilestoneStatus,
    MILESTONE_SUMMARY_MAX_LEN,
    run_m07_multi_modal_integration,
)
from brain.invariants import register
from brain.tlica.profile import COGITO_ID


def _has_forbidden_term(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-DEVMILE-07", status="REQUIRED")
def check_developmental_milestone_m07() -> None:
    """Phase 3.21 milestone M07_MULTI_MODAL_INTEGRATION integration audit."""
    for seed_offset in (0, 7):
        result = run_m07_multi_modal_integration(seed_offset=seed_offset)
        assert result.milestone == (
            DevelopmentalMilestone.M07_MULTI_MODAL_INTEGRATION
        ), (
            "I-DEVMILE-07 violated: milestone mismatch "
            f"(got {result.milestone!r})"
        )
        assert result.status == MilestoneStatus.PASS, (
            "I-DEVMILE-07 violated: status "
            f"{result.status.value!r} != pass (summary: {result.summary!r})"
        )
        assert isinstance(result.summary, str) and result.summary.isprintable(), (
            "I-DEVMILE-07 violated: summary not bounded printable"
        )
        assert len(result.summary) <= MILESTONE_SUMMARY_MAX_LEN, (
            "I-DEVMILE-07 violated: summary length "
            f"{len(result.summary)} exceeds MILESTONE_SUMMARY_MAX_LEN"
        )
        assert COGITO_ID not in result.summary, (
            "I-DEVMILE-07 violated: summary contains COGITO_ID"
        )
        term = _has_forbidden_term(result.summary)
        assert term is None, (
            "I-DEVMILE-07 violated: summary contains forbidden "
            f"non-claim term {term!r}"
        )
        result2 = run_m07_multi_modal_integration(seed_offset=seed_offset)
        assert result == result2, (
            "I-DEVMILE-07 violated: helper not deterministic for "
            f"seed_offset={seed_offset}"
        )
