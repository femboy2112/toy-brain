"""CLI entrypoint for ``python3 -m brain.ui``.

This module is the operator-facing entrypoint that either launches the
thin curses wrapper (:func:`brain.ui.tui.run_curses`) or prints a
helpful local message and exits when no usable terminal is available.

Catalog rows driven from here:

* ``I-UI-07`` (REQUIRED) — no UI path performs real LLM behaviour, spawns
  a subprocess, opens a shell, performs network I/O, writes a file
  outside an explicitly user-approved save/export path (none exist in
  this campaign), or invokes arbitrary host execution. This module
  imports only the Python standard library plus the local UI surfaces;
  the static AST audit in :mod:`brain.ui.fixtures.tui_smoke` enforces
  this property.
* ``I-UI-12`` (STRUCTURAL) — the entrypoint exits with a helpful local
  message when no usable terminal is available. It does not spawn
  alternate shells, open files, call a browser, or mutate the
  filesystem. The non-interactive smoke test exercises this code path
  without attaching to a real terminal by calling
  :func:`detect_terminal` and :func:`build_no_terminal_message`
  directly.

Default tick stand-in:

The entrypoint ships an ``OfflineStandInClient`` that returns the literal
string ``"PRESERVE"`` for every prompt. This is a **deterministic local
stand-in** for the LLM-protocol surface the kernel's ``tick()`` consumes;
it performs no network I/O, no subprocess spawn, and no file mutation.
The campaign explicitly forbids real LLM behaviour; the stand-in is the
only way to drive the bottom-up tick path from an operator-facing TUI
without inviting an external dependency.

The entrypoint never imports :mod:`brain.tlica` or :mod:`brain.llm` and
never opens a file outside this module's own source.
"""
from __future__ import annotations

import argparse
import io
import os
import pathlib
import sys
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Optional, TextIO

from brain.ui.commands import Command, OperatorCommand, make_command
from brain.ui.composer import ComposerState
from brain.ui.render import render_agent
from brain.ui.session import OperatorSession
from brain.ui.transcript import OperatorTranscript
from brain.ui.tui import build_agent_view_for_session

if TYPE_CHECKING:  # pragma: no cover - typing-only imports
    pass


# ---------------------------------------------------------------------------
# Terminal detection — pure, side-effect-free probe.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TerminalCheck:
    """Result of :func:`detect_terminal`.

    ``usable`` is ``True`` only when stdin and stdout are both attached
    to a TTY and the ``TERM`` environment variable is set to something
    other than ``"dumb"`` / empty / unset. ``reason`` is a printable
    string that the entrypoint surfaces in the "no terminal" code path.
    """

    usable: bool
    reason: str


def detect_terminal(
    *,
    stdin: Optional[TextIO] = None,
    stdout: Optional[TextIO] = None,
    env: Optional[dict[str, str]] = None,
) -> TerminalCheck:
    """Return whether the current process has a usable terminal.

    Pure: it reads :data:`sys.stdin` / :data:`sys.stdout` / :data:`os.environ`
    by default but accepts injected stand-ins so the smoke test can
    exercise the "no terminal" branch deterministically.
    """
    stdin_ = stdin if stdin is not None else sys.stdin
    stdout_ = stdout if stdout is not None else sys.stdout
    env_ = env if env is not None else dict(os.environ)

    if not hasattr(stdout_, "isatty") or not stdout_.isatty():
        return TerminalCheck(
            usable=False, reason="stdout is not attached to a terminal"
        )
    if not hasattr(stdin_, "isatty") or not stdin_.isatty():
        return TerminalCheck(
            usable=False, reason="stdin is not attached to a terminal"
        )
    term = env_.get("TERM", "")
    if not term:
        return TerminalCheck(usable=False, reason="TERM environment is unset")
    if term == "dumb":
        return TerminalCheck(usable=False, reason="TERM=dumb is not supported")
    return TerminalCheck(usable=True, reason=f"TERM={term}")


