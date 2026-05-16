"""Phase 3.9 persistence failed-save fixture.

Drives:

* ``I-PERSIST-07`` (REQUIRED) — Failed save preserves the live
  session. A mid-save IntegrityError / OperationalError / DatabaseError
  rolls back the transaction; the live :class:`OperatorSession` is
  unchanged; a subsequent successful save into the same DB produces a
  clean v1-shaped snapshot.
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
        {COGITO_ID: 1, "alpha": Fraction(3, 7), "beta": Fraction(11, 13)}
    )
    msi = make_msi(profile, contents={COGITO_ID, "alpha"}, threshold=Fraction(1, 3))
    ptcns = make_ptcns(
        msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "alpha": ConsistencyEval.PRESERVE,
            "beta": ConsistencyEval.NEUTRAL,
        },
    )
    registry = ContentRegistry(
        texts=MappingProxyType({"alpha": "alpha text", "beta": "beta text"})
    )
    state = BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)
    return OperatorSession(state=state, tick_counter=5)


@register("I-PERSIST-07", status="REQUIRED")
def check_i_persist_07_failed_save_preserves_session() -> None:
    """A mid-save failure rolls back and leaves the live session intact."""
    session = _build_session()
    snapshot_before = (
        session.state.profile.values[COGITO_ID],
        session.state.profile.values["alpha"],
        session.state.profile.values["beta"],
        session.state.msi.threshold,
        session.tick_counter,
        session.state is session.state,
    )

    with tempfile.TemporaryDirectory(prefix="brain-persist-07-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        config = SessionStoreConfig(db_path=db_path)

        # Inject a mid-save failure by patching _serialize_to_db.
        original_serialize = _persistence._serialize_to_db

        def _failing_serialize(conn, snap):
            # Insert a few rows so a partial state would be visible if
            # rollback failed; then raise IntegrityError mid-transaction.
            conn.execute(
                "INSERT INTO profile_values(content_id, rho_num, rho_den) "
                "VALUES (?, ?, ?)",
                ("alpha", 3, 7),
            )
            raise sqlite3.IntegrityError(
                "synthetic IntegrityError (I-PERSIST-07 fixture)"
            )

        _persistence._serialize_to_db = _failing_serialize  # type: ignore[assignment]
        try:
            try:
                save_session(session, config)
            except PersistenceError:
                pass
            else:
                raise AssertionError(
                    "I-PERSIST-07 violated: save_session did not raise on "
                    "synthetic IntegrityError"
                )
        finally:
            _persistence._serialize_to_db = original_serialize  # type: ignore[assignment]

        # Live session unchanged.
        snapshot_after = (
            session.state.profile.values[COGITO_ID],
            session.state.profile.values["alpha"],
            session.state.profile.values["beta"],
            session.state.msi.threshold,
            session.tick_counter,
            session.state is session.state,
        )
        if snapshot_before != snapshot_after:
            raise AssertionError(
                f"I-PERSIST-07 violated: live session changed across "
                f"failed save: {snapshot_before!r} -> {snapshot_after!r}"
            )

        # DB rolled back: the failed transaction left the file either
        # absent or with empty schema-only state. A subsequent
        # successful save produces a clean snapshot.
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            try:
                # Profile rows from the failed attempt must not survive
                # the rollback.
                count = conn.execute(
                    "SELECT COUNT(*) FROM profile_values "
                    "WHERE content_id = 'alpha' AND rho_num = 3 AND rho_den = 7"
                ).fetchone()[0]
                if count != 0:
                    raise AssertionError(
                        "I-PERSIST-07 violated: orphan profile_values row "
                        "from the failed save survived rollback"
                    )
            finally:
                conn.close()

        save_session(session, config)
        loaded, _ = load_session(config)
        if loaded.state.profile.values[COGITO_ID] != Fraction(1):
            raise AssertionError(
                "I-PERSIST-07 violated: post-failure save did not produce a "
                "clean snapshot"
            )
        if loaded.state.profile.values["alpha"] != Fraction(3, 7):
            raise AssertionError(
                "I-PERSIST-07 violated: post-failure save did not preserve "
                "alpha rho"
            )
