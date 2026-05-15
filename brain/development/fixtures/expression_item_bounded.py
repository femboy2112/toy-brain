"""Fixture for I-EXP-02: ExpressionItem.text is bounded printable."""
from __future__ import annotations

from brain.development.expression import (
    EXPRESSION_TEXT_MAX_LEN,
    ExpressionItem,
    ExpressionSource,
)
from brain.invariants import register


def _assert_rejects(call, tag: str = "I-EXP-02") -> None:
    try:
        call()
    except (TypeError, ValueError) as exc:
        assert tag in str(exc), (
            f"{tag} negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            f"{tag} violated: invalid ExpressionItem was accepted"
        )


@register("I-EXP-02", status="REQUIRED")
def check_expression_item_is_bounded_printable() -> None:
    item = ExpressionItem(
        item_id="exp:item-1",
        text="hello world",
        source=ExpressionSource.OUTPUT_HISTORY,
    )
    assert item.item_id == "exp:item-1"
    assert item.text == "hello world"

    empty_text_ok = ExpressionItem(
        item_id="exp:empty",
        text="",
        source=ExpressionSource.OUTPUT_HISTORY,
    )
    assert empty_text_ok.text == ""

    _assert_rejects(
        lambda: ExpressionItem(
            item_id="",
            text="hello",
            source=ExpressionSource.OUTPUT_HISTORY,
        )
    )
    _assert_rejects(
        lambda: ExpressionItem(
            item_id="exp:nonprintable",
            text="bad\ntext",
            source=ExpressionSource.OUTPUT_HISTORY,
        )
    )
    _assert_rejects(
        lambda: ExpressionItem(
            item_id="exp:overlong",
            text="a" * (EXPRESSION_TEXT_MAX_LEN + 1),
            source=ExpressionSource.OUTPUT_HISTORY,
        )
    )
