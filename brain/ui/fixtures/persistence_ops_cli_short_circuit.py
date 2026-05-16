"""Phase 3.10a CLI short-circuit + exit-code fixture.

Drives:

* ``I-OPSHARDEN-09`` (REQUIRED) — CLI short-circuit ordering and
  mutual exclusion + exit codes. ``brain/ui/__main__.py`` parses
  ``--db-status``, ``--db-verify``, ``--db-backup PATH``,
  ``--db-backup-force``. The three new short-circuit flags are
  mutually exclusive at argparse time. They short-circuit AFTER
  ``--check-terminal`` and ``--print-once`` but BEFORE
  ``_resolve_llm_runtime_config`` and curses initialization. On
  success the process exits with code 0; on failure with code 1.

* ``I-OPSHARDEN-14`` (STRUCTURAL) — Exit code mapping fixture.
  ``--db-status`` returns 0 on success and 1 on missing DB.
  ``--db-verify`` returns 0 on PASS and 1 on FAIL.
  ``--db-backup`` returns 0 on success and 1 on failure.
"""
from __future__ import annotations

import io
import pathlib
import tempfile

from brain.invariants import register
from brain.ui.__main__ import build_arg_parser, main
from brain.ui.persistence import SessionStoreConfig, save_session
from brain.ui.__main__ import build_default_session


def _run_main(argv: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    rc = main(argv=argv, stdout=stdout, stderr=stderr, env={"TERM": "xterm"})
    return rc, stdout.getvalue(), stderr.getvalue()


@register("I-OPSHARDEN-09", status="REQUIRED")
def check_i_opsharden_09_cli_short_circuit() -> None:
    parser = build_arg_parser()
    # Mutual exclusion: --db-status + --db-verify must fail at parse.
    raised = False
    try:
        parser.parse_args([
            "--session-db", "/tmp/x.sqlite3",
            "--db-status", "--db-verify",
        ])
    except SystemExit:
        raised = True
    if not raised:
        raise AssertionError(
            "I-OPSHARDEN-09 violated: argparse accepted --db-status + "
            "--db-verify together"
        )

    # Combining --db-backup with --db-status must also fail.
    raised = False
    try:
        parser.parse_args([
            "--session-db", "/tmp/x.sqlite3",
            "--db-status", "--db-backup", "/tmp/y.sqlite3",
        ])
    except SystemExit:
        raised = True
    if not raised:
        raise AssertionError(
            "I-OPSHARDEN-09 violated: argparse accepted --db-status + "
            "--db-backup together"
        )


@register("I-OPSHARDEN-14", status="STRUCTURAL")
def check_i_opsharden_14_exit_codes() -> None:
    with tempfile.TemporaryDirectory(prefix="brain-opsharden-14-") as td:
        db_path = pathlib.Path(td) / "session.sqlite3"
        missing_path = pathlib.Path(td) / "missing.sqlite3"
        dst_path = pathlib.Path(td) / "dst.sqlite3"

        # Set up a valid saved DB for the success branches.
        session = build_default_session()
        save_session(session, SessionStoreConfig(db_path=db_path))

        # --db-status on a missing DB -> exit code 1.
        rc, out, _err = _run_main([
            "--session-db", str(missing_path), "--db-status",
        ])
        if rc != 1:
            raise AssertionError(
                "I-OPSHARDEN-14 violated: --db-status on missing DB "
                f"returned rc={rc}, expected 1 (out={out!r})"
            )

        # --db-status on existing DB -> exit code 0.
        rc, out, _err = _run_main([
            "--session-db", str(db_path), "--db-status",
        ])
        if rc != 0:
            raise AssertionError(
                "I-OPSHARDEN-14 violated: --db-status on existing DB "
                f"returned rc={rc}, expected 0 (out={out!r})"
            )

        # --db-verify on existing DB -> exit code 0.
        rc, out, _err = _run_main([
            "--session-db", str(db_path), "--db-verify",
        ])
        if rc != 0:
            raise AssertionError(
                "I-OPSHARDEN-14 violated: --db-verify on existing DB "
                f"returned rc={rc}, expected 0 (out={out!r})"
            )

        # --db-verify on missing DB -> exit code 1.
        rc, out, _err = _run_main([
            "--session-db", str(missing_path), "--db-verify",
        ])
        if rc != 1:
            raise AssertionError(
                "I-OPSHARDEN-14 violated: --db-verify on missing DB "
                f"returned rc={rc}, expected 1 (out={out!r})"
            )

        # --db-backup success -> exit code 0.
        rc, out, _err = _run_main([
            "--session-db", str(db_path),
            "--db-backup", str(dst_path),
        ])
        if rc != 0:
            raise AssertionError(
                "I-OPSHARDEN-14 violated: --db-backup success returned "
                f"rc={rc}, expected 0 (out={out!r})"
            )

        # --db-backup overwrite without --force -> exit code 1.
        rc, out, _err = _run_main([
            "--session-db", str(db_path),
            "--db-backup", str(dst_path),
        ])
        if rc != 1:
            raise AssertionError(
                "I-OPSHARDEN-14 violated: --db-backup repeat without "
                f"--force returned rc={rc}, expected 1 (out={out!r})"
            )

        # --db-backup with --force overwrites and returns 0.
        rc, out, _err = _run_main([
            "--session-db", str(db_path),
            "--db-backup", str(dst_path),
            "--db-backup-force",
        ])
        if rc != 0:
            raise AssertionError(
                "I-OPSHARDEN-14 violated: --db-backup --db-backup-force "
                f"returned rc={rc}, expected 0 (out={out!r})"
            )

        # Missing --session-db -> exit code 1.
        rc, _out, _err = _run_main(["--db-status"])
        if rc != 1:
            raise AssertionError(
                "I-OPSHARDEN-14 violated: --db-status without --session-db "
                f"returned rc={rc}, expected 1"
            )
