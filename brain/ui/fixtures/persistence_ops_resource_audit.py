"""Phase 3.10a session resource-audit fixture.

Drives:

* ``I-OPSHARDEN-13`` (STRUCTURAL) — persistence_ops session resource
  audit. No :class:`OperatorSession` field is added in Phase 3.10a.
  After ``/session-status``, ``/db-status``, ``/db-verify``,
  ``/db-backup``, the session field shape is identical to the
  pre-call shape (no ``sqlite3.Connection`` / ``Cursor`` /
  subprocess / socket / file object / callable / curses object
  appears anywhere).
"""
from __future__ import annotations

import pathlib
import sqlite3
import tempfile

from brain.invariants import register
from brain.ui.__main__ import build_default_session
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.persistence import SessionStoreConfig, save_session
from brain.ui.session import _ALLOWED_SESSION_ATTRS, OperatorSession


#: Phase 3.9 session attribute set (snapshot before Phase 3.10a). The
#: fixture asserts that Phase 3.10a did NOT widen this set. Phase 3.10c
#: (Autosave Policy) is explicitly authorized to add the two
#: ``autosave_config`` and ``last_autosave_status`` fields per the
#: accepted v0.19 catalog patch; the assertion below treats those as
#: a known Phase 3.10c addition rather than a Phase 3.10a drift.
_PHASE_3_9_SESSION_ATTRS: frozenset[str] = frozenset({
    "state",
    "latest_tick",
    "output_history",
    "worldlet_history",
    "repl_history",
    "event_queue",
    "active_view",
    "status_message",
    "error_message",
    "quit_flag",
    "tick_counter",
    "stream_history",
    "stream_candidates",
    "stream_chunk_serial",
    "session_store_config",
})


#: Phase 3.10c (Autosave Policy) additions to the OperatorSession
#: attribute surface. The fixture allows these names through the
#: I-OPSHARDEN-13 check because the v0.19 catalog patch authorizes
#: them; the I-AUTOSAVE-14 resource audit fixture asserts the
#: positive shape of these fields.
_PHASE_3_10C_SESSION_ATTRS: frozenset[str] = frozenset({
    "autosave_config",
    "last_autosave_status",
})


#: Phase 3.12c (Pattern Ledger) additions to the OperatorSession
#: attribute surface. The fixture allows this name through the
#: I-OPSHARDEN-13 check because the v0.21 catalog patch authorizes
#: it; the I-PLEDGER-16 resource audit fixture asserts the positive
#: shape (no callable / handle / client) of the Pattern Ledger field.
_PHASE_3_12C_SESSION_ATTRS: frozenset[str] = frozenset({
    "pattern_ledger",
})


#: Phase 3.13 (Growth Ledger) additions to the OperatorSession
#: attribute surface. The fixture allows this name through the
#: I-OPSHARDEN-13 check because the v0.23 catalog patch authorizes
#: it; the I-GROW-13 / I-GROW-14 rows assert the positive shape (no
#: callable / handle / client) of the Growth Ledger field.
_PHASE_3_13_SESSION_ATTRS: frozenset[str] = frozenset({
    "growth_ledger",
})


#: Phase 3.18 (Bounded Internal Processing Window) additions to the
#: OperatorSession attribute surface. Both fields are bounded
#: non-negative ints; the I-PWND-01 / I-PWND-02 rows assert the
#: positive shape (no callable / handle / client / path / connection)
#: of these fields. The v0.26 catalog patch authorizes them through
#: this tier.
_PHASE_3_18_SESSION_ATTRS: frozenset[str] = frozenset({
    "processing_window_size",
    "processing_window_call_budget",
})


#: Phase 3.19 (Internal Feedback Loop) additions to the
#: OperatorSession attribute surface. The single field is a bounded
#: ``FeedbackMode`` enum value; the I-IFBK-01 / I-IFBK-02 rows
#: assert the positive shape (no callable / handle / client / path /
#: connection) of this field. The v0.27 catalog patch authorizes it
#: through this tier.
_PHASE_3_19_SESSION_ATTRS: frozenset[str] = frozenset({
    "feedback_mode",
})


