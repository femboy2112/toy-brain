"""Bottom composer edit model for the agent-style Operator TUI.

This module defines the immutable :class:`ComposerState` record, the
closed enumeration :class:`ComposerAction` of edit events, the
:class:`ComposerSubmission` record returned on Enter, and the pure
:class:`BottomComposer` driver that transitions one state to the next.

The composer is a **typed local UI command line**, not a chat surface.
It carries no callable, file handle, socket, real LLM client, or
mutable reference into ``BrainState`` or developmental histories. It
performs no I/O, no shell expansion, no eval / exec / compile, no
network access, and no subprocess spawn. Edit events are pure
state-to-state transitions over bounded printable text.

Catalog rows driven from here:

* ``I-UI-17`` (REQUIRED) — ``BottomComposer`` edit model supports
  ``INSERT_CHAR`` / ``BACKSPACE`` / ``SUBMIT`` / ``CLEAR_BUFFER`` /
  ``HISTORY_PREV`` / ``HISTORY_NEXT`` deterministically. The history
  ring is bounded; the buffer is bounded by
  :data:`MAX_COMPOSER_BUFFER`; non-printable ``INSERT_CHAR`` payloads
  are rejected.

This module imports only standard-library typing helpers, ``dataclasses``,
and ``enum``. It does **not** import :mod:`curses`, :mod:`brain.tick`,
:mod:`brain.tlica`, :mod:`brain.llm`, :mod:`os`, :mod:`subprocess`,
:mod:`socket`, :mod:`urllib`, :mod:`http`, :mod:`requests`, :mod:`json`,
:mod:`yaml`, :mod:`ast`, :mod:`code`, or :mod:`codeop`. The companion
:mod:`brain.ui.command_line` consumes :class:`ComposerSubmission`
records emitted by :class:`BottomComposer`.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Bounds shared with the kickoff and corrigenda.
# ---------------------------------------------------------------------------


#: Maximum number of printable characters the composer buffer accepts.
#: Mirrors the bounded-text policy in :data:`brain.ui.session.MAX_STATUS_TEXT_LEN`
#: so an over-long paste cannot blow past the composer pane budget.
#: Drives the buffer half of ``I-UI-17``.
MAX_COMPOSER_BUFFER: int = 240


#: Maximum number of submitted lines retained in the composer history
#: ring. Once the ring reaches this size the oldest entry is dropped on
#: the next successful SUBMIT (copy-on-write). Drives the history half
#: of ``I-UI-17``.
MAX_COMPOSER_HISTORY: int = 32


#: Bounded length for the composer's meta-row status field. Matches the
#: bounded-status policy in :mod:`brain.ui.session`.
MAX_COMPOSER_STATUS: int = 240


#: Composer mode tag advertised on the meta row. The agent-style
#: campaign only supports the typed local command line; no chat mode.
COMPOSER_MODE_LOCAL_CMD: str = "local-cmd"


# ---------------------------------------------------------------------------
# ComposerAction — closed enumeration of edit events.
# ---------------------------------------------------------------------------


class ComposerAction(str, Enum):
    """Closed enumeration of edit events the composer accepts.

    Drives ``I-UI-17``. Any value supplied to :meth:`BottomComposer.apply`
    that is not a member of this enumeration raises before the composer
    state is mutated.
    """

    INSERT_CHAR = "insert_char"
    BACKSPACE = "backspace"
    SUBMIT = "submit"
    CLEAR_BUFFER = "clear_buffer"
    HISTORY_PREV = "history_prev"
    HISTORY_NEXT = "history_next"


# ---------------------------------------------------------------------------
# Bounded-printable helper.
# ---------------------------------------------------------------------------


def _bound_printable(label: str, value: str, *, limit: int) -> str:
    """Reject non-printable text; truncate at *limit*.

    The composer never accepts terminal control characters or callables
    in any text field. Truncation preserves printability (the surviving
    prefix is printable because the whole string was). Empty strings are
    allowed and represent a cleared buffer or empty status line.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"I-UI-17 violated: {label} must be a str (got {type(value).__name__})"
        )
    if value and not value.isprintable():
        raise ValueError(
            f"I-UI-17 violated: {label} must be printable text (got {value!r})"
        )
    if len(value) > limit:
        return value[: limit - 1] + "…"
    return value