def build_no_terminal_message(check: TerminalCheck) -> str:
    """Helpful local message for the no-terminal exit path.

    The message lists what the entrypoint would do under a usable
    terminal, what to set up for it to run, and the deterministic
    alternative (``--print-once``) the entrypoint exposes for
    non-interactive inspection.
    """
    if not isinstance(check, TerminalCheck):
        raise TypeError(
            "build_no_terminal_message requires a TerminalCheck "
            f"(got {type(check).__name__})"
        )
    lines = (
        "brain.ui: no usable terminal detected.",
        f"  reason: {check.reason}",
        "  next:   re-run inside an interactive terminal "
        "(stdin + stdout both TTY, TERM set, not 'dumb').",
        "  alt:    `python3 -m brain.ui --print-once` renders one "
        "deterministic agent-layout frame of the operator view to stdout "
        "and exits.",
        "  policy: this entrypoint does not spawn shells, open files, "
        "call a browser, or perform network I/O.",
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# OfflineStandInClient — deterministic non-LLM stand-in.
# ---------------------------------------------------------------------------


class OfflineStandInClient:
    """Deterministic local stand-in for the LLM-protocol surface.

    Returns the literal string ``"PRESERVE"`` for every prompt. The
    kernel's :class:`brain.llm.llm_backed_ptcns.LLMBackedPtCns` retry
    shell parses this into :data:`brain.tlica.ptcns.ConsistencyEval.PRESERVE`,
    so the operator can drive the bottom-up tick path through
    :func:`brain.tick.tick` without depending on a real LLM client. This
    class performs no network I/O, no subprocess spawn, no file
    mutation. It is intentionally minimal — the only public method is
    :meth:`eval_consistency`.
    """

    def __init__(self) -> None:
        # Recording calls is useful for smoke / observability without
        # introducing any external surface.
        self.calls: int = 0

    def eval_consistency(self, prompt: str) -> str:
        if not isinstance(prompt, str):
            raise TypeError(
                "OfflineStandInClient.eval_consistency requires str prompt "
                f"(got {type(prompt).__name__})"
            )
        self.calls += 1
        return "PRESERVE"


# ---------------------------------------------------------------------------
# Default operator session builder.
# ---------------------------------------------------------------------------


def build_default_session() -> OperatorSession:
    """Construct a deterministic starting :class:`OperatorSession`.

    The session contains a minimal :class:`brain.tick.BrainState` whose
    profile has ``COGITO_ID`` at 1 plus one supporting content. The
    bottom-up tick path can be exercised against this session by
    queueing a :class:`brain.ui.commands.QueuePerceptPayload` and
    dispatching :data:`brain.ui.commands.OperatorCommand.STEP_TICK`.

    This helper imports the kernel builders lazily so the import-time
    dependency surface of :mod:`brain.ui.__main__` remains minimal
    (drives ``I-UI-07``).
    """
    # Lazy imports keep the static import graph for this module limited
    # to stdlib + brain.ui.* so the I-UI-07 audit has a clean root set.
    from brain.io_types import ContentRegistry
    from brain.tick import BrainState
    from brain.tlica.builders import (
        make_msi,
        make_profile_with_cogito,
        make_ptcns,
    )
    from brain.tlica.profile import COGITO_ID
    from brain.tlica.ptcns import ConsistencyEval

    profile = make_profile_with_cogito({COGITO_ID: 1, "alpha": Fraction(3, 4)})
    msi = make_msi(
        profile,
        contents={COGITO_ID, "alpha"},
        threshold=Fraction(1, 2),
    )
    ptcns = make_ptcns(
        msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "alpha": ConsistencyEval.PRESERVE,
        },
    )
    registry = ContentRegistry(texts=MappingProxyType({"alpha": "alpha text"}))
    state = BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)
    return OperatorSession(state=state)


