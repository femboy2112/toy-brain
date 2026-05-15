"""Fixtures for Phase 3.4 Proto-BASIC REPL feedback rows.

This module drives ``I-REPL-06``..``I-REPL-10``: bounded valence, reuse of
existing source / provenance discipline, bounded-negative scoring for the
non-near-miss / non-valid parse and execution categories, and the strong-
positive-feedback gate that requires ``execution_result.effective == True``.
"""
from __future__ import annotations

from fractions import Fraction

from brain.development.stream import FrameSourceKind
from brain.development.repl import (
    PROTO_BASIC_STRONG_POSITIVE_THRESHOLD,
    ProtoBasicExecutionCategory,
    ProtoBasicExecutionResult,
    ProtoBasicFeedback,
    ProtoBasicFeedbackProvenance,
    ProtoBasicParseCategory,
    ProtoBasicParseResult,
    ProtoBasicValence,
    score_feedback,
)
from brain.invariants import register


def _provenance() -> ProtoBasicFeedbackProvenance:
    return ProtoBasicFeedbackProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(4, 5),
        trace_event_ids=("repl:trace:feedback-1",),
    )


@register("I-REPL-06", status="REQUIRED")
def check_proto_basic_valence_is_exact_and_bounded() -> None:
    ok = ProtoBasicValence(Fraction(1, 2))
    assert ok.value == Fraction(1, 2)

    # Boundary values pass.
    assert ProtoBasicValence(Fraction(-1)).value == Fraction(-1)
    assert ProtoBasicValence(Fraction(1)).value == Fraction(1)

    # Out-of-range values are rejected without clamping.
    for bad in (Fraction(-3, 2), Fraction(3, 2)):
        try:
            ProtoBasicValence(bad)
        except ValueError as exc:
            assert "I-REPL-06" in str(exc)
        else:
            raise AssertionError(
                f"I-REPL-06 violated: out-of-range valence {bad} accepted"
            )

    # Non-Fraction types are rejected.
    try:
        ProtoBasicValence(0.5)  # type: ignore[arg-type]
    except ValueError as exc:
        assert "I-REPL-06" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-06 violated: non-Fraction valence accepted"
        )


@register("I-REPL-07", status="STRUCTURAL")
def check_proto_basic_feedback_reuses_existing_source_provenance_discipline() -> None:
    provenance = _provenance()
    assert isinstance(provenance.source_kind, FrameSourceKind)
    assert Fraction(0) <= provenance.confidence <= Fraction(1)
    assert all(isinstance(tid, str) for tid in provenance.trace_event_ids)

    # No Proto-BASIC-specific FrameSourceKind member exists. We assert the
    # enum still has exactly the v0.6 source-kind members.
    members = {member.value for member in FrameSourceKind}
    expected = {
        "endogenous",
        "operator_injection",
        "probe_echo",
        "external",
        "generated",
    }
    assert members == expected, (
        "I-REPL-07 violated: FrameSourceKind gained a Proto-BASIC-specific "
        f"member; saw {members - expected}"
    )

    # Out-of-range confidence is rejected with the row tag.
    try:
        ProtoBasicFeedbackProvenance(
            source_kind=FrameSourceKind.GENERATED,
            confidence=Fraction(3, 2),
        )
    except ValueError as exc:
        assert "I-REPL-07" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-07 violated: out-of-range confidence accepted"
        )

    # Wrong source_kind type rejected with the row tag.
    try:
        ProtoBasicFeedbackProvenance(
            source_kind="generated",  # type: ignore[arg-type]
            confidence=Fraction(1, 2),
        )
    except TypeError as exc:
        assert "I-REPL-07" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-07 violated: non-FrameSourceKind source accepted"
        )

    # ProtoBasicFeedback rejects non-provenance values with the row tag.
    parse_result = ProtoBasicParseResult(
        line_id="repl:line:provenance",
        category=ProtoBasicParseCategory.SYNTAX_INVALID,
    )
    feedback = score_feedback(parse_result=parse_result, provenance=provenance)
    assert isinstance(feedback.provenance, ProtoBasicFeedbackProvenance)


