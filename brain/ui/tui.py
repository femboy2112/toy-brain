"""Operator TUI curses wrapper.

This module is the thin terminal adapter for the Operator TUI. It contains
only screen initialization / teardown, key reading, key-to-:class:`Command`
translation, painting of pre-rendered display rows, resize re-rendering,
and clean quit. All cognitive / mutation work is delegated to
:class:`brain.ui.session.OperatorSession`; all display formatting is
delegated to :func:`brain.ui.render.render` (legacy single-pane path) and
:func:`brain.ui.render.render_agent` (agent-style layout path).

Catalog rows driven from here:

* ``I-UI-11`` (STRUCTURAL) — the curses wrapper imports no module from
  ``brain.tlica`` or ``brain.llm``, calls no kernel mutation function
  directly, evaluates no arbitrary Python, and performs no file or
  network I/O.
* ``I-UI-21`` (STRUCTURAL) — the curses wrapper delegates input to the
  bottom composer / typed-command parser / :class:`OperatorSession`
  router and never mutates kernel state directly. The agent-style
  delegation table built by :func:`build_agent_keystroke_router` is the
  fixture-audited surface that backs this property.

The wrapper is **optional**: the keyboard map, the input loop, the paint
helper, and the lifecycle hooks are all importable and unit-testable
without attaching to a real terminal. :func:`run_curses` is the only
function that actually opens :mod:`curses`; the campaign's non-interactive
smoke fixtures exercise the agent-style path through
:func:`step_agent_loop` and :func:`build_agent_keystroke_router` directly.

This module imports only the Python standard library plus the local
:mod:`brain.ui.commands` / :mod:`brain.ui.command_line` /
:mod:`brain.ui.composer` / :mod:`brain.ui.layout` / :mod:`brain.ui.render`
/ :mod:`brain.ui.session` / :mod:`brain.ui.snapshot` /
:mod:`brain.ui.transcript` surfaces. It does **not** import
``brain.tick``, ``brain.tlica``, ``brain.llm``, ``subprocess``,
``socket``, ``urllib``, ``http``, or ``requests``.

Per ``OPERATOR_TUI_AGENT_LAYOUT_CORRIGENDA.md`` ruling E, the legacy
single-pane :class:`brain.ui.render.TuiViewModel` is no longer the
runtime surface of this wrapper: :func:`run_curses` builds an
:class:`brain.ui.layout.AgentTuiViewModel` and renders it through
:func:`brain.ui.render.render_agent`. The legacy
:class:`~brain.ui.render.TuiViewModel` and :func:`brain.ui.render.render`
remain importable for the legacy ``--print-once`` path and for the
``brain.ui.fixtures.snapshot_view`` / ``brain.ui.fixtures.render_view``
fixtures; the wrapper itself does not consume them on the live path.
"""
from __future__ import annotations

import curses
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Optional

from brain.ui.command_line import (
    LOCAL_COMMAND_HELP,
    LocalCommandError,
    LocalCommandLine,
)
from brain.ui.commands import (
    Command,
    ContentState,
    OperatorCommand,
    QueuePerceptPayload,
    make_command,
)
from brain.ui.composer import (
    BottomComposer,
    ComposerAction,
    ComposerState,
    ComposerSubmission,
)
from brain.ui.layout import (
    AgentLayout,
    AgentTuiViewModel,
    ComposerSnapshot,
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
    render_agent,
)
from brain.ui.session import OperatorSession
from brain.ui.snapshot import (
    build_brain_snapshot,
    build_development_snapshot,
)
from brain.ui.transcript import (
    OperatorTranscript,
    TranscriptKind,
)

if TYPE_CHECKING:  # pragma: no cover - typing-only imports
    from brain.llm.client import LLMClient


# ---------------------------------------------------------------------------
# Keyboard map — finite enumeration, matches DEFAULT_KEYBOARD_HELP.
# ---------------------------------------------------------------------------


