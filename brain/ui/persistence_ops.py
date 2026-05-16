"""Phase 3.10a Operational Hardening — typed report records and helpers.

This module exposes:

* :class:`SessionStatusReport`, :class:`DbStatusReport`,
  :class:`DbVerifyReport`, :class:`DbBackupReport` — frozen / slotted
  typed report records with ``__post_init__`` bound enforcement.
* :func:`session_status`, :func:`db_status`, :func:`db_verify`,
  :func:`db_backup` — the four Phase 3.10a operational helpers.
* :data:`OPS_REPORT_TEXT_MAX_LEN` (= 256) bounded string cap and
  :data:`DB_BACKUP_FORBIDDEN_SCHEMES` URI rejection set.

Catalog rows driven from here (Phase 3.10a):

* ``I-OPSHARDEN-01`` (REQUIRED) — ``/session-status`` is read-only
  and bounded.
* ``I-OPSHARDEN-02`` (REQUIRED) — ``/db-status`` is read-only
  ``mode=ro`` and bounded.
* ``I-OPSHARDEN-03`` (REQUIRED) — ``/db-verify`` reuses
  :func:`brain.ui.persistence.load_session` and DROPS the candidate.
* ``I-OPSHARDEN-04`` (REQUIRED) — ``/db-verify`` failure preserves
  the live session.
* ``I-OPSHARDEN-05`` (REQUIRED) — ``/db-backup`` uses
  ``sqlite3.Connection.backup()`` (page-faithful).
* ``I-OPSHARDEN-06`` (REQUIRED) — ``/db-backup`` refuses to overwrite
  without ``--force``.
* ``I-OPSHARDEN-07`` (REQUIRED) — ``/db-backup`` refuses URI-scheme
  destinations.
* ``I-OPSHARDEN-08`` (REQUIRED) — ``/db-backup`` never modifies the
  source DB.
* ``I-OPSHARDEN-10`` (STRUCTURAL) — source connection ``mode=ro``
  during backup.
* ``I-OPSHARDEN-11`` (STRUCTURAL) — Phase 3.10a defensive
  autosave-absent audit.
* ``I-OPSHARDEN-12`` (STRUCTURAL) — module static audit.
* ``I-OPSHARDEN-13`` (STRUCTURAL) — session resource audit.

Hard boundaries pinned by
``PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_CORRIGENDA.md`` and
``PHASE3_10_OPS_OBSERVABILITY_CATALOG_PATCH_PLAN.md``:

* SQLite via the standard-library ``sqlite3`` module only — no
  ``pickle`` / ``shelve`` / ``marshal`` / ``dill`` / ``cloudpickle``
  / ``joblib`` / ``subprocess`` / ``socket`` / ``urllib`` / ``http``
  / ``requests`` / ``curses`` / ``brain.tick`` / ``brain.tlica``
  internals beyond what ``brain.ui.persistence`` re-exports /
  ``brain.llm``.
* ``/session-status`` reads in-memory ``OperatorSession`` fields
  only; no disk IO; no ``tick()``; no curses; no
  ``sqlite3.Connection``.
* ``/db-status`` opens the configured DB through
  ``sqlite3.connect("file:<path>?mode=ro", uri=True)`` inside a
  ``with conn:`` block, reads ``meta`` rows, closes; no
  ``tick()``; no swap; no builder call.
* ``/db-verify`` reuses ``load_session`` (the Phase 3.9 helper),
  immediately DROPS the returned candidate, and returns a typed
  ``DbVerifyReport``; the candidate is never assigned to the live
  ``OperatorSession``; the live session reference is unchanged by
  ``id()`` before and after the call.
* ``/db-backup`` uses ``sqlite3.Connection.backup()`` (page-faithful)
  from a ``mode=ro`` source connection to a write-mode destination
  connection inside ``with`` blocks; refuses to overwrite an
  existing destination unless ``force=True``; refuses URI-scheme
  destinations (``sqlite:``, ``file:``, ``http:``, ``https:``,
  ``ftp:``, ``ws:``, ``wss:``, ``data:``, ``gopher:``, ``ssh:``,
  ``git:``); refuses ``dest_path == source_path``; never modifies
  the source DB.
* No ``sqlite3.Connection`` is stored on ``OperatorSession``; Phase
  3.10a adds NO new session field.
* No autosave entry point exists; no ``@atexit`` / signal /
  threading / asyncio autosave hook is registered; the Phase 3.10c
  autosave track is gated behind its own review gate.
* Module-level statements are limited to imports, constants,
  function defs, and class defs (plus this docstring).
"""
from __future__ import annotations

