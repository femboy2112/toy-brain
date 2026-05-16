"""Phase 3.9 Persistent Session Store — typed records + finite SQLite schema.

This module owns the :class:`SessionStoreConfig`,
:class:`PersistenceError`, the ``Persistent*Snapshot`` value records,
:class:`SaveSessionResult`, :class:`LoadSessionResult`, the
``SCHEMA_VERSION_V1`` integer, and the closed v1 SQLite schema used by
``/save-session`` / ``/load-session``. The Step 9 implementation
extends this module with the ``save_session`` and ``load_session``
top-level helpers; the Step 10 implementation wires the dispatchers
into :class:`brain.ui.session.OperatorSession` and the
``/save-session`` / ``/load-session`` typed commands.

Catalog rows driven from here (Phase 3.9):

* ``I-PERSIST-01`` (REQUIRED) — SQLite schema is finite and closed.
  The schema declared in this module is exactly the v1 set
  ``{meta, content_registry, profile_values, msi_contents,
  msi_threshold, ptcns_eval, session_state, stream_chunks,
  stream_candidates}`` with the documented columns, NOT NULL
  constraints, PRIMARY KEY / UNIQUE / FOREIGN KEY structure, and
  CHECK constraints (``rho_den > 0``, ``den > 0``,
  ``msi_threshold.id = 1``).

* ``I-PERSIST-12`` (STRUCTURAL) — Static AST audit over this module
  rejects imports of ``pickle``, ``shelve``, ``marshal``, ``dill``,
  ``cloudpickle``, ``joblib``, ``subprocess``, ``socket``,
  ``urllib``, ``http``, ``requests``, and ``curses``; rejects
  ``__import__``, ``importlib.import_module``, ``eval(``, ``exec(``,
  ``compile(``, ``atexit.register``, ``threading``, ``asyncio``, and
  signal handlers; allows ``brain.tick.BrainState`` as a typed
  record import and forbids importing or calling the ``tick``
  callable; limits module-level statements to imports, constants,
  function defs, and class defs (plus a module docstring).

* ``I-PERSIST-13`` (STRUCTURAL) — No kernel-numeric ``REAL`` column
  in the schema. Every kernel-numeric value (``rho_num``,
  ``rho_den``, ``msi_threshold.num``, ``msi_threshold.den``,
  ``tick_at_event``) uses ``INTEGER``; identifiers, enum names,
  printable text, and timestamps use ``TEXT``; the schema contains
  no ``REAL`` / ``NUMERIC`` / ``FLOAT`` / ``DOUBLE`` column.

Hard boundaries pinned by
``PHASE3_9_PERSISTENT_SESSION_STORE_CORRIGENDA.md``:

* SQLite via the standard-library ``sqlite3`` module only — no
  pickle / shelve / marshal / dill / cloudpickle / joblib.
* Fractions persist exactly as ``num INTEGER + den INTEGER`` pairs;
  no kernel-numeric REAL / NUMERIC / FLOAT / DOUBLE column.
* Step 9 load reconstructs through the existing public builders
  (``make_profile_with_cogito``, ``make_msi``, ``make_ptcns``,
  ``ContentRegistry``, ``BrainState``, ``make_text_stream_chunk``,
  ``TextStreamHistory``, ``make_stream_promotion_candidate``,
  ``OperatorSession``) and runs invariant assertions before
  returning a candidate session; ``COGITO_ID`` cannot be
  overwritten by persisted data.
* Step 9 failed save / failed load preserve the live
  ``OperatorSession``; load opens the DB in sqlite3 uri
  ``mode=ro``.
* No ``sqlite3.Connection`` is stored on ``OperatorSession``;
  helpers use ``with sqlite3.connect(...) as conn:`` and close
  the connection on with-block exit.
* No autosave; ``/save-session`` and ``/load-session`` are the
  only persistence routes, both explicit operator commands; this
  module is not reachable from ``/step``, ``/stream``,
  ``/stream-promote``, or any other tick-adjacent dispatch path.
"""
from __future__ import annotations

import pathlib
import sqlite3
from dataclasses import dataclass
from typing import Optional

from brain.development.text_stream import (
    STREAM_PROVENANCE_MAX_LEN,
    STREAM_TEXT_MAX_LEN,
)


# ---------------------------------------------------------------------------
# Schema version + module identifiers
# ---------------------------------------------------------------------------


