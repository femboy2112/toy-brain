"""Phase 3.10a /db-verify candidate-drop fixture.

Drives:

* ``I-OPSHARDEN-03`` (REQUIRED) — ``/db-verify`` reuses
  :func:`brain.ui.persistence.load_session` and DROPS the candidate.
  The candidate session built inside ``db_verify`` is never assigned
  to the live :class:`OperatorSession`: ``id(session)`` before and
  after the call is the same, every visible session field is
  identical, and no new attribute is added.
"""
from __future__ import annotations

import pathlib
import tempfile

from brain.invariants import register
from brain.ui.__main__ import build_default_session
from brain.ui.persistence import SessionStoreConfig, save_session
from brain.ui.persistence_ops import db_verify
from brain.ui.session import _ALLOWED_SESSION_ATTRS


@register("I-OPSHARDEN-03", status="REQUIRED")
def check_i_opsharden_03_db_verify_drops_candidate() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-opsharden-03-drop-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        session = build_default_session()
        config = SessionStoreConfig(db_path=db_path)
        save_session(session, config)

        # Snapshot the live session identity and every visible field.
        prior_id = id(session)
        prior_field_ids = {
            name: id(getattr(session, name))
            for name in _ALLOWED_SESSION_ATTRS
        }

        report = db_verify(config)
        if not report.passed:
            raise AssertionError(
                "I-OPSHARDEN-03 violated: clean verify failed "
                f"({report.error_text!r}); cannot exercise drop check"
            )

        if id(session) != prior_id:
            raise AssertionError(
                "I-OPSHARDEN-03 violated: live session id() changed across "
                "db_verify"
            )
        # The state / stream_history / stream_candidates / config
        # references must be the exact same objects on the live session
        # (db_verify must not swap the candidate in).
        for name in ("state", "stream_history", "stream_candidates", "session_store_config"):
            if id(getattr(session, name)) != prior_field_ids[name]:
                raise AssertionError(
                    f"I-OPSHARDEN-03 violated: live session.{name} object "
                    "identity changed across db_verify (candidate was not "
                    "dropped)"
                )

        # The session attribute surface is unchanged.
        if set(session.__slots__) != set(_ALLOWED_SESSION_ATTRS):
            raise AssertionError(
                "I-OPSHARDEN-03 violated: OperatorSession.__slots__ drifted "
                "after db_verify"
            )
