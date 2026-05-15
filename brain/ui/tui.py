"""Operator TUI curses wrapper.

This module is the thin terminal adapter for the Operator TUI. It contains
only screen initialization / teardown, key reading, key-to-:class:`Command`
translation, painting of pre-rendered display rows, resize re-rendering,
and clean quit. All cognitive / mutation work is delegated to
:class:`brain.ui.session.OperatorSession`; all display formatting is
delegated to :func:`brain.ui.render.render`.

Catalog rows driven from here:

* ``I-UI-11`` (STRUCTURAL) — the curses wrapper imports no module from
  ``brain.tlica`` or ``brain.llm``, calls no kernel mutation function
  directly, evaluates no arbitrary Python, and performs no file or
  network I/O. The static AST audit in :mod:`brain.ui.fixtures.tui_smoke`
  enforces this property; this module is written to satisfy the audit
  surface listed in ``OPERATOR_TUI_CATALOG_PATCH_PLAN.md`` Section 8.

The wrapper is **optional**: the keyboard map, the input loop, the paint
helper, and the lifecycle hooks are all importable and unit-testable
without attaching to a real terminal. :func:`run_curses` is the only
function that actually opens :mod:`curses`; the campaign's non-interactive
smoke test exercises :func:`translate_key`, :func:`paint_rows`,
:func:`step_loop`, and :func:`KEYMAP` directly.

This module imports only the Python standard library plus the local
:mod:`brain.ui.commands` / :mod:`brain.ui.render` / :mod:`brain.ui.session`
/ :mod:`brain.ui.snapshot` surfaces. It does **not** import
``brain.tick``, ``brain.tlica``, ``brain.llm``, ``subprocess``,
``socket``, ``urllib``, ``http``, or ``requests``.
"""
from __future__ import annotations

import curses
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Optional

from brain.ui.commands import (
    Command,
    OperatorCommand,
    make_command,
)
from brain.ui.render import (
    DEFAULT_HEIGHT,
    DEFAULT_KEYBOARD_HELP,
    DEFAULT_WIDTH,
    MIN_HEIGHT,
    MIN_WIDTH,
    TuiViewModel,
    build_view_model,
    render,
)
from brain.ui.session import OperatorSession
from brain.ui.snapshot import (
    build_brain_snapshot,
    build_development_snapshot,
)

if TYPE_CHECKING:  # pragma: no cover - typing-only imports
    from brain.llm.client import LLMClient


# ---------------------------------------------------------------------------
# Keyboard map — finite enumeration, matches DEFAULT_KEYBOARD_HELP.
# ---------------------------------------------------------------------------


#: Mapping from keystroke (single printable character or the literal
#: string ``"space"`` / ``"?"``) to the :class:`OperatorCommand` kind the
#: wrapper dispatches. Drives ``I-UI-11`` (terminal-only translation) and
#: matches the help-pane enumeration declared by
#: :data:`brain.ui.render.DEFAULT_KEYBOARD_HELP`.
KEYMAP: dict[str, OperatorCommand] = {
    "s": OperatorCommand.INSPECT_STATE,
    "t": OperatorCommand.INSPECT_TICK,
    "o": OperatorCommand.INSPECT_OUTPUT,
    "w": OperatorCommand.INSPECT_WORLDLET,
    "r": OperatorCommand.INSPECT_REPL,
    "p": OperatorCommand.INSPECT_STATE,  # alias: peek the active view
    "e": OperatorCommand.QUEUE_PERCEPT,
    " ": OperatorCommand.STEP_TICK,
    "space": OperatorCommand.STEP_TICK,
    "c": OperatorCommand.CLEAR_STATUS,
    "?": OperatorCommand.HELP,
    "h": OperatorCommand.HELP,
    "q": OperatorCommand.QUIT,
}


# ---------------------------------------------------------------------------
# Pure, terminal-agnostic helpers
# ---------------------------------------------------------------------------


def translate_key(keystroke: str) -> Optional[OperatorCommand]:
    """Translate a single keystroke to an :class:`OperatorCommand`.

    Returns ``None`` when the keystroke is not in :data:`KEYMAP`; the
    caller should treat that as a no-op (and may surface a local UI
    status message). The translator never raises on unknown input —
    that would let a stray keypress crash the wrapper.
    """
    if not isinstance(keystroke, str):
        return None
    if keystroke == "":
        return None
    return KEYMAP.get(keystroke)


