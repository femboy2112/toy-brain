"""Phase 3.10b Persistence Observability — typed read-only reports + diff.

This module exposes:

* :class:`DbSummaryReport`, :class:`ProfileSummaryRow`,
  :class:`ProfileSummaryReport`, :class:`StreamDbSummaryRow`,
  :class:`StreamDbSummaryReport`, :class:`DbDiffField`,
  :class:`DbDiffReport` — frozen / slotted typed records with
  ``__post_init__`` bound enforcement.
* :func:`db_summary`, :func:`profile_summary`, :func:`stream_db_summary`,
  :func:`db_diff` — four operational read-only observers; every one
  opens the configured DB in ``mode=ro`` inside a ``with conn:`` block
  and never invokes a kernel builder.
* Locked default row caps: :data:`PROFILE_SUMMARY_ROW_CAP` = 64,
  :data:`STREAM_DB_SUMMARY_HEAD_CAP` = 8,
  :data:`STREAM_DB_SUMMARY_TAIL_CAP` = 8, :data:`DB_DIFF_ROW_CAP` = 32,
  :data:`STREAM_TEXT_PREVIEW_MAX_LEN` = 64,
  :data:`PROFILE_VALUE_STRING_MAX_LEN` = 64,
  :data:`OPS_REPORT_TEXT_MAX_LEN` = 256 (re-exported from
  :mod:`brain.ui.persistence_ops`).

Catalog rows driven from here (Phase 3.10b):

* ``I-OBSERVE-01`` (REQUIRED) — ``/db-summary`` reads in ``mode=ro``;
  closed ``with`` block; bounded report.
* ``I-OBSERVE-02`` (REQUIRED) — ``/profile-summary`` returns exact-
  Fraction ``"num/den"`` rows, COGITO first, deterministic sort.
* ``I-OBSERVE-03`` (REQUIRED) — ``/stream-db-summary`` returns bounded
  head + tail with text-preview cap.
* ``I-OBSERVE-04`` (REQUIRED) — ``/db-diff`` reports finite field
  enumeration; ``"<missing>"`` on one-sided absence; never invents
  defaults.
* ``I-OBSERVE-05`` (REQUIRED) — observability commands never activate
  saved state and never mutate live ``BrainState``.
* ``I-OBSERVE-06`` (STRUCTURAL) — module static audit (import-set,
  module-level-statement audit).
* ``I-OBSERVE-07`` (STRUCTURAL) — no builder call anywhere in this
  module (no ``make_profile_with_cogito`` /
  ``make_msi`` / ``make_ptcns`` / ``ContentRegistry`` / ``BrainState`` /
  ``make_text_stream_chunk`` / ``TextStreamHistory`` /
  ``make_stream_promotion_candidate`` / ``OperatorSession``).
* ``I-OBSERVE-08`` (STRUCTURAL) — session resource audit (Phase 3.10b
  adds no new ``OperatorSession`` field).
* ``I-OBSERVE-09`` (STRUCTURAL) — locked default row caps.
* ``I-OBSERVE-10`` (STRUCTURAL) — defensive autosave-absent audit.

Hard boundaries pinned by
``PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_CORRIGENDA.md`` and
``PHASE3_10_OPS_OBSERVABILITY_CATALOG_PATCH_PLAN.md``:

* SQLite via the standard-library ``sqlite3`` module only — no
  ``pickle`` / ``shelve`` / ``marshal`` / ``dill`` / ``cloudpickle``
  / ``joblib`` / ``subprocess`` / ``socket`` / ``urllib`` / ``http``
  / ``requests`` / ``curses`` / ``brain.tick`` / ``brain.tlica``
  internals beyond what ``brain.ui.persistence`` re-exports /
  ``brain.llm``.
* Every helper opens the DB through
  ``sqlite3.connect("file:<path>?mode=ro", uri=True)`` inside a
  ``with conn:`` block.
* No helper invokes any kernel builder; the diff calls
  :func:`brain.ui.persistence.snapshot_session` (a pure projection
  promoted in the Phase 3.10b narrow extension) on the live side and
  :func:`brain.ui.persistence._deserialize_from_db` on the saved side.
* All ``Fraction`` values display as exact ``"num/den"`` strings via a
  single shared :func:`_render_fraction` helper; no ``float()`` /
  ``repr()`` / JSON leakage.
* The diff is over the finite field enumeration declared in
  :data:`_DIFF_FIELD_PREFIXES` / :data:`_DIFF_FIXED_FIELDS`; unknown
  field names raise at :class:`DbDiffField` construction time.
* Phase 3.10b adds NO new ``OperatorSession`` field.
* No autosave entry point exists; no ``@atexit`` / signal /
  threading / asyncio autosave hook is registered.
* Module-level statements are limited to imports, constants, function
  defs, and class defs (plus this docstring).
"""
from __future__ import annotations

import pathlib
import sqlite3
from dataclasses import dataclass
from fractions import Fraction

from brain.tlica.profile import COGITO_ID
from brain.ui.persistence import (
    CONTENT_REGISTRY_TABLE_NAME,
    META_CATALOG_VERSION_KEY,
    META_CREATED_AT_KEY,
    META_SCHEMA_VERSION_KEY,
    META_UPDATED_AT_KEY,
    MSI_CONTENTS_TABLE_NAME,
    MSI_THRESHOLD_TABLE_NAME,
    PROFILE_VALUES_TABLE_NAME,
    PTCNS_EVAL_TABLE_NAME,
    PersistenceError,
    PersistentSessionSnapshot,
    STREAM_CANDIDATES_TABLE_NAME,
    STREAM_CHUNKS_TABLE_NAME,
    SESSION_STATE_STREAM_SERIAL_KEY,
    SESSION_STATE_TABLE_NAME,
    SESSION_STATE_TICK_COUNTER_KEY,
    SessionStoreConfig,
    _deserialize_from_db,
    _read_meta_value,
    snapshot_session,
)
from brain.ui.persistence_ops import OPS_REPORT_TEXT_MAX_LEN


# ---------------------------------------------------------------------------
# Locked default row caps (drives I-OBSERVE-09)
# ---------------------------------------------------------------------------


