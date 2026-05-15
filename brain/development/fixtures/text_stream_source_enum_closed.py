"""Fixture for I-STRM-01: TextStreamSource is a finite closed enumeration."""
from __future__ import annotations

from brain.development.text_stream import (
    TextStreamChunk,
    TextStreamSource,
)
from brain.invariants import register


_EXPECTED_MEMBERS = {"OPERATOR", "SYSTEM", "PROBE_ECHO", "GENERATED"}


@register("I-STRM-01", status="REQUIRED")
def check_text_stream_source_is_finite_closed() -> None:
    members = {m.name for m in TextStreamSource}
    assert members == _EXPECTED_MEMBERS, (
        f"I-STRM-01 violated: TextStreamSource members {members} != "
        f"expected {_EXPECTED_MEMBERS}"
    )
    for member in TextStreamSource:
        assert isinstance(member.value, str)
        assert member.value and member.value.isprintable()

    try:
        TextStreamChunk(
            chunk_id="chunk:bad-source",
            text="hello",
            source="OPERATOR",  # type: ignore[arg-type]
            provenance="origin:test",
        )
    except (TypeError, ValueError) as exc:
        assert "I-STRM-02" in str(exc) or "I-STRM-01" in str(exc), (
            "I-STRM-01 negative-case message lacks row tag: "
            f"{exc!r}"
        )
    else:
        raise AssertionError(
            "I-STRM-01 violated: non-TextStreamSource source was accepted"
        )