# ---------------------------------------------------------------------------
# ComposerState — immutable record of the composer's edit state.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ComposerState:
    """Immutable snapshot of the bottom composer's edit state.

    Fields:

    * ``buffer`` — printable text currently in the editor row.
    * ``cursor`` — column offset within ``buffer``
      (``0 <= cursor <= len(buffer)``). The composer always edits at the
      tail of the buffer in this campaign; the cursor field is preserved
      so future steps can introduce caret movement without re-shaping
      the record.
    * ``history`` — tuple of previously submitted lines, oldest first.
      Bounded by :data:`MAX_COMPOSER_HISTORY`.
    * ``history_cursor`` — index into ``history`` for HISTORY_PREV /
      HISTORY_NEXT recall. ``None`` means "no history entry is currently
      selected" (the buffer is the operator's live input).
    * ``mode`` — composer mode tag (only :data:`COMPOSER_MODE_LOCAL_CMD`
      in this campaign).
    * ``status_line`` — bounded printable meta-row text. Set by SUBMIT on
      an empty buffer (drives ruling A in
      ``OPERATOR_TUI_AGENT_LAYOUT_CORRIGENDA.md``), or by the wrapper
      after a successful parse via :meth:`with_status`.

    Drives ``I-UI-17``: the record is frozen, every field is a bounded
    primitive or a tuple of bounded primitives, and the slot list
    excludes any callable, file handle, socket, or LLM-client shape.
    """

    buffer: str = ""
    cursor: int = 0
    history: tuple[str, ...] = ()
    history_cursor: Optional[int] = None
    mode: str = COMPOSER_MODE_LOCAL_CMD
    status_line: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.buffer, str):
            raise TypeError(
                "ComposerState.buffer must be str "
                f"(got {type(self.buffer).__name__})"
            )
        if self.buffer and not self.buffer.isprintable():
            raise ValueError(
                "I-UI-17 violated: ComposerState.buffer must be printable "
                f"(got {self.buffer!r})"
            )
        if len(self.buffer) > MAX_COMPOSER_BUFFER:
            raise ValueError(
                "I-UI-17 violated: ComposerState.buffer exceeds bound "
                f"(len={len(self.buffer)}, limit={MAX_COMPOSER_BUFFER})"
            )
        if not isinstance(self.cursor, int) or isinstance(self.cursor, bool):
            raise TypeError(
                "ComposerState.cursor must be int "
                f"(got {type(self.cursor).__name__})"
            )
        if self.cursor < 0:
            raise ValueError(
                f"ComposerState.cursor must be non-negative (got {self.cursor!r})"
            )
        if self.cursor > len(self.buffer):
            raise ValueError(
                "ComposerState.cursor exceeds buffer length "
                f"(cursor={self.cursor}, len(buffer)={len(self.buffer)})"
            )
        if not isinstance(self.history, tuple):
            raise TypeError(
                "ComposerState.history must be a tuple "
                f"(got {type(self.history).__name__})"
            )
        if len(self.history) > MAX_COMPOSER_HISTORY:
            raise ValueError(
                "I-UI-17 violated: ComposerState.history exceeds bound "
                f"(len={len(self.history)}, limit={MAX_COMPOSER_HISTORY})"
            )
        for entry in self.history:
            if not isinstance(entry, str):
                raise TypeError(
                    "ComposerState.history entries must be str "
                    f"(got {type(entry).__name__})"
                )
            if entry and not entry.isprintable():
                raise ValueError(
                    "I-UI-17 violated: ComposerState.history entry is not "
                    f"printable ({entry!r})"
                )
            if len(entry) > MAX_COMPOSER_BUFFER:
                raise ValueError(
                    "I-UI-17 violated: ComposerState.history entry exceeds "
                    f"bound (len={len(entry)}, limit={MAX_COMPOSER_BUFFER})"
                )
        if self.history_cursor is not None:
            if (
                not isinstance(self.history_cursor, int)
                or isinstance(self.history_cursor, bool)
            ):
                raise TypeError(
                    "ComposerState.history_cursor must be int | None "
                    f"(got {type(self.history_cursor).__name__})"
                )
            if not (0 <= self.history_cursor < len(self.history)):
                raise ValueError(
                    "ComposerState.history_cursor must index history "
                    f"(got {self.history_cursor!r}, len(history)={len(self.history)})"
                )
        if not isinstance(self.mode, str) or not self.mode:
            raise ValueError(
                "ComposerState.mode must be a non-empty str "
                f"(got {self.mode!r})"
            )
        if self.mode != COMPOSER_MODE_LOCAL_CMD:
            raise ValueError(
                "I-UI-17 violated: ComposerState.mode must be "
                f"{COMPOSER_MODE_LOCAL_CMD!r} (got {self.mode!r})"
            )
        if not isinstance(self.status_line, str):
            raise TypeError(
                "ComposerState.status_line must be str "
                f"(got {type(self.status_line).__name__})"
            )
        if self.status_line and not self.status_line.isprintable():
            raise ValueError(
                "I-UI-17 violated: ComposerState.status_line must be "
                f"printable (got {self.status_line!r})"
            )
        if len(self.status_line) > MAX_COMPOSER_STATUS:
            raise ValueError(
                "I-UI-17 violated: ComposerState.status_line exceeds bound "
                f"(len={len(self.status_line)}, limit={MAX_COMPOSER_STATUS})"
            )

    # ------------------------------------------------------------------
    # Convenience constructors / projections.
    # ------------------------------------------------------------------

    @classmethod
    def empty(cls) -> "ComposerState":
        """Return a fresh empty composer state.

        Equivalent to ``ComposerState()`` but reads as the wrapper's
        startup intent ("the composer begins empty").
        """
        return cls()

    def with_status(self, status: str) -> "ComposerState":
        """Return a copy with ``status_line`` replaced by *status*.

        Used by the wrapper after a successful parse to surface
        :attr:`brain.ui.session.OperatorSession.status_message` on the
        composer's meta row (per corrigenda ruling A). Truncates and
        rejects non-printable text via :func:`_bound_printable`.
        """
        bounded = _bound_printable(
            "ComposerState.status_line", status, limit=MAX_COMPOSER_STATUS
        )
        return ComposerState(
            buffer=self.buffer,
            cursor=self.cursor,
            history=self.history,
            history_cursor=self.history_cursor,
            mode=self.mode,
            status_line=bounded,
        )


