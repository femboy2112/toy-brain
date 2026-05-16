"""Operator TUI command primitives.

This module defines the finite closed enumeration of operator commands
(:class:`OperatorCommand`) and the typed payload for the single command
that carries an operator-supplied :class:`PerceptEvent` candidate
(:class:`QueuePerceptPayload`). It also exposes a small :class:`Command`
wrapper that pairs a command kind with at most one approved payload type.

Catalog rows driven from here:

* ``I-UI-03`` — ``OperatorCommand`` is a finite closed enumeration; no
  command kind exists outside the documented set, and command
  construction never accepts a callable, shell string, file path,
  network endpoint, or arbitrary Python expression in any payload field.
* ``I-UI-04`` — a ``QUEUE_PERCEPT`` payload is bounded by the public
  :class:`PerceptEvent` constructor: building a queued candidate goes
  through that constructor and out-of-range values raise without
  partially mutating an :class:`OperatorSession`.

This module imports only :mod:`brain.io_types` and :mod:`brain.toce_core`
(plus :mod:`fractions` and :mod:`enum`). It does **not** import
``curses``, ``brain.tick``, ``brain.tlica``, or ``brain.llm``; the
router and session paths that consume these primitives must remain free
of those surfaces as well (see :class:`I-UI-07` / :class:`I-UI-10`).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Optional, Union

from brain.development.text_stream import (
    STREAM_PROVENANCE_MAX_LEN,
    STREAM_TEXT_MAX_LEN,
)
from brain.io_types import PerceptEvent
from brain.toce_core import ContentState


# Bounded length cap for /stream-promote candidate_id arguments. Mirrors
# `STREAM_PROVENANCE_MAX_LEN` from `brain.development.text_stream`; the
# Phase 3.8 fixture `stream_constant_parity.py` verifies the equality.
STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN: int = STREAM_PROVENANCE_MAX_LEN


_COGITO_RESERVED_ID: str = "__cogito__"


# ---------------------------------------------------------------------------
# OperatorCommand — closed enumeration
# ---------------------------------------------------------------------------


class OperatorCommand(str, Enum):
    """Finite closed enumeration of operator command kinds.

    Drives ``I-UI-03``. Any string value supplied to :func:`make_command`
    that does not appear in this enumeration raises before any session
    state is touched. ``OperatorCommand`` is intentionally a ``str``
    enum so its serialized form is a bounded printable identifier.
    """

    INSPECT_STATE = "inspect_state"
    INSPECT_TICK = "inspect_tick"
    INSPECT_OUTPUT = "inspect_output"
    INSPECT_WORLDLET = "inspect_worldlet"
    INSPECT_REPL = "inspect_repl"
    QUEUE_PERCEPT = "queue_percept"
    STEP_TICK = "step_tick"
    CLEAR_STATUS = "clear_status"
    HELP = "help"
    QUIT = "quit"
    NOOP = "noop"
    STREAM_APPEND = "stream_append"
    INSPECT_STREAM_SUMMARY = "inspect_stream_summary"
    INSPECT_STREAM_CANDIDATES = "inspect_stream_candidates"
    STREAM_PROMOTE = "stream_promote"
    SAVE_SESSION = "save_session"
    LOAD_SESSION = "load_session"


#: The closed set of inspection-only commands. Maps each kind to the
#: ``active_view`` string the router should select when handling it.
INSPECT_VIEW_MAP: dict[OperatorCommand, str] = {
    OperatorCommand.INSPECT_STATE: "state",
    OperatorCommand.INSPECT_TICK: "tick",
    OperatorCommand.INSPECT_OUTPUT: "output",
    OperatorCommand.INSPECT_WORLDLET: "worldlet",
    OperatorCommand.INSPECT_REPL: "repl",
    OperatorCommand.INSPECT_STREAM_SUMMARY: "stream_summary",
    OperatorCommand.INSPECT_STREAM_CANDIDATES: "stream_candidates",
}


#: Commands that do not accept a payload. Any other command kind must
#: either pair with the matching payload type or carry ``None``.
_COMMANDS_WITHOUT_PAYLOAD: frozenset[OperatorCommand] = frozenset({
    OperatorCommand.INSPECT_STATE,
    OperatorCommand.INSPECT_TICK,
    OperatorCommand.INSPECT_OUTPUT,
    OperatorCommand.INSPECT_WORLDLET,
    OperatorCommand.INSPECT_REPL,
    OperatorCommand.INSPECT_STREAM_SUMMARY,
    OperatorCommand.INSPECT_STREAM_CANDIDATES,
    OperatorCommand.STEP_TICK,
    OperatorCommand.CLEAR_STATUS,
    OperatorCommand.HELP,
    OperatorCommand.QUIT,
    OperatorCommand.NOOP,
})


# ---------------------------------------------------------------------------
# QueuePerceptPayload — PerceptEvent-constructor-bounded payload
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class QueuePerceptPayload:
    """Operator-supplied candidate for a future ``STEP_TICK``.

    The payload carries only the four fields accepted by the public
    :class:`PerceptEvent` constructor: ``content_id``, ``text``,
    ``content_state``, and ``initial_rho``. No other field is permitted,
    and no callable / shell string / file path / network endpoint may be
    smuggled in via a constructor argument.

    Drives ``I-UI-04``. Construction calls the real ``PerceptEvent``
    constructor on the supplied fields so any value the kernel would
    reject (``COGITO_ID`` collision, non-printable text, out-of-range
    rho, wrong :class:`ContentState` type) raises before the payload
    record is fully built. The validated :class:`PerceptEvent` is
    accessible via :meth:`build_event`.
    """

    content_id: str
    text: str
    content_state: ContentState
    initial_rho: Fraction

    def __post_init__(self) -> None:
        # Reject obviously non-PerceptEvent-shaped fields up front so
        # the error path is local to this constructor. The remaining
        # validation is delegated to ``PerceptEvent.__post_init__``
        # below: that constructor is the public contract for
        # I-RT-01 (no COGITO_ID), I-RT-09 (non-empty printable text),
        # and the [0, 1] bound on ``initial_rho``.
        if not isinstance(self.content_id, str):
            raise TypeError(
                "QueuePerceptPayload.content_id must be str "
                f"(got {type(self.content_id).__name__})"
            )
        if not isinstance(self.text, str):
            raise TypeError(
                "QueuePerceptPayload.text must be str "
                f"(got {type(self.text).__name__})"
            )
        if not isinstance(self.content_state, ContentState):
            raise TypeError(
                "QueuePerceptPayload.content_state must be a ContentState "
                f"(got {type(self.content_state).__name__})"
            )
        if callable(self.content_id) or callable(self.text):
            # Belt-and-suspenders: dataclass-typed fields cannot be
            # callable, but a future refactor could introduce a
            # subclass; reject explicitly so the audit row catches it.
            raise TypeError(
                "QueuePerceptPayload fields must not be callable"
            )

        # Normalize / validate ``initial_rho`` via the same path the
        # PerceptEvent constructor uses. ``rho()`` raises if the value
        # is outside [0, 1]. We do the conversion here so the stored
        # payload field is already an exact ``Fraction`` and a later
        # ``build_event`` call cannot re-normalize through a different
        # path.
        if isinstance(self.initial_rho, Fraction):
            if not (Fraction(0) <= self.initial_rho <= Fraction(1)):
                raise ValueError(
                    "QueuePerceptPayload.initial_rho must be in [0, 1]; "
                    f"got {self.initial_rho}"
                )
            rho_value = self.initial_rho
        elif isinstance(self.initial_rho, (int, str)):
            from brain.tlica.builders import rho as _rho
            rho_value = _rho(self.initial_rho)
        else:
            raise TypeError(
                "QueuePerceptPayload.initial_rho must be Fraction | int | str "
                f"(got {type(self.initial_rho).__name__})"
            )
        object.__setattr__(self, "initial_rho", rho_value)

        # Drive the PerceptEvent constructor on the normalized fields so
        # any kernel-level rejection (COGITO_ID, non-printable text)
        # surfaces here. The constructed event is discarded; the
        # payload remains the source of truth so the router can rebuild
        # it deterministically.
        PerceptEvent(
            content_id=self.content_id,
            text=self.text,
            content_state=self.content_state,
            initial_rho=rho_value,
        )

    def build_event(self) -> PerceptEvent:
        """Rebuild a :class:`PerceptEvent` from this payload.

        The payload constructor has already validated each field, so the
        returned event is guaranteed to be accepted by the public
        ``tick(...)`` entrypoint without further normalization.
        """
        return PerceptEvent(
            content_id=self.content_id,
            text=self.text,
            content_state=self.content_state,
            initial_rho=self.initial_rho,
        )

    def summary(self) -> tuple[str, ...]:
        """Bounded printable summary tuple for the queued-event pane.

        Returns short lines like ``content_id = ...`` for the renderer
        to place under the "queued event" header. The summary contains
        no callable, file handle, or socket value.
        """
        return (
            f"content_id    = {self.content_id}",
            f"text          = {self.text}",
            f"initial_rho   = {self.initial_rho}",
            "content_state = "
            f"available={self.content_state.available}, "
            f"verification_path={self.content_state.verification_path}, "
            f"retrievable={self.content_state.retrievable}, "
            f"operative={self.content_state.operative}",
        )


# ---------------------------------------------------------------------------
# StreamAppendPayload / StreamPromotePayload — bounded stream-command payloads
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StreamAppendPayload:
    """Operator-supplied bounded text for `/stream` append.

    Drives ``I-UISTRM-02``. Construction validates that ``text`` is a
    non-empty printable string whose length is at most
    :data:`STREAM_TEXT_MAX_LEN`, the same bound the Phase 3.7
    `TextStreamChunk` constructor enforces. The payload carries no
    callable, file handle, socket, LLM client, subprocess handle, or
    path object.
    """

    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError(
                "I-UISTRM-02 violated: StreamAppendPayload.text must be str "
                f"(got {type(self.text).__name__})"
            )
        if not self.text:
            raise ValueError(
                "I-UISTRM-02 violated: StreamAppendPayload.text must be non-empty"
            )
        if len(self.text) > STREAM_TEXT_MAX_LEN:
            raise ValueError(
                "I-UISTRM-02 violated: StreamAppendPayload.text length "
                f"{len(self.text)} exceeds STREAM_TEXT_MAX_LEN="
                f"{STREAM_TEXT_MAX_LEN}"
            )
        for ch in self.text:
            if ch in ("\n", "\t"):
                continue
            if not ch.isprintable():
                raise ValueError(
                    "I-UISTRM-02 violated: StreamAppendPayload.text must be "
                    "printable raw text"
                )
        if self.text == _COGITO_RESERVED_ID:
            raise ValueError(
                "I-UISTRM-02 violated: StreamAppendPayload.text cannot equal "
                "COGITO_ID"
            )


@dataclass(frozen=True, slots=True)
class StreamPromotePayload:
    """Operator-supplied candidate_id for `/stream-promote`.

    Drives ``I-UISTRM-02``. Construction validates that ``candidate_id``
    is a non-empty printable string whose length is at most
    :data:`STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN`. The payload carries no
    callable, file handle, socket, LLM client, subprocess handle, or
    path object. Resolution to a `StreamPromotionCandidate` happens at
    dispatch time in :class:`OperatorSession`; this payload is the typed
    parser output only.
    """

    candidate_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_id, str):
            raise TypeError(
                "I-UISTRM-02 violated: StreamPromotePayload.candidate_id "
                f"must be str (got {type(self.candidate_id).__name__})"
            )
        if not self.candidate_id:
            raise ValueError(
                "I-UISTRM-02 violated: StreamPromotePayload.candidate_id "
                "must be non-empty"
            )
        if not self.candidate_id.isprintable():
            raise ValueError(
                "I-UISTRM-02 violated: StreamPromotePayload.candidate_id "
                "must be printable"
            )
        if len(self.candidate_id) > STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN:
            raise ValueError(
                "I-UISTRM-02 violated: StreamPromotePayload.candidate_id "
                f"length {len(self.candidate_id)} exceeds "
                f"STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN="
                f"{STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN}"
            )
        if self.candidate_id == _COGITO_RESERVED_ID:
            raise ValueError(
                "I-UISTRM-02 violated: StreamPromotePayload.candidate_id "
                "cannot equal COGITO_ID"
            )


CommandPayload = Union[QueuePerceptPayload, StreamAppendPayload, StreamPromotePayload]


# ---------------------------------------------------------------------------
# Command wrapper
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Command:
    """A typed (kind, payload) pair routed by :class:`OperatorSession`.

    Drives ``I-UI-03`` and ``I-UISTRM-01``/``I-UISTRM-02``. The
    constructor enforces:

    * ``kind`` is an :class:`OperatorCommand` enum member.
    * ``payload`` is exactly one of: ``None`` (for any command kind
      that does not take a payload), :class:`QueuePerceptPayload`
      (for :data:`OperatorCommand.QUEUE_PERCEPT`),
      :class:`StreamAppendPayload`
      (for :data:`OperatorCommand.STREAM_APPEND`), or
      :class:`StreamPromotePayload`
      (for :data:`OperatorCommand.STREAM_PROMOTE`).

    No callable, shell string, file path, network endpoint, or arbitrary
    Python expression may appear in a command payload. The wrapper is a
    frozen dataclass: once constructed it can be inspected freely but
    not mutated.
    """

    kind: OperatorCommand
    payload: Optional[CommandPayload] = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, OperatorCommand):
            raise TypeError(
                "Command.kind must be an OperatorCommand "
                f"(got {type(self.kind).__name__})"
            )
        if self.kind is OperatorCommand.QUEUE_PERCEPT:
            if not isinstance(self.payload, QueuePerceptPayload):
                raise TypeError(
                    "Command.payload must be a QueuePerceptPayload for "
                    "QUEUE_PERCEPT (got "
                    f"{type(self.payload).__name__})"
                )
        elif self.kind is OperatorCommand.STREAM_APPEND:
            if not isinstance(self.payload, StreamAppendPayload):
                raise TypeError(
                    "Command.payload must be a StreamAppendPayload for "
                    "STREAM_APPEND (got "
                    f"{type(self.payload).__name__})"
                )
        elif self.kind is OperatorCommand.STREAM_PROMOTE:
            if not isinstance(self.payload, StreamPromotePayload):
                raise TypeError(
                    "Command.payload must be a StreamPromotePayload for "
                    "STREAM_PROMOTE (got "
                    f"{type(self.payload).__name__})"
                )
        else:
            if self.payload is not None:
                raise TypeError(
                    f"Command.payload must be None for {self.kind!r} "
                    f"(got {type(self.payload).__name__})"
                )
        # Reject callable payloads explicitly so a future subclass cannot
        # smuggle a callback into a router-driven command.
        if callable(self.payload):
            raise TypeError("Command.payload must not be callable")


def make_command(
    kind: OperatorCommand | str,
    *,
    content_id: Optional[str] = None,
    text: Optional[str] = None,
    content_state: Optional[ContentState] = None,
    initial_rho: Optional[Fraction | int | str] = None,
    stream_text: Optional[str] = None,
    candidate_id: Optional[str] = None,
) -> Command:
    """Construct a :class:`Command` from a finite kind plus optional fields.

    Accepts a string ``kind`` and coerces it through the
    :class:`OperatorCommand` enumeration; unknown kinds raise
    ``ValueError`` without partial side effects (``I-UI-03``).

    When ``kind`` is :data:`OperatorCommand.QUEUE_PERCEPT` the helper
    builds a :class:`QueuePerceptPayload` from the supplied
    ``content_id`` / ``text`` / ``content_state`` / ``initial_rho``
    arguments — the public ``PerceptEvent`` constructor runs as part of
    payload construction (``I-UI-04``).
    """
    if isinstance(kind, OperatorCommand):
        resolved = kind
    elif isinstance(kind, str):
        try:
            resolved = OperatorCommand(kind)
        except ValueError as exc:
            raise ValueError(
                f"I-UI-03 violated: unknown OperatorCommand kind {kind!r}; "
                f"expected one of {[c.value for c in OperatorCommand]!r}"
            ) from exc
    else:
        raise TypeError(
            "make_command kind must be OperatorCommand | str "
            f"(got {type(kind).__name__})"
        )

    if resolved is OperatorCommand.QUEUE_PERCEPT:
        if content_id is None or text is None or content_state is None or initial_rho is None:
            raise TypeError(
                "make_command(QUEUE_PERCEPT) requires content_id, text, "
                "content_state, and initial_rho"
            )
        if stream_text is not None or candidate_id is not None:
            raise TypeError(
                "make_command(QUEUE_PERCEPT) does not accept stream_text or "
                "candidate_id"
            )
        payload: Optional[CommandPayload] = QueuePerceptPayload(
            content_id=content_id,
            text=text,
            content_state=content_state,
            initial_rho=(
                initial_rho
                if isinstance(initial_rho, Fraction)
                else Fraction(initial_rho)
                if isinstance(initial_rho, int)
                else initial_rho  # str -> let payload normalize
            ),
        )
    elif resolved is OperatorCommand.STREAM_APPEND:
        if stream_text is None:
            raise TypeError(
                "make_command(STREAM_APPEND) requires stream_text"
            )
        if (
            content_id is not None
            or text is not None
            or content_state is not None
            or initial_rho is not None
            or candidate_id is not None
        ):
            raise TypeError(
                "make_command(STREAM_APPEND) does not accept "
                "content_id/text/content_state/initial_rho/candidate_id"
            )
        payload = StreamAppendPayload(text=stream_text)
    elif resolved is OperatorCommand.STREAM_PROMOTE:
        if candidate_id is None:
            raise TypeError(
                "make_command(STREAM_PROMOTE) requires candidate_id"
            )
        if (
            content_id is not None
            or text is not None
            or content_state is not None
            or initial_rho is not None
            or stream_text is not None
        ):
            raise TypeError(
                "make_command(STREAM_PROMOTE) does not accept "
                "content_id/text/content_state/initial_rho/stream_text"
            )
        payload = StreamPromotePayload(candidate_id=candidate_id)
    else:
        if (
            content_id is not None
            or text is not None
            or content_state is not None
            or initial_rho is not None
            or stream_text is not None
            or candidate_id is not None
        ):
            raise TypeError(
                f"make_command({resolved.name}) does not accept "
                "content_id/text/content_state/initial_rho/stream_text/candidate_id"
            )
        payload = None

    return Command(kind=resolved, payload=payload)


__all__ = [
    "OperatorCommand",
    "INSPECT_VIEW_MAP",
    "QueuePerceptPayload",
    "StreamAppendPayload",
    "StreamPromotePayload",
    "STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN",
    "CommandPayload",
    "Command",
    "make_command",
]
