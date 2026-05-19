"""Phase 3.21 milestone harness static audit.

Drives I-DEVMILE-11 (STRUCTURAL). The audit confirms that:

* :class:`DevelopmentalMilestone` is a closed ``(str, Enum)`` with
  exactly the ten members M01..M10.
* :class:`MilestoneStatus` is a closed ``(str, Enum)`` with exactly
  the four members ``PASS / WARN / FAIL / NOT_APPLICABLE``.
* :class:`MilestoneResult` is a frozen / slotted dataclass with
  exactly the five fields ``milestone`` / ``status`` / ``summary``
  / ``primary_metric`` / ``secondary_metric``.
* Every entry in :data:`MODULE_PRODUCED_STRINGS` is bounded
  printable and contains no term from
  ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``.
* The module source contains no forbidden non-claim term.
* :func:`run_all_milestones` returns a tuple of exactly ten
  :class:`MilestoneResult` records in canonical order.
* Each per-milestone helper is deterministic across two
  invocations with the same ``seed_offset``.
"""
from __future__ import annotations

from pathlib import Path

from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.milestone_harness import (
    DevelopmentalMilestone,
    MILESTONE_SUMMARY_MAX_LEN,
    MODULE_PRODUCED_STRINGS,
    MilestoneResult,
    MilestoneStatus,
    run_all_milestones,
)
from brain.invariants import register


_HARNESS_SOURCE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "development"
    / "milestone_harness.py"
)


_EXPECTED_MILESTONE_VALUES: frozenset[str] = frozenset({
    "m01_reflexive_baseline",
    "m02_habituation",
    "m03_recognition",
    "m04_rehearsal",
    "m05_pattern_self_feedback",
    "m06_structural_self_monitoring",
    "m07_multi_modal_integration",
    "m08_saturation_novelty",
    "m09_cross_input_differentiation",
    "m10_sustained_behavior",
})


_EXPECTED_STATUS_VALUES: frozenset[str] = frozenset({
    "pass",
    "warn",
    "fail",
    "not_applicable",
})


_EXPECTED_RESULT_SLOTS: tuple[str, ...] = (
    "milestone",
    "status",
    "summary",
    "primary_metric",
    "secondary_metric",
)