# ---------------------------------------------------------------------------
# ComposerSubmission — record returned on SUBMIT with a non-empty buffer.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ComposerSubmission:
    """Immutable submission record returned by :meth:`BottomComposer.apply`.

    A submission is produced when :data:`ComposerAction.SUBMIT` is
    applied to a state whose buffer (after stripping whitespace) is
    non-empty. The submission carries the *exact* buffer contents as
    typed (no whitespace stripping; the parser handles its own
    normalization) so future audits can correlate the operator's typed
    text with the parser's behaviour. The accompanying ``next_state``
    field is the post-submit composer state (buffer cleared, history
    extended, history_cursor reset).
    """

    line: str
    next_state: ComposerState

    def __post_init__(self) -> None:
        if not isinstance(self.line, str):
            raise TypeError(
                "ComposerSubmission.line must be str "
                f"(got {type(self.line).__name__})"
            )
        if self.line and not self.line.isprintable():
            raise ValueError(
                "I-UI-17 violated: ComposerSubmission.line must be printable "
                f"(got {self.line!r})"
            )
        if len(self.line) > MAX_COMPOSER_BUFFER:
            raise ValueError(
                "I-UI-17 violated: ComposerSubmission.line exceeds bound "
                f"(len={len(self.line)}, limit={MAX_COMPOSER_BUFFER})"
            )
        if not isinstance(self.next_state, ComposerState):
            raise TypeError(
                "ComposerSubmission.next_state must be a ComposerState "
                f"(got {type(self.next_state).__name__})"
            )