import datetime
import pathlib
import sqlite3
from dataclasses import dataclass
from typing import Optional

from brain.ui.persistence import (
    META_CATALOG_VERSION_KEY,
    META_CREATED_AT_KEY,
    META_SCHEMA_VERSION_KEY,
    META_UPDATED_AT_KEY,
    PersistenceError,
    SessionStoreConfig,
    _read_meta_value,
    load_session,
)


# ---------------------------------------------------------------------------
# Bounded string + URI rejection constants
# ---------------------------------------------------------------------------


#: Maximum length of any string field in a Phase 3.10a typed report
#: (paths, version strings, ISO-8601 timestamps, error text).
OPS_REPORT_TEXT_MAX_LEN: int = 256


#: URI schemes rejected as ``/db-backup`` destinations. Drives
#: ``I-OPSHARDEN-07``. The check is a simple ``"<scheme>:"`` prefix
#: scan on the destination string; the static audit forbids importing
#: ``urllib``.
DB_BACKUP_FORBIDDEN_SCHEMES: frozenset[str] = frozenset({
    "sqlite",
    "file",
    "http",
    "https",
    "ftp",
    "ws",
    "wss",
    "data",
    "gopher",
    "ssh",
    "git",
})


# ---------------------------------------------------------------------------
# Bound enforcement helpers
# ---------------------------------------------------------------------------


def _require_bounded_str(label: str, value: str) -> None:
    """Reject non-str / non-printable / over-cap report string fields.

    The empty string is allowed (used for "no value" markers on the
    missing-DB code paths and for the success-case ``error_text``).
    """
    if not isinstance(value, str):
        raise TypeError(
            f"{label} must be a str (got {type(value).__name__})"
        )
    if value and not value.isprintable():
        raise ValueError(
            f"{label} must be printable text (got {value!r})"
        )
    if len(value) > OPS_REPORT_TEXT_MAX_LEN:
        raise ValueError(
            f"{label} length {len(value)} exceeds "
            f"OPS_REPORT_TEXT_MAX_LEN={OPS_REPORT_TEXT_MAX_LEN}"
        )


