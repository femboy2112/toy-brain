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
from fractions import Fraction
from typing import TYPE_CHECKING, Optional

from brain.development.text_stream import (
    STREAM_PROMOTION_MAX,
    StreamPromotionCandidate,
    TextStreamHistory,
    TextStreamSource,
    make_stream_promotion_candidate,
    make_text_stream_chunk,
)
from brain.tick import BrainState, tick
from brain.ui.commands import (
    INSPECT_VIEW_MAP,
    Command,
    OperatorCommand,
    QueuePerceptPayload,
    StreamAppendPayload,
    StreamPromotePayload,
)
from brain.ui.render import DEFAULT_KEYBOARD_HELP
from brain.ui.snapshot import ACTIVE_VIEWS

if TYPE_CHECKING:  # pragma: no cover - typing-only imports
    from brain.development.output import OutputHistory
    from brain.development.repl import ProtoBasicHistory
    from brain.development.worldlet import WorldletHistory
    from brain.io_types import TickRecord
    from brain.llm.client import LLMClient
    from brain.toce_core import ContentState
    from brain.ui.persistence import SessionStoreConfig


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
    "stream_history",
    "stream_candidates",
    "stream_chunk_serial",
    "session_store_config",
})


# Defaults for converting StreamPromotionCandidate -> QueuePerceptPayload.
# The constants are local to the stream-promote bridge and are matched
# against the LocalCommandLine defaults by the constant-parity fixture
# (``stream_constant_parity.py``).
_STREAM_PROMOTE_DEFAULT_RHO = Fraction(1, 2)


