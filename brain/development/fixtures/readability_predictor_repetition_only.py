"""Fixture for I-EXP-10: repetition alone never increases the score."""
from __future__ import annotations

from brain.development.expression import (
    ExpressionItem,
    ExpressionSource,
    predict_readability,
)
from brain.invariants import register


def _repeat_item(token: str, count: int) -> ExpressionItem:
    text = " ".join([token] * count)
    return ExpressionItem(
        item_id=f"exp:rep-{count}",
        text=text,
        source=ExpressionSource.PROTO_BASIC_HISTORY,
    )


@register("I-EXP-10", status="REQUIRED")
def check_repetition_alone_never_increases_score() -> None:
    base_score = predict_readability(_repeat_item("alpha", 1)).score.value

    for count in (2, 4, 8, 16, 32, 64):
        score = predict_readability(_repeat_item("alpha", count)).score.value
        assert score <= base_score, (
            f"I-EXP-10 violated: repeat-only count={count} score {score} "
            f"exceeded single-instance baseline {base_score}"
        )

    # Adding distinct tokens must do strictly better than pure repetition.
    diverse = ExpressionItem(
        item_id="exp:diverse",
        text="alpha beta gamma delta epsilon zeta",
        source=ExpressionSource.PROTO_BASIC_HISTORY,
    )
    rep = _repeat_item("alpha", 6)
    diverse_score = predict_readability(diverse).score.value
    rep_score = predict_readability(rep).score.value
    assert diverse_score > rep_score, (
        "I-EXP-10 violated: pure-repetition score is not below diverse-token score"
    )
