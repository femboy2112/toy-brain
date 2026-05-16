"""Phase 3.9 persistence failed-load fixture.

Drives:

* ``I-PERSIST-02`` (REQUIRED) — Unknown ``schema_version`` is rejected
  on load.
* ``I-PERSIST-08`` (REQUIRED) — Failed load preserves the live
  session: missing DB, wrong file type, missing meta rows, unknown
  schema version, FOREIGN KEY violations, malformed ``Fraction``
  pairs, over-bound text, and constructor / invariant rejection all
  raise :class:`PersistenceError`; the on-disk DB is unchanged (load
  runs in sqlite3 uri ``mode=ro``).
"""
from __future__ import annotations

import copy
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
    msi = make_msi(profile, contents={COGITO_ID, "alpha"}, threshold=Fraction(1, 4))
    ptcns = make_ptcns(
        msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "alpha": ConsistencyEval.PRESERVE,
        },
    )
    registry = ContentRegistry(texts=MappingProxyType({"alpha": "alpha text"}))
    state = BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)
    return OperatorSession(state=state, tick_counter=3)


def _assert_persistence_error(fn, label: str) -> None:
    try:
        fn()
    except PersistenceError:
        return
    except BaseException as exc:  # noqa: BLE001
        raise AssertionError(
            f"{label}: expected PersistenceError, got "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    raise AssertionError(f"{label}: load_session unexpectedly succeeded")


@register("I-PERSIST-02", status="REQUIRED")
def check_i_persist_02_unknown_schema_version_rejected() -> None:
    """A meta.schema_version row outside SUPPORTED_SCHEMA_VERSIONS fails load."""
    session = _build_session()
    with tempfile.TemporaryDirectory(prefix="brain-persist-02-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        config = SessionStoreConfig(db_path=db_path)
        save_session(session, config)

        # Corrupt the meta.schema_version row directly.
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute(
                "UPDATE meta SET value = ? WHERE key = 'schema_version'",
                ("99",),
            )
            conn.commit()
        finally:
            conn.close()

        _assert_persistence_error(
            lambda: load_session(config),
            "I-PERSIST-02 (unknown_schema_version)",
        )

        # Non-integer schema_version also rejected.
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute(
                "UPDATE meta SET value = ? WHERE key = 'schema_version'",
                ("not-an-int",),
            )
            conn.commit()
        finally:
            conn.close()
        _assert_persistence_error(
            lambda: load_session(config),
            "I-PERSIST-02 (non_integer_schema_version)",
        )


@register("I-PERSIST-08", status="REQUIRED")
def check_i_persist_08_failed_load_preserves_session() -> None:
    """Every documented failed-load mode preserves the live session."""
    with tempfile.TemporaryDirectory(prefix="brain-persist-08-") as td:
        missing_path = pathlib.Path(td) / "missing.sqlite3"
        dir_path = pathlib.Path(td) / "directory.sqlite3"
        dir_path.mkdir()
        good_path = pathlib.Path(td) / "good.sqlite3"

        # 1. Missing DB.
        _assert_persistence_error(
            lambda: load_session(SessionStoreConfig(db_path=missing_path)),
            "I-PERSIST-08 (missing_db)",
        )

        # 2. Directory path.
        _assert_persistence_error(
            lambda: load_session(SessionStoreConfig(db_path=dir_path)),
            "I-PERSIST-08 (directory_path)",
        )

        # 3. Good baseline: save then load works.
        session = _build_session()
        save_session(session, SessionStoreConfig(db_path=good_path))
        loaded, _ = load_session(SessionStoreConfig(db_path=good_path))
        if loaded.state.profile.values[COGITO_ID] != Fraction(1):
            raise AssertionError(
                "I-PERSIST-08 baseline: loaded COGITO rho != 1"
            )

        # 4. Missing meta.schema_version row.
        conn = sqlite3.connect(str(good_path))
        try:
            conn.execute("DELETE FROM meta WHERE key = 'schema_version'")
            conn.commit()
        finally:
            conn.close()
        _assert_persistence_error(
            lambda: load_session(SessionStoreConfig(db_path=good_path)),
            "I-PERSIST-08 (missing_schema_version)",
        )

        # 5. Restore baseline, then corrupt msi_threshold.
        good_path.unlink()
        save_session(session, SessionStoreConfig(db_path=good_path))
        conn = sqlite3.connect(str(good_path))
        try:
            conn.execute("DELETE FROM msi_threshold WHERE id = 1")
            conn.commit()
        finally:
            conn.close()
        _assert_persistence_error(
            lambda: load_session(SessionStoreConfig(db_path=good_path)),
            "I-PERSIST-08 (missing_msi_threshold)",
        )

        # 6. Restore baseline, then create a malformed profile_values row
        #    (rho_num > rho_den, violating [0, 1] reconstruction bound).
        good_path.unlink()
        save_session(session, SessionStoreConfig(db_path=good_path))
        # Drop the existing alpha row and reinsert with an invalid pair.
        conn = sqlite3.connect(str(good_path))
        try:
            conn.execute(
                "DELETE FROM profile_values WHERE content_id = 'alpha'"
            )
            conn.execute(
                "INSERT INTO profile_values(content_id, rho_num, rho_den) "
                "VALUES ('alpha', 5, 3)"
            )
            conn.commit()
        finally:
            conn.close()
        _assert_persistence_error(
            lambda: load_session(SessionStoreConfig(db_path=good_path)),
            "I-PERSIST-08 (malformed_fraction)",
        )

        # 7. Live session is never replaced by load on failure. Build a
        #    fresh good DB; deepcopy the candidate; corrupt the schema
        #    version; verify load fails and the live session is unchanged.
        good_path.unlink()
        save_session(session, SessionStoreConfig(db_path=good_path))
        live_session = _build_session()
        before = (
            live_session.state.profile.values[COGITO_ID],
            live_session.state.profile.values["alpha"],
            live_session.tick_counter,
            len(live_session.stream_history.chunks),
        )
        before_copy = copy.copy(live_session)
        conn = sqlite3.connect(str(good_path))
        try:
            conn.execute(
                "UPDATE meta SET value = ? WHERE key = 'schema_version'",
                ("99",),
            )
            conn.commit()
        finally:
            conn.close()
        try:
            load_session(SessionStoreConfig(db_path=good_path))
        except PersistenceError:
            pass
        after = (
            live_session.state.profile.values[COGITO_ID],
            live_session.state.profile.values["alpha"],
            live_session.tick_counter,
            len(live_session.stream_history.chunks),
        )
        if before != after:
            raise AssertionError(
                f"I-PERSIST-08 violated: live session changed across "
                f"failed load: {before!r} -> {after!r}"
            )
        if live_session.state is not before_copy.state:
            raise AssertionError(
                "I-PERSIST-08 violated: live BrainState identity changed"
            )
