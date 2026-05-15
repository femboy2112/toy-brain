"""Fixtures for I-EXP-03 and I-EXP-14.

I-EXP-03: `ExpressionFeatureVector` is deterministic and exact.
I-EXP-14: Expression records are frozen dataclasses with bounded fields.
"""
from __future__ import annotations

from dataclasses import is_dataclass, fields
from fractions import Fraction

from brain.development.expression import (
    ExpressionFeatureVector,
    ExpressionHistory,
    ExpressionHistorySummary,
    ExpressionItem,
    ExpressionRecord,
    ExpressionSource,
    ReadabilityPrediction,
    ReadabilityScore,
    extract_features,
    make_expression_record,
)
from brain.invariants import register


def _item(text: str = "alpha beta gamma") -> ExpressionItem:
    return ExpressionItem(
        item_id="exp:feat-1",
        text=text,
        source=ExpressionSource.OUTPUT_HISTORY,
    )


@register("I-EXP-03", status="REQUIRED")
def check_feature_vector_is_deterministic_and_exact() -> None:
    item = _item("alpha beta alpha gamma")
    fv1 = extract_features(item)
    fv2 = extract_features(item)
    assert fv1 == fv2, "I-EXP-03 violated: feature extraction is non-deterministic"
    assert isinstance(fv1.char_count, int)
    assert isinstance(fv1.token_count, int)
    assert isinstance(fv1.printable_non_space_count, int)
    assert isinstance(fv1.distinct_token_count, int)
    assert isinstance(fv1.max_run_length, int)
    assert isinstance(fv1.whitespace_only, bool)
    assert fv1.char_count == len("alpha beta alpha gamma")
    assert fv1.token_count == 4
    assert fv1.distinct_token_count == 3
    assert fv1.max_run_length == 1
    assert fv1.whitespace_only is False

    fv_empty = extract_features(_item(""))
    assert fv_empty.whitespace_only is True
    assert fv_empty.token_count == 0

    fv_ws = extract_features(_item("   "))
    assert fv_ws.whitespace_only is True
    assert fv_ws.token_count == 0

    fv_repeat = extract_features(_item("foo foo foo foo"))
    assert fv_repeat.token_count == 4
    assert fv_repeat.distinct_token_count == 1
    assert fv_repeat.max_run_length == 4


_FROZEN_RECORDS = (
    ExpressionItem,
    ExpressionFeatureVector,
    ExpressionRecord,
    ReadabilityScore,
    ReadabilityPrediction,
    ExpressionHistory,
    ExpressionHistorySummary,
)


@register("I-EXP-14", status="STRUCTURAL")
def check_expression_records_are_frozen_dataclasses() -> None:
    for cls in _FROZEN_RECORDS:
        assert is_dataclass(cls), (
            f"I-EXP-14 violated: {cls.__name__} is not a dataclass"
        )
        params = getattr(cls, "__dataclass_params__", None)
        assert params is not None and params.frozen, (
            f"I-EXP-14 violated: {cls.__name__} is not frozen"
        )

    record = make_expression_record(_item("alpha beta"))
    try:
        record.item = _item("mutated")  # type: ignore[misc]
    except Exception:
        pass
    else:
        raise AssertionError(
            "I-EXP-14 violated: ExpressionRecord allowed attribute mutation"
        )

    # Records must not carry callable, file, socket, or path fields.
    forbidden_types_substrings = ("callable", "file", "socket", "path", "client")
    for cls in _FROZEN_RECORDS:
        for fld in fields(cls):
            type_repr = repr(fld.type).lower() if fld.type is not None else ""
            for bad in forbidden_types_substrings:
                assert bad not in type_repr, (
                    f"I-EXP-14 violated: {cls.__name__}.{fld.name} type "
                    f"{fld.type!r} mentions forbidden substring {bad!r}"
                )

    record_again = make_expression_record(_item("alpha beta"))
    assert record == record_again, (
        "I-EXP-14 violated: equal inputs produced unequal frozen records"
    )
    assert isinstance(record.prediction.score.value, Fraction)
