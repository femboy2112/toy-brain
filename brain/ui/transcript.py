"""Operator transcript / event log for the agent-style Operator TUI.

This module defines the immutable :class:`TranscriptEntry` record, the
closed enumeration :class:`TranscriptKind` of operator UI event tags,
and the :class:`OperatorTranscript` copy-on-write ring buffer that
records local UI events for the wrapper to render in the transcript
pane.

The transcript is **local UI state only**. It holds no callable, no
file handle, no socket, no LLM client, and no mutable reference into
:class:`brain.tick.BrainState` or any developmental history. Every
append is copy-on-write: appending to a transcript returns a new
:class:`OperatorTranscript` value; the original is unmodified.

Per ``OPERATOR_TUI_AGENT_LAYOUT_CORRIGENDA.md`` ruling D, the
transcript does **not** persist across ``python3 -m brain.ui``
invocations — there is no filesystem read/write of
``~/.brain_tui_history`` or any similar path. The wrapper constructs a
fresh :meth:`OperatorTranscript.empty` at startup and the transcript
dies with the curses wrapper.

Catalog rows driven from here:

* ``I-UI-19`` (REQUIRED) — :class:`OperatorTranscript` records UI
  events copy-on-write and remains local UI state only. The ring is
  bounded by :data:`TRANSCRIPT_MAX_ENTRIES`; oldest entries are dropped
  before new entries are appended when the ring is full. Entry text is
  bounded printable text (mirrors the ``I-UI-13`` policy in
  :mod:`brain.ui.session`).

This module imports only standard-library typing helpers,
``dataclasses``, and ``enum``, plus the read-only ``TranscriptSnapshot``
/ ``TranscriptSnapshotEntry`` projection types from
:mod:`brain.ui.layout` (so the wrapper can build an
:class:`brain.ui.layout.AgentTuiViewModel` without converting fields
by hand). It does **not** import :mod:`curses`, :mod:`brain.tick`,
:mod:`brain.tlica`, :mod:`brain.llm`, :mod:`os`, :mod:`subprocess`,
:mod:`socket`, :mod:`urllib`, :mod:`http`, :mod:`requests`, :mod:`json`,
:mod:`yaml`, :mod:`ast`, :mod:`code`, or :mod:`codeop`.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from brain.ui.layout import TranscriptSnapshot, TranscriptSnapshotEntry


# ---------------------------------------------------------------------------
# Bounds — locked by the corrigenda (section 5.4).
# ---------------------------------------------------------------------------


#: Maximum number of entries retained in the ring before the oldest is
#: dropped. Drives the bound half of ``I-UI-19``. Matches the kickoff
#: section 9 value (``TRANSCRIPT_MAX_ENTRIES = 64``) and the corrigenda
#: section 5.4 ruling.
TRANSCRIPT_MAX_ENTRIES: int = 64


#: Maximum number of printable characters retained in a single
#: transcript entry. Mirrors :data:`brain.ui.session.MAX_STATUS_TEXT_LEN`
#: so a long status / error message cannot blow past the transcript pane
#: budget. Drives the bounded-text half of ``I-UI-19``.
TRANSCRIPT_MAX_TEXT_LEN: int = 240


# ---------------------------------------------------------------------------
# TranscriptKind — closed enumeration of UI event tags.
# ---------------------------------------------------------------------------


class TranscriptKind(str, Enum):
    """Closed enumeration of operator UI event tags.

    The tag is rendered in the transcript pane (e.g. ``[QUEUED@3] ...``)
    and identifies which wrapper action produced the entry. The
    enumeration is intentionally a ``str`` subclass so each tag is a
    bounded printable identifier that can be placed directly into a
    rendered row.

    Drives ``I-UI-19``. Adding a tag here is a deliberate UI surface
    change; the parser, composer, and session continue to treat the
    transcript as opaque local UI state.
    """

    #: Operator submitted a parsed local command (the parser accepted
    #: the input and produced a Command). The text is the original
    #: composer line (bounded printable).
    SUBMIT = "SUBMIT"

    #: A ``QUEUE_PERCEPT`` command was dispatched and the session
    #: accepted the payload. The text is the session status message
    #: emitted by the dispatch (e.g. ``"queued percept 'beta' (queue
    #: size = 1)"``).
    QUEUED = "QUEUED"

    #: A ``STEP_TICK`` command was dispatched and the session ran one
    #: tick. The text is the session status message emitted by the
    #: dispatch (e.g. ``"tick 1 ok (...)"``).
    STEP = "STEP"

    #: The parser rejected the input, or the session captured a
    #: dispatch-time failure as a local UI error. The text is the
    #: corresponding error / status message.
    ERROR = "ERROR"

    #: The operator selected a different inspector pane (e.g. ``/state``,
    #: ``/tick``, ``/help``). The text is the session status message
    #: emitted by the dispatch (e.g. ``"view = state"``).
    VIEW = "VIEW"

    #: The operator submitted ``/quit``. The text is the session status
    #: message emitted by the dispatch (``"quit"``).
    QUIT = "QUIT"


#: The closed set of legal :class:`TranscriptKind` string values.
ALLOWED_TRANSCRIPT_KINDS: frozenset[str] = frozenset(k.value for k in TranscriptKind)


# ---------------------------------------------------------------------------
# Bounded-printable helper.
# ---------------------------------------------------------------------------


def _bound_printable(label: str, value: str, *, limit: int) -> str:
    """Reject non-printable text; truncate at *limit*.

    The transcript never accepts terminal control characters or callables
    in any text field. Truncation preserves printability (the surviving
    prefix is printable because the whole string was). Empty strings are
    allowed and represent a transcript entry with no payload text.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"I-UI-19 violated: {label} must be a str (got {type(value).__name__})"
        )
    if value and not value.isprintable():
        raise ValueError(
            f"I-UI-19 violated: {label} must be printable text (got {value!r})"
        )
    if len(value) > limit:
        return value[: limit - 1] + "…"
    return value


