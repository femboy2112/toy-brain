"""Phase 3.31 two-token combination + drive-stream pressure fixture.

Drives ``I-PSPEECH-11`` (REQUIRED) and ``I-PSPEECH-16`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.proto_speech_acquisition import (
    ProtoSpeechCondition,
    ProtoSpeechDriveKind,
    ProtoSpeechStatus,
    ProtoUtteranceDisposition,
    run_proto_speech_live_test,
)
from brain.invariants import register


@register("I-PSPEECH-11", status="REQUIRED")
def check_two_token_combination_emerges() -> None:
    """Two-token combination only after stable single prerequisites."""
    report = run_proto_speech_live_test()
    status_map = dict(report.condition_statuses)
    assert status_map.get(
        ProtoSpeechCondition.TWO_TOKEN_COMBINATION
    ) is ProtoSpeechStatus.PASS

    comb_turns = [
        t
        for t in report.turns
        if t.condition is ProtoSpeechCondition.TWO_TOKEN_COMBINATION
    ]
    assert comb_turns
    # No earlier turn produced a 2-token utterance.
    for t in comb_turns[:-1]:
        assert t.selected_utterance.token_count != 2, (
            f"early 2-token emission: {t.turn_id}"
        )
    # The final turn produced a 2-token utterance.
    last = comb_turns[-1]
    assert last.selected_utterance.token_count == 2
    # The final turn's drive stream contains a COMBINATION_PRESSURE
    # frame.
    kinds = {f.drive_kind for f in last.drive_stream.frames}
    assert ProtoSpeechDriveKind.COMBINATION_PRESSURE in kinds


@register("I-PSPEECH-16", status="REQUIRED")
def check_drive_pressures_distinct() -> None:
    """Distinct drive kinds are exercised across the v1 battery."""
    report = run_proto_speech_live_test()
    seen_kinds: set[ProtoSpeechDriveKind] = set()
    for t in report.turns:
        for f in t.drive_stream.frames:
            seen_kinds.add(f.drive_kind)
    expected = {
        ProtoSpeechDriveKind.LOW_EVIDENCE,
        ProtoSpeechDriveKind.CAREGIVER_AMBIENT_PRIME,
        ProtoSpeechDriveKind.CAREGIVER_FEEDBACK_PRIME,
        ProtoSpeechDriveKind.RECURRENCE_PRESSURE,
        ProtoSpeechDriveKind.NOVELTY_PRESSURE,
        ProtoSpeechDriveKind.UNRESOLVED_HYPOTHESIS,
        ProtoSpeechDriveKind.SUPPRESSION_PRESSURE,
        ProtoSpeechDriveKind.COMBINATION_PRESSURE,
        ProtoSpeechDriveKind.REFUSAL_GUARD,
        ProtoSpeechDriveKind.TRANSFER_PRESSURE,
    }
    missing = expected - seen_kinds
    assert not missing, f"missing drive kinds: {missing}"

    # Silence linter import.
    _ = ProtoUtteranceDisposition
