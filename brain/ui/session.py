"""Operator TUI session and command router.

This module owns the :class:`OperatorSession` runtime: the resource-free
record of "what the operator is currently looking at" plus the
non-curses command router that dispatches an :class:`OperatorCommand`
through the existing public ``tick()`` entrypoint.

Catalog rows driven from here:

* ``I-UI-05`` — ``STEP_TICK`` route uses the public ``tick()`` path only.
  The session invokes :func:`brain.tick.tick` exactly once per
  ``STEP_TICK`` command with the operator-queued :class:`PerceptEvent`,
  stores the returned :class:`TickRecord`, and replaces the session's
  :class:`BrainState` with the new state.
* ``I-UI-06`` — validation and tick failures are local UI status only.
  If :class:`PerceptEvent` validation or ``tick()`` raises, the router
  records the failure as local UI status / error text on the session
  and leaves every kernel container unchanged.
* ``I-UI-10`` — ``OperatorSession`` holds no unsafe resources. The
  record's declared fields are exactly the read-only kernel /
  developmental references the campaign approves; no LLM client, no
  subprocess handle, no file descriptor, no socket, no shell-command
  string intended for execution, and no host-execution callback may
  appear on a session instance.
* ``I-UI-13`` — local UI status text is bounded printable text only.
  Status and error setters reject non-printable input and truncate to a
  bounded length so a long error message cannot blow past the
  status-pane budget. The keyboard map is the finite
  :data:`brain.ui.render.DEFAULT_KEYBOARD_HELP` enumeration; the
  session never writes status text to a trace, scenario, or history.

This module imports :mod:`brain.tick` for the ``BrainState`` /
``tick`` symbols (the only public kernel orchestrator) and from the
local :mod:`brain.ui.commands` / :mod:`brain.ui.snapshot` /
:mod:`brain.ui.render` UI surfaces. It does **not** import ``curses``,
``brain.llm``, ``subprocess``, ``socket``, ``urllib``, ``http``, or
``requests``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from brain.tick import BrainState, tick
from brain.ui.commands import (
    INSPECT_VIEW_MAP,
    Command,
    OperatorCommand,
    QueuePerceptPayload,
)
from brain.ui.render import DEFAULT_KEYBOARD_HELP
from brain.ui.snapshot import ACTIVE_VIEWS

if TYPE_CHECKING:  # pragma: no cover - typing-only imports
    from brain.development.output import OutputHistory
    from brain.development.repl import ProtoBasicHistory
    from brain.development.worldlet import WorldletHistory
    from brain.io_types import TickRecord
    from brain.llm.client import LLMClient


# ---------------------------------------------------------------------------
# Bounded UI text policy
# ---------------------------------------------------------------------------


#: Maximum number of operator-queued events the session keeps before the
#: queue is treated as full. The router rejects further ``QUEUE_PERCEPT``
#: commands with a local UI status update; it never silently drops a
#: queued event.
DEFAULT_EVENT_QUEUE_LIMIT = 4


#: Maximum number of printable characters the session retains in its
#: status / error fields. Drives the bounded-text half of ``I-UI-13``.
MAX_STATUS_TEXT_LEN = 240


def _bound_printable(label: str, value: str) -> str:
    """Reject non-printable text; truncate at :data:`MAX_STATUS_TEXT_LEN`.

    Drives ``I-UI-13``: status / error text is bounded printable text
    only. Non-strings and non-printable strings raise a
    :class:`TypeError` / :class:`ValueError` so the caller cannot
    smuggle terminal control sequences or callable values into the
    status pane.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"I-UI-13 violated: {label} must be a str (got "
            f"{type(value).__name__})"
        )
    # Empty string is allowed (no status / cleared error).
    if value and not value.isprintable():
        raise ValueError(
            f"I-UI-13 violated: {label} must be printable text "
            f"(got {value!r})"
        )
    if len(value) > MAX_STATUS_TEXT_LEN:
        # Truncation preserves printability (the surviving prefix is
        # printable because the whole string was).
        return value[: MAX_STATUS_TEXT_LEN - 1] + "…"
    return value