# ---------------------------------------------------------------------------
# TranscriptEntry — immutable bounded record.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TranscriptEntry:
    """A single immutable transcript record.

    Fields:

    * ``kind`` — closed :class:`TranscriptKind` tag.
    * ``tick_at_event`` — value of
      :attr:`brain.ui.session.OperatorSession.tick_counter` at the time
      the wrapper appended the entry. Non-negative.
    * ``text`` — bounded printable text payload (bounded by
      :data:`TRANSCRIPT_MAX_TEXT_LEN`).

    Drives ``I-UI-19``. The record is a frozen dataclass with slots;
    every field is a bounded primitive. No callable, file handle,
    socket, or LLM-client value may appear here.
    """

    kind: TranscriptKind
    tick_at_event: int
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, TranscriptKind):
            raise TypeError(
                "TranscriptEntry.kind must be a TranscriptKind "
                f"(got {type(self.kind).__name__})"
            )
        if not isinstance(self.tick_at_event, int) or isinstance(
            self.tick_at_event, bool
        ):
            raise TypeError(
                "TranscriptEntry.tick_at_event must be int "
                f"(got {type(self.tick_at_event).__name__})"
            )
        if self.tick_at_event < 0:
            raise ValueError(
                "TranscriptEntry.tick_at_event must be non-negative "
                f"(got {self.tick_at_event!r})"
            )
        object.__setattr__(
            self,
            "text",
            _bound_printable(
                "TranscriptEntry.text", self.text, limit=TRANSCRIPT_MAX_TEXT_LEN
            ),
        )


