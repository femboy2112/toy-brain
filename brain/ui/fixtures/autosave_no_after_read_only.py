"""Phase 3.10c read-only-dispatch does-not-trigger-autosave fixture.

Drives:

* ``I-AUTOSAVE-10`` (REQUIRED) — read-only dispatch does NOT trigger
  autosave. For every command kind in the closed read-only list
  (``INSPECT_*``, ``CLEAR_STATUS``, ``HELP``, ``QUIT``, ``NOOP``,
  ``SESSION_STATUS``, ``DB_STATUS``, ``DB_VERIFY``, ``DB_SUMMARY``,
  ``PROFILE_SUMMARY``, ``STREAM_DB_SUMMARY``, ``DB_DIFF``,
  ``DB_BACKUP``, ``AUTOSAVE_STATUS``, ``SAVE_SESSION``,
  ``LOAD_SESSION``), dispatching the command on a session with
  autosave enabled leaves ``session.last_autosave_status`` unchanged.
"""
from __future__ import annotations

import pathlib
import tempfile

from brain.invariants import register
from brain.ui.__main__ import build_default_session
from brain.ui.autosave import (
    AutosaveMode,
    autosave_enable,
)
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.persistence import SessionStoreConfig, save_session


# Closed read-only verb list (per the corrigenda section 10 and the
# I-AUTOSAVE-10 row text). DB_BACKUP carries a payload (dest_path);
# the rest are no-payload.
_READ_ONLY_COMMANDS: tuple[OperatorCommand, ...] = (
    OperatorCommand.INSPECT_STATE,
    OperatorCommand.INSPECT_TICK,
    OperatorCommand.INSPECT_OUTPUT,
    OperatorCommand.INSPECT_WORLDLET,
    OperatorCommand.INSPECT_REPL,
    OperatorCommand.INSPECT_STREAM_SUMMARY,
    OperatorCommand.INSPECT_STREAM_CANDIDATES,
    OperatorCommand.CLEAR_STATUS,
    OperatorCommand.HELP,
    OperatorCommand.NOOP,
    OperatorCommand.SESSION_STATUS,
    OperatorCommand.DB_STATUS,
    OperatorCommand.DB_VERIFY,
    OperatorCommand.DB_SUMMARY,
    OperatorCommand.PROFILE_SUMMARY,
    OperatorCommand.STREAM_DB_SUMMARY,
    OperatorCommand.DB_DIFF,
    OperatorCommand.AUTOSAVE_STATUS,
    OperatorCommand.SAVE_SESSION,
    OperatorCommand.LOAD_SESSION,
)


@register("I-AUTOSAVE-10", status="REQUIRED")
def check_i_autosave_10_read_only_no_autosave() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-autosave-10-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        backup_dest = pathlib.Path(td) / "backup.sqlite3"
        session = build_default_session()
        session.session_store_config = SessionStoreConfig(db_path=db_path)

        # Seed the DB so /load-session has a snapshot to read.
        save_session(session, session.session_store_config)

        autosave_enable(
            session, AutosaveMode.AFTER_SUCCESSFUL_MUTATION
        )

        for kind in _READ_ONLY_COMMANDS:
            prior_last = session.last_autosave_status
            session.dispatch(make_command(kind))
            if session.last_autosave_status is not prior_last:
                raise AssertionError(
                    f"I-AUTOSAVE-10 violated: {kind.value} mutated "
                    f"last_autosave_status "
                    f"({prior_last!r} -> {session.last_autosave_status!r})"
                )

        # /db-backup also must not trigger autosave (it carries a
        # payload, so dispatched separately).
        prior_last = session.last_autosave_status
        session.dispatch(
            make_command(OperatorCommand.DB_BACKUP, dest_path=backup_dest)
        )
        if session.last_autosave_status is not prior_last:
            raise AssertionError(
                "I-AUTOSAVE-10 violated: DB_BACKUP mutated "
                f"last_autosave_status "
                f"({prior_last!r} -> {session.last_autosave_status!r})"
            )

        # /quit (also read-only re kernel + stream) must not trigger
        # autosave. Dispatched last so the quit_flag does not interfere
        # with the per-loop dispatches above.
        prior_last = session.last_autosave_status
        session.dispatch(make_command(OperatorCommand.QUIT))
        if session.last_autosave_status is not prior_last:
            raise AssertionError(
                "I-AUTOSAVE-10 violated: QUIT mutated "
                f"last_autosave_status "
                f"({prior_last!r} -> {session.last_autosave_status!r})"
            )
