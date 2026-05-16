"""Phase 3.9 Persistent Session Store — typed records, finite SQLite schema, save/load.

This module owns the :class:`SessionStoreConfig`,
:class:`PersistenceError`, the ``Persistent*Snapshot`` value records,
:class:`SaveSessionResult`, :class:`LoadSessionResult`, the
``SCHEMA_VERSION_V1`` integer, the closed v1 SQLite schema, and the
``save_session`` / ``load_session`` helpers used by the Step 10
``/save-session`` / ``/load-session`` typed operator commands.

Catalog rows driven from here (Phase 3.9):

* ``I-PERSIST-01`` (REQUIRED) — SQLite schema is finite and closed.
* ``I-PERSIST-02`` (REQUIRED) — Unknown ``schema_version`` rejected on load.
* ``I-PERSIST-03`` (REQUIRED) — ``Fraction`` round-trip exact via
  integer ``num/den`` pairs.
* ``I-PERSIST-04`` (REQUIRED) — ``COGITO_ID`` cannot be overwritten by
  persisted data.
* ``I-PERSIST-05`` (REQUIRED) — Load reconstructs through public
  builders / constructors only.
* ``I-PERSIST-06`` (REQUIRED) — Load runs invariant assertions before
  returning a candidate session.
* ``I-PERSIST-07`` (REQUIRED) — Failed save preserves the live session.
* ``I-PERSIST-08`` (REQUIRED) — Failed load preserves the live session.
* ``I-PERSIST-10`` (STRUCTURAL) — Save transaction is atomic.
* ``I-PERSIST-12`` (STRUCTURAL) — Static AST audit over this module.
* ``I-PERSIST-13`` (STRUCTURAL) — No kernel-numeric ``REAL`` column
  in the schema.
* ``I-PERSIST-14`` (STRUCTURAL) — No long-lived ``sqlite3.Connection``
  on ``OperatorSession``.

Hard boundaries pinned by
``PHASE3_9_PERSISTENT_SESSION_STORE_CORRIGENDA.md``:

* SQLite via the standard-library ``sqlite3`` module only — no
  pickle / shelve / marshal / dill / cloudpickle / joblib.
* Fractions persist exactly as ``num INTEGER + den INTEGER`` pairs;
  no kernel-numeric REAL / NUMERIC / FLOAT / DOUBLE column.
* Load reconstructs through the existing public builders
  (``make_profile_with_cogito``, ``make_msi``, ``make_ptcns``,
  ``ContentRegistry``, ``BrainState``, ``make_text_stream_chunk``,
  ``TextStreamHistory``, ``make_stream_promotion_candidate``,
  ``OperatorSession``) and runs ``assert_state_invariants`` before
  returning a candidate session; ``COGITO_ID`` cannot be overwritten
  by persisted data.
* Failed save / failed load preserve the live ``OperatorSession``;
  load opens the DB in sqlite3 uri ``mode=ro``.
* No ``sqlite3.Connection`` is stored on ``OperatorSession``;
  helpers use ``with sqlite3.connect(...) as conn:`` and close the
  connection on with-block exit.
* No autosave; ``/save-session`` and ``/load-session`` are the only
  persistence routes, both explicit operator commands; this module
  is not reachable from ``/step``, ``/stream``, ``/stream-promote``,
  or any other tick-adjacent dispatch path.
"""
from __future__ import annotations

import datetime
import pathlib
import sqlite3
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Optional

from brain.development.text_stream import (
    STREAM_PROVENANCE_MAX_LEN,
    STREAM_TEXT_MAX_LEN,
    StreamPromotionCandidate,
    TextStreamChunk,
    TextStreamHistory,
    TextStreamSource,
    make_stream_promotion_candidate,
    make_text_stream_chunk,
)
from brain.io_types import ContentRegistry
from brain.tick import BrainState, assert_state_invariants
from brain.tlica.builders import make_msi, make_profile_with_cogito, make_ptcns
from brain.tlica.profile import COGITO_ID
from brain.tlica.ptcns import ConsistencyEval


# ---------------------------------------------------------------------------
# Schema version + module identifiers
# ---------------------------------------------------------------------------


#: Integer version of the v1 SQLite schema persisted in
#: ``meta.schema_version``. Bumped only when the schema is changed in a
#: way that requires a migration; a future campaign owns migrations.
SCHEMA_VERSION_V1: int = 1

