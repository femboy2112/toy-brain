"""Phase 3.10c autosave default-OFF + idempotent disable fixture.

Drives:

* ``I-AUTOSAVE-01`` (REQUIRED) — default OFF on every cold start.
  :func:`build_default_session` returns a session whose
  ``autosave_config`` is ``None`` or whose mode is
  :data:`AutosaveMode.OFF`; the argparse default for
  ``--autosave-mode`` is ``"off"``; neither path reads an ambient
  environment variable.
* ``I-AUTOSAVE-05`` (REQUIRED) — ``/autosave-disable`` is idempotent.
  :func:`autosave_disable` on a session in any autosave state returns
  an :class:`AutosaveStatusReport` with ``mode = OFF``; calling it
  twice in a row produces identical reports; it never raises.
"""
from __future__ import annotations

import os
import pathlib
import tempfile

from brain.invariants import register
from brain.ui.__main__ import build_arg_parser, build_default_session
from brain.ui.autosave import (
    AutosaveConfig,
    AutosaveMode,
    AutosaveStatusReport,
    autosave_disable,
    autosave_enable,
    autosave_status,
)
from brain.ui.persistence import SessionStoreConfig


_FORBIDDEN_ENV_KEYS: tuple[str, ...] = (
    "BRAIN_AUTOSAVE_MODE",
    "BRAIN_AUTOSAVE",
    "AUTOSAVE_MODE",
    "AUTOSAVE",
)


@register("I-AUTOSAVE-01", status="REQUIRED")
def check_i_autosave_01_default_off() -> None:
    # Session construction default.
    session = build_default_session()
    config = session.autosave_config
    if config is not None:
        if not isinstance(config, AutosaveConfig):
            raise AssertionError(
                "I-AUTOSAVE-01 violated: autosave_config is set but not "
                f"an AutosaveConfig (got {type(config).__name__})"
            )
        if config.mode is not AutosaveMode.OFF:
            raise AssertionError(
                "I-AUTOSAVE-01 violated: default session autosave_config "
                f"mode is {config.mode!r} (expected OFF or None)"
            )
    if session.last_autosave_status is not None:
        raise AssertionError(
            "I-AUTOSAVE-01 violated: default session last_autosave_status "
            f"is not None (got {session.last_autosave_status!r})"
        )

    # CLI parser default for --autosave-mode.
    parser = build_arg_parser()
    args = parser.parse_args([])
    if args.autosave_mode != "off":
        raise AssertionError(
            "I-AUTOSAVE-01 violated: parser default --autosave-mode is "
            f"{args.autosave_mode!r} (expected 'off')"
        )

    # No ambient environment variable widens the cold-start surface.
    snapshot = dict(os.environ)
    try:
        for key in _FORBIDDEN_ENV_KEYS:
            os.environ[key] = "after-successful-mutation"
        args_env = build_arg_parser().parse_args([])
        if args_env.autosave_mode != "off":
            raise AssertionError(
                "I-AUTOSAVE-01 violated: environment variable widened "
                f"the default (got {args_env.autosave_mode!r})"
            )
        env_session = build_default_session()
        env_config = env_session.autosave_config
        if env_config is not None and env_config.mode is not AutosaveMode.OFF:
            raise AssertionError(
                "I-AUTOSAVE-01 violated: environment variable widened "
                f"build_default_session (got {env_config.mode!r})"
            )
    finally:
        for key in _FORBIDDEN_ENV_KEYS:
            os.environ.pop(key, None)
        os.environ.update(snapshot)

    # Status report on the default session is bounded and never raises.
    report = autosave_status(session)
    if not isinstance(report, AutosaveStatusReport):
        raise AssertionError(
            "I-AUTOSAVE-01 violated: autosave_status returned "
            f"{type(report).__name__}"
        )
    if report.mode is not AutosaveMode.OFF:
        raise AssertionError(
            "I-AUTOSAVE-01 violated: default-session report mode is "
            f"{report.mode!r}"
        )


@register("I-AUTOSAVE-05", status="REQUIRED")
def check_i_autosave_05_disable_is_idempotent() -> None:
    # Disable on a freshly-built session: never raises; produces OFF.
    session = build_default_session()
    first = autosave_disable(session)
    if not isinstance(first, AutosaveStatusReport):
        raise AssertionError(
            "I-AUTOSAVE-05 violated: autosave_disable returned "
            f"{type(first).__name__}"
        )
    if first.mode is not AutosaveMode.OFF:
        raise AssertionError(
            "I-AUTOSAVE-05 violated: disable produced mode "
            f"{first.mode!r}"
        )
    # Idempotent: a second call produces an identical report.
    second = autosave_disable(session)
    if second != first:
        raise AssertionError(
            "I-AUTOSAVE-05 violated: a second autosave_disable produced "
            f"a different report ({second!r} vs {first!r})"
        )

    # Disable after a non-OFF enable also works and produces OFF.
    with tempfile.TemporaryDirectory(prefix="brain-autosave-05-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        configured = build_default_session()
        configured.session_store_config = SessionStoreConfig(db_path=db_path)
        autosave_enable(
            configured, AutosaveMode.AFTER_SUCCESSFUL_MUTATION
        )
        report_after_enable = autosave_status(configured)
        if (
            report_after_enable.mode
            is not AutosaveMode.AFTER_SUCCESSFUL_MUTATION
        ):
            raise AssertionError(
                "I-AUTOSAVE-05 violated: enable did not switch mode "
                f"(got {report_after_enable.mode!r})"
            )
        disabled = autosave_disable(configured)
        if disabled.mode is not AutosaveMode.OFF:
            raise AssertionError(
                "I-AUTOSAVE-05 violated: disable after enable produced "
                f"mode {disabled.mode!r}"
            )
        # Idempotent again on a previously-enabled session.
        disabled2 = autosave_disable(configured)
        if disabled2 != disabled:
            raise AssertionError(
                "I-AUTOSAVE-05 violated: a second disable on an enabled "
                f"session produced {disabled2!r} vs {disabled!r}"
            )
