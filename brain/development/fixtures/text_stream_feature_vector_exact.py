"""Fixtures for I-STRM-04 (deterministic exact) and I-STRM-13 (frozen)."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from fractions import Fraction

from brain.development.text_stream import (
    StreamFeatureVector,
    TextStreamSource,
    extract_stream_features,
    make_text_stream_chunk,
)
from brain.invariants import register


@register("I-STRM-04", status="REQUIRED")
def check_stream_feature_vector_deterministic_exact() -> None:
    chunk = make_text_stream_chunk(
        chunk_id="chunk:a",
        text="abc abc\nabcd",
        source=TextStreamSource.OPERATOR,
        provenance="origin:t",
    )
    a = extract_stream_features(chunk)
    b = extract_stream_features(chunk)
    assert a == b, "I-STRM-04 violated: extract_stream_features is non-deterministic"
    assert isinstance(a.text_length, int) and not isinstance(a.text_length, bool)
    assert a.text_length == len(chunk.text)
    # printable_length counts chars per str.isprintable(); newline is excluded.
    expected_printable = sum(1 for ch in chunk.text if ch.isprintable())
    assert a.printable_length == expected_printable
    assert a.line_count == 2  # one newline => 2 lines
    assert a.whitespace_run_count >= 1
    assert a.distinct_char_count == len(set(chunk.text))
    assert isinstance(a.repeat_ratio, Fraction)
    expected_repeat = Fraction(len(chunk.text) - len(set(chunk.text)), len(chunk.text))
    assert a.repeat_ratio == expected_repeat

    # Bounds: repeat_ratio in [0, 1]; under "all distinct chars" it must be < 1.
    chunk_all_distinct = make_text_stream_chunk(
        chunk_id="chunk:b",
        text="abcdef",
        source=TextStreamSource.OPERATOR,
        provenance="origin:t",
    )
    feats = extract_stream_features(chunk_all_distinct)
    assert feats.distinct_char_count == 6
    assert feats.repeat_ratio == Fraction(0)

    chunk_all_same = make_text_stream_chunk(
        chunk_id="chunk:c",
        text="aaaaa",
        source=TextStreamSource.OPERATOR,
        provenance="origin:t",
    )
    feats_same = extract_stream_features(chunk_all_same)
    assert feats_same.distinct_char_count == 1
    assert feats_same.repeat_ratio == Fraction(4, 5)

    # Direct StreamFeatureVector validation: ratio out of range raises.
    try:
        StreamFeatureVector(
            chunk_id="chunk:bad",
            text_length=1,
            printable_length=1,
            line_count=1,
            whitespace_run_count=0,
            distinct_char_count=1,
            repeat_ratio=Fraction(3, 2),
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-04" in str(exc), (
            f"I-STRM-04 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-04 violated: StreamFeatureVector accepted out-of-range repeat_ratio"
        )

    try:
        StreamFeatureVector(
            chunk_id="chunk:bad-neg",
            text_length=-1,
            printable_length=0,
            line_count=1,
            whitespace_run_count=0,
            distinct_char_count=0,
            repeat_ratio=Fraction(0),
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-04" in str(exc), (
            f"I-STRM-04 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-04 violated: StreamFeatureVector accepted negative text_length"
        )


@register("I-STRM-13", status="STRUCTURAL")
def check_text_stream_records_are_frozen() -> None:
    """All six text-stream records (chunk, history, fv, segment, pattern,
    promotion) are immutable frozen dataclasses with bounded primitives
    or tuples thereof."""
    from brain.development.text_stream import (
        SegmentCandidate,
        StreamPattern,
        StreamPromotionCandidate,
        TextStreamChunk,
        TextStreamHistory,
        make_stream_pattern,
        make_stream_promotion_candidate,
    )

    chunk = make_text_stream_chunk(
        chunk_id="chunk:fz",
        text="abc",
        source=TextStreamSource.OPERATOR,
        provenance="origin:t",
    )
    history = TextStreamHistory().append(chunk)
    fv = StreamFeatureVector(
        chunk_id="chunk:fv",
        text_length=3,
        printable_length=3,
        line_count=1,
        whitespace_run_count=0,
        distinct_char_count=3,
        repeat_ratio=Fraction(0),
    )
    segment = SegmentCandidate(
        candidate_id="seg:1",
        chunk_id="chunk:fz",
        start=0,
        end=3,
        segment_kind="line",
    )
    pattern = make_stream_pattern(
        pattern_id="pat:1",
        signature=("abc",),
        recurrence_count=2,
    )
    promotion = make_stream_promotion_candidate(
        candidate_id="pc:1",
        target_content_id="content:abc",
        source=TextStreamSource.OPERATOR,
        chunk_id="chunk:fz",
        text="abc",
        provenance="origin:t",
    )
    records = (chunk, history, fv, segment, pattern, promotion)
    for record in records:
        assert is_dataclass(record), (
            f"I-STRM-13 violated: {type(record).__name__} is not a dataclass"
        )
        params = getattr(type(record), "__dataclass_params__")
        assert params.frozen, (
            f"I-STRM-13 violated: {type(record).__name__} is not frozen"
        )

    fv_field_names = {f.name for f in fields(fv)}
    expected_fv = {
        "chunk_id",
        "text_length",
        "printable_length",
        "line_count",
        "whitespace_run_count",
        "distinct_char_count",
        "repeat_ratio",
    }
    assert fv_field_names == expected_fv, (
        f"I-STRM-13 violated: unexpected StreamFeatureVector fields {fv_field_names}"
    )

    try:
        fv.text_length = 99  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "I-STRM-13 violated: StreamFeatureVector allowed attribute mutation"
        )
    try:
        segment.start = 7  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "I-STRM-13 violated: SegmentCandidate allowed attribute mutation"
        )
    try:
        pattern.recurrence_count = 99  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "I-STRM-13 violated: StreamPattern allowed attribute mutation"
        )
    try:
        promotion.target_content_id = "other"  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "I-STRM-13 violated: StreamPromotionCandidate allowed attribute mutation"
        )