#: Closed set of schema versions ``load_session`` will accept.
SUPPORTED_SCHEMA_VERSIONS: frozenset[int] = frozenset({SCHEMA_VERSION_V1})

#: Catalog version stamp written into ``meta.catalog_version`` by save.
#: Diagnostic only; does not gate v1 load.
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


REGISTRY_TEXT_MAX_LEN: int = STREAM_TEXT_MAX_LEN
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
    written into the ``meta`` table by save. The Step 10 commands
    attach a config to operator sessions through the
    ``OperatorSession.session_store_config`` field; the field carries
    no ``sqlite3.Connection``, no callable, no socket, no subprocess
    handle, and no LLM client (drives I-PERSIST-11 / I-PERSIST-14).
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
    """Typed snapshot of a :class:`brain.tick.BrainState` for save/load."""

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
    """Top-level snapshot persisted by ``save_session``."""

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
    """Return the closed sequence of CREATE TABLE statements."""
    return _SCHEMA_STATEMENTS


def _create_schema(conn: sqlite3.Connection) -> None:
    """Create the v1 schema on ``conn``.

    The caller is responsible for opening ``conn`` and for the BEGIN /
    COMMIT envelope. ``PRAGMA foreign_keys = ON`` is enabled so the
    FOREIGN KEY constraints in the schema are active.
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
# Snapshot construction from live records
# ---------------------------------------------------------------------------


def _snapshot_brain_state(state: BrainState) -> PersistentBrainStateSnapshot:
    """Materialise a :class:`PersistentBrainStateSnapshot` from a live state.

    Values are taken from the live ``BrainState`` record. The snapshot
    constructor validates types and bounds. No raw float arithmetic.
    """
    profile_values_list: list[tuple[str, int, int]] = []
    for cid in sorted(state.profile.domain):
        value = state.profile.values[cid]
        if not isinstance(value, Fraction):
            raise PersistenceError(
                f"profile value for {cid!r} is not a Fraction "
                f"(got {type(value).__name__})"
            )
        profile_values_list.append((str(cid), value.numerator, value.denominator))

    msi_contents_list = tuple(sorted(state.msi.contents))

    threshold = state.msi.threshold
    if not isinstance(threshold, Fraction):
        raise PersistenceError(
            f"msi.threshold is not a Fraction (got {type(threshold).__name__})"
        )

    ptcns_eval_list: list[tuple[str, str]] = []
    for cid in sorted(state.profile.domain):
        eval_value = state.ptcns.eval_map[cid]
        if not isinstance(eval_value, ConsistencyEval):
            raise PersistenceError(
                f"ptcns_eval[{cid!r}] is not a ConsistencyEval"
            )
        ptcns_eval_list.append((str(cid), eval_value.name))

    registry_texts_list: list[tuple[str, str]] = []
    for cid in sorted(state.registry.texts.keys()):
        registry_texts_list.append((str(cid), state.registry.texts[cid]))

    return PersistentBrainStateSnapshot(
        profile_values=tuple(profile_values_list),
        msi_contents=msi_contents_list,
        msi_threshold_num=threshold.numerator,
        msi_threshold_den=threshold.denominator,
        ptcns_eval=tuple(ptcns_eval_list),
        registry_texts=tuple(registry_texts_list),
    )


def snapshot_session(
    session: "OperatorSessionLike",
    config: SessionStoreConfig,
    *,
    now_iso: str,
    created_at_iso: Optional[str],
) -> PersistentSessionSnapshot:
    """Materialise a :class:`PersistentSessionSnapshot` from a live session.

    Pure projection helper: no IO, no kernel builder call, no session
    mutation. Phase 3.10b promoted this name from ``_snapshot_session``
    (corrigenda section 9) so :func:`brain.ui.persistence_observe.db_diff`
    can project the live session for the diff comparison without
    re-exporting a private helper.
    """
    brain_snapshot = _snapshot_brain_state(session.state)

    chunks_list: list[PersistentStreamChunkSnapshot] = []
    for idx, chunk in enumerate(session.stream_history.chunks, start=1):
        if not isinstance(chunk, TextStreamChunk):
            raise PersistenceError(
                f"stream_history.chunks[{idx - 1}] is not a TextStreamChunk"
            )
        chunks_list.append(
            PersistentStreamChunkSnapshot(
                ordinal=idx,
                chunk_id=chunk.chunk_id,
                source=chunk.source.name,
                text=chunk.text,
                provenance_tag=chunk.provenance,
            )
        )

    cand_list: list[PersistentStreamCandidateSnapshot] = []
    for idx, cand in enumerate(session.stream_candidates, start=1):
        if not isinstance(cand, StreamPromotionCandidate):
            raise PersistenceError(
                f"stream_candidates[{idx - 1}] is not a StreamPromotionCandidate"
            )
        cand_list.append(
            PersistentStreamCandidateSnapshot(
                ordinal=idx,
                candidate_id=cand.candidate_id,
                target_content_id=cand.target_content_id,
                chunk_id=cand.chunk_id,
                pattern_id=cand.pattern_id,
                source=cand.source.name,
                text=cand.text,
                provenance_tag=cand.provenance,
            )
        )

    return PersistentSessionSnapshot(
        schema_version=config.schema_version,
        catalog_version=config.catalog_version,
        created_at=created_at_iso or now_iso,
        updated_at=now_iso,
        brain_state=brain_snapshot,
        tick_counter=session.tick_counter,
        stream_chunk_serial=session.stream_chunk_serial,
        stream_chunks=tuple(chunks_list),
        stream_candidates=tuple(cand_list),
    )


# ---------------------------------------------------------------------------
# DB read / write
# ---------------------------------------------------------------------------


def _utc_now_iso(now: Optional[datetime.datetime]) -> str:
    moment = (
        now
        if now is not None
        else datetime.datetime.now(tz=datetime.timezone.utc)
    )
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=datetime.timezone.utc)
    return moment.isoformat()


def _read_meta_value(
    conn: sqlite3.Connection, key: str
) -> Optional[str]:
    row = conn.execute(
        f"SELECT value FROM {META_TABLE_NAME} WHERE key = ?", (key,)
    ).fetchone()
    if row is None:
        return None
    return str(row[0])


def _write_meta_value(
    conn: sqlite3.Connection, key: str, value: str
) -> None:
    conn.execute(
        f"INSERT INTO {META_TABLE_NAME}(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def _clear_kernel_tables(conn: sqlite3.Connection) -> None:
    conn.execute(f"DELETE FROM {STREAM_CANDIDATES_TABLE_NAME}")
    conn.execute(f"DELETE FROM {STREAM_CHUNKS_TABLE_NAME}")
    conn.execute(f"DELETE FROM {SESSION_STATE_TABLE_NAME}")
    conn.execute(f"DELETE FROM {PTCNS_EVAL_TABLE_NAME}")
    conn.execute(f"DELETE FROM {MSI_THRESHOLD_TABLE_NAME}")
    conn.execute(f"DELETE FROM {MSI_CONTENTS_TABLE_NAME}")
    conn.execute(f"DELETE FROM {PROFILE_VALUES_TABLE_NAME}")
    conn.execute(f"DELETE FROM {CONTENT_REGISTRY_TABLE_NAME}")


def _serialize_to_db(
    conn: sqlite3.Connection, snap: PersistentSessionSnapshot
) -> None:
    _write_meta_value(
        conn, META_SCHEMA_VERSION_KEY, str(snap.schema_version)
    )
    _write_meta_value(
        conn, META_CATALOG_VERSION_KEY, snap.catalog_version
    )
    if _read_meta_value(conn, META_CREATED_AT_KEY) is None:
        _write_meta_value(conn, META_CREATED_AT_KEY, snap.created_at)
    _write_meta_value(conn, META_UPDATED_AT_KEY, snap.updated_at)

    for cid, num, den in snap.brain_state.profile_values:
        conn.execute(
            f"INSERT INTO {PROFILE_VALUES_TABLE_NAME}"
            "(content_id, rho_num, rho_den) VALUES (?, ?, ?)",
            (cid, int(num), int(den)),
        )
    for cid in snap.brain_state.msi_contents:
        conn.execute(
            f"INSERT INTO {MSI_CONTENTS_TABLE_NAME}(content_id) VALUES (?)",
            (cid,),
        )
    conn.execute(
        f"INSERT INTO {MSI_THRESHOLD_TABLE_NAME}(id, num, den) "
        "VALUES (1, ?, ?)",
        (int(snap.brain_state.msi_threshold_num),
         int(snap.brain_state.msi_threshold_den)),
    )
    for cid, name in snap.brain_state.ptcns_eval:
        conn.execute(
            f"INSERT INTO {PTCNS_EVAL_TABLE_NAME}(content_id, eval) "
            "VALUES (?, ?)",
            (cid, name),
        )
    for cid, text in snap.brain_state.registry_texts:
        conn.execute(
            f"INSERT INTO {CONTENT_REGISTRY_TABLE_NAME}(content_id, text) "
            "VALUES (?, ?)",
            (cid, text),
        )

    conn.execute(
        f"INSERT INTO {SESSION_STATE_TABLE_NAME}(key, value) VALUES (?, ?)",
        (SESSION_STATE_TICK_COUNTER_KEY, str(snap.tick_counter)),
    )
    conn.execute(
        f"INSERT INTO {SESSION_STATE_TABLE_NAME}(key, value) VALUES (?, ?)",
        (SESSION_STATE_STREAM_SERIAL_KEY, str(snap.stream_chunk_serial)),
    )

    for chunk in snap.stream_chunks:
        conn.execute(
            f"INSERT INTO {STREAM_CHUNKS_TABLE_NAME}"
            "(ordinal, chunk_id, source, text, provenance_tag) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                int(chunk.ordinal),
                chunk.chunk_id,
                chunk.source,
                chunk.text,
                chunk.provenance_tag,
            ),
        )
    for cand in snap.stream_candidates:
        conn.execute(
            f"INSERT INTO {STREAM_CANDIDATES_TABLE_NAME}"
            "(ordinal, candidate_id, target_content_id, chunk_id, "
            "pattern_id, source, text, provenance_tag) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                int(cand.ordinal),
                cand.candidate_id,
                cand.target_content_id,
                cand.chunk_id,
                cand.pattern_id,
                cand.source,
                cand.text,
                cand.provenance_tag,
            ),
        )


def _deserialize_from_db(
    conn: sqlite3.Connection,
) -> PersistentSessionSnapshot:
    schema_text = _read_meta_value(conn, META_SCHEMA_VERSION_KEY)
    if schema_text is None:
        raise PersistenceError(
            "session DB is missing meta.schema_version row"
        )
    try:
        schema_version = int(schema_text)
    except (TypeError, ValueError) as exc:
        raise PersistenceError(
            f"meta.schema_version is not a valid integer: {schema_text!r}"
        ) from exc
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise PersistenceError(
            f"unsupported schema_version: {schema_version}; expected one of "
            f"{sorted(SUPPORTED_SCHEMA_VERSIONS)!r}"
        )

    catalog_version = _read_meta_value(conn, META_CATALOG_VERSION_KEY)
    if catalog_version is None:
        raise PersistenceError(
            "session DB is missing meta.catalog_version row"
        )
    created_at = _read_meta_value(conn, META_CREATED_AT_KEY)
    if created_at is None:
        raise PersistenceError(
            "session DB is missing meta.created_at row"
        )
    updated_at = _read_meta_value(conn, META_UPDATED_AT_KEY)
    if updated_at is None:
        raise PersistenceError(
            "session DB is missing meta.updated_at row"
        )

    profile_rows = list(conn.execute(
        f"SELECT content_id, rho_num, rho_den FROM {PROFILE_VALUES_TABLE_NAME} "
        "ORDER BY content_id"
    ))
    msi_rows = list(conn.execute(
        f"SELECT content_id FROM {MSI_CONTENTS_TABLE_NAME} ORDER BY content_id"
    ))
    threshold_row = conn.execute(
        f"SELECT num, den FROM {MSI_THRESHOLD_TABLE_NAME} WHERE id = 1"
    ).fetchone()
    if threshold_row is None:
        raise PersistenceError(
            "session DB is missing msi_threshold row (id = 1)"
        )
    eval_rows = list(conn.execute(
        f"SELECT content_id, eval FROM {PTCNS_EVAL_TABLE_NAME} "
        "ORDER BY content_id"
    ))
    registry_rows = list(conn.execute(
        f"SELECT content_id, text FROM {CONTENT_REGISTRY_TABLE_NAME} "
        "ORDER BY content_id"
    ))

    brain_snapshot = PersistentBrainStateSnapshot(
        profile_values=tuple(
            (str(cid), int(num), int(den)) for cid, num, den in profile_rows
        ),
        msi_contents=tuple(str(row[0]) for row in msi_rows),
        msi_threshold_num=int(threshold_row[0]),
        msi_threshold_den=int(threshold_row[1]),
        ptcns_eval=tuple((str(cid), str(name)) for cid, name in eval_rows),
        registry_texts=tuple(
            (str(cid), str(text)) for cid, text in registry_rows
        ),
    )

    tick_counter_text = _read_session_state_value(
        conn, SESSION_STATE_TICK_COUNTER_KEY
    )
    if tick_counter_text is None:
        raise PersistenceError(
            "session DB is missing session_state.tick_counter row"
        )
    try:
        tick_counter = int(tick_counter_text)
    except (TypeError, ValueError) as exc:
        raise PersistenceError(
            f"session_state.tick_counter is not an integer: "
            f"{tick_counter_text!r}"
        ) from exc

    stream_serial_text = _read_session_state_value(
        conn, SESSION_STATE_STREAM_SERIAL_KEY
    )
    if stream_serial_text is None:
        raise PersistenceError(
            "session DB is missing session_state.stream_chunk_serial row"
        )
    try:
        stream_chunk_serial = int(stream_serial_text)
    except (TypeError, ValueError) as exc:
        raise PersistenceError(
            f"session_state.stream_chunk_serial is not an integer: "
            f"{stream_serial_text!r}"
        ) from exc

    chunk_rows = list(conn.execute(
        f"SELECT ordinal, chunk_id, source, text, provenance_tag "
        f"FROM {STREAM_CHUNKS_TABLE_NAME} ORDER BY ordinal"
    ))
    chunk_snapshots = tuple(
        PersistentStreamChunkSnapshot(
            ordinal=int(row[0]),
            chunk_id=str(row[1]),
            source=str(row[2]),
            text=str(row[3]),
            provenance_tag=str(row[4]),
        )
        for row in chunk_rows
    )

    cand_rows = list(conn.execute(
        f"SELECT ordinal, candidate_id, target_content_id, chunk_id, "
        f"pattern_id, source, text, provenance_tag "
        f"FROM {STREAM_CANDIDATES_TABLE_NAME} ORDER BY ordinal"
    ))
    cand_snapshots = tuple(
        PersistentStreamCandidateSnapshot(
            ordinal=int(row[0]),
            candidate_id=str(row[1]),
            target_content_id=str(row[2]),
            chunk_id=str(row[3]),
            pattern_id=None if row[4] is None else str(row[4]),
            source=str(row[5]),
            text=str(row[6]),
            provenance_tag=str(row[7]),
        )
        for row in cand_rows
    )

    return PersistentSessionSnapshot(
        schema_version=schema_version,
        catalog_version=catalog_version,
        created_at=created_at,
        updated_at=updated_at,
        brain_state=brain_snapshot,
        tick_counter=tick_counter,
        stream_chunk_serial=stream_chunk_serial,
        stream_chunks=chunk_snapshots,
        stream_candidates=cand_snapshots,
    )


def _read_session_state_value(
    conn: sqlite3.Connection, key: str
) -> Optional[str]:
    row = conn.execute(
        f"SELECT value FROM {SESSION_STATE_TABLE_NAME} WHERE key = ?",
        (key,),
    ).fetchone()
    if row is None:
        return None
    return str(row[0])


# ---------------------------------------------------------------------------
# Builder routing on load
# ---------------------------------------------------------------------------


def _text_stream_source_from_name(name: str) -> TextStreamSource:
    for member in TextStreamSource:
        if member.name == name:
            return member
    raise PersistenceError(
        f"unknown TextStreamSource name: {name!r}"
    )


def _consistency_eval_from_name(name: str) -> ConsistencyEval:
    for member in ConsistencyEval:
        if member.name == name:
            return member
    raise PersistenceError(
        f"unknown ConsistencyEval name: {name!r}"
    )


def _reconstruct_brain_state(
    snap: PersistentBrainStateSnapshot,
) -> BrainState:
    profile_values: dict[str, Fraction] = {
        cid: Fraction(num, den) for cid, num, den in snap.profile_values
    }
    if COGITO_ID not in profile_values:
        raise PersistenceError(
            f"profile_values is missing reserved COGITO_ID ({COGITO_ID!r})"
        )
    if profile_values[COGITO_ID] != Fraction(1):
        raise PersistenceError(
            f"persisted COGITO_ID rho is {profile_values[COGITO_ID]}; "
            "must be 1 (COGITO_ID cannot be overwritten by persisted data)"
        )
    if COGITO_ID not in snap.msi_contents:
        raise PersistenceError(
            f"msi_contents is missing reserved COGITO_ID ({COGITO_ID!r})"
        )
    profile = make_profile_with_cogito(profile_values)
    msi = make_msi(
        profile,
        contents=frozenset(snap.msi_contents),
        threshold=Fraction(snap.msi_threshold_num, snap.msi_threshold_den),
    )
    eval_map: dict[str, ConsistencyEval] = {}
    for cid, name in snap.ptcns_eval:
        eval_map[cid] = _consistency_eval_from_name(name)
    if eval_map.get(COGITO_ID) is not ConsistencyEval.PRESERVE:
        raise PersistenceError(
            "persisted ptcns_eval[COGITO_ID] is not PRESERVE "
            "(COGITO_ID cannot be overwritten by persisted data)"
        )
    ptcns = make_ptcns(msi, eval_map=eval_map)

    registry_dict = {cid: text for cid, text in snap.registry_texts}
    registry = ContentRegistry(texts=MappingProxyType(registry_dict))

    return BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)


def _reconstruct_stream_history(
    chunks: tuple[PersistentStreamChunkSnapshot, ...],
) -> TextStreamHistory:
    rebuilt: list[TextStreamChunk] = []
    for chunk in chunks:
        rebuilt.append(
            make_text_stream_chunk(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                source=_text_stream_source_from_name(chunk.source),
                provenance=chunk.provenance_tag,
            )
        )
    return TextStreamHistory(chunks=tuple(rebuilt))


def _reconstruct_stream_candidates(
    candidates: tuple[PersistentStreamCandidateSnapshot, ...],
) -> tuple[StreamPromotionCandidate, ...]:
    rebuilt: list[StreamPromotionCandidate] = []
    for cand in candidates:
        rebuilt.append(
            make_stream_promotion_candidate(
                candidate_id=cand.candidate_id,
                target_content_id=cand.target_content_id,
                source=_text_stream_source_from_name(cand.source),
                chunk_id=cand.chunk_id,
                text=cand.text,
                provenance=cand.provenance_tag,
                pattern_id=cand.pattern_id,
            )
        )
    return tuple(rebuilt)


# ---------------------------------------------------------------------------
# Public save / load helpers
# ---------------------------------------------------------------------------


# Typing-shim alias so the helpers can accept an `OperatorSession`-shaped
# argument without importing `OperatorSession` at module scope (which
# would create a circular import: session.py needs SessionStoreConfig
# from this module). The session-resource audit fixture confirms there
# is no `sqlite3.Connection` field on the actual `OperatorSession`.
OperatorSessionLike = object  # documented as `brain.ui.session.OperatorSession`


def save_session(
    session: "OperatorSessionLike",
    config: SessionStoreConfig,
    *,
    now: Optional[datetime.datetime] = None,
) -> SaveSessionResult:
    """Transactionally save ``session`` to ``config.db_path``.

    Drives I-PERSIST-07 (failed save preserves live session) and
    I-PERSIST-10 (save transaction atomic). Returns
    :class:`SaveSessionResult` on success; raises
    :class:`PersistenceError` on any IO / constructor / integrity error.
    """
    if not isinstance(config, SessionStoreConfig):
        raise PersistenceError(
            "save_session requires a SessionStoreConfig "
            f"(got {type(config).__name__})"
        )
    db_path = config.db_path
    if db_path.exists() and db_path.is_dir():
        raise PersistenceError(
            f"session DB path {db_path!s} is a directory; refusing to save"
        )

    now_iso = _utc_now_iso(now)

    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(str(db_path), isolation_level=None)
        # Schema bootstrap runs in autocommit (outside the data
        # transaction) so a rolled-back data write does not also drop
        # the schema. CREATE TABLE IF NOT EXISTS is idempotent.
        conn.execute("PRAGMA foreign_keys = ON")
        _create_schema(conn)

        # The data transaction is the atomic unit (drives I-PERSIST-10).
        try:
            conn.execute("BEGIN IMMEDIATE")
            created_at_existing = _read_meta_value(
                conn, META_CREATED_AT_KEY
            )
            snap = snapshot_session(
                session,
                config,
                now_iso=now_iso,
                created_at_iso=created_at_existing,
            )
            _clear_kernel_tables(conn)
            _serialize_to_db(conn, snap)
            conn.execute("COMMIT")
        except BaseException:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
    except PersistenceError:
        raise
    except (sqlite3.Error, ValueError, TypeError) as exc:
        raise PersistenceError(f"save_session failed: {exc}") from exc
    finally:
        if conn is not None:
            conn.close()

    return SaveSessionResult(
        db_path=db_path,
        schema_version=config.schema_version,
        catalog_version=config.catalog_version,
        updated_at=now_iso,
        saved_chunks=len(snap.stream_chunks),
        saved_candidates=len(snap.stream_candidates),
    )


def load_session(
    config: SessionStoreConfig,
    *,
    rebuild_candidates_if_missing: bool = True,
) -> tuple["OperatorSessionLike", LoadSessionResult]:
    """Read ``config.db_path`` and reconstruct an :class:`OperatorSession`.

    Opens the DB in sqlite3 uri ``mode=ro`` so a load never mutates the
    on-disk file. Builds typed snapshots, reconstructs kernel state
    through the existing public builders (drives I-PERSIST-05), runs
    :func:`brain.tick.assert_state_invariants` on the candidate state
    (drives I-PERSIST-06), and returns the candidate session together
    with a :class:`LoadSessionResult`. Raises
    :class:`PersistenceError` on any error; the caller is responsible
    for swapping the candidate into the live session only on success.
    """
    if not isinstance(config, SessionStoreConfig):
        raise PersistenceError(
            "load_session requires a SessionStoreConfig "
            f"(got {type(config).__name__})"
        )
    db_path = config.db_path
    if not db_path.exists():
        raise PersistenceError(
            f"session DB path {db_path!s} does not exist"
        )
    if not db_path.is_file():
        raise PersistenceError(
            f"session DB path {db_path!s} is not a regular file"
        )

    uri = pathlib.Path(db_path).resolve().as_uri() + "?mode=ro"

    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(uri, uri=True)
        conn.execute("PRAGMA foreign_keys = ON")
        snap = _deserialize_from_db(conn)
    except PersistenceError:
        raise
    except (sqlite3.Error, ValueError, TypeError) as exc:
        raise PersistenceError(f"load_session failed: {exc}") from exc
    finally:
        if conn is not None:
            conn.close()

    try:
        candidate_state = _reconstruct_brain_state(snap.brain_state)
        stream_history = _reconstruct_stream_history(snap.stream_chunks)
        if snap.stream_candidates:
            candidates = _reconstruct_stream_candidates(snap.stream_candidates)
            rebuilt_candidates = False
        elif rebuild_candidates_if_missing:
            candidates = ()
            rebuilt_candidates = True
        else:
            candidates = ()
            rebuilt_candidates = False
    except PersistenceError:
        raise
    except (ValueError, TypeError) as exc:
        raise PersistenceError(
            f"load_session: kernel reconstruction failed: {exc}"
        ) from exc

    try:
        assert_state_invariants(candidate_state)
    except (ValueError, TypeError, AssertionError) as exc:
        raise PersistenceError(
            f"load_session: invariant check failed: {exc}"
        ) from exc

    # Constructing OperatorSession is the final assembly step. Local
    # import avoids the persistence <-> session module import cycle.
    from brain.ui.session import OperatorSession  # noqa: PLC0415

    try:
        candidate_session = OperatorSession(
            state=candidate_state,
            tick_counter=snap.tick_counter,
            stream_history=stream_history,
            stream_candidates=candidates,
            stream_chunk_serial=snap.stream_chunk_serial,
            session_store_config=config,
        )
    except (ValueError, TypeError) as exc:
        raise PersistenceError(
            f"load_session: OperatorSession construction failed: {exc}"
        ) from exc

    return candidate_session, LoadSessionResult(
        db_path=db_path,
        schema_version=snap.schema_version,
        catalog_version=snap.catalog_version,
        loaded_chunks=len(snap.stream_chunks),
        loaded_candidates=len(snap.stream_candidates),
        rebuilt_candidates=rebuilt_candidates,
    )


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
    "save_session",
    "load_session",
    "snapshot_session",
)
