"""Phase 3.31 turn-taking + refusal-held fixture.

Drives ``I-PSPEECH-12`` (REQUIRED) and ``I-PSPEECH-13`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.proto_speech_acquisition import (
    ProtoSpeechCondition,
    ProtoSpeechDriveKind,
    ProtoSpeechStatus,
    run_proto_speech_live_test,
)
from brain.invariants import register


@register("I-PSPEECH-12", status="REQUIRED")
def check_turn_taking_order() -> None:
    """Turn-taking proves the closed bounded turn order."""
    report = run_proto_speech_live_test()
    status_map = dict(report.condition_statuses)
    assert status_map.get(
        ProtoSpeechCondition.TURN_TAKING
    ) is ProtoSpeechStatus.PASS

    tt_turns = [
        t
        for t in report.turns
        if t.condition is ProtoSpeechCondition.TURN_TAKING
    ]
    assert len(tt_turns) == 1
    t = tt_turns[0]
    assert not t.refusal_taken
    assert len(t.drive_stream.frames) >= 1
    assert t.selected_utterance.token_count > 0
    assert len(t.evidence_records_added) >= 1
    assert t.context.context_signature
    assert t.feedback.kind  # closed enum membership already enforced

    # Determinism: two invocations produce equal turn records.
    report_b = run_proto_speech_live_test()
    tt_b = [
        t
        for t in report_b.turns
        if t.condition is ProtoSpeechCondition.TURN_TAKING
    ]
    assert tt_turns == tt_b


@register("I-PSPEECH-13", status="REQUIRED")
def check_refusal_held() -> None:
    """Cognitive-claim refusal path stays intact under proto-speech load."""
    report = run_proto_speech_live_test()
    status_map = dict(report.condition_statuses)
    assert status_map.get(
        ProtoSpeechCondition.REFUSAL_HELD
    ) is ProtoSpeechStatus.PASS

    ref_turns = [
        t
        for t in report.turns
        if t.condition is ProtoSpeechCondition.REFUSAL_HELD
    ]
    assert len(ref_turns) == 1
    t = ref_turns[0]
    assert t.refusal_taken
    assert t.selected_utterance.token_count == 0
    assert len(t.evidence_records_added) == 0
    assert any(
        f.drive_kind is ProtoSpeechDriveKind.REFUSAL_GUARD
        for f in t.drive_stream.frames
    )