# ---------------------------------------------------------------------------
# OperatorEventQueue — bounded read-only-from-outside queue
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class OperatorEventQueue:
    """Bounded FIFO of queued :class:`QueuePerceptPayload` candidates.

    The queue stores only validated payloads. The session is the sole
    writer; external callers read the snapshot via :meth:`peek` or
    :meth:`snapshot`. The queue carries no callable, file handle, or
    socket — only payload records.
    """

    limit: int = DEFAULT_EVENT_QUEUE_LIMIT
    _items: list[QueuePerceptPayload] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.limit, int) or self.limit <= 0:
            raise ValueError(
                "OperatorEventQueue.limit must be a positive int "
                f"(got {self.limit!r})"
            )

    def __len__(self) -> int:
        return len(self._items)

    def is_full(self) -> bool:
        return len(self._items) >= self.limit

    def enqueue(self, payload: QueuePerceptPayload) -> None:
        if not isinstance(payload, QueuePerceptPayload):
            raise TypeError(
                "OperatorEventQueue.enqueue requires a QueuePerceptPayload "
                f"(got {type(payload).__name__})"
            )
        if self.is_full():
            raise OverflowError(
                f"OperatorEventQueue is full (limit={self.limit})"
            )
        self._items.append(payload)

    def dequeue(self) -> QueuePerceptPayload:
        if not self._items:
            raise IndexError("OperatorEventQueue is empty")
        return self._items.pop(0)

    def peek(self) -> Optional[QueuePerceptPayload]:
        if not self._items:
            return None
        return self._items[0]

    def snapshot(self) -> tuple[QueuePerceptPayload, ...]:
        return tuple(self._items)


# ---------------------------------------------------------------------------
# OperatorSession — resource-free runtime record
# ---------------------------------------------------------------------------


#: The set of attribute names :class:`OperatorSession` is allowed to
#: expose. Drives ``I-UI-10``: any other attribute (LLM client,
#: subprocess handle, file descriptor, socket, shell-command string for
#: execution, host-execution callback) is rejected at construction time
#: and at every router dispatch.
_ALLOWED_SESSION_ATTRS: frozenset[str] = frozenset({
    "state",
    "latest_tick",
    "output_history",
    "worldlet_history",
    "repl_history",
    "event_queue",
    "active_view",
    "status_message",
    "error_message",
    "quit_flag",
    "tick_counter",
})


