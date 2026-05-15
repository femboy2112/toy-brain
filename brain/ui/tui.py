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
    ContentState,
    OperatorCommand,
    QueuePerceptPayload,
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
# Interactive percept input prompt — testable curses prompt.
# ---------------------------------------------------------------------------


#: Maximum number of characters accepted at the curses prompt for a single
#: input field. Mirrors the bounded-text policy in
#: :mod:`brain.ui.session` (``MAX_STATUS_TEXT_LEN``) for the field-level
#: read budget. Two reads — one for ``content_id`` and one for ``text`` —
#: are the only blocking input calls inside :func:`prompt_queue_percept`.
PROMPT_MAX_INPUT_LEN = 64


#: Safe default :class:`ContentState` value used by
#: :func:`prompt_queue_percept` when the operator does not need to control
#: the TOCE classification at prompt time. ``CONSCIOUS_CLEAR`` is the
#: simplest classification (available + verification_path), matches the
#: existing :mod:`brain.ui.fixtures.tui_smoke` ``_good_percept`` shape,
#: and is the same default used by the bottom-up tick fixture.
PROMPT_DEFAULT_CONTENT_STATE: ContentState = ContentState(
    available=True,
    verification_path=True,
    retrievable=True,
    operative=True,
)


#: Safe default ``initial_rho`` for prompt-built percepts. Encoded as a
#: string so :mod:`brain.ui.tui` does not need to import :mod:`fractions`
#: (the I-UI-11 audit restricts the import roots of this file). The
#: :class:`QueuePerceptPayload` constructor normalizes the string through
#: :func:`brain.tlica.builders.rho` exactly as :class:`PerceptEvent`
#: would.
PROMPT_DEFAULT_RHO: str = "1/2"


def _decode_getstr(raw: object) -> str:
    """Normalize a curses ``getstr`` return value into a :class:`str`.

    Curses' real ``getstr`` returns :class:`bytes`; the in-process test
    fake (see :class:`brain.ui.fixtures.tui_smoke._FakeStdscr`) may return
    a :class:`str` directly. Both shapes are accepted and decoded into a
    stripped Unicode string. Anything else raises ``ValueError`` so the
    surrounding :func:`prompt_queue_percept` failure path can route the
    error through ``step_loop``'s local UI status channel.
    """
    if isinstance(raw, bytes):
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"prompt input was not valid UTF-8: {exc}"
            ) from exc
    elif isinstance(raw, str):
        decoded = raw
    else:
        raise ValueError(
            "prompt input must be bytes or str "
            f"(got {type(raw).__name__})"
        )
    return decoded.strip()


def _prompt_read_field(
    stdscr: object,
    label: str,
    row: int,
    *,
    width: int,
) -> str:
    """Paint a prompt label and read one bounded field from ``stdscr``.

    The window only needs to expose ``addnstr(y, x, text, n)`` and
    ``getstr(y, x, n)``; both are subset members of the real curses
    ``Window`` class and are also implemented by the smoke fixture's fake
    window. Reads are bounded by :data:`PROMPT_MAX_INPUT_LEN` so an
    over-long paste cannot blow past the field budget.
    """
    if not isinstance(label, str) or not label:
        raise TypeError("_prompt_read_field requires a non-empty str label")
    if not isinstance(row, int) or row < 0:
        raise ValueError(
            f"_prompt_read_field row must be a non-negative int (got {row!r})"
        )
    bounded_width = max(int(width), MIN_WIDTH)
    addnstr = getattr(stdscr, "addnstr", None)
    getstr = getattr(stdscr, "getstr", None)
    if not callable(addnstr) or not callable(getstr):
        raise TypeError(
            "_prompt_read_field requires a curses-like window with "
            "addnstr() and getstr()"
        )
    # Paint the label at the requested row, column 0. The label is bounded
    # by the supplied width so it never overruns the prompt pane.
    addnstr(row, 0, label, bounded_width)
    # Read at the next row so the user types below the label rather than
    # over it; curses will echo into the same line if echo() is enabled.
    raw = getstr(row + 1, 0, PROMPT_MAX_INPUT_LEN)
    return _decode_getstr(raw)


