"""Fixture for I-EXP-08: expression ops do not mutate source histories."""
from __future__ import annotations

from fractions import Fraction

from brain.development.expression import (
    ExpressionHistory,
    expression_record_from_output_entry,
    expression_record_from_proto_basic_line,
    expression_record_from_transcript_entry,
    expression_record_from_worldlet_response,
)
from brain.development.output import (
    OutputHistory,
    OutputImpulse,
    OutputProvenance,
    append_output_impulse,
)
from brain.development.repl import tokenize
from brain.development.stream import FrameSourceKind
from brain.development.worldlet import (
    WorldletProvenance,
    WorldletResponse,
    WorldletValence,
)
from brain.invariants import register
from brain.ui.transcript import OperatorTranscript, TranscriptEntry, TranscriptKind


def _output_history() -> tuple[OutputHistory, OutputImpulse]:
    provenance = OutputProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(3, 5),
        trace_event_ids=("trace:out-1",),
    )
    impulse = OutputImpulse(
        impulse_id="out:imp-1",
        text="hello",
        provenance=provenance,
    )
    history = append_output_impulse(OutputHistory(), impulse)
    return history, impulse


def _worldlet_response() -> WorldletResponse:
    provenance = WorldletProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(4, 5),
        trace_event_ids=("trace:wld-1",),
    )
    return WorldletResponse(
        response_id="wld:resp-1",
        attempt_id="wld:att-1",
        accepted=True,
        reason="accepted alpha",
        valence=WorldletValence(Fraction(1, 2)),
        provenance=provenance,
    )


def _transcript() -> tuple[OperatorTranscript, TranscriptEntry]:
    transcript = OperatorTranscript.empty().append(
        kind=TranscriptKind.SUBMIT,
        tick_at_event=3,
        text="hello operator",
    )
    entry = transcript.entries[-1]
    return transcript, entry


@register("I-EXP-08", status="REQUIRED")
def check_expression_does_not_mutate_source_histories() -> None:
    # --- OutputHistory ---
    out_hist, impulse = _output_history()
    out_hist_id = id(out_hist)
    out_impulses_before = out_hist.impulses
    rec_out = expression_record_from_output_entry(impulse)
    assert rec_out.item.text == "hello"
    assert id(out_hist) == out_hist_id
    assert out_hist.impulses is out_impulses_before
    assert out_hist.impulses == (impulse,)

    # --- WorldletResponse ---
    response = _worldlet_response()
    resp_repr_before = (
        response.response_id,
        response.attempt_id,
        response.accepted,
        response.reason,
        response.valence.value,
    )
    rec_wld = expression_record_from_worldlet_response(response)
    assert rec_wld.item.text == "accepted alpha"
    resp_repr_after = (
        response.response_id,
        response.attempt_id,
        response.accepted,
        response.reason,
        response.valence.value,
    )
    assert resp_repr_before == resp_repr_after

    # --- ProtoBasicLine ---
    line = tokenize("PRINT X", line_id="repl:line-1")
    line_repr_before = (line.line_id, line.raw_text, tuple(line.tokens))
    rec_repl = expression_record_from_proto_basic_line(line)
    assert rec_repl.item.text == "PRINT X"
    line_repr_after = (line.line_id, line.raw_text, tuple(line.tokens))
    assert line_repr_before == line_repr_after

    # --- OperatorTranscript ---
    transcript, entry = _transcript()
    transcript_entries_before = transcript.entries
    rec_tx = expression_record_from_transcript_entry(entry)
    assert rec_tx.item.text == "hello operator"
    assert transcript.entries is transcript_entries_before
    assert transcript.entries == (entry,)

    # Building an ExpressionHistory does not mutate source containers either.
    history = (
        ExpressionHistory()
        .append(rec_out)
        .append(rec_wld)
        .append(rec_repl)
        .append(rec_tx)
    )
    assert len(history.records) == 4
    assert out_hist.impulses == (impulse,)
    assert transcript.entries == (entry,)
