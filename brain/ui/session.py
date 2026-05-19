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

from brain.development.growth_ledger import (
    GrowthEventSource,
    GrowthEventType,
    GrowthLedger,
)
from brain.development.pattern_ledger import (
    PatternLedger,
    derive_pattern_id,
    derive_pattern_signature,
)
from brain.development.processing_window import (
    FeedbackMode,
    InternalEventSource,
    WORLDLET_SUMMARY_ABSENT_SENTINEL,
    build_cohmon_summary_text,
    build_pledger_summary_text,
    build_rehearsal_provenance,
    build_worldlet_summary_text,
    plan_rehearsals,
    validate_feedback_mode,
    validate_processing_window_call_budget,
    validate_processing_window_size,
)
from brain.development.text_stream import (
    STREAM_PROMOTION_MAX,
    StreamPromotionCandidate,
    TextStreamChunk,
    TextStreamHistory,
    TextStreamSource,
    make_stream_promotion_candidate,
    make_text_stream_chunk,
)
from brain.tick import BrainState, tick
from brain.ui.commands import (
    INSPECT_VIEW_MAP,
    Command,
    DbBackupPayload,
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
    from brain.ui.autosave import AutosaveConfig, AutosaveStatusReport
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
    "autosave_config",
    "last_autosave_status",
    "pattern_ledger",
    "growth_ledger",
    "processing_window_size",
    "processing_window_call_budget",
    "feedback_mode",
    # Phase 3.23 dispatch tracer (I-DTRACE-03): single-slot post-action
    # record carrying the bounded DispatchTraceReport produced by the
    # most recent OperatorSession.dispatch call. The precedent is
    # last_autosave_status (Phase 3.10c).
    "latest_dispatch_trace",
})


# Defaults for converting StreamPromotionCandidate -> QueuePerceptPayload.
# The constants are local to the stream-promote bridge and are matched
# against the LocalCommandLine defaults by the constant-parity fixture
# (``stream_constant_parity.py``).
_STREAM_PROMOTE_DEFAULT_RHO = Fraction(1, 2)