def _has_forbidden_term(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-DEVMILE-11", status="STRUCTURAL")
def check_developmental_milestone_static_audit() -> None:
    """Static audit on milestone_harness.py."""

    # 1. DevelopmentalMilestone membership.
    assert issubclass(DevelopmentalMilestone, str), (
        "I-DEVMILE-11 violated: DevelopmentalMilestone is not a str enum"
    )
    actual_milestone_values = frozenset(
        m.value for m in DevelopmentalMilestone
    )
    assert actual_milestone_values == _EXPECTED_MILESTONE_VALUES, (
        "I-DEVMILE-11 violated: DevelopmentalMilestone value set drifted "
        f"(got {sorted(actual_milestone_values)!r}, expected "
        f"{sorted(_EXPECTED_MILESTONE_VALUES)!r})"
    )
    assert len(list(DevelopmentalMilestone)) == 10, (
        "I-DEVMILE-11 violated: DevelopmentalMilestone has "
        f"{len(list(DevelopmentalMilestone))} members, expected 10"
    )

    # 2. MilestoneStatus membership.
    assert issubclass(MilestoneStatus, str), (
        "I-DEVMILE-11 violated: MilestoneStatus is not a str enum"
    )
    actual_status_values = frozenset(s.value for s in MilestoneStatus)
    assert actual_status_values == _EXPECTED_STATUS_VALUES, (
        "I-DEVMILE-11 violated: MilestoneStatus value set drifted "
        f"(got {sorted(actual_status_values)!r}, expected "
        f"{sorted(_EXPECTED_STATUS_VALUES)!r})"
    )

    # 3. MilestoneResult slots.
    assert MilestoneResult.__slots__ == _EXPECTED_RESULT_SLOTS, (
        "I-DEVMILE-11 violated: MilestoneResult slots drifted "
        f"(got {MilestoneResult.__slots__!r}, expected "
        f"{_EXPECTED_RESULT_SLOTS!r})"
    )

    # 4. MilestoneResult constructor rejects bounded-shape violations.
    rejection_cases = (
        ("not-a-milestone", MilestoneStatus.PASS, "x", 0, 0,
         "non-milestone"),
        (DevelopmentalMilestone.M01_REFLEXIVE_BASELINE,
         "not-a-status", "x", 0, 0, "non-status"),
        (DevelopmentalMilestone.M01_REFLEXIVE_BASELINE,
         MilestoneStatus.PASS, "", 0, 0, "empty summary"),
        (DevelopmentalMilestone.M01_REFLEXIVE_BASELINE,
         MilestoneStatus.PASS, "x" * (MILESTONE_SUMMARY_MAX_LEN + 1),
         0, 0, "overlong summary"),
        (DevelopmentalMilestone.M01_REFLEXIVE_BASELINE,
         MilestoneStatus.PASS, "x", -1, 0, "negative primary"),
        (DevelopmentalMilestone.M01_REFLEXIVE_BASELINE,
         MilestoneStatus.PASS, "x", True, 0, "bool primary"),
        (DevelopmentalMilestone.M01_REFLEXIVE_BASELINE,
         MilestoneStatus.PASS, "x", 0, -1, "negative secondary"),
    )
    for (milestone, status, summary, primary, secondary, tag) in (
        rejection_cases
    ):
        raised = False
        try:
            MilestoneResult(
                milestone=milestone,  # type: ignore[arg-type]
                status=status,  # type: ignore[arg-type]
                summary=summary,
                primary_metric=primary,  # type: ignore[arg-type]
                secondary_metric=secondary,  # type: ignore[arg-type]
            )
        except ValueError:
            raised = True
        assert raised, (
            "I-DEVMILE-11 violated: MilestoneResult accepted invalid "
            f"input ({tag})"
        )

    # 5. MODULE_PRODUCED_STRINGS contains every enum value, all
    # bounded printable, all non-claim-clean.
    expected_in_module_strings = (
        _EXPECTED_MILESTONE_VALUES | _EXPECTED_STATUS_VALUES
    )
    actual_module_strings = frozenset(MODULE_PRODUCED_STRINGS)
    missing = expected_in_module_strings - actual_module_strings
    assert not missing, (
        "I-DEVMILE-11 violated: MODULE_PRODUCED_STRINGS missing entries "
        f"{sorted(missing)!r}"
    )
    for produced in MODULE_PRODUCED_STRINGS:
        assert isinstance(produced, str) and produced.isprintable(), (
            "I-DEVMILE-11 violated: MODULE_PRODUCED_STRINGS entry "
            f"{produced!r} not bounded printable"
        )
        term = _has_forbidden_term(produced)
        assert term is None, (
            "I-DEVMILE-11 violated: MODULE_PRODUCED_STRINGS entry "
            f"{produced!r} contains forbidden non-claim term {term!r}"
        )

    # 6. Module source contains no forbidden non-claim term.
    source = _HARNESS_SOURCE_PATH.read_text(encoding="utf-8")
    bad_term_in_source = _has_forbidden_term(source)
    assert bad_term_in_source is None, (
        "I-DEVMILE-11 violated: milestone_harness.py source contains "
        f"forbidden non-claim term {bad_term_in_source!r}"
    )

    # 7. run_all_milestones returns exactly 10 results in canonical
    # order.
    results = run_all_milestones()
    assert isinstance(results, tuple) and len(results) == 10, (
        "I-DEVMILE-11 violated: run_all_milestones did not return "
        f"a 10-tuple (got {type(results).__name__} len="
        f"{len(results) if isinstance(results, tuple) else 'n/a'})"
    )
    expected_order = tuple(DevelopmentalMilestone)
    for i, (r, expected) in enumerate(zip(results, expected_order)):
        assert isinstance(r, MilestoneResult), (
            "I-DEVMILE-11 violated: run_all_milestones[%d] is not a "
            "MilestoneResult" % i
        )
        assert r.milestone == expected, (
            "I-DEVMILE-11 violated: run_all_milestones[%d] milestone "
            "%r != expected %r" % (i, r.milestone, expected)
        )

    # 8. Determinism: re-run and compare bit-identity for the full
    # ordered tuple.
    results2 = run_all_milestones()
    assert results == results2, (
        "I-DEVMILE-11 violated: run_all_milestones not deterministic"
    )