#: Maximum number of profile rows :func:`profile_summary` returns before
#: setting ``truncated=True``. Locked by the corrigenda section 4.
PROFILE_SUMMARY_ROW_CAP: int = 64


#: Maximum number of chunks in :class:`StreamDbSummaryReport.head`.
STREAM_DB_SUMMARY_HEAD_CAP: int = 8


#: Maximum number of chunks in :class:`StreamDbSummaryReport.tail`.
STREAM_DB_SUMMARY_TAIL_CAP: int = 8


#: Maximum number of :class:`DbDiffField` rows :func:`db_diff` returns
#: before setting ``truncated=True``.
DB_DIFF_ROW_CAP: int = 32


#: Maximum length of :attr:`StreamDbSummaryRow.text_preview` (chars).
STREAM_TEXT_PREVIEW_MAX_LEN: int = 64


#: Maximum length of an exact-Fraction ``"num/den"`` string field in a
#: Phase 3.10b report.
PROFILE_VALUE_STRING_MAX_LEN: int = 64


#: Literal value used on the live / saved side of a :class:`DbDiffField`
#: when the field is absent on one side. Never substituted with a
#: silent default such as ``0`` or ``""``.
DIFF_MISSING_MARKER: str = "<missing>"


# ---------------------------------------------------------------------------
# Finite DbDiffField name enumeration (drives I-OBSERVE-04)
# ---------------------------------------------------------------------------


#: Fully-qualified field names with no prefix-based suffix. The diff is
#: closed over this set plus the prefix-keyed entries below.
_DIFF_FIXED_FIELDS: frozenset[str] = frozenset({
    "msi.contents",
    "msi.threshold",
    "tick_counter",
    "stream_chunk_serial",
    "stream_history.count",
    "stream_candidates.count",
})


#: Allowed ``"<prefix>.<content_id>"`` prefixes for content-keyed fields.
_DIFF_FIELD_PREFIXES: frozenset[str] = frozenset({
    "profile.",
    "ptcns_eval.",
    "registry.",
})


def _validate_diff_field_name(name: str) -> None:
    """Raise if ``name`` is outside the closed enumeration."""
    if not isinstance(name, str):
        raise TypeError(
            f"DbDiffField.field must be a str (got {type(name).__name__})"
        )
    if not name:
        raise ValueError("DbDiffField.field must be non-empty")
    if name in _DIFF_FIXED_FIELDS:
        return
    for prefix in _DIFF_FIELD_PREFIXES:
        if name.startswith(prefix):
            suffix = name[len(prefix):]
            if not suffix:
                raise ValueError(
                    f"DbDiffField.field {name!r} has empty content_id "
                    "suffix"
                )
            if not suffix.isprintable():
                raise ValueError(
                    f"DbDiffField.field {name!r} content_id suffix is "
                    "not printable"
                )
            return
    raise ValueError(
        f"DbDiffField.field {name!r} is not in the closed enumeration; "
        f"expected one of {sorted(_DIFF_FIXED_FIELDS)!r} or a name "
        f"starting with one of {sorted(_DIFF_FIELD_PREFIXES)!r}"
    )


# ---------------------------------------------------------------------------
# Bound enforcement helpers (mirror the persistence_ops style)
# ---------------------------------------------------------------------------


def _require_bounded_str(
    label: str, value: str, *, cap: int = OPS_REPORT_TEXT_MAX_LEN
) -> None:
    """Reject non-str / non-printable / over-cap report string fields.

    The empty string is allowed (used for "no value" markers on the
    missing-DB / one-sided-absence code paths and for the success-case
    ``error_text``).
    """
    if not isinstance(value, str):
        raise TypeError(
            f"{label} must be a str (got {type(value).__name__})"
        )
    if value and not value.isprintable():
        raise ValueError(
            f"{label} must be printable text (got {value!r})"
        )
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
        raise ValueError(
            f"{label} must be non-negative (got {value!r})"
        )


def _require_bool(label: str, value: bool) -> None:
    if not isinstance(value, bool):
        raise TypeError(
            f"{label} must be a bool (got {type(value).__name__})"
        )


def _bound_error_text(value: str) -> str:
    """Truncate / coerce ``value`` so it satisfies the report cap."""
    if not isinstance(value, str):
        value = str(value)
    if not value.isprintable():
        value = "".join(ch if ch.isprintable() else "?" for ch in value)
    if len(value) > OPS_REPORT_TEXT_MAX_LEN:
        value = value[: OPS_REPORT_TEXT_MAX_LEN - 1] + "…"
    return value


def _render_fraction(num: int, den: int) -> str:
    """Render an integer ``num``/``den`` pair as the exact ``"num/den"`` string.

    This is the single shared renderer for all Phase 3.10b reports
    (drives the "no float / no repr / no str(Fraction)" requirement of
    I-OBSERVE-02). The caller is responsible for ensuring ``den > 0``
    and integer types; this helper does not normalize / reduce the
    fraction so what comes out of the DB lands in the report verbatim.
    """
    if not isinstance(num, int) or isinstance(num, bool):
        raise TypeError(
            f"_render_fraction num must be int (got {type(num).__name__})"
        )
    if not isinstance(den, int) or isinstance(den, bool):
        raise TypeError(
            f"_render_fraction den must be int (got {type(den).__name__})"
        )
    if den <= 0:
        raise ValueError(
            f"_render_fraction den must be positive (got {den!r})"
        )
    return f"{num}/{den}"


def _ro_connect_uri(db_path: pathlib.Path) -> str:
    """Return the sqlite3 file URI for opening ``db_path`` in mode=ro."""
    return pathlib.Path(db_path).resolve().as_uri() + "?mode=ro"


