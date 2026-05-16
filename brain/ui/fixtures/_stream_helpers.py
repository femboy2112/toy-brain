"""Deterministic helpers for the Phase 3.8 Operator Stream Interaction fixtures.

Drives the I-UISTRM-* row family. The helpers in this module construct a
minimal :class:`brain.ui.session.OperatorSession` over a deterministic
:class:`brain.tick.BrainState` and produce a known-good chunk_id /
candidate_id sequence for each fixture to reuse. None of the helpers
mutate global registry state, perform I/O, or import ``brain.llm``,
``brain.tlica`` runtime mutation surfaces, or ``curses``.
"""
from __future__ import annotations

from fractions import Fraction
from types import MappingProxyType

from brain.io_types import ContentRegistry
from brain.tick import BrainState
from brain.tlica.builders import (
    make_msi,
    make_profile_with_cogito,
    make_ptcns,
)
from brain.tlica.profile import COGITO_ID
from brain.tlica.ptcns import ConsistencyEval
from brain.ui.session import OperatorSession


def make_state() -> BrainState:
    profile = make_profile_with_cogito({
        COGITO_ID: 1,
        "alpha": Fraction(3, 4),
    })
    msi = make_msi(
        profile,
        contents={COGITO_ID, "alpha"},
        threshold=Fraction(1, 2),
    )
    ptcns = make_ptcns(
        msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "alpha": ConsistencyEval.PRESERVE,
        },
    )
    registry = ContentRegistry(
        texts=MappingProxyType({"alpha": "alpha text"})
    )
    return BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)


def state_identity(state: BrainState) -> tuple:
    return (
        id(state),
        id(state.profile),
        id(state.profile.values),
        id(state.msi),
        id(state.msi.contents),
        id(state.ptcns),
        id(state.ptcns.eval_map),
        id(state.registry),
        id(state.registry.texts),
        repr(state),
    )


def make_session() -> OperatorSession:
    return OperatorSession(state=make_state())


def session_kernel_identity(session: OperatorSession) -> tuple:
    return (
        state_identity(session.state),
        session.tick_counter,
        id(session.latest_tick),
        len(session.event_queue),
    )
