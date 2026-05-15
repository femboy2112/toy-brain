"""Fixture for I-EXP-04: ReadabilityScore is a Fraction in [0, 1]."""
from __future__ import annotations

from fractions import Fraction

from brain.development.expression import ReadabilityScore
from brain.invariants import register


def _assert_rejects(call) -> None:
    try:
        call()
    except (TypeError, ValueError) as exc:
        assert "I-EXP-04" in str(exc), (
            f"I-EXP-04 negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-EXP-04 violated: invalid ReadabilityScore was accepted"
        )


@register("I-EXP-04", status="REQUIRED")
def check_readability_score_fraction_bounded() -> None:
    for value in (Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(1)):
        score = ReadabilityScore(value=value)
        assert isinstance(score.value, Fraction)
        assert Fraction(0) <= score.value <= Fraction(1)

    _assert_rejects(lambda: ReadabilityScore(value=Fraction(-1, 100)))
    _assert_rejects(lambda: ReadabilityScore(value=Fraction(101, 100)))
    _assert_rejects(lambda: ReadabilityScore(value=0.5))  # type: ignore[arg-type]
    _assert_rejects(lambda: ReadabilityScore(value=1))  # type: ignore[arg-type]
    _assert_rejects(lambda: ReadabilityScore(value="0.5"))  # type: ignore[arg-type]
