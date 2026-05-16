"""Phase 3.10a /db-status fixture.

Drives:

* ``I-OPSHARDEN-02`` (REQUIRED) — ``/db-status`` is read-only
  ``mode=ro`` and bounded. ``db_status(config)`` opens the configured
  DB through ``sqlite3.connect("file:<path>?mode=ro", uri=True)``
  inside a ``with conn:`` block, reads ``meta`` rows, closes the
  connection, and returns a :class:`DbStatusReport`. On a missing DB,
  the report has ``db_exists=False`` and empty schema / catalog /
  timestamp fields; no sqlite3 error propagates.
"""
from __future__ import annotations

import pathlib
import tempfile

from brain.invariants import register
from brain.ui.__main__ import build_default_session
from brain.ui.persistence import (
    CATALOG_VERSION_STAMP,
    SCHEMA_VERSION_V1,
    SessionStoreConfig,
    save_session,
)
from brain.ui.persistence_ops import DbStatusReport, db_status


@register("I-OPSHARDEN-02", status="REQUIRED")
def check_i_opsharden_02_db_status() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-opsharden-02-") as td:
        # Missing DB case.
        missing_path = pathlib.Path(td) / "absent.sqlite3"
        config_missing = SessionStoreConfig(db_path=missing_path)
        missing_report = db_status(config_missing)
        if not isinstance(missing_report, DbStatusReport):
            raise AssertionError(
                "I-OPSHARDEN-02 violated: db_status did not return a "
                f"DbStatusReport (got {type(missing_report).__name__})"
            )
        if missing_report.db_exists:
            raise AssertionError(
                "I-OPSHARDEN-02 violated: missing DB reports db_exists=True"
            )
        if missing_report.schema_version != 0:
            raise AssertionError(
                "I-OPSHARDEN-02 violated: missing DB reports schema_version="
                f"{missing_report.schema_version!r}, expected 0"
            )
        if missing_report.catalog_version != "":
            raise AssertionError(
                "I-OPSHARDEN-02 violated: missing DB reports "
                f"catalog_version={missing_report.catalog_version!r}, "
                "expected empty"
            )
        if missing_report.created_at != "":
            raise AssertionError(
                "I-OPSHARDEN-02 violated: missing DB reports created_at="
                f"{missing_report.created_at!r}"
            )
        if missing_report.updated_at != "":
            raise AssertionError(
                "I-OPSHARDEN-02 violated: missing DB reports updated_at="
                f"{missing_report.updated_at!r}"
            )

        # Freshly saved DB case.
        existing_path = pathlib.Path(td) / "session.sqlite3"
        session = build_default_session()
        config = SessionStoreConfig(db_path=existing_path)
        save_session(session, config)
        report = db_status(config)
        if not report.db_exists:
            raise AssertionError(
                "I-OPSHARDEN-02 violated: freshly saved DB reports "
                "db_exists=False"
            )
        if report.schema_version != SCHEMA_VERSION_V1:
            raise AssertionError(
                "I-OPSHARDEN-02 violated: schema_version "
                f"{report.schema_version!r} != "
                f"SCHEMA_VERSION_V1 {SCHEMA_VERSION_V1!r}"
            )
        if report.catalog_version != CATALOG_VERSION_STAMP:
            raise AssertionError(
                "I-OPSHARDEN-02 violated: catalog_version "
                f"{report.catalog_version!r} != "
                f"CATALOG_VERSION_STAMP {CATALOG_VERSION_STAMP!r}"
            )
        if not report.created_at:
            raise AssertionError(
                "I-OPSHARDEN-02 violated: freshly saved DB has empty "
                "created_at"
            )
        if not report.updated_at:
            raise AssertionError(
                "I-OPSHARDEN-02 violated: freshly saved DB has empty "
                "updated_at"
            )
        if report.db_byte_size <= 0:
            raise AssertionError(
                "I-OPSHARDEN-02 violated: freshly saved DB reports "
                f"db_byte_size={report.db_byte_size!r}"
            )
        if report.error_text:
            raise AssertionError(
                "I-OPSHARDEN-02 violated: freshly saved DB has non-empty "
                f"error_text {report.error_text!r}"
            )
