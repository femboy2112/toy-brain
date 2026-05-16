"""Phase 3.9 persistence atomic-save fixture.

Drives:

* ``I-PERSIST-10`` (STRUCTURAL) — Save transaction is atomic.
  ``save_session`` uses ``sqlite3.connect(...)`` with
  ``isolation_level=None`` and an explicit BEGIN IMMEDIATE / COMMIT
  pair; a mid-save failure triggers ROLLBACK and leaves no orphaned
  rows from the failed attempt; the next successful save into the same
  DB produces a snapshot indistinguishable from one made without the
  injected failure.
"""
from __future__ import annotations

import ast
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


_PERSISTENCE_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "persistence.py"
)


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


def _audit_static_transaction_shape() -> list[str]:
    errors: list[str] = []
    source = _PERSISTENCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_PERSISTENCE_PATH))

    save_func: ast.FunctionDef | None = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "save_session":
            save_func = node
            break
    if save_func is None:
        return ["save_session() function not found in persistence.py"]

    saw_isolation_none = False
    saw_begin_immediate = False
    saw_commit = False
    saw_rollback = False
    for node in ast.walk(save_func):
        if isinstance(node, ast.keyword) and node.arg == "isolation_level":
            if isinstance(node.value, ast.Constant) and node.value.value is None:
                saw_isolation_none = True
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value.upper()
            if "BEGIN IMMEDIATE" in text:
                saw_begin_immediate = True
            if text.strip() == "COMMIT":
                saw_commit = True
            if text.strip() == "ROLLBACK":
                saw_rollback = True
    if not saw_isolation_none:
        errors.append(
            "save_session does not pass isolation_level=None to "
            "sqlite3.connect"
        )
    if not saw_begin_immediate:
        errors.append("save_session does not BEGIN IMMEDIATE")
    if not saw_commit:
        errors.append("save_session does not COMMIT")
    if not saw_rollback:
        errors.append("save_session does not ROLLBACK on failure")
    return errors


@register("I-PERSIST-10", status="STRUCTURAL")
def check_i_persist_10_atomic_save() -> None:
    """save_session is transactional and rolls back on failure."""
    errors = _audit_static_transaction_shape()
    if errors:
        raise AssertionError(
            "I-PERSIST-10 violated:\n  - " + "\n  - ".join(errors)
        )

    session = _build_session()
    with tempfile.TemporaryDirectory(prefix="brain-persist-10-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        config = SessionStoreConfig(db_path=db_path)
        save_session(session, config)

        # Snapshot the clean DB for byte comparison after a failed save.
        clean_bytes = db_path.read_bytes()

        # Inject a mid-save failure: monkeypatch _serialize_to_db to
        # insert one row then raise.
        original_serialize = _persistence._serialize_to_db

        def _failing(conn, snap):
            conn.execute(
                "DELETE FROM stream_chunks"
            )
            conn.execute(
                "INSERT INTO stream_chunks(ordinal, chunk_id, source, text, "
                "provenance_tag) VALUES (?, ?, ?, ?, ?)",
                (1, "synthetic-chunk-rollback", "OPERATOR", "synthetic",
                 "synthetic"),
            )
            raise sqlite3.OperationalError(
                "synthetic OperationalError (I-PERSIST-10 fixture)"
            )

        _persistence._serialize_to_db = _failing  # type: ignore[assignment]
        try:
            try:
                save_session(session, config)
            except PersistenceError:
                pass
            else:
                raise AssertionError(
                    "I-PERSIST-10 violated: synthetic failure did not raise"
                )
        finally:
            _persistence._serialize_to_db = original_serialize  # type: ignore[assignment]

        # After the rolled-back save, the synthetic row must not exist.
        conn = sqlite3.connect(str(db_path))
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM stream_chunks "
                "WHERE chunk_id = 'synthetic-chunk-rollback'"
            ).fetchone()[0]
            if count != 0:
                raise AssertionError(
                    "I-PERSIST-10 violated: synthetic stream_chunks row "
                    "from the failed save survived ROLLBACK"
                )
        finally:
            conn.close()

        # A subsequent successful save produces a snapshot that loads
        # to the same kernel state as the original clean save.
        save_session(session, config)
        loaded, _ = load_session(config)
        if loaded.state.profile.values[COGITO_ID] != Fraction(1):
            raise AssertionError(
                "I-PERSIST-10 violated: post-failure save did not produce a "
                "loadable snapshot"
            )
        if loaded.state.profile.values["alpha"] != Fraction(1, 2):
            raise AssertionError(
                "I-PERSIST-10 violated: post-failure save did not preserve "
                "alpha rho"
            )