@dataclass(slots=True)
class OperatorSession:
    """Resource-free record of the current operator session.

    All fields are either immutable kernel / developmental records, the
    bounded :class:`OperatorEventQueue`, bounded printable text, or
    plain integers / bools / strings. No field is a callable, file
    handle, socket, subprocess handle, or LLM client.

    Drives ``I-UI-10`` (no unsafe resources) and contributes to
    ``I-UI-13`` (status / error text is bounded printable text).

    The active LLM client is **not** stored on the session. The router
    method :meth:`step_tick` accepts the client as an argument so the
    session record remains free of LLM-protocol surfaces (``I-UI-10``).
    """

    state: BrainState
    latest_tick: Optional["TickRecord"] = None
    output_history: Optional["OutputHistory"] = None
    worldlet_history: Optional["WorldletHistory"] = None
    repl_history: Optional["ProtoBasicHistory"] = None
    event_queue: OperatorEventQueue = field(default_factory=OperatorEventQueue)
    active_view: str = "state"
    status_message: str = ""
    error_message: str = ""
    quit_flag: bool = False
    tick_counter: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.state, BrainState):
            raise TypeError(
                "OperatorSession.state must be a BrainState "
                f"(got {type(self.state).__name__})"
            )
        if not isinstance(self.event_queue, OperatorEventQueue):
            raise TypeError(
                "OperatorSession.event_queue must be an OperatorEventQueue "
                f"(got {type(self.event_queue).__name__})"
            )
        if self.active_view not in ACTIVE_VIEWS:
            raise ValueError(
                "I-UI-10 violated: active_view "
                f"{self.active_view!r} is not in {ACTIVE_VIEWS!r}"
            )
        # Bounded printable status/error text (drives I-UI-13).
        object.__setattr__(
            self,
            "status_message",
            _bound_printable("OperatorSession.status_message", self.status_message),
        )
        object.__setattr__(
            self,
            "error_message",
            _bound_printable("OperatorSession.error_message", self.error_message),
        )
        if not isinstance(self.quit_flag, bool):
            raise TypeError(
                "OperatorSession.quit_flag must be bool "
                f"(got {type(self.quit_flag).__name__})"
            )
        if not isinstance(self.tick_counter, int) or self.tick_counter < 0:
            raise ValueError(
                "OperatorSession.tick_counter must be a non-negative int "
                f"(got {self.tick_counter!r})"
            )
        self._assert_no_unsafe_resources()

    # ------------------------------------------------------------------
    # I-UI-10 — runtime self-audit for forbidden resources.
    # ------------------------------------------------------------------

    def _assert_no_unsafe_resources(self) -> None:
        """Reject any attribute that looks like an unsafe resource handle.

        Drives ``I-UI-10``. The declared slot list already restricts the
        attribute surface; this check inspects each declared value and
        rejects callables, file handles, sockets, subprocess handles,
        and LLM-client-shaped objects (``eval_consistency`` duck type).
        Together with the slot list this prevents a future refactor
        from silently widening the session's surface.
        """
        declared = set(_ALLOWED_SESSION_ATTRS)
        actual = set(self.__slots__)
        if actual != declared:
            raise AssertionError(
                "I-UI-10 violated: OperatorSession attribute surface "
                f"drifted (declared={sorted(declared)!r}, "
                f"actual={sorted(actual)!r})"
            )
        for name in declared:
            value = getattr(self, name)
            if callable(value):
                raise AssertionError(
                    f"I-UI-10 violated: OperatorSession.{name} is callable"
                )
            # LLM-client duck typing: anything that exposes
            # ``eval_consistency`` is treated as an LLM client.
            if hasattr(value, "eval_consistency"):
                raise AssertionError(
                    f"I-UI-10 violated: OperatorSession.{name} looks like an "
                    "LLM client (has eval_consistency)"
                )
            # Resource-handle duck typing: file/socket/process-like.
            if (
                hasattr(value, "read")
                and hasattr(value, "write")
                and not isinstance(value, BrainState)
            ):
                raise AssertionError(
                    f"I-UI-10 violated: OperatorSession.{name} exposes "
                    "read/write (file/socket-like)"
                )
            if hasattr(value, "fileno"):
                raise AssertionError(
                    f"I-UI-10 violated: OperatorSession.{name} exposes "
                    "fileno() (resource-like)"
                )
            if hasattr(value, "send_signal") or hasattr(value, "communicate"):
                raise AssertionError(
                    f"I-UI-10 violated: OperatorSession.{name} looks like a "
                    "subprocess handle"
                )

    # ------------------------------------------------------------------
    # Status / error / view setters — all enforce I-UI-13 bounds.
    # ------------------------------------------------------------------

    def set_status(self, message: str) -> None:
        self.status_message = _bound_printable(
            "OperatorSession.status_message", message
        )

    def set_error(self, message: str) -> None:
        self.error_message = _bound_printable(
            "OperatorSession.error_message", message
        )

    def clear_status(self) -> None:
        self.status_message = ""
        self.error_message = ""

    def set_active_view(self, view: str) -> None:
        if view not in ACTIVE_VIEWS:
            raise ValueError(
                "I-UI-13 violated: active_view "
                f"{view!r} is not in {ACTIVE_VIEWS!r}"
            )
        self.active_view = view

    # ------------------------------------------------------------------
    # Router entrypoints
    # ------------------------------------------------------------------

    def dispatch(
        self,
        command: Command,
        *,
        client: Optional["LLMClient"] = None,
    ) -> None:
        """Route a single :class:`Command` to its handler.

        The handler updates the session in-place. ``client`` is only
        consulted for :data:`OperatorCommand.STEP_TICK`; every other
        command kind ignores it. ``client`` is **not** stored on the
        session (``I-UI-10``).
        """
        if not isinstance(command, Command):
            raise TypeError(
                "OperatorSession.dispatch requires a Command "
                f"(got {type(command).__name__})"
            )

        kind = command.kind
        if kind in INSPECT_VIEW_MAP:
            self.set_active_view(INSPECT_VIEW_MAP[kind])
            self.set_status(f"view = {INSPECT_VIEW_MAP[kind]}")
        elif kind is OperatorCommand.QUEUE_PERCEPT:
            self._dispatch_queue(command.payload)
        elif kind is OperatorCommand.STEP_TICK:
            self._dispatch_step(client)
        elif kind is OperatorCommand.CLEAR_STATUS:
            self.clear_status()
        elif kind is OperatorCommand.HELP:
            self.set_active_view("help")
            self.set_status("help")
        elif kind is OperatorCommand.QUIT:
            self.quit_flag = True
            self.set_status("quit")
        elif kind is OperatorCommand.NOOP:
            # Explicit no-op: leave session state unchanged. Drives the
            # "every command kind is handled" branch of I-UI-03.
            return
        else:  # pragma: no cover - the enum is closed
            raise AssertionError(
                f"I-UI-03 violated: unrouted OperatorCommand {kind!r}"
            )

        # Self-audit after every dispatch so a buggy handler cannot
        # widen the session's resource surface unnoticed.
        self._assert_no_unsafe_resources()

    # ------------------------------------------------------------------
    # Internal handlers
    # ------------------------------------------------------------------

    def _dispatch_queue(self, payload: Optional[QueuePerceptPayload]) -> None:
        if not isinstance(payload, QueuePerceptPayload):
            # ``Command.__post_init__`` rejects this, so reaching here
            # means a caller bypassed the wrapper. Treat as local UI
            # status only — do not raise.
            self.set_error("QUEUE_PERCEPT requires a QueuePerceptPayload")
            return
        if self.event_queue.is_full():
            self.set_error(
                f"event queue full (limit={self.event_queue.limit})"
            )
            return
        try:
            self.event_queue.enqueue(payload)
        except (TypeError, ValueError, OverflowError) as exc:
            # Local UI status only (drives I-UI-06).
            self.set_error(f"queue rejected percept: {exc}")
            return
        self.set_active_view("queue")
        self.set_status(
            f"queued percept {payload.content_id!r} "
            f"(queue size = {len(self.event_queue)})"
        )

    def _dispatch_step(self, client: Optional["LLMClient"]) -> None:
        """Single-tick router. Drives ``I-UI-05`` and ``I-UI-06``.

        Pops one queued payload, rebuilds the :class:`PerceptEvent`,
        calls :func:`brain.tick.tick` exactly once, stores the returned
        :class:`TickRecord`, and replaces the session's
        :class:`BrainState` with the new state. Any exception during
        validation or tick is captured as local UI status / error;
        no kernel container is mutated on the failure path.
        """
        if client is None:
            self.set_error("STEP_TICK requires an LLM client argument")
            return
        # Capture the pre-tick session snapshot so a failure path can
        # assert no kernel-side mutation occurred (drives I-UI-06).
        prior_state = self.state
        prior_latest_tick = self.latest_tick
        prior_queue_size = len(self.event_queue)

        if prior_queue_size == 0:
            self.set_error("STEP_TICK with empty event queue")
            return

        payload = self.event_queue.peek()
        assert payload is not None  # peek returned because queue not empty
        try:
            event = payload.build_event()
        except (TypeError, ValueError) as exc:
            # PerceptEvent construction rejected the payload; this can
            # only happen if a payload was stored without going through
            # the validating constructor. Record as local UI status,
            # leave kernel state and queue intact.
            self.set_error(f"percept rejected: {exc}")
            # Verify no kernel mutation occurred.
            assert self.state is prior_state
            assert self.latest_tick is prior_latest_tick
            assert len(self.event_queue) == prior_queue_size
            return

        try:
            new_state, record = tick(
                prior_state,
                [event],
                client,
                tick_id=self.tick_counter + 1,
            )
        except Exception as exc:  # noqa: BLE001 - capture every tick failure
            # I-UI-06: local UI status only on tick failure.
            self.set_error(f"tick failure: {type(exc).__name__}: {exc}")
            # Kernel state and queue must remain untouched.
            assert self.state is prior_state, (
                "I-UI-06 violated: state mutated on tick failure"
            )
            assert self.latest_tick is prior_latest_tick, (
                "I-UI-06 violated: latest_tick mutated on tick failure"
            )
            assert len(self.event_queue) == prior_queue_size, (
                "I-UI-06 violated: event_queue size changed on tick failure"
            )
            return

        # Success: consume the queued payload (one dequeue), update
        # state, store record. Drives I-UI-05.
        self.event_queue.dequeue()
        self.state = new_state
        self.latest_tick = record
        self.tick_counter += 1
        self.set_active_view("tick")
        self.set_status(
            f"tick {self.tick_counter} ok "
            f"({record.triggered_mode.name if record.triggered_mode else 'noop'})"
        )

    # ------------------------------------------------------------------
    # Bounded display contracts (used by the renderer / smoke tests)
    # ------------------------------------------------------------------

    def keyboard_help(self) -> tuple[tuple[str, str], ...]:
        """The closed keyboard map. Matches the renderer's help pane.

        Drives ``I-UI-13``: the keyboard map is a finite enumeration
        that matches the help pane.
        """
        return DEFAULT_KEYBOARD_HELP

    def queued_event_summary(self) -> tuple[str, ...]:
        """Bounded printable summary of the head-of-queue payload."""
        payload = self.event_queue.peek()
        if payload is None:
            return ()
        return payload.summary()


__all__ = [
    "DEFAULT_EVENT_QUEUE_LIMIT",
    "MAX_STATUS_TEXT_LEN",
    "OperatorEventQueue",
    "OperatorSession",
]
