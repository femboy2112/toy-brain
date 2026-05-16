"""Phase 3.10a /db-backup core fixture.

Drives:

* ``I-OPSHARDEN-05`` (REQUIRED) — ``/db-backup`` uses
  ``sqlite3.Connection.backup()`` (page-faithful). ``load_session``
  against the backup file yields the same
  :class:`PersistentSessionSnapshot` as the source.
* ``I-OPSHARDEN-08`` (REQUIRED) — ``/db-backup`` never modifies the
  source DB. The source file is byte-identical to its pre-call
  state. ``dest_path == source_path`` raises
  :class:`PersistenceError`.
"""
from __future__ import annotations

import pathlib
import tempfile

from brain.invariants import register
from brain.ui.__main__ import build_default_session
from brain.ui.persistence import (
    PersistenceError,
    SessionStoreConfig,
    load_session,
    save_session,
)
from brain.ui.persistence_ops import DbBackupReport, db_backup


def _read_db_bytes(path: pathlib.Path) -> bytes:
    with path.open("rb") as fh:
        return fh.read()


@register("I-OPSHARDEN-05", status="REQUIRED")
def check_i_opsharden_05_db_backup_page_faithful() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-opsharden-05-") as td:
        src_path = pathlib.Path(td) / "src.sqlite3"
        dst_path = pathlib.Path(td) / "dst.sqlite3"
        session = build_default_session()
        src_config = SessionStoreConfig(db_path=src_path)
        save_session(session, src_config)

        report = db_backup(src_config, dst_path)
        if not isinstance(report, DbBackupReport):
            raise AssertionError(
                "I-OPSHARDEN-05 violated: db_backup did not return a "
                f"DbBackupReport (got {type(report).__name__})"
            )
        if not report.succeeded:
            raise AssertionError(
                "I-OPSHARDEN-05 violated: db_backup failed: "
                f"{report.error_text!r}"
            )
        if not dst_path.exists():
            raise AssertionError(
                "I-OPSHARDEN-05 violated: dst_path was not created"
            )
        if report.pages_copied == 0 or report.total_pages == 0:
            raise AssertionError(
                "I-OPSHARDEN-05 violated: report has zero pages "
                f"(pages_copied={report.pages_copied}, "
                f"total_pages={report.total_pages})"
            )

        # Page-faithful: load_session against the backup yields the
        # same content (compare PersistentSessionSnapshot.brain_state).
        dst_config = SessionStoreConfig(db_path=dst_path)
        src_loaded, _ = load_session(src_config)
        dst_loaded, _ = load_session(dst_config)
        # The reconstructed BrainState should match via profile values
        # and msi threshold (kernel-numeric equality on Fractions).
        if (
            src_loaded.state.profile.values
            != dst_loaded.state.profile.values
        ):
            raise AssertionError(
                "I-OPSHARDEN-05 violated: backup profile values do not "
                "match source after load"
            )
        if (
            src_loaded.state.msi.threshold
            != dst_loaded.state.msi.threshold
        ):
            raise AssertionError(
                "I-OPSHARDEN-05 violated: backup msi threshold does not "
                "match source after load"
            )


@register("I-OPSHARDEN-08", status="REQUIRED")
def check_i_opsharden_08_db_backup_source_integrity() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-opsharden-08-") as td:
        src_path = pathlib.Path(td) / "src.sqlite3"
        dst_path = pathlib.Path(td) / "dst.sqlite3"
        session = build_default_session()
        src_config = SessionStoreConfig(db_path=src_path)
        save_session(session, src_config)

        prior_bytes = _read_db_bytes(src_path)

        report = db_backup(src_config, dst_path)
        if not report.succeeded:
            raise AssertionError(
                "I-OPSHARDEN-08 violated: db_backup failed: "
                f"{report.error_text!r}"
            )
        post_bytes = _read_db_bytes(src_path)
        if post_bytes != prior_bytes:
            raise AssertionError(
                "I-OPSHARDEN-08 violated: source DB bytes changed across "
                f"db_backup ({len(prior_bytes)} -> {len(post_bytes)})"
            )

        # dest_path == source_path is rejected as PersistenceError.
        raised = False
        try:
            db_backup(src_config, src_path)
        except PersistenceError:
            raised = True
        if not raised:
            raise AssertionError(
                "I-OPSHARDEN-08 violated: db_backup did not reject "
                "dest_path == source_path"
            )