#: Mapping from keystroke (single printable character or the literal
#: string ``"space"`` / ``"?"``) to the :class:`OperatorCommand` kind the
#: legacy single-letter wrapper dispatches. The agent-style wrapper uses a
#: derived router (see :func:`build_agent_keystroke_router`) so the
#: composer can intercept characters before they reach the shortcut path.
#: This mapping is retained because :func:`step_loop` and the existing
#: I-UI-11 / I-UI-14 fixtures continue to drive the wrapper through it.
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
    """Build a legacy :class:`TuiViewModel` from the live
    :class:`OperatorSession`.

    Retained for the legacy ``--print-once`` path and the
    ``brain.ui.fixtures.snapshot_view`` / ``brain.ui.fixtures.render_view``
    fixtures. The agent-style runtime path uses
    :func:`build_agent_view_for_session` instead.
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


def build_agent_view_for_session(
    session: OperatorSession,
    composer_state: ComposerState,
    transcript: OperatorTranscript,
    *,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> AgentTuiViewModel:
    """Build an :class:`AgentTuiViewModel` from the live session + composer
    + transcript triple.

    Pure projection: reads the public ``OperatorSession`` fields plus the
    composer state and the local transcript ring. Never mutates the
    session, never touches the kernel. Drives the structural surface of
    ``I-UI-21`` (no side effects).
    """
    if not isinstance(session, OperatorSession):
        raise TypeError(
            "build_agent_view_for_session requires an OperatorSession "
            f"(got {type(session).__name__})"
        )
    if not isinstance(composer_state, ComposerState):
        raise TypeError(
            "build_agent_view_for_session requires a ComposerState "
            f"(got {type(composer_state).__name__})"
        )
    if not isinstance(transcript, OperatorTranscript):
        raise TypeError(
            "build_agent_view_for_session requires an OperatorTranscript "
            f"(got {type(transcript).__name__})"
        )
    bounded_width = max(int(width), MIN_WIDTH)
    bounded_height = max(int(height), MIN_HEIGHT)
    brain = build_brain_snapshot(session.state, latest_tick=session.latest_tick)
    development = build_development_snapshot(
        output_history=session.output_history,
        worldlet_history=session.worldlet_history,
        repl_history=session.repl_history,
    )
    layout = AgentLayout.from_size(bounded_width, bounded_height)
    composer_snapshot = ComposerSnapshot(
        buffer=composer_state.buffer,
        cursor=composer_state.cursor,
        history_size=len(composer_state.history),
        mode=composer_state.mode,
        status_line=composer_state.status_line,
    )
    return AgentTuiViewModel(
        active_view=session.active_view,
        width=bounded_width,
        height=bounded_height,
        brain=brain,
        development=development,
        layout=layout,
        composer=composer_snapshot,
        transcript=transcript.to_snapshot(),
        tick_counter=session.tick_counter,
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
    resource. The agent-style wrapper reuses this factory for the legacy
    ``n`` keystroke (per corrigenda ruling B: ``n`` opens the bounded
    two-field prompt; it is a wrapper concession, not a composer feature).
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
# Step loop — legacy single-keystroke dispatch path (retained for fixtures).
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
    """Translate one keystroke, dispatch, and render the next view (legacy).

    Retained for the existing ``I-UI-14`` aggregate walk and the
    ``I-UI-11`` smoke fixture. The agent-style runtime loop uses
    :func:`step_agent_loop` instead; this function continues to operate
    against the legacy single-pane :class:`TuiViewModel` so the existing
    fixtures keep their input contract.

    The function is total: unknown keystrokes return a :class:`StepOutcome`
    with ``command=None`` and ``dispatched=False``; the session is left
    untouched in that branch.
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
# Agent-style keystroke router — the I-UI-21 delegation surface.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AgentKeyKind:
    """Closed string-tag identity for an agent-style keystroke class.

    The wrapper translates each raw curses key code into exactly one
    :class:`AgentKeyKind` value before deciding whether to forward to
    the composer or to a reserved-key shortcut. Drives ``I-UI-21``: the
    delegation surface is a finite table.

    ``AgentKeyKind`` is implemented as a frozen-dataclass tag rather
    than an :class:`enum.Enum` because :mod:`brain.ui.tui` is constrained
    by ``I-UI-11`` to import only from a narrow root set (``__future__``,
    ``curses``, ``dataclasses``, ``typing``, ``brain.*``). The closed
    membership is enforced by :data:`AGENT_KEY_KINDS` (a frozenset of
    every legal ``value``) and by ``__post_init__``.
    """

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError(
                "AgentKeyKind.value must be str "
                f"(got {type(self.value).__name__})"
            )
        if self.value not in _AGENT_KEY_KIND_VALUES:
            raise ValueError(
                f"AgentKeyKind.value {self.value!r} is not in "
                f"{sorted(_AGENT_KEY_KIND_VALUES)!r}"
            )


