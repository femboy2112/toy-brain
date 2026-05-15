"""Fixture for I-EXP-06: ExpressionHistory is copy-on-write and bounded."""
from __future__ import annotations

from fractions import Fraction

from brain.development.expression import (
    EXPRESSION_HISTORY_MAX_ENTRIES,
    ExpressionHistory,
    ExpressionItem,
    ExpressionSource,
    make_expression_record,
    summarize_expression_history,
)
from brain.invariants import register


def _record(i: int) -> "ExpressionItem":
    item = ExpressionItem(
        item_id=f"exp:hist-{i}",
        text=f"alpha beta gamma {i}",
        source=ExpressionSource.OUTPUT_HISTORY,
    )
    return make_expression_record(item)


@register("I-EXP-06", status="REQUIRED")
def check_expression_history_is_cow_and_bounded() -> None:
    empty = ExpressionHistory()
    assert empty.records == ()

    r0 = _record(0)
    h1 = empty.append(r0)
    assert empty is not h1
    assert empty.records == ()
    assert h1.records == (r0,)

    r1 = _record(1)
    h2 = h1.append(r1)
    assert h2 is not h1
    assert h1.records == (r0,)
    assert h2.records == (r0, r1)

    # Append must reject non-ExpressionRecord values.
    try:
        h2.append("not a record")  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "I-EXP-06 violated: ExpressionHistory.append accepted non-record"
        )

    # Bounded ring: appending beyond EXPRESSION_HISTORY_MAX_ENTRIES drops
    # the oldest entry.
    current = ExpressionHistory()
    target = EXPRESSION_HISTORY_MAX_ENTRIES + 8
    for i in range(target):
        current = current.append(_record(i))
    assert len(current.records) == EXPRESSION_HISTORY_MAX_ENTRIES
    # The earliest records were dropped: the first surviving record has
    # item_id equal to the offset of the first non-dropped append.
    expected_first_index = target - EXPRESSION_HISTORY_MAX_ENTRIES
    assert current.records[0].item.item_id == f"exp:hist-{expected_first_index}"
    assert current.records[-1].item.item_id == f"exp:hist-{target - 1}"

    # ExpressionHistory must reject construction with > MAX records.
    too_many = tuple(_record(i) for i in range(EXPRESSION_HISTORY_MAX_ENTRIES + 1))
    try:
        ExpressionHistory(records=too_many)
    except ValueError as exc:
        assert "I-EXP-06" in str(exc), (
            f"I-EXP-06 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-EXP-06 violated: ExpressionHistory accepted over-long records tuple"
        )

    # Summary view (I-EXP-17 OBSERVED runtime helper) is non-mutating.
    summary_records_before = current.records
    summary = summarize_expression_history(current)
    assert current.records is summary_records_before
    assert summary.count == EXPRESSION_HISTORY_MAX_ENTRIES
    assert summary.score_min <= summary.score_max
    assert isinstance(summary.score_mean, Fraction)
    assert summary.counts_by_source[ExpressionSource.OUTPUT_HISTORY] == (
        EXPRESSION_HISTORY_MAX_ENTRIES
    )
