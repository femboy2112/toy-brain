"""Phase 3.10a /db-backup URI rejection fixture.

Drives:

* ``I-OPSHARDEN-07`` (REQUIRED) — ``/db-backup`` refuses URI-scheme
  destinations. ``dest_path`` strings that parse as a URI in the
  closed :data:`DB_BACKUP_FORBIDDEN_SCHEMES` set
  (``sqlite:``, ``file:``, ``http:``, ``https:``, ``ftp:``, ``ws:``,
  ``wss:``, ``data:``, ``gopher:``, ``ssh:``, ``git:``) are rejected
  at argument validation time. The rejection applies to both the
  Python :func:`db_backup` API and the
  :class:`brain.ui.command_line.LocalCommandLine` parser
  (``/db-backup`` composer verb). :class:`PersistenceError` is
  raised; no sqlite3 call is made; no destination file is touched.
"""
from __future__ import annotations

import pathlib
import tempfile

from brain.invariants import register
from brain.ui.__main__ import build_default_session
from brain.ui.command_line import LocalCommandError, LocalCommandLine
from brain.ui.persistence import (
    PersistenceError,
    SessionStoreConfig,
    save_session,
)
from brain.ui.persistence_ops import DB_BACKUP_FORBIDDEN_SCHEMES, db_backup


@register("I-OPSHARDEN-07", status="REQUIRED")
def check_i_opsharden_07_db_backup_rejects_uri() -> None:
    expected = {
        "sqlite", "file", "http", "https", "ftp",
        "ws", "wss", "data", "gopher", "ssh", "git",
    }
    if set(DB_BACKUP_FORBIDDEN_SCHEMES) != expected:
        raise AssertionError(
            "I-OPSHARDEN-07 violated: DB_BACKUP_FORBIDDEN_SCHEMES drift "
            f"(expected {sorted(expected)!r}, got "
            f"{sorted(DB_BACKUP_FORBIDDEN_SCHEMES)!r})"
        )

    parser = LocalCommandLine()
    with tempfile.TemporaryDirectory(prefix="brain-opsharden-07-") as td:
        src_path = pathlib.Path(td) / "src.sqlite3"
        session = build_default_session()
        config = SessionStoreConfig(db_path=src_path)
        save_session(session, config)

        for scheme in sorted(DB_BACKUP_FORBIDDEN_SCHEMES):
            dest_str = f"{scheme}://victim/backup.sqlite3"
            # Python API: PersistenceError at validation time.
            raised = False
            try:
                db_backup(config, pathlib.Path(dest_str))
            except PersistenceError:
                raised = True
            if not raised:
                raise AssertionError(
                    f"I-OPSHARDEN-07 violated: db_backup did not reject "
                    f"URI scheme {scheme!r} (dest_str={dest_str!r})"
                )
            # Parser: returns a LocalCommandError, no Command produced.
            result = parser.parse(f"/db-backup {dest_str}")
            if not isinstance(result, LocalCommandError):
                raise AssertionError(
                    f"I-OPSHARDEN-07 violated: parser accepted URI scheme "
                    f"{scheme!r} (returned {type(result).__name__})"
                )
            if "URI" not in result.message and "scheme" not in result.message:
                raise AssertionError(
                    f"I-OPSHARDEN-07 violated: parser error message for "
                    f"{scheme!r} lacks URI/scheme tag (got "
                    f"{result.message!r})"
                )