#: Closed set of legal :class:`AgentKeyKind` string values. The constant
#: lives at module scope so the constructor can validate at
#: construction time without inflating the surface.
_AGENT_KEY_KIND_VALUES: frozenset[str] = frozenset({
    "char",
    "submit",
    "backspace",
    "clear_buffer",
    "history_prev",
    "history_next",
    "open_prompt",
    "accel",
    "none",
})


def _make_agent_key_kind(value: str) -> AgentKeyKind:
    """Construct an :class:`AgentKeyKind`. Internal helper."""
    return AgentKeyKind(value=value)


# Singleton tags — the closed enumeration the wrapper consults. The
# objects are frozen and value-equal across calls, so ``is`` and ``==``
# both work for routing.
_AGENT_KEY_CHAR = _make_agent_key_kind("char")
_AGENT_KEY_SUBMIT = _make_agent_key_kind("submit")
_AGENT_KEY_BACKSPACE = _make_agent_key_kind("backspace")
_AGENT_KEY_CLEAR_BUFFER = _make_agent_key_kind("clear_buffer")
_AGENT_KEY_HISTORY_PREV = _make_agent_key_kind("history_prev")
_AGENT_KEY_HISTORY_NEXT = _make_agent_key_kind("history_next")
_AGENT_KEY_OPEN_PROMPT = _make_agent_key_kind("open_prompt")
_AGENT_KEY_ACCEL = _make_agent_key_kind("accel")
_AGENT_KEY_NONE = _make_agent_key_kind("none")


def _agent_key_kind_singletons() -> dict[str, AgentKeyKind]:
    """Return the closed mapping of name -> :class:`AgentKeyKind` singleton.

    Exposed for fixtures so they can spell ``AgentKeyKind.CHAR`` style
    references through the public attribute surface below.
    """
    return {
        "CHAR": _AGENT_KEY_CHAR,
        "SUBMIT": _AGENT_KEY_SUBMIT,
        "BACKSPACE": _AGENT_KEY_BACKSPACE,
        "CLEAR_BUFFER": _AGENT_KEY_CLEAR_BUFFER,
        "HISTORY_PREV": _AGENT_KEY_HISTORY_PREV,
        "HISTORY_NEXT": _AGENT_KEY_HISTORY_NEXT,
        "OPEN_PROMPT": _AGENT_KEY_OPEN_PROMPT,
        "ACCEL": _AGENT_KEY_ACCEL,
        "NONE": _AGENT_KEY_NONE,
    }


# Re-expose the singletons as attributes of the :class:`AgentKeyKind`
# class itself so the fixture API ``AgentKeyKind.CHAR`` continues to
# work without importing the underscore-prefixed names.
for _name, _singleton in _agent_key_kind_singletons().items():
    setattr(AgentKeyKind, _name, _singleton)


@dataclass(frozen=True, slots=True)
class AgentKeyRoute:
    """One key route entry produced by :func:`build_agent_keystroke_router`.

    Fields:

    * ``kind`` — closed :class:`AgentKeyKind` tag.
    * ``char`` — single printable character payload for ``CHAR`` routes;
      empty for every other ``kind``.
    * ``accel`` — :class:`OperatorCommand` for ``ACCEL`` routes;
      ``None`` for every other ``kind``.

    Drives ``I-UI-21``: the route is a frozen record with bounded
    primitive fields; no callable, no resource handle.
    """

    kind: AgentKeyKind
    char: str = ""
    accel: Optional[OperatorCommand] = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, AgentKeyKind):
            raise TypeError(
                "AgentKeyRoute.kind must be an AgentKeyKind "
                f"(got {type(self.kind).__name__})"
            )
        if not isinstance(self.char, str):
            raise TypeError(
                "AgentKeyRoute.char must be str "
                f"(got {type(self.char).__name__})"
            )
        if self.kind is AgentKeyKind.CHAR:
            if len(self.char) != 1 or not self.char.isprintable():
                raise ValueError(
                    "AgentKeyRoute.char must be a single printable character "
                    f"for CHAR routes (got {self.char!r})"
                )
            if self.accel is not None:
                raise ValueError(
                    "AgentKeyRoute.accel must be None for CHAR routes"
                )
        elif self.kind is AgentKeyKind.ACCEL:
            if not isinstance(self.accel, OperatorCommand):
                raise TypeError(
                    "AgentKeyRoute.accel must be an OperatorCommand for ACCEL "
                    f"routes (got {type(self.accel).__name__})"
                )
            if self.char != "":
                raise ValueError(
                    "AgentKeyRoute.char must be empty for ACCEL routes"
                )
        else:
            if self.char != "":
                raise ValueError(
                    f"AgentKeyRoute.char must be empty for {self.kind.value} routes"
                )
            if self.accel is not None:
                raise ValueError(
                    f"AgentKeyRoute.accel must be None for {self.kind.value} routes"
                )


