"""Phase 3.10c Autosave Policy — runtime.

Default-OFF opt-in autosave policy that hooks the central
:class:`brain.ui.session.OperatorSession` dispatch loop. After a mutating
dispatch (``/step`` with ``STEP_TICK`` or ``/stream-promote`` with
``STREAM_PROMOTE``) succeeds, the central :meth:`OperatorSession.dispatch`
calls :func:`maybe_autosave_after_mutation` which, when autosave is
enabled and a session DB is configured, routes through the existing
:func:`brain.ui.persistence.save_session` helper.

Catalog rows driven from here (Phase 3.10c):

* ``I-AUTOSAVE-01`` (REQUIRED) — default OFF on every cold start.
* ``I-AUTOSAVE-02`` (REQUIRED) — AutosaveConfig with mode != OFF +
  empty ``db_path_str`` raises ``ValueError``.
* ``I-AUTOSAVE-03`` (REQUIRED) — ``/autosave-enable`` without
  ``--session-db`` raises ``PersistenceError``.
* ``I-AUTOSAVE-04`` (REQUIRED) — ``/autosave-enable`` with valid mode +
  DB transitions ``session.autosave_config`` correctly.
* ``I-AUTOSAVE-05`` (REQUIRED) — ``/autosave-disable`` is idempotent.
* ``I-AUTOSAVE-06`` (REQUIRED) — ``/autosave-status`` returns a bounded
  :class:`AutosaveStatusReport`; never raises.
* ``I-AUTOSAVE-07`` (REQUIRED) — :func:`maybe_autosave_after_mutation`
  never raises.
* ``I-AUTOSAVE-08`` (REQUIRED) — ``/step`` + autosave + success ->
  ``last_attempt_outcome="ok"``.
* ``I-AUTOSAVE-09`` (REQUIRED) — failed dispatch does NOT trigger
  autosave.
* ``I-AUTOSAVE-10`` (REQUIRED) — read-only dispatch does NOT trigger
  autosave.
* ``I-AUTOSAVE-11`` (REQUIRED) — autosave reuses ``save_session``; no
  second save code path exists.
* ``I-AUTOSAVE-12`` (STRUCTURAL) — ``AutosaveMode`` + ``AutosaveTrigger``
  are closed ``(str, Enum)``.
* ``I-AUTOSAVE-13`` (STRUCTURAL) — module static audit.
* ``I-AUTOSAVE-14`` (STRUCTURAL) — session resource audit +
  outcome-detection contract.

Hard boundaries pinned by ``PHASE3_10C_AUTOSAVE_CORRIGENDA.md`` and
``PHASE3_10C_AUTOSAVE_CATALOG_PATCH_PLAN.md``:

* No ``@atexit.register``, no ``threading``, no ``asyncio``, no signal
  handler, no ``curses`` callback, no ``tick(`` call.
* SQLite via the existing :func:`brain.ui.persistence.save_session`
  helper only. This module never imports ``sqlite3`` directly.
* Failure preserves the live :class:`OperatorSession`; the
  ``PersistenceError`` is absorbed into the typed status report.
* Module-level statements are limited to imports, constants, function
  defs, and class defs (plus this docstring).
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from brain.ui.persistence import (
    PersistenceError,
    SessionStoreConfig,
    save_session,
)
from brain.ui.persistence_ops import OPS_REPORT_TEXT_MAX_LEN


# ---------------------------------------------------------------------------
# Closed enums.
# ---------------------------------------------------------------------------


class AutosaveMode(str, Enum):
    """Finite closed enumeration of autosave modes.

    ``OFF`` is the default on every cold start.
    ``AFTER_SUCCESSFUL_MUTATION`` is the only non-off mode authorized
    by Phase 3.10c v1; future modes require an explicit catalog row
    family extension.
    """

    OFF = "off"
    AFTER_SUCCESSFUL_MUTATION = "after-successful-mutation"


#: The closed set of accepted autosave modes. Used by
#: :class:`AutosaveConfig` validation and the
#: ``autosave_mode_closed`` / ``autosave_trigger_set`` fixtures.
SUPPORTED_AUTOSAVE_MODES: frozenset[AutosaveMode] = frozenset({
    AutosaveMode.OFF,
    AutosaveMode.AFTER_SUCCESSFUL_MUTATION,
})


class AutosaveTrigger(str, Enum):
    """Finite closed enumeration of autosave triggers.

    The trigger is the *cause* of the post-dispatch autosave invocation.
    Only mutating dispatches that succeeded appear here; the static
    audit confirms the trigger set is closed and that no read-only
    dispatch is wired to fire autosave.
    """

    STEP_TICK = "step_tick"
    STREAM_PROMOTE = "stream_promote"


#: The closed set of accepted autosave triggers. Used by
#: :func:`maybe_autosave_after_mutation` and the
#: ``autosave_trigger_set`` fixture.
SUPPORTED_AUTOSAVE_TRIGGERS: frozenset[AutosaveTrigger] = frozenset({
    AutosaveTrigger.STEP_TICK,
    AutosaveTrigger.STREAM_PROMOTE,
})


#: Closed set of accepted outcome strings for
#: :attr:`AutosaveStatusReport.last_attempt_outcome`.
AUTOSAVE_STATUS_OUTCOMES: frozenset[str] = frozenset({"", "ok", "error"})


# ---------------------------------------------------------------------------
# Typed records.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AutosaveConfig:
    """Immutable autosave configuration carried on :class:`OperatorSession`.

    Carries the active mode plus a denormalized path string copy for
    display. The actual :class:`SessionStoreConfig` still lives on
    :attr:`OperatorSession.session_store_config`; autosave never
    duplicates the path semantics, only the display string.
    """

    mode: AutosaveMode = AutosaveMode.OFF
    db_path_str: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.mode, AutosaveMode):
            raise TypeError(
                "AutosaveConfig.mode must be an AutosaveMode "
                f"(got {type(self.mode).__name__})"
            )
        if self.mode not in SUPPORTED_AUTOSAVE_MODES:
            raise ValueError(
                "AutosaveConfig.mode must be in "
                f"{sorted(m.value for m in SUPPORTED_AUTOSAVE_MODES)!r} "
                f"(got {self.mode!r})"
            )
        if not isinstance(self.db_path_str, str):
            raise TypeError(
                "AutosaveConfig.db_path_str must be a str "
                f"(got {type(self.db_path_str).__name__})"
            )
        if len(self.db_path_str) > OPS_REPORT_TEXT_MAX_LEN:
            raise ValueError(
                "AutosaveConfig.db_path_str length "
                f"{len(self.db_path_str)} exceeds "
                f"OPS_REPORT_TEXT_MAX_LEN={OPS_REPORT_TEXT_MAX_LEN}"
            )
        if self.db_path_str and not self.db_path_str.isprintable():
            raise ValueError(
                "AutosaveConfig.db_path_str must be printable "
                f"(got {self.db_path_str!r})"
            )
        # mode=OFF + db_path_str="" is the cold-start default. A non-OFF
        # mode requires a non-empty db_path_str (drives I-AUTOSAVE-02).
        if self.mode is not AutosaveMode.OFF and not self.db_path_str:
            raise ValueError(
                "AutosaveConfig with non-OFF mode requires a "
                "non-empty db_path_str"
            )


@dataclass(frozen=True, slots=True)
class AutosaveStatusReport:
    """Bounded read-only snapshot of the autosave subsystem state.

    Drives ``I-AUTOSAVE-06`` (bounded report; never raises). Every
    string field is bounded by :data:`OPS_REPORT_TEXT_MAX_LEN`; every
    integer field is non-negative; ``last_attempt_outcome`` is in
    :data:`AUTOSAVE_STATUS_OUTCOMES`; ``last_attempt_trigger`` is in
    ``{t.value for t in SUPPORTED_AUTOSAVE_TRIGGERS} | {""}``.
    """

    mode: AutosaveMode
    db_path_str: str
    last_attempt_tick: int
    last_attempt_outcome: str
    last_attempt_at: str
    last_attempt_trigger: str
    last_error_text: str

    def __post_init__(self) -> None:
        if not isinstance(self.mode, AutosaveMode):
            raise TypeError(
                "AutosaveStatusReport.mode must be an AutosaveMode "
                f"(got {type(self.mode).__name__})"
            )
        if self.mode not in SUPPORTED_AUTOSAVE_MODES:
            raise ValueError(
                "AutosaveStatusReport.mode must be in "
                f"{sorted(m.value for m in SUPPORTED_AUTOSAVE_MODES)!r} "
                f"(got {self.mode!r})"
            )
        for field_name in (
            "db_path_str",
            "last_attempt_outcome",
            "last_attempt_at",
            "last_attempt_trigger",
            "last_error_text",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(
                    f"AutosaveStatusReport.{field_name} must be a str "
                    f"(got {type(value).__name__})"
                )
            if len(value) > OPS_REPORT_TEXT_MAX_LEN:
                raise ValueError(
                    f"AutosaveStatusReport.{field_name} length "
                    f"{len(value)} exceeds "
                    f"OPS_REPORT_TEXT_MAX_LEN={OPS_REPORT_TEXT_MAX_LEN}"
                )
            if value and not value.isprintable():
                raise ValueError(
                    f"AutosaveStatusReport.{field_name} must be "
                    f"printable (got {value!r})"
                )
        if not isinstance(self.last_attempt_tick, int) or isinstance(
            self.last_attempt_tick, bool
        ):
            raise TypeError(
                "AutosaveStatusReport.last_attempt_tick must be an int "
                f"(got {type(self.last_attempt_tick).__name__})"
            )
        if self.last_attempt_tick < 0:
            raise ValueError(
                "AutosaveStatusReport.last_attempt_tick must be "
                f"non-negative (got {self.last_attempt_tick!r})"
            )
        if self.last_attempt_outcome not in AUTOSAVE_STATUS_OUTCOMES:
            raise ValueError(
                "AutosaveStatusReport.last_attempt_outcome must be in "
                f"{sorted(AUTOSAVE_STATUS_OUTCOMES)!r} "
                f"(got {self.last_attempt_outcome!r})"
            )
        allowed_triggers = frozenset(
            {t.value for t in SUPPORTED_AUTOSAVE_TRIGGERS} | {""}
        )
        if self.last_attempt_trigger not in allowed_triggers:
            raise ValueError(
                "AutosaveStatusReport.last_attempt_trigger must be in "
                f"{sorted(allowed_triggers)!r} "
                f"(got {self.last_attempt_trigger!r})"
            )


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _bound_error_text(text: str) -> str:
    """Coerce *text* into bounded printable form for the typed report.

    Replaces non-printable characters with ``?`` and truncates to
    :data:`OPS_REPORT_TEXT_MAX_LEN` (appending an ellipsis when
    truncation occurred).
    """
    if not isinstance(text, str):
        text = str(text)
    if text and not text.isprintable():
        text = "".join(ch if ch.isprintable() else "?" for ch in text)
    if len(text) > OPS_REPORT_TEXT_MAX_LEN:
        text = text[: OPS_REPORT_TEXT_MAX_LEN - 1] + "…"
    return text


def _utc_now_iso(now: Optional[datetime.datetime] = None) -> str:
    """Return a bounded ISO-8601 UTC timestamp string."""
    moment = now if now is not None else datetime.datetime.now(
        tz=datetime.timezone.utc
    )
    text = moment.isoformat()
    if len(text) > OPS_REPORT_TEXT_MAX_LEN:
        text = text[:OPS_REPORT_TEXT_MAX_LEN]
    return text


def _default_status_report(
    config: Optional[AutosaveConfig],
    last: Optional[AutosaveStatusReport],
) -> AutosaveStatusReport:
    """Build an :class:`AutosaveStatusReport` from in-memory session fields."""
    mode = config.mode if config is not None else AutosaveMode.OFF
    db_path_str = config.db_path_str if config is not None else ""
    if last is None:
        return AutosaveStatusReport(
            mode=mode,
            db_path_str=db_path_str,
            last_attempt_tick=0,
            last_attempt_outcome="",
            last_attempt_at="",
            last_attempt_trigger="",
            last_error_text="",
        )
    # The persisted history fields stay; only the live mode / path
    # string track the current config.
    return AutosaveStatusReport(
        mode=mode,
        db_path_str=db_path_str,
        last_attempt_tick=last.last_attempt_tick,
        last_attempt_outcome=last.last_attempt_outcome,
        last_attempt_at=last.last_attempt_at,
        last_attempt_trigger=last.last_attempt_trigger,
        last_error_text=last.last_error_text,
    )


def autosave_status(session: object) -> AutosaveStatusReport:
    """Read ``session.autosave_config`` and ``session.last_autosave_status``.

    Drives ``I-AUTOSAVE-06``. Reads in-memory fields only; never touches
    disk; never raises. Returns a bounded :class:`AutosaveStatusReport`
    with ``""`` / ``0`` defaults when the underlying fields are
    ``None``.
    """
    config = getattr(session, "autosave_config", None)
    last = getattr(session, "last_autosave_status", None)
    if config is not None and not isinstance(config, AutosaveConfig):
        # Defensive: a caller that smuggled a non-typed config into
        # the session still gets a typed-default report rather than a
        # raise (drives the never-raises contract).
        config = None
    if last is not None and not isinstance(last, AutosaveStatusReport):
        last = None
    return _default_status_report(config, last)


def autosave_enable(
    session: object,
    mode: AutosaveMode,
) -> AutosaveStatusReport:
    """Switch ``session.autosave_config`` to *mode*.

    Drives ``I-AUTOSAVE-03`` and ``I-AUTOSAVE-04``. Raises
    :class:`PersistenceError` when *mode* is non-OFF and
    ``session.session_store_config`` is ``None``; raises
    :class:`PersistenceError` on invalid mode (any value outside
    :data:`SUPPORTED_AUTOSAVE_MODES`). Does NOT invoke
    :func:`save_session`; the next eligible mutating dispatch does that.
    """
    if not isinstance(mode, AutosaveMode):
        raise PersistenceError(
            "autosave_enable mode must be an AutosaveMode "
            f"(got {type(mode).__name__})"
        )
    if mode not in SUPPORTED_AUTOSAVE_MODES:
        raise PersistenceError(
            "autosave_enable mode must be in "
            f"{sorted(m.value for m in SUPPORTED_AUTOSAVE_MODES)!r} "
            f"(got {mode!r})"
        )
    store_config = getattr(session, "session_store_config", None)
    if mode is not AutosaveMode.OFF:
        if not isinstance(store_config, SessionStoreConfig):
            raise PersistenceError(
                "autosave_enable requires a configured --session-db "
                "for a non-OFF mode"
            )
        db_path_str = str(store_config.db_path)
        # Bound the display string before AutosaveConfig sees it.
        if len(db_path_str) > OPS_REPORT_TEXT_MAX_LEN:
            db_path_str = db_path_str[
                : OPS_REPORT_TEXT_MAX_LEN - 1
            ] + "…"
        new_config = AutosaveConfig(mode=mode, db_path_str=db_path_str)
    else:
        new_config = AutosaveConfig(mode=AutosaveMode.OFF, db_path_str="")
    session.autosave_config = new_config  # type: ignore[attr-defined]
    return autosave_status(session)


def autosave_disable(session: object) -> AutosaveStatusReport:
    """Switch ``session.autosave_config`` to :data:`AutosaveMode.OFF`.

    Drives ``I-AUTOSAVE-05``. Idempotent; never raises. The
    last-attempt history is preserved so the operator can still see
    the outcome of the most recent autosave attempt after disabling.
    """
    session.autosave_config = AutosaveConfig(  # type: ignore[attr-defined]
        mode=AutosaveMode.OFF, db_path_str=""
    )
    return autosave_status(session)


def maybe_autosave_after_mutation(
    session: object,
    *,
    triggered_by: AutosaveTrigger,
    now: Optional[datetime.datetime] = None,
) -> Optional[AutosaveStatusReport]:
    """Post-dispatch autosave trigger.

    Drives ``I-AUTOSAVE-07`` / ``I-AUTOSAVE-08`` / ``I-AUTOSAVE-11``.
    Returns ``None`` when autosave is OFF / unset, when
    ``session.session_store_config`` is ``None``, or when
    *triggered_by* is not in :data:`SUPPORTED_AUTOSAVE_TRIGGERS`.

    Otherwise calls :func:`save_session` (the single Phase 3.9 save
    code path) and returns a typed :class:`AutosaveStatusReport`.
    On :class:`PersistenceError` the helper absorbs the exception and
    populates ``outcome="error"`` + bounded ``last_error_text``.
    NEVER raises. The caller (the central dispatch in
    :class:`OperatorSession`) stores the returned report on
    ``session.last_autosave_status``.
    """
    config = getattr(session, "autosave_config", None)
    if not isinstance(config, AutosaveConfig):
        return None
    if config.mode is AutosaveMode.OFF:
        return None
    if not isinstance(triggered_by, AutosaveTrigger):
        return None
    if triggered_by not in SUPPORTED_AUTOSAVE_TRIGGERS:
        return None
    store_config = getattr(session, "session_store_config", None)
    if not isinstance(store_config, SessionStoreConfig):
        return None

    tick_counter = getattr(session, "tick_counter", 0)
    if not isinstance(tick_counter, int) or tick_counter < 0:
        tick_counter = 0

    timestamp = _utc_now_iso(now)
    try:
        save_session(session, store_config, now=now)
    except PersistenceError as exc:
        return AutosaveStatusReport(
            mode=config.mode,
            db_path_str=config.db_path_str,
            last_attempt_tick=tick_counter,
            last_attempt_outcome="error",
            last_attempt_at=timestamp,
            last_attempt_trigger=triggered_by.value,
            last_error_text=_bound_error_text(str(exc)),
        )
    except Exception as exc:  # noqa: BLE001 - never raise into dispatch
        # Defense in depth: save_session contracts to raise only
        # PersistenceError, but any unexpected error is still absorbed
        # into the typed report (drives the never-raises contract).
        return AutosaveStatusReport(
            mode=config.mode,
            db_path_str=config.db_path_str,
            last_attempt_tick=tick_counter,
            last_attempt_outcome="error",
            last_attempt_at=timestamp,
            last_attempt_trigger=triggered_by.value,
            last_error_text=_bound_error_text(
                f"{type(exc).__name__}: {exc}"
            ),
        )

    return AutosaveStatusReport(
        mode=config.mode,
        db_path_str=config.db_path_str,
        last_attempt_tick=tick_counter,
        last_attempt_outcome="ok",
        last_attempt_at=timestamp,
        last_attempt_trigger=triggered_by.value,
        last_error_text="",
    )


__all__ = [
    "AUTOSAVE_STATUS_OUTCOMES",
    "AutosaveConfig",
    "AutosaveMode",
    "AutosaveStatusReport",
    "AutosaveTrigger",
    "SUPPORTED_AUTOSAVE_MODES",
    "SUPPORTED_AUTOSAVE_TRIGGERS",
    "autosave_disable",
    "autosave_enable",
    "autosave_status",
    "maybe_autosave_after_mutation",
]