#: Integer version of the v1 SQLite schema persisted in
#: ``meta.schema_version``. Bumped only when the schema is changed in a
#: way that requires a migration; a future campaign owns migrations.
SCHEMA_VERSION_V1: int = 1

#: Closed set of schema versions ``load_session`` will accept.
SUPPORTED_SCHEMA_VERSIONS: frozenset[int] = frozenset({SCHEMA_VERSION_V1})

#: Catalog version stamp written into ``meta.catalog_version`` by save
#: helpers landed in Step 9. Diagnostic only; does not gate v1 load.
CATALOG_VERSION_STAMP: str = "v0.17"


# ---------------------------------------------------------------------------
# Table and meta key names
# ---------------------------------------------------------------------------


META_TABLE_NAME: str = "meta"
CONTENT_REGISTRY_TABLE_NAME: str = "content_registry"
PROFILE_VALUES_TABLE_NAME: str = "profile_values"
MSI_CONTENTS_TABLE_NAME: str = "msi_contents"
MSI_THRESHOLD_TABLE_NAME: str = "msi_threshold"
PTCNS_EVAL_TABLE_NAME: str = "ptcns_eval"
SESSION_STATE_TABLE_NAME: str = "session_state"
STREAM_CHUNKS_TABLE_NAME: str = "stream_chunks"
STREAM_CANDIDATES_TABLE_NAME: str = "stream_candidates"

#: Closed set of table names declared by the v1 schema. The
#: ``persistence_schema.py`` fixture asserts that the set of tables
#: actually created by ``_create_schema`` matches this set exactly
#: (drives I-PERSIST-01).
EXPECTED_TABLES: frozenset[str] = frozenset({
    META_TABLE_NAME,
    CONTENT_REGISTRY_TABLE_NAME,
    PROFILE_VALUES_TABLE_NAME,
    MSI_CONTENTS_TABLE_NAME,
    MSI_THRESHOLD_TABLE_NAME,
    PTCNS_EVAL_TABLE_NAME,
    SESSION_STATE_TABLE_NAME,
    STREAM_CHUNKS_TABLE_NAME,
    STREAM_CANDIDATES_TABLE_NAME,
})

META_SCHEMA_VERSION_KEY: str = "schema_version"
META_CATALOG_VERSION_KEY: str = "catalog_version"
META_CREATED_AT_KEY: str = "created_at"
META_UPDATED_AT_KEY: str = "updated_at"

SESSION_STATE_TICK_COUNTER_KEY: str = "tick_counter"
SESSION_STATE_STREAM_SERIAL_KEY: str = "stream_chunk_serial"


# ---------------------------------------------------------------------------
# Bounded string policy
# ---------------------------------------------------------------------------


#: Bound on persisted ContentRegistry texts. Phase 3.7 text-stream
#: chunks already cap at ``STREAM_TEXT_MAX_LEN``; registry texts may
#: be either upstream kernel content (typically short) or downstream
#: stream-promoted content. The shared cap keeps every persisted text
#: column bounded.
REGISTRY_TEXT_MAX_LEN: int = STREAM_TEXT_MAX_LEN

#: Bound on persisted catalog_version / created_at / updated_at /
#: meta value strings. Catalog version stamps are short ("v0.17");
#: ISO-8601 UTC timestamps are at most 32 chars. 128 covers both with
#: room for future format extensions.
META_VALUE_MAX_LEN: int = 128


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class PersistenceError(Exception):
    """Bounded local error raised by save / load helpers.

    The message is a printable string suitable for surfacing through
    the existing :data:`brain.ui.session.MAX_STATUS_TEXT_LEN`-bounded
    status/error pipeline. Persistence helpers raise
    :class:`PersistenceError` and never let an underlying
    ``sqlite3.DatabaseError`` / ``ValueError`` / ``TypeError`` escape
    into the curses wrapper.
    """