def prompt_queue_percept(
    stdscr: object,
    session: OperatorSession,
    *,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> Command:
    """Read a bounded percept from the curses screen and build a
    ``QUEUE_PERCEPT`` :class:`Command`.

    The helper paints a small prompt area (two label / input rows for
    ``content_id`` and ``text``) on the supplied curses-like window,
    collects the operator's input through ``getstr``, and builds a
    :class:`Command` whose payload is a fully-validated
    :class:`QueuePerceptPayload`. Every cognitive contract is enforced by
    the existing public constructors:

    * :class:`QueuePerceptPayload.__post_init__` runs the public
      :class:`PerceptEvent` constructor on the supplied fields, so
      ``COGITO_ID`` collisions, non-printable text, and out-of-range
      ``initial_rho`` raise :class:`ValueError` / :class:`TypeError`
      before the payload record is fully built (drives ``I-UI-04``).
    * :class:`Command.__post_init__` re-checks that the kind is
      :data:`OperatorCommand.QUEUE_PERCEPT` and that the payload is a
      :class:`QueuePerceptPayload` (drives ``I-UI-03``).

    Failure modes:

    * Any input that the public constructors reject surfaces as a
      :class:`ValueError` raised by this helper. The surrounding
      :func:`step_loop` catches ``TypeError`` / ``ValueError`` from the
      ``percept_factory`` and converts it to a local UI error message
      (``I-UI-06``) — the operator session is not mutated.
    * The helper never calls :func:`brain.tick.tick`, never writes a
      file, scenario, trace, history, or catalog row, and never mutates
      the :class:`OperatorSession` directly.
    """
    if not isinstance(session, OperatorSession):
        raise TypeError(
            "prompt_queue_percept requires an OperatorSession "
            f"(got {type(session).__name__})"
        )
    if stdscr is None:
        raise TypeError("prompt_queue_percept requires a curses-like window")
    # The window must expose at minimum addnstr / getstr / clear / refresh.
    # Reject anything else up front so we do not partially repaint the
    # screen before discovering the window is unusable.
    for required in ("addnstr", "getstr", "clear", "refresh"):
        if not callable(getattr(stdscr, required, None)):
            raise TypeError(
                "prompt_queue_percept window missing required curses "
                f"method {required!r}"
            )

    bounded_width = max(int(width), MIN_WIDTH)
    bounded_height = max(int(height), MIN_HEIGHT)
    # Best-effort: enable echo + visible cursor so the operator can see
    # what they type. These are module-level curses helpers; if the
    # window backend (or the test fake) does not support them we ignore
    # the failure and continue — the prompt still works without echo.
    try:
        curses.echo()
    except (curses.error, AttributeError):
        pass
    try:
        curses.curs_set(1)
    except (curses.error, AttributeError):
        pass

    try:
        stdscr.clear()  # type: ignore[attr-defined]
        # Header line so the operator knows what just opened. ``addnstr``
        # is bounded by the supplied width to satisfy I-UI-13's bounded
        # printable text policy.
        header = "[ queue percept ] content_id then text; empty cancels"
        stdscr.addnstr(0, 0, header[:bounded_width], bounded_width)  # type: ignore[attr-defined]
        # Two field reads. ``_prompt_read_field`` paints the label at the
        # supplied row and reads input at row + 1.
        content_id = _prompt_read_field(
            stdscr, "content_id:", 2, width=bounded_width
        )
        text = _prompt_read_field(
            stdscr, "text:", 5, width=bounded_width
        )
    finally:
        # Restore the no-echo / hidden-cursor state the wrapper expects.
        try:
            curses.noecho()
        except (curses.error, AttributeError):
            pass
        try:
            curses.curs_set(0)
        except (curses.error, AttributeError):
            pass

    if not content_id:
        # Empty content_id is the cancel path: surface a clean local error
        # via the step_loop / percept_factory boundary so no session state
        # is mutated.
        raise ValueError("prompt cancelled (empty content_id)")
    if not text:
        raise ValueError("prompt cancelled (empty text)")

    # The two public constructors below are the only points where this
    # helper interacts with kernel-validation: QueuePerceptPayload runs
    # PerceptEvent under the hood (I-UI-04) and Command rejects any kind
    # / payload mismatch (I-UI-03). Both raise without touching the
    # OperatorSession.
    payload = QueuePerceptPayload(
        content_id=content_id,
        text=text,
        content_state=PROMPT_DEFAULT_CONTENT_STATE,
        initial_rho=PROMPT_DEFAULT_RHO,  # type: ignore[arg-type]
    )
    return Command(kind=OperatorCommand.QUEUE_PERCEPT, payload=payload)


def make_curses_percept_factory(
    stdscr: object,
    *,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> Callable[[OperatorSession], Command]:
    """Return a :func:`step_loop`-compatible ``percept_factory`` that drives
    :func:`prompt_queue_percept` against the supplied curses window.

    The returned closure captures only the window reference plus the
    bounded geometry; it carries no kernel state, LLM client, or other
    resource. Step 2 of the campaign wires this into the :func:`run_curses`
    body so the live entrypoint can prompt for percepts without the
    operator needing to construct a :class:`Command` by hand.
    """
    if stdscr is None:
        raise TypeError("make_curses_percept_factory requires a curses window")
    bounded_width = max(int(width), MIN_WIDTH)
    bounded_height = max(int(height), MIN_HEIGHT)

    def _factory(session: OperatorSession) -> Command:
        return prompt_queue_percept(
            stdscr,
            session,
            width=bounded_width,
            height=bounded_height,
        )

    return _factory


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
    percept_factory_builder: Optional[
        Callable[..., Callable[[OperatorSession], Command]]
    ] = None,
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

    There are two ways to supply a ``QUEUE_PERCEPT`` factory:

    * ``percept_factory`` — a pre-built callable. Useful when the caller
      already owns a curses window stand-in (for tests). The wrapper
      passes this object straight through to :func:`step_loop`.
    * ``percept_factory_builder`` — a callable that is handed the live
      ``stdscr`` (plus the current ``(width, height)`` geometry) inside
      :func:`curses.wrapper` and returns the per-iteration factory. This
      is the path the live entrypoint uses, because the curses window
      does not exist until :func:`curses.wrapper` runs.

    If neither is supplied, the wrapper defaults to
    :func:`make_curses_percept_factory` against the live ``stdscr`` so the
    live entrypoint always has a working interactive prompt without
    re-importing or re-wiring the helper at every call site.

    Passing both ``percept_factory`` and ``percept_factory_builder`` is a
    configuration error: the wrapper accepts only one factory source per
    invocation.
    """
    if not isinstance(session, OperatorSession):
        raise TypeError(
            "run_curses requires an OperatorSession "
            f"(got {type(session).__name__})"
        )
    if percept_factory is not None and percept_factory_builder is not None:
        raise TypeError(
            "run_curses accepts at most one of percept_factory / "
            "percept_factory_builder, not both"
        )
    if percept_factory is not None and not callable(percept_factory):
        raise TypeError(
            "run_curses percept_factory must be callable "
            f"(got {type(percept_factory).__name__})"
        )
    if percept_factory_builder is not None and not callable(percept_factory_builder):
        raise TypeError(
            "run_curses percept_factory_builder must be callable "
            f"(got {type(percept_factory_builder).__name__})"
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
            bounded_width = max(int(width), MIN_WIDTH)
            bounded_height = max(int(height), MIN_HEIGHT)
            view = build_view_for_session(
                session,
                width=bounded_width,
                height=bounded_height,
            )
            rows = render(view)
            paint_rows(
                stdscr,
                rows,
                width=bounded_width,
                height=bounded_height,
            )
            keystroke = _read_keystroke(stdscr)
            if keystroke == "":
                # No mapped keystroke; loop and repaint.
                continue
            # Resolve the effective percept factory for this iteration.
            # When the caller supplied a pre-built ``percept_factory`` it is
            # passed straight through. Otherwise the builder (defaulting to
            # :func:`make_curses_percept_factory`) is called with the live
            # ``stdscr`` so the QUEUE_PERCEPT prompt can read from the
            # active terminal. The builder is invoked per iteration so a
            # terminal resize is picked up by the next prompt.
            if percept_factory is not None:
                effective_factory = percept_factory
            else:
                builder = (
                    percept_factory_builder
                    if percept_factory_builder is not None
                    else make_curses_percept_factory
                )
                # The builder is invoked with keyword geometry so a
                # builder written against :func:`make_curses_percept_factory`
                # (which declares ``width`` / ``height`` keyword-only) and
                # a more permissive ``Callable`` shape both work.
                effective_factory = builder(
                    stdscr, width=bounded_width, height=bounded_height
                )
            step_loop(
                session,
                keystroke,
                width=bounded_width,
                height=bounded_height,
                client=client,
                percept_factory=effective_factory,
            )

    curses.wrapper(_body)


__all__ = [
    "KEYMAP",
    "PROMPT_DEFAULT_CONTENT_STATE",
    "PROMPT_DEFAULT_RHO",
    "PROMPT_MAX_INPUT_LEN",
    "PaintCall",
    "PaintRecorder",
    "StepOutcome",
    "build_view_for_session",
    "make_curses_percept_factory",
    "paint_rows",
    "prompt_queue_percept",
    "run_curses",
    "step_loop",
    "translate_key",
]
