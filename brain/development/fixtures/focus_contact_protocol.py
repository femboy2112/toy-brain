"""Fixtures for the focus-contact probe protocol."""
from __future__ import annotations

from fractions import Fraction

from brain.development.history import SubstrateHistory
from brain.development.probes import FOCUS_CONTACT, ProbePolicyState, ProbeUse, focus_contact
from brain.development.stream import FrameSourceKind
from brain.invariants import register


@register("I-DEV-04", status="REQUIRED")
def check_focus_contact_records_use_budget_and_no_promotion() -> None:
    policy = ProbePolicyState.with_full_focus()
    history = SubstrateHistory()

    next_policy, next_history, use, promoted_event = focus_contact(
        policy,
        history,
        probe_id="probe:focus-1",
        target_channel="edge",
        echo_value=Fraction(2, 3),
        budget_cost=Fraction(1, 4),
    )

    assert isinstance(use, ProbeUse)
    assert use.kind is FOCUS_CONTACT
    assert next_policy.focus_budget == Fraction(3, 4)
    assert next_policy.uses == (use,)
    assert len(next_history.frames) == 1
    assert next_history.frames[0].sources["edge"].kind is FrameSourceKind.PROBE_ECHO
    assert promoted_event is None
    assert next_history.proto_contents == {}
