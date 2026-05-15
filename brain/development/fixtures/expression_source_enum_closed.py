"""Fixture for I-EXP-01: ExpressionSource is a finite closed enumeration."""
from __future__ import annotations

from brain.development.expression import ExpressionItem, ExpressionSource
from brain.invariants import register


_EXPECTED_MEMBERS = {
    "OUTPUT_HISTORY",
    "WORLDLET_HISTORY",
    "PROTO_BASIC_HISTORY",
    "OPERATOR_TRANSCRIPT",
}


@register("I-EXP-01", status="REQUIRED")
def check_expression_source_is_finite_closed() -> None:
    members = {m.name for m in ExpressionSource}
    assert members == _EXPECTED_MEMBERS, (
        f"I-EXP-01 violated: ExpressionSource members {members} != expected "
        f"{_EXPECTED_MEMBERS}"
    )
    for member in ExpressionSource:
        assert isinstance(member.value, str)
        assert member.value and member.value.isprintable()

    try:
        ExpressionItem(
            item_id="exp:bad-source",
            text="hello",
            source="OUTPUT_HISTORY",  # type: ignore[arg-type]
        )
    except (TypeError, ValueError) as exc:
        assert "I-EXP-01" in str(exc), (
            f"I-EXP-01 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-EXP-01 violated: non-ExpressionSource source was accepted"
        )