# ---------------------------------------------------------------------------
# Typed report records (frozen + slots, __post_init__ validation)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DbSummaryReport:
    """Bounded read-only summary of the configured session DB.

    Returned by :func:`db_summary`. Every string field is bounded by
    :data:`OPS_REPORT_TEXT_MAX_LEN`; every integer field is
    non-negative; the ``msi_threshold`` field is the exact
    ``"num/den"`` string.
    """

    db_path_str: str
    schema_version: int
    catalog_version: str
    created_at: str
    updated_at: str
    profile_row_count: int
    msi_content_count: int
    msi_threshold: str
    ptcns_eval_row_count: int
    registry_row_count: int
    stream_chunk_count: int
    stream_candidate_count: int
    tick_counter: int
    stream_chunk_serial: int
    error_text: str

    def __post_init__(self) -> None:
        _require_bounded_str("DbSummaryReport.db_path_str", self.db_path_str)
        _require_nonneg_int(
            "DbSummaryReport.schema_version", self.schema_version
        )
        _require_bounded_str(
            "DbSummaryReport.catalog_version", self.catalog_version
        )
        _require_bounded_str("DbSummaryReport.created_at", self.created_at)
        _require_bounded_str("DbSummaryReport.updated_at", self.updated_at)
        _require_nonneg_int(
            "DbSummaryReport.profile_row_count", self.profile_row_count
        )
        _require_nonneg_int(
            "DbSummaryReport.msi_content_count", self.msi_content_count
        )
        _require_bounded_str(
            "DbSummaryReport.msi_threshold",
            self.msi_threshold,
            cap=PROFILE_VALUE_STRING_MAX_LEN,
        )
        _require_nonneg_int(
            "DbSummaryReport.ptcns_eval_row_count",
            self.ptcns_eval_row_count,
        )
        _require_nonneg_int(
            "DbSummaryReport.registry_row_count", self.registry_row_count
        )
        _require_nonneg_int(
            "DbSummaryReport.stream_chunk_count", self.stream_chunk_count
        )
        _require_nonneg_int(
            "DbSummaryReport.stream_candidate_count",
            self.stream_candidate_count,
        )
        _require_nonneg_int(
            "DbSummaryReport.tick_counter", self.tick_counter
        )
        _require_nonneg_int(
            "DbSummaryReport.stream_chunk_serial", self.stream_chunk_serial
        )
        _require_bounded_str("DbSummaryReport.error_text", self.error_text)


@dataclass(frozen=True, slots=True)
class ProfileSummaryRow:
    """One row of :class:`ProfileSummaryReport`.

    ``value_str`` is the exact ``"num/den"`` string for the row's
    persisted Fraction (rendered via :func:`_render_fraction`); it is
    never a float / repr / JSON string.
    """

    content_id: str
    value_str: str

    def __post_init__(self) -> None:
        _require_bounded_str(
            "ProfileSummaryRow.content_id",
            self.content_id,
            cap=OPS_REPORT_TEXT_MAX_LEN,
        )
        if not self.content_id:
            raise ValueError(
                "ProfileSummaryRow.content_id must be non-empty"
            )
        _require_bounded_str(
            "ProfileSummaryRow.value_str",
            self.value_str,
            cap=PROFILE_VALUE_STRING_MAX_LEN,
        )
        if not self.value_str:
            raise ValueError(
                "ProfileSummaryRow.value_str must be non-empty"
            )


@dataclass(frozen=True, slots=True)
class ProfileSummaryReport:
    """Bounded :class:`ProfileSummaryRow` listing from the saved DB."""

    db_path_str: str
    rows: tuple[ProfileSummaryRow, ...]
    truncated: bool
    error_text: str

    def __post_init__(self) -> None:
        _require_bounded_str(
            "ProfileSummaryReport.db_path_str", self.db_path_str
        )
        if not isinstance(self.rows, tuple):
            raise TypeError(
                "ProfileSummaryReport.rows must be a tuple "
                f"(got {type(self.rows).__name__})"
            )
        for row in self.rows:
            if not isinstance(row, ProfileSummaryRow):
                raise TypeError(
                    "ProfileSummaryReport.rows entries must be "
                    f"ProfileSummaryRow (got {type(row).__name__})"
                )
        _require_bool("ProfileSummaryReport.truncated", self.truncated)
        _require_bounded_str(
            "ProfileSummaryReport.error_text", self.error_text
        )


@dataclass(frozen=True, slots=True)
class StreamDbSummaryRow:
    """One row of :class:`StreamDbSummaryReport` head / tail.

    ``text_preview`` is bounded by :data:`STREAM_TEXT_PREVIEW_MAX_LEN`;
    the full chunk text is never returned (drives the bounded preview
    half of I-OBSERVE-03).
    """

    ordinal: int
    chunk_id: str
    source: str
    tick_at_event: int
    provenance_tag: str
    text_preview: str

    def __post_init__(self) -> None:
        _require_nonneg_int("StreamDbSummaryRow.ordinal", self.ordinal)
        _require_bounded_str(
            "StreamDbSummaryRow.chunk_id", self.chunk_id
        )
        if not self.chunk_id:
            raise ValueError(
                "StreamDbSummaryRow.chunk_id must be non-empty"
            )
        _require_bounded_str("StreamDbSummaryRow.source", self.source)
        _require_nonneg_int(
            "StreamDbSummaryRow.tick_at_event", self.tick_at_event
        )
        _require_bounded_str(
            "StreamDbSummaryRow.provenance_tag", self.provenance_tag
        )
        _require_bounded_str(
            "StreamDbSummaryRow.text_preview",
            self.text_preview,
            cap=STREAM_TEXT_PREVIEW_MAX_LEN,
        )


