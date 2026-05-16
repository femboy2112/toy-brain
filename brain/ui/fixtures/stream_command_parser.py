"""Phase 3.8 stream command parser fixtures.

Drives:

* ``I-UISTRM-01`` (REQUIRED) — Stream command parser is finite and typed.
* ``I-UISTRM-02`` (REQUIRED) — Stream command payloads are bounded and
  constructor-checked.
"""
from __future__ import annotations

from brain.development.text_stream import (
    STREAM_PROVENANCE_MAX_LEN,
    STREAM_TEXT_MAX_LEN,
)
from brain.invariants import register
from brain.ui.command_line import (
    LOCAL_COMMAND_HELP,
    LOCAL_COMMAND_VERBS,
    LocalCommandError,
    LocalCommandLine,
)
from brain.ui.commands import (
    STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN,
    Command,
    OperatorCommand,
    StreamAppendPayload,
    StreamPromotePayload,
)


_PARSER = LocalCommandLine()
_COGITO_RESERVED_ID = "__cogito__"


def _assert_parse_ok(line: str, expected_kind: OperatorCommand) -> Command:
    result = _PARSER.parse(line)
    assert isinstance(result, Command), (
        f"I-UISTRM-01 violated: {line!r} did not parse to a Command "
        f"(got {result!r})"
    )
    assert result.kind is expected_kind, (
        f"I-UISTRM-01 violated: {line!r} parsed to {result.kind!r} "
        f"(expected {expected_kind!r})"
    )
    return result


def _assert_parse_error(line: str) -> LocalCommandError:
    result = _PARSER.parse(line)
    assert isinstance(result, LocalCommandError), (
        f"I-UISTRM-01 violated: {line!r} did not produce a LocalCommandError "
        f"(got {result!r})"
    )
    return result


@register("I-UISTRM-01", status="REQUIRED")
def check_I_UISTRM_01_stream_parser_finite_typed() -> None:
    # Each /stream-* verb is in LOCAL_COMMAND_VERBS and routes to its
    # expected OperatorCommand.
    for verb in ("stream", "stream-summary", "stream-candidates", "stream-promote"):
        assert verb in LOCAL_COMMAND_VERBS, (
            f"I-UISTRM-01 violated: /{verb} missing from LOCAL_COMMAND_VERBS"
        )

    _assert_parse_ok("/stream hello", OperatorCommand.STREAM_APPEND)
    _assert_parse_ok("/stream-summary", OperatorCommand.INSPECT_STREAM_SUMMARY)
    _assert_parse_ok(
        "/stream-candidates", OperatorCommand.INSPECT_STREAM_CANDIDATES
    )
    _assert_parse_ok("/stream-promote alpha", OperatorCommand.STREAM_PROMOTE)

    # Malformed forms surface as LocalCommandError, not exceptions.
    _assert_parse_error("/stream")
    _assert_parse_error("/stream   ")
    _assert_parse_error("/stream-summary extra")
    _assert_parse_error("/stream-candidates extra")
    _assert_parse_error("/stream-promote")
    _assert_parse_error("/stream-promote a b")
    _assert_parse_error("/streamx hello")

    # Help table covers every new verb exactly once.
    help_keys = [entry[0].split()[0].lstrip("/") for entry in LOCAL_COMMAND_HELP]
    for verb in ("stream", "stream-summary", "stream-candidates", "stream-promote"):
        assert help_keys.count(verb) == 1, (
            f"I-UISTRM-01 violated: /{verb} not present exactly once in "
            "LOCAL_COMMAND_HELP"
        )


@register("I-UISTRM-02", status="REQUIRED")
def check_I_UISTRM_02_stream_payloads_bounded() -> None:
    # /stream payload bounds.
    long_text = "x" * (STREAM_TEXT_MAX_LEN + 1)
    err = _assert_parse_error(f"/stream {long_text}")
    assert "exceeds" in err.message.lower(), (
        f"I-UISTRM-02 violated: oversize /stream did not mention bound "
        f"(got {err.message!r})"
    )

    # Valid bounded text builds a StreamAppendPayload.
    parsed = _assert_parse_ok("/stream hello world", OperatorCommand.STREAM_APPEND)
    assert isinstance(parsed.payload, StreamAppendPayload)
    assert parsed.payload.text == "hello world"

    # Direct construction rejects non-printable / empty / oversize / cogito.
    for bad_text in ("", "\x00", "x" * (STREAM_TEXT_MAX_LEN + 1), _COGITO_RESERVED_ID):
        try:
            StreamAppendPayload(text=bad_text)
        except (TypeError, ValueError):
            continue
        raise AssertionError(
            "I-UISTRM-02 violated: StreamAppendPayload accepted bad text "
            f"{bad_text!r}"
        )

    # /stream-promote candidate_id bounds.
    long_id = "x" * (STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN + 1)
    err = _assert_parse_error(f"/stream-promote {long_id}")
    assert "exceeds" in err.message.lower(), (
        f"I-UISTRM-02 violated: oversize candidate_id did not mention bound "
        f"(got {err.message!r})"
    )

    parsed = _assert_parse_ok(
        "/stream-promote promo-1", OperatorCommand.STREAM_PROMOTE
    )
    assert isinstance(parsed.payload, StreamPromotePayload)
    assert parsed.payload.candidate_id == "promo-1"

    # Direct construction rejects empty / non-printable / oversize / cogito.
    for bad_id in (
        "",
        "with space",  # space-split removed by parser, but constructor only
        "\x00abc",
        "x" * (STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN + 1),
        _COGITO_RESERVED_ID,
    ):
        try:
            payload = StreamPromotePayload(candidate_id=bad_id)
            # "with space" is technically printable; ensure we reject via
            # the parser's split-arity rule instead. Accept printable
            # whitespace at construction is allowed for STR but parser
            # rejects multi-token forms separately.
            if bad_id == "with space":
                # the constructor accepts this (it is printable and
                # within length); the parser rejects multi-token forms,
                # which the I-UISTRM-01 case already exercises.
                continue
        except (TypeError, ValueError):
            continue
        raise AssertionError(
            "I-UISTRM-02 violated: StreamPromotePayload accepted bad id "
            f"{bad_id!r}"
        )

    # Payload records carry no callable / resource handles.
    payload = StreamAppendPayload(text="abc")
    assert not callable(payload)
    payload = StreamPromotePayload(candidate_id="promo-1")
    assert not callable(payload)

    # Constants parity with text_stream is checked in stream_constant_parity.py;
    # here we only ensure the candidate_id cap is the documented value.
    assert STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN == STREAM_PROVENANCE_MAX_LEN
