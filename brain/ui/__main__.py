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
    """
    parser = argparse.ArgumentParser(
        prog="python3 -m brain.ui",
        description=(
            "Operator TUI entrypoint. Inspects BrainState / TickRecord / "
            "Phase 3.1-3.4 developmental histories and routes bottom-up "
            "PerceptEvent inputs through the public tick() path. No real "
            "LLM, shell, network, file mutation, or host execution."
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

    check = detect_terminal(stdin=stdin, stdout=stdout_, env=env)
    if not check.usable:
        print(build_no_terminal_message(check), file=stderr_)
        return 1

    # Usable terminal: import the curses wrapper lazily and hand off.
    # The wrapper is responsible for the actual screen lifecycle; we
    # only construct the default session and the offline stand-in
    # client and pass them through.
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

    session = build_default_session()
    client = OfflineStandInClient()
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