@dataclass(frozen=True, slots=True)
class StreamDbSummaryReport:
    """Bounded head + tail summary of the saved ``stream_chunks`` table."""

    db_path_str: str
    chunk_count: int
    candidate_count: int
    first_ordinal: int
    last_ordinal: int
    head: tuple[StreamDbSummaryRow, ...]
    tail: tuple[StreamDbSummaryRow, ...]
    truncated: bool
    error_text: str

    def __post_init__(self) -> None:
        _require_bounded_str(
            "StreamDbSummaryReport.db_path_str", self.db_path_str
        )
        _require_nonneg_int(
            "StreamDbSummaryReport.chunk_count", self.chunk_count
        )
        _require_nonneg_int(
            "StreamDbSummaryReport.candidate_count", self.candidate_count
        )
        _require_nonneg_int(
            "StreamDbSummaryReport.first_ordinal", self.first_ordinal
        )
        _require_nonneg_int(
            "StreamDbSummaryReport.last_ordinal", self.last_ordinal
        )
        if not isinstance(self.head, tuple):
            raise TypeError(
                "StreamDbSummaryReport.head must be a tuple "
                f"(got {type(self.head).__name__})"
            )
        for row in self.head:
            if not isinstance(row, StreamDbSummaryRow):
                raise TypeError(
                    "StreamDbSummaryReport.head entries must be "
                    f"StreamDbSummaryRow (got {type(row).__name__})"
                )
        if len(self.head) > STREAM_DB_SUMMARY_HEAD_CAP:
            raise ValueError(
                f"StreamDbSummaryReport.head length {len(self.head)} "
                f"exceeds STREAM_DB_SUMMARY_HEAD_CAP="
                f"{STREAM_DB_SUMMARY_HEAD_CAP}"
            )
        if not isinstance(self.tail, tuple):
            raise TypeError(
                "StreamDbSummaryReport.tail must be a tuple "
                f"(got {type(self.tail).__name__})"
            )
        for row in self.tail:
            if not isinstance(row, StreamDbSummaryRow):
                raise TypeError(
                    "StreamDbSummaryReport.tail entries must be "
                    f"StreamDbSummaryRow (got {type(row).__name__})"
                )
        if len(self.tail) > STREAM_DB_SUMMARY_TAIL_CAP:
            raise ValueError(
                f"StreamDbSummaryReport.tail length {len(self.tail)} "
                f"exceeds STREAM_DB_SUMMARY_TAIL_CAP="
                f"{STREAM_DB_SUMMARY_TAIL_CAP}"
            )
        _require_bool(
            "StreamDbSummaryReport.truncated", self.truncated
        )
        _require_bounded_str(
            "StreamDbSummaryReport.error_text", self.error_text
        )


@dataclass(frozen=True, slots=True)
class DbDiffField:
    """One difference cell between live and saved state.

    The ``field`` string must come from the closed enumeration declared
    by :func:`_validate_diff_field_name`. The ``live`` and ``saved``
    fields use the exact ``"num/den"`` string for kernel-numeric values,
    integer text for counters, the comma-joined sorted list for the
    ``msi.contents`` set, and the literal :data:`DIFF_MISSING_MARKER`
    (``"<missing>"``) for one-sided absence.
    """

    field: str
    live: str
    saved: str

    def __post_init__(self) -> None:
        _validate_diff_field_name(self.field)
        _require_bounded_str(
            "DbDiffField.live",
            self.live,
            cap=OPS_REPORT_TEXT_MAX_LEN,
        )
        if not self.live:
            raise ValueError("DbDiffField.live must be non-empty")
        _require_bounded_str(
            "DbDiffField.saved",
            self.saved,
            cap=OPS_REPORT_TEXT_MAX_LEN,
        )
        if not self.saved:
            raise ValueError("DbDiffField.saved must be non-empty")


@dataclass(frozen=True, slots=True)
class DbDiffReport:
    """Bounded live-vs-saved diff over the finite field enumeration."""

    db_path_str: str
    matches: bool
    diff_count: int
    differences: tuple[DbDiffField, ...]
    truncated: bool
    error_text: str

    def __post_init__(self) -> None:
        _require_bounded_str("DbDiffReport.db_path_str", self.db_path_str)
        _require_bool("DbDiffReport.matches", self.matches)
        _require_nonneg_int("DbDiffReport.diff_count", self.diff_count)
        if not isinstance(self.differences, tuple):
            raise TypeError(
                "DbDiffReport.differences must be a tuple "
                f"(got {type(self.differences).__name__})"
            )
        for entry in self.differences:
            if not isinstance(entry, DbDiffField):
                raise TypeError(
                    "DbDiffReport.differences entries must be DbDiffField "
                    f"(got {type(entry).__name__})"
                )
        if len(self.differences) > DB_DIFF_ROW_CAP:
            raise ValueError(
                f"DbDiffReport.differences length {len(self.differences)} "
                f"exceeds DB_DIFF_ROW_CAP={DB_DIFF_ROW_CAP}"
            )
        _require_bool("DbDiffReport.truncated", self.truncated)
        _require_bounded_str("DbDiffReport.error_text", self.error_text)


# ---------------------------------------------------------------------------
# Internal helpers (DB reads + saved-snapshot projection)
# ---------------------------------------------------------------------------


def _table_row_count(conn: sqlite3.Connection, table: str) -> int:
    """Return ``COUNT(*)`` for ``table`` (assumed table name is trusted)."""
    row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    if row is None:
        return 0
    return int(row[0])


def _read_session_state_int(
    conn: sqlite3.Connection, key: str
) -> int:
    row = conn.execute(
        f"SELECT value FROM {SESSION_STATE_TABLE_NAME} WHERE key = ?",
        (key,),
    ).fetchone()
    if row is None:
        return 0
    try:
        return int(row[0])
    except (TypeError, ValueError):
        return 0


def _saved_profile_map(
    snap: PersistentSessionSnapshot,
) -> dict[str, str]:
    """Return ``{content_id: "num/den"}`` from a saved snapshot."""
    out: dict[str, str] = {}
    for cid, num, den in snap.brain_state.profile_values:
        out[cid] = _render_fraction(num, den)
    return out


def _saved_ptcns_map(
    snap: PersistentSessionSnapshot,
) -> dict[str, str]:
    out: dict[str, str] = {}
    for cid, name in snap.brain_state.ptcns_eval:
        out[cid] = name
    return out


def _saved_registry_map(
    snap: PersistentSessionSnapshot,
) -> dict[str, str]:
    out: dict[str, str] = {}
    for cid, text in snap.brain_state.registry_texts:
        out[cid] = text
    return out


def _live_profile_map(session: object) -> dict[str, str]:
    """Read live session.state.profile.values into ``{cid: "num/den"}``.

    Accesses session.state.profile.values directly (no kernel builder
    call; pure read of an immutable mapping). Each value must already
    be a :class:`Fraction`; otherwise a :class:`PersistenceError` is
    raised so the diff cannot silently coerce.
    """
    out: dict[str, str] = {}
    profile = session.state.profile  # type: ignore[attr-defined]
    for cid in profile.domain:
        value = profile.values[cid]
        if not isinstance(value, Fraction):
            raise PersistenceError(
                f"live profile value for {cid!r} is not a Fraction "
                f"(got {type(value).__name__})"
            )
        out[str(cid)] = _render_fraction(value.numerator, value.denominator)
    return out