# ---------------------------------------------------------------------------
# Argument parsing.
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Flags:

    * ``--print-once`` — render one deterministic agent-layout frame of
      the default operator view to stdout and exit. Useful for
      non-interactive inspection and for the I-UI-12 smoke fixture.
    * ``--check-terminal`` — print the result of :func:`detect_terminal`
      and exit. Never touches curses.
    * ``--llm-mode`` — Phase 3.8b LLM runtime toggle. Accepts
      ``offline`` (default), ``mock``, ``anthropic-api``, or
      ``claude-cli``. Model-backed modes require explicit opt-in.
    * ``--llm-anthropic-api-key`` — explicit API key override for
      ``anthropic-api``. Otherwise resolved from
      ``BRAIN_ANTHROPIC_API_KEY`` or ``ANTHROPIC_API_KEY``.
    * ``--llm-anthropic-model`` — model name override.
    * ``--llm-claude-cli-executable`` — executable override for
      ``claude-cli``.
    * ``--llm-timeout`` — request timeout in seconds.
    * ``--llm-enable-cache`` — wrap model-backed clients in
      :class:`CachedClient`. Only honored for ``anthropic-api`` /
      ``claude-cli``.
    * ``--llm-mock-response`` — repeatable canned response for ``mock``.
    """
    parser = argparse.ArgumentParser(
        prog="python3 -m brain.ui",
        description=(
            "Operator TUI entrypoint. Inspects BrainState / TickRecord / "
            "Phase 3.1-3.4 developmental histories and routes bottom-up "
            "PerceptEvent inputs through the public tick() path. No real "
            "LLM, shell, network, file mutation, or host execution unless "
            "an explicit --llm-mode is supplied."
        ),
    )
    parser.add_argument(
        "--print-once",
        action="store_true",
        help=(
            "render one deterministic agent-layout frame of the default "
            "operator view to stdout and exit"
        ),
    )
    parser.add_argument(
        "--check-terminal",
        action="store_true",
        help="print the terminal detection result and exit",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=80,
        help="terminal width for --print-once (default: 80)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=24,
        help="terminal height for --print-once (default: 24)",
    )
    parser.add_argument(
        "--llm-mode",
        default=None,
        help=(
            "LLM runtime mode: offline (default), mock, anthropic-api, "
            "or claude-cli. Model-backed modes require explicit opt-in. "
            "Also honors BRAIN_LLM_MODE; --llm-mode wins."
        ),
    )
    parser.add_argument(
        "--llm-anthropic-api-key",
        default=None,
        help=(
            "explicit Anthropic API key override; otherwise resolved "
            "from BRAIN_ANTHROPIC_API_KEY then ANTHROPIC_API_KEY"
        ),
    )
    parser.add_argument(
        "--llm-anthropic-model",
        default=None,
        help="model name override for anthropic-api",
    )
    parser.add_argument(
        "--llm-claude-cli-executable",
        default=None,
        help="executable override for claude-cli (default: claude)",
    )
    parser.add_argument(
        "--llm-timeout",
        default=None,
        help="request timeout in seconds (default: 30.0)",
    )
    parser.add_argument(
        "--llm-enable-cache",
        action="store_true",
        help=(
            "wrap model-backed clients with CachedClient under "
            "brain/.llm_cache; only honored for anthropic-api / claude-cli"
        ),
    )
    parser.add_argument(
        "--llm-mock-response",
        action="append",
        default=None,
        help=(
            "canned response for mode 'mock'; repeatable; required when "
            "--llm-mode mock is selected"
        ),
    )
    parser.add_argument(
        "--session-db",
        default=None,
        help=(
            "path to the SQLite session database used by /save-session "
            "and /load-session (Phase 3.9). Omit to disable persistence."
        ),
    )
    load_group = parser.add_mutually_exclusive_group()
    load_group.add_argument(
        "--load-session",
        dest="load_session",
        action="store_true",
        default=False,
        help=(
            "after argument parsing, load the session from --session-db "
            "before launching the TUI; on failure, fall back to the "
            "default session and report the bounded local reason"
        ),
    )
    load_group.add_argument(
        "--no-load-session",
        dest="load_session",
        action="store_false",
        default=False,
        help=(
            "explicit opposite of --load-session; useful when --session-db "
            "is configured but the operator does not want to load on this "
            "launch (default when --session-db is supplied alone)"
        ),
    )
    # Phase 3.10a short-circuit ops flags. These are mutually exclusive
    # at argparse time and short-circuit BEFORE LLM runtime resolution
    # and curses initialization (drives I-OPSHARDEN-09 / I-OPSHARDEN-14).
    ops_group = parser.add_mutually_exclusive_group()
    ops_group.add_argument(
        "--db-status",
        action="store_true",
        default=False,
        help=(
            "Phase 3.10a: print a bounded read-only status report for "
            "--session-db and exit. Requires --session-db. Does not "
            "load curses."
        ),
    )
    ops_group.add_argument(
        "--db-verify",
        action="store_true",
        default=False,
        help=(
            "Phase 3.10a: run db_verify against --session-db and exit "
            "with 0 (PASS) or 1 (FAIL). Requires --session-db. Does "
            "not load curses."
        ),
    )
    ops_group.add_argument(
        "--db-backup",
        dest="db_backup",
        default=None,
        help=(
            "Phase 3.10a: copy --session-db to the given destination "
            "via the sqlite3 backup API and exit. Requires --session-db. "
            "Refuses to overwrite an existing destination unless "
            "--db-backup-force is also supplied."
        ),
    )
    parser.add_argument(
        "--db-backup-force",
        action="store_true",
        default=False,
        help=(
            "Phase 3.10a: permit --db-backup to overwrite an existing "
            "destination file."
        ),
    )
    return parser


# ---------------------------------------------------------------------------
# Main entrypoint.
# ---------------------------------------------------------------------------


def main(
    argv: Optional[list[str]] = None,
    *,
    stdin: Optional[TextIO] = None,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
    env: Optional[dict[str, str]] = None,
) -> int:
    """Run the entrypoint. Returns a process exit code.

    The function accepts injected stdin / stdout / stderr / env stand-ins
    so the smoke fixture can exercise every branch (no terminal,
    ``--print-once``, ``--check-terminal``) without attaching to a real
    terminal. The default values read :data:`sys.stdin` / :data:`sys.stdout`
    / :data:`sys.stderr` / :data:`os.environ`.

    Phase 3.8b: the LLM runtime mode is selected via
    :func:`brain.ui.llm_runtime.parse_llm_runtime_args` and the client
    is built via :func:`brain.ui.llm_runtime.build_llm_client_from_config`
    before ``run_curses`` is invoked (drives I-LLMTOG-09). The
    ``--print-once`` / ``--check-terminal`` branches return before the
    factory is invoked (drives I-LLMTOG-10).
    """
    stdout_ = stdout if stdout is not None else sys.stdout
    stderr_ = stderr if stderr is not None else sys.stderr

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.check_terminal:
        check = detect_terminal(stdin=stdin, stdout=stdout_, env=env)
        print(
            f"usable={check.usable}, reason={check.reason}",
            file=stdout_,
        )
        return 0 if check.usable else 1

    if args.print_once:
        # --print-once remains independent of the selected LLM mode
        # (I-LLMTOG-10): we render without constructing any backend.
        session = build_default_session()
        view = build_agent_view_for_session(
            session,
            ComposerState.empty(),
            OperatorTranscript.empty(),
            width=max(int(args.width), 20),
            height=max(int(args.height), 6),
        )
        for row in render_agent(view):
            print(row, file=stdout_)
        return 0

    # Phase 3.10a short-circuit ops flags. These exit BEFORE
    # _resolve_llm_runtime_config and curses initialization (drives
    # I-OPSHARDEN-09). Exit codes follow I-OPSHARDEN-14: 0 on success,
    # 1 on failure.
    if args.db_status or args.db_verify or args.db_backup is not None:
        return _dispatch_ops_short_circuit(args, stdout=stdout_, stderr=stderr_)

    check = detect_terminal(stdin=stdin, stdout=stdout_, env=env)
    if not check.usable:
        print(build_no_terminal_message(check), file=stderr_)
        return 1

    # Resolve the LLM runtime config from the parsed args + env. This
    # happens before any session / curses initialization so a missing
    # API key / executable / mock response surfaces locally (ruling D).
    from brain.ui.llm_runtime import (
        LlmRuntimeError,
        build_llm_client_from_config,
        format_startup_mode_line,
    )

    env_ = env if env is not None else dict(os.environ)
    try:
        llm_config = _resolve_llm_runtime_config(argv, env_)
        client = build_llm_client_from_config(llm_config)
    except LlmRuntimeError as exc:
        print(f"brain.ui: llm runtime error: {exc}", file=stderr_)
        return 1

    # Tactile feedback: print the resolved mode line to stdout (ruling F).
    print(format_startup_mode_line(llm_config), file=stdout_)

    # Usable terminal: import the curses wrapper lazily and hand off.
    # The wrapper is responsible for the actual screen lifecycle; we
    # only construct the default session and the selected client and
    # pass them through.
    #
    # The ``percept_factory_builder`` is passed in so the curses wrapper
    # can construct a live :func:`brain.ui.tui.prompt_queue_percept`
    # closure against the real ``stdscr`` once :func:`curses.wrapper`
    # has obtained it. Without this wiring the ``e`` key would map to
    # ``QUEUE_PERCEPT`` but :func:`step_loop` would surface
    # "queue percept: no input prompt configured" because no factory
    # was available — the regression the live-input campaign exists to
    # patch. Passing the builder (not a pre-built factory) keeps the
    # window reference scoped to the body of :func:`curses.wrapper`,
    # matching the existing ``run_curses`` lifecycle.
    from brain.ui.tui import make_curses_percept_factory, run_curses

    session_db_path = (
        pathlib.Path(args.session_db) if args.session_db is not None else None
    )
    if args.load_session and session_db_path is None:
        print(
            "brain.ui: --load-session requires --session-db",
            file=stderr_,
        )
        return 1

    session = build_default_session()

    if session_db_path is not None:
        # Attach a SessionStoreConfig so /save-session and /load-session
        # can be dispatched from inside the TUI without command-line
        # round-trips.
        from brain.ui.persistence import (  # noqa: PLC0415
            PersistenceError,
            SessionStoreConfig,
            load_session as _load_session,
        )
        try:
            config = SessionStoreConfig(db_path=session_db_path)
        except (TypeError, ValueError) as exc:
            print(
                f"brain.ui: invalid --session-db: {exc}",
                file=stderr_,
            )
            return 1
        session.session_store_config = config
        if args.load_session:
            try:
                loaded, result = _load_session(config)
            except PersistenceError as exc:
                print(
                    f"brain.ui: session db = {session_db_path!s} "
                    f"(load failed: {exc}; using default session)",
                    file=stdout_,
                )
            else:
                # The candidate already carries the config; reuse it.
                session = loaded
                print(
                    f"brain.ui: session db = {session_db_path!s} "
                    f"(loaded; schema=v{result.schema_version}; "
                    f"catalog={result.catalog_version}; "
                    f"chunks={result.loaded_chunks}; "
                    f"candidates={result.loaded_candidates})",
                    file=stdout_,
                )
        else:
            print(
                f"brain.ui: session db = {session_db_path!s} "
                f"(load skipped; use /load-session to load)",
                file=stdout_,
            )
    else:
        print(
            "brain.ui: session db = not configured",
            file=stdout_,
        )

    try:
        run_curses(
            session,
            client=client,
            percept_factory_builder=make_curses_percept_factory,
        )
    except KeyboardInterrupt:
        # A clean Ctrl-C exit is a documented quit path.
        return 0
    return 0


def _dispatch_ops_short_circuit(
    args: argparse.Namespace,
    *,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Short-circuit dispatcher for the Phase 3.10a ``--db-*`` flags.

    Drives ``I-OPSHARDEN-09`` (short-circuit ordering / mutual
    exclusion) and ``I-OPSHARDEN-14`` (exit-code mapping). Argparse has
    already enforced mutual exclusion via the ``ops_group`` group; this
    helper picks the active flag, runs the operation, prints a bounded
    one-line summary to stdout, and returns the exit code.
    """
    if args.session_db is None:
        print(
            "brain.ui: --db-status / --db-verify / --db-backup require "
            "--session-db",
            file=stderr,
        )
        return 1

    session_db_path = pathlib.Path(args.session_db)
    from brain.ui.persistence import (  # noqa: PLC0415
        PersistenceError,
        SessionStoreConfig,
    )
    try:
        config = SessionStoreConfig(db_path=session_db_path)
    except (TypeError, ValueError) as exc:
        print(f"brain.ui: invalid --session-db: {exc}", file=stderr)
        return 1

    from brain.ui.persistence_ops import (  # noqa: PLC0415
        db_backup,
        db_status,
        db_verify,
    )

    if args.db_status:
        try:
            status_report = db_status(config)
        except PersistenceError as exc:
            print(f"brain.ui: db-status error: {exc}", file=stderr)
            return 1
        print(
            "brain.ui: db-status = "
            + ("ok" if status_report.db_exists and not status_report.error_text else "fail")
            + f" (path={status_report.db_path_str!r}; "
            f"exists={status_report.db_exists}; "
            f"schema=v{status_report.schema_version}; "
            f"catalog={status_report.catalog_version!r}; "
            f"bytes={status_report.db_byte_size})",
            file=stdout,
        )
        if not status_report.db_exists or status_report.error_text:
            return 1
        return 0

    if args.db_verify:
        try:
            verify_report = db_verify(config)
        except PersistenceError as exc:
            print(f"brain.ui: db-verify error: {exc}", file=stderr)
            return 1
        print(
            "brain.ui: db-verify = "
            + ("pass" if verify_report.passed else "fail")
            + f" (path={verify_report.db_path_str!r}; "
            f"schema=v{verify_report.schema_version}; "
            f"chunks={verify_report.loaded_chunks}; "
            f"candidates={verify_report.loaded_candidates}; "
            f"error={verify_report.error_text!r})",
            file=stdout,
        )
        return 0 if verify_report.passed else 1

    if args.db_backup is not None:
        dest_path = pathlib.Path(args.db_backup)
        try:
            backup_report = db_backup(
                config, dest_path, force=bool(args.db_backup_force)
            )
        except PersistenceError as exc:
            print(f"brain.ui: db-backup error: {exc}", file=stderr)
            return 1
        print(
            "brain.ui: db-backup = "
            + ("ok" if backup_report.succeeded else "fail")
            + f" (source={backup_report.source_path_str!r}; "
            f"dest={backup_report.dest_path_str!r}; "
            f"pages={backup_report.pages_copied}/{backup_report.total_pages}; "
            f"bytes={backup_report.dest_byte_size}; "
            f"overwritten={backup_report.overwritten}; "
            f"error={backup_report.error_text!r})",
            file=stdout,
        )
        return 0 if backup_report.succeeded else 1

    # Unreachable: caller checks one of the three flags is set.
    return 1


