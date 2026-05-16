"""Phase 3.10c failed-dispatch does-not-trigger-autosave fixture.

Drives:

* ``I-AUTOSAVE-09`` (REQUIRED) — failed dispatch does NOT trigger
  autosave. A ``/step`` dispatch on an empty queue (which fails with a
  bounded local error) on a session with autosave enabled leaves
  ``session.last_autosave_status`` unchanged.
"""
from __future__ import annotations

import pathlib
import tempfile
from fractions import Fraction

from brain.invariants import register
from brain.toce_core import ContentState
from brain.ui.__main__ import build_default_session
from brain.ui.autosave import (
    AutosaveMode,
    autosave_enable,
)
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.persistence import SessionStoreConfig


class _PreserveClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        return "PRESERVE"


@register("I-AUTOSAVE-09", status="REQUIRED")
def check_i_autosave_09_failed_dispatch_no_autosave() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-autosave-09-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        session = build_default_session()
        session.session_store_config = SessionStoreConfig(db_path=db_path)
        autosave_enable(
            session, AutosaveMode.AFTER_SUCCESSFUL_MUTATION
        )

        # /step on an empty queue fails (local error).
        prior_last = session.last_autosave_status
        client = _PreserveClient()
        session.dispatch(
            make_command(OperatorCommand.STEP_TICK), client=client
        )
        if not session.error_message:
            raise AssertionError(
                "I-AUTOSAVE-09 violated: failed /step did not set "
                "error_message"
            )
        # The DB file must NOT have been written.
        if db_path.exists():
            raise AssertionError(
                "I-AUTOSAVE-09 violated: failed /step wrote the "
                "session DB"
            )
        # session.last_autosave_status is unchanged.
        if session.last_autosave_status is not prior_last:
            raise AssertionError(
                "I-AUTOSAVE-09 violated: failed /step mutated "
                f"last_autosave_status ({prior_last!r} -> "
                f"{session.last_autosave_status!r})"
            )

        # Counter-check: a subsequent /step that succeeds DOES trigger
        # autosave normally.
        session.dispatch(make_command(
            OperatorCommand.QUEUE_PERCEPT,
            content_id="beta",
            text="beta probe",
            content_state=ContentState(True, True, True, True),
            initial_rho=Fraction(3, 4),
        ))
        session.dispatch(
            make_command(OperatorCommand.STEP_TICK), client=client
        )
        if session.tick_counter != 1:
            raise AssertionError(
                "I-AUTOSAVE-09 violated: counter-check /step did not "
                f"advance tick (got {session.tick_counter!r})"
            )
        if session.last_autosave_status is None:
            raise AssertionError(
                "I-AUTOSAVE-09 violated: counter-check /step did not "
                "trigger autosave"
            )
        if session.last_autosave_status.last_attempt_outcome != "ok":
            raise AssertionError(
                "I-AUTOSAVE-09 violated: counter-check autosave outcome "
                f"is {session.last_autosave_status.last_attempt_outcome!r}"
            )

        # A subsequent failed /step (empty queue) again leaves
        # last_autosave_status unchanged.
        prior_last = session.last_autosave_status
        session.dispatch(
            make_command(OperatorCommand.STEP_TICK), client=client
        )
        if session.last_autosave_status is not prior_last:
            raise AssertionError(
                "I-AUTOSAVE-09 violated: second failed /step mutated "
                "last_autosave_status"
            )
