"""Fixtures for proto-content promotion through the tick boundary."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

from brain.development.history import SubstrateHistory
from brain.development.probes import ProbePolicyState, focus_contact
from brain.development.promotion import can_promote_proto_content, promote_proto_content
from brain.development.proto_content import (
    ProtoContent,
    PromotionProvenance,
    maybe_stabilize_proto_content,
)
from brain.development.proto_pattern import update_proto_pattern
from brain.invariants import register
from brain.io_types import PerceptEvent
from brain.llm.client import MockClient
from brain.tick import initial_state, tick
from brain.tlica.profile import COGITO_ID


def _stable_proto_content() -> ProtoContent:
    policy = ProbePolicyState.with_full_focus()
    history = SubstrateHistory()
    pattern_history = SubstrateHistory()

    policy, history, first_use, _ = focus_contact(
        policy,
        history,
        probe_id="probe:promotion-1",
        target_channel="glow",
        echo_value=Fraction(3, 5),
        budget_cost=Fraction(1, 5),
    )
    pattern_history, first_pattern = update_proto_pattern(
        pattern_history,
        first_use.result_frame,
    )
    assert first_pattern is None

    policy, history, second_use, _ = focus_contact(
        policy,
        history,
        probe_id="probe:promotion-2",
        target_channel="glow",
        echo_value=Fraction(3, 5),
        budget_cost=Fraction(1, 5),
    )
    pattern_history, pattern = update_proto_pattern(
        pattern_history,
        second_use.result_frame,
    )
    assert pattern is not None

    pattern_history, content = maybe_stabilize_proto_content(
        pattern_history,
        pattern,
        salience=Fraction(4, 5),
        trace_event_ids=(first_use.probe_id, second_use.probe_id),
    )
    assert content is not None
    assert content.content_id in pattern_history.proto_contents
    return content


@register("I-DEV-05", status="REQUIRED")
def check_proto_content_promotes_only_as_percept_event_through_tick() -> None:
    content = _stable_proto_content()
    event = promote_proto_content(content)
    assert isinstance(event, PerceptEvent)
    assert event.content_id == content.content_id
    assert event.initial_rho == content.stability
    assert can_promote_proto_content(content)

    state = initial_state()
    before_profile = state.profile
    before_msi = state.msi
    before_ptcns = state.ptcns
    before_registry = state.registry

    # Promotion construction is boundary-only: it has not changed runtime state.
    assert state.profile is before_profile
    assert state.msi is before_msi
    assert state.ptcns is before_ptcns
    assert state.registry is before_registry
    assert event.content_id not in state.profile.domain

    new_state, record = tick(state, [event], MockClient(["PRESERVE"]))
    assert event.content_id in new_state.profile.domain
    assert event.content_id in record.profile_values
    assert event.content_id in new_state.registry.texts
    assert event.content_id in new_state.msi.contents
    assert state.profile is before_profile
    assert state.msi is before_msi
    assert state.ptcns is before_ptcns
    assert state.registry is before_registry


@register("I-DEV-06", status="REQUIRED")
def check_developmental_content_cannot_produce_cogito_id() -> None:
    content = _stable_proto_content()
    bad = replace(
        content,
        content_id=COGITO_ID,
        provenance=PromotionProvenance(
            pattern_id=content.pattern_id,
            source_kinds=content.provenance.source_kinds,
            trace_event_ids=content.provenance.trace_event_ids,
        ),
    )
    try:
        promote_proto_content(bad)
    except ValueError as exc:
        assert "I-DEV-06" in str(exc)
    else:
        raise AssertionError("I-DEV-06 violated: COGITO_ID promotion was accepted")
