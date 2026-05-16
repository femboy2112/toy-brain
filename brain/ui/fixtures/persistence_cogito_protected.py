"""Phase 3.9 persistence COGITO_ID protection fixture.

Drives:

* ``I-PERSIST-04`` (REQUIRED) — ``COGITO_ID`` cannot be overwritten by
  persisted data. A profile_values row with ``content_id = COGITO_ID``
  and ``rho != 1``, a missing ``msi_contents`` ``COGITO_ID`` row, or a
  ``ptcns_eval`` row mapping ``COGITO_ID`` to a non-``PRESERVE``
  evaluation raises :class:`PersistenceError` on load; save of a
  session with ``COGITO_ID`` at value ``1`` round-trips exactly.
"""
from __future__ import annotations

import pathlib
import sqlite3
import tempfile
from fractions import Fraction
from types import MappingProxyType

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


def _expect_persistence_error(fn, label: str) -> None:
    try:
        fn()
    except PersistenceError:
        return
    except BaseException as exc:  # noqa: BLE001
        raise AssertionError(
            f"{label}: expected PersistenceError, got "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    raise AssertionError(
        f"{label}: load_session unexpectedly succeeded"
    )


@register("I-PERSIST-04", status="REQUIRED")
def check_i_persist_04_cogito_protected() -> None:
    """Persisted COGITO_ID rows cannot overwrite the reserved sentinel."""
    session = _build_session()
    with tempfile.TemporaryDirectory(prefix="brain-persist-04-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        config = SessionStoreConfig(db_path=db_path)

        # Baseline: clean save + load round-trips COGITO_ID at value 1.
        save_session(session, config)
        loaded, _ = load_session(config)
        if loaded.state.profile.values[COGITO_ID] != Fraction(1):
            raise AssertionError(
                "I-PERSIST-04 baseline: loaded COGITO rho != 1"
            )
        if COGITO_ID not in loaded.state.msi.contents:
            raise AssertionError(
                "I-PERSIST-04 baseline: loaded msi.contents missing COGITO_ID"
            )
        if loaded.state.ptcns.eval_map[COGITO_ID] is not ConsistencyEval.PRESERVE:
            raise AssertionError(
                "I-PERSIST-04 baseline: loaded ptcns.eval_map[COGITO_ID] != "
                "PRESERVE"
            )

        # 1. Corrupt the COGITO profile row to a non-1 value.
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute(
                "UPDATE profile_values SET rho_num = 1, rho_den = 2 "
                "WHERE content_id = ?",
                (COGITO_ID,),
            )
            conn.commit()
        finally:
            conn.close()
        _expect_persistence_error(
            lambda: load_session(config),
            "I-PERSIST-04 (cogito_rho_overwrite)",
        )

        # 2. Drop the COGITO msi_contents row (msi membership required).
        db_path.unlink()
        save_session(session, config)
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute(
                "DELETE FROM msi_contents WHERE content_id = ?", (COGITO_ID,)
            )
            conn.commit()
        finally:
            conn.close()
        _expect_persistence_error(
            lambda: load_session(config),
            "I-PERSIST-04 (cogito_msi_missing)",
        )

        # 3. Map COGITO_ID to a non-PRESERVE eval.
        db_path.unlink()
        save_session(session, config)
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute(
                "UPDATE ptcns_eval SET eval = 'NEUTRAL' WHERE content_id = ?",
                (COGITO_ID,),
            )
            conn.commit()
        finally:
            conn.close()
        _expect_persistence_error(
            lambda: load_session(config),
            "I-PERSIST-04 (cogito_eval_overwrite)",
        )

        # 4. Drop the COGITO profile row entirely.
        db_path.unlink()
        save_session(session, config)
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                "DELETE FROM ptcns_eval WHERE content_id = ?", (COGITO_ID,)
            )
            conn.execute(
                "DELETE FROM msi_contents WHERE content_id = ?", (COGITO_ID,)
            )
            conn.execute(
                "DELETE FROM profile_values WHERE content_id = ?", (COGITO_ID,)
            )
            conn.commit()
        finally:
            conn.close()
        _expect_persistence_error(
            lambda: load_session(config),
            "I-PERSIST-04 (cogito_absent)",
        )
