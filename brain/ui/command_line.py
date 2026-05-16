"""Typed local command-line parser for the agent-style Operator TUI.

This module defines :class:`LocalCommandLine`, a finite parser over the
ten approved typed verbs (``help``, ``state``, ``tick``, ``output``,
``worldlet``, ``repl``, ``queue``, ``step``, ``clear``, ``quit``), the
:class:`LocalCommandError` record returned for invalid input, and the
:class:`ParseResult` union returned by :meth:`LocalCommandLine.parse`.

The parser is **inert**: it performs no shell expansion, no JSON / YAML
/ TOML parsing, no ``eval`` / ``exec`` / ``compile`` / ``__import__``
call, no ``os.system`` / ``subprocess`` / ``socket`` / ``urllib`` /
``http`` / ``requests`` access, and no filesystem mutation. It accepts
no callable, file handle, socket, or LLM-client value. Its only output
is either a :class:`brain.ui.commands.Command` record or a
:class:`LocalCommandError` carrying bounded printable text.

Catalog rows driven from here:

* ``I-UI-18`` (REQUIRED) — ``LocalCommandLine`` parser is finite, typed,
  and maps only to approved :class:`brain.ui.commands.OperatorCommand` /
  :class:`brain.ui.commands.QueuePerceptPayload` routes. Anything else
  surfaces as a local status / error only.

This module imports only standard-library typing helpers, ``dataclasses``,
and the local :mod:`brain.ui.commands` surface. It does **not** import
:mod:`curses`, :mod:`brain.tick`, :mod:`brain.tlica`, :mod:`brain.llm`,
:mod:`os`, :mod:`subprocess`, :mod:`socket`, :mod:`urllib`, :mod:`http`,
:mod:`requests`, :mod:`json`, :mod:`yaml`, :mod:`ast`, :mod:`code`, or
:mod:`codeop`. The companion :mod:`brain.ui.composer` produces the
:class:`brain.ui.composer.ComposerSubmission` records this parser
consumes.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Union

from brain.development.text_stream import (
    STREAM_TEXT_MAX_LEN,
)
from brain.ui.commands import (
    STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN,
    Command,
    OperatorCommand,
    make_command,
)
from brain.toce_core import ContentState


# ---------------------------------------------------------------------------
# Module-level constants for /queue defaults.
# ---------------------------------------------------------------------------
#
# These mirror the defaults in :mod:`brain.ui.tui` (``PROMPT_DEFAULT_*``)
# so the typed ``/queue`` path produces percepts indistinguishable from
# the curses prompt path. They are redeclared here rather than imported
# from :mod:`brain.ui.tui` because that module imports :mod:`curses`,
# which :mod:`brain.ui.command_line` is forbidden to depend on (see
# ``OPERATOR_TUI_AGENT_LAYOUT_CORRIGENDA.md`` section 3.4 and ruling G).


#: Safe default :class:`ContentState` value used when the operator types
#: ``/queue`` without supplying TOCE classification flags. Matches
#: :data:`brain.ui.tui.PROMPT_DEFAULT_CONTENT_STATE`.
LOCAL_CMD_DEFAULT_CONTENT_STATE: ContentState = ContentState(
    available=True,
    verification_path=True,
    retrievable=True,
    operative=True,
)


#: Safe default ``initial_rho`` for typed ``/queue`` percepts. Encoded
#: as a :class:`fractions.Fraction` matching the documented default in
#: :data:`brain.ui.tui.PROMPT_DEFAULT_RHO` (``"1/2"``).
LOCAL_CMD_DEFAULT_RHO: Fraction = Fraction(1, 2)


#: Maximum length of operator-supplied text for typed /queue. Mirrors
#: :data:`brain.ui.tui.PROMPT_MAX_INPUT_LEN` so the typed path stays
#: bounded by the same per-field budget as the curses prompt.
LOCAL_CMD_MAX_FIELD_LEN: int = 64


#: Bounded length for parser-emitted error messages.
LOCAL_CMD_MAX_ERROR_LEN: int = 240


#: Closed enumeration of typed verbs the parser accepts. Verbs are
#: matched lowercase; a verb outside this set surfaces as
#: :class:`LocalCommandError`. The set is intentionally a frozen
#: ``tuple`` so the iteration order is deterministic for ``/help``
#: rendering.
LOCAL_COMMAND_VERBS: tuple[str, ...] = (
    "help",
    "state",
    "tick",
    "output",
    "worldlet",
    "repl",
    "queue",
    "step",
    "clear",
    "quit",
    "stream",
    "stream-summary",
    "stream-candidates",
    "stream-promote",
    "save-session",
    "load-session",
)


# ---------------------------------------------------------------------------
# LocalCommandError — bounded printable error record.
# ---------------------------------------------------------------------------


def _bound_printable_error(message: str) -> str:
    """Return *message* truncated to :data:`LOCAL_CMD_MAX_ERROR_LEN` and asserted printable.

    The parser never returns an error containing a terminal control
    sequence or a callable; this helper enforces both halves.
    """
    if not isinstance(message, str):
        raise TypeError(
            f"I-UI-18 violated: LocalCommandError.message must be str "
            f"(got {type(message).__name__})"
        )
    if message and not message.isprintable():
        # Replace non-printables with a placeholder rather than raising:
        # the error text is operator-facing and a non-printable byte
        # inside an unfamiliar verb should surface as visible feedback.
        # Truncate to the first non-printable, append a marker.
        printable_prefix = "".join(
            ch if ch.isprintable() else "?" for ch in message
        )
        message = printable_prefix
    if len(message) > LOCAL_CMD_MAX_ERROR_LEN:
        message = message[: LOCAL_CMD_MAX_ERROR_LEN - 1] + "…"
    return message


@dataclass(frozen=True, slots=True)
class LocalCommandError:
    """Bounded printable error produced by :meth:`LocalCommandLine.parse`.

    The record carries no callable, file handle, or socket. The
    ``message`` field is bounded printable text. Drives ``I-UI-18``:
    invalid commands stay as local status/error only.
    """

    message: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "message", _bound_printable_error(self.message)
        )


#: The :class:`LocalCommandLine.parse` return type.
ParseResult = Union[Command, LocalCommandError]


# ---------------------------------------------------------------------------
# LocalCommandLine — finite parser.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LocalCommandLine:
    """Finite parser over the typed local command verbs.

    The parser is pure: every call to :meth:`parse` is a function of
    its input string. The parser stores no state, opens no file handle,
    and accepts no callable.

    Drives ``I-UI-18``. The verb dispatch table is the closed
    enumeration :data:`LOCAL_COMMAND_VERBS`. Unknown verbs, missing
    arguments, and constructor rejections from
    :class:`brain.ui.commands.QueuePerceptPayload` all return
    :class:`LocalCommandError`.
    """

    def parse(self, line: object) -> ParseResult:
        """Parse one operator-typed line.

        The line is expected to be a :class:`str` produced by
        :class:`brain.ui.composer.BottomComposer` (which already
        enforces printability). The parser tolerates leading and
        trailing whitespace.

        Returns either a :class:`Command` (success) or a
        :class:`LocalCommandError` (rejection). Never raises for
        operator-facing failures; type errors on non-``str`` input
        still raise so a caller passing a wrong type is detected.
        """
        if not isinstance(line, str):
            raise TypeError(
                f"I-UI-18 violated: LocalCommandLine.parse requires str "
                f"(got {type(line).__name__})"
            )

        stripped = line.strip()
        if not stripped:
            return LocalCommandError("empty command")
        if not stripped.startswith("/"):
            return LocalCommandError("expected leading '/'")

        body = stripped[1:]  # drop the '/'
        if not body or body[0].isspace():
            return LocalCommandError("expected verb after '/'")

        # Split into at most two tokens: verb + remainder. The remainder
        # is left as-is so the /queue handler can split it again into
        # (content_id, text).
        tokens = body.split(None, 1)
        verb = tokens[0].lower()
        remainder = tokens[1] if len(tokens) > 1 else ""

        if verb not in LOCAL_COMMAND_VERBS:
            return LocalCommandError(
                f"unknown command: /{verb}"
            )

        # Dispatch table. Every branch returns either a Command or
        # LocalCommandError. No branch performs I/O.
        if verb == "help":
            return self._parse_no_args(verb, remainder, OperatorCommand.HELP)
        if verb == "state":
            return self._parse_no_args(
                verb, remainder, OperatorCommand.INSPECT_STATE
            )
        if verb == "tick":
            return self._parse_no_args(
                verb, remainder, OperatorCommand.INSPECT_TICK
            )
        if verb == "output":
            return self._parse_no_args(
                verb, remainder, OperatorCommand.INSPECT_OUTPUT
            )
        if verb == "worldlet":
            return self._parse_no_args(
                verb, remainder, OperatorCommand.INSPECT_WORLDLET
            )
        if verb == "repl":
            return self._parse_no_args(
                verb, remainder, OperatorCommand.INSPECT_REPL
            )
        if verb == "step":
            return self._parse_no_args(verb, remainder, OperatorCommand.STEP_TICK)
        if verb == "clear":
            return self._parse_no_args(
                verb, remainder, OperatorCommand.CLEAR_STATUS
            )
        if verb == "quit":
            return self._parse_no_args(verb, remainder, OperatorCommand.QUIT)
        if verb == "queue":
            return self._parse_queue(remainder)
        if verb == "stream":
            return self._parse_stream(remainder)
        if verb == "stream-summary":
            return self._parse_no_args(
                verb, remainder, OperatorCommand.INSPECT_STREAM_SUMMARY
            )
        if verb == "stream-candidates":
            return self._parse_no_args(
                verb, remainder, OperatorCommand.INSPECT_STREAM_CANDIDATES
            )
        if verb == "stream-promote":
            return self._parse_stream_promote(remainder)
        if verb == "save-session":
            return self._parse_no_args(
                verb, remainder, OperatorCommand.SAVE_SESSION
            )
        if verb == "load-session":
            return self._parse_no_args(
                verb, remainder, OperatorCommand.LOAD_SESSION
            )
        # Unreachable: every verb in LOCAL_COMMAND_VERBS is handled above.
        raise AssertionError(  # pragma: no cover - enumeration is closed
            f"I-UI-18 violated: unrouted typed verb /{verb}"
        )

    # ------------------------------------------------------------------
    # Verb handlers
    # ------------------------------------------------------------------

    def _parse_no_args(
        self,
        verb: str,
        remainder: str,
        kind: OperatorCommand,
    ) -> ParseResult:
        if remainder.strip():
            return LocalCommandError(
                f"/{verb} does not accept arguments"
            )
        return make_command(kind)

    def _parse_queue(self, remainder: str) -> ParseResult:
        if not remainder.strip():
            return LocalCommandError(
                "/queue requires <content_id> <text>"
            )
        parts = remainder.split(None, 1)
        if len(parts) != 2:
            return LocalCommandError(
                "/queue requires <content_id> <text>"
            )
        content_id, text = parts[0], parts[1]
        # Strip trailing whitespace from text but preserve internal
        # spaces; an empty text body after the split is rejected.
        text = text.rstrip()
        if not text:
            return LocalCommandError(
                "/queue requires <content_id> <text>"
            )
        # Per-field length bounds: keep the typed path's per-field budget
        # aligned with the curses prompt's ``PROMPT_MAX_INPUT_LEN``.
        if len(content_id) > LOCAL_CMD_MAX_FIELD_LEN:
            return LocalCommandError(
                f"/queue content_id exceeds {LOCAL_CMD_MAX_FIELD_LEN} chars"
            )
        if len(text) > LOCAL_CMD_MAX_FIELD_LEN:
            return LocalCommandError(
                f"/queue text exceeds {LOCAL_CMD_MAX_FIELD_LEN} chars"
            )
        # Delegate domain validation to PerceptEvent (via
        # QueuePerceptPayload's __post_init__) by attempting the build.
        # A constructor failure becomes a LocalCommandError; this is the
        # single validation point per corrigenda section 7.
        try:
            command = make_command(
                OperatorCommand.QUEUE_PERCEPT,
                content_id=content_id,
                text=text,
                content_state=LOCAL_CMD_DEFAULT_CONTENT_STATE,
                initial_rho=LOCAL_CMD_DEFAULT_RHO,
            )
        except (TypeError, ValueError) as exc:
            return LocalCommandError(f"/queue rejected: {exc}")
        return command

    def _parse_stream(self, remainder: str) -> ParseResult:
        # /stream preserves the full operator-supplied text body so that
        # the bounded TextStreamChunk constructor sees exactly what the
        # operator typed (with one trailing newline-style strip).
        text = remainder.rstrip("\n")
        if not text or not text.strip():
            return LocalCommandError(
                "/stream requires <text>"
            )
        if len(text) > STREAM_TEXT_MAX_LEN:
            return LocalCommandError(
                f"/stream text exceeds {STREAM_TEXT_MAX_LEN} chars"
            )
        try:
            command = make_command(
                OperatorCommand.STREAM_APPEND,
                stream_text=text,
            )
        except (TypeError, ValueError) as exc:
            return LocalCommandError(f"/stream rejected: {exc}")
        return command

    def _parse_stream_promote(self, remainder: str) -> ParseResult:
        candidate_id = remainder.strip()
        if not candidate_id:
            return LocalCommandError(
                "/stream-promote requires <candidate_id>"
            )
        # The candidate_id is split-on-whitespace; reject extra tokens to
        # match the rest of the parser's finite-arity discipline.
        parts = candidate_id.split()
        if len(parts) != 1:
            return LocalCommandError(
                "/stream-promote requires exactly one <candidate_id>"
            )
        candidate_id = parts[0]
        if len(candidate_id) > STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN:
            return LocalCommandError(
                "/stream-promote candidate_id exceeds "
                f"{STREAM_PROMOTE_CANDIDATE_ID_MAX_LEN} chars"
            )
        try:
            command = make_command(
                OperatorCommand.STREAM_PROMOTE,
                candidate_id=candidate_id,
            )
        except (TypeError, ValueError) as exc:
            return LocalCommandError(f"/stream-promote rejected: {exc}")
        return command


# ---------------------------------------------------------------------------
# Help-text rendering helper.
# ---------------------------------------------------------------------------


#: Per-verb one-line help strings. Used by the curses wrapper (Step 10)
#: to render the typed-command help pane. The list is deterministic and
#: matches :data:`LOCAL_COMMAND_VERBS` order.
LOCAL_COMMAND_HELP: tuple[tuple[str, str], ...] = (
    ("/help", "show this typed-command help"),
    ("/state", "inspect BrainState"),
    ("/tick", "inspect latest TickRecord"),
    ("/output", "inspect OutputHistory"),
    ("/worldlet", "inspect WorldletHistory"),
    ("/repl", "inspect Proto-BASIC REPL history"),
    ("/queue <id> <text>", "queue a percept candidate"),
    ("/step", "advance one tick using the head of the queue"),
    ("/clear", "clear local status/error (^U clears composer)"),
    ("/quit", "exit the operator session"),
    ("/stream <text>", "append bounded text to the local stream history"),
    ("/stream-summary", "inspect local stream summary"),
    ("/stream-candidates", "inspect local stream promotion candidates"),
    ("/stream-promote <id>", "queue one explicit promotion candidate"),
    ("/save-session", "save the session to the configured DB"),
    ("/load-session", "load the session from the configured DB"),
)


__all__ = [
    "LOCAL_CMD_DEFAULT_CONTENT_STATE",
    "LOCAL_CMD_DEFAULT_RHO",
    "LOCAL_CMD_MAX_FIELD_LEN",
    "LOCAL_CMD_MAX_ERROR_LEN",
    "LOCAL_COMMAND_VERBS",
    "LOCAL_COMMAND_HELP",
    "LocalCommandError",
    "ParseResult",
    "LocalCommandLine",
]
