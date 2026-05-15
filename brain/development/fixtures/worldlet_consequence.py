"""Fixtures for Phase 3.3 worldlet consequence rows."""
from __future__ import annotations

from fractions import Fraction

from brain.development.output import (
    LearnedOutputToken,
    OutputHistory,
    OutputImpulse,
    OutputPattern,
    OutputProvenance,
    OutputTokenCandidate,
    ProtoOutputActionReadiness,
    echo_output_impulse,
    learn_output_token,
    maybe_create_output_token_candidate,
    observe_proto_output_action_readiness,
    update_output_pattern,
)
from brain.development.stream import FrameSourceKind
from brain.development.worldlet import (
    WorldletAttempt,
    WorldletHistory,
    WorldletObject,
    WorldletProvenance,
    WorldletResponse,
    WorldletState,
    construct_worldlet_attempt,
    respond_worldlet,
)
from brain.invariants import register
from brain.tick import initial_state


def _output_provenance() -> OutputProvenance:
    return OutputProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(4, 5),
        trace_event_ids=("worldlet:consequence-output",),
    )


def _worldlet_provenance() -> WorldletProvenance:
    return WorldletProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(4, 5),
        trace_event_ids=("worldlet:consequence",),
    )


def _impulse(suffix: str, *, text: str = "tap") -> OutputImpulse:
    return OutputImpulse(
        impulse_id=f"out:wld-consequence-{suffix}",
        text=text,
        provenance=_output_provenance(),
    )


def _ready_support() -> tuple[
    OutputHistory,
    OutputTokenCandidate,
    LearnedOutputToken,
    ProtoOutputActionReadiness,
]:
    first = _impulse("one")
    second = _impulse("two")
    history = OutputHistory()
    history, one_off = update_output_pattern(history, first)
    assert one_off is None
    history, pattern = update_output_pattern(history, second)
    assert isinstance(pattern, OutputPattern)

    for impulse_id, suffix in (
        (pattern.impulse_ids[0], "one"),
        (pattern.impulse_ids[1], "two"),
    ):
        history = echo_output_impulse(
            history,
            impulse_id=impulse_id,
            echo_id=f"out:wld-consequence-echo-{suffix}",
        )

    history, candidate = maybe_create_output_token_candidate(history, pattern)
    assert isinstance(candidate, OutputTokenCandidate)
    learned_history = learn_output_token(history, candidate)
    learned_token = learned_history.learned_tokens[candidate.token_id]
    readiness = observe_proto_output_action_readiness(learned_history, candidate)
    assert isinstance(learned_token, LearnedOutputToken)
    assert readiness.ready is True
    return learned_history, candidate, learned_token, readiness


def _state(accepted_token_id: str) -> WorldletState:
    accepts = WorldletObject(
        object_id="wld:target-accepts",
        label="accepts",
        available=True,
        accepted_token_ids=(accepted_token_id,),
    )
    rejects = WorldletObject(
        object_id="wld:target-rejects",
        label="rejects",
        available=True,
        accepted_token_ids=("out-token:other",),
    )
    unavailable = WorldletObject(
        object_id="wld:target-unavailable",
        label="unavailable",
        available=False,
        accepted_token_ids=(accepted_token_id,),
    )
    return WorldletState(
        state_id="wld:state-consequence",
        objects={
            accepts.object_id: accepts,
            rejects.object_id: rejects,
            unavailable.object_id: unavailable,
        },
    )


def _attempt(target_id: str | None, *, attempt_id: str) -> WorldletAttempt:
    history, _, learned_token, readiness = _ready_support()
    return construct_worldlet_attempt(
        history,
        readiness,
        learned_token,
        attempt_id=attempt_id,
        target_id=target_id,
        provenance=_worldlet_provenance(),
    )


@register("I-WLD-09", status="REQUIRED")
def check_accepted_worldlet_attempt_produces_deterministic_bounded_response() -> None:
    runtime_state = initial_state()
    before_profile = runtime_state.profile
    before_msi = runtime_state.msi
    before_ptcns = runtime_state.ptcns
    before_registry = runtime_state.registry

    attempt = _attempt("wld:target-accepts", attempt_id="wld:attempt-accepted")
    worldlet_state = _state(attempt.token_id)
    history = WorldletHistory(latest_state=worldlet_state)
    next_history, response = respond_worldlet(history, attempt)
    repeat_history, repeat_response = respond_worldlet(history, attempt)

    assert isinstance(response, WorldletResponse)
    assert response.accepted is True
    assert response.reason == "accepted"
    assert response.valence.value == Fraction(1, 2)
    assert repeat_response == response
    assert repeat_history.latest_state == next_history.latest_state
    assert next_history is not history
    assert history.attempts == ()
    assert history.responses == ()
    assert next_history.attempts == (attempt,)
    assert next_history.responses == (response,)
    assert next_history.latest_state.step_index == worldlet_state.step_index + 1
    assert next_history.latest_state.objects == worldlet_state.objects

    assert runtime_state.profile is before_profile
    assert runtime_state.msi is before_msi
    assert runtime_state.ptcns is before_ptcns
    assert runtime_state.registry is before_registry
    assert response.response_id not in runtime_state.profile.domain
    assert response.response_id not in runtime_state.registry.texts


@register("I-WLD-10", status="REQUIRED")
def check_negative_worldlet_outcomes_are_bounded_and_local() -> None:
    runtime_state = initial_state()
    before_profile = runtime_state.profile
    before_msi = runtime_state.msi
    before_ptcns = runtime_state.ptcns
    before_registry = runtime_state.registry

    cases = (
        ("wld:target-rejects", "rejected"),
        ("wld:target-unavailable", "target-unavailable"),
        ("wld:target-missing", "missing-target"),
    )
    for target_id, reason in cases:
        attempt = _attempt(target_id, attempt_id=f"wld:attempt-{reason}")
        worldlet_state = _state(attempt.token_id)
        history = WorldletHistory(latest_state=worldlet_state)
        next_history, response = respond_worldlet(history, attempt)

        assert isinstance(response, WorldletResponse)
        assert response.accepted is False
        assert response.reason == reason
        assert response.valence.value == Fraction(-1, 2)
        assert Fraction(-1) <= response.valence.value <= Fraction(1)
        assert next_history.attempts == (attempt,)
        assert next_history.responses == (response,)
        assert next_history.latest_state.step_index == worldlet_state.step_index + 1
        assert history.attempts == ()
        assert history.responses == ()

    assert runtime_state.profile is before_profile
    assert runtime_state.msi is before_msi
    assert runtime_state.ptcns is before_ptcns
    assert runtime_state.registry is before_registry