def _execution(
    category: ProtoBasicExecutionCategory,
    *,
    line_id: str,
) -> ProtoBasicExecutionResult:
    effective = category is ProtoBasicExecutionCategory.VALID_EFFECTIVE
    return ProtoBasicExecutionResult(
        line_id=line_id,
        category=category,
        effective=effective,
        detail=f"detail:{category.value}",
    )


@register("I-REPL-08", status="REQUIRED")
def check_negative_categories_produce_bounded_negative_valence() -> None:
    provenance = _provenance()

    # Parse-side categories.
    negative_parse_categories = (
        ProtoBasicParseCategory.SYNTAX_INVALID,
        ProtoBasicParseCategory.SEMANTIC_INVALID,
        ProtoBasicParseCategory.TOOL_UNAVAILABLE,
        ProtoBasicParseCategory.RESOURCE_LIMIT,
        ProtoBasicParseCategory.SANDBOX_FAULT,
    )
    for category in negative_parse_categories:
        parse_result = ProtoBasicParseResult(
            line_id=f"repl:line:neg-parse:{category.value}",
            category=category,
        )
        feedback = score_feedback(
            parse_result=parse_result, provenance=provenance
        )
        value = feedback.valence.value
        assert value < Fraction(0), (
            f"I-REPL-08 violated: {category} produced non-negative valence "
            f"{value}"
        )
        assert Fraction(-1) <= value < Fraction(0), (
            f"I-REPL-08 violated: {category} valence {value} outside [-1, 0)"
        )

    # Execution-side categories.
    negative_exec_categories = (
        ProtoBasicExecutionCategory.TOOL_UNAVAILABLE,
        ProtoBasicExecutionCategory.RESOURCE_LIMIT,
        ProtoBasicExecutionCategory.SANDBOX_FAULT,
    )
    for category in negative_exec_categories:
        execution = _execution(
            category, line_id=f"repl:line:neg-exec:{category.value}"
        )
        feedback = score_feedback(
            execution_result=execution, provenance=provenance
        )
        value = feedback.valence.value
        assert Fraction(-1) <= value < Fraction(0), (
            f"I-REPL-08 violated: {category} valence {value} outside [-1, 0)"
        )

    # Determinism: same input twice -> same output.
    parse_result = ProtoBasicParseResult(
        line_id="repl:line:neg-determinism",
        category=ProtoBasicParseCategory.SYNTAX_INVALID,
    )
    first = score_feedback(parse_result=parse_result, provenance=provenance)
    second = score_feedback(parse_result=parse_result, provenance=provenance)
    assert first == second


@register("I-REPL-09", status="REQUIRED")
def check_valid_syntax_alone_does_not_grant_strong_positive_feedback() -> None:
    from brain.development.repl import ProtoBasicTokenKind

    provenance = _provenance()
    threshold = PROTO_BASIC_STRONG_POSITIVE_THRESHOLD

    # A syntactically-VALID parse result alone scores at or below the
    # non-strong threshold.
    valid_parse = ProtoBasicParseResult(
        line_id="repl:line:valid-print",
        category=ProtoBasicParseCategory.VALID,
        matched_shape=(
            ProtoBasicTokenKind.VERB,
            ProtoBasicTokenKind.TARGET,
        ),
        matched_token_ids=("repl:verb:print", "repl:target:x"),
    )
    parse_feedback = score_feedback(
        parse_result=valid_parse, provenance=provenance
    )
    assert abs(parse_feedback.valence.value) <= threshold, (
        "I-REPL-09 violated: valid-parse-only feedback exceeded threshold "
        f"{parse_feedback.valence.value}"
    )

    # Valid-ineffective execution scores at or below the threshold.
    ineffective = _execution(
        ProtoBasicExecutionCategory.VALID_INEFFECTIVE,
        line_id="repl:line:valid-ineffective",
    )
    ineffective_feedback = score_feedback(
        execution_result=ineffective, provenance=provenance
    )
    assert (
        abs(ineffective_feedback.valence.value) <= threshold
    ), (
        "I-REPL-09 violated: valid-ineffective feedback exceeded threshold "
        f"{ineffective_feedback.valence.value}"
    )

    # Near-miss feedback also cannot reach strong positive valence even with
    # a maximal diminishing_returns_factor.
    near = ProtoBasicParseResult(
        line_id="repl:line:near-feedback",
        category=ProtoBasicParseCategory.NEAR_MISS,
        matched_shape=None,
        matched_token_ids=(),
        correction_hint=_dummy_hint(),
    )
    near_feedback = score_feedback(
        parse_result=near,
        provenance=provenance,
        diminishing_returns_factor=Fraction(1),
    )
    assert near_feedback.valence.value < threshold, (
        "I-REPL-09 violated: near-miss feedback reached strong positive "
        f"valence {near_feedback.valence.value}"
    )


