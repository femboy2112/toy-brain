"""Scenario v1 fixture (Phase 2 v1).

Drives:
  I-RT-08 (REQUIRED) — invariant runner is green after every tick;
    inline ``assert_state_invariants`` raises if violated mid-trajectory.
  I-RT-09 (STRUCTURAL) — every PerceptEvent in the scenario JSON
    constructs successfully (text non-empty + printable).
  I-RT-10 (STRUCTURAL) — ContentRegistry retains text metadata across
    ticks: ``len(registry.texts) >= len(profile.domain) - 1``.
  I-BHV-01 (REQUIRED) — orchestration check: under MockClient seeded
    from ``expected_eval``, the actual mode trace matches
    ``expected_mode``. Per corrigenda C1, this verifies eval→mode→state
    orchestration only — *not* LLM behavior, which is exercised by the
    separate ``python -m brain.scenario run …`` CLI.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from brain.invariants import register
from brain.io_types import PerceptEvent
from brain.llm.client import MockClient
from brain.scenario import REPO_ROOT, load_scenario, run_scenario
from brain.tick import initial_state, tick
from brain.tlica.profile import ContentID
from brain.toce_core import ContentState

SCENARIO_PATH = REPO_ROOT / "scenarios" / "first_scenario_v1.json"


def _seeded_mock(spec) -> MockClient:
    """Build a MockClient whose responses are exactly each tick's
    ``expected_eval`` token in order. The fixture relies on the LLM
    layer to consume one response per tick (the cogito short-circuits
    with no call, and existing MSI members reuse the prior tick's
    cached eval, so each *new* content is one MockClient call).
    """
    responses = [t.expected_eval.name for t in spec.ticks]
    return MockClient(responses)


def _run_once():
    spec = load_scenario(SCENARIO_PATH)
    client = _seeded_mock(spec)
    result = run_scenario(spec, client)
    return spec, result


@register("I-RT-08")
def check_I_RT_08() -> None:
    """Walk the scenario; assert no invariant violation escapes any tick.

    ``brain/tick.py::tick`` calls ``assert_state_invariants`` after each
    tick and raises ValueError on failure. Reaching this assertion with
    a successful result means I-RT-08 held throughout the trajectory.
    """
    spec, result = _run_once()
    # Sanity: we got a record per tick and each one points at a
    # post-tick state that survived assert_state_invariants.
    assert len(result.records) == len(spec.ticks), (
        f"expected {len(spec.ticks)} records, got {len(result.records)}"
    )


@register("I-RT-09", status="STRUCTURAL")
def check_I_RT_09() -> None:
    """Every PerceptEvent in the scenario constructs successfully.

    ``load_scenario`` already runs each PerceptEvent through its
    ``__post_init__`` — if any text were empty or non-printable, this
    fixture would fail at import time. We re-confirm explicitly.
    """
    spec = load_scenario(SCENARIO_PATH)
    for st in spec.ticks:
        assert st.percept.text and st.percept.text.isprintable(), (
            f"PerceptEvent at tick {st.tick} has invalid text"
        )


@register("I-RT-10", status="STRUCTURAL")
def check_I_RT_10() -> None:
    """ContentRegistry accumulates: |texts| >= |domain| - 1."""
    _, result = _run_once()
    final = result.final_state
    assert len(final.registry.texts) >= len(final.profile.domain) - 1, (
        f"registry has {len(final.registry.texts)} texts but profile.domain "
        f"has {len(final.profile.domain)} contents (cogito excluded)"
    )


def _dummy_event(content_id: str, rho: str = "3/5") -> PerceptEvent:
    return PerceptEvent(
        content_id=ContentID(content_id),
        text=f"dummy content for {content_id}",
        content_state=ContentState(
            available=True, verification_path=True, retrievable=True, operative=True
        ),
        initial_rho=Fraction(rho),
    )


@register("I-RT-11", status="STRUCTURAL")
def check_I_RT_11() -> None:
    """tick() with more than one event raises ValueError naming I-RT-11."""
    state = initial_state()
    events = [_dummy_event("a"), _dummy_event("b")]
    try:
        tick(state, events, MockClient([]))
    except ValueError as exc:
        assert "I-RT-11" in str(exc), (
            f"multi-event tick raised but message missing I-RT-11: {exc}"
        )
        return
    raise AssertionError(
        "I-RT-11 violated: tick() did not raise on a 2-event call"
    )


@register("I-RT-12", status="STRUCTURAL")
def check_I_RT_12() -> None:
    """tick() rejects a percept whose content_id is already in profile.domain."""
    state = initial_state()
    # First tick: promote "foo" into the profile.
    state, _ = tick(state, [_dummy_event("foo")], MockClient(["PRESERVE"]))
    assert ContentID("foo") in state.profile.domain
    # Second tick with the same content_id must raise.
    try:
        tick(state, [_dummy_event("foo")], MockClient(["PRESERVE"]))
    except ValueError as exc:
        assert "I-RT-12" in str(exc), (
            f"duplicate-content tick raised but message missing I-RT-12: {exc}"
        )
        return
    raise AssertionError(
        "I-RT-12 violated: tick() did not raise on duplicate content_id"
    )


@register("I-BHV-01")
def check_I_BHV_01() -> None:
    """Mode trace under seeded MockClient matches expected_mode sequence.

    Per corrigenda C1: this verifies orchestration (eval→mode→state-update)
    under controlled inputs, not LLM behavior.
    """
    spec, result = _run_once()
    expected = tuple(t.expected_mode for t in spec.ticks)
    assert result.actual_modes == expected, (
        f"mode trace mismatch: actual={[m.name for m in result.actual_modes]} "
        f"expected={[m.name for m in expected]}"
    )
