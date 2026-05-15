"""Fixture for I-REF-06: reflective ops do not mutate BrainState / MSI / PtCns / registry."""
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
    make_reflective_snapshot,
    make_reflective_summary,
)
from brain.development.stream import FrameSourceKind
from brain.invariants import register
from brain.tick import initial_state


def _output_history() -> OutputHistory:
    provenance = OutputProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(2, 5),
        trace_event_ids=("trace:nb-1",),
    )
    impulse = OutputImpulse(
        impulse_id="out:nb-1",
        text="hello world",
        provenance=provenance,
    )
    return append_output_impulse(OutputHistory(), impulse)


def _expression_history() -> ExpressionHistory:
    item = ExpressionItem(
        item_id="exp:nb-1",
        text="alpha beta gamma",
        source=ExpressionSource.OPERATOR_TRANSCRIPT,
    )
    return ExpressionHistory().append(make_expression_record(item))


@register("I-REF-06", status="REQUIRED")
def check_reflective_does_not_mutate_brainstate() -> None:
    state = initial_state()
    before_profile = state.profile
    before_msi = state.msi
    before_ptcns = state.ptcns
    before_registry = state.registry
    before_profile_values = dict(state.profile.values)
    before_msi_contents = frozenset(state.msi.contents)
    before_ptcns_pos = frozenset(state.ptcns.positive_contents)
    before_registry_texts = dict(state.registry.texts)

    snap = make_reflective_snapshot(
        snapshot_id="snap:nb",
        output_history=_output_history(),
        expression_history=_expression_history(),
    )
    summary = make_reflective_summary(snap)

    assert summary.item_count == 2
    assert summary.total_entry_count == 2

    assert state.profile is before_profile
    assert state.msi is before_msi
    assert state.ptcns is before_ptcns
    assert state.registry is before_registry
    assert dict(state.profile.values) == before_profile_values
    assert frozenset(state.msi.contents) == before_msi_contents
    assert frozenset(state.ptcns.positive_contents) == before_ptcns_pos
    assert dict(state.registry.texts) == before_registry_texts
    assert "out:nb-1" not in state.profile.domain
    assert "exp:nb-1" not in state.registry.texts
