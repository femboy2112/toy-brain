"""Fixtures for Phase 3.2 output impulse and echo rows."""
from __future__ import annotations

from dataclasses import fields
from fractions import Fraction

from brain.development.output import (
    OutputEcho,
    OutputHistory,
    OutputImpulse,
    OutputProvenance,
    append_output_impulse,
    echo_output_impulse,
)
from brain.development.stream import FrameSourceKind
from brain.invariants import register
from brain.tick import initial_state
from brain.tlica.profile import COGITO_ID


def _provenance(
    kind: FrameSourceKind = FrameSourceKind.GENERATED,
    confidence: Fraction = Fraction(4, 5),
) -> OutputProvenance:
    return OutputProvenance(
        source_kind=kind,
        confidence=confidence,
        trace_event_ids=("output:trace-1",),
    )


def _impulse() -> OutputImpulse:
    return OutputImpulse(
        impulse_id="out:impulse-1",
        text="pulse",
        provenance=_provenance(),
    )


def _history_with_impulse() -> tuple[OutputHistory, OutputImpulse, OutputHistory]:
    before = OutputHistory()
    impulse = _impulse()
    after = append_output_impulse(before, impulse)
    return before, impulse, after


def _assert_i_out_01_rejects(call: object) -> None:
    try:
        assert callable(call)
        call()
    except ValueError as exc:
        assert "I-OUT-01" in str(exc)
    else:
        raise AssertionError("I-OUT-01 violated: invalid output impulse passed")


def _assert_i_out_02_rejects(call: object) -> None:
    try:
        assert callable(call)
        call()
    except ValueError as exc:
        assert "I-OUT-02" in str(exc)
    else:
        raise AssertionError("I-OUT-02 violated: invalid output provenance passed")


@register("I-OUT-01", status="STRUCTURAL")
def check_output_impulse_is_bounded_printable_event() -> None:
    impulse = _impulse()
    assert impulse.impulse_id == "out:impulse-1"
    assert impulse.text == "pulse"
    assert impulse.target_id is None

    _assert_i_out_01_rejects(
        lambda: OutputImpulse(
            impulse_id="out:empty-text",
            text="",
            provenance=_provenance(),
        )
    )
    _assert_i_out_01_rejects(
        lambda: OutputImpulse(
            impulse_id="out:reserved-target",
            text="pulse",
            provenance=_provenance(),
            target_id=COGITO_ID,
        )
    )
    _assert_i_out_01_rejects(
        lambda: OutputImpulse(
            impulse_id="",
            text="pulse",
            provenance=_provenance(),
        )
    )
    _assert_i_out_01_rejects(
        lambda: OutputImpulse(
            impulse_id="out:nonprintable",
            text="bad\ntext",
            provenance=_provenance(),
        )
    )


@register("I-OUT-02", status="STRUCTURAL")
def check_output_provenance_reuses_source_kinds() -> None:
    provenance = _provenance(FrameSourceKind.PROBE_ECHO, Fraction(1, 2))
    assert isinstance(provenance.source_kind, FrameSourceKind)
    assert provenance.confidence == Fraction(1, 2)
    assert isinstance(provenance.confidence, Fraction)
    assert Fraction(0) <= provenance.confidence <= Fraction(1)
    assert "OUTPUT_ECHO" not in {kind.name for kind in FrameSourceKind}

    _assert_i_out_02_rejects(
        lambda: OutputProvenance(
            source_kind=FrameSourceKind.GENERATED,
            confidence=Fraction(4, 3),
        )
    )
    _assert_i_out_02_rejects(
        lambda: OutputProvenance(
            source_kind=FrameSourceKind.GENERATED,
            confidence=0.5,  # type: ignore[arg-type]
        )
    )


@register("I-OUT-03", status="REQUIRED")
def check_output_impulses_record_deterministically() -> None:
    before, impulse, after = _history_with_impulse()
    assert before is not after
    assert before.impulses == ()
    assert after.impulses == (impulse,)
    assert after.impulses[0].provenance is impulse.provenance
    assert after.echoes == ()
    assert after.output_patterns == before.output_patterns
    assert after.token_candidates == before.token_candidates
    assert after.learned_tokens == before.learned_tokens


@register("I-OUT-04", status="REQUIRED")
def check_output_echo_enters_history_but_not_agency() -> None:
    _, impulse, with_impulse = _history_with_impulse()
    with_echo = echo_output_impulse(
        with_impulse,
        impulse_id=impulse.impulse_id,
        echo_id="out:echo-1",
    )
    assert with_echo is not with_impulse
    assert with_echo.impulses == with_impulse.impulses
    assert len(with_echo.echoes) == 1
    echo = with_echo.echoes[0]
    assert echo.impulse is impulse
    assert echo.provenance is impulse.provenance

    forbidden = {
        "act",
        "action",
        "agency",
        "agency_witness",
        "mode",
        "mode_op",
        "percept_event",
        "pce",
        "tick",
        "preserve",
    }
    for obj in (impulse, echo, with_echo):
        names = {field.name for field in fields(obj)}
        assert not (names & forbidden), (
            f"I-OUT-04 violated: {type(obj).__name__} exposes {names & forbidden}"
        )


@register("I-OUT-05", status="STRUCTURAL")
def check_output_echo_exposes_no_agency_handles() -> None:
    _, impulse, with_impulse = _history_with_impulse()
    with_echo = echo_output_impulse(
        with_impulse,
        impulse_id=impulse.impulse_id,
        echo_id="out:echo-1",
    )

    forbidden = {
        "Act",
        "ModeOp",
        "AgencyWitness",
        "PerceptEvent",
        "feasibleProjectedPCE",
        "feasible_projected_pce",
        "state_mutation",
    }
    for obj in (with_echo.echoes[0], with_echo):
        names = {field.name for field in fields(obj)}
        assert not (names & {name.lower() for name in forbidden})
        for name in forbidden:
            assert not hasattr(obj, name), (
                f"I-OUT-05 violated: {type(obj).__name__} exposes {name}"
            )


@register("I-OUT-12", status="REQUIRED")
def check_output_history_does_not_bypass_tick_boundary() -> None:
    state = initial_state()
    before_profile = state.profile
    before_msi = state.msi
    before_ptcns = state.ptcns
    before_registry = state.registry

    _, impulse, with_impulse = _history_with_impulse()
    with_echo = echo_output_impulse(
        with_impulse,
        impulse_id=impulse.impulse_id,
        echo_id="out:echo-1",
    )
    assert with_echo.echoes

    assert state.profile is before_profile
    assert state.msi is before_msi
    assert state.ptcns is before_ptcns
    assert state.registry is before_registry
    assert impulse.impulse_id not in state.profile.domain
    assert impulse.impulse_id not in state.registry.texts
