"""Fixture for I-EXP-11: length alone is capped (anti-Goodhart)."""
from __future__ import annotations

from fractions import Fraction

from brain.development.expression import (
    LENGTH_SATURATION_BOUND,
    ExpressionItem,
    ExpressionSource,
    extract_features,
    predict_readability,
)
from brain.invariants import register


_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _distinct_two_char_tokens(count: int) -> list[str]:
    """Return `count` distinct fixed-length 2-char tokens.

    Two-char tokens keep the printable / total-char ratio close to
    constant across counts, isolating the length component for the
    saturation probe.
    """
    out: list[str] = []
    base = len(_ALPHABET)
    for i in range(count):
        a = _ALPHABET[(i // base) % base]
        b = _ALPHABET[i % base]
        out.append(a + b)
    assert len(set(out)) == count, "internal: token uniqueness lost"
    return out


def _pad_distinct(count: int) -> ExpressionItem:
    text = " ".join(_distinct_two_char_tokens(count))
    return ExpressionItem(
        item_id=f"exp:pad-{count}",
        text=text,
        source=ExpressionSource.WORLDLET_HISTORY,
    )


@register("I-EXP-11", status="REQUIRED")
def check_length_alone_is_capped() -> None:
    sat_item = _pad_distinct(LENGTH_SATURATION_BOUND)
    over_item = _pad_distinct(LENGTH_SATURATION_BOUND * 2)

    sat_features = extract_features(sat_item)
    over_features = extract_features(over_item)
    assert sat_features.token_count == LENGTH_SATURATION_BOUND
    assert over_features.token_count == LENGTH_SATURATION_BOUND * 2

    sat_score = predict_readability(sat_item).score.value
    over_score = predict_readability(over_item).score.value

    assert Fraction(0) <= sat_score <= Fraction(1)
    assert Fraction(0) <= over_score <= Fraction(1)
    # Beyond LENGTH_SATURATION_BOUND, the length component stops growing.
    # All other components stay constant (all-distinct → distinct ratio 1,
    # no repeats → 0 penalty, fixed-length tokens → near-constant shape).
    # So the over-saturation score must not strictly exceed the saturation
    # score.
    assert over_score <= sat_score, (
        f"I-EXP-11 violated: doubling distinct-token length raised score "
        f"from {sat_score} to {over_score}"
    )