# ---------------------------------------------------------------------------
# SessionStoreConfig
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SessionStoreConfig:
    """Bounded immutable session-store configuration.

    Carries a :class:`pathlib.Path` to the SQLite session DB plus the
    integer ``schema_version`` and bounded ``catalog_version`` stamp
    written into the ``meta`` table by save. The Step 9 helpers attach
    a config to operator sessions through the
    ``OperatorSession.session_store_config`` field (see Step 9 of the
    campaign); the field carries no ``sqlite3.Connection``, no
    callable, no socket, no subprocess handle, and no LLM client
    (drives I-PERSIST-11 / I-PERSIST-14).
    """

    db_path: pathlib.Path
    schema_version: int = SCHEMA_VERSION_V1
    catalog_version: str = CATALOG_VERSION_STAMP

    def __post_init__(self) -> None:
        if not isinstance(self.db_path, pathlib.Path):
            raise TypeError(
                "SessionStoreConfig.db_path must be a pathlib.Path "
                f"(got {type(self.db_path).__name__})"
            )
        if not isinstance(self.schema_version, int) or isinstance(
            self.schema_version, bool
        ):
            raise TypeError(
                "SessionStoreConfig.schema_version must be an int "
                f"(got {type(self.schema_version).__name__})"
            )
        if self.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError(
                "SessionStoreConfig.schema_version must be in "
                f"{sorted(SUPPORTED_SCHEMA_VERSIONS)!r} "
                f"(got {self.schema_version!r})"
            )
        if not isinstance(self.catalog_version, str):
            raise TypeError(
                "SessionStoreConfig.catalog_version must be a str "
                f"(got {type(self.catalog_version).__name__})"
            )
        if not self.catalog_version:
            raise ValueError(
                "SessionStoreConfig.catalog_version must be non-empty"
            )
        if len(self.catalog_version) > META_VALUE_MAX_LEN:
            raise ValueError(
                "SessionStoreConfig.catalog_version length "
                f"{len(self.catalog_version)} exceeds "
                f"META_VALUE_MAX_LEN={META_VALUE_MAX_LEN}"
            )
        if not self.catalog_version.isprintable():
            raise ValueError(
                "SessionStoreConfig.catalog_version must be printable "
                f"(got {self.catalog_version!r})"
            )


# ---------------------------------------------------------------------------
# Persistent snapshot records
# ---------------------------------------------------------------------------


def _require_printable_id(label: str, value: str) -> None:
    if not isinstance(value, str):
        raise TypeError(
            f"{label} must be a str (got {type(value).__name__})"
        )
    if not value:
        raise ValueError(f"{label} must be non-empty")
    if not value.isprintable():
        raise ValueError(f"{label} must be printable (got {value!r})")
    if len(value) > STREAM_PROVENANCE_MAX_LEN:
        raise ValueError(
            f"{label} length {len(value)} exceeds "
            f"STREAM_PROVENANCE_MAX_LEN={STREAM_PROVENANCE_MAX_LEN}"
        )


def _require_bounded_text(label: str, value: str, *, cap: int) -> None:
    if not isinstance(value, str):
        raise TypeError(
            f"{label} must be a str (got {type(value).__name__})"
        )
    if not value.isprintable():
        raise ValueError(f"{label} must be printable (got {value!r})")
    if len(value) > cap:
        raise ValueError(
            f"{label} length {len(value)} exceeds cap={cap}"
        )


