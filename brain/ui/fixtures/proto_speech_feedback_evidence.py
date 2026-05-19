"""Phase 3.31 caregiver feedback + evidence-update bounds fixture.

Drives ``I-PSPEECH-03`` (REQUIRED) and ``I-PSPEECH-04`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.proto_speech_acquisition import (
    PROTO_SPEECH_DIGEST_HEX_LEN,
    PROTO_SPEECH_EVIDENCE_TABLE_MAX,
    PROTO_SPEECH_WEIGHT_MAX,
    PROTO_SPEECH_WEIGHT_MIN,
    CaregiverFeedback,
    CaregiverFeedbackKind,
    ProtoSpeechEvidenceRecord,
    ProtoSpeechEvidenceTable,
    ProtoUtteranceDisposition,
    ProtoVocalToken,
    build_proto_speech_context,
    build_proto_utterance,
    empty_evidence_table,
    update_proto_speech_evidence,
)
from brain.invariants import register


def _assert_raises(callable_):
    try:
        callable_()
    except (TypeError, ValueError):
        return
    raise AssertionError("expected TypeError or ValueError; none raised")


@register("I-PSPEECH-03", status="REQUIRED")
def check_caregiver_feedback_bounds() -> None:
    """CaregiverFeedback validates fields and audits the context_label."""
    u = build_proto_utterance((ProtoVocalToken.SAME,))
    fb = CaregiverFeedback(
        kind=CaregiverFeedbackKind.ECHO,
        offered_utterance=u,
        ambient_utterance=None,
        context_label="ctx-fb",
        evidence_delta=3,
    )
    assert fb.kind is CaregiverFeedbackKind.ECHO
    assert fb.offered_utterance is u

    # Forbidden direct-instruction in label.
    _assert_raises(
        lambda: CaregiverFeedback(
            kind=CaregiverFeedbackKind.ECHO,
            offered_utterance=u,
            ambient_utterance=None,
            context_label="alpha forget",
            evidence_delta=3,
        )
    )
    # Non-CaregiverFeedbackKind kind rejected.
    _assert_raises(
        lambda: CaregiverFeedback(
            kind="accepted",
            offered_utterance=None,
            ambient_utterance=None,
            context_label="ctx-fb",
            evidence_delta=3,
        )
    )
    # Non-ProtoUtterance offered.
    _assert_raises(
        lambda: CaregiverFeedback(
            kind=CaregiverFeedbackKind.ECHO,
            offered_utterance="ba",
            ambient_utterance=None,
            context_label="ctx-fb",
            evidence_delta=3,
        )
    )
    # Out-of-bound evidence_delta.
    _assert_raises(
        lambda: CaregiverFeedback(
            kind=CaregiverFeedbackKind.ECHO,
            offered_utterance=None,
            ambient_utterance=None,
            context_label="ctx-fb",
            evidence_delta=100,
        )
    )


@register("I-PSPEECH-04", status="REQUIRED")
def check_evidence_update_rules() -> None:
    """Evidence table updates obey closed integer-rule and bounds."""
    table = empty_evidence_table()
    assert isinstance(table, ProtoSpeechEvidenceTable)
    assert table.entries == ()
    assert len(table.digest_hex16) == PROTO_SPEECH_DIGEST_HEX_LEN
    assert table.max_records == PROTO_SPEECH_EVIDENCE_TABLE_MAX

    ctx = build_proto_speech_context(
        abstract_pattern_digest="0123456789abcdef",
        abstract_pattern_shape="A B A",
    )
    u = build_proto_utterance((ProtoVocalToken.SAME,))

    # ACCEPTED: +3 to attempted form. Transition: BABBLE -> CANDIDATE
    # because weight 3 is below STABLE_SINGLE_THRESHOLD (6).
    fb_ack = CaregiverFeedback(
        kind=CaregiverFeedbackKind.ACCEPTED,
        offered_utterance=None,
        ambient_utterance=None,
        context_label="ctx-fb",
        evidence_delta=3,
    )
    t1, recs1 = update_proto_speech_evidence(
        table, context=ctx, attempted=u, feedback=fb_ack
    )
    assert recs1[0].weight_after == 3
    assert recs1[0].disposition is ProtoUtteranceDisposition.CANDIDATE

    # ECHO again: +3 -> 6 -> STABLE_SINGLE.
    fb_echo = CaregiverFeedback(
        kind=CaregiverFeedbackKind.ECHO,
        offered_utterance=None,
        ambient_utterance=None,
        context_label="ctx-fb",
        evidence_delta=3,
    )
    t2, recs2 = update_proto_speech_evidence(
        t1, context=ctx, attempted=u, feedback=fb_echo
    )
    assert recs2[0].weight_after == 6
    assert recs2[0].disposition is ProtoUtteranceDisposition.STABLE_SINGLE

    # CORRECTED: -2 to attempted, +3 to offered.
    offered = build_proto_utterance((ProtoVocalToken.YES,))
    fb_corr = CaregiverFeedback(
        kind=CaregiverFeedbackKind.CORRECTED,
        offered_utterance=offered,
        ambient_utterance=None,
        context_label="ctx-fb",
        evidence_delta=-2,
    )
    t3, recs3 = update_proto_speech_evidence(
        t2, context=ctx, attempted=u, feedback=fb_corr
    )
    # Two records produced: attempted -2 (6 -> 4), offered +3 (0 -> 3).
    assert len(recs3) == 2
    assert recs3[0].weight_after == 4
    assert recs3[1].weight_after == 3

    # IGNORED: -1 to attempted only.
    fb_ig = CaregiverFeedback(
        kind=CaregiverFeedbackKind.IGNORED,
        offered_utterance=None,
        ambient_utterance=None,
        context_label="ctx-fb",
        evidence_delta=-1,
    )
    t4, recs4 = update_proto_speech_evidence(
        t3, context=ctx, attempted=u, feedback=fb_ig
    )
    assert recs4[0].weight_after == 3

    # AMBIENT_ONLY: +1 to ambient form only.
    amb = build_proto_utterance((ProtoVocalToken.LOOK,))
    fb_amb = CaregiverFeedback(
        kind=CaregiverFeedbackKind.AMBIENT_ONLY,
        offered_utterance=None,
        ambient_utterance=amb,
        context_label="ctx-fb",
        evidence_delta=1,
    )
    t5, recs5 = update_proto_speech_evidence(
        t4, context=ctx, attempted=u, feedback=fb_amb
    )
    # Attempted delta is 0 for AMBIENT_ONLY; only the ambient form moves.
    assert len(recs5) == 1
    assert recs5[0].utterance_digest == amb.digest_hex16
    assert recs5[0].weight_after == 1

    # Determinism: same inputs produce equal new tables.
    t1b, recs1b = update_proto_speech_evidence(
        table, context=ctx, attempted=u, feedback=fb_ack
    )
    assert recs1b == recs1
    assert t1b.digest_hex16 == t1.digest_hex16

    # ProtoSpeechEvidenceRecord bounds.
    _assert_raises(
        lambda: ProtoSpeechEvidenceRecord(
            context_signature="0" * 16,
            utterance_digest="0" * 16,
            utterance_text="ba",
            feedback_kind=CaregiverFeedbackKind.ACCEPTED,
            weight_before=0,
            weight_after=PROTO_SPEECH_WEIGHT_MAX + 1,
            disposition=ProtoUtteranceDisposition.REINFORCED,
            update_reason="reason",
            drive_stream_digest_hex16=None,
            digest_hex16="0" * 16,
        )
    )
    _assert_raises(
        lambda: ProtoSpeechEvidenceRecord(
            context_signature="0" * 16,
            utterance_digest="0" * 16,
            utterance_text="ba",
            feedback_kind=CaregiverFeedbackKind.ACCEPTED,
            weight_before=PROTO_SPEECH_WEIGHT_MIN - 1,
            weight_after=0,
            disposition=ProtoUtteranceDisposition.REINFORCED,
            update_reason="reason",
            drive_stream_digest_hex16=None,
            digest_hex16="0" * 16,
        )
    )