def _live_ptcns_map(session: object) -> dict[str, str]:
    out: dict[str, str] = {}
    profile = session.state.profile  # type: ignore[attr-defined]
    eval_map = session.state.ptcns.eval_map  # type: ignore[attr-defined]
    for cid in profile.domain:
        eval_value = eval_map[cid]
        out[str(cid)] = eval_value.name
    return out


def _live_registry_map(session: object) -> dict[str, str]:
    out: dict[str, str] = {}
    texts = session.state.registry.texts  # type: ignore[attr-defined]
    for cid in texts:
        out[str(cid)] = texts[cid]
    return out


def _live_msi_contents_str(session: object) -> str:
    contents = session.state.msi.contents  # type: ignore[attr-defined]
    return ",".join(sorted(str(cid) for cid in contents))


def _saved_msi_contents_str(snap: PersistentSessionSnapshot) -> str:
    return ",".join(sorted(snap.brain_state.msi_contents))


def _live_msi_threshold_str(session: object) -> str:
    threshold = session.state.msi.threshold  # type: ignore[attr-defined]
    if not isinstance(threshold, Fraction):
        raise PersistenceError(
            "live msi.threshold is not a Fraction "
            f"(got {type(threshold).__name__})"
        )
    return _render_fraction(threshold.numerator, threshold.denominator)


def _saved_msi_threshold_str(snap: PersistentSessionSnapshot) -> str:
    return _render_fraction(
        snap.brain_state.msi_threshold_num,
        snap.brain_state.msi_threshold_den,
    )


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def db_summary(config: SessionStoreConfig) -> DbSummaryReport:
    """Return a bounded :class:`DbSummaryReport` for ``config.db_path``.

    Drives ``I-OBSERVE-01``. Opens the DB through
    ``sqlite3.connect("file:<path>?mode=ro", uri=True)`` inside a
    ``with conn:`` block, reads meta + per-table row counts, closes.
    Missing DB returns a bounded ``error_text`` with zeroed counts.
    """
    if not isinstance(config, SessionStoreConfig):
        raise PersistenceError(
            "db_summary requires a SessionStoreConfig "
            f"(got {type(config).__name__})"
        )
    db_path = config.db_path
    db_path_str = _bound_error_text(str(db_path))

    if not db_path.exists():
        return DbSummaryReport(
            db_path_str=db_path_str,
            schema_version=0,
            catalog_version="",
            created_at="",
            updated_at="",
            profile_row_count=0,
            msi_content_count=0,
            msi_threshold="",
            ptcns_eval_row_count=0,
            registry_row_count=0,
            stream_chunk_count=0,
            stream_candidate_count=0,
            tick_counter=0,
            stream_chunk_serial=0,
            error_text=_bound_error_text(
                f"session DB at {db_path!s} does not exist"
            ),
        )
    if db_path.is_dir():
        return DbSummaryReport(
            db_path_str=db_path_str,
            schema_version=0,
            catalog_version="",
            created_at="",
            updated_at="",
            profile_row_count=0,
            msi_content_count=0,
            msi_threshold="",
            ptcns_eval_row_count=0,
            registry_row_count=0,
            stream_chunk_count=0,
            stream_candidate_count=0,
            tick_counter=0,
            stream_chunk_serial=0,
            error_text=_bound_error_text(
                f"session DB at {db_path!s} is a directory"
            ),
        )

    uri = _ro_connect_uri(db_path)
    schema_version = 0
    catalog_version = ""
    created_at = ""
    updated_at = ""
    profile_row_count = 0
    msi_content_count = 0
    msi_threshold = ""
    ptcns_eval_row_count = 0
    registry_row_count = 0
    stream_chunk_count = 0
    stream_candidate_count = 0
    tick_counter = 0
    stream_chunk_serial = 0
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

                profile_row_count = _table_row_count(
                    conn, PROFILE_VALUES_TABLE_NAME
                )
                msi_content_count = _table_row_count(
                    conn, MSI_CONTENTS_TABLE_NAME
                )
                threshold_row = conn.execute(
                    f"SELECT num, den FROM {MSI_THRESHOLD_TABLE_NAME} "
                    "WHERE id = 1"
                ).fetchone()
                if threshold_row is not None:
                    try:
                        msi_threshold = _render_fraction(
                            int(threshold_row[0]), int(threshold_row[1])
                        )
                    except (TypeError, ValueError):
                        msi_threshold = ""
                ptcns_eval_row_count = _table_row_count(
                    conn, PTCNS_EVAL_TABLE_NAME
                )
                registry_row_count = _table_row_count(
                    conn, CONTENT_REGISTRY_TABLE_NAME
                )
                stream_chunk_count = _table_row_count(
                    conn, STREAM_CHUNKS_TABLE_NAME
                )
                stream_candidate_count = _table_row_count(
                    conn, STREAM_CANDIDATES_TABLE_NAME
                )
                tick_counter = _read_session_state_int(
                    conn, SESSION_STATE_TICK_COUNTER_KEY
                )
                stream_chunk_serial = _read_session_state_int(
                    conn, SESSION_STATE_STREAM_SERIAL_KEY
                )
            except sqlite3.Error as exc:
                error_text = _bound_error_text(f"summary read failed: {exc}")
    except sqlite3.Error as exc:
        error_text = _bound_error_text(f"open failed: {exc}")

    return DbSummaryReport(
        db_path_str=db_path_str,
        schema_version=schema_version,
        catalog_version=catalog_version,
        created_at=created_at,
        updated_at=updated_at,
        profile_row_count=profile_row_count,
        msi_content_count=msi_content_count,
        msi_threshold=msi_threshold,
        ptcns_eval_row_count=ptcns_eval_row_count,
        registry_row_count=registry_row_count,
        stream_chunk_count=stream_chunk_count,
        stream_candidate_count=stream_candidate_count,
        tick_counter=tick_counter,
        stream_chunk_serial=stream_chunk_serial,
        error_text=error_text,
    )


