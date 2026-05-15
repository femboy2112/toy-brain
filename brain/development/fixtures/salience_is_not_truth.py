"""Fixtures for salience/probe boundary discipline."""
from __future__ import annotations

from fractions import Fraction

from brain.development.history import SubstrateHistory
from brain.development.probes import (
    ProbePolicyState,
    focus_contact,
    probe_output_is_knowledge,
    probe_output_promotes_by_itself,
)
from brain.development.proto_content import maybe_stabilize_proto_content
from brain.invariants import register


@register("I-DEV-03", status="REQUIRED")
def check_salience_alone_does_not_promote() -> None:
    history = SubstrateHistory()
    history, content = maybe_stabilize_proto_content(
        history,
        None,
        salience=Fraction(1),
    )

    assert content is None
    assert history.proto_contents == {}


@register("I-SBX-01", status="STRUCTURAL")
def check_probe_output_is_not_knowledge_by_itself() -> None:
    policy = ProbePolicyState.with_full_focus()
    history = SubstrateHistory()
    policy, history, use, promoted_event = focus_contact(
        policy,
        history,
        probe_id="probe:salience-boundary",
        target_channel="tone",
        echo_value=Fraction(4, 5),
    )

    assert promoted_event is None
    assert policy.uses == (use,)
    assert len(history.frames) == 1
    assert not probe_output_is_knowledge(use)
    assert not probe_output_promotes_by_itself(use)
    assert history.proto_contents == {}


@register("I-SBX-02", status="REQUIRED")
def check_salience_cannot_bypass_stability_or_prediction_gain() -> None:
    policy = ProbePolicyState.with_full_focus()
    history = SubstrateHistory()
    _, history, _, _ = focus_contact(
        policy,
        history,
        probe_id="probe:high-salience",
        target_channel="flash",
        echo_value=Fraction(1),
    )
    history, content = maybe_stabilize_proto_content(
        history,
        None,
        salience=Fraction(1),
    )

    assert content is None
    assert history.proto_contents == {}
