"""Fixture for I-STRM-07: StreamPromotionCandidate explicit, non-reserved, not PerceptEvent."""
from __future__ import annotations

from brain.development.text_stream import (
    STREAM_PROVENANCE_MAX_LEN,
    STREAM_TEXT_MAX_LEN,
    StreamPromotionCandidate,
    TextStreamSource,
    _COGITO_RESERVED_ID,
    make_stream_promotion_candidate,
)
from brain.invariants import register


def _assert_rejects(call, tag: str) -> None:
    try:
        call()
    except (TypeError, ValueError) as exc:
        assert tag in str(exc), (
            f"{tag} negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            f"{tag} violated: invalid StreamPromotionCandidate was accepted"
        )


@register("I-STRM-07", status="REQUIRED")
def check_stream_promotion_candidate_explicit_non_reserved() -> None:
    # Valid candidate.
    candidate = make_stream_promotion_candidate(
        candidate_id="pc:1",
        target_content_id="content:hello",
        source=TextStreamSource.OPERATOR,
        chunk_id="chunk:1",
        text="hello world",
        provenance="origin:operator",
        pattern_id="pat:greet",
    )
    assert candidate.candidate_id == "pc:1"
    assert candidate.target_content_id == "content:hello"
    assert candidate.source is TextStreamSource.OPERATOR
    assert candidate.chunk_id == "chunk:1"
    assert candidate.text == "hello world"
    assert candidate.provenance == "origin:operator"
    assert candidate.pattern_id == "pat:greet"

    # Valid candidate without pattern_id.
    no_pattern = make_stream_promotion_candidate(
        candidate_id="pc:2",
        target_content_id="content:goodbye",
        source=TextStreamSource.SYSTEM,
        chunk_id="chunk:2",
        text="goodbye",
        provenance="origin:system",
    )
    assert no_pattern.pattern_id is None

    # StreamPromotionCandidate must not be a PerceptEvent / expose runtime fields.
    forbidden_attrs = (
        "act",
        "mode_op",
        "agency_witness",
        "feasibleProjectedPCE",
        "feasible_projected_pce",
        "tick_callback",
        "event_queue_append",
        "rho",
        "initial_rho",
        "content_state",
        "tick",
        "preserve",
        "damage",
    )
    for name in forbidden_attrs:
        assert not hasattr(candidate, name), (
            f"I-STRM-07 violated: StreamPromotionCandidate exposes forbidden field {name!r}"
        )

    # target_content_id == COGITO_ID rejected.
    _assert_rejects(
        lambda: make_stream_promotion_candidate(
            candidate_id="pc:bad-cogito",
            target_content_id=_COGITO_RESERVED_ID,
            source=TextStreamSource.OPERATOR,
            chunk_id="chunk:1",
            text="hello",
            provenance="origin:t",
        ),
        tag="I-STRM-07",
    )
    # empty target_content_id rejected.
    _assert_rejects(
        lambda: make_stream_promotion_candidate(
            candidate_id="pc:bad-target",
            target_content_id="",
            source=TextStreamSource.OPERATOR,
            chunk_id="chunk:1",
            text="hello",
            provenance="origin:t",
        ),
        tag="I-STRM-07",
    )
    # missing source rejected.
    _assert_rejects(
        lambda: make_stream_promotion_candidate(
            candidate_id="pc:bad-source",
            target_content_id="content:x",
            source="OPERATOR",  # type: ignore[arg-type]
            chunk_id="chunk:1",
            text="hello",
            provenance="origin:t",
        ),
        tag="I-STRM-07",
    )
    # missing chunk_id rejected.
    _assert_rejects(
        lambda: make_stream_promotion_candidate(
            candidate_id="pc:bad-chunk",
            target_content_id="content:x",
            source=TextStreamSource.OPERATOR,
            chunk_id="",
            text="hello",
            provenance="origin:t",
        ),
        tag="I-STRM-07",
    )
    # empty provenance rejected.
    _assert_rejects(
        lambda: make_stream_promotion_candidate(
            candidate_id="pc:bad-prov",
            target_content_id="content:x",
            source=TextStreamSource.OPERATOR,
            chunk_id="chunk:1",
            text="hello",
            provenance="",
        ),
        tag="I-STRM-07",
    )
    # over-length provenance rejected.
    _assert_rejects(
        lambda: make_stream_promotion_candidate(
            candidate_id="pc:bad-prov-long",
            target_content_id="content:x",
            source=TextStreamSource.OPERATOR,
            chunk_id="chunk:1",
            text="hello",
            provenance="p" * (STREAM_PROVENANCE_MAX_LEN + 1),
        ),
        tag="I-STRM-07",
    )
    # empty text rejected.
    _assert_rejects(
        lambda: make_stream_promotion_candidate(
            candidate_id="pc:bad-text-empty",
            target_content_id="content:x",
            source=TextStreamSource.OPERATOR,
            chunk_id="chunk:1",
            text="",
            provenance="origin:t",
        ),
        tag="I-STRM-07",
    )
    # over-length text rejected.
    _assert_rejects(
        lambda: make_stream_promotion_candidate(
            candidate_id="pc:bad-text-long",
            target_content_id="content:x",
            source=TextStreamSource.OPERATOR,
            chunk_id="chunk:1",
            text="x" * (STREAM_TEXT_MAX_LEN + 1),
            provenance="origin:t",
        ),
        tag="I-STRM-07",
    )
    # text == COGITO_ID rejected.
    _assert_rejects(
        lambda: make_stream_promotion_candidate(
            candidate_id="pc:bad-text-cogito",
            target_content_id="content:x",
            source=TextStreamSource.OPERATOR,
            chunk_id="chunk:1",
            text=_COGITO_RESERVED_ID,
            provenance="origin:t",
        ),
        tag="I-STRM-07",
    )
    # over-length pattern_id rejected.
    _assert_rejects(
        lambda: make_stream_promotion_candidate(
            candidate_id="pc:bad-pat-long",
            target_content_id="content:x",
            source=TextStreamSource.OPERATOR,
            chunk_id="chunk:1",
            text="hello",
            provenance="origin:t",
            pattern_id="p" * (STREAM_PROVENANCE_MAX_LEN + 1),
        ),
        tag="I-STRM-07",
    )
