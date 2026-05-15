"""Fixture for I-STRM-05: SegmentCandidate is structural (closed vocabulary)."""
from __future__ import annotations

from brain.development.text_stream import (
    ALLOWED_SEGMENT_KINDS,
    STREAM_SEGMENTS_MAX,
    SegmentCandidate,
    TextStreamSource,
    extract_segment_candidates,
    make_text_stream_chunk,
)
from brain.invariants import register


@register("I-STRM-05", status="REQUIRED")
def check_segment_candidate_is_structural() -> None:
    # Closed vocabulary.
    assert ALLOWED_SEGMENT_KINDS == ("line", "delimited_span", "whitespace_run")

    # Valid construction.
    seg = SegmentCandidate(
        candidate_id="seg:1",
        chunk_id="chunk:1",
        start=0,
        end=5,
        segment_kind="line",
    )
    assert seg.segment_kind == "line"
    assert seg.start == 0 and seg.end == 5

    # SegmentCandidate must not expose payload / parse / language fields.
    forbidden_attrs = (
        "text",
        "payload",
        "tokens",
        "parse_tree",
        "ast",
        "language",
        "meaning",
        "truth",
        "preserve",
        "damage",
        "readability_score",
        "act",
        "agency_witness",
        "tick_callback",
    )
    for name in forbidden_attrs:
        assert not hasattr(seg, name), (
            f"I-STRM-05 violated: SegmentCandidate exposes forbidden field {name!r}"
        )

    # segment_kind outside vocabulary raises.
    try:
        SegmentCandidate(
            candidate_id="seg:bad-kind",
            chunk_id="chunk:1",
            start=0,
            end=1,
            segment_kind="sentence",
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-05" in str(exc), (
            f"I-STRM-05 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-05 violated: SegmentCandidate accepted segment_kind outside "
            f"{ALLOWED_SEGMENT_KINDS}"
        )

    # end < start raises.
    try:
        SegmentCandidate(
            candidate_id="seg:bad-span",
            chunk_id="chunk:1",
            start=5,
            end=3,
            segment_kind="line",
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-05" in str(exc), (
            f"I-STRM-05 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-05 violated: SegmentCandidate accepted end < start"
        )

    # negative start raises.
    try:
        SegmentCandidate(
            candidate_id="seg:bad-neg",
            chunk_id="chunk:1",
            start=-1,
            end=1,
            segment_kind="line",
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-05" in str(exc), (
            f"I-STRM-05 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-05 violated: SegmentCandidate accepted negative start"
        )

    # Extraction is deterministic and bounded.
    chunk = make_text_stream_chunk(
        chunk_id="chunk:seg",
        text="alpha\nbeta\ngamma\ndelta",
        source=TextStreamSource.OPERATOR,
        provenance="origin:t",
    )
    a = extract_segment_candidates(chunk)
    b = extract_segment_candidates(chunk)
    assert a == b, "I-STRM-05 violated: extract_segment_candidates is non-deterministic"
    assert len(a) <= STREAM_SEGMENTS_MAX
    for seg in a:
        assert seg.segment_kind in ALLOWED_SEGMENT_KINDS
        assert seg.chunk_id == chunk.chunk_id
        assert 0 <= seg.start <= seg.end <= len(chunk.text)
    # Four lines from three newlines.
    assert len(a) == 4

    # Huge chunk yields at most STREAM_SEGMENTS_MAX segments.
    big_text = "\n".join(f"line-{i}" for i in range(STREAM_SEGMENTS_MAX * 2))
    big_chunk = make_text_stream_chunk(
        chunk_id="chunk:bigseg",
        text=big_text,
        source=TextStreamSource.OPERATOR,
        provenance="origin:t",
    )
    big = extract_segment_candidates(big_chunk)
    assert len(big) <= STREAM_SEGMENTS_MAX
