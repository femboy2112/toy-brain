"""Fixture for I-REF-08: reflective layer surfaces source-supplied scores only."""
from __future__ import annotations

from dataclasses import fields
from fractions import Fraction

from brain.development.expression import (
    ExpressionHistory,
    ExpressionItem,
    ExpressionSource,
    make_expression_record,
)
from brain.development.reflective import (
    ReflectiveInspectionSnapshot,
    ReflectiveInspectionSummary,
    ReflectiveSource,
    ReflectiveSummaryItem,
    make_reflective_snapshot,
    make_reflective_summary,
)
from brain.invariants import register


_FORBIDDEN_FIELD_NAMES: frozenset[str] = frozenset({
    "score",
    "scores",
    "quality",
    "intelligence",
    "social_success",
    "aggregate_score",
    "aggregate_quality",
    "aggregate_intelligence",
    "aggregate_social_success",
    "truth",
    "validity",
    "accuracy",
})

_ALLOWED_TAGGED_FIELDS: frozenset[str] = frozenset({
    "source_supplied_scores",
    "source_supplied_score_count",
})


def _expression_history() -> ExpressionHistory:
    item = ExpressionItem(
        item_id="exp:agg-1",
        text="alpha beta gamma",
        source=ExpressionSource.OUTPUT_HISTORY,
    )
    return ExpressionHistory().append(make_expression_record(item))


def _all_field_names(record_type: type) -> set[str]:
    return {f.name for f in fields(record_type)}


@register("I-REF-08", status="REQUIRED")
def check_reflective_surfaces_source_supplied_scores_only() -> None:
    for record_type in (
        ReflectiveSummaryItem,
        ReflectiveInspectionSnapshot,
        ReflectiveInspectionSummary,
    ):
        names = _all_field_names(record_type)
        for name in names:
            if name in _ALLOWED_TAGGED_FIELDS:
                continue
            for forbidden in _FORBIDDEN_FIELD_NAMES:
                assert forbidden not in name, (
                    "I-REF-08 violated: untagged aggregate-score-like field "
                    f"{name!r} on {record_type.__name__}; only "
                    f"source_supplied_* names are tagged passthroughs"
                )

    expr_hist = _expression_history()
    snap = make_reflective_snapshot(
        snapshot_id="snap:agg",
        expression_history=expr_hist,
    )
    summary = make_reflective_summary(snap)

    expr_item = next(
        i for i in snap.items if i.source is ReflectiveSource.EXPRESSION_HISTORY
    )
    expected_score = expr_hist.records[0].prediction.score.value
    assert expr_item.source_supplied_scores == (expected_score,), (
        "I-REF-08 violated: source_supplied_scores must passthrough "
        f"existing ReadabilityScore (got {expr_item.source_supplied_scores})"
    )
    for s in expr_item.source_supplied_scores:
        assert isinstance(s, Fraction)

    assert summary.source_supplied_score_count == 1
    assert not hasattr(summary, "aggregate_score")
    assert not hasattr(summary, "quality")
    assert not hasattr(summary, "intelligence")
    assert not hasattr(summary, "social_success")