#: Curses key codes (control characters and special keys). Re-declared
#: here as integer literals so the wrapper never imports
#: ``curses.KEY_*`` constants at module-import time (curses is imported
#: above for ``curses.echo`` / ``curses.curs_set`` / ``curses.wrapper``,
#: but the keycode constants themselves are only stable after the
#: terminal is initialized). Drives ``I-UI-21``: the route table is a
#: pure-data dictionary, not a curses-runtime lookup.
_KEY_CTRL_C: int = 3
_KEY_CTRL_N: int = 14
_KEY_CTRL_P: int = 16
_KEY_CTRL_U: int = 21
_KEY_ENTER: int = 10
_KEY_RETURN: int = 13
_KEY_BACKSPACE_ASCII: int = 127
_KEY_BACKSPACE_BS: int = 8


def _agent_accel_kind_for(letter: str) -> Optional[OperatorCommand]:
    """Return the :class:`OperatorCommand` for a reserved-accelerator letter.

    The reserved letters fire only when the composer buffer is empty
    (per kickoff section 13). The mapping is the same closed enumeration
    as :data:`KEYMAP` minus the ``"e"`` shortcut (replaced by ``"n"`` per
    corrigenda ruling B; ``"e"`` is not a reserved accelerator in the
    agent layout because typed ``/queue`` is the primary path).
    """
    table: dict[str, OperatorCommand] = {
        "s": OperatorCommand.INSPECT_STATE,
        "t": OperatorCommand.INSPECT_TICK,
        "o": OperatorCommand.INSPECT_OUTPUT,
        "w": OperatorCommand.INSPECT_WORLDLET,
        "r": OperatorCommand.INSPECT_REPL,
        "c": OperatorCommand.CLEAR_STATUS,
        "?": OperatorCommand.HELP,
        "h": OperatorCommand.HELP,
        "q": OperatorCommand.QUIT,
        " ": OperatorCommand.STEP_TICK,
    }
    return table.get(letter)


def build_agent_keystroke_router() -> dict[int, AgentKeyRoute]:
    """Build the agent-style keystroke routing table.

    Returns a finite dict mapping curses key codes to
    :class:`AgentKeyRoute` records. The wrapper uses this table to
    decide, for each raw keystroke, whether to forward to the bottom
    composer or to a reserved-key handler. Drives ``I-UI-21``: the
    delegation surface is a finite, fixture-auditable table built once
    per session.

    Printable characters (codes 32..126) are routed as ``CHAR`` so the
    wrapper can decide at routing time whether the composer's buffer
    state implies the keystroke should fire an accelerator instead.
    """
    table: dict[int, AgentKeyRoute] = {}
    # Control characters and special keys.
    table[_KEY_ENTER] = AgentKeyRoute(kind=AgentKeyKind.SUBMIT)
    table[_KEY_RETURN] = AgentKeyRoute(kind=AgentKeyKind.SUBMIT)
    table[_KEY_BACKSPACE_ASCII] = AgentKeyRoute(kind=AgentKeyKind.BACKSPACE)
    table[_KEY_BACKSPACE_BS] = AgentKeyRoute(kind=AgentKeyKind.BACKSPACE)
    table[_KEY_CTRL_C] = AgentKeyRoute(kind=AgentKeyKind.CLEAR_BUFFER)
    table[_KEY_CTRL_U] = AgentKeyRoute(kind=AgentKeyKind.CLEAR_BUFFER)
    table[_KEY_CTRL_P] = AgentKeyRoute(kind=AgentKeyKind.HISTORY_PREV)
    table[_KEY_CTRL_N] = AgentKeyRoute(kind=AgentKeyKind.HISTORY_NEXT)
    # Printable characters: every ASCII printable maps to CHAR. The
    # buffer-empty accelerator decision is made by the wrapper at
    # dispatch time (see :func:`route_agent_keystroke`).
    for code in range(32, 127):
        table[code] = AgentKeyRoute(kind=AgentKeyKind.CHAR, char=chr(code))
    return table