def _profile_sort_key(content_id: str) -> tuple[int, str]:
    """Return a sort key that places ``COGITO_ID`` first, then ASCII order."""
    return (0 if content_id == COGITO_ID else 1, content_id)


def profile_summary(
    config: SessionStoreConfig,
    *,
    row_cap: int = PROFILE_SUMMARY_ROW_CAP,
) -> ProfileSummaryReport:
    """Read ``profile_values`` in ``mode=ro`` and render exact-Fraction rows.

    Drives ``I-OBSERVE-02``. Rows are sorted with ``COGITO_ID`` first
    then by content_id ASCII-ascending. Each Fraction is rendered via
    :func:`_render_fraction` (a single shared helper; never via
    ``float()``, ``repr()``, or ``str(Fraction(...))``). Truncates at
    ``row_cap`` with ``truncated=True`` when the cap is hit.
    """
    if not isinstance(config, SessionStoreConfig):
        raise PersistenceError(
            "profile_summary requires a SessionStoreConfig "
            f"(got {type(config).__name__})"
        )
    if not isinstance(row_cap, int) or isinstance(row_cap, bool):
        raise PersistenceError(
            "profile_summary row_cap must be an int "
            f"(got {type(row_cap).__name__})"
        )
    if row_cap <= 0:
        raise PersistenceError(
            f"profile_summary row_cap must be positive (got {row_cap!r})"
        )
    db_path = config.db_path
    db_path_str = _bound_error_text(str(db_path))

    if not db_path.exists() or db_path.is_dir():
        return ProfileSummaryReport(
            db_path_str=db_path_str,
            rows=(),
            truncated=False,
            error_text=_bound_error_text(
                f"session DB at {db_path!s} is missing or not a file"
            ),
        )

    uri = _ro_connect_uri(db_path)
    rows: tuple[ProfileSummaryRow, ...] = ()
    truncated = False
    error_text = ""
    try:
        with sqlite3.connect(uri, uri=True) as conn:
            try:
                raw_rows = list(conn.execute(
                    f"SELECT content_id, rho_num, rho_den "
                    f"FROM {PROFILE_VALUES_TABLE_NAME}"
                ))
            except sqlite3.Error as exc:
                error_text = _bound_error_text(
                    f"profile read failed: {exc}"
                )
                raw_rows = []
    except sqlite3.Error as exc:
        error_text = _bound_error_text(f"open failed: {exc}")
        raw_rows = []

    if not error_text:
        try:
            sorted_rows = sorted(
                raw_rows,
                key=lambda r: _profile_sort_key(str(r[0])),
            )
            truncated = len(sorted_rows) > row_cap
            kept = sorted_rows[:row_cap]
            rendered: list[ProfileSummaryRow] = []
            for cid, num, den in kept:
                rendered.append(
                    ProfileSummaryRow(
                        content_id=str(cid),
                        value_str=_render_fraction(int(num), int(den)),
                    )
                )
            rows = tuple(rendered)
        except (TypeError, ValueError) as exc:
            rows = ()
            truncated = False
            error_text = _bound_error_text(
                f"profile render failed: {exc}"
            )

    return ProfileSummaryReport(
        db_path_str=db_path_str,
        rows=rows,
        truncated=truncated,
        error_text=error_text,
    )


def _truncate_preview(text: str) -> str:
    """Coerce ``text`` to printable and truncate to the preview cap."""
    if not isinstance(text, str):
        text = str(text)
    if not text.isprintable():
        text = "".join(ch if ch.isprintable() else "?" for ch in text)
    if len(text) > STREAM_TEXT_PREVIEW_MAX_LEN:
        return text[: STREAM_TEXT_PREVIEW_MAX_LEN - 1] + "…"
    return text


