"""Fixture for I-REF-07: reflective ops do not mutate source histories."""
from __future__ import annotations

from fractions import Fraction

from brain.development.expression import (
    ExpressionHistory,
    ExpressionItem,
    ExpressionSource,
    make_expression_record,
)
from brain.development.output import (
    OutputHistory,
    OutputImpulse,
    OutputProvenance,
    append_output_impulse,
)
from brain.development.reflective import (
    make_reflective_item_from_expression_history,
    make_reflective_item_from_operator_transcript,
    make_reflective_item_from_output_history,
    make_reflective_item_from_proto_basic_history,
    make_reflective_item_from_worldlet_history,
    make_reflective_snapshot,
    make_reflective_summary,
)
from brain.development.repl import ProtoBasicHistory
from brain.development.stream import FrameSourceKind
from brain.development.worldlet import (
    WorldletHistory,
    WorldletObject,
    WorldletProvenance,
    WorldletResponse,
    WorldletState,
    WorldletValence,
)
from brain.invariants import register
from brain.ui.transcript import OperatorTranscript, TranscriptKind


def _output_history() -> OutputHistory:
    provenance = OutputProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(2, 5),
        trace_event_ids=("trace:o-1",),
    )
    impulse = OutputImpulse(
        impulse_id="out:o-1",
        text="hi",
        provenance=provenance,
    )
    return append_output_impulse(OutputHistory(), impulse)


def _worldlet_history() -> WorldletHistory:
    obj = WorldletObject(
        object_id="wld:obj-1",
        label="alpha",
        available=True,
    )
    state = WorldletState(
        state_id="wld:s-1",
        objects={"wld:obj-1": obj},
    )
    provenance = WorldletProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(3, 5),
        trace_event_ids=("trace:w-1",),
    )
    response = WorldletResponse(
        response_id="wld:resp-1",
        attempt_id="wld:att-1",
        accepted=True,
        reason="accepted",
        valence=WorldletValence(Fraction(1, 2)),
        provenance=provenance,
    )
    return WorldletHistory(latest_state=state, attempts=(), responses=(response,))


def _proto_basic_history() -> ProtoBasicHistory:
    return ProtoBasicHistory()


def _expression_history() -> ExpressionHistory:
    item = ExpressionItem(
        item_id="exp:e-1",
        text="alpha beta gamma",
        source=ExpressionSource.OUTPUT_HISTORY,
    )
    return ExpressionHistory().append(make_expression_record(item))


def _operator_transcript() -> OperatorTranscript:
    transcript = OperatorTranscript.empty()
    transcript = transcript.append(
        kind=TranscriptKind.SUBMIT, tick_at_event=0, text="hello"
    )
    return transcript


@register("I-REF-07", status="REQUIRED")
def check_reflective_does_not_mutate_source_histories() -> None:
    output_hist = _output_history()
    worldlet_hist = _worldlet_history()
    proto_hist = _proto_basic_history()
    expr_hist = _expression_history()
    transcript = _operator_transcript()

    out_id = id(output_hist)
    out_impulses_before = output_hist.impulses
    wld_id = id(worldlet_hist)
    wld_responses_before = worldlet_hist.responses
    proto_id = id(proto_hist)
    proto_parses_before = proto_hist.parse_results
    expr_id = id(expr_hist)
    expr_records_before = expr_hist.records
    transcript_id = id(transcript)
    transcript_entries_before = transcript.entries

    item_out = make_reflective_item_from_output_history(output_hist)
    item_wld = make_reflective_item_from_worldlet_history(worldlet_hist)
    item_proto = make_reflective_item_from_proto_basic_history(proto_hist)
    item_expr = make_reflective_item_from_expression_history(expr_hist)
    item_tx = make_reflective_item_from_operator_transcript(transcript)
    snap = make_reflective_snapshot(
        snapshot_id="snap:nshm",
        output_history=output_hist,
        worldlet_history=worldlet_hist,
        proto_basic_history=proto_hist,
        expression_history=expr_hist,
        operator_transcript=transcript,
    )
    summary = make_reflective_summary(snap)

    assert item_out.entry_count == 1
    assert item_wld.entry_count == 1
    assert item_proto.entry_count == 0
    assert item_expr.entry_count == 1
    assert item_tx.entry_count == 1
    assert summary.item_count == 5

    assert id(output_hist) == out_id
    assert output_hist.impulses is out_impulses_before
    assert output_hist.impulses == out_impulses_before
    assert id(worldlet_hist) == wld_id
    assert worldlet_hist.responses is wld_responses_before
    assert worldlet_hist.responses == wld_responses_before
    assert id(proto_hist) == proto_id
    assert proto_hist.parse_results is proto_parses_before
    assert id(expr_hist) == expr_id
    assert expr_hist.records is expr_records_before
    assert id(transcript) == transcript_id
    assert transcript.entries is transcript_entries_before