# ---------------------------------------------------------------------------
# BottomComposer — pure state transition driver.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BottomComposer:
    """Pure state transition driver for the bottom composer.

    The composer is stateless across calls: every call to :meth:`apply`
    takes the current :class:`ComposerState` plus a
    :class:`ComposerAction` (and optional payload) and returns either
    the next :class:`ComposerState` or a :class:`ComposerSubmission`
    (which itself carries the next state).

    Drives ``I-UI-17``. The driver carries no mutable fields; it exists
    as a frozen dataclass so its public surface is a clean import target
    for the curses wrapper.
    """

    def apply(
        self,
        state: ComposerState,
        action: ComposerAction,
        *,
        char: Optional[str] = None,
    ) -> ComposerState | ComposerSubmission:
        """Apply a single edit event to *state* and return the next state.

        ``INSERT_CHAR`` requires a single-character *char* payload (a
        printable string of length 1). Other actions ignore *char*.

        SUBMIT returns a :class:`ComposerSubmission` when the buffer
        (after stripping whitespace) is non-empty; otherwise it returns
        a :class:`ComposerState` with ``status_line`` set to
        ``"empty composer submission"`` and the buffer preserved.

        Every transition is pure: the call performs no I/O and produces
        a fresh frozen record.
        """
        if not isinstance(state, ComposerState):
            raise TypeError(
                "BottomComposer.apply requires a ComposerState "
                f"(got {type(state).__name__})"
            )
        if not isinstance(action, ComposerAction):
            raise TypeError(
                "BottomComposer.apply requires a ComposerAction "
                f"(got {type(action).__name__})"
            )

        if action is ComposerAction.INSERT_CHAR:
            return self._insert_char(state, char)
        if action is ComposerAction.BACKSPACE:
            return self._backspace(state)
        if action is ComposerAction.SUBMIT:
            return self._submit(state)
        if action is ComposerAction.CLEAR_BUFFER:
            return self._clear_buffer(state)
        if action is ComposerAction.HISTORY_PREV:
            return self._history_prev(state)
        if action is ComposerAction.HISTORY_NEXT:
            return self._history_next(state)
        # The enum is closed; this branch is unreachable.
        raise AssertionError(  # pragma: no cover - enum is closed
            f"I-UI-17 violated: unrouted ComposerAction {action!r}"
        )

    # ------------------------------------------------------------------
    # Edit handlers
    # ------------------------------------------------------------------

    def _insert_char(
        self,
        state: ComposerState,
        char: Optional[str],
    ) -> ComposerState:
        if not isinstance(char, str):
            raise TypeError(
                "I-UI-17 violated: INSERT_CHAR requires a str char "
                f"(got {type(char).__name__})"
            )
        if len(char) != 1:
            raise ValueError(
                "I-UI-17 violated: INSERT_CHAR requires a single character "
                f"(got len={len(char)})"
            )
        if not char.isprintable():
            raise ValueError(
                "I-UI-17 violated: INSERT_CHAR requires printable input "
                f"(got {char!r})"
            )
        new_buffer = state.buffer + char
        if len(new_buffer) > MAX_COMPOSER_BUFFER:
            # Reject the insert rather than silently truncating; the
            # wrapper surfaces this as a local UI status update.
            return ComposerState(
                buffer=state.buffer,
                cursor=state.cursor,
                history=state.history,
                history_cursor=state.history_cursor,
                mode=state.mode,
                status_line=_bound_printable(
                    "ComposerState.status_line",
                    f"composer buffer full (limit={MAX_COMPOSER_BUFFER})",
                    limit=MAX_COMPOSER_STATUS,
                ),
            )
        return ComposerState(
            buffer=new_buffer,
            cursor=len(new_buffer),
            history=state.history,
            history_cursor=None,
            mode=state.mode,
            status_line="",
        )

    def _backspace(self, state: ComposerState) -> ComposerState:
        if not state.buffer:
            return ComposerState(
                buffer=state.buffer,
                cursor=state.cursor,
                history=state.history,
                history_cursor=state.history_cursor,
                mode=state.mode,
                status_line="",
            )
        new_buffer = state.buffer[:-1]
        return ComposerState(
            buffer=new_buffer,
            cursor=len(new_buffer),
            history=state.history,
            history_cursor=None,
            mode=state.mode,
            status_line="",
        )

    def _submit(
        self, state: ComposerState
    ) -> ComposerState | ComposerSubmission:
        line = state.buffer
        if not line.strip():
            # Empty submission: clear status flag is the meta-row hint;
            # the buffer is preserved so the operator does not lose a
            # typed leading-whitespace draft.
            return ComposerState(
                buffer=state.buffer,
                cursor=state.cursor,
                history=state.history,
                history_cursor=None,
                mode=state.mode,
                status_line=_bound_printable(
                    "ComposerState.status_line",
                    "empty composer submission",
                    limit=MAX_COMPOSER_STATUS,
                ),
            )
        # Successful submit: append to history (dedup against the most
        # recent entry to avoid filling the ring with repeats), bound
        # the ring, clear the buffer.
        new_history = self._extend_history(state.history, line)
        next_state = ComposerState(
            buffer="",
            cursor=0,
            history=new_history,
            history_cursor=None,
            mode=state.mode,
            status_line="",
        )
        return ComposerSubmission(line=line, next_state=next_state)

    def _clear_buffer(self, state: ComposerState) -> ComposerState:
        return ComposerState(
            buffer="",
            cursor=0,
            history=state.history,
            history_cursor=None,
            mode=state.mode,
            status_line="",
        )

    def _history_prev(self, state: ComposerState) -> ComposerState:
        if not state.history:
            return ComposerState(
                buffer=state.buffer,
                cursor=state.cursor,
                history=state.history,
                history_cursor=None,
                mode=state.mode,
                status_line=_bound_printable(
                    "ComposerState.status_line",
                    "composer history empty",
                    limit=MAX_COMPOSER_STATUS,
                ),
            )
        if state.history_cursor is None:
            new_cursor = len(state.history) - 1
        elif state.history_cursor == 0:
            # Already at the oldest entry; stay there but signal.
            new_cursor = 0
        else:
            new_cursor = state.history_cursor - 1
        recalled = state.history[new_cursor]
        return ComposerState(
            buffer=recalled,
            cursor=len(recalled),
            history=state.history,
            history_cursor=new_cursor,
            mode=state.mode,
            status_line="",
        )

    def _history_next(self, state: ComposerState) -> ComposerState:
        if not state.history:
            return ComposerState(
                buffer=state.buffer,
                cursor=state.cursor,
                history=state.history,
                history_cursor=None,
                mode=state.mode,
                status_line=_bound_printable(
                    "ComposerState.status_line",
                    "composer history empty",
                    limit=MAX_COMPOSER_STATUS,
                ),
            )
        if state.history_cursor is None:
            # Nothing to advance to; preserve current state and signal.
            return ComposerState(
                buffer=state.buffer,
                cursor=state.cursor,
                history=state.history,
                history_cursor=None,
                mode=state.mode,
                status_line="",
            )
        if state.history_cursor >= len(state.history) - 1:
            # Past the newest entry — exit recall mode (live buffer).
            return ComposerState(
                buffer="",
                cursor=0,
                history=state.history,
                history_cursor=None,
                mode=state.mode,
                status_line="",
            )
        new_cursor = state.history_cursor + 1
        recalled = state.history[new_cursor]
        return ComposerState(
            buffer=recalled,
            cursor=len(recalled),
            history=state.history,
            history_cursor=new_cursor,
            mode=state.mode,
            status_line="",
        )

    # ------------------------------------------------------------------
    # History ring helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extend_history(
        history: tuple[str, ...], entry: str
    ) -> tuple[str, ...]:
        """Append *entry* to *history* with dedup-vs-newest and bound enforcement.

        The bound is :data:`MAX_COMPOSER_HISTORY`. When the ring is full
        the oldest entry is dropped before the new entry is appended.
        Consecutive duplicate submissions (the same line twice in a row)
        do not produce a new history entry; the existing newest entry
        stays in place.
        """
        if not isinstance(entry, str):
            raise TypeError(
                "BottomComposer._extend_history entry must be str "
                f"(got {type(entry).__name__})"
            )
        if history and history[-1] == entry:
            return history
        new = history + (entry,)
        if len(new) > MAX_COMPOSER_HISTORY:
            new = new[len(new) - MAX_COMPOSER_HISTORY:]
        return new


__all__ = [
    "MAX_COMPOSER_BUFFER",
    "MAX_COMPOSER_HISTORY",
    "MAX_COMPOSER_STATUS",
    "COMPOSER_MODE_LOCAL_CMD",
    "ComposerAction",
    "ComposerState",
    "ComposerSubmission",
    "BottomComposer",
]
