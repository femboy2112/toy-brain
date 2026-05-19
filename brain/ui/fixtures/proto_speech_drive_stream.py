"""Phase 3.31 drive stream + drive-grounded babble fixture.

Drives ``I-PSPEECH-14`` (REQUIRED) and ``I-PSPEECH-15`` (REQUIRED).
"""
from __future__ import annotations

import inspect

import brain.development.proto_speech_acquisition as _pspeech
from brain.development.proto_speech_acquisition import (
    PROTO_SPEECH_DIGEST_HEX_LEN,
    PROTO_SPEECH_MAX_FRAMES_PER_STREAM,
    PROTO_SPEECH_SUGGESTED_SET_MAX,
    PROTO_SPEECH_WEIGHT_HINT_MAX,
    CaregiverFeedback,
    CaregiverFeedbackKind,
    ProtoSpeechDriveFrame,
    ProtoSpeechDriveKind,
    ProtoSpeechDriveStream,
    ProtoSpeechStatus,
    ProtoVocalToken,
    REFUSAL_SENTINEL,
    build_proto_speech_context,
    build_proto_speech_drive_stream,
    build_proto_utterance,
    empty_evidence_table,
    select_babble_from_drive_stream,
)
from brain.invariants import register


def _assert_raises(callable_):
    try:
        callable_()
    except (TypeError, ValueError):
        return
    raise AssertionError("expected TypeError or ValueError; none raised")


@register("I-PSPEECH-14", status="REQUIRED")
def check_drive_stream_construction_bounds() -> None:
    """ProtoSpeechDriveFrame / ProtoSpeechDriveStream bounds and determinism."""
    ctx = build_proto_speech_context(
        abstract_pattern_digest="0123456789abcdef",
        abstract_pattern_shape="A B A",
    )
    s1 = build_proto_speech_drive_stream(
        context=ctx, input_text="alpha beta alpha"
    )
    s2 = build_proto_speech_drive_stream(
        context=ctx, input_text="alpha beta alpha"
    )
    assert isinstance(s1, ProtoSpeechDriveStream)
    assert s1.digest_hex16 == s2.digest_hex16
    assert s1.frames == s2.frames
    assert s1.status is ProtoSpeechStatus.PASS
    assert s1.max_frames == PROTO_SPEECH_MAX_FRAMES_PER_STREAM
    assert len(s1.digest_hex16) == PROTO_SPEECH_DIGEST_HEX_LEN

    # Frame bounds.
    base_frame = ProtoSpeechDriveFrame(
        drive_kind=ProtoSpeechDriveKind.LOW_EVIDENCE,
        source_surface="evidence_table",
        context_signature=ctx.context_signature,
        input_digest_hex16="0" * 16,
        evidence_digest_hex16=None,
        reasoning_trace_digest_hex16=None,
        dispatch_trace_digest_hex16=None,
        caregiver_utterance_digest_hex16=None,
        weight_hint=2,
        suggested_token_set=(ProtoVocalToken.BA,),
        explanation="low evidence",
    )
    assert isinstance(base_frame, ProtoSpeechDriveFrame)

    # Reject duplicate suggestions.
    _assert_raises(
        lambda: ProtoSpeechDriveFrame(
            drive_kind=ProtoSpeechDriveKind.LOW_EVIDENCE,
            source_surface="evidence_table",
            context_signature=ctx.context_signature,
            input_digest_hex16="0" * 16,
            evidence_digest_hex16=None,
            reasoning_trace_digest_hex16=None,
            dispatch_trace_digest_hex16=None,
            caregiver_utterance_digest_hex16=None,
            weight_hint=2,
            suggested_token_set=(
                ProtoVocalToken.BA, ProtoVocalToken.BA,
            ),
            explanation="dup",
        )
    )
    # Reject oversize suggested_token_set.
    _assert_raises(
        lambda: ProtoSpeechDriveFrame(
            drive_kind=ProtoSpeechDriveKind.LOW_EVIDENCE,
            source_surface="evidence_table",
            context_signature=ctx.context_signature,
            input_digest_hex16="0" * 16,
            evidence_digest_hex16=None,
            reasoning_trace_digest_hex16=None,
            dispatch_trace_digest_hex16=None,
            caregiver_utterance_digest_hex16=None,
            weight_hint=2,
            suggested_token_set=tuple(
                list(ProtoVocalToken)[: PROTO_SPEECH_SUGGESTED_SET_MAX + 1]
            ),
            explanation="oversize",
        )
    )
    # weight_hint must be in [0, 16].
    _assert_raises(
        lambda: ProtoSpeechDriveFrame(
            drive_kind=ProtoSpeechDriveKind.LOW_EVIDENCE,
            source_surface="evidence_table",
            context_signature=ctx.context_signature,
            input_digest_hex16="0" * 16,
            evidence_digest_hex16=None,
            reasoning_trace_digest_hex16=None,
            dispatch_trace_digest_hex16=None,
            caregiver_utterance_digest_hex16=None,
            weight_hint=PROTO_SPEECH_WEIGHT_HINT_MAX + 1,
            suggested_token_set=(ProtoVocalToken.BA,),
            explanation="over",
        )
    )


@register("I-PSPEECH-15", status="REQUIRED")
def check_drive_grounded_babble_no_random() -> None:
    """Babble selection comes from drive stream; no random / time import."""
    ctx = build_proto_speech_context(
        abstract_pattern_digest="0123456789abcdef",
        abstract_pattern_shape="A B A",
    )
    table = empty_evidence_table()

    # LOW_EVIDENCE baseline returns one of (BA, MA, DA) and varies
    # by turn_index modulo 3.
    s = build_proto_speech_drive_stream(
        context=ctx, input_text="alpha beta alpha"
    )
    picks = [
        select_babble_from_drive_stream(
            drive_stream=s,
            evidence_table=table,
            context=ctx,
            turn_index=i,
        )
        for i in range(3)
    ]
    assert {p.tokens[0] for p in picks} == {
        ProtoVocalToken.BA,
        ProtoVocalToken.MA,
        ProtoVocalToken.DA,
    }

    # CAREGIVER_FEEDBACK_PRIME wins single selection.
    look = build_proto_utterance((ProtoVocalToken.LOOK,))
    fb = CaregiverFeedback(
        kind=CaregiverFeedbackKind.ACCEPTED,
        offered_utterance=look,
        ambient_utterance=None,
        context_label="ctx-fb",
        evidence_delta=3,
    )
    s2 = build_proto_speech_drive_stream(
        context=ctx, caregiver_feedback=fb, input_text="alpha beta alpha"
    )
    u = select_babble_from_drive_stream(
        drive_stream=s2,
        evidence_table=table,
        context=ctx,
        turn_index=0,
    )
    assert u.text == "look"

    # REFUSAL_GUARD returns the sentinel.
    s3 = build_proto_speech_drive_stream(
        context=ctx, refusal_guard=True
    )
    u3 = select_babble_from_drive_stream(
        drive_stream=s3,
        evidence_table=table,
        context=ctx,
        turn_index=0,
    )
    assert u3 == REFUSAL_SENTINEL
    assert u3.token_count == 0

    # Module source contains no random / time import.
    src = inspect.getsource(_pspeech)
    assert "import random" not in src
    assert "from random" not in src
    assert "import time" not in src
    assert "from time" not in src
