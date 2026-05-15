"""Observed focus-contact stabilization/dissolution fixture."""
from __future__ import annotations

from fractions import Fraction

from brain.development.history import SubstrateHistory
from brain.development.probes import ProbePolicyState, focus_contact
from brain.development.proto_pattern import ProtoPattern, update_proto_pattern
from brain.invariants import register


@register("I-DEV-07", status="OBSERVED")
def observe_focus_contact_stabilizes_or_remains_unpromoted() -> None:
    policy = ProbePolicyState.with_full_focus()
    history = SubstrateHistory()
    pattern_history = SubstrateHistory()

    policy, history, first_use, first_event = focus_contact(
        policy,
        history,
        probe_id="probe:focus-observed-1",
        target_channel="glow",
        echo_value=Fraction(1, 2),
        budget_cost=Fraction(1, 5),
    )
    pattern_history, first_pattern = update_proto_pattern(
        pattern_history,
        first_use.result_frame,
    )
    assert first_event is None
    assert first_pattern is None
    assert history.proto_contents == {}

    policy, history, second_use, second_event = focus_contact(
        policy,
        history,
        probe_id="probe:focus-observed-2",
        target_channel="glow",
        echo_value=Fraction(1, 2),
        budget_cost=Fraction(1, 5),
    )
    pattern_history, recurring_pattern = update_proto_pattern(
        pattern_history,
        second_use.result_frame,
    )
    assert second_event is None
    assert isinstance(recurring_pattern, ProtoPattern)
    assert recurring_pattern.support_count >= 2
    assert history.proto_contents == {}
