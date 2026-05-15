"""Fixture for I-EXP-05: ReadabilityPrediction is source-tagged and predictor-tagged."""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from fractions import Fraction

from brain.development.expression import (
    PREDICTOR_ID,
    ExpressionItem,
    ExpressionSource,
    ReadabilityPrediction,
    ReadabilityScore,
    predict_readability,
)
from brain.invariants import register


def _item(text: str = "alpha beta") -> ExpressionItem:
    return ExpressionItem(
        item_id="exp:pred-1",
        text=text,
        source=ExpressionSource.OPERATOR_TRANSCRIPT,
    )


def _assert_rejects(call) -> None:
    try:
        call()
    except (TypeError, ValueError) as exc:
        assert "I-EXP-05" in str(exc), (
            f"I-EXP-05 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-EXP-05 violated: invalid ReadabilityPrediction was accepted"
        )


@register("I-EXP-05", status="REQUIRED")
def check_readability_prediction_tagged() -> None:
    item = _item()
    prediction = predict_readability(item)

    assert prediction.item_id == item.item_id
    assert prediction.source is item.source
    assert prediction.predictor_id == PREDICTOR_ID
    assert prediction.predictor_id and prediction.predictor_id.isprintable()
    assert isinstance(prediction.score, ReadabilityScore)
    assert isinstance(prediction.score.value, Fraction)

    assert is_dataclass(ReadabilityPrediction)
    params = getattr(ReadabilityPrediction, "__dataclass_params__", None)
    assert params is not None and params.frozen

    field_names = {f.name for f in fields(prediction)}
    forbidden = {
        "callback",
        "client",
        "socket",
        "file",
        "path",
        "handle",
        "tick",
        "percept_event",
        "act",
        "agency",
        "trace",
    }
    assert not (field_names & forbidden), (
        f"I-EXP-05 violated: ReadabilityPrediction exposes {field_names & forbidden}"
    )

    _assert_rejects(
        lambda: ReadabilityPrediction(
            item_id="",
            source=ExpressionSource.OPERATOR_TRANSCRIPT,
            predictor_id=PREDICTOR_ID,
            score=ReadabilityScore(value=Fraction(1, 2)),
        )
    )
    _assert_rejects(
        lambda: ReadabilityPrediction(
            item_id="exp:bad",
            source="OPERATOR_TRANSCRIPT",  # type: ignore[arg-type]
            predictor_id=PREDICTOR_ID,
            score=ReadabilityScore(value=Fraction(1, 2)),
        )
    )
    _assert_rejects(
        lambda: ReadabilityPrediction(
            item_id="exp:bad",
            source=ExpressionSource.OPERATOR_TRANSCRIPT,
            predictor_id="",
            score=ReadabilityScore(value=Fraction(1, 2)),
        )
    )
    _assert_rejects(
        lambda: ReadabilityPrediction(
            item_id="exp:bad",
            source=ExpressionSource.OPERATOR_TRANSCRIPT,
            predictor_id=PREDICTOR_ID,
            score=Fraction(1, 2),  # type: ignore[arg-type]
        )
    )