def _assert_session_resource_free(session: OperatorSession, *, tag: str) -> None:
    """Raise if any session field exposes a forbidden resource."""
    for attr in _ALLOWED_SESSION_ATTRS:
        value = getattr(session, attr)
        if isinstance(value, sqlite3.Connection):
            raise AssertionError(
                f"I-OPSHARDEN-13 violated [{tag}]: session.{attr} is "
                "a sqlite3.Connection"
            )
        if isinstance(value, sqlite3.Cursor):
            raise AssertionError(
                f"I-OPSHARDEN-13 violated [{tag}]: session.{attr} is "
                "a sqlite3.Cursor"
            )
        if callable(value):
            raise AssertionError(
                f"I-OPSHARDEN-13 violated [{tag}]: session.{attr} is "
                "callable"
            )
        if hasattr(value, "fileno"):
            raise AssertionError(
                f"I-OPSHARDEN-13 violated [{tag}]: session.{attr} "
                "exposes fileno()"
            )
        if hasattr(value, "send_signal") or hasattr(value, "communicate"):
            raise AssertionError(
                f"I-OPSHARDEN-13 violated [{tag}]: session.{attr} looks "
                "like a subprocess handle"
            )


@register("I-OPSHARDEN-13", status="STRUCTURAL")
def check_i_opsharden_13_session_resource_audit() -> None:
    # Phase 3.10a must not widen the OperatorSession attribute surface
    # beyond the Phase 3.9 baseline plus the Phase 3.10c (Autosave
    # Policy) additions authorized by the v0.19 catalog patch, the
    # Phase 3.12c (Pattern Ledger) addition authorized by the v0.21
    # catalog patch, and the Phase 3.13 (Growth Ledger) addition
    # authorized by the v0.23 catalog patch.
    allowed = (
        _PHASE_3_9_SESSION_ATTRS
        | _PHASE_3_10C_SESSION_ATTRS
        | _PHASE_3_12C_SESSION_ATTRS
        | _PHASE_3_13_SESSION_ATTRS
        | _PHASE_3_18_SESSION_ATTRS
        | _PHASE_3_19_SESSION_ATTRS
    )
    if frozenset(_ALLOWED_SESSION_ATTRS) != allowed:
        added = set(_ALLOWED_SESSION_ATTRS) - allowed
        dropped = allowed - set(_ALLOWED_SESSION_ATTRS)
        raise AssertionError(
            "I-OPSHARDEN-13 violated: OperatorSession attribute surface "
            f"drifted (added={sorted(added)!r}, dropped={sorted(dropped)!r})"
        )

    with tempfile.TemporaryDirectory(prefix="brain-opsharden-13-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        dst_path = pathlib.Path(td) / "backup.sqlite3"
        session = build_default_session()
        config = SessionStoreConfig(db_path=db_path)
        session.session_store_config = config
        save_session(session, config)

        # Re-check attribute surface after configuring the session.
        if set(session.__slots__) != allowed:
            raise AssertionError(
                "I-OPSHARDEN-13 violated: configured session __slots__ "
                "drifted"
            )

        _assert_session_resource_free(session, tag="pre-dispatch")

        # /session-status
        session.dispatch(make_command(OperatorCommand.SESSION_STATUS))
        _assert_session_resource_free(session, tag="after session-status")

        # /db-status
        session.dispatch(make_command(OperatorCommand.DB_STATUS))
        _assert_session_resource_free(session, tag="after db-status")

        # /db-verify
        session.dispatch(make_command(OperatorCommand.DB_VERIFY))
        _assert_session_resource_free(session, tag="after db-verify")

        # /db-backup
        session.dispatch(
            make_command(OperatorCommand.DB_BACKUP, dest_path=dst_path)
        )
        _assert_session_resource_free(session, tag="after db-backup")
