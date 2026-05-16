"""Fixture for I-STRM-11: anti-growth on repeated / huge text-stream input.

Verifies two contracts:

1. ``TextStreamChunk.text`` over ``STREAM_TEXT_MAX_LEN`` raises with row
   tag ``I-STRM-11`` — no silent truncation.
2. ``TextStreamHistory`` never grows above ``STREAM_HISTORY_MAX_CHUNKS``
   under arbitrary repeated append (cap is enforced by drop-oldest, not by
   silent extend).
3. ``StreamPattern.recurrence_count`` saturates at
   ``STREAM_PATTERN_RECURRENCE_MAX`` under arbitrary repetition; values
   above the cap raise via construction; ``make_stream_pattern`` saturates
   over-bound inputs.
"""
from __future__ import annotations

from brain.development.text_stream import (
    STREAM_HISTORY_MAX_CHUNKS,
    STREAM_PATTERN_RECURRENCE_MAX,
    STREAM_PATTERN_RECURRENCE_MIN,
    STREAM_TEXT_MAX_LEN,
    StreamPattern,
    TextStreamHistory,
    TextStreamSource,
    make_stream_pattern,
    make_text_stream_chunk,
)
from brain.invariants import register


@register("I-STRM-11", status="REQUIRED")
def check_text_stream_anti_growth() -> None:
    # 1. Over-length text raises with I-STRM-11 (no silent truncation).
    try:
        make_text_stream_chunk(
            chunk_id="chunk:overlength",
            text="x" * (STREAM_TEXT_MAX_LEN + 1),
            source=TextStreamSource.OPERATOR,
            provenance="origin:t",
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-11" in str(exc), (
            f"I-STRM-11 violated: over-length text raised without row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-11 violated: text over STREAM_TEXT_MAX_LEN was silently accepted"
        )

    # Boundary: exactly STREAM_TEXT_MAX_LEN is allowed.
    boundary = make_text_stream_chunk(
        chunk_id="chunk:boundary",
        text="x" * STREAM_TEXT_MAX_LEN,
        source=TextStreamSource.OPERATOR,
        provenance="origin:t",
    )
    assert len(boundary.text) == STREAM_TEXT_MAX_LEN

    # 2. History never grows above MAX under arbitrary append.
    h = TextStreamHistory()
    for i in range(STREAM_HISTORY_MAX_CHUNKS * 2):
        chunk = make_text_stream_chunk(
            chunk_id=f"chunk:grow-{i}",
            text=f"text-{i}",
            source=TextStreamSource.OPERATOR,
            provenance="origin:t",
        )
        h = h.append(chunk)
        assert len(h.chunks) <= STREAM_HISTORY_MAX_CHUNKS
    assert len(h.chunks) == STREAM_HISTORY_MAX_CHUNKS

    # 3. StreamPattern recurrence_count saturates at MAX under make_stream_pattern.
    saturated = make_stream_pattern(
        pattern_id="pat:saturated",
        signature=("alpha",),
        recurrence_count=STREAM_PATTERN_RECURRENCE_MAX + 1000,
    )
    assert saturated.recurrence_count == STREAM_PATTERN_RECURRENCE_MAX

    # And direct construction above MAX raises.
    try:
        StreamPattern(
            pattern_id="pat:overmax",
            signature=("alpha",),
            recurrence_count=STREAM_PATTERN_RECURRENCE_MAX + 1,
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-06" in str(exc), (
            f"I-STRM-11 violated: direct over-max construction did not name "
            f"I-STRM-06: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-11 violated: direct StreamPattern construction accepted "
            "recurrence_count above STREAM_PATTERN_RECURRENCE_MAX"
        )

    # And recurrence_count below MIN raises.
    try:
        StreamPattern(
            pattern_id="pat:undermin",
            signature=("alpha",),
            recurrence_count=STREAM_PATTERN_RECURRENCE_MIN - 1,
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-06" in str(exc), (
            f"I-STRM-11 violated: under-min construction did not name "
            f"I-STRM-06: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-11 violated: StreamPattern accepted recurrence_count below "
            "STREAM_PATTERN_RECURRENCE_MIN"
        )
