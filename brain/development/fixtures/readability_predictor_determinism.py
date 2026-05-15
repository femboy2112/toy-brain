"""Fixture for I-EXP-12: predictor determinism."""
from __future__ import annotations

from brain.development.expression import (
    ExpressionItem,
    ExpressionSource,
    predict_readability,
)
from brain.invariants import register


_PROBE_TEXTS = (
    "alpha",
    "alpha beta",
    "alpha beta gamma delta",
    "abc def ghi jkl",
    "PRINT X PRINT Y",
    "   ",
    "a b c d e f g h i j",
)


@register("I-EXP-12", status="REQUIRED")
def check_readability_predictor_is_deterministic() -> None:
    for text in _PROBE_TEXTS:
        item = ExpressionItem(
            item_id=f"exp:det:{text or 'empty'}".replace(" ", "_")[:64],
            text=text,
            source=ExpressionSource.OPERATOR_TRANSCRIPT,
        )
        first = predict_readability(item)
        for _ in range(4):
            again = predict_readability(item)
            assert again.score.value == first.score.value, (
                f"I-EXP-12 violated: non-deterministic score for {text!r}: "
                f"{first.score.value} vs {again.score.value}"
            )
            assert again.predictor_id == first.predictor_id
            assert again.source is first.source
            assert again.item_id == first.item_id
