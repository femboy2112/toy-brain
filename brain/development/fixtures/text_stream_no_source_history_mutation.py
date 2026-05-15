"""Fixture for I-STRM-09: text-stream ops do not mutate any existing source history."""
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
from brain.development.stream import FrameSourceKind
from brain.development.text_stream import (
    TextStreamHistory,
    TextStreamSource,
    extract_segment_candidates,
    extract_stream_features,
    make_stream_pattern,
    make_stream_promotion_candidate,
    make_text_stream_chunk,
)
from brain.invariants import register


def _output_history() -> OutputHistory:
    provenance = OutputProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(1, 3),
        trace_event_ids=("trace:strm-1",),
    )
    impulse = OutputImpulse(
        impulse_id="out:strm-1",
        text="hello",
        provenance=provenance,
    )
    return append_output_impulse(OutputHistory(), impulse)


def _expression_history() -> ExpressionHistory:
    item = ExpressionItem(
        item_id="exp:strm-1",
        text="alpha beta",
        source=ExpressionSource.OPERATOR_TRANSCRIPT,
    )
    return ExpressionHistory().append(make_expression_record(item))


@register("I-STRM-09", status="REQUIRED")
def check_text_stream_does_not_mutate_source_history() -> None:
    out = _output_history()
    expr = _expression_history()

    before_out_id = id(out)
    before_out_len = len(out.impulses)
    before_out_tuple = out.impulses
    before_expr_id = id(expr)
    before_expr_len = len(expr.records)
    before_expr_tuple = expr.records

    chunk = make_text_stream_chunk(
        chunk_id="chunk:src",
        text="hello\nworld",
        source=TextStreamSource.OPERATOR,
        provenance="origin:operator",
    )
    history = TextStreamHistory().append(chunk)
    extract_stream_features(chunk)
    extract_segment_candidates(chunk)
    pattern = make_stream_pattern(
        pattern_id="pat:src",
        signature=("hello",),
        recurrence_count=2,
    )
    make_stream_promotion_candidate(
        candidate_id="pc:src",
        target_content_id="content:src",
        source=TextStreamSource.OPERATOR,
        chunk_id=chunk.chunk_id,
        text="hello",
        provenance="origin:operator",
        pattern_id=pattern.pattern_id,
    )

    assert len(history.chunks) == 1
    assert id(out) == before_out_id
    assert len(out.impulses) == before_out_len
    assert out.impulses == before_out_tuple
    assert id(expr) == before_expr_id
    assert len(expr.records) == before_expr_len
    assert expr.records == before_expr_tuple