#: The closed list of typed verb tokens the parser accepts. The wrapper
#: uses :data:`brain.ui.command_line.LOCAL_COMMAND_HELP` for the
#: footer/help text but consults this constant only for documentation
#: completeness; the parser is the source of truth.
_AGENT_HELP_HINT: str = (
    "type /help for typed-command list; "
    "enter submits, ^u clears, ^p / ^n recall history"
)


def route_agent_keystroke(
    code: int,
    composer_state: ComposerState,
    *,
    router: Optional[dict[int, AgentKeyRoute]] = None,
) -> AgentKeyRoute:
    """Translate a raw curses key code into an :class:`AgentKeyRoute`.

    The router is built once per session and passed in for determinism;
    callers that want default behaviour can omit the argument and the
    function builds a fresh table.

    Coexistence rule (kickoff section 13, locked by corrigenda): a
    printable character fires its reserved accelerator (when one exists)
    only when ``composer_state.buffer`` is empty AND the character is not
    ``"/"``. Once the composer has any input or the operator types
    ``"/"``, every printable keystroke flows through ``INSERT_CHAR`` until
    the buffer is cleared or submitted.
    """
    if not isinstance(code, int) or isinstance(code, bool):
        raise TypeError(
            f"route_agent_keystroke requires int code (got {type(code).__name__})"
        )
    if not isinstance(composer_state, ComposerState):
        raise TypeError(
            "route_agent_keystroke requires a ComposerState "
            f"(got {type(composer_state).__name__})"
        )
    table = router if router is not None else build_agent_keystroke_router()
    if code < 0:
        return AgentKeyRoute(kind=AgentKeyKind.NONE)
    route = table.get(code)
    if route is None:
        return AgentKeyRoute(kind=AgentKeyKind.NONE)
    if route.kind is AgentKeyKind.CHAR:
        # The reserved accelerator only fires when the composer is empty
        # AND the character is not "/" (the typed-command prefix).
        if not composer_state.buffer and route.char != "/":
            accel = _agent_accel_kind_for(route.char)
            if accel is not None:
                if route.char == "n":
                    return AgentKeyRoute(kind=AgentKeyKind.OPEN_PROMPT)
                return AgentKeyRoute(kind=AgentKeyKind.ACCEL, accel=accel)
            # ``n`` opens the legacy prompt even though it is not in the
            # _agent_accel_kind_for table (it is not an OperatorCommand).
            if route.char == "n":
                return AgentKeyRoute(kind=AgentKeyKind.OPEN_PROMPT)
        return route
    return route


# ---------------------------------------------------------------------------
# Agent-style step loop — composer + parser + dispatch + transcript.
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class AgentStepResult:
    """Result of one agent-style step.

    The result carries the next :class:`ComposerState`, the next
    :class:`OperatorTranscript`, an inspection summary of what the
    wrapper did, and the rendered rows for the frame. Drives the
    structural side of ``I-UI-21`` (delegation visibility) and the
    OBSERVED side of ``I-UI-23`` (scripted walk inspection).
    """

    composer_state: ComposerState
    transcript: OperatorTranscript
    route_kind: AgentKeyKind
    submitted_line: Optional[str] = None
    parsed_command: Optional[Command] = None
    parse_error: Optional[str] = None
    dispatched: bool = False
    dispatched_kind: Optional[OperatorCommand] = None
    accel_kind: Optional[OperatorCommand] = None
    transcript_appends: list[TranscriptKind] = field(default_factory=list)


