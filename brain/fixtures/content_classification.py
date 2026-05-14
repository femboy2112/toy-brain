"""TOCE Boolean classifier fixture.

Drives: I-TOCE-01..05.

Strategy: enumerate the 16 ``ContentState`` truth-table cells and verify
each catalog assertion against the resulting class.
"""
from __future__ import annotations

from itertools import product

from brain.invariants import register
from brain.toce_core import ContentClass, ContentState, classify_content


def _all_states() -> list[ContentState]:
    return [
        ContentState(available=a, verification_path=v, retrievable=r, operative=o)
        for a, v, r, o in product([False, True], repeat=4)
    ]


@register("I-TOCE-01")
def check_I_TOCE_01() -> None:
    """Classification is independent of ``operative``."""
    by_avr: dict[tuple[bool, bool, bool], ContentClass] = {}
    for s in _all_states():
        key = (s.available, s.verification_path, s.retrievable)
        cls = classify_content(s)
        if key in by_avr:
            assert by_avr[key] == cls, (
                f"classifyContent depends on operative: key={key} got {cls} vs {by_avr[key]}"
            )
        else:
            by_avr[key] = cls


@register("I-TOCE-02")
def check_I_TOCE_02() -> None:
    """available=True ⇒ class ∈ {consciousClear, consciousFuzzy}."""
    valid = {ContentClass.CONSCIOUS_CLEAR, ContentClass.CONSCIOUS_FUZZY}
    for s in _all_states():
        if not s.available:
            continue
        cls = classify_content(s)
        assert cls in valid, f"available=True but class={cls!r}"


@register("I-TOCE-03")
def check_I_TOCE_03() -> None:
    """available=False ⇒ class ∈ {latentRetrievable, unconsciousOperative}."""
    valid = {ContentClass.LATENT_RETRIEVABLE, ContentClass.UNCONSCIOUS_OPERATIVE}
    for s in _all_states():
        if s.available:
            continue
        cls = classify_content(s)
        assert cls in valid, f"available=False but class={cls!r}"


@register("I-TOCE-04")
def check_I_TOCE_04() -> None:
    """consciousClear ⇒ available=True."""
    for s in _all_states():
        if classify_content(s) is ContentClass.CONSCIOUS_CLEAR:
            assert s.available, f"consciousClear but available=False, state={s!r}"


@register("I-TOCE-05")
def check_I_TOCE_05() -> None:
    """consciousFuzzy ⇒ available=True."""
    for s in _all_states():
        if classify_content(s) is ContentClass.CONSCIOUS_FUZZY:
            assert s.available, f"consciousFuzzy but available=False, state={s!r}"
