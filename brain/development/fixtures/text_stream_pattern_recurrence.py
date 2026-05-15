"""Fixture for I-STRM-06: StreamPattern requires recurrence; no truth/agency field."""
from __future__ import annotations

from brain.development.text_stream import (
    STREAM_PATTERN_RECURRENCE_MAX,
    STREAM_PATTERN_RECURRENCE_MIN,
    STREAM_PATTERN_SIG_MAX,
    StreamPattern,
    make_stream_pattern,
)
from brain.invariants import register


@register("I-STRM-06", status="REQUIRED")
def check_stream_pattern_requires_recurrence() -> None:
    # Valid: recurrence_count at MIN works.
    p = make_stream_pattern(
        pattern_id="pat:1",
        signature=("alpha",),
        recurrence_count=STREAM_PATTERN_RECURRENCE_MIN,
    )
    assert p.recurrence_count == STREAM_PATTERN_RECURRENCE_MIN

    # StreamPattern must not expose truth / PRESERVE / agency fields.
    forbidden_attrs = (
        "preserve",
        "damage",
        "pce",
        "projected_pce",
        "feasible_projected_pce",
        "feasibleProjectedPCE",
        "act",
        "mode_op",
        "mode",
        "agency_witness",
        "agency",
        "truth",
        "validity",
        "readability_score",
        "language",
        "meaning",
        "tick_callback",
    )
    for name in forbidden_attrs:
        assert not hasattr(p, name), (
            f"I-STRM-06 violated: StreamPattern exposes forbidden field {name!r}"
        )

    # recurrence_count below MIN raises.
    try:
        StreamPattern(
            pattern_id="pat:undermin",
            signature=("alpha",),
            recurrence_count=STREAM_PATTERN_RECURRENCE_MIN - 1,
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-06" in str(exc), (
            f"I-STRM-06 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-06 violated: StreamPattern accepted recurrence_count below MIN"
        )

    # recurrence_count above MAX raises (direct construction).
    try:
        StreamPattern(
            pattern_id="pat:overmax",
            signature=("alpha",),
            recurrence_count=STREAM_PATTERN_RECURRENCE_MAX + 1,
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-06" in str(exc), (
            f"I-STRM-06 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-06 violated: StreamPattern accepted recurrence_count above MAX"
        )

    # make_stream_pattern saturates over-bound input rather than raising.
    saturated = make_stream_pattern(
        pattern_id="pat:saturated",
        signature=("alpha",),
        recurrence_count=STREAM_PATTERN_RECURRENCE_MAX + 9999,
    )
    assert saturated.recurrence_count == STREAM_PATTERN_RECURRENCE_MAX

    # empty signature raises.
    try:
        StreamPattern(
            pattern_id="pat:nosig",
            signature=(),
            recurrence_count=STREAM_PATTERN_RECURRENCE_MIN,
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-06" in str(exc), (
            f"I-STRM-06 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-06 violated: StreamPattern accepted empty signature"
        )

    # over-bound signature raises.
    try:
        StreamPattern(
            pattern_id="pat:bigsig",
            signature=tuple(f"tok-{i}" for i in range(STREAM_PATTERN_SIG_MAX + 1)),
            recurrence_count=STREAM_PATTERN_RECURRENCE_MIN,
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-06" in str(exc), (
            f"I-STRM-06 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-06 violated: StreamPattern accepted oversized signature"
        )

    # non-printable signature entry raises.
    try:
        StreamPattern(
            pattern_id="pat:badsig",
            signature=("ok", "bad\x00entry"),
            recurrence_count=STREAM_PATTERN_RECURRENCE_MIN,
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-06" in str(exc), (
            f"I-STRM-06 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-06 violated: StreamPattern accepted non-printable signature entry"
        )