def step_agent_loop(
    session: OperatorSession,
    composer_state: ComposerState,
    transcript: OperatorTranscript,
    code: int,
    *,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    client: Optional["LLMClient"] = None,
    percept_factory: Optional[Callable[[OperatorSession], Command]] = None,
    composer: Optional[BottomComposer] = None,
    parser: Optional[LocalCommandLine] = None,
    router: Optional[dict[int, AgentKeyRoute]] = None,
) -> AgentStepResult:
    """Translate one raw curses keystroke and run the agent-style step.

    Drives ``I-UI-21`` (the wrapper delegates input to composer / parser
    / router and does not mutate kernel state directly) and feeds the
    OBSERVED ``I-UI-23`` walk fixture.

    The function is total: an unknown keystroke yields an
    :class:`AgentStepResult` with ``route_kind=AgentKeyKind.NONE`` and
    no mutation of session / composer / transcript beyond a fresh
    ``next_state`` adoption (which preserves all fields).
    """
    if not isinstance(session, OperatorSession):
        raise TypeError(
            "step_agent_loop requires an OperatorSession "
            f"(got {type(session).__name__})"
        )
    if not isinstance(composer_state, ComposerState):
        raise TypeError(
            "step_agent_loop requires a ComposerState "
            f"(got {type(composer_state).__name__})"
        )
    if not isinstance(transcript, OperatorTranscript):
        raise TypeError(
            "step_agent_loop requires an OperatorTranscript "
            f"(got {type(transcript).__name__})"
        )
    bottom = composer if composer is not None else BottomComposer()
    cmd_parser = parser if parser is not None else LocalCommandLine()
    route = route_agent_keystroke(code, composer_state, router=router)
    result = AgentStepResult(
        composer_state=composer_state,
        transcript=transcript,
        route_kind=route.kind,
    )

    if route.kind is AgentKeyKind.NONE:
        return result

    if route.kind is AgentKeyKind.CHAR:
        new_state = bottom.apply(
            composer_state, ComposerAction.INSERT_CHAR, char=route.char
        )
        assert isinstance(new_state, ComposerState)
        result.composer_state = new_state
        return result

    if route.kind is AgentKeyKind.BACKSPACE:
        new_state = bottom.apply(composer_state, ComposerAction.BACKSPACE)
        assert isinstance(new_state, ComposerState)
        result.composer_state = new_state
        return result

    if route.kind is AgentKeyKind.CLEAR_BUFFER:
        new_state = bottom.apply(composer_state, ComposerAction.CLEAR_BUFFER)
        assert isinstance(new_state, ComposerState)
        result.composer_state = new_state
        return result

    if route.kind is AgentKeyKind.HISTORY_PREV:
        new_state = bottom.apply(composer_state, ComposerAction.HISTORY_PREV)
        assert isinstance(new_state, ComposerState)
        result.composer_state = new_state
        return result

    if route.kind is AgentKeyKind.HISTORY_NEXT:
        new_state = bottom.apply(composer_state, ComposerAction.HISTORY_NEXT)
        assert isinstance(new_state, ComposerState)
        result.composer_state = new_state
        return result

    if route.kind is AgentKeyKind.OPEN_PROMPT:
        # The legacy curses prompt is opened only when a factory has been
        # configured (the live entrypoint always supplies one). When no
        # factory is configured, surface a local UI error so the operator
        # sees the same fail-closed behaviour the legacy `e` keystroke
        # already provides.
        if percept_factory is None:
            session.set_error("queue percept: no input prompt configured")
            result.transcript = transcript.append(
                TranscriptKind.ERROR,
                session.tick_counter,
                session.error_message,
            )
            result.transcript_appends.append(TranscriptKind.ERROR)
            return result
        try:
            cmd = percept_factory(session)
        except (TypeError, ValueError) as exc:
            session.set_error(f"queue percept rejected: {exc}")
            result.transcript = transcript.append(
                TranscriptKind.ERROR,
                session.tick_counter,
                session.error_message,
            )
            result.transcript_appends.append(TranscriptKind.ERROR)
            return result
        if not isinstance(cmd, Command) or cmd.kind is not OperatorCommand.QUEUE_PERCEPT:
            session.set_error(
                "queue percept factory did not return a QUEUE_PERCEPT Command"
            )
            result.transcript = transcript.append(
                TranscriptKind.ERROR,
                session.tick_counter,
                session.error_message,
            )
            result.transcript_appends.append(TranscriptKind.ERROR)
            return result
        result.transcript = _dispatch_and_log(
            session, transcript, cmd, client=client
        )
        result.transcript_appends.append(
            _transcript_kind_for(cmd.kind, session)
        )
        result.dispatched = True
        result.dispatched_kind = cmd.kind
        result.parsed_command = cmd
        return result

    if route.kind is AgentKeyKind.ACCEL:
        assert route.accel is not None
        result.accel_kind = route.accel
        cmd = make_command(route.accel)
        result.transcript = _dispatch_and_log(
            session,
            transcript,
            cmd,
            client=client,
        )
        result.transcript_appends.append(_transcript_kind_for(route.accel, session))
        result.dispatched = True
        result.dispatched_kind = route.accel
        result.parsed_command = cmd
        return result

    if route.kind is AgentKeyKind.SUBMIT:
        submitted = bottom.apply(composer_state, ComposerAction.SUBMIT)
        if isinstance(submitted, ComposerState):
            # Empty submission: the composer surfaced the empty-submission
            # status on the meta row; no parse, no dispatch, no transcript.
            result.composer_state = submitted
            return result
        assert isinstance(submitted, ComposerSubmission)
        result.composer_state = submitted.next_state
        result.submitted_line = submitted.line
        # Always log the SUBMIT entry so the transcript pane reflects the
        # operator's typed input verbatim.
        next_transcript = transcript.append(
            TranscriptKind.SUBMIT,
            session.tick_counter,
            submitted.line,
        )
        result.transcript_appends.append(TranscriptKind.SUBMIT)
        parse_result = cmd_parser.parse(submitted.line)
        if isinstance(parse_result, LocalCommandError):
            session.set_error(parse_result.message)
            next_transcript = next_transcript.append(
                TranscriptKind.ERROR,
                session.tick_counter,
                parse_result.message,
            )
            result.transcript_appends.append(TranscriptKind.ERROR)
            result.transcript = next_transcript
            result.parse_error = parse_result.message
            return result
        # parse_result is a Command record.
        result.parsed_command = parse_result
        if parse_result.kind is OperatorCommand.QUEUE_PERCEPT:
            # Re-route through the same logging helper. We forward the
            # transcript already extended with SUBMIT so the dispatch
            # path appends QUEUED on top.
            result.transcript = _dispatch_and_log(
                session,
                next_transcript,
                parse_result,
                client=client,
            )
            result.transcript_appends.append(
                _transcript_kind_for(parse_result.kind, session)
            )
        else:
            result.transcript = _dispatch_and_log(
                session,
                next_transcript,
                parse_result,
                client=client,
            )
            result.transcript_appends.append(
                _transcript_kind_for(parse_result.kind, session)
            )
        result.dispatched = True
        result.dispatched_kind = parse_result.kind
        return result

    # Defensive: every AgentKeyKind member is handled above.
    raise AssertionError(  # pragma: no cover - enum is closed
        f"I-UI-21 violated: unrouted AgentKeyKind {route.kind!r}"
    )


