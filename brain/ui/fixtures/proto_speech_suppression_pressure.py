"""Phase 3.31 suppression + suppression-pressure fixture.

Drives ``I-PSPEECH-09`` (REQUIRED) and ``I-PSPEECH-17`` (REQUIRED).
"""
from __future__ import annotations

from brain.development.proto_speech_acquisition import (
    SUPPRESS_THRESHOLD,
    ProtoSpeechCondition,
    ProtoSpeechStatus,
    ProtoUtteranceDisposition,
    ProtoVocalToken,
    build_proto_utterance,
    run_proto_speech_live_test,
)
from brain.invariants import register


@register("I-PSPEECH-09", status="REQUIRED")
def check_suppression_threshold() -> None:
    """Repeated IGNORED feedback suppresses a form past the threshold."""
    report = run_proto_speech_live_test()
    status_map = dict(report.condition_statuses)
    assert status_map.get(ProtoSpeechCondition.SUPPRESSION) is (
        ProtoSpeechStatus.PASS
    )

    sup_turns = [
        t
        for t in report.turns
        if t.condition is ProtoSpeechCondition.SUPPRESSION
    ]
    assert sup_turns
    na_utt = build_proto_utterance((ProtoVocalToken.NA,))

    # Inspect every NA record across the condition; the most recent
    # one must be SUPPRESSED with weight <= -3.
    final_record = None
    for t in sup_turns:
        for r in t.evidence_records_added:
            if r.utterance_digest == na_utt.digest_hex16:
                final_record = r
    assert final_record is not None, "no NA evidence record observed"
    assert final_record.weight_after <= SUPPRESS_THRESHOLD, (
        f"NA weight: {final_record.weight_after}"
    )
    assert final_record.disposition is ProtoUtteranceDisposition.SUPPRESSED


@register("I-PSPEECH-17", status="REQUIRED")
def check_suppression_pressure_blocks() -> None:
    """SUPPRESSION_PRESSURE filters a suppressed form from later turns."""
    report = run_proto_speech_live_test()
    sup_turns = [
        t
        for t in report.turns
        if t.condition is ProtoSpeechCondition.SUPPRESSION
    ]
    assert sup_turns
    # The final suppression turn must NOT emit NA, even though NA was
    # the historical ambient-primed form. The suppression record had
    # decremented its weight past SUPPRESS_THRESHOLD.
    last = sup_turns[-1]
    assert last.selected_utterance.text != "na", (
        f"suppressed form still emitted: {last.turn_id}"
    )
