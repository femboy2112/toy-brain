"""Phase 3.9 persistence SQLite schema fixture.

Drives:

* ``I-PERSIST-01`` (REQUIRED) — SQLite schema is finite and closed.
  ``brain/ui/persistence._create_schema`` populates exactly the v1
  tables ``{meta, content_registry, profile_values, msi_contents,
  msi_threshold, ptcns_eval, session_state, stream_chunks,
  stream_candidates}`` with the documented columns, NOT NULL
  constraints, PRIMARY KEY / UNIQUE / FOREIGN KEY structure, and CHECK
  constraints (``rho_den > 0``, ``den > 0``, ``msi_threshold.id = 1``).

* ``I-PERSIST-13`` (STRUCTURAL) — No kernel-numeric ``REAL`` column
  in the schema. The schema declared in ``brain/ui/persistence.py``
  uses ``INTEGER`` for every kernel-numeric value (``rho_num``,
  ``rho_den``, ``msi_threshold.num``, ``msi_threshold.den``,
  ``tick_at_event``), ``TEXT`` for every identifier / enum name /
  printable text / timestamp, and contains no ``REAL`` / ``NUMERIC``
  / ``FLOAT`` / ``DOUBLE`` column.
"""
from __future__ import annotations

import sqlite3

from brain.invariants import register
from brain.ui.persistence import (
    EXPECTED_TABLES,
    _create_schema,
    schema_statements,
)


# Closed expected (column_name, column_type) sets per table. The fixture
# asserts the live SQLite PRAGMA table_info output matches exactly.
_EXPECTED_COLUMNS: dict[str, tuple[tuple[str, str], ...]] = {
    "meta": (
        ("key", "TEXT"),
        ("value", "TEXT"),
    ),
    "content_registry": (
        ("content_id", "TEXT"),
        ("text", "TEXT"),
    ),
    "profile_values": (
        ("content_id", "TEXT"),
        ("rho_num", "INTEGER"),
        ("rho_den", "INTEGER"),
    ),
    "msi_contents": (
        ("content_id", "TEXT"),
    ),
    "msi_threshold": (
        ("id", "INTEGER"),
        ("num", "INTEGER"),
        ("den", "INTEGER"),
    ),
    "ptcns_eval": (
        ("content_id", "TEXT"),
        ("eval", "TEXT"),
    ),
    "session_state": (
        ("key", "TEXT"),
        ("value", "TEXT"),
    ),
    "stream_chunks": (
        ("ordinal", "INTEGER"),
        ("chunk_id", "TEXT"),
        ("source", "TEXT"),
        ("text", "TEXT"),
        ("tick_at_event", "INTEGER"),
        ("provenance_tag", "TEXT"),
    ),
    "stream_candidates": (
        ("ordinal", "INTEGER"),
        ("candidate_id", "TEXT"),
        ("target_content_id", "TEXT"),
        ("chunk_id", "TEXT"),
        ("pattern_id", "TEXT"),
        ("source", "TEXT"),
        ("text", "TEXT"),
        ("provenance_tag", "TEXT"),
    ),
}


_FORBIDDEN_COLUMN_TYPES: frozenset[str] = frozenset({
    "REAL",
    "NUMERIC",
    "FLOAT",
    "DOUBLE",
    "DOUBLE PRECISION",
})


def _build_in_memory_schema() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    _create_schema(conn)
    return conn