def _transcript_kind_for(
    kind: OperatorCommand, session: OperatorSession
) -> TranscriptKind:
    """Pick the :class:`TranscriptKind` tag for a dispatched command kind.

    A dispatch that produced an error surfaces ``ERROR`` regardless of the
    kind so the operator sees the failure path in the transcript.
    """
    if session.error_message:
        return TranscriptKind.ERROR
    if kind is OperatorCommand.QUEUE_PERCEPT:
        return TranscriptKind.QUEUED
    if kind is OperatorCommand.STEP_TICK:
        return TranscriptKind.STEP
    if kind is OperatorCommand.QUIT:
        return TranscriptKind.QUIT
    return TranscriptKind.VIEW


def _dispatch_and_log(
    session: OperatorSession,
    transcript: OperatorTranscript,
    command: Command,
    *,
    client: Optional["LLMClient"],
) -> OperatorTranscript:
    """Dispatch *command* on *session* and return the transcript with the
    follow-up entry appended.

    The dispatch path is identical to today's keystroke path
    (``session.dispatch(command, client=client)``); the transcript append
    is local UI state only. Drives the I-UI-21 delegation property: the
    wrapper never appends to ``session.event_queue`` directly and never
    calls ``brain.tick.tick`` directly.
    """
    pre_error = session.error_message
    session.dispatch(command, client=client)
    kind = _transcript_kind_for(command.kind, session)
    if kind is TranscriptKind.ERROR:
        message = session.error_message or "dispatch failure"
    else:
        message = session.status_message or command.kind.value
    return transcript.append(kind, session.tick_counter, message)


# ---------------------------------------------------------------------------
# Lifecycle — the only curses-touching surface in this module.
# ---------------------------------------------------------------------------


