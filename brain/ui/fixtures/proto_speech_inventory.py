"""Phase 3.31 proto-vocal inventory + ProtoUtterance bounds fixture.

Drives ``I-PSPEECH-01`` (REQUIRED) and ``I-PSPEECH-02`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.proto_speech_acquisition import (
    PROTO_SPEECH_DIGEST_HEX_LEN,
    CaregiverFeedback,
    CaregiverFeedbackKind,
    ProtoSpeechContext,
    ProtoSpeechContextKind,
    ProtoUtterance,
    ProtoVocalToken,
    build_proto_speech_context,
    build_proto_utterance,
)
from brain.invariants import register


_EXPECTED_VOCAL_TOKEN_VALUES = frozenset({
    "ba", "ma", "da", "na", "la",
    "same", "more", "again", "no", "yes",
    "look", "this", "that", "help", "done",
})


def _assert_raises(callable_):
    try:
        callable_()
    except (TypeError, ValueError):
        return
    raise AssertionError("expected TypeError or ValueError; none raised")


@register("I-PSPEECH-01", status="REQUIRED")
def check_proto_speech_record_bounds() -> None:
    """Records reject invalid input."""
    # ProtoUtterance happy path.
    u = build_proto_utterance((ProtoVocalToken.BA,))
    assert u == build_proto_utterance((ProtoVocalToken.BA,))
    assert u.token_count == 1
    assert u.text == "ba"
    assert len(u.digest_hex16) == PROTO_SPEECH_DIGEST_HEX_LEN

    # Length bound: >2 tokens rejected.
    _assert_raises(
        lambda: build_proto_utterance(
            (ProtoVocalToken.BA, ProtoVocalToken.MA, ProtoVocalToken.DA)
        )
    )
    # Wrong tokens-type rejected.
    _assert_raises(lambda: build_proto_utterance(["ba"]))
    _assert_raises(lambda: build_proto_utterance((ProtoVocalToken.BA, "ma")))

    # CaregiverFeedback happy path + bounds.
    fb = CaregiverFeedback(
        kind=CaregiverFeedbackKind.ACCEPTED,
        offered_utterance=None,
        ambient_utterance=None,
        context_label="ctx-1",
        evidence_delta=3,
    )
    assert fb.kind is CaregiverFeedbackKind.ACCEPTED
    assert fb.evidence_delta == 3
    # Forbidden direct-instruction in label rejected.
    _assert_raises(
        lambda: CaregiverFeedback(
            kind=CaregiverFeedbackKind.ACCEPTED,
            offered_utterance=None,
            ambient_utterance=None,
            context_label="alpha curriculum",
            evidence_delta=3,
        )
    )
    # evidence_delta out of bound.
    _assert_raises(
        lambda: CaregiverFeedback(
            kind=CaregiverFeedbackKind.ACCEPTED,
            offered_utterance=None,
            ambient_utterance=None,
            context_label="ctx-1",
            evidence_delta=99,
        )
    )

    # ProtoSpeechContext happy path + bounds.
    ctx = build_proto_speech_context(
        abstract_pattern_digest="0123456789abcdef",
        abstract_pattern_shape="A B A",
    )
    assert isinstance(ctx, ProtoSpeechContext)
    assert ctx.context_kind is ProtoSpeechContextKind.ABSTRACT_PATTERN
    assert len(ctx.context_signature) == PROTO_SPEECH_DIGEST_HEX_LEN
    # Non-16-hex digest rejected.
    _assert_raises(
        lambda: build_proto_speech_context(abstract_pattern_digest="short")
    )


@register("I-PSPEECH-02", status="REQUIRED")
def check_proto_vocal_inventory_closed() -> None:
    """ProtoVocalToken is the closed 15-token inventory."""
    values = frozenset(t.value for t in ProtoVocalToken)
    assert values == _EXPECTED_VOCAL_TOKEN_VALUES, (
        f"I-PSPEECH-02 violated: ProtoVocalToken values drifted: {values}"
    )
    assert len(list(ProtoVocalToken)) == 15

    # 1-token utterance.
    u1 = build_proto_utterance((ProtoVocalToken.BA,))
    assert u1.token_count == 1
    assert u1.text == "ba"
    assert not u1.reduplicated

    # 2-token distinct utterance.
    u2 = build_proto_utterance((ProtoVocalToken.SAME, ProtoVocalToken.AGAIN))
    assert u2.token_count == 2
    assert u2.text == "same again"
    assert not u2.reduplicated

    # 2-token reduplicated utterance.
    u3 = build_proto_utterance((ProtoVocalToken.BA, ProtoVocalToken.BA))
    assert u3.reduplicated is True

    # Deterministic digest.
    u4 = build_proto_utterance((ProtoVocalToken.BA,))
    assert u4.digest_hex16 == u1.digest_hex16

    # Inventory size.
    assert len(_EXPECTED_VOCAL_TOKEN_VALUES) == 15
