"""Phase 3.10c autosave-enable + status + /step success fixture.

Drives:

* ``I-AUTOSAVE-04`` (REQUIRED) — ``/autosave-enable`` with valid mode +
  DB transitions ``session.autosave_config`` correctly.
* ``I-AUTOSAVE-06`` (REQUIRED) — ``/autosave-status`` returns a bounded
  :class:`AutosaveStatusReport`; never raises.
* ``I-AUTOSAVE-08`` (REQUIRED) — ``/step`` + autosave + success ->
  ``last_attempt_outcome == "ok"`` with ``last_attempt_trigger ==
  "step_tick"`` and a non-empty ``last_attempt_at`` timestamp.
"""
from __future__ import annotations

import pathlib
import tempfile
from fractions import Fraction

from brain.invariants import register
from brain.toce_core import ContentState
from brain.ui.__main__ import build_default_session
from brain.ui.autosave import (
    AUTOSAVE_STATUS_OUTCOMES,
    AutosaveMode,
    AutosaveStatusReport,
    AutosaveTrigger,
    SUPPORTED_AUTOSAVE_TRIGGERS,
    autosave_enable,
    autosave_status,
)
from brain.ui.commands import OperatorCommand, make_command
from brain.ui.persistence import SessionStoreConfig
from brain.ui.persistence_ops import OPS_REPORT_TEXT_MAX_LEN


