"""Fixture for I-STRM-02: TextStreamChunk is bounded printable + COGITO_ID rejected.

Also contributes a sanity check on TextStreamChunk's frozen-record contract;
the I-STRM-13 row itself is registered in text_stream_feature_vector_exact.py
(which covers all six text-stream records together).
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass

from brain.development.text_stream import (
    STREAM_PROVENANCE_MAX_LEN,
    STREAM_TEXT_MAX_LEN,
    TextStreamChunk,
    TextStreamSource,
    _COGITO_RESERVED_ID,
    make_text_stream_chunk,
)
from brain.invariants import register
from brain.tlica.profile import COGITO_ID

# Hard sanity check: text_stream.py's locally-duplicated cogito sentinel
# must match brain.tlica.profile.COGITO_ID. text_stream.py itself cannot
# import brain.tlica per I-STRM-12, so the fixture verifies parity here at
# import time. Divergence fails immediately rather than silently.
assert _COGITO_RESERVED_ID == COGITO_ID, (
    "I-STRM-02 violated: text_stream._COGITO_RESERVED_ID "
    f"({_COGITO_RESERVED_ID!r}) does not match brain.tlica.profile.COGITO_ID "
    f"({COGITO_ID!r})"
)


def _assert_rejects(call, tag: str) -> None:
    try:
        call()
    except (TypeError, ValueError) as exc:
        assert tag in str(exc), (
            f"{tag} negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            f"{tag} violated: invalid TextStreamChunk was accepted"
        )


@register("I-STRM-02", status="REQUIRED")
def check_text_stream_chunk_is_bounded() -> None:
    chunk = make_text_stream_chunk(
        chunk_id="chunk:1",
        text="hello world",
        source=TextStreamSource.OPERATOR,
        provenance="origin:operator",
    )
    assert chunk.chunk_id == "chunk:1"
    assert chunk.text == "hello world"
    assert chunk.source is TextStreamSource.OPERATOR
    assert chunk.provenance == "origin:operator"

    # Sanity: chunk is frozen (formal I-STRM-13 registration lives in
    # text_stream_feature_vector_exact.py and covers all six records).
    assert is_dataclass(chunk)
    assert getattr(type(chunk), "__dataclass_params__").frozen
    try:
        chunk.text = "mutated"  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "I-STRM-02 violated: TextStreamChunk allowed attribute mutation"
        )

    # empty / non-printable / over-length text
    _assert_rejects(
        lambda: make_text_stream_chunk(
            chunk_id="chunk:bad-empty",
            text="",
            source=TextStreamSource.OPERATOR,
            provenance="origin:t",
        ),
        tag="I-STRM-02",
    )
    _assert_rejects(
        lambda: make_text_stream_chunk(
            chunk_id="chunk:bad-nonprintable",
            text="hello\x00world",
            source=TextStreamSource.OPERATOR,
            provenance="origin:t",
        ),
        tag="I-STRM-02",
    )
    # over-length text raises under I-STRM-11 (no silent truncation)
    try:
        make_text_stream_chunk(
            chunk_id="chunk:bad-over",
            text="x" * (STREAM_TEXT_MAX_LEN + 1),
            source=TextStreamSource.OPERATOR,
            provenance="origin:t",
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-11" in str(exc) or "I-STRM-02" in str(exc), (
            f"over-length text did not name I-STRM-11/I-STRM-02: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-02 violated: over-length text was accepted"
        )

    # chunk_id COGITO_ID rejected
    _assert_rejects(
        lambda: make_text_stream_chunk(
            chunk_id=COGITO_ID,
            text="hello",
            source=TextStreamSource.OPERATOR,
            provenance="origin:t",
        ),
        tag="I-STRM-02",
    )
    # text == COGITO_ID rejected
    _assert_rejects(
        lambda: make_text_stream_chunk(
            chunk_id="chunk:bad-text-cogito",
            text=COGITO_ID,
            source=TextStreamSource.OPERATOR,
            provenance="origin:t",
        ),
        tag="I-STRM-02",
    )
    # provenance over-length
    _assert_rejects(
        lambda: make_text_stream_chunk(
            chunk_id="chunk:bad-prov",
            text="hello",
            source=TextStreamSource.OPERATOR,
            provenance="p" * (STREAM_PROVENANCE_MAX_LEN + 1),
        ),
        tag="I-STRM-02",
    )
    # missing provenance (empty)
    _assert_rejects(
        lambda: make_text_stream_chunk(
            chunk_id="chunk:no-prov",
            text="hello",
            source=TextStreamSource.OPERATOR,
            provenance="",
        ),
        tag="I-STRM-02",
    )
