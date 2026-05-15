"""Fixtures for Phase 3.3 worldlet attempt rows."""
from __future__ import annotations

from dataclasses import fields, replace
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
    WorldletProvenance,
    construct_worldlet_attempt,
)
from brain.invariants import register
from brain.tlica.profile import COGITO_ID


def _output_provenance() -> OutputProvenance:
    return OutputProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(4, 5),
        trace_event_ids=("worldlet:attempt-output",),
    )


def _worldlet_provenance() -> WorldletProvenance:
    return WorldletProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(4, 5),
        trace_event_ids=("worldlet:attempt",),
    )


def _impulse(suffix: str, *, text: str = "tap") -> OutputImpulse:
    return OutputImpulse(
        impulse_id=f"out:wld-attempt-{suffix}",
        text=text,
        provenance=_output_provenance(),
    )


def _history_with_candidate() -> tuple[OutputHistory, OutputTokenCandidate]:
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
            echo_id=f"out:wld-attempt-echo-{suffix}",
        )

    history, candidate = maybe_create_output_token_candidate(history, pattern)
    assert isinstance(candidate, OutputTokenCandidate)
    return history, candidate


def _ready_support() -> tuple[
    OutputHistory,
    OutputTokenCandidate,
    LearnedOutputToken,
    ProtoOutputActionReadiness,
]:
    history, candidate = _history_with_candidate()
    learned_history = learn_output_token(history, candidate)
    learned_token = learned_history.learned_tokens[candidate.token_id]
    readiness = observe_proto_output_action_readiness(learned_history, candidate)
    assert isinstance(learned_token, LearnedOutputToken)
    assert readiness.ready is True
    return learned_history, candidate, learned_token, readiness


def _valid_attempt() -> WorldletAttempt:
    history, _, learned_token, readiness = _ready_support()
    return construct_worldlet_attempt(
        history,
        readiness,
        learned_token,
        attempt_id="wld:attempt-supported",
        target_id="wld:target-supported",
        provenance=_worldlet_provenance(),
    )


def _assert_i_wld_07_rejects(call: object) -> None:
    try:
        assert callable(call)
        call()
    except ValueError as exc:
        assert "I-WLD-07" in str(exc)
    else:
        raise AssertionError("I-WLD-07 violated: unsupported attempt passed")


@register("I-WLD-07", status="REQUIRED")
def check_worldlet_attempt_requires_ready_learned_token_support() -> None:
    history, candidate, learned_token, readiness = _ready_support()
    attempt = construct_worldlet_attempt(
        history,
        readiness,
        learned_token,
        attempt_id="wld:attempt-supported",
        target_id="wld:target-supported",
        provenance=_worldlet_provenance(),
    )
    assert attempt.token_id == learned_token.token_id
    assert attempt.pattern_id == learned_token.pattern_id
    assert attempt.target_id == "wld:target-supported"

    incomplete = observe_proto_output_action_readiness(
        _history_with_candidate()[0],
        candidate,
    )
    assert incomplete.ready is False

    _assert_i_wld_07_rejects(
        lambda: construct_worldlet_attempt(
            history,
            readiness,
            None,  # type: ignore[arg-type]
            attempt_id="wld:attempt-no-token",
            target_id="wld:target-supported",
            provenance=_worldlet_provenance(),
        )
    )
    _assert_i_wld_07_rejects(
        lambda: construct_worldlet_attempt(
            history,
            incomplete,
            learned_token,
            attempt_id="wld:attempt-incomplete",
            target_id="wld:target-supported",
            provenance=_worldlet_provenance(),
        )
    )
    _assert_i_wld_07_rejects(
        lambda: construct_worldlet_attempt(
            OutputHistory(),
            readiness,
            learned_token,
            attempt_id="wld:attempt-missing-history",
            target_id="wld:target-supported",
            provenance=_worldlet_provenance(),
        )
    )
    _assert_i_wld_07_rejects(
        lambda: construct_worldlet_attempt(
            history,
            replace(readiness, token_id="out-token:mismatch"),
            learned_token,
            attempt_id="wld:attempt-token-mismatch",
            target_id="wld:target-supported",
            provenance=_worldlet_provenance(),
        )
    )
    _assert_i_wld_07_rejects(
        lambda: construct_worldlet_attempt(
            history,
            replace(readiness, pattern_id="out-pattern:mismatch"),
            learned_token,
            attempt_id="wld:attempt-pattern-mismatch",
            target_id="wld:target-supported",
            provenance=_worldlet_provenance(),
        )
    )
    _assert_i_wld_07_rejects(
        lambda: construct_worldlet_attempt(
            history,
            readiness,
            learned_token,
            attempt_id=COGITO_ID,
            target_id="wld:target-supported",
            provenance=_worldlet_provenance(),
        )
    )
    _assert_i_wld_07_rejects(
        lambda: construct_worldlet_attempt(
            history,
            readiness,
            learned_token,
            attempt_id="wld:attempt-bad-target",
            target_id="bad\ntarget",
            provenance=_worldlet_provenance(),
        )
    )


@register("I-WLD-08", status="STRUCTURAL")
def check_worldlet_attempt_remains_below_agency_language_and_repl() -> None:
    attempt = _valid_attempt()
    forbidden = {
        "act",
        "action",
        "selected_action",
        "mode",
        "mode_op",
        "agency",
        "agency_witness",
        "percept_event",
        "feasible_projected_pce",
        "grammar",
        "command_syntax",
        "teacher_correction",
        "language",
        "tick",
    }
    names = {field.name for field in fields(attempt)}
    assert not (names & forbidden), (
        f"I-WLD-08 violated: WorldletAttempt exposes {names & forbidden}"
    )
    for name in forbidden | {"Act", "ModeOp", "AgencyWitness", "PerceptEvent"}:
        assert not hasattr(attempt, name), (
            f"I-WLD-08 violated: WorldletAttempt exposes {name}"
        )