class _PreserveClient:
    """Deterministic LLM stand-in: every call returns ``PRESERVE``."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        return "PRESERVE"


def _assert_status_report_bounded(
    report: AutosaveStatusReport, *, tag: str
) -> None:
    if not isinstance(report, AutosaveStatusReport):
        raise AssertionError(
            f"I-AUTOSAVE-06 violated [{tag}]: autosave_status returned "
            f"{type(report).__name__}"
        )
    for field_name in (
        "db_path_str",
        "last_attempt_outcome",
        "last_attempt_at",
        "last_attempt_trigger",
        "last_error_text",
    ):
        value = getattr(report, field_name)
        if len(value) > OPS_REPORT_TEXT_MAX_LEN:
            raise AssertionError(
                f"I-AUTOSAVE-06 violated [{tag}]: report.{field_name} "
                f"length {len(value)} exceeds "
                f"OPS_REPORT_TEXT_MAX_LEN={OPS_REPORT_TEXT_MAX_LEN}"
            )
    if report.last_attempt_tick < 0:
        raise AssertionError(
            f"I-AUTOSAVE-06 violated [{tag}]: last_attempt_tick is "
            f"negative ({report.last_attempt_tick!r})"
        )
    if report.last_attempt_outcome not in AUTOSAVE_STATUS_OUTCOMES:
        raise AssertionError(
            f"I-AUTOSAVE-06 violated [{tag}]: last_attempt_outcome "
            f"{report.last_attempt_outcome!r} is not in "
            f"{sorted(AUTOSAVE_STATUS_OUTCOMES)!r}"
        )
    allowed_triggers = (
        {t.value for t in SUPPORTED_AUTOSAVE_TRIGGERS} | {""}
    )
    if report.last_attempt_trigger not in allowed_triggers:
        raise AssertionError(
            f"I-AUTOSAVE-06 violated [{tag}]: last_attempt_trigger "
            f"{report.last_attempt_trigger!r} is not in "
            f"{sorted(allowed_triggers)!r}"
        )


@register("I-AUTOSAVE-04", status="REQUIRED")
def check_i_autosave_04_enable_transitions() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-autosave-04-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        session = build_default_session()
        session.session_store_config = SessionStoreConfig(db_path=db_path)

        before = autosave_status(session)
        if before.mode is not AutosaveMode.OFF:
            raise AssertionError(
                "I-AUTOSAVE-04 violated: configured session reports "
                f"non-OFF mode before enable (got {before.mode!r})"
            )

        report = autosave_enable(
            session, AutosaveMode.AFTER_SUCCESSFUL_MUTATION
        )
        if report.mode is not AutosaveMode.AFTER_SUCCESSFUL_MUTATION:
            raise AssertionError(
                "I-AUTOSAVE-04 violated: autosave_enable did not set "
                f"mode (got {report.mode!r})"
            )
        if (
            session.autosave_config is None
            or session.autosave_config.mode
            is not AutosaveMode.AFTER_SUCCESSFUL_MUTATION
        ):
            raise AssertionError(
                "I-AUTOSAVE-04 violated: session.autosave_config not "
                f"updated (got {session.autosave_config!r})"
            )
        expected_path_str = str(db_path)
        if (
            session.autosave_config.db_path_str != expected_path_str
            and not session.autosave_config.db_path_str.startswith(
                expected_path_str[: OPS_REPORT_TEXT_MAX_LEN - 1]
            )
        ):
            raise AssertionError(
                "I-AUTOSAVE-04 violated: session.autosave_config "
                f"db_path_str is {session.autosave_config.db_path_str!r} "
                f"(expected {expected_path_str!r})"
            )

        # /autosave-status verb reflects the new mode.
        session.dispatch(make_command(OperatorCommand.AUTOSAVE_STATUS))
        if "after-successful-mutation" not in session.status_message:
            raise AssertionError(
                "I-AUTOSAVE-04 violated: /autosave-status verb did not "
                f"reflect the new mode ({session.status_message!r})"
            )


@register("I-AUTOSAVE-06", status="REQUIRED")
def check_i_autosave_06_status_report_bounded() -> None:
    # autosave_status on a default (DB-less) session never raises and
    # returns a bounded report with OFF mode.
    session = build_default_session()
    report = autosave_status(session)
    _assert_status_report_bounded(report, tag="default-session")
    if report.mode is not AutosaveMode.OFF:
        raise AssertionError(
            "I-AUTOSAVE-06 violated: default-session report mode is "
            f"{report.mode!r}"
        )

    # Status on an enabled session is also bounded.
    with tempfile.TemporaryDirectory(prefix="brain-autosave-06-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        configured = build_default_session()
        configured.session_store_config = SessionStoreConfig(db_path=db_path)
        autosave_enable(
            configured, AutosaveMode.AFTER_SUCCESSFUL_MUTATION
        )
        report_enabled = autosave_status(configured)
        _assert_status_report_bounded(
            report_enabled, tag="enabled-session"
        )

    # Defensive: a session with corrupted autosave_config (not an
    # AutosaveConfig) still produces a typed report rather than raising.
    rogue = build_default_session()
    rogue.autosave_config = "not-a-config"  # type: ignore[assignment]
    try:
        report_rogue = autosave_status(rogue)
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(
            "I-AUTOSAVE-06 violated: autosave_status raised on a "
            f"rogue session ({type(exc).__name__}: {exc})"
        )
    _assert_status_report_bounded(report_rogue, tag="rogue-session")
    if report_rogue.mode is not AutosaveMode.OFF:
        raise AssertionError(
            "I-AUTOSAVE-06 violated: rogue session report mode is "
            f"{report_rogue.mode!r}"
        )


@register("I-AUTOSAVE-08", status="REQUIRED")
def check_i_autosave_08_step_success_triggers_autosave() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-autosave-08-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        session = build_default_session()
        session.session_store_config = SessionStoreConfig(db_path=db_path)
        autosave_enable(
            session, AutosaveMode.AFTER_SUCCESSFUL_MUTATION
        )

        # Queue + step.
        session.dispatch(make_command(
            OperatorCommand.QUEUE_PERCEPT,
            content_id="beta",
            text="beta probe",
            content_state=ContentState(True, True, True, True),
            initial_rho=Fraction(3, 4),
        ))
        if len(session.event_queue) != 1:
            raise AssertionError(
                "I-AUTOSAVE-08 violated: queue did not accept the "
                "payload"
            )
        client = _PreserveClient()
        session.dispatch(
            make_command(OperatorCommand.STEP_TICK), client=client
        )
        if session.tick_counter != 1:
            raise AssertionError(
                "I-AUTOSAVE-08 violated: tick_counter did not advance "
                f"(got {session.tick_counter!r})"
            )
        # The post-dispatch autosave hook must have fired and set
        # last_autosave_status.
        last = session.last_autosave_status
        if last is None:
            raise AssertionError(
                "I-AUTOSAVE-08 violated: last_autosave_status is None "
                "after a successful /step"
            )
        if last.last_attempt_outcome != "ok":
            raise AssertionError(
                "I-AUTOSAVE-08 violated: last_attempt_outcome is "
                f"{last.last_attempt_outcome!r} (expected 'ok')"
            )
        if last.last_attempt_trigger != AutosaveTrigger.STEP_TICK.value:
            raise AssertionError(
                "I-AUTOSAVE-08 violated: last_attempt_trigger is "
                f"{last.last_attempt_trigger!r} (expected "
                f"{AutosaveTrigger.STEP_TICK.value!r})"
            )
        if not last.last_attempt_at:
            raise AssertionError(
                "I-AUTOSAVE-08 violated: last_attempt_at is empty"
            )
        # The DB on-disk file exists and has non-zero size.
        if not db_path.exists():
            raise AssertionError(
                "I-AUTOSAVE-08 violated: session DB was not written"
            )
        if db_path.stat().st_size == 0:
            raise AssertionError(
                "I-AUTOSAVE-08 violated: session DB is empty"
            )
