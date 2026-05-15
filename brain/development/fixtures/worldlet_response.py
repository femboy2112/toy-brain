"""Fixtures for Phase 3.3 worldlet valence/response rows."""
from __future__ import annotations

from dataclasses import fields
from fractions import Fraction

from brain.development.stream import FrameSourceKind
from brain.development.worldlet import (
    WorldletAttempt,
    WorldletHistory,
    WorldletProvenance,
    WorldletResponse,
    WorldletState,
    WorldletValence,
    append_worldlet_response,
)
from brain.invariants import register
from brain.tick import initial_state


def _provenance(
    kind: FrameSourceKind = FrameSourceKind.GENERATED,
    confidence: Fraction = Fraction(4, 5),
) -> WorldletProvenance:
    return WorldletProvenance(
        source_kind=kind,
        confidence=confidence,
        trace_event_ids=("worldlet:response-trace",),
    )


def _attempt() -> WorldletAttempt:
    return WorldletAttempt(
        attempt_id="wld:attempt-1",
        token_id="out-token:alpha",
        pattern_id="out-pattern:alpha",
        target_id=None,
        provenance=_provenance(),
    )


def _response() -> WorldletResponse:
    return WorldletResponse(
        response_id="wld:response-1",
        attempt_id=_attempt().attempt_id,
        accepted=True,
        reason="accepted",
        valence=WorldletValence(Fraction(1, 2)),
        provenance=_provenance(),
    )


def _assert_i_wld_02_rejects(call: object) -> None:
    try:
        assert callable(call)
        call()
    except ValueError as exc:
        assert "I-WLD-02" in str(exc)
    else:
        raise AssertionError("I-WLD-02 violated: invalid valence passed")


def _assert_i_wld_03_rejects(call: object) -> None:
    try:
        assert callable(call)
        call()
    except ValueError as exc:
        assert "I-WLD-03" in str(exc)
    else:
        raise AssertionError("I-WLD-03 violated: invalid provenance passed")


@register("I-WLD-02", status="REQUIRED")
def check_worldlet_valence_is_exact_and_bounded() -> None:
    negative = WorldletValence(Fraction(-1))
    neutral = WorldletValence(Fraction(0))
    positive = WorldletValence(Fraction(1))

    for valence in (negative, neutral, positive):
        assert isinstance(valence.value, Fraction)
        assert Fraction(-1) <= valence.value <= Fraction(1)

    _assert_i_wld_02_rejects(lambda: WorldletValence(Fraction(-2, 1)))
    _assert_i_wld_02_rejects(lambda: WorldletValence(Fraction(3, 2)))
    _assert_i_wld_02_rejects(lambda: WorldletValence(0.5))  # type: ignore[arg-type]


@register("I-WLD-03", status="STRUCTURAL")
def check_worldlet_provenance_reuses_source_discipline() -> None:
    provenance = _provenance(FrameSourceKind.PROBE_ECHO, Fraction(1, 2))
    assert isinstance(provenance.source_kind, FrameSourceKind)
    assert isinstance(provenance.confidence, Fraction)
    assert provenance.confidence == Fraction(1, 2)
    assert "WORLDLET" not in {kind.name for kind in FrameSourceKind}

    _assert_i_wld_03_rejects(
        lambda: WorldletProvenance(
            source_kind=FrameSourceKind.GENERATED,
            confidence=Fraction(4, 3),
        )
    )
    _assert_i_wld_03_rejects(
        lambda: WorldletProvenance(
            source_kind=FrameSourceKind.GENERATED,
            confidence=0.5,  # type: ignore[arg-type]
        )
    )


@register("I-WLD-05", status="STRUCTURAL")
def check_worldlet_response_is_source_tagged_local_record() -> None:
    response = _response()
    assert response.response_id == "wld:response-1"
    assert response.attempt_id == "wld:attempt-1"
    assert response.accepted is True
    assert response.reason == "accepted"
    assert response.valence.value == Fraction(1, 2)
    assert isinstance(response.provenance.source_kind, FrameSourceKind)

    forbidden = {
        "percept_event",
        "PerceptEvent",
        "callback",
        "runtime_callback",
        "tick",
        "state_mutation",
    }
    names = {field.name for field in fields(response)}
    assert not (names & {name.lower() for name in forbidden}), (
        f"I-WLD-05 violated: WorldletResponse exposes {names & forbidden}"
    )
    for name in forbidden:
        assert not hasattr(response, name), (
            f"I-WLD-05 violated: WorldletResponse exposes {name}"
        )


@register("I-WLD-06", status="REQUIRED")
def check_worldlet_response_history_does_not_mutate_tlica_runtime() -> None:
    state = initial_state()
    before_profile = state.profile
    before_msi = state.msi
    before_ptcns = state.ptcns
    before_registry = state.registry

    worldlet_state = WorldletState(state_id="wld:state-1")
    history = WorldletHistory(latest_state=worldlet_state)
    response = _response()
    next_worldlet_state = WorldletState(
        state_id="wld:state-2",
        objects=worldlet_state.objects,
        step_index=worldlet_state.step_index + 1,
    )
    next_history = append_worldlet_response(
        history,
        response,
        latest_state=next_worldlet_state,
    )

    assert next_history.responses == (response,)
    assert next_history.latest_state is next_worldlet_state
    assert state.profile is before_profile
    assert state.msi is before_msi
    assert state.ptcns is before_ptcns
    assert state.registry is before_registry
    assert response.response_id not in state.profile.domain
    assert response.response_id not in state.registry.texts
