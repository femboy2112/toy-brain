"""Phase 3.9 persistence session-resource-audit fixture.

Drives:

* ``I-PERSIST-11`` (STRUCTURAL) — ``OperatorSession`` is resource-free
  with ``SessionStoreConfig``: the optional config field carries only
  bounded primitives (``pathlib.Path``, ``int``, ``str``); no
  ``OperatorSession`` or ``SessionStoreConfig`` field holds an
  ``sqlite3.Connection``, ``sqlite3.Cursor``, subprocess handle,
  socket, file object, callable, curses object, or LLM client.

* ``I-PERSIST-14`` (STRUCTURAL) — No long-lived ``sqlite3.Connection``
  on ``OperatorSession``: the persistence module declares no
  module-level connection, no class field of type
  ``sqlite3.Connection``, and no function returns a
  ``sqlite3.Connection`` to an external caller; no
  ``OperatorSession`` field stores an open connection.
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
    SessionStoreConfig,
    save_session,
)
from brain.ui.session import _ALLOWED_SESSION_ATTRS, OperatorSession


_PERSISTENCE_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "persistence.py"
)


def _build_session_with_config(db_path: pathlib.Path) -> OperatorSession:
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
    return OperatorSession(
        state=state,
        session_store_config=SessionStoreConfig(db_path=db_path),
    )


@register("I-PERSIST-11", status="STRUCTURAL")
def check_i_persist_11_session_resource_free() -> None:
    """OperatorSession with SessionStoreConfig holds no unsafe resource."""
    if "session_store_config" not in _ALLOWED_SESSION_ATTRS:
        raise AssertionError(
            "I-PERSIST-11 violated: 'session_store_config' is not in "
            "_ALLOWED_SESSION_ATTRS"
        )

    with tempfile.TemporaryDirectory(prefix="brain-persist-11-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        session = _build_session_with_config(db_path)
        if not isinstance(session.session_store_config, SessionStoreConfig):
            raise AssertionError(
                "I-PERSIST-11 violated: session_store_config attribute is "
                f"not a SessionStoreConfig (got "
                f"{type(session.session_store_config).__name__})"
            )

        config = session.session_store_config
        for field_name in ("db_path", "schema_version", "catalog_version"):
            value = getattr(config, field_name)
            if isinstance(value, sqlite3.Connection):
                raise AssertionError(
                    f"I-PERSIST-11 violated: SessionStoreConfig.{field_name} "
                    "is a sqlite3.Connection"
                )
            if isinstance(value, sqlite3.Cursor):
                raise AssertionError(
                    f"I-PERSIST-11 violated: SessionStoreConfig.{field_name} "
                    "is a sqlite3.Cursor"
                )
            if callable(value):
                raise AssertionError(
                    f"I-PERSIST-11 violated: SessionStoreConfig.{field_name} "
                    "is callable"
                )

        if not isinstance(config.db_path, pathlib.Path):
            raise AssertionError(
                f"I-PERSIST-11 violated: SessionStoreConfig.db_path is "
                f"{type(config.db_path).__name__}, expected pathlib.Path"
            )
        if not isinstance(config.schema_version, int):
            raise AssertionError(
                f"I-PERSIST-11 violated: SessionStoreConfig.schema_version "
                f"is {type(config.schema_version).__name__}, expected int"
            )
        if not isinstance(config.catalog_version, str):
            raise AssertionError(
                f"I-PERSIST-11 violated: SessionStoreConfig.catalog_version "
                f"is {type(config.catalog_version).__name__}, expected str"
            )

        # session._assert_no_unsafe_resources is called by __post_init__
        # and would have already raised; re-run to be explicit.
        session._assert_no_unsafe_resources()

        # A save through the config does not place a Connection on the
        # session.
        save_session(session, config)
        if hasattr(session, "_conn"):
            raise AssertionError(
                "I-PERSIST-11 violated: session gained a _conn attribute "
                "after save"
            )


@register("I-PERSIST-14", status="STRUCTURAL")
def check_i_persist_14_no_long_lived_connection() -> None:
    """No long-lived sqlite3.Connection lives on OperatorSession."""
    source = _PERSISTENCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_PERSISTENCE_PATH))

    errors: list[str] = []

    # Module-level: no `name = sqlite3.connect(...)` or class field of
    # type sqlite3.Connection.
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    value = node.value
                    if (
                        isinstance(value, ast.Call)
                        and isinstance(value.func, ast.Attribute)
                        and isinstance(value.func.value, ast.Name)
                        and value.func.value.id == "sqlite3"
                        and value.func.attr == "connect"
                    ):
                        errors.append(
                            f"module-level sqlite3.connect at line "
                            f"{node.lineno}"
                        )
        if isinstance(node, ast.AnnAssign):
            anno = node.annotation
            if isinstance(anno, ast.Attribute):
                if (
                    isinstance(anno.value, ast.Name)
                    and anno.value.id == "sqlite3"
                    and anno.attr == "Connection"
                ):
                    errors.append(
                        f"module-level sqlite3.Connection annotation at line "
                        f"{node.lineno}"
                    )

    # Class fields: no sqlite3.Connection-typed annotation in any
    # dataclass defined in the persistence module.
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign):
                    anno = stmt.annotation
                    if isinstance(anno, ast.Attribute):
                        if (
                            isinstance(anno.value, ast.Name)
                            and anno.value.id == "sqlite3"
                            and anno.attr in {"Connection", "Cursor"}
                        ):
                            errors.append(
                                f"class field of type sqlite3.{anno.attr} on "
                                f"{node.name} at line {stmt.lineno}"
                            )

    # Function return types: no top-level function returns sqlite3.Connection.
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            ret = node.returns
            if isinstance(ret, ast.Attribute):
                if (
                    isinstance(ret.value, ast.Name)
                    and ret.value.id == "sqlite3"
                    and ret.attr in {"Connection", "Cursor"}
                ):
                    errors.append(
                        f"top-level function {node.name!r} returns "
                        f"sqlite3.{ret.attr} (no long-lived connections "
                        "may leak to callers)"
                    )

    # The OperatorSession field set declared in _ALLOWED_SESSION_ATTRS
    # does not include anything Connection-shaped. Verify by attribute
    # name: no allowed attr is "conn" / "connection" / "cursor".
    for attr in _ALLOWED_SESSION_ATTRS:
        if attr.lower() in {"conn", "connection", "cursor", "db_conn"}:
            errors.append(
                f"OperatorSession permits a connection-named attribute: "
                f"{attr!r}"
            )

    # Behavioural check: after a save, no OperatorSession field is a
    # sqlite3.Connection or sqlite3.Cursor.
    with tempfile.TemporaryDirectory(prefix="brain-persist-14-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        profile = make_profile_with_cogito({COGITO_ID: 1, "alpha": Fraction(1, 2)})
        msi = make_msi(profile, contents={COGITO_ID, "alpha"}, threshold=Fraction(1, 3))
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
        state = BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)
        session = OperatorSession(
            state=state,
            session_store_config=SessionStoreConfig(db_path=db_path),
        )
        save_session(session, session.session_store_config)
        for attr in _ALLOWED_SESSION_ATTRS:
            value = getattr(session, attr)
            if isinstance(value, sqlite3.Connection):
                errors.append(
                    f"OperatorSession.{attr} is a sqlite3.Connection "
                    "after save"
                )
            if isinstance(value, sqlite3.Cursor):
                errors.append(
                    f"OperatorSession.{attr} is a sqlite3.Cursor after save"
                )

    if errors:
        raise AssertionError(
            "I-PERSIST-14 violated:\n  - " + "\n  - ".join(errors)
        )

    # Reference _persistence to keep the import live (avoids a stray F401).
    _ = _persistence
