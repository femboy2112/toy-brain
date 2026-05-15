"""Fixtures for Phase 3.2 output token-candidate rows."""
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
    echo_output_impulse,
    learn_output_token,
    maybe_create_output_token_candidate,
    token_id_for_output_pattern,
    update_output_pattern,
)
from brain.development.stream import FrameSourceKind
from brain.invariants import register
from brain.tick import initial_state
from brain.tlica.profile import COGITO_ID


def _provenance(
    kind: FrameSourceKind = FrameSourceKind.GENERATED,
) -> OutputProvenance:
    return OutputProvenance(
        source_kind=kind,
        confidence=Fraction(4, 5),
        trace_event_ids=("output:token-trace",),
    )


def _impulse(suffix: str, *, text: str = "pulse") -> OutputImpulse:
    return OutputImpulse(
        impulse_id=f"out:token-{suffix}",
        text=text,
        provenance=_provenance(),
    )


def _history_with_pattern() -> tuple[OutputHistory, OutputPattern]:
    first = _impulse("one")
    second = _impulse("two")
    history = OutputHistory()
    history, one_off = update_output_pattern(history, first)
    assert one_off is None
    history, pattern = update_output_pattern(history, second)
    assert isinstance(pattern, OutputPattern)
    return history, pattern


def _history_with_candidate() -> tuple[OutputHistory, OutputTokenCandidate]:
    history, pattern = _history_with_pattern()
    for impulse_id, echo_suffix in (
        (pattern.impulse_ids[0], "one"),
        (pattern.impulse_ids[1], "two"),
    ):
        history = echo_output_impulse(
            history,
            impulse_id=impulse_id,
            echo_id=f"out:echo-token-{echo_suffix}",
        )

    history, candidate = maybe_create_output_token_candidate(history, pattern)
    assert isinstance(candidate, OutputTokenCandidate)
    return history, candidate


def _assert_i_out_08_rejects(call: object) -> None:
    try:
        assert callable(call)
        call()
    except ValueError as exc:
        assert "I-OUT-08" in str(exc)
    else:
        raise AssertionError("I-OUT-08 violated: invalid token candidate passed")


@register("I-OUT-08", status="REQUIRED")
def check_token_candidate_requires_recurrence_and_echo_provenance() -> None:
    history, pattern = _history_with_pattern()
    recurrent_only_history, recurrent_only = maybe_create_output_token_candidate(
        history,
        pattern,
    )
    assert recurrent_only_history is history
    assert recurrent_only is None

    echo_only = OutputHistory()
    echo_only = echo_output_impulse(
        update_output_pattern(echo_only, _impulse("echo-only"))[0],
        impulse_id="out:token-echo-only",
        echo_id="out:echo-only",
    )
    echo_only_history, echo_only_candidate = maybe_create_output_token_candidate(
        echo_only,
        None,
    )
    assert echo_only_history is echo_only
    assert echo_only_candidate is None

    one_off_history, one_off_pattern = update_output_pattern(
        OutputHistory(),
        _impulse("one-off"),
    )
    assert one_off_pattern is None
    one_off_history, one_off_candidate = maybe_create_output_token_candidate(
        one_off_history,
        one_off_pattern,
    )
    assert one_off_candidate is None

    history, candidate = _history_with_candidate()
    assert history.token_candidates[candidate.token_id] is candidate
    assert candidate.token_id == token_id_for_output_pattern(pattern)
    assert candidate.support_count == 2
    assert len(candidate.impulse_ids) == 2
    assert len(candidate.echo_ids) == 2
    assert candidate.source_kinds == pattern.source_kinds

    _assert_i_out_08_rejects(
        lambda: OutputTokenCandidate(
            token_id=COGITO_ID,
            pattern_id=pattern.pattern_id,
            text=pattern.text,
            support_count=2,
            impulse_ids=pattern.impulse_ids,
            echo_ids=("out:echo-a", "out:echo-b"),
            source_kinds=pattern.source_kinds,
        )
    )
    _assert_i_out_08_rejects(
        lambda: OutputTokenCandidate(
            token_id="out-token:one-off",
            pattern_id=pattern.pattern_id,
            text=pattern.text,
            support_count=1,
            impulse_ids=(pattern.impulse_ids[0],),
            echo_ids=("out:echo-a",),
            source_kinds=pattern.source_kinds,
        )
    )
    _assert_i_out_08_rejects(
        lambda: OutputTokenCandidate(
            token_id="out-token:missing-echo",
            pattern_id=pattern.pattern_id,
            text=pattern.text,
            support_count=2,
            impulse_ids=pattern.impulse_ids,
            echo_ids=(),
            source_kinds=pattern.source_kinds,
        )
    )
    _assert_i_out_08_rejects(
        lambda: OutputTokenCandidate(
            token_id="out-token:missing-source",
            pattern_id=pattern.pattern_id,
            text=pattern.text,
            support_count=2,
            impulse_ids=pattern.impulse_ids,
            echo_ids=("out:echo-a", "out:echo-b"),
            source_kinds=frozenset(),
        )
    )


@register("I-OUT-09", status="STRUCTURAL")
def check_learned_output_token_remains_below_language() -> None:
    history, candidate = _history_with_candidate()
    learned_history = learn_output_token(history, candidate)
    token = learned_history.learned_tokens[candidate.token_id]
    assert isinstance(token, LearnedOutputToken)
    assert token.text == candidate.text
    assert token.pattern_id == candidate.pattern_id
    assert token.support_count == candidate.support_count

    forbidden = {
        "grammar",
        "teacher_correction",
        "world_reference",
        "readability",
        "social_meaning",
        "command_syntax",
        "language",
    }
    for obj in (candidate, token):
        names = {field.name for field in fields(obj)}
        assert not (names & forbidden), (
            f"I-OUT-09 violated: {type(obj).__name__} exposes {names & forbidden}"
        )
        for name in forbidden:
            assert not hasattr(obj, name), (
                f"I-OUT-09 violated: {type(obj).__name__} exposes {name}"
            )


@register("I-OUT-10", status="REQUIRED")
def check_learned_output_token_requires_candidate_and_no_runtime_mutation() -> None:
    state = initial_state()
    before_profile = state.profile
    before_msi = state.msi
    before_ptcns = state.ptcns
    before_registry = state.registry

    history, candidate = _history_with_candidate()
    learned_history = learn_output_token(history, candidate)
    token = learned_history.learned_tokens[candidate.token_id]

    assert isinstance(token, LearnedOutputToken)
    assert token.candidate is candidate
    assert token.token_id == candidate.token_id
    assert learned_history is not history
    assert history.learned_tokens == {}

    unsupported_history = OutputHistory()
    try:
        learn_output_token(unsupported_history, candidate)
    except ValueError as exc:
        assert "I-OUT-10" in str(exc)
    else:
        raise AssertionError(
            "I-OUT-10 violated: learned token was built without candidate support"
        )

    assert state.profile is before_profile
    assert state.msi is before_msi
    assert state.ptcns is before_ptcns
    assert state.registry is before_registry
    assert token.token_id not in state.profile.domain
    assert token.token_id not in state.registry.texts
