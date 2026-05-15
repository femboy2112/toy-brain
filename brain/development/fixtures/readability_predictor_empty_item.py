"""Fixture for I-EXP-09: empty / whitespace-only items score Fraction(0)."""
from __future__ import annotations

from fractions import Fraction

from brain.development.expression import (
    ExpressionItem,
    ExpressionSource,
    predict_readability,
)
from brain.invariants import register


def _item(text: str) -> ExpressionItem:
    return ExpressionItem(
        item_id="exp:empty-1",
        text=text,
        source=ExpressionSource.OUTPUT_HISTORY,
    )


@register("I-EXP-09", status="REQUIRED")
def check_readability_predictor_empty_item_is_zero() -> None:
    for text in ("", " ", "  ", "   ", "                "):
        prediction = predict_readability(_item(text))
        assert prediction.score.value == Fraction(0), (
            f"I-EXP-09 violated: whitespace-only text {text!r} scored "
            f"{prediction.score.value}"
        )

    # Sanity: a non-empty item must produce a strictly positive score.
    non_empty = ExpressionItem(
        item_id="exp:non-empty",
        text="alpha",
        source=ExpressionSource.OUTPUT_HISTORY,
    )
    assert predict_readability(non_empty).score.value > Fraction(0)