def stream_db_summary(
    config: SessionStoreConfig,
    *,
    head_cap: int = STREAM_DB_SUMMARY_HEAD_CAP,
    tail_cap: int = STREAM_DB_SUMMARY_TAIL_CAP,
) -> StreamDbSummaryReport:
    """Return a bounded head + tail :class:`StreamDbSummaryReport`.

    Drives ``I-OBSERVE-03``. Reads ``stream_chunks`` + ``stream_candidates``
    counts plus a head slice (first ``head_cap`` chunks by ordinal) and
    a tail slice (last ``tail_cap`` chunks by ordinal). Each row's
    ``text_preview`` is bounded by
    :data:`STREAM_TEXT_PREVIEW_MAX_LEN`; full chunk text is never
    returned. ``truncated=True`` iff the chunk count exceeds
    ``head_cap + tail_cap``.
    """
    if not isinstance(config, SessionStoreConfig):
        raise PersistenceError(
            "stream_db_summary requires a SessionStoreConfig "
            f"(got {type(config).__name__})"
        )
    if (
        not isinstance(head_cap, int)
        or isinstance(head_cap, bool)
        or head_cap < 0
    ):
        raise PersistenceError(
            "stream_db_summary head_cap must be a non-negative int "
            f"(got {head_cap!r})"
        )
    if (
        not isinstance(tail_cap, int)
        or isinstance(tail_cap, bool)
        or tail_cap < 0
    ):
        raise PersistenceError(
            "stream_db_summary tail_cap must be a non-negative int "
            f"(got {tail_cap!r})"
        )
    if head_cap > STREAM_DB_SUMMARY_HEAD_CAP:
        raise PersistenceError(
            "stream_db_summary head_cap exceeds locked default "
            f"{STREAM_DB_SUMMARY_HEAD_CAP} (got {head_cap!r})"
        )
    if tail_cap > STREAM_DB_SUMMARY_TAIL_CAP:
        raise PersistenceError(
            "stream_db_summary tail_cap exceeds locked default "
            f"{STREAM_DB_SUMMARY_TAIL_CAP} (got {tail_cap!r})"
        )

    db_path = config.db_path
    db_path_str = _bound_error_text(str(db_path))

    if not db_path.exists() or db_path.is_dir():
        return StreamDbSummaryReport(
            db_path_str=db_path_str,
            chunk_count=0,
            candidate_count=0,
            first_ordinal=0,
            last_ordinal=0,
            head=(),
            tail=(),
            truncated=False,
            error_text=_bound_error_text(
                f"session DB at {db_path!s} is missing or not a file"
            ),
        )

    uri = _ro_connect_uri(db_path)
    chunk_count = 0
    candidate_count = 0
    first_ordinal = 0
    last_ordinal = 0
    head: tuple[StreamDbSummaryRow, ...] = ()
    tail: tuple[StreamDbSummaryRow, ...] = ()
    truncated = False
    error_text = ""
    try:
        with sqlite3.connect(uri, uri=True) as conn:
            try:
                chunk_count = _table_row_count(
                    conn, STREAM_CHUNKS_TABLE_NAME
                )
                candidate_count = _table_row_count(
                    conn, STREAM_CANDIDATES_TABLE_NAME
                )
                if chunk_count > 0:
                    min_row = conn.execute(
                        f"SELECT MIN(ordinal), MAX(ordinal) "
                        f"FROM {STREAM_CHUNKS_TABLE_NAME}"
                    ).fetchone()
                    if min_row is not None and min_row[0] is not None:
                        first_ordinal = int(min_row[0])
                        last_ordinal = int(min_row[1])

                    head_rows = list(conn.execute(
                        f"SELECT ordinal, chunk_id, source, text, "
                        f"provenance_tag FROM {STREAM_CHUNKS_TABLE_NAME} "
                        f"ORDER BY ordinal ASC LIMIT ?",
                        (head_cap,),
                    ))
                    tail_rows_raw = list(conn.execute(
                        f"SELECT ordinal, chunk_id, source, text, "
                        f"provenance_tag FROM {STREAM_CHUNKS_TABLE_NAME} "
                        f"ORDER BY ordinal DESC LIMIT ?",
                        (tail_cap,),
                    ))
                    # Tail comes back DESC; flip to ASC for display.
                    tail_rows = list(reversed(tail_rows_raw))

                    truncated = chunk_count > (head_cap + tail_cap)

                    head_built: list[StreamDbSummaryRow] = []
                    for ordinal, chunk_id, source, text, prov in head_rows:
                        head_built.append(
                            StreamDbSummaryRow(
                                ordinal=int(ordinal),
                                chunk_id=str(chunk_id),
                                source=_bound_error_text(str(source)),
                                tick_at_event=0,
                                provenance_tag=_bound_error_text(str(prov)),
                                text_preview=_truncate_preview(str(text)),
                            )
                        )
                    head = tuple(head_built)

                    tail_built: list[StreamDbSummaryRow] = []
                    for ordinal, chunk_id, source, text, prov in tail_rows:
                        tail_built.append(
                            StreamDbSummaryRow(
                                ordinal=int(ordinal),
                                chunk_id=str(chunk_id),
                                source=_bound_error_text(str(source)),
                                tick_at_event=0,
                                provenance_tag=_bound_error_text(str(prov)),
                                text_preview=_truncate_preview(str(text)),
                            )
                        )
                    tail = tuple(tail_built)
            except sqlite3.Error as exc:
                error_text = _bound_error_text(
                    f"stream read failed: {exc}"
                )
                head = ()
                tail = ()
    except sqlite3.Error as exc:
        error_text = _bound_error_text(f"open failed: {exc}")

    return StreamDbSummaryReport(
        db_path_str=db_path_str,
        chunk_count=chunk_count,
        candidate_count=candidate_count,
        first_ordinal=first_ordinal,
        last_ordinal=last_ordinal,
        head=head,
        tail=tail,
        truncated=truncated,
        error_text=error_text,
    )


def _diff_map(
    field_prefix: str,
    live_map: dict[str, str],
    saved_map: dict[str, str],
) -> list[DbDiffField]:
    """Diff two ``{content_id: str}`` maps under ``field_prefix``.

    A key present on both sides produces a :class:`DbDiffField` only
    when the values differ. A key present on one side produces a
    :class:`DbDiffField` with :data:`DIFF_MISSING_MARKER` on the absent
    side. No silent default is invented.
    """
    diffs: list[DbDiffField] = []
    keys = sorted(set(live_map.keys()) | set(saved_map.keys()))
    for key in keys:
        live_value = live_map.get(key)
        saved_value = saved_map.get(key)
        if live_value == saved_value:
            continue
        diffs.append(
            DbDiffField(
                field=f"{field_prefix}{key}",
                live=live_value if live_value is not None else DIFF_MISSING_MARKER,
                saved=saved_value if saved_value is not None else DIFF_MISSING_MARKER,
            )
        )
    return diffs


