"""Phase 3.31 holophrase transfer fixture.

Drives ``I-PSPEECH-10`` (REQUIRED). Covers both the positive
same-shape transfer and the negative different-shape control.
"""
from __future__ import annotations

from brain.development.proto_speech_acquisition import (
    ProtoSpeechCondition,
    ProtoSpeechStatus,
    ProtoUtteranceDisposition,
    ProtoVocalToken,
    build_proto_utterance,
    run_proto_speech_live_test,
)
from brain.invariants import register


@register("I-PSPEECH-10", status="REQUIRED")
def check_holophrase_transfer() -> None:
    """Stable single transfers to renamed same-shape context only."""
    report = run_proto_speech_live_test()
    status_map = dict(report.condition_statuses)
    assert status_map.get(
        ProtoSpeechCondition.HOLOPHRASE_TRANSFER
    ) is ProtoSpeechStatus.PASS

    holo_turns = [
        t
        for t in report.turns
        if t.condition is ProtoSpeechCondition.HOLOPHRASE_TRANSFER
    ]
    assert holo_turns
    assert report.transfer_success_count == 1, (
        f"transfer_success_count: {report.transfer_success_count}"
    )
    assert report.false_positive_count == 0

    # The penultimate turn is the positive target; the last turn is
    # the negative-control different-shape context.
    pos_turn = holo_turns[-2]
    neg_turn = holo_turns[-1]
    assert pos_turn.transfer_taken is True, (
        f"positive transfer not taken: {pos_turn.turn_id}"
    )
    assert neg_turn.transfer_taken is False, (
        f"negative transfer should not have been taken: {neg_turn.turn_id}"
    )

    this_utt = build_proto_utterance((ProtoVocalToken.THIS,))
    # Walk the positive target's evidence records for a TRANSFERRED
    # disposition.
    found_transferred = False
    for r in pos_turn.evidence_records_added:
        if r.utterance_digest == this_utt.digest_hex16 and (
            r.disposition is ProtoUtteranceDisposition.TRANSFERRED
        ):
            found_transferred = True
    assert found_transferred, (
        "positive target missing TRANSFERRED record"
    )

    # Negative target context must not carry a TRANSFERRED record for
    # THIS.
    for r in neg_turn.evidence_records_added:
        if r.utterance_digest == this_utt.digest_hex16:
            assert r.disposition is not (
                ProtoUtteranceDisposition.TRANSFERRED
            ), "negative-control context picked up transferred form"