def _dummy_hint():
    from brain.development.repl import (
        ProtoBasicCorrectionHint,
        ProtoBasicEditKind,
    )

    return ProtoBasicCorrectionHint(
        edit_kind=ProtoBasicEditKind.CASE_FOLD,
        edit_position=0,
        expected_token_id="repl:verb:print",
        edit_distance=1,
    )


@register("I-REPL-10", status="REQUIRED")
def check_strong_positive_requires_valid_effective_execution() -> None:
    provenance = _provenance()
    threshold = PROTO_BASIC_STRONG_POSITIVE_THRESHOLD

    # valid-effective execution produces strong positive valence.
    effective = _execution(
        ProtoBasicExecutionCategory.VALID_EFFECTIVE,
        line_id="repl:line:effective",
    )
    feedback = score_feedback(
        execution_result=effective, provenance=provenance
    )
    assert feedback.valence.value > threshold, (
        "I-REPL-10 violated: valid-effective execution did not reach strong "
        f"positive valence (got {feedback.valence.value})"
    )

    # No other execution category yields a value above the threshold.
    for category in (
        ProtoBasicExecutionCategory.VALID_INEFFECTIVE,
        ProtoBasicExecutionCategory.TOOL_UNAVAILABLE,
        ProtoBasicExecutionCategory.RESOURCE_LIMIT,
        ProtoBasicExecutionCategory.SANDBOX_FAULT,
    ):
        execution = _execution(
            category, line_id=f"repl:line:non-effective:{category.value}"
        )
        non_strong = score_feedback(
            execution_result=execution, provenance=provenance
        )
        assert non_strong.valence.value <= threshold, (
            "I-REPL-10 violated: non-effective category produced strong "
            f"positive valence; {category} -> {non_strong.valence.value}"
        )

    # Construction of an ExecutionResult with mismatched effective/category
    # is rejected -- there is no path that bypasses ``effective``.
    try:
        ProtoBasicExecutionResult(
            line_id="repl:line:bad-effective",
            category=ProtoBasicExecutionCategory.VALID_INEFFECTIVE,
            effective=True,
        )
    except ValueError as exc:
        assert "I-REPL-13" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-10 violated: invalid effective/category combination "
            "accepted"
        )

    # Even at the maximum diminishing-returns factor (Fraction(1)), only
    # valid-effective execution reaches strong positive valence.
    other_categories = (
        ProtoBasicExecutionCategory.VALID_INEFFECTIVE,
        ProtoBasicExecutionCategory.TOOL_UNAVAILABLE,
    )
    for category in other_categories:
        execution = _execution(
            category, line_id=f"repl:line:max-factor:{category.value}"
        )
        feedback = score_feedback(
            execution_result=execution,
            provenance=provenance,
            diminishing_returns_factor=Fraction(1),
        )
        assert feedback.valence.value <= threshold

    # Parse-only categories likewise never reach strong positive valence
    # regardless of the factor (I-REPL-10 cross-check with I-REPL-09).
    from brain.development.repl import ProtoBasicTokenKind

    valid_parse = ProtoBasicParseResult(
        line_id="repl:line:parse-strong-check",
        category=ProtoBasicParseCategory.VALID,
        matched_shape=(
            ProtoBasicTokenKind.VERB,
            ProtoBasicTokenKind.TARGET,
        ),
        matched_token_ids=("repl:verb:print", "repl:target:x"),
    )
    parse_feedback = score_feedback(
        parse_result=valid_parse, provenance=provenance
    )
    assert parse_feedback.valence.value <= threshold