def db_diff(
    session: object,
    config: SessionStoreConfig,
    *,
    row_cap: int = DB_DIFF_ROW_CAP,
) -> DbDiffReport:
    """Diff a live :class:`OperatorSession` against the saved DB.

    Drives ``I-OBSERVE-04`` and the behavioural half of
    ``I-OBSERVE-05``. Snapshots the live session via the public
    :func:`brain.ui.persistence.snapshot_session` helper, reads the
    saved :class:`PersistentSessionSnapshot` via
    :func:`brain.ui.persistence._deserialize_from_db` in ``mode=ro``,
    and diffs over the closed enumeration declared by
    :func:`_validate_diff_field_name`. Missing-on-one-side fields use
    the literal :data:`DIFF_MISSING_MARKER`; no kernel builder is
    invoked and no live session field is mutated.
    """
    if not isinstance(config, SessionStoreConfig):
        raise PersistenceError(
            "db_diff requires a SessionStoreConfig "
            f"(got {type(config).__name__})"
        )
    if (
        not isinstance(row_cap, int)
        or isinstance(row_cap, bool)
        or row_cap <= 0
    ):
        raise PersistenceError(
            "db_diff row_cap must be a positive int "
            f"(got {row_cap!r})"
        )

    # Local import keeps the import graph minimal at module load
    # (the static audit allows brain.ui.session).
    from brain.ui.session import OperatorSession  # noqa: PLC0415

    if not isinstance(session, OperatorSession):
        raise PersistenceError(
            "db_diff requires an OperatorSession "
            f"(got {type(session).__name__})"
        )

    db_path = config.db_path
    db_path_str = _bound_error_text(str(db_path))

    if not db_path.exists() or db_path.is_dir():
        return DbDiffReport(
            db_path_str=db_path_str,
            matches=False,
            diff_count=0,
            differences=(),
            truncated=False,
            error_text=_bound_error_text(
                f"session DB at {db_path!s} is missing or not a file"
            ),
        )

    # Project the live session through the promoted public helper. The
    # ``now_iso`` / ``created_at_iso`` arguments are required by the
    # signature but their values are never compared (the diff is over
    # kernel content, not timestamps).
    try:
        live_snapshot = snapshot_session(
            session,
            config,
            now_iso="1970-01-01T00:00:00+00:00",
            created_at_iso="1970-01-01T00:00:00+00:00",
        )
    except PersistenceError as exc:
        return DbDiffReport(
            db_path_str=db_path_str,
            matches=False,
            diff_count=0,
            differences=(),
            truncated=False,
            error_text=_bound_error_text(
                f"live snapshot failed: {exc}"
            ),
        )

    uri = _ro_connect_uri(db_path)
    try:
        with sqlite3.connect(uri, uri=True) as conn:
            try:
                saved_snapshot = _deserialize_from_db(conn)
            except PersistenceError as exc:
                return DbDiffReport(
                    db_path_str=db_path_str,
                    matches=False,
                    diff_count=0,
                    differences=(),
                    truncated=False,
                    error_text=_bound_error_text(
                        f"saved snapshot failed: {exc}"
                    ),
                )
            except sqlite3.Error as exc:
                return DbDiffReport(
                    db_path_str=db_path_str,
                    matches=False,
                    diff_count=0,
                    differences=(),
                    truncated=False,
                    error_text=_bound_error_text(
                        f"saved read failed: {exc}"
                    ),
                )
    except sqlite3.Error as exc:
        return DbDiffReport(
            db_path_str=db_path_str,
            matches=False,
            diff_count=0,
            differences=(),
            truncated=False,
            error_text=_bound_error_text(f"open failed: {exc}"),
        )

    # Build the live-side maps from the projected snapshot (rather than
    # re-reading session.state) so the live + saved sides go through
    # the same projection contract.
    live_profile = _saved_profile_map(live_snapshot)
    saved_profile = _saved_profile_map(saved_snapshot)
    live_ptcns = _saved_ptcns_map(live_snapshot)
    saved_ptcns = _saved_ptcns_map(saved_snapshot)
    live_registry = _saved_registry_map(live_snapshot)
    saved_registry = _saved_registry_map(saved_snapshot)

    diffs: list[DbDiffField] = []
    diffs.extend(_diff_map("profile.", live_profile, saved_profile))

    live_msi_str = ",".join(sorted(live_snapshot.brain_state.msi_contents))
    saved_msi_str = ",".join(sorted(saved_snapshot.brain_state.msi_contents))
    if live_msi_str != saved_msi_str:
        diffs.append(
            DbDiffField(
                field="msi.contents",
                live=live_msi_str if live_msi_str else DIFF_MISSING_MARKER,
                saved=saved_msi_str if saved_msi_str else DIFF_MISSING_MARKER,
            )
        )

    live_threshold = _render_fraction(
        live_snapshot.brain_state.msi_threshold_num,
        live_snapshot.brain_state.msi_threshold_den,
    )
    saved_threshold = _render_fraction(
        saved_snapshot.brain_state.msi_threshold_num,
        saved_snapshot.brain_state.msi_threshold_den,
    )
    if live_threshold != saved_threshold:
        diffs.append(
            DbDiffField(
                field="msi.threshold",
                live=live_threshold,
                saved=saved_threshold,
            )
        )

    diffs.extend(_diff_map("ptcns_eval.", live_ptcns, saved_ptcns))
    diffs.extend(_diff_map("registry.", live_registry, saved_registry))

    if live_snapshot.tick_counter != saved_snapshot.tick_counter:
        diffs.append(
            DbDiffField(
                field="tick_counter",
                live=str(live_snapshot.tick_counter),
                saved=str(saved_snapshot.tick_counter),
            )
        )
    if live_snapshot.stream_chunk_serial != saved_snapshot.stream_chunk_serial:
        diffs.append(
            DbDiffField(
                field="stream_chunk_serial",
                live=str(live_snapshot.stream_chunk_serial),
                saved=str(saved_snapshot.stream_chunk_serial),
            )
        )
    live_chunk_count = len(live_snapshot.stream_chunks)
    saved_chunk_count = len(saved_snapshot.stream_chunks)
    if live_chunk_count != saved_chunk_count:
        diffs.append(
            DbDiffField(
                field="stream_history.count",
                live=str(live_chunk_count),
                saved=str(saved_chunk_count),
            )
        )
    live_cand_count = len(live_snapshot.stream_candidates)
    saved_cand_count = len(saved_snapshot.stream_candidates)
    if live_cand_count != saved_cand_count:
        diffs.append(
            DbDiffField(
                field="stream_candidates.count",
                live=str(live_cand_count),
                saved=str(saved_cand_count),
            )
        )

    diff_count = len(diffs)
    truncated = diff_count > row_cap
    kept = tuple(diffs[:row_cap])
    matches = diff_count == 0

    return DbDiffReport(
        db_path_str=db_path_str,
        matches=matches,
        diff_count=diff_count,
        differences=kept,
        truncated=truncated,
        error_text="",
    )


__all__ = (
    "PROFILE_SUMMARY_ROW_CAP",
    "STREAM_DB_SUMMARY_HEAD_CAP",
    "STREAM_DB_SUMMARY_TAIL_CAP",
    "DB_DIFF_ROW_CAP",
    "STREAM_TEXT_PREVIEW_MAX_LEN",
    "PROFILE_VALUE_STRING_MAX_LEN",
    "OPS_REPORT_TEXT_MAX_LEN",
    "DIFF_MISSING_MARKER",
    "DbSummaryReport",
    "ProfileSummaryRow",
    "ProfileSummaryReport",
    "StreamDbSummaryRow",
    "StreamDbSummaryReport",
    "DbDiffField",
    "DbDiffReport",
    "db_summary",
    "profile_summary",
    "stream_db_summary",
    "db_diff",
)
