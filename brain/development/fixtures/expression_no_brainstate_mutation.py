"""Fixture for I-EXP-07: expression ops do not mutate BrainState / MSI / PtCns / registry."""
from __future__ import annotations

from brain.development.expression import (
    ExpressionHistory,
    ExpressionItem,
    ExpressionSource,
    extract_features,
    make_expression_record,
    predict_readability,
)
from brain.invariants import register
from brain.tick import initial_state


def _item() -> ExpressionItem:
    return ExpressionItem(
        item_id="exp:nb-1",
        text="alpha beta gamma delta",
        source=ExpressionSource.WORLDLET_HISTORY,
    )


@register("I-EXP-07", status="REQUIRED")
def check_expression_does_not_mutate_brainstate() -> None:
    state = initial_state()
    before_profile = state.profile
    before_msi = state.msi
    before_ptcns = state.ptcns
    before_registry = state.registry
    before_profile_values = dict(state.profile.values)
    before_msi_contents = frozenset(state.msi.contents)
    before_ptcns_pos = frozenset(state.ptcns.positive_contents)
    before_registry_texts = dict(state.registry.texts)

    item = _item()
    features = extract_features(item)
    prediction = predict_readability(item)
    record = make_expression_record(item)
    history = ExpressionHistory().append(record)
    assert history.records == (record,)
    assert features.token_count == 4
    assert prediction.score.value >= 0

    assert state.profile is before_profile
    assert state.msi is before_msi
    assert state.ptcns is before_ptcns
    assert state.registry is before_registry
    assert dict(state.profile.values) == before_profile_values
    assert frozenset(state.msi.contents) == before_msi_contents
    assert frozenset(state.ptcns.positive_contents) == before_ptcns_pos
    assert dict(state.registry.texts) == before_registry_texts
    assert item.item_id not in state.profile.domain
    assert item.item_id not in state.registry.texts
