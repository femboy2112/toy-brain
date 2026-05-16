"""Phase 3.10c autosave-requires-DB fixture.

Drives:

* ``I-AUTOSAVE-03`` (REQUIRED) — ``/autosave-enable`` without
  ``--session-db`` raises ``PersistenceError``;
  ``--autosave-mode after-successful-mutation`` without ``--session-db``
  raises argparse error code 2 before main()'s body executes.
"""
from __future__ import annotations

import contextlib
import io
import sys

from brain.invariants import register
from brain.ui.__main__ import build_default_session, main
from brain.ui.autosave import (
    AutosaveMode,
    autosave_enable,
)
from brain.ui.persistence import PersistenceError


@register("I-AUTOSAVE-03", status="REQUIRED")
def check_i_autosave_03_requires_db() -> None:
    # autosave_enable on a session with session_store_config=None
    # raises PersistenceError when mode is non-OFF.
    session = build_default_session()
    if session.session_store_config is not None:
        raise AssertionError(
            "I-AUTOSAVE-03 violated: default session has a session DB "
            "configured"
        )
    try:
        autosave_enable(
            session, AutosaveMode.AFTER_SUCCESSFUL_MUTATION
        )
    except PersistenceError:
        pass
    else:
        raise AssertionError(
            "I-AUTOSAVE-03 violated: autosave_enable accepted non-OFF "
            "mode on a session without a configured DB"
        )

    # autosave_enable(session, OFF) succeeds even without a DB
    # (OFF is the cold-start mode; no DB is required).
    report = autosave_enable(session, AutosaveMode.OFF)
    if report.mode is not AutosaveMode.OFF:
        raise AssertionError(
            "I-AUTOSAVE-03 violated: autosave_enable(..., OFF) on a "
            f"DB-less session produced mode {report.mode!r}"
        )

    # CLI parser path: --autosave-mode after-successful-mutation without
    # --session-db raises argparse error code 2 BEFORE main()'s body
    # executes. parser.error() calls sys.exit(2) via argparse and
    # writes to sys.stderr (not the injected captured stream), so we
    # silence the real sys.stderr / sys.stdout temporarily to keep the
    # invariants-runner JSON output clean.
    captured_stderr = io.StringIO()
    captured_stdout = io.StringIO()
    captured_stdin = io.StringIO()
    real_stderr = io.StringIO()
    real_stdout = io.StringIO()
    with contextlib.redirect_stderr(real_stderr), contextlib.redirect_stdout(real_stdout):
        try:
            exit_code = main(
                argv=["--autosave-mode", "after-successful-mutation"],
                stdin=captured_stdin,
                stdout=captured_stdout,
                stderr=captured_stderr,
                env={},
            )
        except SystemExit as exc:
            sys_exit_code = exc.code
        else:
            sys_exit_code = None  # didn't raise
    if sys_exit_code is None:
        raise AssertionError(
            "I-AUTOSAVE-03 violated: --autosave-mode "
            "after-successful-mutation without --session-db did not "
            f"raise SystemExit (got return code {exit_code!r})"
        )
    if sys_exit_code != 2:
        raise AssertionError(
            "I-AUTOSAVE-03 violated: argparse exit code is "
            f"{sys_exit_code!r} (expected 2)"
        )
    # The argparse error message went to the redirected real stderr
    # (not the captured stream, because argparse uses sys.stderr
    # directly). Verify it mentioned --session-db.
    err_text = real_stderr.getvalue()
    if "session-db" not in err_text:
        raise AssertionError(
            "I-AUTOSAVE-03 violated: argparse error did not mention "
            f"session-db (stderr: {err_text!r})"
        )
    # The argparse parser.error() path writes through argparse's own
    # sys.stderr (not the injected captured stderr), so we only assert
    # the SystemExit code above; verifying the error mentions
    # --session-db is exercised by the parser_error_test below
    # (parse_args -> SystemExit even when stderr is sys.stderr).

    # Counter-check: --autosave-mode off without --session-db is fine
    # (it is the cold-start default).
    parser_args_argv = ["--autosave-mode", "off", "--check-terminal"]
    captured_stdout2 = io.StringIO()
    captured_stderr2 = io.StringIO()
    captured_stdin2 = io.StringIO()
    # --check-terminal exits before any LLM / curses init, so this is
    # the cleanest way to verify the argparse path accepts off + no DB.
    try:
        result = main(
            argv=parser_args_argv,
            stdin=captured_stdin2,
            stdout=captured_stdout2,
            stderr=captured_stderr2,
            env={},
        )
    except SystemExit as exc:
        # --check-terminal returns 0/1 from main; SystemExit means
        # argparse rejected the args, which would be a regression.
        raise AssertionError(
            "I-AUTOSAVE-03 violated: --autosave-mode off + "
            "--check-terminal raised SystemExit "
            f"({exc.code!r}; stderr={captured_stderr2.getvalue()!r})"
        )
    # Either exit code is fine — we just verified no argparse error.
    if result not in (0, 1):
        raise AssertionError(
            "I-AUTOSAVE-03 violated: --autosave-mode off path returned "
            f"unexpected code {result!r}"
        )
