"""Fixtures for Phase 3.3 worldlet consequence rows."""
from __future__ import annotations

from dataclasses import fields
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
    WORLDLET_LOCAL_EVIDENCE_SCOPE,
    WORLDLET_PUSHBACK_REASONS,
    WorldletConsequenceSummary,
    WorldletAttempt,
    WorldletHistory,
    WorldletObject,
    WorldletProvenance,
    WorldletResponse,
    WorldletState,
    construct_worldlet_attempt,
    respond_worldlet,
    summarize_worldlet_consequences,
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


def _history_with_all_consequence_cases() -> tuple[
    WorldletHistory,
    tuple[WorldletResponse, ...],
]:
    accepted_attempt = _attempt(
        "wld:target-accepts",
        attempt_id="wld:attempt-summary-accepted",
    )
    history = WorldletHistory(latest_state=_state(accepted_attempt.token_id))
    responses: tuple[WorldletResponse, ...] = ()
    attempts = (
        accepted_attempt,
        _attempt("wld:target-rejects", attempt_id="wld:attempt-summary-rejected"),
        _attempt(
            "wld:target-unavailable",
            attempt_id="wld:attempt-summary-target-unavailable",
        ),
        _attempt("wld:target-missing", attempt_id="wld:attempt-summary-missing"),
    )
    for attempt in attempts:
        history, response = respond_worldlet(history, attempt)
        responses = responses + (response,)
    return history, responses


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


@register("I-WLD-11", status="STRUCTURAL")
def check_not_i_pushback_is_local_response_evidence() -> None:
    history, responses = _history_with_all_consequence_cases()
    summaries = summarize_worldlet_consequences(history)
    assert len(summaries) == len(responses)

    forbidden = {
        "external_reality",
        "external_truth",
        "external_world",
        "external_world_truth",
        "social_teacher",
        "teacher_correction",
        "language",
        "language_understanding",
        "affect_taxonomy",
        "free_will",
        "free_will_branch",
        "mode_b",
        "mode_b_planning",
        "percept_event",
        "tick",
    }
    for response, summary in zip(responses, summaries, strict=True):
        assert isinstance(summary, WorldletConsequenceSummary)
        assert summary.response_id == response.response_id
        assert summary.attempt_id == response.attempt_id
        assert summary.reason == response.reason
        assert summary.source_kind is response.provenance.source_kind
        assert summary.confidence == response.provenance.confidence
        assert summary.evidence_scope == WORLDLET_LOCAL_EVIDENCE_SCOPE

        response_names = {field.name for field in fields(response)}
        summary_names = {field.name for field in fields(summary)}
        assert not (response_names & forbidden), (
            f"I-WLD-11 violated: WorldletResponse exposes {response_names & forbidden}"
        )
        assert not (summary_names & forbidden), (
            "I-WLD-11 violated: WorldletConsequenceSummary exposes "
            f"{summary_names & forbidden}"
        )
        for name in forbidden | {"ExternalReality", "ModeB", "PerceptEvent"}:
            assert not hasattr(response, name), (
                f"I-WLD-11 violated: WorldletResponse exposes {name}"
            )
            assert not hasattr(summary, name), (
                f"I-WLD-11 violated: WorldletConsequenceSummary exposes {name}"
            )

        if summary.reason in WORLDLET_PUSHBACK_REASONS:
            assert summary.is_pushback is True
            assert summary.accepted is False
            assert summary.valence < 0
        else:
            assert summary.reason == "accepted"
            assert summary.is_pushback is False
            assert summary.accepted is True
            assert summary.valence > 0


@register("I-WLD-12", status="OBSERVED")
def observe_aggregate_local_consequence_history() -> None:
    history, responses = _history_with_all_consequence_cases()
    summaries = summarize_worldlet_consequences(history)
    assert history.responses == responses
    assert tuple(summary.reason for summary in summaries) == (
        "accepted",
        "rejected",
        "target-unavailable",
        "missing-target",
    )
    by_reason = {summary.reason: summary for summary in summaries}
    assert by_reason["accepted"].accepted is True
    assert by_reason["accepted"].valence == Fraction(1, 2)
    for reason in WORLDLET_PUSHBACK_REASONS:
        assert by_reason[reason].accepted is False
        assert by_reason[reason].is_pushback is True
        assert by_reason[reason].valence == Fraction(-1, 2)


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
