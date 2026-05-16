"""Phase 3.10a /session-status fixture.

Drives:

* ``I-OPSHARDEN-01`` (REQUIRED) — ``/session-status`` is read-only and
  bounded. ``session_status(session)`` reads ``OperatorSession`` fields
  only; no disk IO, no ``tick()``, no curses, no ``sqlite3.Connection``.
  The returned :class:`SessionStatusReport`'s string / integer fields
  are bounded by ``OPS_REPORT_TEXT_MAX_LEN = 256`` and non-negativity.
  ``_dispatch_session_status`` surfaces the report through
  ``status_message``.
"""
from __future__ import annotations

import pathlib
import sqlite3
import tempfile
from fractions import Fraction

from brain.invariants import register
from brain.tlica.profile import COGITO_ID
from brain.ui.__main__ import build_default_session
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.persistence import SessionStoreConfig
from brain.ui.persistence_ops import (
    OPS_REPORT_TEXT_MAX_LEN,
    SessionStatusReport,
    session_status,
)


@register("I-OPSHARDEN-01", status="REQUIRED")
def check_i_opsharden_01_session_status() -> None:
    session = build_default_session()
    # The default session has COGITO at value 1.
    if session.state.profile.values[COGITO_ID] != Fraction(1):
        raise AssertionError(
            "I-OPSHARDEN-01 violated: default session COGITO is not 1 "
            f"(got {session.state.profile.values[COGITO_ID]!r})"
        )

    report = session_status(session)
    if not isinstance(report, SessionStatusReport):
        raise AssertionError(
            "I-OPSHARDEN-01 violated: session_status did not return a "
            f"SessionStatusReport (got {type(report).__name__})"
        )
    # Bounded fields.
    for field_name in (
        "active_view",
        "session_db_path_str",
    ):
        value = getattr(report, field_name)
        if len(value) > OPS_REPORT_TEXT_MAX_LEN:
            raise AssertionError(
                f"I-OPSHARDEN-01 violated: SessionStatusReport.{field_name} "
                f"length {len(value)} exceeds "
                f"OPS_REPORT_TEXT_MAX_LEN={OPS_REPORT_TEXT_MAX_LEN}"
            )
    for field_name in (
        "tick_counter",
        "queue_size",
        "stream_chunk_count",
        "stream_candidate_count",
        "stream_chunk_serial",
    ):
        value = getattr(report, field_name)
        if not isinstance(value, int) or value < 0:
            raise AssertionError(
                f"I-OPSHARDEN-01 violated: SessionStatusReport.{field_name} "
                f"is not a non-negative int (got {value!r})"
            )
    if report.session_db_configured:
        raise AssertionError(
            "I-OPSHARDEN-01 violated: default session reports "
            "session_db_configured=True (no config attached)"
        )
    if report.session_db_path_str != "":
        raise AssertionError(
            "I-OPSHARDEN-01 violated: default session db_path_str must "
            f"be empty (got {report.session_db_path_str!r})"
        )

    # No disk IO: session_status with an absent DB path still works.
    with tempfile.TemporaryDirectory(prefix="brain-opsharden-01-") as td:
        db_path = pathlib.Path(td) / "no-such-file.sqlite3"
        configured = build_default_session()
        configured.session_store_config = SessionStoreConfig(db_path=db_path)
        report2 = session_status(configured)
        if not report2.session_db_configured:
            raise AssertionError(
                "I-OPSHARDEN-01 violated: configured session must report "
                "session_db_configured=True"
            )
        if db_path.exists():
            raise AssertionError(
                "I-OPSHARDEN-01 violated: session_status created the DB file"
            )

    # No sqlite3.Connection appears on session fields after the call.
    for attr in session.__slots__:
        value = getattr(session, attr)
        if isinstance(value, sqlite3.Connection):
            raise AssertionError(
                f"I-OPSHARDEN-01 violated: session.{attr} is a "
                "sqlite3.Connection after session_status"
            )

    # Dispatcher surfaces the report through status_message.
    cmd = make_command(OperatorCommand.SESSION_STATUS)
    session.dispatch(cmd)
    if not session.status_message.startswith("session-status: "):
        raise AssertionError(
            "I-OPSHARDEN-01 violated: SESSION_STATUS dispatch did not set "
            f"status_message (got {session.status_message!r})"
        )
    if session.error_message:
        raise AssertionError(
            "I-OPSHARDEN-01 violated: SESSION_STATUS dispatch set "
            f"error_message ({session.error_message!r})"
        )
