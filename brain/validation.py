"""Reusable assertion helpers for fixtures and the invariant runner.

Per the catalog's "three-way split" convention:
    builders → validation
    invariants → fixtures + validation
    tick → builders + invariants

This module is the **shared** assertion utility layer — pure, side-effect
free, no construction. Imports stdlib + ``brain.tlica.profile`` only.
"""
from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction
from typing import TypeVar

from brain.tlica.profile import ScalarProfile

T = TypeVar("T")


def is_in_unit_interval(v: Fraction) -> bool:
    """``True`` iff ``v ∈ [0, 1]``. ``Fraction``-only by convention."""
    return Fraction(0) <= v <= Fraction(1)


def profile_equiv(p: ScalarProfile, q: ScalarProfile) -> bool:
    """Exact equality of profiles (domain + values).

    Safe under ``Fraction`` because ``==`` on Fractions is exact. Used by
    the runner for ``I-PMAP-02`` (project(NOOP, P) == natural_dynamics(P))
    and ``I-TRJ-01`` (one-step generated trajectory).
    """
    if p.domain != q.domain:
        return False
    for k in p.domain:
        if p.values[k] != q.values[k]:
            return False
    return True


def assert_subset_rank_le(
    rank_fn: Callable[[frozenset[T]], Fraction],
    pairs: list[tuple[frozenset[T], frozenset[T]]],
) -> None:
    """For each supplied (S, T) with S ⊆ T, assert rank_fn(S) ≤ rank_fn(T).

    Per corrigenda D6: pairs come from the fixture, not from internal
    randomness — the runner must be deterministic. Each fixture supplies
    a hand-built list of ``(subset, superset)`` pairs that exercise the
    row's intent.

    Raises ``AssertionError`` on a violation (so the runner can report it
    as a red row), or ``ValueError`` if a supplied pair is not a subset.
    """
    for S, super_T in pairs:
        if not S <= super_T:
            raise ValueError(
                f"assert_subset_rank_le: {S!r} is not a subset of {super_T!r}"
            )
        rs = rank_fn(S)
        rt = rank_fn(super_T)
        if not rs <= rt:
            raise AssertionError(
                f"monotonicity failed: rank({S!r})={rs} > rank({super_T!r})={rt}"
            )


def assert_partition(
    pos: frozenset[T],
    neg: frozenset[T],
    neu: frozenset[T],
    domain: frozenset[T],
) -> None:
    """Encode I-PTC-02 (disjoint) and I-PTC-03 (cover) in one helper."""
    if pos & neg:
        raise AssertionError(
            f"I-PTC-02 violated: positive ∩ negative = {pos & neg!r}"
        )
    if pos & neu:
        raise AssertionError(
            f"I-PTC-02 violated: positive ∩ neutral = {pos & neu!r}"
        )
    if neg & neu:
        raise AssertionError(
            f"I-PTC-02 violated: negative ∩ neutral = {neg & neu!r}"
        )
    union = pos | neg | neu
    if union != domain:
        raise AssertionError(
            f"I-PTC-03 violated: positive ∪ negative ∪ neutral = {union!r} "
            f"!= domain {domain!r}"
        )
