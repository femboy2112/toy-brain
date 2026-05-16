"""Phase 3.9 persistence load-runs-invariants fixture.

Drives:

* ``I-PERSIST-06`` (REQUIRED) — Load runs invariant assertions before
  returning a candidate session: ``load_session`` invokes
  :func:`brain.tick.assert_state_invariants` on the assembled candidate
  ``BrainState``; if the assertion raises, ``load_session`` raises
  :class:`PersistenceError` and returns no candidate session.
"""
from __future__ import annotations

import pathlib
import tempfile
from fractions import Fraction
from types import MappingProxyType

from brain import tick as _tick
from brain.invariants import register
from brain.io_types import ContentRegistry
from brain.tick import BrainState
from brain.tlica.builders import (
    make_msi,
    make_profile_with_cogito,
    make_ptcns,
)
from brain.tlica.profile import COGITO_ID
from brain.tlica.ptcns import ConsistencyEval
from brain.ui import persistence as _persistence
from brain.ui.persistence import (
    PersistenceError,
    SessionStoreConfig,
    load_session,
    save_session,
)
from brain.ui.session import OperatorSession


def _build_session() -> OperatorSession:
    profile = make_profile_with_cogito(
        {COGITO_ID: 1, "alpha": Fraction(1, 2)}
    )
    msi = make_msi(profile, contents={COGITO_ID, "alpha"}, threshold=Fraction(1, 3))
    ptcns = make_ptcns(
        msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "alpha": ConsistencyEval.PRESERVE,
        },
    )
    registry = ContentRegistry(texts=MappingProxyType({"alpha": "alpha text"}))
    state = BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)
    return OperatorSession(state=state)


@register("I-PERSIST-06", status="REQUIRED")
def check_i_persist_06_load_runs_invariants() -> None:
    """Patch assert_state_invariants and confirm load_session calls it."""
    session = _build_session()
    call_count = {"n": 0}
    original = _persistence.assert_state_invariants

    def _counting(*args, **kwargs):
        call_count["n"] += 1
        return original(*args, **kwargs)

    # Also patch the alias on brain.tick so any code path reaching it
    # through the source module is observed.
    tick_original = _tick.assert_state_invariants

    _persistence.assert_state_invariants = _counting  # type: ignore[assignment]

    try:
        with tempfile.TemporaryDirectory(prefix="brain-persist-06-") as td:
            db_path = pathlib.Path(td) / "session.sqlite3"
            config = SessionStoreConfig(db_path=db_path)
            save_session(session, config)
            load_session(config)
            if call_count["n"] < 1:
                raise AssertionError(
                    "I-PERSIST-06 violated: load_session did not call "
                    "assert_state_invariants on the candidate state"
                )

            # Now patch the assert to raise; verify PersistenceError.
            def _raising(*_args, **_kwargs):
                raise ValueError(
                    "synthetic invariant failure (I-PERSIST-06 fixture)"
                )

            _persistence.assert_state_invariants = _raising  # type: ignore[assignment]
            try:
                load_session(config)
            except PersistenceError:
                pass
            else:
                raise AssertionError(
                    "I-PERSIST-06 violated: load_session did not raise "
                    "PersistenceError when assert_state_invariants failed"
                )
    finally:
        _persistence.assert_state_invariants = original  # type: ignore[assignment]
        # tick_original is identical to original; reset for hygiene.
        _tick.assert_state_invariants = tick_original  # type: ignore[assignment]
