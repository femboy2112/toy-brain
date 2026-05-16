"""Fixture for I-REF-01: ReflectiveSource is a finite closed enumeration."""
from __future__ import annotations

from brain.development.reflective import ReflectiveSource, ReflectiveSummaryItem
from brain.invariants import register


_EXPECTED_MEMBERS = {
    "OUTPUT_HISTORY",
    "WORLDLET_HISTORY",
    "PROTO_BASIC_HISTORY",
    "EXPRESSION_HISTORY",
    "OPERATOR_TRANSCRIPT",
}


@register("I-REF-01", status="REQUIRED")
def check_reflective_source_is_finite_closed() -> None:
    members = {m.name for m in ReflectiveSource}
    assert members == _EXPECTED_MEMBERS, (
        f"I-REF-01 violated: ReflectiveSource members {members} != "
        f"expected {_EXPECTED_MEMBERS}"
    )
    for member in ReflectiveSource:
        assert isinstance(member.value, str)
        assert member.value and member.value.isprintable()

    try:
        ReflectiveSummaryItem(
            source="OUTPUT_HISTORY",  # type: ignore[arg-type]
            summary_id="reflective:bad-source",
            entry_count=0,
            distinct_id_count=0,
            counts_by_category={},
            source_supplied_scores=(),
            notes=(),
        )
    except (TypeError, ValueError) as exc:
        assert "I-REF-02" in str(exc) or "I-REF-01" in str(exc), (
            "I-REF-01 negative-case message lacks I-REF-01/I-REF-02 row tag: "
            f"{exc!r}"
        )
    else:
        raise AssertionError(
            "I-REF-01 violated: non-ReflectiveSource source was accepted"
        )