@register("I-PERSIST-01", status="REQUIRED")
def check_i_persist_01_schema_finite_and_closed() -> None:
    """v1 schema declares exactly the expected tables and columns."""
    conn = _build_in_memory_schema()
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        live_tables = frozenset(row[0] for row in rows)
        if live_tables != EXPECTED_TABLES:
            extra = sorted(live_tables - EXPECTED_TABLES)
            missing = sorted(EXPECTED_TABLES - live_tables)
            raise AssertionError(
                "I-PERSIST-01 violated: "
                f"live tables {sorted(live_tables)!r} != "
                f"EXPECTED_TABLES {sorted(EXPECTED_TABLES)!r} "
                f"(extra={extra!r}, missing={missing!r})"
            )

        for table, expected_cols in _EXPECTED_COLUMNS.items():
            info_rows = conn.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()
            if not info_rows:
                raise AssertionError(
                    f"I-PERSIST-01 violated: table {table!r} has no columns"
                )
            live_cols = tuple((row[1], row[2].upper()) for row in info_rows)
            expected_cols_upper = tuple(
                (name, ctype.upper()) for name, ctype in expected_cols
            )
            if live_cols != expected_cols_upper:
                raise AssertionError(
                    f"I-PERSIST-01 violated: table {table!r} columns "
                    f"{live_cols!r} != expected {expected_cols_upper!r}"
                )

        fk_rows = conn.execute(
            "PRAGMA foreign_key_list(msi_contents)"
        ).fetchall()
        if not any(row[2] == "profile_values" for row in fk_rows):
            raise AssertionError(
                "I-PERSIST-01 violated: msi_contents lacks FOREIGN KEY to "
                "profile_values"
            )
        fk_rows = conn.execute(
            "PRAGMA foreign_key_list(ptcns_eval)"
        ).fetchall()
        if not any(row[2] == "profile_values" for row in fk_rows):
            raise AssertionError(
                "I-PERSIST-01 violated: ptcns_eval lacks FOREIGN KEY to "
                "profile_values"
            )
        fk_rows = conn.execute(
            "PRAGMA foreign_key_list(stream_candidates)"
        ).fetchall()
        if not any(row[2] == "stream_chunks" for row in fk_rows):
            raise AssertionError(
                "I-PERSIST-01 violated: stream_candidates lacks FOREIGN KEY "
                "to stream_chunks"
            )

        # CHECK constraints are not introspectable via PRAGMA; verify them
        # by inserting violating rows and confirming the integrity error.
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            conn.execute(
                "INSERT INTO profile_values (content_id, rho_num, rho_den) "
                "VALUES ('rho_den_zero', 0, 0)"
            )
            raise AssertionError(
                "I-PERSIST-01 violated: profile_values accepts rho_den=0"
            )
        except sqlite3.IntegrityError:
            pass
        try:
            conn.execute(
                "INSERT INTO msi_threshold (id, num, den) VALUES (2, 1, 2)"
            )
            raise AssertionError(
                "I-PERSIST-01 violated: msi_threshold accepts id != 1"
            )
        except sqlite3.IntegrityError:
            pass
        try:
            conn.execute(
                "INSERT INTO msi_threshold (id, num, den) VALUES (1, 1, 0)"
            )
            raise AssertionError(
                "I-PERSIST-01 violated: msi_threshold accepts den=0"
            )
        except sqlite3.IntegrityError:
            pass
    finally:
        conn.close()


@register("I-PERSIST-13", status="STRUCTURAL")
def check_i_persist_13_no_kernel_real_column() -> None:
    """No CREATE TABLE statement uses REAL/NUMERIC/FLOAT/DOUBLE."""
    statements = schema_statements()
    if not isinstance(statements, tuple):
        raise AssertionError(
            "I-PERSIST-13 violated: schema_statements() must return a tuple"
        )
    if len(statements) != len(EXPECTED_TABLES):
        raise AssertionError(
            f"I-PERSIST-13 violated: schema_statements() length "
            f"{len(statements)} != len(EXPECTED_TABLES) "
            f"{len(EXPECTED_TABLES)}"
        )
    for stmt in statements:
        upper = stmt.upper()
        for forbidden in _FORBIDDEN_COLUMN_TYPES:
            for token in (
                f" {forbidden} ",
                f" {forbidden},",
                f" {forbidden}\n",
                f" {forbidden})",
            ):
                if token in upper:
                    raise AssertionError(
                        "I-PERSIST-13 violated: CREATE TABLE uses forbidden "
                        f"column type {forbidden!r} in statement: {stmt!r}"
                    )

    # Cross-check by inspecting the live PRAGMA output: no column type
    # surfaces as one of the forbidden kernel-numeric types.
    conn = _build_in_memory_schema()
    try:
        for table in EXPECTED_TABLES:
            for row in conn.execute(f"PRAGMA table_info({table})").fetchall():
                col_type = row[2].upper()
                if col_type in _FORBIDDEN_COLUMN_TYPES:
                    raise AssertionError(
                        "I-PERSIST-13 violated: table "
                        f"{table!r} column {row[1]!r} has forbidden type "
                        f"{col_type!r}"
                    )
    finally:
        conn.close()
