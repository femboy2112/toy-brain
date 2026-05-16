"""Fixture for I-STRM-03: TextStreamHistory is copy-on-write and bounded."""
from __future__ import annotations

from brain.development.text_stream import (
    STREAM_HISTORY_MAX_CHUNKS,
    TextStreamHistory,
    TextStreamSource,
    make_text_stream_chunk,
)
from brain.invariants import register


def _chunk(i: int) -> object:
    return make_text_stream_chunk(
        chunk_id=f"chunk:{i}",
        text=f"text-{i}",
        source=TextStreamSource.OPERATOR,
        provenance="origin:t",
    )


@register("I-STRM-03", status="REQUIRED")
def check_text_stream_history_is_cow_bounded() -> None:
    h0 = TextStreamHistory()
    assert h0.chunks == ()

    c1 = _chunk(1)
    h1 = h0.append(c1)
    assert h0 is not h1
    assert h0.chunks == ()
    assert h1.chunks == (c1,)

    c2 = _chunk(2)
    h2 = h1.append(c2)
    assert h1 is not h2
    assert h1.chunks == (c1,)
    assert h2.chunks == (c1, c2)

    # Fill exactly to STREAM_HISTORY_MAX_CHUNKS.
    h = TextStreamHistory()
    for i in range(STREAM_HISTORY_MAX_CHUNKS):
        h = h.append(_chunk(i))
    assert len(h.chunks) == STREAM_HISTORY_MAX_CHUNKS
    first_chunk_id = h.chunks[0].chunk_id

    # One more append: oldest dropped, length unchanged.
    h_next = h.append(_chunk(STREAM_HISTORY_MAX_CHUNKS))
    assert len(h_next.chunks) == STREAM_HISTORY_MAX_CHUNKS
    assert h_next.chunks[0].chunk_id != first_chunk_id
    assert h_next.chunks[-1].chunk_id == f"chunk:{STREAM_HISTORY_MAX_CHUNKS}"

    # Original h must be unchanged (copy-on-write).
    assert len(h.chunks) == STREAM_HISTORY_MAX_CHUNKS
    assert h.chunks[0].chunk_id == first_chunk_id

    # Construction-time enforcement: tuple longer than max is rejected.
    try:
        TextStreamHistory(chunks=tuple(_chunk(i) for i in range(STREAM_HISTORY_MAX_CHUNKS + 1)))
    except (TypeError, ValueError) as exc:
        assert "I-STRM-03" in str(exc), (
            f"I-STRM-03 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-03 violated: over-bound TextStreamHistory accepted at construction"
        )