# ---------------------------------------------------------------------------
# OperatorTranscript — copy-on-write ring buffer.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OperatorTranscript:
    """Immutable copy-on-write ring of :class:`TranscriptEntry` records.

    The transcript is bounded by ``limit`` (defaults to
    :data:`TRANSCRIPT_MAX_ENTRIES`). When :meth:`append` is called on a
    full ring the oldest entry is dropped before the new entry is
    added. The append is **copy-on-write**: the call returns a new
    :class:`OperatorTranscript`; the original instance is unchanged.

    The wrapper holds the current transcript in its local stack and
    replaces the reference each frame; the transcript never escapes the
    wrapper (no filesystem write, no trace, no developmental history
    append).

    Drives ``I-UI-19``.
    """

    entries: tuple[TranscriptEntry, ...] = ()
    limit: int = TRANSCRIPT_MAX_ENTRIES

    def __post_init__(self) -> None:
        if not isinstance(self.limit, int) or isinstance(self.limit, bool):
            raise TypeError(
                "OperatorTranscript.limit must be int "
                f"(got {type(self.limit).__name__})"
            )
        if self.limit <= 0:
            raise ValueError(
                "OperatorTranscript.limit must be a positive int "
                f"(got {self.limit!r})"
            )
        if not isinstance(self.entries, tuple):
            raise TypeError(
                "OperatorTranscript.entries must be a tuple "
                f"(got {type(self.entries).__name__})"
            )
        if len(self.entries) > self.limit:
            raise ValueError(
                "I-UI-19 violated: OperatorTranscript.entries exceeds limit "
                f"(len={len(self.entries)}, limit={self.limit})"
            )
        for entry in self.entries:
            if not isinstance(entry, TranscriptEntry):
                raise TypeError(
                    "OperatorTranscript.entries items must be TranscriptEntry "
                    f"(got {type(entry).__name__})"
                )

    # ------------------------------------------------------------------
    # Construction helpers.
    # ------------------------------------------------------------------

    @classmethod
    def empty(
        cls, *, limit: int = TRANSCRIPT_MAX_ENTRIES
    ) -> "OperatorTranscript":
        """Return a fresh empty transcript.

        Equivalent to ``OperatorTranscript()`` with an explicit limit
        argument. Used by the curses wrapper at startup so each
        ``python3 -m brain.ui`` invocation begins with a clean ring
        (corrigenda ruling D — no cross-invocation persistence).
        """
        return cls(entries=(), limit=limit)

    # ------------------------------------------------------------------
    # Append (copy-on-write).
    # ------------------------------------------------------------------

    def append(
        self,
        kind: TranscriptKind,
        tick_at_event: int,
        text: str,
    ) -> "OperatorTranscript":
        """Return a new transcript with ``(kind, tick_at_event, text)`` appended.

        The transcript itself is not mutated (frozen dataclass). When the
        ring is at :attr:`limit` the oldest entry is dropped before the
        new entry is appended; the resulting transcript has exactly
        ``limit`` entries.

        Drives ``I-UI-19``. Text is bounded printable; non-printable
        text raises a :class:`ValueError`; over-long text is truncated
        with a horizontal-ellipsis suffix (per
        :data:`TRANSCRIPT_MAX_TEXT_LEN`).
        """
        entry = TranscriptEntry(
            kind=kind, tick_at_event=tick_at_event, text=text
        )
        new_entries = self.entries + (entry,)
        if len(new_entries) > self.limit:
            new_entries = new_entries[len(new_entries) - self.limit :]
        return OperatorTranscript(entries=new_entries, limit=self.limit)

    def extend(
        self, items: tuple[tuple[TranscriptKind, int, str], ...]
    ) -> "OperatorTranscript":
        """Return a new transcript with each item appended in order.

        Convenience helper for bulk replay (used by fixtures). Each item
        is a ``(kind, tick_at_event, text)`` triple. The bound is
        enforced after every append, so a bulk extend that exceeds the
        ring limit produces a transcript holding only the most recent
        ``limit`` entries.
        """
        result = self
        for kind, tick, text in items:
            result = result.append(kind, tick, text)
        return result

    # ------------------------------------------------------------------
    # Display projection.
    # ------------------------------------------------------------------

    def to_snapshot(self) -> TranscriptSnapshot:
        """Project this transcript into a renderer-facing
        :class:`brain.ui.layout.TranscriptSnapshot`.

        The snapshot is the read-only projection the layout-aware
        renderer consumes via
        :class:`brain.ui.layout.AgentTuiViewModel`. The projection
        copies each entry into a :class:`TranscriptSnapshotEntry`
        without sharing mutable state (both records are frozen).
        """
        return TranscriptSnapshot(
            entries=tuple(
                TranscriptSnapshotEntry(
                    kind=entry.kind.value,
                    tick_at_event=entry.tick_at_event,
                    text=entry.text,
                )
                for entry in self.entries
            )
        )

    # ------------------------------------------------------------------
    # Inspection helpers.
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.entries)

    def last(self) -> "TranscriptEntry | None":
        """Return the most recent entry, or ``None`` for an empty ring."""
        if not self.entries:
            return None
        return self.entries[-1]


__all__ = [
    "TRANSCRIPT_MAX_ENTRIES",
    "TRANSCRIPT_MAX_TEXT_LEN",
    "TranscriptKind",
    "ALLOWED_TRANSCRIPT_KINDS",
    "TranscriptEntry",
    "OperatorTranscript",
]
