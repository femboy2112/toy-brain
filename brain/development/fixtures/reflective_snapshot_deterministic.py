"""Fixture for I-REF-05: ReflectiveInspectionSnapshot construction is deterministic."""
from __future__ import annotations

from fractions import Fraction

from brain.development.expression import (
    ExpressionHistory,
    ExpressionItem,
    ExpressionSource,
    make_expression_record,
)
from brain.development.output import (
    OutputHistory,
    OutputImpulse,
    OutputProvenance,
    append_output_impulse,
)
from brain.development.reflective import (
    ReflectiveInspectionSnapshot,
    ReflectiveSource,
    ReflectiveSummaryItem,
    make_reflective_snapshot,
    make_reflective_summary,
)
from brain.development.stream import FrameSourceKind
from brain.invariants import register


def _output_history() -> OutputHistory:
    provenance = OutputProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(3, 5),
        trace_event_ids=("trace:out-1",),
    )
    impulse = OutputImpulse(
        impulse_id="out:imp-1",
        text="hello",
        provenance=provenance,
    )
    return append_output_impulse(OutputHistory(), impulse)


def _expression_history() -> ExpressionHistory:
    item = ExpressionItem(
        item_id="exp:r-1",
        text="alpha beta gamma delta",
        source=ExpressionSource.WORLDLET_HISTORY,
    )
    return ExpressionHistory().append(make_expression_record(item))


@register("I-REF-05", status="REQUIRED")
def check_reflective_snapshot_construction_is_deterministic() -> None:
    out1 = _output_history()
    out2 = _output_history()
    expr1 = _expression_history()
    expr2 = _expression_history()

    snap_a = make_reflective_snapshot(
        snapshot_id="snap:det",
        output_history=out1,
        expression_history=expr1,
    )
    snap_b = make_reflective_snapshot(
        snapshot_id="snap:det",
        output_history=out2,
        expression_history=expr2,
    )
    assert isinstance(snap_a, ReflectiveInspectionSnapshot)
    assert snap_a == snap_b, (
        f"I-REF-05 violated: snapshot drift\n  a={snap_a}\n  b={snap_b}"
    )

    # Items follow the canonical bridge order.
    sources = tuple(item.source for item in snap_a.items)
    assert sources == (
        ReflectiveSource.OUTPUT_HISTORY,
        ReflectiveSource.EXPRESSION_HISTORY,
    ), f"I-REF-05 violated: unexpected source order {sources}"

    for item in snap_a.items:
        assert isinstance(item, ReflectiveSummaryItem)

    # Empty snapshot is also deterministic.
    empty_a = make_reflective_snapshot(snapshot_id="snap:empty")
    empty_b = make_reflective_snapshot(snapshot_id="snap:empty")
    assert empty_a == empty_b
    assert empty_a.items == ()

    # Summary aggregation is deterministic.
    sum_a = make_reflective_summary(snap_a)
    sum_b = make_reflective_summary(snap_b)
    assert sum_a == sum_b
    assert sum_a.item_count == 2
    assert sum_a.total_entry_count == 1 + 1