def _require_nonneg_int(label: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(
            f"{label} must be an int (got {type(value).__name__})"
        )
    if value < 0:
        raise ValueError(
            f"{label} must be non-negative (got {value!r})"
        )


def _require_bool(label: str, value: bool) -> None:
    if not isinstance(value, bool):
        raise TypeError(
            f"{label} must be a bool (got {type(value).__name__})"
        )


def _bound_error_text(value: str) -> str:
    """Truncate / coerce ``value`` so it satisfies the report cap.

    Used by the helper bodies when surfacing an underlying exception
    message: the report constructor enforces the cap as a class
    invariant, but the helpers also call this to keep the truncation
    consistent (rather than raising on a too-long ``sqlite3`` error).
    """
    if not isinstance(value, str):
        value = str(value)
    if not value.isprintable():
        value = "".join(ch if ch.isprintable() else "?" for ch in value)
    if len(value) > OPS_REPORT_TEXT_MAX_LEN:
        value = value[: OPS_REPORT_TEXT_MAX_LEN - 1] + "…"
    return value


def _destination_uri_scheme(text: str) -> Optional[str]:
    """Return the URI scheme of ``text`` if any of the forbidden set match.

    Manual scheme detection: the static audit forbids ``urllib`` /
    ``urllib.parse``. We scan for ``"<scheme>:"`` prefixes against the
    closed :data:`DB_BACKUP_FORBIDDEN_SCHEMES` set. Returns the matched
    scheme on hit, ``None`` otherwise.
    """
    if not isinstance(text, str):
        return None
    if ":" not in text:
        return None
    prefix = text.split(":", 1)[0].lower()
    if prefix in DB_BACKUP_FORBIDDEN_SCHEMES:
        return prefix
    return None


# ---------------------------------------------------------------------------
# Typed report records
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SessionStatusReport:
    """Bounded read-only snapshot of an :class:`OperatorSession`.

    Constructed by :func:`session_status` from in-memory fields only;
    no disk IO, no ``tick()``, no ``sqlite3.Connection``.
    """

    tick_counter: int
    queue_size: int
    active_view: str
    has_latest_tick: bool
    has_output_history: bool
    has_worldlet_history: bool
    has_repl_history: bool
    stream_chunk_count: int
    stream_candidate_count: int
    stream_chunk_serial: int
    session_db_configured: bool
    session_db_path_str: str
    quit_flag: bool

    def __post_init__(self) -> None:
        _require_nonneg_int("SessionStatusReport.tick_counter", self.tick_counter)
        _require_nonneg_int("SessionStatusReport.queue_size", self.queue_size)
        _require_bounded_str("SessionStatusReport.active_view", self.active_view)
        _require_bool("SessionStatusReport.has_latest_tick", self.has_latest_tick)
        _require_bool(
            "SessionStatusReport.has_output_history", self.has_output_history
        )
        _require_bool(
            "SessionStatusReport.has_worldlet_history", self.has_worldlet_history
        )
        _require_bool("SessionStatusReport.has_repl_history", self.has_repl_history)
        _require_nonneg_int(
            "SessionStatusReport.stream_chunk_count", self.stream_chunk_count
        )
        _require_nonneg_int(
            "SessionStatusReport.stream_candidate_count",
            self.stream_candidate_count,
        )
        _require_nonneg_int(
            "SessionStatusReport.stream_chunk_serial", self.stream_chunk_serial
        )
        _require_bool(
            "SessionStatusReport.session_db_configured",
            self.session_db_configured,
        )
        _require_bounded_str(
            "SessionStatusReport.session_db_path_str", self.session_db_path_str
        )
        _require_bool("SessionStatusReport.quit_flag", self.quit_flag)


@dataclass(frozen=True, slots=True)
class DbStatusReport:
    """Bounded read-only status of the configured session DB."""

    db_path_str: str
    db_exists: bool
    db_byte_size: int
    db_modified_at: str
    schema_version: int
    catalog_version: str
    created_at: str
    updated_at: str
    error_text: str

    def __post_init__(self) -> None:
        _require_bounded_str("DbStatusReport.db_path_str", self.db_path_str)
        _require_bool("DbStatusReport.db_exists", self.db_exists)
        _require_nonneg_int("DbStatusReport.db_byte_size", self.db_byte_size)
        _require_bounded_str(
            "DbStatusReport.db_modified_at", self.db_modified_at
        )
        _require_nonneg_int(
            "DbStatusReport.schema_version", self.schema_version
        )
        _require_bounded_str(
            "DbStatusReport.catalog_version", self.catalog_version
        )
        _require_bounded_str("DbStatusReport.created_at", self.created_at)
        _require_bounded_str("DbStatusReport.updated_at", self.updated_at)
        _require_bounded_str("DbStatusReport.error_text", self.error_text)


@dataclass(frozen=True, slots=True)
class DbVerifyReport:
    """Bounded PASS/FAIL report from ``/db-verify``."""

    db_path_str: str
    passed: bool
    schema_version: int
    catalog_version: str
    loaded_chunks: int
    loaded_candidates: int
    rebuilt_candidates: bool
    error_text: str

    def __post_init__(self) -> None:
        _require_bounded_str("DbVerifyReport.db_path_str", self.db_path_str)
        _require_bool("DbVerifyReport.passed", self.passed)
        _require_nonneg_int(
            "DbVerifyReport.schema_version", self.schema_version
        )
        _require_bounded_str(
            "DbVerifyReport.catalog_version", self.catalog_version
        )
        _require_nonneg_int(
            "DbVerifyReport.loaded_chunks", self.loaded_chunks
        )
        _require_nonneg_int(
            "DbVerifyReport.loaded_candidates", self.loaded_candidates
        )
        _require_bool(
            "DbVerifyReport.rebuilt_candidates", self.rebuilt_candidates
        )
        _require_bounded_str("DbVerifyReport.error_text", self.error_text)


@dataclass(frozen=True, slots=True)
class DbBackupReport:
    """Bounded result record from ``/db-backup``."""

    source_path_str: str
    dest_path_str: str
    source_byte_size: int
    dest_byte_size: int
    pages_copied: int
    total_pages: int
    succeeded: bool
    overwritten: bool
    error_text: str

    def __post_init__(self) -> None:
        _require_bounded_str(
            "DbBackupReport.source_path_str", self.source_path_str
        )
        _require_bounded_str(
            "DbBackupReport.dest_path_str", self.dest_path_str
        )
        _require_nonneg_int(
            "DbBackupReport.source_byte_size", self.source_byte_size
        )
        _require_nonneg_int(
            "DbBackupReport.dest_byte_size", self.dest_byte_size
        )
        _require_nonneg_int("DbBackupReport.pages_copied", self.pages_copied)
        _require_nonneg_int("DbBackupReport.total_pages", self.total_pages)
        _require_bool("DbBackupReport.succeeded", self.succeeded)
        _require_bool("DbBackupReport.overwritten", self.overwritten)
        _require_bounded_str("DbBackupReport.error_text", self.error_text)


# ---------------------------------------------------------------------------
# session_status — in-memory read of OperatorSession
# ---------------------------------------------------------------------------


def session_status(session: object) -> SessionStatusReport:
    """Return a bounded :class:`SessionStatusReport` for ``session``.

    Drives ``I-OPSHARDEN-01``. No disk IO, no ``tick()``, no curses,
    no ``sqlite3.Connection``. All fields are read from in-memory
    ``OperatorSession`` attributes.
    """
    # Local import keeps the import graph minimal at module load
    # (the static audit allows brain.ui.session).
    from brain.ui.session import OperatorSession  # noqa: PLC0415

    if not isinstance(session, OperatorSession):
        raise PersistenceError(
            "session_status requires an OperatorSession "
            f"(got {type(session).__name__})"
        )

    config = session.session_store_config
    if config is None:
        db_path_str = ""
        configured = False
    else:
        configured = True
        db_path_str = _bound_error_text(str(config.db_path))

    return SessionStatusReport(
        tick_counter=int(session.tick_counter),
        queue_size=int(len(session.event_queue)),
        active_view=str(session.active_view),
        has_latest_tick=session.latest_tick is not None,
        has_output_history=session.output_history is not None,
        has_worldlet_history=session.worldlet_history is not None,
        has_repl_history=session.repl_history is not None,
        stream_chunk_count=int(len(session.stream_history.chunks)),
        stream_candidate_count=int(len(session.stream_candidates)),
        stream_chunk_serial=int(session.stream_chunk_serial),
        session_db_configured=configured,
        session_db_path_str=db_path_str,
        quit_flag=bool(session.quit_flag),
    )


# ---------------------------------------------------------------------------
# db_status — mode=ro read of meta rows
# ---------------------------------------------------------------------------


def _ro_connect_uri(db_path: pathlib.Path) -> str:
    """Return the sqlite3 file URI for opening ``db_path`` in mode=ro.

    The audit (``I-OPSHARDEN-10``) confirms the literal substring
    ``"mode=ro"`` appears in this module; the source-connection open
    sites in :func:`db_status`, :func:`db_verify`, and :func:`db_backup`
    all call this helper.
    """
    return pathlib.Path(db_path).resolve().as_uri() + "?mode=ro"


def db_status(config: SessionStoreConfig) -> DbStatusReport:
    """Return a bounded :class:`DbStatusReport` for ``config.db_path``.

    Drives ``I-OPSHARDEN-02``. Opens the DB through
    ``sqlite3.connect("file:<path>?mode=ro", uri=True)`` inside a
    ``with conn:`` block, reads ``meta`` rows, closes. Missing DB
    returns ``db_exists=False`` plus a bounded ``error_text`` and
    empty version / timestamp fields; no ``sqlite3`` error propagates.
    """
    if not isinstance(config, SessionStoreConfig):
        raise PersistenceError(
            "db_status requires a SessionStoreConfig "
            f"(got {type(config).__name__})"
        )
    db_path = config.db_path
    db_path_str = _bound_error_text(str(db_path))

    if not db_path.exists():
        return DbStatusReport(
            db_path_str=db_path_str,
            db_exists=False,
            db_byte_size=0,
            db_modified_at="",
            schema_version=0,
            catalog_version="",
            created_at="",
            updated_at="",
            error_text=_bound_error_text(
                f"session DB at {db_path!s} does not exist"
            ),
        )
    if db_path.is_dir():
        return DbStatusReport(
            db_path_str=db_path_str,
            db_exists=False,
            db_byte_size=0,
            db_modified_at="",
            schema_version=0,
            catalog_version="",
            created_at="",
            updated_at="",
            error_text=_bound_error_text(
                f"session DB at {db_path!s} is a directory"
            ),
        )

    try:
        stat = db_path.stat()
        db_byte_size = int(stat.st_size)
        db_modified_at = datetime.datetime.fromtimestamp(
            stat.st_mtime, tz=datetime.timezone.utc
        ).isoformat()
    except OSError as exc:
        return DbStatusReport(
            db_path_str=db_path_str,
            db_exists=False,
            db_byte_size=0,
            db_modified_at="",
            schema_version=0,
            catalog_version="",
            created_at="",
            updated_at="",
            error_text=_bound_error_text(f"stat failed: {exc}"),
        )

    uri = _ro_connect_uri(db_path)
    schema_version = 0
    catalog_version = ""
    created_at = ""
    updated_at = ""
    error_text = ""
    try:
        with sqlite3.connect(uri, uri=True) as conn:
            try:
                schema_text = _read_meta_value(conn, META_SCHEMA_VERSION_KEY)
                if schema_text is not None:
                    try:
                        schema_version = int(schema_text)
                    except (TypeError, ValueError):
                        schema_version = 0
                catalog_value = _read_meta_value(
                    conn, META_CATALOG_VERSION_KEY
                )
                if catalog_value is not None:
                    catalog_version = _bound_error_text(catalog_value)
                created_value = _read_meta_value(conn, META_CREATED_AT_KEY)
                if created_value is not None:
                    created_at = _bound_error_text(created_value)
                updated_value = _read_meta_value(conn, META_UPDATED_AT_KEY)
                if updated_value is not None:
                    updated_at = _bound_error_text(updated_value)
            except sqlite3.Error as exc:
                error_text = _bound_error_text(f"meta read failed: {exc}")
    except sqlite3.Error as exc:
        error_text = _bound_error_text(f"open failed: {exc}")

    return DbStatusReport(
        db_path_str=db_path_str,
        db_exists=True,
        db_byte_size=db_byte_size,
        db_modified_at=_bound_error_text(db_modified_at),
        schema_version=schema_version,
        catalog_version=catalog_version,
        created_at=created_at,
        updated_at=updated_at,
        error_text=error_text,
    )


# ---------------------------------------------------------------------------
# db_verify — reuse load_session, drop the candidate
# ---------------------------------------------------------------------------


def db_verify(
    config: SessionStoreConfig,
    *,
    rebuild_candidates_if_missing: bool = True,
) -> DbVerifyReport:
    """Run :func:`load_session` and drop the candidate; return PASS/FAIL.

    Drives ``I-OPSHARDEN-03`` and ``I-OPSHARDEN-04``. The candidate
    returned by ``load_session`` is captured into a local variable
    and immediately discarded; it is never assigned to any live
    :class:`OperatorSession`. On :class:`PersistenceError` the report
    has ``passed=False`` and a bounded ``error_text``; the live
    operator session is unaffected.
    """
    if not isinstance(config, SessionStoreConfig):
        raise PersistenceError(
            "db_verify requires a SessionStoreConfig "
            f"(got {type(config).__name__})"
        )
    db_path_str = _bound_error_text(str(config.db_path))
    try:
        candidate, result = load_session(
            config,
            rebuild_candidates_if_missing=rebuild_candidates_if_missing,
        )
    except PersistenceError as exc:
        return DbVerifyReport(
            db_path_str=db_path_str,
            passed=False,
            schema_version=0,
            catalog_version="",
            loaded_chunks=0,
            loaded_candidates=0,
            rebuilt_candidates=False,
            error_text=_bound_error_text(str(exc)),
        )

    # Drop the candidate immediately. The local name `candidate` falls
    # out of scope when the function returns; we explicitly delete it
    # to make the discard intent visible. The static audit + the
    # persistence_ops_db_verify_drop fixture both confirm that no
    # live session reference is rebound by this function.
    schema_version = int(result.schema_version)
    catalog_version = _bound_error_text(result.catalog_version)
    loaded_chunks = int(result.loaded_chunks)
    loaded_candidates = int(result.loaded_candidates)
    rebuilt_candidates = bool(result.rebuilt_candidates)
    del candidate

    return DbVerifyReport(
        db_path_str=db_path_str,
        passed=True,
        schema_version=schema_version,
        catalog_version=catalog_version,
        loaded_chunks=loaded_chunks,
        loaded_candidates=loaded_candidates,
        rebuilt_candidates=rebuilt_candidates,
        error_text="",
    )


# ---------------------------------------------------------------------------
# db_backup — sqlite3.Connection.backup() with mode=ro source
# ---------------------------------------------------------------------------


def db_backup(
    config: SessionStoreConfig,
    dest_path: pathlib.Path,
    *,
    force: bool = False,
) -> DbBackupReport:
    """Copy ``config.db_path`` to ``dest_path`` via the SQLite Backup API.

    Drives ``I-OPSHARDEN-05``, ``I-OPSHARDEN-06``, ``I-OPSHARDEN-07``,
    ``I-OPSHARDEN-08``. The source connection is opened ``mode=ro``;
    the destination is opened writable. Both connections live inside
    ``with conn:`` blocks. Refuses URI-scheme destinations, refuses
    ``dest_path == source_path``, refuses an existing destination
    unless ``force=True``, refuses a destination that is a directory.
    """
    if not isinstance(config, SessionStoreConfig):
        raise PersistenceError(
            "db_backup requires a SessionStoreConfig "
            f"(got {type(config).__name__})"
        )
    if not isinstance(dest_path, pathlib.Path):
        raise PersistenceError(
            "db_backup dest_path must be a pathlib.Path "
            f"(got {type(dest_path).__name__})"
        )
    if not isinstance(force, bool):
        raise PersistenceError(
            "db_backup force must be a bool "
            f"(got {type(force).__name__})"
        )

    source_path = config.db_path
    source_path_str = _bound_error_text(str(source_path))
    dest_str_raw = str(dest_path)
    dest_path_str = _bound_error_text(dest_str_raw)

    # Reject URI-scheme destinations at validation time (no sqlite3
    # call yet). Drives I-OPSHARDEN-07.
    scheme = _destination_uri_scheme(dest_str_raw)
    if scheme is not None:
        raise PersistenceError(
            f"db_backup dest_path uses forbidden URI scheme "
            f"{scheme!r} (got {dest_str_raw!r})"
        )

    if not source_path.exists():
        return DbBackupReport(
            source_path_str=source_path_str,
            dest_path_str=dest_path_str,
            source_byte_size=0,
            dest_byte_size=0,
            pages_copied=0,
            total_pages=0,
            succeeded=False,
            overwritten=False,
            error_text=_bound_error_text(
                f"source DB at {source_path!s} does not exist"
            ),
        )
    if source_path.is_dir():
        return DbBackupReport(
            source_path_str=source_path_str,
            dest_path_str=dest_path_str,
            source_byte_size=0,
            dest_byte_size=0,
            pages_copied=0,
            total_pages=0,
            succeeded=False,
            overwritten=False,
            error_text=_bound_error_text(
                f"source DB at {source_path!s} is a directory"
            ),
        )

    try:
        source_resolved = source_path.resolve()
        dest_resolved = dest_path.resolve()
    except OSError as exc:
        return DbBackupReport(
            source_path_str=source_path_str,
            dest_path_str=dest_path_str,
            source_byte_size=0,
            dest_byte_size=0,
            pages_copied=0,
            total_pages=0,
            succeeded=False,
            overwritten=False,
            error_text=_bound_error_text(f"path resolve failed: {exc}"),
        )

    if source_resolved == dest_resolved:
        raise PersistenceError(
            "db_backup dest_path must differ from source_path "
            f"(both resolved to {source_resolved!s})"
        )

    if dest_path.exists() and dest_path.is_dir():
        return DbBackupReport(
            source_path_str=source_path_str,
            dest_path_str=dest_path_str,
            source_byte_size=int(source_path.stat().st_size),
            dest_byte_size=0,
            pages_copied=0,
            total_pages=0,
            succeeded=False,
            overwritten=False,
            error_text=_bound_error_text(
                f"dest_path {dest_path!s} is a directory"
            ),
        )

    dest_existed = dest_path.exists()
    if dest_existed and not force:
        return DbBackupReport(
            source_path_str=source_path_str,
            dest_path_str=dest_path_str,
            source_byte_size=int(source_path.stat().st_size),
            dest_byte_size=int(dest_path.stat().st_size),
            pages_copied=0,
            total_pages=0,
            succeeded=False,
            overwritten=False,
            error_text=_bound_error_text(
                f"dest_path {dest_path!s} exists; pass force=True to overwrite"
            ),
        )

    source_uri = _ro_connect_uri(source_path)
    pages_copied = 0
    total_pages = 0
    error_text = ""
    succeeded = False
    overwritten = False

    try:
        # If overwriting, remove the destination first so the new file
        # is exactly the same byte sequence as the source. Without this
        # the SQLite Backup API copies pages into the existing file
        # (still page-faithful, but the file size may not equal the
        # source size if the destination was larger).
        if dest_existed and force:
            dest_path.unlink()
            overwritten = True

        with sqlite3.connect(source_uri, uri=True) as source_conn:
            with sqlite3.connect(str(dest_path)) as dest_conn:
                # sqlite3.Connection.backup is page-faithful. Track
                # progress through a callback. The connection-level
                # backup runs synchronously inside this with-block.
                progress: dict[str, int] = {"copied": 0, "total": 0}

                def _track(status: int, remaining: int, total: int) -> None:
                    progress["total"] = int(total)
                    progress["copied"] = int(total) - int(remaining)
                    _ = status  # unused; required by API

                source_conn.backup(dest_conn, progress=_track)
                pages_copied = int(progress["copied"])
                total_pages = int(progress["total"])
        succeeded = True
    except (sqlite3.Error, OSError) as exc:
        error_text = _bound_error_text(f"backup failed: {exc}")
        succeeded = False

    source_byte_size = int(source_path.stat().st_size)
    dest_byte_size = (
        int(dest_path.stat().st_size) if dest_path.exists() else 0
    )

    return DbBackupReport(
        source_path_str=source_path_str,
        dest_path_str=dest_path_str,
        source_byte_size=source_byte_size,
        dest_byte_size=dest_byte_size,
        pages_copied=pages_copied,
        total_pages=total_pages,
        succeeded=succeeded,
        overwritten=overwritten,
        error_text=error_text,
    )


__all__ = (
    "OPS_REPORT_TEXT_MAX_LEN",
    "DB_BACKUP_FORBIDDEN_SCHEMES",
    "SessionStatusReport",
    "DbStatusReport",
    "DbVerifyReport",
    "DbBackupReport",
    "session_status",
    "db_status",
    "db_verify",
    "db_backup",
)
