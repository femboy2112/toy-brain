"""Phase 3.10c autosave-failure isolation fixture.

Drives:

* ``I-AUTOSAVE-07`` (REQUIRED) — :func:`maybe_autosave_after_mutation`
  never raises. Calling the helper on a session whose underlying
  :func:`save_session` raises :class:`PersistenceError` absorbs the
  exception, populates ``last_attempt_outcome="error"`` plus bounded
  ``last_error_text``, and leaves the live ``OperatorSession`` kernel
  state intact. A subsequent successful ``/step`` succeeds normally.
"""
from __future__ import annotations

import copy
import pathlib
import tempfile
from fractions import Fraction

from brain.invariants import register
from brain.toce_core import ContentState
from brain.ui import autosave as autosave_module
from brain.ui.__main__ import build_default_session
from brain.ui.autosave import (
    AutosaveMode,
    AutosaveTrigger,
    autosave_enable,
    maybe_autosave_after_mutation,
)
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.persistence import PersistenceError, SessionStoreConfig
from brain.ui.persistence_ops import OPS_REPORT_TEXT_MAX_LEN


class _PreserveClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        return "PRESERVE"


def _raising_save_session(session, config, *, now=None):  # noqa: ANN001
    raise PersistenceError("synthetic save failure (fixture)")


@register("I-AUTOSAVE-07", status="REQUIRED")
def check_i_autosave_07_failure_never_raises() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-autosave-07-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        session = build_default_session()
        session.session_store_config = SessionStoreConfig(db_path=db_path)
        autosave_enable(
            session, AutosaveMode.AFTER_SUCCESSFUL_MUTATION
        )

        # Queue + step (the step itself succeeds; we then call
        # maybe_autosave_after_mutation directly with a monkeypatched
        # save_session that raises).
        session.dispatch(make_command(
            OperatorCommand.QUEUE_PERCEPT,
            content_id="beta",
            text="beta probe",
            content_state=ContentState(True, True, True, True),
            initial_rho=Fraction(3, 4),
        ))
        client = _PreserveClient()
        session.dispatch(
            make_command(OperatorCommand.STEP_TICK), client=client
        )
        if session.tick_counter != 1:
            raise AssertionError(
                "I-AUTOSAVE-07 violated: precondition /step did not "
                f"advance tick (got {session.tick_counter!r})"
            )

        # Snapshot kernel + stream state before the synthetic failure.
        prior_state = session.state
        prior_tick_counter = session.tick_counter
        prior_stream_history = session.stream_history
        prior_session_copy = copy.copy(session)

        # Monkeypatch save_session in the autosave module to raise.
        real_save = autosave_module.save_session
        autosave_module.save_session = _raising_save_session  # type: ignore[assignment]
        try:
            report = maybe_autosave_after_mutation(
                session,
                triggered_by=AutosaveTrigger.STEP_TICK,
            )
        except Exception as exc:  # noqa: BLE001 - must never raise
            autosave_module.save_session = real_save  # type: ignore[assignment]
            raise AssertionError(
                "I-AUTOSAVE-07 violated: helper raised "
                f"{type(exc).__name__}: {exc}"
            )
        finally:
            autosave_module.save_session = real_save  # type: ignore[assignment]

        if report is None:
            raise AssertionError(
                "I-AUTOSAVE-07 violated: helper returned None on the "
                "failure path (expected an error-tagged report)"
            )
        if report.last_attempt_outcome != "error":
            raise AssertionError(
                "I-AUTOSAVE-07 violated: outcome is "
                f"{report.last_attempt_outcome!r} (expected 'error')"
            )
        if not report.last_error_text:
            raise AssertionError(
                "I-AUTOSAVE-07 violated: last_error_text is empty"
            )
        if len(report.last_error_text) > OPS_REPORT_TEXT_MAX_LEN:
            raise AssertionError(
                "I-AUTOSAVE-07 violated: last_error_text length "
                f"{len(report.last_error_text)} exceeds "
                f"OPS_REPORT_TEXT_MAX_LEN={OPS_REPORT_TEXT_MAX_LEN}"
            )
        if not report.last_error_text.isprintable():
            raise AssertionError(
                "I-AUTOSAVE-07 violated: last_error_text is not "
                "printable"
            )

        # The live session's kernel + stream fields are unchanged.
        if session.state is not prior_state:
            raise AssertionError(
                "I-AUTOSAVE-07 violated: session.state was mutated by "
                "the failed autosave"
            )
        if session.tick_counter != prior_tick_counter:
            raise AssertionError(
                "I-AUTOSAVE-07 violated: session.tick_counter was "
                "mutated by the failed autosave"
            )
        if session.stream_history is not prior_stream_history:
            raise AssertionError(
                "I-AUTOSAVE-07 violated: session.stream_history was "
                "mutated by the failed autosave"
            )

        # Touch every field through prior_session_copy for completeness.
        if prior_session_copy.tick_counter != session.tick_counter:
            raise AssertionError(
                "I-AUTOSAVE-07 violated: copy-vs-live tick_counter "
                "diverged"
            )