def _stream_promote_default_content_state() -> "ContentState":
    from brain.toce_core import ContentState as _ContentState
    return _ContentState(
        available=True,
        verification_path=True,
        retrievable=True,
        operative=True,
    )


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
    stream_history: TextStreamHistory = field(default_factory=TextStreamHistory)
    stream_candidates: tuple[StreamPromotionCandidate, ...] = ()
    stream_chunk_serial: int = 0
    session_store_config: Optional["SessionStoreConfig"] = None

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
        if not isinstance(self.stream_history, TextStreamHistory):
            raise TypeError(
                "OperatorSession.stream_history must be a TextStreamHistory "
                f"(got {type(self.stream_history).__name__})"
            )
        if not isinstance(self.stream_candidates, tuple):
            raise TypeError(
                "OperatorSession.stream_candidates must be a tuple "
                f"(got {type(self.stream_candidates).__name__})"
            )
        for cand in self.stream_candidates:
            if not isinstance(cand, StreamPromotionCandidate):
                raise TypeError(
                    "OperatorSession.stream_candidates entries must be "
                    f"StreamPromotionCandidate (got {type(cand).__name__})"
                )
        if len(self.stream_candidates) > STREAM_PROMOTION_MAX:
            raise ValueError(
                "I-UISTRM-11 violated: stream_candidates length "
                f"{len(self.stream_candidates)} exceeds STREAM_PROMOTION_MAX="
                f"{STREAM_PROMOTION_MAX}"
            )
        if (
            not isinstance(self.stream_chunk_serial, int)
            or self.stream_chunk_serial < 0
        ):
            raise ValueError(
                "OperatorSession.stream_chunk_serial must be a non-negative int "
                f"(got {self.stream_chunk_serial!r})"
            )
        if self.session_store_config is not None:
            # Local import avoids a brain.ui.session <-> brain.ui.persistence
            # module-load cycle. SessionStoreConfig is a frozen / slotted
            # record carrying only bounded primitives + a pathlib.Path
            # (drives I-PERSIST-11 / I-PERSIST-14: no sqlite3.Connection
            # may live on OperatorSession).
            from brain.ui.persistence import SessionStoreConfig as _Config
            if not isinstance(self.session_store_config, _Config):
                raise TypeError(
                    "OperatorSession.session_store_config must be a "
                    "SessionStoreConfig or None "
                    f"(got {type(self.session_store_config).__name__})"
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

        # A new valid command attempt supersedes any prior local UI
        # error. Failure handlers below set a fresh error if this
        # command is rejected; success paths must not leave a stale error
        # visible in the transcript/footer.
        self.error_message = ""

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
        elif kind is OperatorCommand.STREAM_APPEND:
            self._dispatch_stream_append(command.payload)
        elif kind is OperatorCommand.STREAM_PROMOTE:
            self._dispatch_stream_promote(command.payload)
        elif kind is OperatorCommand.SAVE_SESSION:
            self._dispatch_save_session()
        elif kind is OperatorCommand.LOAD_SESSION:
            self._dispatch_load_session()
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
    # Stream-command handlers (Phase 3.8)
    # ------------------------------------------------------------------

    def _next_stream_chunk_id(self) -> str:
        """Return a deterministic non-reserved chunk_id for the next /stream.

        Uses the session-owned ``stream_chunk_serial`` counter so each
        append produces a unique bounded printable identifier. The
        counter is incremented as part of a successful append; the id
        format ``"strm-chunk-N"`` is short enough to satisfy the
        Phase 3.7 substrate bounds and is never equal to ``COGITO_ID``.
        """
        return f"strm-chunk-{self.stream_chunk_serial + 1}"

    def _append_stream_candidates(
        self, new_candidates: tuple[StreamPromotionCandidate, ...]
    ) -> None:
        combined = self.stream_candidates + tuple(new_candidates)
        if len(combined) > STREAM_PROMOTION_MAX:
            combined = combined[-STREAM_PROMOTION_MAX:]
        self.stream_candidates = combined

    def _dispatch_stream_append(
        self, payload: Optional[StreamAppendPayload]
    ) -> None:
        if not isinstance(payload, StreamAppendPayload):
            self.set_error("STREAM_APPEND requires a StreamAppendPayload")
            return

        prior_history = self.stream_history
        prior_candidates = self.stream_candidates
        prior_serial = self.stream_chunk_serial

        chunk_id = self._next_stream_chunk_id()
        try:
            chunk = make_text_stream_chunk(
                chunk_id=chunk_id,
                text=payload.text,
                source=TextStreamSource.OPERATOR,
                provenance="operator",
            )
        except (TypeError, ValueError) as exc:
            self.set_error(f"stream append rejected: {exc}")
            assert self.stream_history is prior_history
            assert self.stream_candidates == prior_candidates
            assert self.stream_chunk_serial == prior_serial
            return

        try:
            new_history = prior_history.append(chunk)
            candidate = make_stream_promotion_candidate(
                candidate_id=f"promo-{chunk.chunk_id}",
                target_content_id=f"strm-{chunk.chunk_id}",
                source=chunk.source,
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                provenance=chunk.provenance,
            )
        except (TypeError, ValueError) as exc:
            self.set_error(f"stream append rejected: {exc}")
            assert self.stream_history is prior_history
            assert self.stream_candidates == prior_candidates
            assert self.stream_chunk_serial == prior_serial
            return

        self.stream_history = new_history
        self._append_stream_candidates((candidate,))
        self.stream_chunk_serial = prior_serial + 1
        self.set_active_view("stream_summary")
        self.set_status(
            f"stream chunk {chunk.chunk_id!r} appended "
            f"(history size = {len(new_history.chunks)})"
        )

    def _resolve_stream_candidate(
        self, candidate_id: str
    ) -> Optional[StreamPromotionCandidate]:
        for cand in self.stream_candidates:
            if cand.candidate_id == candidate_id:
                return cand
        return None

    def _dispatch_stream_promote(
        self, payload: Optional[StreamPromotePayload]
    ) -> None:
        if not isinstance(payload, StreamPromotePayload):
            self.set_error("STREAM_PROMOTE requires a StreamPromotePayload")
            return

        prior_history = self.stream_history
        prior_candidates = self.stream_candidates
        prior_state = self.state
        prior_latest_tick = self.latest_tick
        prior_queue_size = len(self.event_queue)
        prior_tick_counter = self.tick_counter
        prior_serial = self.stream_chunk_serial

        candidate = self._resolve_stream_candidate(payload.candidate_id)
        if candidate is None:
            self.set_error(
                f"unknown stream candidate: {payload.candidate_id!r}"
            )
            assert self.stream_history is prior_history
            assert self.stream_candidates == prior_candidates
            assert self.state is prior_state
            assert self.latest_tick is prior_latest_tick
            assert len(self.event_queue) == prior_queue_size
            assert self.tick_counter == prior_tick_counter
            assert self.stream_chunk_serial == prior_serial
            return

        if self.event_queue.is_full():
            self.set_error(
                f"event queue full (limit={self.event_queue.limit})"
            )
            assert self.stream_history is prior_history
            assert self.stream_candidates == prior_candidates
            assert self.state is prior_state
            assert self.latest_tick is prior_latest_tick
            assert len(self.event_queue) == prior_queue_size
            assert self.tick_counter == prior_tick_counter
            assert self.stream_chunk_serial == prior_serial
            return

        try:
            queue_payload = QueuePerceptPayload(
                content_id=candidate.target_content_id,
                text=candidate.text,
                content_state=_stream_promote_default_content_state(),
                initial_rho=_STREAM_PROMOTE_DEFAULT_RHO,
            )
        except (TypeError, ValueError) as exc:
            self.set_error(f"stream-promote rejected: {exc}")
            assert self.stream_history is prior_history
            assert self.stream_candidates == prior_candidates
            assert self.state is prior_state
            assert self.latest_tick is prior_latest_tick
            assert len(self.event_queue) == prior_queue_size
            assert self.tick_counter == prior_tick_counter
            assert self.stream_chunk_serial == prior_serial
            return

        try:
            self.event_queue.enqueue(queue_payload)
        except (TypeError, ValueError, OverflowError) as exc:
            self.set_error(f"queue rejected promotion: {exc}")
            assert self.stream_history is prior_history
            assert self.stream_candidates == prior_candidates
            assert self.state is prior_state
            assert self.latest_tick is prior_latest_tick
            assert len(self.event_queue) == prior_queue_size
            assert self.tick_counter == prior_tick_counter
            assert self.stream_chunk_serial == prior_serial
            return

        # Success: leave stream state intact except for view/status; the
        # /step path consumes the queued payload through the existing
        # _dispatch_step route. Stream history, candidates, and serial
        # are not consumed here.
        self.set_active_view("queue")
        self.set_status(
            f"promoted stream candidate {candidate.candidate_id!r} "
            f"(queue size = {len(self.event_queue)})"
        )

    # ------------------------------------------------------------------
    # /save-session and /load-session — explicit persistence dispatchers
    # (drive I-PERSIST-09). Both routes are local: no tick() call, no
    # event_queue mutation, no stream-history mutation. Failure paths
    # surface as bounded local error text only.
    # ------------------------------------------------------------------

    def _dispatch_save_session(self) -> None:
        config = self.session_store_config
        if config is None:
            self.set_error(
                "/save-session requires a configured --session-db"
            )
            return
        # Lazy import keeps the brain.ui.session <-> brain.ui.persistence
        # module-load order acyclic.
        from brain.ui.persistence import (  # noqa: PLC0415
            PersistenceError,
            save_session,
        )
        try:
            result = save_session(self, config)
        except PersistenceError as exc:
            self.set_error(f"/save-session failed: {exc}")
            return
        self.set_status(
            f"saved session to {result.db_path!s} "
            f"(chunks={result.saved_chunks}, "
            f"candidates={result.saved_candidates})"
        )

    def _dispatch_load_session(self) -> None:
        config = self.session_store_config
        if config is None:
            self.set_error(
                "/load-session requires a configured --session-db"
            )
            return
        from brain.ui.persistence import (  # noqa: PLC0415
            PersistenceError,
            load_session,
        )
        try:
            candidate, result = load_session(config)
        except PersistenceError as exc:
            self.set_error(f"/load-session failed: {exc}")
            return
        # Apply the candidate's kernel + stream state in-place. This is
        # the controlled swap routine documented in the kickoff section
        # 9: we copy the loaded immutable fields onto the live session
        # so live wrappers (curses, transcripts) keep their identity.
        # Status / error / active_view / event_queue are intentionally
        # preserved across loads -- they belong to the live operator
        # surface, not the persisted snapshot.
        self.state = candidate.state
        self.tick_counter = candidate.tick_counter
        self.stream_history = candidate.stream_history
        self.stream_candidates = candidate.stream_candidates
        self.stream_chunk_serial = candidate.stream_chunk_serial
        self.set_status(
            f"loaded session from {result.db_path!s} "
            f"(chunks={result.loaded_chunks}, "
            f"candidates={result.loaded_candidates}"
            + (", rebuilt=true" if result.rebuilt_candidates else "")
            + ")"
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


# Convenience accessors for fixtures and the constant-parity audit.
STREAM_PROMOTE_DEFAULT_RHO: Fraction = _STREAM_PROMOTE_DEFAULT_RHO
