"""Phase 3.10a /db-backup --force fixture.

Drives:

* ``I-OPSHARDEN-06`` (REQUIRED) — ``/db-backup`` refuses to
  overwrite without ``--force``. If ``dest_path.exists()`` and
  ``force=False``, ``db_backup`` returns a :class:`DbBackupReport`
  with ``succeeded=False``, ``overwritten=False``, and a bounded
  ``error_text``. No destination write occurs.

  With ``force=True``, the existing destination is overwritten and
  ``overwritten=True`` is reported.
"""
from __future__ import annotations

import pathlib
import tempfile

from brain.invariants import register
from brain.ui.__main__ import build_default_session
from brain.ui.persistence import SessionStoreConfig, save_session
from brain.ui.persistence_ops import db_backup


@register("I-OPSHARDEN-06", status="REQUIRED")
def check_i_opsharden_06_db_backup_force() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-opsharden-06-") as td:
        src_path = pathlib.Path(td) / "src.sqlite3"
        dst_path = pathlib.Path(td) / "dst.sqlite3"
        session = build_default_session()
        src_config = SessionStoreConfig(db_path=src_path)
        save_session(session, src_config)

        # Pre-create the destination with sentinel content. Without
        # --force, the backup must refuse and the sentinel content
        # must remain.
        dst_path.write_bytes(b"sentinel-bytes")
        sentinel = dst_path.read_bytes()

        report = db_backup(src_config, dst_path, force=False)
        if report.succeeded:
            raise AssertionError(
                "I-OPSHARDEN-06 violated: db_backup overwrote without force"
            )
        if report.overwritten:
            raise AssertionError(
                "I-OPSHARDEN-06 violated: db_backup reports overwritten=True "
                "after a force=False rejection"
            )
        if not report.error_text:
            raise AssertionError(
                "I-OPSHARDEN-06 violated: refusal must include bounded "
                "error_text"
            )
        if dst_path.read_bytes() != sentinel:
            raise AssertionError(
                "I-OPSHARDEN-06 violated: destination bytes changed despite "
                "force=False refusal"
            )

        # With --force, the destination is overwritten and the report
        # reflects overwritten=True.
        report_force = db_backup(src_config, dst_path, force=True)
        if not report_force.succeeded:
            raise AssertionError(
                "I-OPSHARDEN-06 violated: force=True backup failed: "
                f"{report_force.error_text!r}"
            )
        if not report_force.overwritten:
            raise AssertionError(
                "I-OPSHARDEN-06 violated: force=True report overwritten=False"
            )
        if dst_path.read_bytes() == sentinel:
            raise AssertionError(
                "I-OPSHARDEN-06 violated: force=True did not overwrite "
                "destination bytes"
            )