def _read_keystroke(stdscr: object) -> str:
    """Translate a curses ``getch()`` to the legacy wrapper's keystroke alphabet.

    Returns the printable character for ASCII keys, the literal string
    ``"space"`` for the spacebar (consistent with
    :data:`brain.ui.render.DEFAULT_KEYBOARD_HELP`), and the empty string
    for keys outside the supported set. The translator never raises.
    Used by :func:`step_loop` (legacy path).
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


def _read_agent_code(stdscr: object) -> int:
    """Read one raw key code for the agent-style loop.

    Returns the raw integer code from ``stdscr.getch()``. The agent
    router (:func:`route_agent_keystroke`) classifies the code into an
    :class:`AgentKeyRoute`; this helper does not perform that
    classification so a future expansion (e.g. ``KEY_LEFT`` / ``KEY_HOME``)
    only needs to extend the router, not this reader.
    """
    if not hasattr(stdscr, "getch"):
        raise TypeError(
            "_read_agent_code requires a curses window (got "
            f"{type(stdscr).__name__})"
        )
    return int(stdscr.getch())  # type: ignore[attr-defined]


def run_curses(
    session: OperatorSession,
    *,
    client: Optional["LLMClient"] = None,
    percept_factory: Optional[Callable[[OperatorSession], Command]] = None,
    percept_factory_builder: Optional[
        Callable[..., Callable[[OperatorSession], Command]]
    ] = None,
) -> None:
    """Open a curses screen and run the agent-style operator session until
    ``QUIT``.

    This is the only function in this module that actually touches
    :mod:`curses`. It delegates every other concern (state, snapshots,
    layout, rendering, key translation, dispatch) to the helpers above
    so the non-interactive smoke fixtures can exercise the full surface
    without attaching to a real terminal.

    The agent-style loop maintains a local :class:`ComposerState` and a
    local :class:`OperatorTranscript` on the wrapper's stack. Both die
    when the wrapper exits (corrigenda ruling D — no cross-invocation
    persistence). The kernel boundary is held exactly where it is today:
    every dispatch goes through :meth:`OperatorSession.dispatch`, every
    ``STEP_TICK`` goes through :func:`brain.tick.tick` via
    :meth:`OperatorSession.step_tick`, and the wrapper never appends to
    :attr:`OperatorSession.event_queue` directly.

    Drives ``I-UI-21`` (delegation) and feeds ``I-UI-23`` (OBSERVED
    scripted-walk fixture).
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

    composer = BottomComposer()
    parser = LocalCommandLine()
    router = build_agent_keystroke_router()

    def _body(stdscr: object) -> None:
        # Hide the cursor; non-blocking input is not required because the
        # operator drives the loop one keystroke at a time.
        try:
            curses.curs_set(0)
        except curses.error:
            # Some terminals reject curs_set; non-fatal.
            pass
        composer_state = ComposerState.empty()
        transcript = OperatorTranscript.empty()
        while not session.quit_flag:
            height, width = stdscr.getmaxyx()  # type: ignore[attr-defined]
            bounded_width = max(int(width), MIN_WIDTH)
            bounded_height = max(int(height), MIN_HEIGHT)
            view = build_agent_view_for_session(
                session,
                composer_state,
                transcript,
                width=bounded_width,
                height=bounded_height,
            )
            rows = render_agent(view)
            paint_rows(
                stdscr,
                rows,
                width=bounded_width,
                height=bounded_height,
            )
            code = _read_agent_code(stdscr)
            if code < 0:
                # No keystroke; loop and repaint.
                continue
            # Resolve the effective percept factory for this iteration.
            if percept_factory is not None:
                effective_factory = percept_factory
            else:
                builder = (
                    percept_factory_builder
                    if percept_factory_builder is not None
                    else make_curses_percept_factory
                )
                effective_factory = builder(
                    stdscr, width=bounded_width, height=bounded_height
                )
            result = step_agent_loop(
                session,
                composer_state,
                transcript,
                code,
                width=bounded_width,
                height=bounded_height,
                client=client,
                percept_factory=effective_factory,
                composer=composer,
                parser=parser,
                router=router,
            )
            composer_state = result.composer_state
            transcript = result.transcript

    curses.wrapper(_body)


__all__ = [
    "AGENT_HELP_HINT",
    "AgentKeyKind",
    "AgentKeyRoute",
    "AgentStepResult",
    "KEYMAP",
    "PROMPT_DEFAULT_CONTENT_STATE",
    "PROMPT_DEFAULT_RHO",
    "PROMPT_MAX_INPUT_LEN",
    "PaintCall",
    "PaintRecorder",
    "StepOutcome",
    "build_agent_keystroke_router",
    "build_agent_view_for_session",
    "build_view_for_session",
    "make_curses_percept_factory",
    "paint_rows",
    "prompt_queue_percept",
    "route_agent_keystroke",
    "run_curses",
    "step_agent_loop",
    "step_loop",
    "translate_key",
]


#: Public alias for the agent-help hint used by the wrapper footer/help
#: text. Exposed for the README and the OBSERVED I-UI-23 fixture.
AGENT_HELP_HINT: str = _AGENT_HELP_HINT