# Phase 3.24 worldlet-pushback reason set, mirrored inline. Matches
# ``brain.development.worldlet.WORLDLET_PUSHBACK_REASONS`` exactly; we
# mirror the closed set here so ``_run_worldlet_feedback_step`` can
# compute the bounded pushback count without importing the worldlet
# substrate at module load time (the substrate is only typing-imported
# above). The pattern mirrors the deferred-import discipline used for
# ``build_full_coherence_report`` in ``_run_cohmon_feedback_step``.
_WORLDLET_PUSHBACK_REASONS_SESSION: frozenset[str] = frozenset({
    "missing-target",
    "rejected",
    "target-unavailable",
})


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
    autosave_config: Optional["AutosaveConfig"] = None
    last_autosave_status: Optional["AutosaveStatusReport"] = None
    pattern_ledger: PatternLedger = field(default_factory=PatternLedger)
    growth_ledger: GrowthLedger = field(default_factory=GrowthLedger)
    # Phase 3.18 processing-window controls. Defaults are 0 / OFF so
    # every existing test, fixture, and CLI invocation behaves bit-
    # identically to the pre-Phase-3.18 runtime. Operators opt in by
    # setting ``processing_window_size`` to a positive int (bounded
    # by ``brain.development.processing_window.PROCESSING_WINDOW_SIZE_MAX``).
    processing_window_size: int = 0
    processing_window_call_budget: int = 0
    # Phase 3.19 internal-feedback control. Default
    # ``FeedbackMode.OFF`` so the rehearsal-only path is preserved
    # bit-identically. Operators opt into pattern-ledger feedback
    # by setting this to ``FeedbackMode.PATTERN_LEDGER``.
    feedback_mode: FeedbackMode = FeedbackMode.OFF
    # Phase 3.23 dispatch tracer (I-DTRACE-03): single-slot post-action
    # record carrying the bounded DispatchTraceReport produced by the
    # most recent OperatorSession.dispatch call. None until the first
    # dispatch lands; the dispatch() handler assigns a fresh report on
    # every non-NOOP / NOOP / error path. The report is a frozen / slotted
    # record without any unsafe resource handle so the I-UI-10 self-audit
    # is preserved.
    latest_dispatch_trace: Optional["DispatchTraceReport"] = None

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
        if self.autosave_config is not None:
            # Local import keeps the brain.ui.session <-> brain.ui.autosave
            # ordering acyclic. AutosaveConfig is a frozen / slotted
            # record carrying only bounded primitives (drives I-AUTOSAVE-14:
            # no sqlite3.Connection, Cursor, callable, socket, subprocess
            # handle, file object, curses object, or LLM client appears
            # in the autosave fields).
            from brain.ui.autosave import AutosaveConfig as _AutosaveConfig
            if not isinstance(self.autosave_config, _AutosaveConfig):
                raise TypeError(
                    "OperatorSession.autosave_config must be an "
                    "AutosaveConfig or None "
                    f"(got {type(self.autosave_config).__name__})"
                )
        if self.last_autosave_status is not None:
            from brain.ui.autosave import (
                AutosaveStatusReport as _AutosaveStatusReport,
            )
            if not isinstance(
                self.last_autosave_status, _AutosaveStatusReport
            ):
                raise TypeError(
                    "OperatorSession.last_autosave_status must be an "
                    "AutosaveStatusReport or None "
                    f"(got {type(self.last_autosave_status).__name__})"
                )
        if not isinstance(self.pattern_ledger, PatternLedger):
            raise TypeError(
                "OperatorSession.pattern_ledger must be a PatternLedger "
                f"(got {type(self.pattern_ledger).__name__})"
            )
        if not isinstance(self.growth_ledger, GrowthLedger):
            raise TypeError(
                "OperatorSession.growth_ledger must be a GrowthLedger "
                f"(got {type(self.growth_ledger).__name__})"
            )
        # Phase 3.18 processing-window field validation. Delegates to
        # the bounded validators in brain.development.processing_window
        # so the range / type discipline lives next to the constants.
        object.__setattr__(
            self,
            "processing_window_size",
            validate_processing_window_size(self.processing_window_size),
        )
        object.__setattr__(
            self,
            "processing_window_call_budget",
            validate_processing_window_call_budget(
                self.processing_window_call_budget
            ),
        )
        # Phase 3.19 feedback-mode field validation.
        object.__setattr__(
            self,
            "feedback_mode",
            validate_feedback_mode(self.feedback_mode),
        )
        # Phase 3.23 dispatch tracer field validation (I-DTRACE-03).
        # The dispatch tracer module is imported lazily here to keep
        # the brain.ui.session <-> brain.development.dispatch_tracer
        # <-> brain.development.coherence_monitor module-load order
        # acyclic. ``DispatchTraceReport`` is a frozen / slotted record
        # carrying only bounded primitives and a ``DispatchTrace`` (in
        # turn a tuple of frozen / slotted ``DispatchTraceStep``
        # records). It exposes no callable, no file handle, no socket,
        # no subprocess handle, and no LLM-client surface, so the
        # I-UI-10 self-audit accepts it as-is.
        if self.latest_dispatch_trace is not None:
            from brain.development.dispatch_tracer import (  # noqa: PLC0415
                DispatchTraceReport as _DispatchTraceReport,
            )
            if not isinstance(
                self.latest_dispatch_trace, _DispatchTraceReport
            ):
                raise TypeError(
                    "OperatorSession.latest_dispatch_trace must be a "
                    "DispatchTraceReport or None "
                    f"(got {type(self.latest_dispatch_trace).__name__})"
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

        Phase 3.23 (I-DTRACE-03..07): every dispatch builds a bounded
        :class:`DispatchTraceReport` and assigns it to
        :attr:`latest_dispatch_trace`. The trace records the command
        kind, route label, pre/post substrate facts, mutation kind,
        autosave consideration, and resource audit outcome. Existing
        semantics (the ``None`` return, the autosave trigger contract,
        the I-UI-10 self-audit, kernel-side invariance on failure) are
        preserved bit-identically.
        """
        if not isinstance(command, Command):
            raise TypeError(
                "OperatorSession.dispatch requires a Command "
                f"(got {type(command).__name__})"
            )

        # Lazy import: keeps the brain.ui.session <-> dispatch_tracer
        # <-> coherence_monitor module-load order acyclic.
        from brain.development.dispatch_tracer import (  # noqa: PLC0415
            DispatchMutationKind,
            DispatchTraceKind,
            DispatchTraceStatus,
            build_dispatch_trace_report,
            new_dispatch_trace_builder,
        )

        # A new valid command attempt supersedes any prior local UI
        # error. Failure handlers below set a fresh error if this
        # command is rejected; success paths must not leave a stale error
        # visible in the transcript/footer.
        self.error_message = ""

        # Outcome-detection contract (drives I-AUTOSAVE-14): a Phase
        # 3.10c-eligible dispatcher returns True iff it mutated kernel /
        # stream state, False iff it failed, None for read-only paths.
        # The central dispatch reads this return value to decide whether
        # to fire the post-dispatch autosave hook; it never scans status
        # / error strings.
        mutation_outcome: Optional[bool] = None

        kind = command.kind
        kind_value = kind.value if isinstance(kind, OperatorCommand) else str(kind)
        route_label, planned_mutation_kind = _classify_dispatch_route(kind)
        handler_method_name = _dispatch_handler_method_name(kind)

        # Phase 3.23 dispatch tracer (I-DTRACE-03): open a bounded
        # trace builder for this dispatch. The interaction_id is
        # synthesized deterministically from bounded session counters
        # so two sessions advanced by the same command sequence produce
        # equal dispatch trace digests at each step.
        interaction_id = self._dispatch_trace_interaction_id(kind_value)
        builder = new_dispatch_trace_builder(interaction_id)
        builder.add(
            DispatchTraceKind.COMMAND_RECEIVED,
            command_kind=kind_value,
            mutation_kind=DispatchMutationKind.NONE,
            status=DispatchTraceStatus.NOT_APPLICABLE,
            route_label=route_label,
            derived_facts=f"command kind received: {kind_value}",
            digest_contribution=f"cmd:{kind_value}",
        )
        builder.add(
            DispatchTraceKind.ROUTE_SELECTED,
            command_kind=kind_value,
            mutation_kind=DispatchMutationKind.NONE,
            status=DispatchTraceStatus.NOT_APPLICABLE,
            route_label=route_label,
            derived_facts=f"route_label={route_label}",
            digest_contribution=f"route:{route_label}",
        )
        pre_facts = self._dispatch_trace_pre_facts()
        builder.add(
            DispatchTraceKind.PRE_STATE_SNAPSHOT,
            command_kind=kind_value,
            mutation_kind=DispatchMutationKind.NONE,
            status=DispatchTraceStatus.NOT_APPLICABLE,
            route_label=route_label,
            before_facts=pre_facts,
            derived_facts="pre-state captured",
            digest_contribution="pre-state",
        )

        if kind is OperatorCommand.NOOP:
            # Explicit no-op: leave session state unchanged. Drives the
            # "every command kind is handled" branch of I-UI-03. The
            # dispatch trace records the no-op route without firing the
            # autosave hook or the self-audit (the early return path
            # preserves the historical behavior bit-identically).
            builder.add(
                DispatchTraceKind.NOOP_RECORDED,
                command_kind=kind_value,
                mutation_kind=DispatchMutationKind.NONE,
                status=DispatchTraceStatus.NOT_APPLICABLE,
                route_label=route_label,
                derived_facts="noop-early-return",
                digest_contribution="noop",
            )
            builder.add(
                DispatchTraceKind.TRACE_FINALIZED,
                command_kind=kind_value,
                mutation_kind=DispatchMutationKind.NONE,
                status=DispatchTraceStatus.NOT_APPLICABLE,
                route_label=route_label,
                derived_facts="trace-finalized",
                digest_contribution="trace-finalized",
            )
            self.latest_dispatch_trace = build_dispatch_trace_report(
                builder.freeze()
            )
            return

        builder.add(
            DispatchTraceKind.HANDLER_ENTERED,
            command_kind=kind_value,
            mutation_kind=DispatchMutationKind.NONE,
            status=DispatchTraceStatus.NOT_APPLICABLE,
            route_label=route_label,
            derived_facts=f"handler={handler_method_name}",
            digest_contribution=f"handler-enter:{handler_method_name}",
        )

        # ----- existing handler tree (semantics unchanged) -----
        if kind in INSPECT_VIEW_MAP:
            self.set_active_view(INSPECT_VIEW_MAP[kind])
            self.set_status(f"view = {INSPECT_VIEW_MAP[kind]}")
        elif kind is OperatorCommand.QUEUE_PERCEPT:
            self._dispatch_queue(command.payload)
        elif kind is OperatorCommand.STEP_TICK:
            mutation_outcome = self._dispatch_step(client)
        elif kind is OperatorCommand.CLEAR_STATUS:
            self.clear_status()
        elif kind is OperatorCommand.HELP:
            self.set_active_view("help")
            self.set_status("help")
        elif kind is OperatorCommand.QUIT:
            self.quit_flag = True
            self.set_status("quit")
        elif kind is OperatorCommand.STREAM_APPEND:
            appended_chunk = self._dispatch_stream_append(command.payload)
            # Phase 3.18 I-PWND-01: after a successful external stream
            # append, run the bounded internal rehearsal window (no-op
            # at the default OFF size of 0). The window does not
            # affect the autosave trigger contract (which is keyed on
            # STEP_TICK / STREAM_PROMOTE, not STREAM_APPEND) and does
            # not change ``mutation_outcome``.
            if appended_chunk is not None:
                self._run_processing_window(seed_chunk=appended_chunk)
        elif kind is OperatorCommand.STREAM_PROMOTE:
            mutation_outcome = self._dispatch_stream_promote(
                command.payload
            )
        elif kind is OperatorCommand.SAVE_SESSION:
            self._dispatch_save_session()
        elif kind is OperatorCommand.LOAD_SESSION:
            self._dispatch_load_session()
        elif kind is OperatorCommand.SESSION_STATUS:
            self._dispatch_session_status()
        elif kind is OperatorCommand.DB_STATUS:
            self._dispatch_db_status()
        elif kind is OperatorCommand.DB_VERIFY:
            self._dispatch_db_verify()
        elif kind is OperatorCommand.DB_BACKUP:
            self._dispatch_db_backup(command.payload)
        elif kind is OperatorCommand.DB_SUMMARY:
            self._dispatch_db_summary()
        elif kind is OperatorCommand.PROFILE_SUMMARY:
            self._dispatch_profile_summary()
        elif kind is OperatorCommand.STREAM_DB_SUMMARY:
            self._dispatch_stream_db_summary()
        elif kind is OperatorCommand.DB_DIFF:
            self._dispatch_db_diff()
        elif kind is OperatorCommand.AUTOSAVE_STATUS:
            self._dispatch_autosave_status()
        elif kind is OperatorCommand.AUTOSAVE_ENABLE:
            self._dispatch_autosave_enable(command.payload)
        elif kind is OperatorCommand.AUTOSAVE_DISABLE:
            self._dispatch_autosave_disable()
        else:  # pragma: no cover - the enum is closed
            raise AssertionError(
                f"I-UI-03 violated: unrouted OperatorCommand {kind!r}"
            )

        # ----- handler returned -----
        handler_outcome_label = _handler_outcome_label(
            mutation_outcome=mutation_outcome,
            error_present=bool(self.error_message),
        )
        builder.add(
            DispatchTraceKind.HANDLER_RETURNED,
            command_kind=kind_value,
            mutation_kind=DispatchMutationKind.NONE,
            status=DispatchTraceStatus.NOT_APPLICABLE,
            route_label=route_label,
            derived_facts=f"outcome={handler_outcome_label}",
            digest_contribution=f"handler-return:{handler_outcome_label}",
        )
        post_facts = self._dispatch_trace_post_facts()
        builder.add(
            DispatchTraceKind.POST_STATE_SNAPSHOT,
            command_kind=kind_value,
            mutation_kind=DispatchMutationKind.NONE,
            status=DispatchTraceStatus.NOT_APPLICABLE,
            route_label=route_label,
            after_facts=post_facts,
            derived_facts="post-state captured",
            digest_contribution="post-state",
        )

        # Classify the mutation actually observed.
        error_present = bool(self.error_message)
        if error_present:
            actual_mutation_kind = DispatchMutationKind.ERROR_ONLY
            mutation_status = DispatchTraceStatus.FAIL
            builder.add(
                DispatchTraceKind.ERROR_RECORDED,
                command_kind=kind_value,
                mutation_kind=DispatchMutationKind.ERROR_ONLY,
                status=DispatchTraceStatus.FAIL,
                route_label=route_label,
                derived_facts="error_message non-empty after handler",
                digest_contribution="error",
            )
        else:
            actual_mutation_kind = _refine_stream_append_mutation_kind(
                planned=planned_mutation_kind,
                pre_facts=pre_facts,
                post_facts=post_facts,
            )
            mutation_status = DispatchTraceStatus.PASS
        builder.add(
            DispatchTraceKind.MUTATION_CLASSIFIED,
            command_kind=kind_value,
            mutation_kind=actual_mutation_kind,
            status=mutation_status,
            route_label=route_label,
            derived_facts=f"mutation_kind={actual_mutation_kind.value}",
            digest_contribution=f"mut:{actual_mutation_kind.value}",
        )

        # Post-dispatch autosave trigger (drives I-AUTOSAVE-08,
        # I-AUTOSAVE-09, I-AUTOSAVE-10). Fires only when:
        #   (a) autosave_config is configured and non-OFF,
        #   (b) command kind is in the Phase 3.10c-eligible trigger set,
        #   (c) the sub-dispatcher returned True (mutated kernel state),
        #   (d) session_store_config is configured.
        # The returned typed report (or None) is stored on
        # session.last_autosave_status. The helper itself never raises.
        autosave_before = self.last_autosave_status
        self._maybe_autosave_after_dispatch(kind, mutation_outcome)
        autosave_outcome = _classify_autosave_outcome(
            autosave_config=self.autosave_config,
            session_store_config=self.session_store_config,
            mutation_outcome=mutation_outcome,
            kind=kind,
            autosave_before=autosave_before,
            autosave_after=self.last_autosave_status,
        )
        builder.add(
            DispatchTraceKind.AUTOSAVE_CHECKED,
            command_kind=kind_value,
            mutation_kind=DispatchMutationKind.NONE,
            status=DispatchTraceStatus.NOT_APPLICABLE,
            route_label=route_label,
            derived_facts=f"autosave={autosave_outcome}",
            digest_contribution=f"autosave:{autosave_outcome}",
        )

        # Self-audit after every dispatch so a buggy handler cannot
        # widen the session's resource surface unnoticed.
        self._assert_no_unsafe_resources()
        builder.add(
            DispatchTraceKind.RESOURCE_AUDIT_CHECKED,
            command_kind=kind_value,
            mutation_kind=DispatchMutationKind.NONE,
            status=DispatchTraceStatus.PASS,
            route_label=route_label,
            derived_facts="audit:ok",
            digest_contribution="audit:ok",
        )
        builder.add(
            DispatchTraceKind.TRACE_FINALIZED,
            command_kind=kind_value,
            mutation_kind=DispatchMutationKind.NONE,
            status=DispatchTraceStatus.NOT_APPLICABLE,
            route_label=route_label,
            derived_facts="trace-finalized",
            digest_contribution="trace-finalized",
        )
        self.latest_dispatch_trace = build_dispatch_trace_report(
            builder.freeze()
        )

    # ------------------------------------------------------------------
    # Phase 3.23 dispatch tracer helpers (I-DTRACE-03..07).
    # ------------------------------------------------------------------

    def _dispatch_trace_interaction_id(self, kind_value: str) -> str:
        """Synthesize a bounded deterministic interaction_id.

        Derived only from bounded session counters and the bounded
        command_kind value, so two sessions advanced by the same
        command sequence produce equal interaction_ids at each step.
        """
        synth = (
            f"dispatch:tc{self.tick_counter}:"
            f"ssc{self.stream_chunk_serial}:"
            f"sh{len(self.stream_history.chunks)}:"
            f"eq{len(self.event_queue)}:"
            f"cmd{kind_value}"
        )
        if len(synth) > 64:
            synth = synth[:60] + " ..."
        return synth

    def _dispatch_trace_pre_facts(
        self,
    ) -> tuple[tuple[str, str], ...]:
        """Bounded snapshot of session-side facts before a handler runs."""
        return self._dispatch_trace_session_facts()

    def _dispatch_trace_post_facts(
        self,
    ) -> tuple[tuple[str, str], ...]:
        """Bounded snapshot of session-side facts after a handler runs."""
        return self._dispatch_trace_session_facts()

    def _dispatch_trace_session_facts(
        self,
    ) -> tuple[tuple[str, str], ...]:
        return (
            ("active_view", self.active_view),
            ("event_queue_size", str(len(self.event_queue))),
            ("stream_history_len", str(len(self.stream_history.chunks))),
            ("stream_candidate_count", str(len(self.stream_candidates))),
            (
                "pattern_entry_count",
                str(len(self.pattern_ledger.entries)),
            ),
            (
                "growth_event_total",
                str(len(self.growth_ledger.events)),
            ),
            (
                "processing_window_size",
                str(self.processing_window_size),
            ),
            ("feedback_mode", self.feedback_mode.value),
            (
                "worldlet_summary_chunks",
                str(
                    sum(
                        1
                        for c in self.stream_history.chunks
                        if c.provenance.endswith(":worldlet_summary")
                    )
                ),
            ),
            ("tick_counter", str(self.tick_counter)),
            (
                "status_message_present",
                "1" if self.status_message else "0",
            ),
            (
                "error_message_present",
                "1" if self.error_message else "0",
            ),
        )

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

    def _dispatch_step(self, client: Optional["LLMClient"]) -> Optional[bool]:
        """Single-tick router. Drives ``I-UI-05`` and ``I-UI-06``.

        Pops one queued payload, rebuilds the :class:`PerceptEvent`,
        calls :func:`brain.tick.tick` exactly once, stores the returned
        :class:`TickRecord`, and replaces the session's
        :class:`BrainState` with the new state. Any exception during
        validation or tick is captured as local UI status / error;
        no kernel container is mutated on the failure path.

        Returns ``True`` iff the step succeeded (BrainState mutated +
        tick_counter advanced); returns ``False`` on any failure path.
        The central :meth:`dispatch` reads this return value to decide
        whether to fire the post-dispatch autosave hook (drives
        ``I-AUTOSAVE-14`` outcome-detection contract).
        """
        if client is None:
            self.set_error("STEP_TICK requires an LLM client argument")
            return False
        # Capture the pre-tick session snapshot so a failure path can
        # assert no kernel-side mutation occurred (drives I-UI-06).
        prior_state = self.state
        prior_latest_tick = self.latest_tick
        prior_queue_size = len(self.event_queue)

        if prior_queue_size == 0:
            self.set_error("STEP_TICK with empty event queue")
            return False

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
            return False

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
            return False

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
        # I-GROW-17: emit Growth Ledger events for the accepted tick
        # and any pre/post profile.domain / msi.contents additions.
        # The deltas come from prior_state captured at the start of
        # _dispatch_step and the new BrainState returned by tick(); no
        # status / error string is inspected. Removals do not emit
        # events in v1.
        self.growth_ledger = self.growth_ledger.observe(
            event_type=GrowthEventType.TICK_SUCCEEDED,
            tick=self.tick_counter,
            source=GrowthEventSource.STEP_DISPATCH,
            references=(f"tick-{record.tick_index}",),
            provenance="step_dispatch:_dispatch_step",
        )
        for content_id in sorted(
            new_state.profile.domain - prior_state.profile.domain
        ):
            self.growth_ledger = self.growth_ledger.observe(
                event_type=GrowthEventType.PROFILE_DOMAIN_ADDED,
                tick=self.tick_counter,
                source=GrowthEventSource.STEP_DISPATCH,
                references=(content_id,),
                provenance="step_dispatch:profile_delta",
            )
        for content_id in sorted(
            new_state.msi.contents - prior_state.msi.contents
        ):
            self.growth_ledger = self.growth_ledger.observe(
                event_type=GrowthEventType.MSI_MEMBER_ADDED,
                tick=self.tick_counter,
                source=GrowthEventSource.STEP_DISPATCH,
                references=(content_id,),
                provenance="step_dispatch:msi_delta",
            )
        return True

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
    ) -> Optional[TextStreamChunk]:
        """Operator-path /stream append.

        Returns the appended :class:`TextStreamChunk` on success, or
        ``None`` on failure. The caller (the top-level :meth:`dispatch`)
        reads the return value to decide whether to fire the Phase
        3.18 processing window (drives ``I-PWND-01``); the rest of the
        success path (active_view + status_message) remains here so
        existing operator UX is unchanged.
        """
        if not isinstance(payload, StreamAppendPayload):
            self.set_error("STREAM_APPEND requires a StreamAppendPayload")
            return None
        chunk = self._append_stream_chunk(
            text=payload.text,
            chunk_provenance="operator",
            growth_provenance="stream_append:_dispatch_stream_append",
        )
        if chunk is None:
            return None
        self.set_active_view("stream_summary")
        self.set_status(
            f"stream chunk {chunk.chunk_id!r} appended "
            f"(history size = {len(self.stream_history.chunks)})"
        )
        return chunk

    def _append_stream_chunk(
        self,
        *,
        text: str,
        chunk_provenance: str,
        growth_provenance: str,
    ) -> Optional[TextStreamChunk]:
        """Core stream-append helper shared by the operator path and
        the Phase 3.18 internal rehearsal path.

        Returns the appended :class:`TextStreamChunk` on success, or
        ``None`` on failure (with :attr:`error_message` set). On
        failure the kernel- and stream-side substrates are guaranteed
        unchanged.

        ``chunk_provenance`` is stamped into the constructed
        :class:`TextStreamChunk.provenance` field (drives
        ``I-PLEDGER-13``'s sole-trigger discipline and the Phase 3.18
        ``I-PWND-02`` provenance audit). ``growth_provenance`` is
        stamped into the emitted ``STREAM_CHUNK_ACCEPTED`` Growth
        Ledger event's bounded printable provenance field.
        """
        prior_history = self.stream_history
        prior_candidates = self.stream_candidates
        prior_serial = self.stream_chunk_serial

        chunk_id = self._next_stream_chunk_id()
        try:
            chunk = make_text_stream_chunk(
                chunk_id=chunk_id,
                text=text,
                source=TextStreamSource.OPERATOR,
                provenance=chunk_provenance,
            )
        except (TypeError, ValueError) as exc:
            self.set_error(f"stream append rejected: {exc}")
            assert self.stream_history is prior_history
            assert self.stream_candidates == prior_candidates
            assert self.stream_chunk_serial == prior_serial
            return None

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
            return None

        self.stream_history = new_history
        self._append_stream_candidates((candidate,))
        self.stream_chunk_serial = prior_serial + 1
        # I-PLEDGER-13: a successful /stream append is the sole v1
        # Pattern Ledger trigger. observe(...) is pure copy-on-write
        # and never reaches BrainState / MSI / PtCns / tick / LLM.
        prior_pattern_ledger = self.pattern_ledger
        self.pattern_ledger = self.pattern_ledger.observe(
            chunk,
            candidate,
            current_tick=self.tick_counter,
        )
        # I-GROW-15: emit Growth Ledger events for the accepted stream
        # append and (when applicable) the Pattern Ledger entry delta.
        # The created/updated distinction is derived from a pure tuple
        # comparison between prior_pattern_ledger.entries and
        # self.pattern_ledger.entries; no status-string parsing.
        self.growth_ledger = self.growth_ledger.observe(
            event_type=GrowthEventType.STREAM_CHUNK_ACCEPTED,
            tick=self.tick_counter,
            source=GrowthEventSource.STREAM_APPEND,
            references=(chunk.chunk_id,),
            provenance=growth_provenance,
        )
        prior_recurrence_by_id: dict[str, int] = {
            entry.pattern_id: entry.recurrence_count
            for entry in prior_pattern_ledger.entries
        }
        for entry in self.pattern_ledger.entries:
            if entry.pattern_id not in prior_recurrence_by_id:
                self.growth_ledger = self.growth_ledger.observe(
                    event_type=GrowthEventType.PATTERN_ENTRY_CREATED,
                    tick=self.tick_counter,
                    source=GrowthEventSource.PATTERN_LEDGER_OBSERVE,
                    references=(entry.pattern_id,),
                    provenance="pattern_ledger:observe",
                )
            elif entry.recurrence_count > prior_recurrence_by_id[entry.pattern_id]:
                self.growth_ledger = self.growth_ledger.observe(
                    event_type=GrowthEventType.PATTERN_ENTRY_UPDATED,
                    tick=self.tick_counter,
                    source=GrowthEventSource.PATTERN_LEDGER_OBSERVE,
                    references=(entry.pattern_id,),
                    provenance="pattern_ledger:observe",
                )
        return chunk

    def _run_processing_window(
        self, *, seed_chunk: TextStreamChunk
    ) -> int:
        """Phase 3.18 architecture A rehearsal loop, extended by
        Phase 3.19 with bounded internal feedback.

        After a successful external STREAM_APPEND, fire up to
        :attr:`processing_window_size` internal rehearsals whose text
        is the EXACT text of ``seed_chunk`` and whose provenance is
        ``"internal_processing_window:<k>:rehearsal"``. Each rehearsal
        goes through :meth:`_append_stream_chunk`, so the Pattern
        Ledger trigger and the Growth Ledger emission path are
        identical to the operator path — only the bounded printable
        provenance strings differ.

        Phase 3.19 addition: when
        :attr:`feedback_mode` is
        :class:`brain.development.processing_window.FeedbackMode.PATTERN_LEDGER`,
        each rehearsal is followed by one deterministic Pattern
        Ledger summary chunk produced by
        :func:`brain.development.processing_window.build_pledger_summary_text`
        and dispatched through the same
        :meth:`_append_stream_chunk` helper under provenance
        ``"internal_processing_window:<k>:pledger_summary"``. The
        summary text has a structurally distinct signature from the
        seed text, so Pattern Ledger.observe records a SECOND-ORDER
        entry. The feedback path consumes zero real model calls
        because STREAM_APPEND does not invoke ``brain.tick.tick`` or
        the LLM.

        Returns the number of internal rehearsals that actually fired
        (each rehearsal counts as 1 regardless of whether the paired
        feedback chunk fired, mirroring Phase 3.18 accounting).
        Drives ``I-PWND-01`` and ``I-IFBK-01``: at OFF (size == 0)
        the call is a no-op and returns 0; otherwise the call is
        synchronous, bounded, and consumes zero real model calls.

        Failure semantics: if a rehearsal's
        :meth:`_append_stream_chunk` returns ``None``, the loop
        stops; :attr:`error_message` carries the failure reason. If
        a feedback chunk's :meth:`_append_stream_chunk` returns
        ``None``, the rehearsal is still counted, the failure is
        recorded, and the loop stops. The external operator status
        message (set by the caller) is preserved.
        """
        n = self.processing_window_size
        if n <= 0:
            return 0
        try:
            plan = plan_rehearsals(seed_text=seed_chunk.text, window_size=n)
        except (TypeError, ValueError) as exc:
            self.set_error(f"processing window plan rejected: {exc}")
            return 0
        pledger_feedback_enabled = self.feedback_mode in (
            FeedbackMode.PATTERN_LEDGER,
            FeedbackMode.PATTERN_AND_COHERENCE,
            FeedbackMode.PATTERN_COHERENCE_WORLDLET,
        )
        cohmon_feedback_enabled = self.feedback_mode in (
            FeedbackMode.COHERENCE,
            FeedbackMode.PATTERN_AND_COHERENCE,
            FeedbackMode.PATTERN_COHERENCE_WORLDLET,
        )
        worldlet_feedback_enabled = self.feedback_mode in (
            FeedbackMode.WORLDLET,
            FeedbackMode.PATTERN_COHERENCE_WORLDLET,
        )
        seed_pattern_id: Optional[str] = None
        if pledger_feedback_enabled:
            seed_pattern_id = derive_pattern_id(
                derive_pattern_signature(seed_chunk)
            )
        fired = 0
        for step in plan:
            chunk = self._append_stream_chunk(
                text=step.text,
                chunk_provenance=step.provenance,
                growth_provenance="stream_append:_run_processing_window",
            )
            if chunk is None:
                # A bounded substrate refused the rehearsal (e.g., a
                # text_stream length bound or a chunk_id collision).
                # error_message is already set; abort the window
                # cleanly without retrying.
                break
            fired += 1
            if pledger_feedback_enabled:
                if not self._run_feedback_step(
                    tick_index=step.tick_index,
                    seed_pattern_id=seed_pattern_id,
                ):
                    # A bounded substrate refused the pledger
                    # feedback chunk; error_message is set by
                    # _append_stream_chunk or the helper. Abort
                    # the window cleanly.
                    break
            if cohmon_feedback_enabled:
                if not self._run_cohmon_feedback_step(
                    tick_index=step.tick_index,
                ):
                    # A bounded substrate refused the cohmon
                    # feedback chunk; error_message is set by
                    # _append_stream_chunk or the helper. Abort
                    # the window cleanly.
                    break
            if worldlet_feedback_enabled:
                if not self._run_worldlet_feedback_step(
                    tick_index=step.tick_index,
                ):
                    # A bounded substrate refused the worldlet
                    # feedback chunk; error_message is set by
                    # _append_stream_chunk or the helper. Abort
                    # the window cleanly.
                    break
        return fired

    def _run_feedback_step(
        self,
        *,
        tick_index: int,
        seed_pattern_id: Optional[str],
    ) -> bool:
        """Fire one Phase 3.19 pattern-ledger feedback chunk.

        Looks up the just-updated seed Pattern Ledger entry, builds
        the deterministic summary text, composes the
        ``pledger_summary`` provenance, and dispatches the chunk
        through :meth:`_append_stream_chunk`. Returns ``True`` on
        success and ``False`` on any bounded substrate refusal
        (with :attr:`error_message` already set).
        """
        if seed_pattern_id is None:
            self.set_error(
                "processing window: feedback step missing seed pattern_id"
            )
            return False
        seed_entry = self.pattern_ledger.find(seed_pattern_id)
        if seed_entry is None:
            self.set_error(
                "processing window: feedback step could not locate seed entry "
                f"for pattern_id={seed_pattern_id!r}"
            )
            return False
        try:
            summary_text = build_pledger_summary_text(
                pattern_id=seed_entry.pattern_id,
                recurrence_count=seed_entry.recurrence_count,
                saturation_state_value=seed_entry.saturation_state.value,
            )
            summary_provenance = build_rehearsal_provenance(
                tick_index=tick_index,
                source=InternalEventSource.PLEDGER_SUMMARY,
            )
        except (TypeError, ValueError) as exc:
            self.set_error(f"processing window feedback rejected: {exc}")
            return False
        chunk = self._append_stream_chunk(
            text=summary_text,
            chunk_provenance=summary_provenance,
            growth_provenance="stream_append:_run_processing_window",
        )
        return chunk is not None

    def _run_cohmon_feedback_step(
        self,
        *,
        tick_index: int,
    ) -> bool:
        """Fire one Phase 3.20 Coherence Monitor feedback chunk.

        Builds a fresh :class:`CoherenceReport` via
        :func:`brain.development.coherence_monitor.build_full_coherence_report`
        (deferred import to avoid a module-load cycle:
        ``coherence_monitor`` already imports
        :class:`OperatorSession`; this module would otherwise
        import ``coherence_monitor`` at the top, completing the
        cycle). Extracts bounded primitives from the report, calls
        :func:`build_cohmon_summary_text` to produce the
        deterministic summary text, composes the
        ``cohmon_summary`` provenance via
        :func:`build_rehearsal_provenance`, and dispatches the
        chunk through :meth:`_append_stream_chunk`. Returns
        ``True`` on success and ``False`` on any bounded substrate
        refusal (with :attr:`error_message` already set).

        Drives ``I-CFBK-01``. Consumes zero real model calls
        because the entire path is offline / structural.
        """
        # Deferred function-body import (LOCK I): avoids the
        # circular module load described in the docstring.
        from brain.development.coherence_monitor import (
            build_full_coherence_report,
        )

        try:
            report = build_full_coherence_report(
                self,
                snapshot_id=f"coh-snap-{tick_index}",
            )
        except (TypeError, ValueError) as exc:
            self.set_error(
                f"processing window cohmon feedback rejected: {exc}"
            )
            return False

        counts: dict[str, int] = {
            "pass": 0,
            "warn": 0,
            "fail": 0,
            "not_applicable": 0,
        }
        for label, count in report.counts_by_status:
            if label in counts:
                counts[label] = count

        try:
            summary_text = build_cohmon_summary_text(
                overall_status_value=report.overall_status.value,
                pass_count=counts["pass"],
                warn_count=counts["warn"],
                fail_count=counts["fail"],
                na_count=counts["not_applicable"],
                check_count=len(report.snapshot.checks),
            )
            summary_provenance = build_rehearsal_provenance(
                tick_index=tick_index,
                source=InternalEventSource.COHMON_SUMMARY,
            )
        except (TypeError, ValueError) as exc:
            self.set_error(
                f"processing window cohmon feedback rejected: {exc}"
            )
            return False
        chunk = self._append_stream_chunk(
            text=summary_text,
            chunk_provenance=summary_provenance,
            growth_provenance="stream_append:_run_processing_window",
        )
        return chunk is not None

    def _run_worldlet_feedback_step(
        self,
        *,
        tick_index: int,
    ) -> bool:
        """Fire one Phase 3.24 worldlet-summary feedback chunk.

        Reads bounded primitives from :attr:`worldlet_history` (or
        falls back to the Phase 3.24 ``"absent"`` sentinel when no
        worldlet history is present), composes a bounded
        deterministic summary via
        :func:`build_worldlet_summary_text`, composes the bounded
        worldlet-summary provenance via
        :func:`build_rehearsal_provenance`, and dispatches the
        chunk through :meth:`_append_stream_chunk`. Returns
        ``True`` on success and ``False`` on any bounded substrate
        refusal (with :attr:`error_message` already set).

        Drives ``I-WFDBK-04``. Consumes zero real model calls
        because the entire path is offline / structural. Does NOT
        mutate :attr:`worldlet_history` (the Phase 3.24 feedback
        path is read-only on the worldlet substrate).
        """
        history = self.worldlet_history
        if history is None:
            state_id_value = WORLDLET_SUMMARY_ABSENT_SENTINEL
            step_index = 0
            object_count = 0
            attempt_count = 0
            response_count = 0
            accepted_count = 0
            pushback_count = 0
            last_reason_value = WORLDLET_SUMMARY_ABSENT_SENTINEL
        else:
            latest_state = history.latest_state
            state_id_value = latest_state.state_id
            step_index = latest_state.step_index
            object_count = len(latest_state.objects)
            attempts = history.attempts
            responses = history.responses
            attempt_count = len(attempts)
            response_count = len(responses)
            accepted_count = sum(
                1 for r in responses if r.accepted
            )
            pushback_count = sum(
                1
                for r in responses
                if (not r.accepted)
                and r.reason in _WORLDLET_PUSHBACK_REASONS_SESSION
            )
            if responses:
                last_reason_value = responses[-1].reason
            else:
                last_reason_value = WORLDLET_SUMMARY_ABSENT_SENTINEL

        try:
            summary_text = build_worldlet_summary_text(
                state_id_value=state_id_value,
                step_index=step_index,
                object_count=object_count,
                attempt_count=attempt_count,
                response_count=response_count,
                accepted_count=accepted_count,
                pushback_count=pushback_count,
                last_reason_value=last_reason_value,
            )
            summary_provenance = build_rehearsal_provenance(
                tick_index=tick_index,
                source=InternalEventSource.WORLDLET_SUMMARY,
            )
        except (TypeError, ValueError) as exc:
            self.set_error(
                f"processing window worldlet feedback rejected: {exc}"
            )
            return False
        chunk = self._append_stream_chunk(
            text=summary_text,
            chunk_provenance=summary_provenance,
            growth_provenance="stream_append:_run_processing_window",
        )
        return chunk is not None

    def _resolve_stream_candidate(
        self, candidate_id: str
    ) -> Optional[StreamPromotionCandidate]:
        for cand in self.stream_candidates:
            if cand.candidate_id == candidate_id:
                return cand
        return None

    def _dispatch_stream_promote(
        self, payload: Optional[StreamPromotePayload]
    ) -> Optional[bool]:
        """Promote one stream candidate onto the event queue.

        Returns ``True`` iff the promotion succeeded (event_queue
        grew); returns ``False`` on any failure path. The central
        :meth:`dispatch` reads this return value to decide whether to
        fire the post-dispatch autosave hook (drives ``I-AUTOSAVE-14``
        outcome-detection contract).
        """
        if not isinstance(payload, StreamPromotePayload):
            self.set_error("STREAM_PROMOTE requires a StreamPromotePayload")
            return False

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
            return False

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
            return False

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
            return False

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
            return False

        # Success: leave stream state intact except for view/status; the
        # /step path consumes the queued payload through the existing
        # _dispatch_step route. Stream history, candidates, and serial
        # are not consumed here.
        self.set_active_view("queue")
        self.set_status(
            f"promoted stream candidate {candidate.candidate_id!r} "
            f"(queue size = {len(self.event_queue)})"
        )
        # I-GROW-16: emit Growth Ledger event for the queued promotion.
        # Triggered by the dispatcher's typed True return signal under
        # the Phase 3.10c outcome-detection contract; no status / error
        # string is inspected.
        self.growth_ledger = self.growth_ledger.observe(
            event_type=GrowthEventType.STREAM_PROMOTION_QUEUED,
            tick=self.tick_counter,
            source=GrowthEventSource.STREAM_PROMOTE,
            references=(candidate.candidate_id,),
            provenance="stream_promote:_dispatch_stream_promote",
        )
        return True

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
    # Phase 3.10a operational hardening dispatchers. None of these
    # routes call tick(); none stores a sqlite3.Connection on the
    # session; each catches PersistenceError and surfaces it as bounded
    # local error_message text.
    # ------------------------------------------------------------------

    def _dispatch_session_status(self) -> None:
        from brain.ui.persistence_ops import (  # noqa: PLC0415
            session_status,
        )
        report = session_status(self)
        self.set_status(
            "session-status: "
            f"tick={report.tick_counter} "
            f"queue={report.queue_size} "
            f"view={report.active_view} "
            f"chunks={report.stream_chunk_count} "
            f"candidates={report.stream_candidate_count} "
            f"db="
            + ("configured" if report.session_db_configured else "off")
        )

    def _dispatch_db_status(self) -> None:
        config = self.session_store_config
        if config is None:
            self.set_error("/db-status requires a configured --session-db")
            return
        from brain.ui.persistence_ops import (  # noqa: PLC0415
            PersistenceError,
            db_status,
        )
        try:
            report = db_status(config)
        except PersistenceError as exc:
            self.set_error(f"/db-status failed: {exc}")
            return
        if not report.db_exists:
            self.set_error(
                f"/db-status: db missing ({report.error_text})"
            )
            return
        self.set_status(
            f"db-status: schema=v{report.schema_version} "
            f"catalog={report.catalog_version!r} "
            f"bytes={report.db_byte_size}"
        )

    def _dispatch_db_verify(self) -> None:
        config = self.session_store_config
        if config is None:
            self.set_error("/db-verify requires a configured --session-db")
            return
        from brain.ui.persistence_ops import (  # noqa: PLC0415
            PersistenceError,
            db_verify,
        )
        try:
            report = db_verify(config)
        except PersistenceError as exc:
            self.set_error(f"/db-verify failed: {exc}")
            return
        if not report.passed:
            self.set_error(f"/db-verify FAIL: {report.error_text}")
            return
        self.set_status(
            f"db-verify PASS: schema=v{report.schema_version} "
            f"chunks={report.loaded_chunks} "
            f"candidates={report.loaded_candidates}"
        )

    def _dispatch_db_backup(self, payload: Optional[DbBackupPayload]) -> None:
        if not isinstance(payload, DbBackupPayload):
            self.set_error("/db-backup requires a DbBackupPayload")
            return
        config = self.session_store_config
        if config is None:
            self.set_error("/db-backup requires a configured --session-db")
            return
        from brain.ui.persistence_ops import (  # noqa: PLC0415
            PersistenceError,
            db_backup,
        )
        try:
            report = db_backup(
                config, payload.dest_path, force=payload.force
            )
        except PersistenceError as exc:
            self.set_error(f"/db-backup failed: {exc}")
            return
        if not report.succeeded:
            self.set_error(f"/db-backup failed: {report.error_text}")
            return
        self.set_status(
            f"db-backup ok: dest={report.dest_path_str!r} "
            f"pages={report.pages_copied}/{report.total_pages} "
            f"bytes={report.dest_byte_size}"
            + (" (overwritten)" if report.overwritten else "")
        )

    # ------------------------------------------------------------------
    # Phase 3.10b persistence observability dispatchers. None of these
    # routes call tick(); none stores a sqlite3.Connection on the
    # session; each catches PersistenceError and surfaces it as bounded
    # local error_message text. None invokes a kernel builder.
    # ------------------------------------------------------------------

    def _dispatch_db_summary(self) -> None:
        config = self.session_store_config
        if config is None:
            self.set_error(
                "/db-summary requires a configured --session-db"
            )
            return
        from brain.ui.persistence import PersistenceError  # noqa: PLC0415
        from brain.ui.persistence_observe import db_summary  # noqa: PLC0415
        try:
            report = db_summary(config)
        except PersistenceError as exc:
            self.set_error(f"/db-summary failed: {exc}")
            return
        if report.error_text:
            self.set_error(f"/db-summary: {report.error_text}")
            return
        self.set_status(
            f"db-summary: profile={report.profile_row_count} "
            f"msi={report.msi_content_count}/"
            f"thr={report.msi_threshold} "
            f"ptcns={report.ptcns_eval_row_count} "
            f"registry={report.registry_row_count} "
            f"chunks={report.stream_chunk_count} "
            f"candidates={report.stream_candidate_count}"
        )

    def _dispatch_profile_summary(self) -> None:
        config = self.session_store_config
        if config is None:
            self.set_error(
                "/profile-summary requires a configured --session-db"
            )
            return
        from brain.ui.persistence import PersistenceError  # noqa: PLC0415
        from brain.ui.persistence_observe import (  # noqa: PLC0415
            profile_summary,
        )
        try:
            report = profile_summary(config)
        except PersistenceError as exc:
            self.set_error(f"/profile-summary failed: {exc}")
            return
        if report.error_text:
            self.set_error(f"/profile-summary: {report.error_text}")
            return
        self.set_status(
            f"profile-summary: rows={len(report.rows)} "
            + ("(truncated)" if report.truncated else "(complete)")
        )

    def _dispatch_stream_db_summary(self) -> None:
        config = self.session_store_config
        if config is None:
            self.set_error(
                "/stream-db-summary requires a configured --session-db"
            )
            return
        from brain.ui.persistence import PersistenceError  # noqa: PLC0415
        from brain.ui.persistence_observe import (  # noqa: PLC0415
            stream_db_summary,
        )
        try:
            report = stream_db_summary(config)
        except PersistenceError as exc:
            self.set_error(f"/stream-db-summary failed: {exc}")
            return
        if report.error_text:
            self.set_error(f"/stream-db-summary: {report.error_text}")
            return
        self.set_status(
            f"stream-db-summary: chunks={report.chunk_count} "
            f"candidates={report.candidate_count} "
            f"head={len(report.head)} tail={len(report.tail)}"
            + (" (truncated)" if report.truncated else "")
        )

    def _dispatch_db_diff(self) -> None:
        config = self.session_store_config
        if config is None:
            self.set_error(
                "/db-diff requires a configured --session-db"
            )
            return
        from brain.ui.persistence import PersistenceError  # noqa: PLC0415
        from brain.ui.persistence_observe import db_diff  # noqa: PLC0415
        try:
            report = db_diff(self, config)
        except PersistenceError as exc:
            self.set_error(f"/db-diff failed: {exc}")
            return
        if report.error_text:
            self.set_error(f"/db-diff: {report.error_text}")
            return
        if report.matches:
            self.set_status("db-diff: matches (diff_count=0)")
        else:
            self.set_status(
                f"db-diff: diff_count={report.diff_count}"
                + (" (truncated)" if report.truncated else "")
            )

    # ------------------------------------------------------------------
    # Phase 3.10c autosave dispatchers. None of these routes call tick();
    # none stores a sqlite3.Connection on the session; each catches
    # PersistenceError and surfaces it as bounded local error_message
    # text. The /autosave-enable / /autosave-disable handlers mutate
    # session.autosave_config but never invoke save_session — the
    # post-dispatch trigger (_maybe_autosave_after_dispatch) is the
    # SOLE save_session entry point in this module.
    # ------------------------------------------------------------------

    def _dispatch_autosave_status(self) -> None:
        from brain.ui.autosave import autosave_status  # noqa: PLC0415
        report = autosave_status(self)
        self.set_status(
            "autosave-status: "
            f"mode={report.mode.value} "
            f"db={report.db_path_str!r} "
            f"last_tick={report.last_attempt_tick} "
            f"last_outcome={report.last_attempt_outcome!r} "
            f"last_trigger={report.last_attempt_trigger!r} "
            f"last_at={report.last_attempt_at!r}"
        )

    def _dispatch_autosave_enable(self, payload) -> None:
        from brain.ui.autosave import autosave_enable  # noqa: PLC0415
        from brain.ui.commands import (  # noqa: PLC0415
            AutosaveEnablePayload,
        )
        from brain.ui.persistence import PersistenceError  # noqa: PLC0415
        if not isinstance(payload, AutosaveEnablePayload):
            self.set_error(
                "AUTOSAVE_ENABLE requires an AutosaveEnablePayload"
            )
            return
        try:
            report = autosave_enable(self, payload.mode)
        except PersistenceError as exc:
            self.set_error(f"/autosave-enable failed: {exc}")
            return
        self.set_status(
            f"autosave-enable ok: mode={report.mode.value} "
            f"db={report.db_path_str!r}"
        )

    def _dispatch_autosave_disable(self) -> None:
        from brain.ui.autosave import autosave_disable  # noqa: PLC0415
        report = autosave_disable(self)
        self.set_status(
            f"autosave-disable ok: mode={report.mode.value}"
        )

    def _maybe_autosave_after_dispatch(
        self,
        kind: OperatorCommand,
        mutation_outcome: Optional[bool],
    ) -> None:
        """Post-dispatch autosave trigger site.

        Drives ``I-AUTOSAVE-08`` / ``I-AUTOSAVE-09`` / ``I-AUTOSAVE-10``.
        Fires :func:`maybe_autosave_after_mutation` exactly when:

          (a) ``session.autosave_config`` is configured and non-OFF,
          (b) ``command.kind`` is in
              {``STEP_TICK``, ``STREAM_PROMOTE``},
          (c) the sub-dispatcher returned ``True`` (kernel / stream
              state mutated successfully),
          (d) ``session.session_store_config`` is configured.

        The returned typed report (or ``None``) is stored on
        :attr:`OperatorSession.last_autosave_status`. The helper itself
        never raises; any :class:`PersistenceError` is absorbed into
        the typed report.
        """
        config = self.autosave_config
        if config is None:
            return
        # Lazy import keeps the brain.ui.session <-> brain.ui.autosave
        # ordering acyclic.
        from brain.ui.autosave import (  # noqa: PLC0415
            AutosaveMode,
            AutosaveTrigger,
            maybe_autosave_after_mutation,
        )
        if config.mode is AutosaveMode.OFF:
            return
        if self.session_store_config is None:
            return
        if mutation_outcome is not True:
            return
        if kind is OperatorCommand.STEP_TICK:
            trigger = AutosaveTrigger.STEP_TICK
        elif kind is OperatorCommand.STREAM_PROMOTE:
            trigger = AutosaveTrigger.STREAM_PROMOTE
        else:
            return
        report = maybe_autosave_after_mutation(
            self, triggered_by=trigger
        )
        if report is not None:
            self.last_autosave_status = report
            if report.last_attempt_outcome == "error":
                # Surface the autosave error as bounded local error
                # text. The mutating dispatcher's success status
                # message is preserved on status_message.
                self.set_error(
                    f"autosave failed: {report.last_error_text}"
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


# ---------------------------------------------------------------------------
# Phase 3.23 dispatch tracer helpers (I-DTRACE-03..07).
# ---------------------------------------------------------------------------


def _classify_dispatch_route(kind):
    """Return the bounded ``(route_label, planned_mutation_kind)`` tuple.

    The actual mutation classification may refine the planned kind
    (for example, the STREAM_APPEND route may classify as
    ``STREAM_WINDOW_INTERNAL`` when the rehearsal window produced
    additional internal chunks); see
    :func:`_refine_stream_append_mutation_kind`.
    """
    # Lazy import: brain.development.dispatch_tracer depends on
    # brain.development.coherence_monitor, which imports OperatorSession.
    from brain.development.dispatch_tracer import (  # noqa: PLC0415
        DispatchMutationKind,
    )

    if kind in INSPECT_VIEW_MAP:
        return ("inspect-view-change", DispatchMutationKind.VIEW_CHANGE)
    if kind is OperatorCommand.QUEUE_PERCEPT:
        return ("queue-percept", DispatchMutationKind.QUEUE_MUTATION)
    if kind is OperatorCommand.STEP_TICK:
        return (
            "step-tick-via-public-tick",
            DispatchMutationKind.STEP_TICK,
        )
    if kind is OperatorCommand.CLEAR_STATUS:
        return ("clear-status", DispatchMutationKind.UI_ONLY)
    if kind is OperatorCommand.HELP:
        return ("help-view", DispatchMutationKind.VIEW_CHANGE)
    if kind is OperatorCommand.QUIT:
        return ("quit-flag", DispatchMutationKind.QUIT_FLAG)
    if kind is OperatorCommand.NOOP:
        return ("noop-early-return", DispatchMutationKind.NONE)
    if kind is OperatorCommand.STREAM_APPEND:
        return ("stream-append", DispatchMutationKind.STREAM_APPEND)
    if kind is OperatorCommand.STREAM_PROMOTE:
        return ("stream-promote", DispatchMutationKind.STREAM_PROMOTE)
    if kind in (
        OperatorCommand.SAVE_SESSION,
        OperatorCommand.LOAD_SESSION,
    ):
        return (
            "session-persistence",
            DispatchMutationKind.SESSION_PERSISTENCE,
        )
    if kind is OperatorCommand.SESSION_STATUS:
        return ("session-status", DispatchMutationKind.UI_ONLY)
    if kind in (
        OperatorCommand.DB_STATUS,
        OperatorCommand.DB_VERIFY,
        OperatorCommand.DB_SUMMARY,
        OperatorCommand.PROFILE_SUMMARY,
        OperatorCommand.STREAM_DB_SUMMARY,
        OperatorCommand.DB_DIFF,
    ):
        return ("db-observe", DispatchMutationKind.DB_OBSERVE)
    if kind is OperatorCommand.DB_BACKUP:
        return ("db-backup", DispatchMutationKind.DB_BACKUP)
    if kind is OperatorCommand.AUTOSAVE_STATUS:
        return ("autosave-status", DispatchMutationKind.UI_ONLY)
    if kind in (
        OperatorCommand.AUTOSAVE_ENABLE,
        OperatorCommand.AUTOSAVE_DISABLE,
    ):
        return ("autosave-config", DispatchMutationKind.AUTOSAVE)
    # The enum is closed; fall back to a bounded printable label
    # rather than raising, so the dispatch trace records the
    # routing failure structurally.
    return ("unrouted", DispatchMutationKind.ERROR_ONLY)


def _dispatch_handler_method_name(kind) -> str:
    """Return the bounded printable name of the handler method.

    Used in the trace's ``HANDLER_ENTERED.derived_facts`` field so
    audits can reconstruct which method handled each route.
    """
    if kind in INSPECT_VIEW_MAP:
        return "set_active_view+set_status"
    mapping = {
        OperatorCommand.QUEUE_PERCEPT: "_dispatch_queue",
        OperatorCommand.STEP_TICK: "_dispatch_step",
        OperatorCommand.CLEAR_STATUS: "clear_status",
        OperatorCommand.HELP: "set_active_view+set_status",
        OperatorCommand.QUIT: "set_quit_flag",
        OperatorCommand.NOOP: "noop-early-return",
        OperatorCommand.STREAM_APPEND: "_dispatch_stream_append",
        OperatorCommand.STREAM_PROMOTE: "_dispatch_stream_promote",
        OperatorCommand.SAVE_SESSION: "_dispatch_save_session",
        OperatorCommand.LOAD_SESSION: "_dispatch_load_session",
        OperatorCommand.SESSION_STATUS: "_dispatch_session_status",
        OperatorCommand.DB_STATUS: "_dispatch_db_status",
        OperatorCommand.DB_VERIFY: "_dispatch_db_verify",
        OperatorCommand.DB_BACKUP: "_dispatch_db_backup",
        OperatorCommand.DB_SUMMARY: "_dispatch_db_summary",
        OperatorCommand.PROFILE_SUMMARY: "_dispatch_profile_summary",
        OperatorCommand.STREAM_DB_SUMMARY: "_dispatch_stream_db_summary",
        OperatorCommand.DB_DIFF: "_dispatch_db_diff",
        OperatorCommand.AUTOSAVE_STATUS: "_dispatch_autosave_status",
        OperatorCommand.AUTOSAVE_ENABLE: "_dispatch_autosave_enable",
        OperatorCommand.AUTOSAVE_DISABLE: "_dispatch_autosave_disable",
    }
    return mapping.get(kind, "unrouted")


def _handler_outcome_label(
    *, mutation_outcome, error_present: bool
) -> str:
    """Bounded printable classification of the handler's outcome.

    The mutation_outcome contract (drives ``I-AUTOSAVE-14``) returns
    ``True`` for a kernel mutation, ``False`` for an outright handler
    failure, and ``None`` for a read-only route. The error_present
    flag captures whether ``error_message`` is non-empty after the
    handler. Combining both yields the bounded label.
    """
    if mutation_outcome is True:
        return "mutated"
    if mutation_outcome is False:
        return "failed"
    if error_present:
        return "failed-readonly"
    return "read-only"


def _refine_stream_append_mutation_kind(
    *, planned, pre_facts, post_facts,
):
    """Refine ``STREAM_APPEND`` to ``STREAM_WINDOW_INTERNAL`` when applicable.

    The Phase 3.18 processing window can append additional internal
    rehearsal chunks during a single STREAM_APPEND dispatch. When that
    happens, the post-dispatch ``stream_history_len`` rises by more
    than 1 above the pre-dispatch value. The mutation classification
    reflects this by switching to ``STREAM_WINDOW_INTERNAL``.
    """
    from brain.development.dispatch_tracer import (  # noqa: PLC0415
        DispatchMutationKind,
    )

    if planned is not DispatchMutationKind.STREAM_APPEND:
        return planned
    pre_lookup = {k: v for k, v in pre_facts}
    post_lookup = {k: v for k, v in post_facts}
    try:
        pre_len = int(pre_lookup.get("stream_history_len", "0"))
        post_len = int(post_lookup.get("stream_history_len", "0"))
    except ValueError:
        return planned
    if post_len > pre_len + 1:
        return DispatchMutationKind.STREAM_WINDOW_INTERNAL
    return planned


def _classify_autosave_outcome(
    *,
    autosave_config,
    session_store_config,
    mutation_outcome,
    kind,
    autosave_before,
    autosave_after,
) -> str:
    """Bounded printable classification of the autosave hook outcome."""
    if autosave_config is None:
        return "considered:no-config"
    # Lazy: brain.ui.autosave imports brain.ui.session.
    from brain.ui.autosave import AutosaveMode  # noqa: PLC0415

    if autosave_config.mode is AutosaveMode.OFF:
        return "considered:mode-off"
    if session_store_config is None:
        return "considered:no-db"
    if mutation_outcome is not True:
        return "considered:no-mutation"
    if kind not in (
        OperatorCommand.STEP_TICK,
        OperatorCommand.STREAM_PROMOTE,
    ):
        return "considered:wrong-trigger"
    if autosave_after is None:
        return "considered:hook-noop"
    if autosave_after is autosave_before:
        return "considered:hook-noop"
    if autosave_after.last_attempt_outcome == "ok":
        return "considered:fired-ok"
    if autosave_after.last_attempt_outcome == "error":
        return "considered:fired-failed"
    return "considered:fired-other"


__all__ = [
    "DEFAULT_EVENT_QUEUE_LIMIT",
    "MAX_STATUS_TEXT_LEN",
    "OperatorEventQueue",
    "OperatorSession",
]


# Convenience accessors for fixtures and the constant-parity audit.
STREAM_PROMOTE_DEFAULT_RHO: Fraction = _STREAM_PROMOTE_DEFAULT_RHO