def _resolve_llm_runtime_config(
    argv: Optional[list[str]],
    env: dict[str, str],
) -> "LlmRuntimeConfig":  # type: ignore[name-defined]
    """Wire argv (from sys.argv when None) + env into LlmRuntimeConfig.

    Kept separate from :func:`main` so the I-LLMTOG-09 / I-LLMTOG-10
    fixtures can exercise the resolve path without re-running argparse.
    """
    from brain.ui.llm_runtime import parse_llm_runtime_args

    raw_argv = list(argv) if argv is not None else list(sys.argv[1:])
    return parse_llm_runtime_args(raw_argv, env)


def _render_once_to_string(session: OperatorSession, *, width: int, height: int) -> str:
    """Helper used by the smoke fixture: render one frame to a string.

    Kept separate from :func:`main` so the fixture does not have to
    reconstruct an argparse ``Namespace``. Returns the concatenated
    rendered rows joined by newlines.
    """
    view = build_agent_view_for_session(
        session,
        ComposerState.empty(),
        OperatorTranscript.empty(),
        width=width,
        height=height,
    )
    return "\n".join(render_agent(view))


__all__ = [
    "OfflineStandInClient",
    "TerminalCheck",
    "build_arg_parser",
    "build_default_session",
    "build_no_terminal_message",
    "detect_terminal",
    "main",
]


if __name__ == "__main__":  # pragma: no cover - exercised via `python3 -m brain.ui`
    raise SystemExit(main())