def build_view_for_session(
    session: OperatorSession,
    *,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> TuiViewModel:
    """Build a :class:`TuiViewModel` from the live :class:`OperatorSession`.

    Uses the read-only snapshot helpers (:func:`build_brain_snapshot` and
    :func:`build_development_snapshot`) so no kernel container is mutated
    during view construction. The supplied ``width`` and ``height`` are
    clamped to the renderer's bounds.
    """
    if not isinstance(session, OperatorSession):
        raise TypeError(
            "build_view_for_session requires an OperatorSession "
            f"(got {type(session).__name__})"
        )
    width = max(int(width), MIN_WIDTH)
    height = max(int(height), MIN_HEIGHT)
    brain = build_brain_snapshot(session.state, latest_tick=session.latest_tick)
    development = build_development_snapshot(
        output_history=session.output_history,
        worldlet_history=session.worldlet_history,
        repl_history=session.repl_history,
    )
    return build_view_model(
        active_view=session.active_view,
        brain=brain,
        development=development,
        width=width,
        height=height,
        queued_event_summary=session.queued_event_summary(),
        status_message=session.status_message,
        error_message=session.error_message,
        keyboard_help=DEFAULT_KEYBOARD_HELP,
    )


# ---------------------------------------------------------------------------
# Paint helper — operates on any "addnstr-like" surface for testability.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PaintCall:
    """A single recorded paint instruction.

    The non-interactive smoke test substitutes a recorder for the curses
    window and asserts the wrapper emitted bounded, printable rows in the
    expected order. ``PaintCall`` is intentionally a frozen dataclass so a
    captured paint trace cannot be mutated after the fact.
    """

    row: int
    col: int
    text: str
    width: int


class PaintRecorder:
    """Test double for a curses window's ``addnstr`` / ``clear`` surface.

    Records every paint call without touching any real terminal. The
    smoke test uses this to assert :func:`paint_rows` emits exactly the
    rows :func:`render` produces, in order, bounded by the supplied
    width, with no curses-attribute side effects.
    """

    def __init__(self) -> None:
        self.calls: list[PaintCall] = []
        self.cleared: int = 0
        self.refreshed: int = 0

    # The curses Window methods we mimic. Their signatures match the
    # subset we actually use from within paint_rows.

    def clear(self) -> None:
        self.cleared += 1

    def addnstr(self, row: int, col: int, text: str, n: int) -> None:
        if not isinstance(text, str):
            raise TypeError(
                f"PaintRecorder.addnstr text must be str (got {type(text).__name__})"
            )
        if n < 0:
            raise ValueError("PaintRecorder.addnstr n must be non-negative")
        # The pure renderer already truncates; we still bound here to
        # mirror curses' semantics so the recorder catches over-runs.
        bounded = text[:n]
        self.calls.append(PaintCall(row=row, col=col, text=bounded, width=n))

    def refresh(self) -> None:
        self.refreshed += 1

    def getmaxyx(self) -> tuple[int, int]:
        # Default test geometry. Tests that want a different size can
        # subclass and override this method.
        return (DEFAULT_HEIGHT, DEFAULT_WIDTH)


def paint_rows(
    window: object,
    rows: tuple[str, ...],
    *,
    width: int,
    height: int,
) -> None:
    """Paint the rendered rows onto a curses-like window.

    The window only needs three methods: ``clear()``, ``addnstr(row, col,
    text, n)``, and ``refresh()``. This subset is also implemented by
    :class:`PaintRecorder` so the wrapper can be exercised without
    attaching to a real terminal (drives the non-interactive surface of
    ``I-UI-12``).
    """
    if not hasattr(window, "addnstr") or not hasattr(window, "clear"):
        raise TypeError(
            "paint_rows requires a curses-like window with clear() and addnstr()"
        )
    window.clear()  # type: ignore[attr-defined]
    bounded_height = min(len(rows), max(int(height), MIN_HEIGHT))
    bounded_width = max(int(width), MIN_WIDTH)
    for row_index in range(bounded_height):
        text = rows[row_index]
        # Defence in depth: the renderer already bounds rows to ``width``
        # and guarantees printability, but a buggy upstream component
        # could feed a non-string; reject it locally so curses never sees
        # something unprintable.
        if not isinstance(text, str):
            raise TypeError(
                "paint_rows row must be str "
                f"(got {type(text).__name__} at index {row_index})"
            )
        window.addnstr(row_index, 0, text, bounded_width)  # type: ignore[attr-defined]
    if hasattr(window, "refresh"):
        window.refresh()  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Step loop — testable, terminal-agnostic dispatch of a single keystroke.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StepOutcome:
    """Result of a single :func:`step_loop` iteration.

    Fields:

    * ``command`` — the resolved :class:`OperatorCommand` (``None`` when
      the keystroke was not in :data:`KEYMAP`).
    * ``dispatched`` — ``True`` when a :class:`Command` was actually
      dispatched into the :class:`OperatorSession`.
    * ``rows`` — the rendered rows after the (possibly no-op) step.
    """

    command: Optional[OperatorCommand]
    dispatched: bool
    rows: tuple[str, ...]


def step_loop(
    session: OperatorSession,
    keystroke: str,
    *,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    client: Optional["LLMClient"] = None,
    percept_factory: Optional[Callable[[OperatorSession], Command]] = None,
) -> StepOutcome:
    """Translate one keystroke, dispatch, and render the next view.

    The function is total: unknown keystrokes return a :class:`StepOutcome`
    with ``command=None`` and ``dispatched=False``; the session is left
    untouched in that branch. ``percept_factory`` is invoked only when the
    user issues :data:`OperatorCommand.QUEUE_PERCEPT` — the factory is the
    integration seam for a curses-managed input prompt (or a test
    stand-in). The factory must return a fully-validated :class:`Command`;
    a ``ValueError`` / ``TypeError`` from it is captured as a local UI
    error instead of propagating (``I-UI-06``).
    """
    if not isinstance(session, OperatorSession):
        raise TypeError(
            "step_loop requires an OperatorSession "
            f"(got {type(session).__name__})"
        )
    kind = translate_key(keystroke)
    dispatched = False
    if kind is None:
        # Unknown keystroke: surface a local UI status only.
        session.set_status(f"unknown key: {keystroke!r}")
    elif kind is OperatorCommand.QUEUE_PERCEPT:
        if percept_factory is None:
            session.set_error("queue percept: no input prompt configured")
        else:
            try:
                cmd = percept_factory(session)
            except (TypeError, ValueError) as exc:
                session.set_error(f"queue percept rejected: {exc}")
            else:
                if not isinstance(cmd, Command) or cmd.kind is not OperatorCommand.QUEUE_PERCEPT:
                    session.set_error(
                        "queue percept factory did not return a QUEUE_PERCEPT Command"
                    )
                else:
                    session.dispatch(cmd, client=client)
                    dispatched = True
    elif kind is OperatorCommand.STEP_TICK:
        session.dispatch(make_command(OperatorCommand.STEP_TICK), client=client)
        dispatched = True
    else:
        session.dispatch(make_command(kind))
        dispatched = True

    view = build_view_for_session(session, width=width, height=height)
    rows = render(view)
    return StepOutcome(command=kind, dispatched=dispatched, rows=rows)


# ---------------------------------------------------------------------------
# Lifecycle — the only curses-touching surface in this module.
# ---------------------------------------------------------------------------


def _read_keystroke(stdscr: object) -> str:
    """Translate a curses ``getch()`` to the wrapper's keystroke alphabet.

    Returns the printable character for ASCII keys, the literal string
    ``"space"`` for the spacebar (consistent with
    :data:`brain.ui.render.DEFAULT_KEYBOARD_HELP`), and the empty string
    for keys outside the supported set. The translator never raises.
    """
    if not hasattr(stdscr, "getch"):
        raise TypeError(
            "_read_keystroke requires a curses window (got "
            f"{type(stdscr).__name__})"
        )
    code: int = stdscr.getch()  # type: ignore[attr-defined]
    if code == -1:
        return ""
    if code == ord(" "):
        return " "
    if 32 <= code < 127:
        return chr(code)
    # Resize / function-key codes are intentionally treated as no-op for
    # this campaign; the next paint cycle picks up the new geometry.
    return ""


def run_curses(
    session: OperatorSession,
    *,
    client: Optional["LLMClient"] = None,
    percept_factory: Optional[Callable[[OperatorSession], Command]] = None,
) -> None:
    """Open a curses screen and run the operator session until ``QUIT``.

    This is the only function in this module that actually touches
    :mod:`curses`. It delegates every other concern (state, snapshots,
    rendering, key translation, dispatch) to the helpers above so the
    non-interactive smoke test can exercise the full surface without
    attaching to a real terminal.

    The caller supplies the :class:`OperatorSession` and (optionally) the
    LLM client used for ``STEP_TICK`` dispatches. The wrapper never
    constructs an LLM client itself; that decision belongs to the
    entrypoint (:mod:`brain.ui.__main__`).
    """
    if not isinstance(session, OperatorSession):
        raise TypeError(
            "run_curses requires an OperatorSession "
            f"(got {type(session).__name__})"
        )

    def _body(stdscr: object) -> None:
        # Hide the cursor; non-blocking input is not required because the
        # operator drives the loop one keystroke at a time.
        try:
            curses.curs_set(0)
        except curses.error:
            # Some terminals reject curs_set; non-fatal.
            pass
        while not session.quit_flag:
            height, width = stdscr.getmaxyx()  # type: ignore[attr-defined]
            view = build_view_for_session(
                session,
                width=max(int(width), MIN_WIDTH),
                height=max(int(height), MIN_HEIGHT),
            )
            rows = render(view)
            paint_rows(
                stdscr,
                rows,
                width=max(int(width), MIN_WIDTH),
                height=max(int(height), MIN_HEIGHT),
            )
            keystroke = _read_keystroke(stdscr)
            if keystroke == "":
                # No mapped keystroke; loop and repaint.
                continue
            step_loop(
                session,
                keystroke,
                width=max(int(width), MIN_WIDTH),
                height=max(int(height), MIN_HEIGHT),
                client=client,
                percept_factory=percept_factory,
            )

    curses.wrapper(_body)


__all__ = [
    "KEYMAP",
    "PaintCall",
    "PaintRecorder",
    "StepOutcome",
    "build_view_for_session",
    "paint_rows",
    "run_curses",
    "step_loop",
    "translate_key",
]
