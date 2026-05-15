"""Fixtures for Phase 3.3 worldlet state/history rows."""
from __future__ import annotations

from dataclasses import fields
from fractions import Fraction

from brain.development.stream import FrameSourceKind
from brain.development.worldlet import (
    WorldletAttempt,
    WorldletHistory,
    WorldletObject,
    WorldletProvenance,
    WorldletResponse,
    WorldletState,
    WorldletValence,
    append_worldlet_attempt,
    append_worldlet_response,
)
from brain.invariants import register
from brain.tlica.profile import COGITO_ID


def _provenance() -> WorldletProvenance:
    return WorldletProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(4, 5),
        trace_event_ids=("worldlet:state-trace",),
    )


def _state() -> WorldletState:
    target = WorldletObject(
        object_id="wld:target-1",
        label="target",
        available=True,
        accepted_token_ids=("out-token:alpha",),
    )
    return WorldletState(
        state_id="wld:state-1",
        objects={target.object_id: target},
        step_index=0,
    )


def _attempt() -> WorldletAttempt:
    return WorldletAttempt(
        attempt_id="wld:attempt-1",
        token_id="out-token:alpha",
        pattern_id="out-pattern:alpha",
        target_id="wld:target-1",
        provenance=_provenance(),
    )


def _response() -> WorldletResponse:
    return WorldletResponse(
        response_id="wld:response-1",
        attempt_id="wld:attempt-1",
        accepted=True,
        reason="accepted",
        valence=WorldletValence(Fraction(1, 2)),
        provenance=_provenance(),
    )


@register("I-WLD-01", status="STRUCTURAL")
def check_worldlet_state_and_object_are_finite_deterministic_records() -> None:
    state = _state()
    target = state.objects["wld:target-1"]

    assert isinstance(target.accepted_token_ids, frozenset)
    assert target.available is True
    assert state.object_for_target("wld:target-1") is target
    assert state.object_for_target("wld:target-1") is target
    assert state.object_for_target("wld:missing") is None
    assert state.object_for_target(None) is None

    try:
        WorldletObject(
            object_id=COGITO_ID,
            label="target",
            available=True,
            accepted_token_ids=("out-token:alpha",),
        )
    except ValueError as exc:
        assert "I-WLD-01" in str(exc)
    else:
        raise AssertionError("I-WLD-01 violated: reserved object ID passed")

    try:
        WorldletState(
            state_id="wld:bad-key",
            objects={"wld:other": target},
            step_index=0,
        )
    except ValueError as exc:
        assert "I-WLD-01" in str(exc)
    else:
        raise AssertionError("I-WLD-01 violated: object key drift passed")

    try:
        WorldletState(
            state_id="wld:bad-step",
            objects={},
            step_index=-1,
        )
    except ValueError as exc:
        assert "I-WLD-01" in str(exc)
    else:
        raise AssertionError("I-WLD-01 violated: negative step passed")


@register("I-WLD-04", status="REQUIRED")
def check_worldlet_history_appends_copy_on_write() -> None:
    state = _state()
    history = WorldletHistory(latest_state=state)
    attempt = _attempt()
    response = _response()
    next_state = WorldletState(
        state_id="wld:state-2",
        objects=state.objects,
        step_index=state.step_index + 1,
    )

    with_attempt = append_worldlet_attempt(history, attempt)
    assert with_attempt is not history
    assert history.attempts == ()
    assert history.responses == ()
    assert with_attempt.attempts == (attempt,)
    assert with_attempt.responses == ()
    assert with_attempt.latest_state is state

    with_response = append_worldlet_response(
        with_attempt,
        response,
        latest_state=next_state,
    )
    assert with_response is not with_attempt
    assert with_attempt.responses == ()
    assert with_response.attempts == with_attempt.attempts
    assert with_response.responses == (response,)
    assert with_response.latest_state is next_state
    assert history.latest_state is state

    forbidden_state_fields = {"profile", "msi", "ptcns", "registry", "tick"}
    for obj in (history, with_attempt, with_response):
        names = {field.name for field in fields(obj)}
        assert not (names & forbidden_state_fields), (
            f"I-WLD-04 violated: WorldletHistory exposes {names & forbidden_state_fields}"
        )