def _require_nonneg_int(label: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(
            f"{label} must be an int (got {type(value).__name__})"
        )
    if value < 0:
        raise ValueError(f"{label} must be non-negative (got {value!r})")


def _require_positive_int(label: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(
            f"{label} must be an int (got {type(value).__name__})"
        )
    if value <= 0:
        raise ValueError(f"{label} must be positive (got {value!r})")


@dataclass(frozen=True, slots=True)
class PersistentBrainStateSnapshot:
    """Typed snapshot of a :class:`brain.tick.BrainState` for save/load.

    All numeric kernel fields are stored as integer ``num/den`` pairs so
    they round-trip through :class:`fractions.Fraction` exactly (drives
    I-PERSIST-03). Identifiers and registry texts are bounded printable
    strings.
    """

    profile_values: tuple[tuple[str, int, int], ...]
    msi_contents: tuple[str, ...]
    msi_threshold_num: int
    msi_threshold_den: int
    ptcns_eval: tuple[tuple[str, str], ...]
    registry_texts: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.profile_values, tuple):
            raise TypeError(
                "PersistentBrainStateSnapshot.profile_values must be a tuple "
                f"(got {type(self.profile_values).__name__})"
            )
        seen_profile: set[str] = set()
        for entry in self.profile_values:
            if not isinstance(entry, tuple) or len(entry) != 3:
                raise TypeError(
                    "profile_values entries must be (content_id, num, den) "
                    f"tuples (got {entry!r})"
                )
            content_id, num, den = entry
            _require_printable_id(
                "profile_values content_id", content_id
            )
            if content_id in seen_profile:
                raise ValueError(
                    f"profile_values has duplicate content_id {content_id!r}"
                )
            seen_profile.add(content_id)
            if not isinstance(num, int) or isinstance(num, bool):
                raise TypeError(
                    f"profile_values num for {content_id!r} must be int "
                    f"(got {type(num).__name__})"
                )
            _require_positive_int(
                f"profile_values den for {content_id!r}", den
            )
            # Bounded to [0, 1]: 0 <= num <= den (consistent with rho).
            if num < 0 or num > den:
                raise ValueError(
                    f"profile_values rho for {content_id!r} is "
                    f"{num}/{den}; must lie in [0, 1]"
                )

        if not isinstance(self.msi_contents, tuple):
            raise TypeError(
                "PersistentBrainStateSnapshot.msi_contents must be a tuple"
            )
        seen_msi: set[str] = set()
        for cid in self.msi_contents:
            _require_printable_id("msi_contents content_id", cid)
            if cid in seen_msi:
                raise ValueError(
                    f"msi_contents has duplicate content_id {cid!r}"
                )
            seen_msi.add(cid)
            if cid not in seen_profile:
                raise ValueError(
                    f"msi_contents references unknown content_id {cid!r}"
                )

        if not isinstance(self.msi_threshold_num, int) or isinstance(
            self.msi_threshold_num, bool
        ):
            raise TypeError(
                "msi_threshold_num must be an int "
                f"(got {type(self.msi_threshold_num).__name__})"
            )
        _require_positive_int("msi_threshold_den", self.msi_threshold_den)
        if self.msi_threshold_num < 0 or self.msi_threshold_num > self.msi_threshold_den:
            raise ValueError(
                f"msi_threshold {self.msi_threshold_num}/"
                f"{self.msi_threshold_den} must lie in [0, 1]"
            )

        if not isinstance(self.ptcns_eval, tuple):
            raise TypeError(
                "PersistentBrainStateSnapshot.ptcns_eval must be a tuple"
            )
        seen_eval: set[str] = set()
        for entry in self.ptcns_eval:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise TypeError(
                    "ptcns_eval entries must be (content_id, eval_name) "
                    f"tuples (got {entry!r})"
                )
            cid, name = entry
            _require_printable_id("ptcns_eval content_id", cid)
            if cid in seen_eval:
                raise ValueError(
                    f"ptcns_eval has duplicate content_id {cid!r}"
                )
            seen_eval.add(cid)
            _require_bounded_text(
                f"ptcns_eval value for {cid!r}", name, cap=64
            )
            if cid not in seen_profile:
                raise ValueError(
                    f"ptcns_eval references unknown content_id {cid!r}"
                )

        if not isinstance(self.registry_texts, tuple):
            raise TypeError(
                "PersistentBrainStateSnapshot.registry_texts must be a tuple"
            )
        seen_registry: set[str] = set()
        for entry in self.registry_texts:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise TypeError(
                    "registry_texts entries must be (content_id, text) "
                    f"tuples (got {entry!r})"
                )
            cid, text = entry
            _require_printable_id("registry_texts content_id", cid)
            if cid in seen_registry:
                raise ValueError(
                    f"registry_texts has duplicate content_id {cid!r}"
                )
            seen_registry.add(cid)
            _require_bounded_text(
                f"registry_texts value for {cid!r}",
                text,
                cap=REGISTRY_TEXT_MAX_LEN,
            )


@dataclass(frozen=True, slots=True)
class PersistentStreamChunkSnapshot:
    """Typed snapshot of one :class:`TextStreamChunk` row."""

    ordinal: int
    chunk_id: str
    source: str
    text: str
    tick_at_event: int
    provenance_tag: str

    def __post_init__(self) -> None:
        _require_positive_int(
            "PersistentStreamChunkSnapshot.ordinal", self.ordinal
        )
        _require_printable_id(
            "PersistentStreamChunkSnapshot.chunk_id", self.chunk_id
        )
        _require_printable_id(
            "PersistentStreamChunkSnapshot.source", self.source
        )
        _require_bounded_text(
            "PersistentStreamChunkSnapshot.text",
            self.text,
            cap=STREAM_TEXT_MAX_LEN,
        )
        if not self.text:
            raise ValueError(
                "PersistentStreamChunkSnapshot.text must be non-empty"
            )
        _require_nonneg_int(
            "PersistentStreamChunkSnapshot.tick_at_event",
            self.tick_at_event,
        )
        _require_printable_id(
            "PersistentStreamChunkSnapshot.provenance_tag",
            self.provenance_tag,
        )


@dataclass(frozen=True, slots=True)
class PersistentStreamCandidateSnapshot:
    """Typed snapshot of one :class:`StreamPromotionCandidate` row."""

    ordinal: int
    candidate_id: str
    target_content_id: str
    chunk_id: str
    pattern_id: Optional[str]
    source: str
    text: str
    provenance_tag: str

    def __post_init__(self) -> None:
        _require_positive_int(
            "PersistentStreamCandidateSnapshot.ordinal", self.ordinal
        )
        _require_printable_id(
            "PersistentStreamCandidateSnapshot.candidate_id",
            self.candidate_id,
        )
        _require_printable_id(
            "PersistentStreamCandidateSnapshot.target_content_id",
            self.target_content_id,
        )
        _require_printable_id(
            "PersistentStreamCandidateSnapshot.chunk_id", self.chunk_id
        )
        if self.pattern_id is not None:
            _require_printable_id(
                "PersistentStreamCandidateSnapshot.pattern_id",
                self.pattern_id,
            )
        _require_printable_id(
            "PersistentStreamCandidateSnapshot.source", self.source
        )
        _require_bounded_text(
            "PersistentStreamCandidateSnapshot.text",
            self.text,
            cap=STREAM_TEXT_MAX_LEN,
        )
        _require_printable_id(
            "PersistentStreamCandidateSnapshot.provenance_tag",
            self.provenance_tag,
        )


@dataclass(frozen=True, slots=True)
class PersistentSessionSnapshot:
    """Top-level snapshot persisted by Step 9's ``save_session``."""

    schema_version: int
    catalog_version: str
    created_at: str
    updated_at: str
    brain_state: PersistentBrainStateSnapshot
    tick_counter: int
    stream_chunk_serial: int
    stream_chunks: tuple[PersistentStreamChunkSnapshot, ...]
    stream_candidates: tuple[PersistentStreamCandidateSnapshot, ...]

    def __post_init__(self) -> None:
        if self.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError(
                "PersistentSessionSnapshot.schema_version must be in "
                f"{sorted(SUPPORTED_SCHEMA_VERSIONS)!r} "
                f"(got {self.schema_version!r})"
            )
        _require_bounded_text(
            "PersistentSessionSnapshot.catalog_version",
            self.catalog_version,
            cap=META_VALUE_MAX_LEN,
        )
        if not self.catalog_version:
            raise ValueError(
                "PersistentSessionSnapshot.catalog_version must be non-empty"
            )
        _require_bounded_text(
            "PersistentSessionSnapshot.created_at",
            self.created_at,
            cap=META_VALUE_MAX_LEN,
        )
        if not self.created_at:
            raise ValueError(
                "PersistentSessionSnapshot.created_at must be non-empty"
            )
        _require_bounded_text(
            "PersistentSessionSnapshot.updated_at",
            self.updated_at,
            cap=META_VALUE_MAX_LEN,
        )
        if not self.updated_at:
            raise ValueError(
                "PersistentSessionSnapshot.updated_at must be non-empty"
            )
        if not isinstance(self.brain_state, PersistentBrainStateSnapshot):
            raise TypeError(
                "PersistentSessionSnapshot.brain_state must be a "
                "PersistentBrainStateSnapshot "
                f"(got {type(self.brain_state).__name__})"
            )
        _require_nonneg_int(
            "PersistentSessionSnapshot.tick_counter", self.tick_counter
        )
        _require_nonneg_int(
            "PersistentSessionSnapshot.stream_chunk_serial",
            self.stream_chunk_serial,
        )
        if not isinstance(self.stream_chunks, tuple):
            raise TypeError(
                "PersistentSessionSnapshot.stream_chunks must be a tuple"
            )
        seen_chunks: set[str] = set()
        for chunk in self.stream_chunks:
            if not isinstance(chunk, PersistentStreamChunkSnapshot):
                raise TypeError(
                    "PersistentSessionSnapshot.stream_chunks entries must be "
                    "PersistentStreamChunkSnapshot "
                    f"(got {type(chunk).__name__})"
                )
            if chunk.chunk_id in seen_chunks:
                raise ValueError(
                    "PersistentSessionSnapshot.stream_chunks has duplicate "
                    f"chunk_id {chunk.chunk_id!r}"
                )
            seen_chunks.add(chunk.chunk_id)
        if not isinstance(self.stream_candidates, tuple):
            raise TypeError(
                "PersistentSessionSnapshot.stream_candidates must be a tuple"
            )
        seen_candidates: set[str] = set()
        for cand in self.stream_candidates:
            if not isinstance(cand, PersistentStreamCandidateSnapshot):
                raise TypeError(
                    "PersistentSessionSnapshot.stream_candidates entries must "
                    "be PersistentStreamCandidateSnapshot "
                    f"(got {type(cand).__name__})"
                )
            if cand.candidate_id in seen_candidates:
                raise ValueError(
                    "PersistentSessionSnapshot.stream_candidates has duplicate "
                    f"candidate_id {cand.candidate_id!r}"
                )
            seen_candidates.add(cand.candidate_id)
            if cand.chunk_id not in seen_chunks:
                raise ValueError(
                    f"PersistentSessionSnapshot.stream_candidates entry "
                    f"{cand.candidate_id!r} references unknown chunk_id "
                    f"{cand.chunk_id!r}"
                )


# ---------------------------------------------------------------------------
# Save / load result records
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SaveSessionResult:
    """Successful save outcome record."""

    db_path: pathlib.Path
    schema_version: int
    catalog_version: str
    updated_at: str
    saved_chunks: int
    saved_candidates: int

    def __post_init__(self) -> None:
        if not isinstance(self.db_path, pathlib.Path):
            raise TypeError(
                "SaveSessionResult.db_path must be a pathlib.Path"
            )
        if self.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError(
                "SaveSessionResult.schema_version must be in "
                f"{sorted(SUPPORTED_SCHEMA_VERSIONS)!r}"
            )
        _require_bounded_text(
            "SaveSessionResult.catalog_version",
            self.catalog_version,
            cap=META_VALUE_MAX_LEN,
        )
        _require_bounded_text(
            "SaveSessionResult.updated_at",
            self.updated_at,
            cap=META_VALUE_MAX_LEN,
        )
        _require_nonneg_int(
            "SaveSessionResult.saved_chunks", self.saved_chunks
        )
        _require_nonneg_int(
            "SaveSessionResult.saved_candidates", self.saved_candidates
        )


@dataclass(frozen=True, slots=True)
class LoadSessionResult:
    """Successful load outcome record."""

    db_path: pathlib.Path
    schema_version: int
    catalog_version: str
    loaded_chunks: int
    loaded_candidates: int
    rebuilt_candidates: bool

    def __post_init__(self) -> None:
        if not isinstance(self.db_path, pathlib.Path):
            raise TypeError(
                "LoadSessionResult.db_path must be a pathlib.Path"
            )
        if self.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError(
                "LoadSessionResult.schema_version must be in "
                f"{sorted(SUPPORTED_SCHEMA_VERSIONS)!r}"
            )
        _require_bounded_text(
            "LoadSessionResult.catalog_version",
            self.catalog_version,
            cap=META_VALUE_MAX_LEN,
        )
        _require_nonneg_int(
            "LoadSessionResult.loaded_chunks", self.loaded_chunks
        )
        _require_nonneg_int(
            "LoadSessionResult.loaded_candidates", self.loaded_candidates
        )
        if not isinstance(self.rebuilt_candidates, bool):
            raise TypeError(
                "LoadSessionResult.rebuilt_candidates must be a bool"
            )


# ---------------------------------------------------------------------------
# SQLite schema statements + bootstrap
# ---------------------------------------------------------------------------


#: Closed sequence of ``CREATE TABLE`` statements that define the v1
#: schema. Order matters because FOREIGN KEY references resolve forward
#: only when the parent table already exists. The
#: ``persistence_schema.py`` fixture executes these against an
#: in-memory SQLite database and verifies the result against
#: :data:`EXPECTED_TABLES`.
_SCHEMA_STATEMENTS: tuple[str, ...] = (
    """CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS content_registry (
        content_id TEXT PRIMARY KEY,
        text TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS profile_values (
        content_id TEXT PRIMARY KEY,
        rho_num INTEGER NOT NULL,
        rho_den INTEGER NOT NULL CHECK (rho_den > 0)
    )""",
    """CREATE TABLE IF NOT EXISTS msi_contents (
        content_id TEXT PRIMARY KEY,
        FOREIGN KEY (content_id) REFERENCES profile_values(content_id)
    )""",
    """CREATE TABLE IF NOT EXISTS msi_threshold (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        num INTEGER NOT NULL,
        den INTEGER NOT NULL CHECK (den > 0)
    )""",
    """CREATE TABLE IF NOT EXISTS ptcns_eval (
        content_id TEXT PRIMARY KEY,
        eval TEXT NOT NULL,
        FOREIGN KEY (content_id) REFERENCES profile_values(content_id)
    )""",
    """CREATE TABLE IF NOT EXISTS session_state (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS stream_chunks (
        ordinal INTEGER PRIMARY KEY,
        chunk_id TEXT NOT NULL UNIQUE,
        source TEXT NOT NULL,
        text TEXT NOT NULL,
        tick_at_event INTEGER NOT NULL,
        provenance_tag TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS stream_candidates (
        ordinal INTEGER PRIMARY KEY,
        candidate_id TEXT NOT NULL UNIQUE,
        target_content_id TEXT NOT NULL,
        chunk_id TEXT NOT NULL,
        pattern_id TEXT,
        source TEXT NOT NULL,
        text TEXT NOT NULL,
        provenance_tag TEXT NOT NULL,
        FOREIGN KEY (chunk_id) REFERENCES stream_chunks(chunk_id)
    )""",
)


def schema_statements() -> tuple[str, ...]:
    """Return the closed sequence of CREATE TABLE statements.

    The fixture (``persistence_schema.py``) calls this to walk the
    declared schema without grabbing a module-level private name.
    """
    return _SCHEMA_STATEMENTS


def _create_schema(conn: sqlite3.Connection) -> None:
    """Create the v1 schema on ``conn`` in a single transaction.

    The caller is responsible for opening ``conn`` and for the BEGIN /
    COMMIT envelope (Step 9's ``save_session`` opens a ``with``-managed
    connection and runs ``BEGIN IMMEDIATE``). ``PRAGMA foreign_keys = ON``
    is enabled so the FOREIGN KEY constraints in the schema are active.
    """
    if not isinstance(conn, sqlite3.Connection):
        raise TypeError(
            "_create_schema requires a sqlite3.Connection "
            f"(got {type(conn).__name__})"
        )
    conn.execute("PRAGMA foreign_keys = ON")
    for stmt in _SCHEMA_STATEMENTS:
        conn.execute(stmt)


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


__all__ = (
    "SCHEMA_VERSION_V1",
    "SUPPORTED_SCHEMA_VERSIONS",
    "CATALOG_VERSION_STAMP",
    "META_TABLE_NAME",
    "CONTENT_REGISTRY_TABLE_NAME",
    "PROFILE_VALUES_TABLE_NAME",
    "MSI_CONTENTS_TABLE_NAME",
    "MSI_THRESHOLD_TABLE_NAME",
    "PTCNS_EVAL_TABLE_NAME",
    "SESSION_STATE_TABLE_NAME",
    "STREAM_CHUNKS_TABLE_NAME",
    "STREAM_CANDIDATES_TABLE_NAME",
    "EXPECTED_TABLES",
    "META_SCHEMA_VERSION_KEY",
    "META_CATALOG_VERSION_KEY",
    "META_CREATED_AT_KEY",
    "META_UPDATED_AT_KEY",
    "SESSION_STATE_TICK_COUNTER_KEY",
    "SESSION_STATE_STREAM_SERIAL_KEY",
    "REGISTRY_TEXT_MAX_LEN",
    "META_VALUE_MAX_LEN",
    "PersistenceError",
    "SessionStoreConfig",
    "PersistentBrainStateSnapshot",
    "PersistentStreamChunkSnapshot",
    "PersistentStreamCandidateSnapshot",
    "PersistentSessionSnapshot",
    "SaveSessionResult",
    "LoadSessionResult",
    "schema_statements",
)
