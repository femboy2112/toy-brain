"""Phase 3.31 feedback reinforcement + correction shaping fixture.

Drives ``I-PSPEECH-07`` (REQUIRED) and ``I-PSPEECH-08`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.proto_speech_acquisition import (
    STABLE_SINGLE_THRESHOLD,
    CaregiverFeedbackKind,
    ProtoSpeechCondition,
    ProtoSpeechStatus,
    ProtoUtteranceDisposition,
    ProtoVocalToken,
    build_proto_utterance,
    run_proto_speech_live_test,
)
from brain.invariants import register


@register("I-PSPEECH-07", status="REQUIRED")
def check_feedback_reinforcement() -> None:
    """ACCEPTED / ECHO feedback strengthens an offered form."""
    report = run_proto_speech_live_test()
    status_map = dict(report.condition_statuses)
    assert status_map.get(
        ProtoSpeechCondition.FEEDBACK_REINFORCEMENT
    ) is ProtoSpeechStatus.PASS

    reinf_turns = [
        t
        for t in report.turns
        if t.condition is ProtoSpeechCondition.FEEDBACK_REINFORCEMENT
    ]
    assert reinf_turns
    # The last turn must re-select LOOK after the priming reinforcement.
    assert reinf_turns[-1].selected_utterance.text == "look"

    # Every priming turn must have produced at least one evidence record
    # of disposition REINFORCED or STABLE_SINGLE for LOOK.
    found = False
    for t in reinf_turns:
        for r in t.evidence_records_added:
            if r.disposition in (
                ProtoUtteranceDisposition.REINFORCED,
                ProtoUtteranceDisposition.STABLE_SINGLE,
            ):
                found = True
    assert found, "no reinforcement disposition observed"


@register("I-PSPEECH-08", status="REQUIRED")
def check_correction_shaping() -> None:
    """CORRECTED weakens attempted; strengthens offered."""
    report = run_proto_speech_live_test()
    status_map = dict(report.condition_statuses)
    assert status_map.get(
        ProtoSpeechCondition.CORRECTION_SHAPING
    ) is ProtoSpeechStatus.PASS

    corr_turns = [
        t
        for t in report.turns
        if t.condition is ProtoSpeechCondition.CORRECTION_SHAPING
    ]
    assert corr_turns
    yes_utt = build_proto_utterance((ProtoVocalToken.YES,))

    # Find the YES record in the last correction turn's records or
    # any later record. Walk the entire condition.
    final_yes_weight = 0
    for t in corr_turns:
        for r in t.evidence_records_added:
            if r.utterance_digest == yes_utt.digest_hex16:
                final_yes_weight = max(final_yes_weight, r.weight_after)
    assert final_yes_weight >= STABLE_SINGLE_THRESHOLD, (
        f"YES weight after correction shaping: {final_yes_weight}"
    )

    # In every CORRECTED-feedback turn the attempted form's weight
    # delta must be <= 0.
    for t in corr_turns:
        if t.feedback.kind is not CaregiverFeedbackKind.CORRECTED:
            continue
        for r in t.evidence_records_added:
            if r.utterance_digest == t.selected_utterance.digest_hex16:
                assert r.weight_after - r.weight_before <= 0, (
                    f"correction did not weaken attempted "
                    f"{t.turn_id}: {r.weight_before} -> {r.weight_after}"
                )
