"""Composer + typed local-command-line fixtures.

Drives:

* ``I-UI-17`` (REQUIRED) — :class:`brain.ui.composer.BottomComposer`
  edit model supports ``INSERT_CHAR`` / ``BACKSPACE`` / ``SUBMIT`` /
  ``CLEAR_BUFFER`` / ``HISTORY_PREV`` / ``HISTORY_NEXT`` deterministically.
  Buffer and history are bounded. Non-printable INSERT_CHAR payloads
  are rejected.
* ``I-UI-18`` (REQUIRED) — :class:`brain.ui.command_line.LocalCommandLine`
  is a finite typed parser. Each verb maps to a single approved
  :class:`brain.ui.commands.OperatorCommand` (or, for ``/queue``, a
  :class:`brain.ui.commands.QueuePerceptPayload`-wrapped command).
  Invalid inputs surface as :class:`brain.ui.command_line.LocalCommandError`
  without invoking any kernel or LLM surface.

The fixtures are pure: they exercise the composer and parser
state-by-state and assert their pre/post invariants. No real curses,
filesystem, network, subprocess, or LLM call is made.
"""
from __future__ import annotations

from fractions import Fraction

from brain.invariants import register
from brain.ui.commands import (
    Command,
    OperatorCommand,
    QueuePerceptPayload,
)
from brain.ui.composer import (
    BottomComposer,
    COMPOSER_MODE_LOCAL_CMD,
    ComposerAction,
    ComposerState,
    ComposerSubmission,
    MAX_COMPOSER_BUFFER,
    MAX_COMPOSER_HISTORY,
)
from brain.ui.command_line import (
    LOCAL_CMD_DEFAULT_CONTENT_STATE,
    LOCAL_CMD_DEFAULT_RHO,
    LOCAL_CMD_MAX_FIELD_LEN,
    LOCAL_COMMAND_HELP,
    LOCAL_COMMAND_VERBS,
    LocalCommandError,
    LocalCommandLine,
)
from brain.tlica.profile import COGITO_ID


# ---------------------------------------------------------------------------
# I-UI-17 — BottomComposer edit model.
# ---------------------------------------------------------------------------


@register("I-UI-17", status="REQUIRED")
def check_I_UI_17_composer_edit_model_is_deterministic() -> None:
    composer = BottomComposer()
    empty = ComposerState.empty()

    # ---- Defaults ----------------------------------------------------
    assert empty.buffer == ""
    assert empty.cursor == 0
    assert empty.history == ()
    assert empty.history_cursor is None
    assert empty.mode == COMPOSER_MODE_LOCAL_CMD
    assert empty.status_line == ""

    # ---- INSERT_CHAR: each character extends the buffer and resets
    # the history cursor. The cursor always tracks the buffer tail in
    # this campaign.
    s = empty
    for ch in "/queue beta hello":
        out = composer.apply(s, ComposerAction.INSERT_CHAR, char=ch)
        assert isinstance(out, ComposerState), (
            "I-UI-17: INSERT_CHAR must return a ComposerState"
        )
        s = out
    assert s.buffer == "/queue beta hello"
    assert s.cursor == len(s.buffer)
    assert s.status_line == ""

    # INSERT_CHAR requires a single printable character.
    try:
        composer.apply(empty, ComposerAction.INSERT_CHAR, char="ab")
    except ValueError:
        pass
    else:
        raise AssertionError("I-UI-17: multi-char INSERT_CHAR was not rejected")

    try:
        composer.apply(empty, ComposerAction.INSERT_CHAR, char="\x01")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-UI-17: non-printable INSERT_CHAR was not rejected"
        )

    try:
        composer.apply(empty, ComposerAction.INSERT_CHAR, char=None)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError("I-UI-17: INSERT_CHAR with None char was not rejected")

    # INSERT_CHAR at buffer-limit produces a status-only update; buffer
    # stays at the bound rather than overflowing.
    near_full = ComposerState(
        buffer="a" * MAX_COMPOSER_BUFFER,
        cursor=MAX_COMPOSER_BUFFER,
    )
    overflow = composer.apply(near_full, ComposerAction.INSERT_CHAR, char="b")
    assert isinstance(overflow, ComposerState)
    assert overflow.buffer == near_full.buffer, (
        "I-UI-17: INSERT_CHAR past bound mutated buffer"
    )
    assert "full" in overflow.status_line, (
        f"I-UI-17: INSERT_CHAR overflow status missing 'full': {overflow.status_line!r}"
    )

    # ---- BACKSPACE: drops one char; on empty buffer it is a no-op.
    s2 = s
    s2 = composer.apply(s2, ComposerAction.BACKSPACE, char=None)  # type: ignore[assignment]
    assert isinstance(s2, ComposerState)
    assert s2.buffer == "/queue beta hell"
    assert s2.cursor == len(s2.buffer)

    s_empty_back = composer.apply(empty, ComposerAction.BACKSPACE)
    assert isinstance(s_empty_back, ComposerState)
    assert s_empty_back.buffer == ""
    assert s_empty_back.status_line == ""

    # ---- CLEAR_BUFFER: empties buffer but preserves history.
    cleared = composer.apply(s, ComposerAction.CLEAR_BUFFER)
    assert isinstance(cleared, ComposerState)
    assert cleared.buffer == ""
    assert cleared.cursor == 0
    assert cleared.history == s.history
    assert cleared.history_cursor is None

    # ---- SUBMIT: non-empty buffer yields a ComposerSubmission with the
    # exact buffer contents, clears the buffer, and appends to history.
    sub = composer.apply(s, ComposerAction.SUBMIT)
    assert isinstance(sub, ComposerSubmission)
    assert sub.line == s.buffer
    assert sub.next_state.buffer == ""
    assert sub.next_state.cursor == 0
    assert sub.next_state.history == (s.buffer,)
    assert sub.next_state.history_cursor is None

    # SUBMIT on an empty buffer is rejected as a status-only event
    # (drives ruling A: "empty composer submission").
    empty_submit = composer.apply(empty, ComposerAction.SUBMIT)
    assert isinstance(empty_submit, ComposerState), (
        "I-UI-17: empty SUBMIT must return a ComposerState, not a submission"
    )
    assert empty_submit.buffer == ""
    assert "empty composer submission" == empty_submit.status_line

    # Whitespace-only buffer is treated as empty for SUBMIT purposes.
    s_ws = empty
    for ch in "   ":
        out = composer.apply(s_ws, ComposerAction.INSERT_CHAR, char=ch)
        assert isinstance(out, ComposerState)
        s_ws = out
    out_ws = composer.apply(s_ws, ComposerAction.SUBMIT)
    assert isinstance(out_ws, ComposerState), (
        "I-UI-17: whitespace-only SUBMIT must not produce a submission"
    )
    assert "empty composer submission" == out_ws.status_line
    # The non-stripped buffer is preserved so the operator does not
    # lose leading whitespace input.
    assert out_ws.buffer == "   "

    # ---- HISTORY_PREV / HISTORY_NEXT on a populated ring.
    # Build a deterministic 3-entry history by submitting three lines.
    after_a = composer.apply(_build_state("/help"), ComposerAction.SUBMIT)
    assert isinstance(after_a, ComposerSubmission)
    sa = after_a.next_state

    # Type and submit "/state" on top of sa.
    for ch in "/state":
        out = composer.apply(sa, ComposerAction.INSERT_CHAR, char=ch)
        assert isinstance(out, ComposerState)
        sa = out
    after_b = composer.apply(sa, ComposerAction.SUBMIT)
    assert isinstance(after_b, ComposerSubmission)
    sb = after_b.next_state

    # Type and submit "/quit" on top of sb.
    for ch in "/quit":
        out = composer.apply(sb, ComposerAction.INSERT_CHAR, char=ch)
        assert isinstance(out, ComposerState)
        sb = out
    after_c = composer.apply(sb, ComposerAction.SUBMIT)
    assert isinstance(after_c, ComposerSubmission)
    populated = after_c.next_state
    assert populated.history == ("/help", "/state", "/quit")

    # PREV walks newest -> oldest.
    p1 = composer.apply(populated, ComposerAction.HISTORY_PREV)
    assert isinstance(p1, ComposerState)
    assert p1.buffer == "/quit"
    assert p1.history_cursor == 2

    p2 = composer.apply(p1, ComposerAction.HISTORY_PREV)
    assert isinstance(p2, ComposerState)
    assert p2.buffer == "/state"
    assert p2.history_cursor == 1

    p3 = composer.apply(p2, ComposerAction.HISTORY_PREV)
    assert isinstance(p3, ComposerState)
    assert p3.buffer == "/help"
    assert p3.history_cursor == 0

    # PREV at oldest entry stays put (deterministic, no wrap).
    p4 = composer.apply(p3, ComposerAction.HISTORY_PREV)
    assert isinstance(p4, ComposerState)
    assert p4.buffer == "/help"
    assert p4.history_cursor == 0

    # NEXT walks oldest -> newest, then exits recall mode.
    n1 = composer.apply(p3, ComposerAction.HISTORY_NEXT)
    assert isinstance(n1, ComposerState)
    assert n1.buffer == "/state"
    assert n1.history_cursor == 1

    n2 = composer.apply(n1, ComposerAction.HISTORY_NEXT)
    assert isinstance(n2, ComposerState)
    assert n2.buffer == "/quit"
    assert n2.history_cursor == 2

    n3 = composer.apply(n2, ComposerAction.HISTORY_NEXT)
    assert isinstance(n3, ComposerState)
    # Past the newest entry -> exit recall mode with empty buffer.
    assert n3.buffer == ""
    assert n3.history_cursor is None

    # HISTORY_PREV / HISTORY_NEXT on an empty history surface a status.
    empty_prev = composer.apply(empty, ComposerAction.HISTORY_PREV)
    assert isinstance(empty_prev, ComposerState)
    assert "history empty" in empty_prev.status_line

    empty_next = composer.apply(empty, ComposerAction.HISTORY_NEXT)
    assert isinstance(empty_next, ComposerState)
    assert "history empty" in empty_next.status_line

    # ---- History dedup: submitting the same line twice in a row does
    # not produce a duplicate history entry.
    s_dup = empty
    for ch in "/help":
        out = composer.apply(s_dup, ComposerAction.INSERT_CHAR, char=ch)
        assert isinstance(out, ComposerState)
        s_dup = out
    sub_dup = composer.apply(s_dup, ComposerAction.SUBMIT)
    assert isinstance(sub_dup, ComposerSubmission)
    s_dup = sub_dup.next_state
    # Type and submit "/help" again.
    for ch in "/help":
        out = composer.apply(s_dup, ComposerAction.INSERT_CHAR, char=ch)
        assert isinstance(out, ComposerState)
        s_dup = out
    sub_dup2 = composer.apply(s_dup, ComposerAction.SUBMIT)
    assert isinstance(sub_dup2, ComposerSubmission)
    assert sub_dup2.next_state.history == ("/help",), (
        f"I-UI-17: dedup failed: {sub_dup2.next_state.history!r}"
    )

    # ---- History ring bound: filling beyond MAX_COMPOSER_HISTORY drops
    # the oldest entry.
    ring = empty
    for i in range(MAX_COMPOSER_HISTORY + 5):
        # Build a distinct line for each iteration so dedup does not
        # collapse them.
        line = f"/help{i}"
        for ch in line:
            out = composer.apply(ring, ComposerAction.INSERT_CHAR, char=ch)
            assert isinstance(out, ComposerState)
            ring = out
        sub_r = composer.apply(ring, ComposerAction.SUBMIT)
        assert isinstance(sub_r, ComposerSubmission)
        ring = sub_r.next_state
    assert len(ring.history) == MAX_COMPOSER_HISTORY, (
        f"I-UI-17: ring bound violated (len={len(ring.history)}, "
        f"limit={MAX_COMPOSER_HISTORY})"
    )
    # The oldest five entries were evicted.
    assert ring.history[0] == "/help5", (
        f"I-UI-17: ring eviction order drift: {ring.history[0]!r}"
    )
    assert ring.history[-1] == f"/help{MAX_COMPOSER_HISTORY + 4}"

    # ---- ComposerState rejects callables, non-strings, oversize text.
    for bad_buffer in (None, 123, ("not", "a", "str"), b"bytes"):
        try:
            ComposerState(buffer=bad_buffer)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError(
                f"I-UI-17: ComposerState accepted bad buffer {bad_buffer!r}"
            )

    try:
        ComposerState(buffer="x" * (MAX_COMPOSER_BUFFER + 1))
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-UI-17: ComposerState accepted oversize buffer"
        )

    try:
        ComposerState(buffer="hello\x01world")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-UI-17: ComposerState accepted non-printable buffer"
        )

    try:
        ComposerState(mode="chat")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-UI-17: ComposerState accepted forbidden mode 'chat'"
        )

    # ---- with_status preserves buffer and bounds the status text.
    s_with = empty.with_status("ok queued")
    assert s_with.buffer == empty.buffer
    assert s_with.status_line == "ok queued"
    # Truncates long status text.
    very_long = "x" * 1024
    s_long = empty.with_status(very_long)
    assert s_long.status_line.endswith("…")
    assert len(s_long.status_line) <= len(very_long)

    # Rejects non-printable status text via _bound_printable's raise path.
    try:
        empty.with_status("bad\x01status")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-UI-17: with_status accepted non-printable status text"
        )

    # ---- Apply with non-enum action / non-state input raises.
    try:
        composer.apply(empty, "submit")  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError("I-UI-17: apply accepted a non-enum action")

    try:
        composer.apply("not a state", ComposerAction.BACKSPACE)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError("I-UI-17: apply accepted a non-state input")


def _build_state(buffer: str) -> ComposerState:
    """Construct a ComposerState whose buffer is *buffer* (no history)."""
    return ComposerState(buffer=buffer, cursor=len(buffer))


# ---------------------------------------------------------------------------
# I-UI-18 — LocalCommandLine parser.
# ---------------------------------------------------------------------------


@register("I-UI-18", status="REQUIRED")
def check_I_UI_18_local_command_line_is_finite_and_typed() -> None:
    parser = LocalCommandLine()

    # ---- Every approved no-arg verb routes to its OperatorCommand.
    expected_no_arg_routes: tuple[tuple[str, OperatorCommand], ...] = (
        ("/help", OperatorCommand.HELP),
        ("/state", OperatorCommand.INSPECT_STATE),
        ("/tick", OperatorCommand.INSPECT_TICK),
        ("/output", OperatorCommand.INSPECT_OUTPUT),
        ("/worldlet", OperatorCommand.INSPECT_WORLDLET),
        ("/repl", OperatorCommand.INSPECT_REPL),
        ("/step", OperatorCommand.STEP_TICK),
        ("/clear", OperatorCommand.CLEAR_STATUS),
        ("/quit", OperatorCommand.QUIT),
    )
    for line, expected_kind in expected_no_arg_routes:
        result = parser.parse(line)
        assert isinstance(result, Command), (
            f"I-UI-18: {line!r} did not return a Command (got {result!r})"
        )
        assert result.kind is expected_kind, (
            f"I-UI-18: {line!r} routed to {result.kind!r}, "
            f"expected {expected_kind!r}"
        )
        assert result.payload is None, (
            f"I-UI-18: {line!r} produced an unexpected payload {result.payload!r}"
        )

    # Whitespace and case tolerance on no-arg verbs.
    for line in ("  /help  ", "/HELP", "/Help"):
        result = parser.parse(line)
        assert isinstance(result, Command)
        assert result.kind is OperatorCommand.HELP

    # No-arg verbs reject trailing arguments.
    bad = parser.parse("/help now")
    assert isinstance(bad, LocalCommandError)
    assert "does not accept arguments" in bad.message

    # ---- /queue happy path produces a QueuePerceptPayload-wrapped command.
    result = parser.parse("/queue beta hello world")
    assert isinstance(result, Command), (
        f"I-UI-18: /queue did not return a Command (got {result!r})"
    )
    assert result.kind is OperatorCommand.QUEUE_PERCEPT
    assert isinstance(result.payload, QueuePerceptPayload)
    assert result.payload.content_id == "beta"
    assert result.payload.text == "hello world"
    assert result.payload.content_state == LOCAL_CMD_DEFAULT_CONTENT_STATE
    assert result.payload.initial_rho == LOCAL_CMD_DEFAULT_RHO
    # Building the event re-runs PerceptEvent's constructor.
    event = result.payload.build_event()
    assert event.content_id == "beta"
    assert event.text == "hello world"

    # ---- /queue rejection paths -------------------------------------
    # Missing arguments.
    err = parser.parse("/queue")
    assert isinstance(err, LocalCommandError)
    assert "<content_id> <text>" in err.message
    err = parser.parse("/queue onlyid")
    assert isinstance(err, LocalCommandError)
    assert "<content_id> <text>" in err.message
    err = parser.parse("/queue   ")
    assert isinstance(err, LocalCommandError)
    assert "<content_id> <text>" in err.message

    # PerceptEvent COGITO_ID rejection surfaces as a LocalCommandError.
    err = parser.parse(f"/queue {COGITO_ID} attempt")
    assert isinstance(err, LocalCommandError), (
        f"I-UI-18: COGITO_ID was not rejected (got {err!r})"
    )
    assert "rejected" in err.message.lower() or "cogito" in err.message.lower()

    # Non-printable text in /queue text -> PerceptEvent rejection.
    err = parser.parse("/queue gamma hello\x01world")
    assert isinstance(err, LocalCommandError)
    # The composer prevents non-printable chars upstream, but the
    # parser still defends against a caller bypassing the composer.

    # Oversize content_id rejected with the per-field bound.
    err = parser.parse(
        "/queue " + ("a" * (LOCAL_CMD_MAX_FIELD_LEN + 1)) + " text"
    )
    assert isinstance(err, LocalCommandError)
    assert "exceeds" in err.message
    # Oversize text rejected with the per-field bound.
    err = parser.parse(
        "/queue beta " + ("x" * (LOCAL_CMD_MAX_FIELD_LEN + 1))
    )
    assert isinstance(err, LocalCommandError)
    assert "exceeds" in err.message

    # ---- Unknown verbs / bad framing --------------------------------
    for line, needle in (
        ("/unknownverb", "unknown command"),
        ("/", "expected verb after '/'"),
        ("/   ", "expected verb after '/'"),
        ("queue beta hello", "expected leading '/'"),
        ("", "empty command"),
        ("   ", "empty command"),
    ):
        err = parser.parse(line)
        assert isinstance(err, LocalCommandError), (
            f"I-UI-18: {line!r} did not return a LocalCommandError"
        )
        assert needle in err.message, (
            f"I-UI-18: {line!r} error missing {needle!r}: {err.message!r}"
        )

    # ---- Non-str input raises TypeError (caller bug, not operator typo).
    for bad in (None, 123, ["/help"]):
        try:
            parser.parse(bad)  # type: ignore[arg-type]
        except TypeError:
            pass
        else:
            raise AssertionError(
                f"I-UI-18: parse accepted non-str input {bad!r}"
            )

    # ---- LocalCommandError is bounded printable.
    long_err = LocalCommandError("x" * 4096)
    assert long_err.message.endswith("…")
    assert len(long_err.message) <= 4096

    # ---- /queue text preserves internal spaces (split(None, 1) only
    # uses the *first* whitespace boundary to separate content_id and
    # text). This is corrigenda section 7.
    result = parser.parse("/queue iota   hello   world  ")
    assert isinstance(result, Command)
    assert result.payload.content_id == "iota"  # type: ignore[union-attr]
    # Trailing whitespace stripped; internal spaces preserved.
    assert result.payload.text == "hello   world"  # type: ignore[union-attr]

    # ---- Verb enumeration coverage: every entry in LOCAL_COMMAND_VERBS
    # is routed by the parser. /queue requires args; the rest are no-arg.
    _arg_verbs = {
        "queue": " beta hello",
        "stream": " hello",
        "stream-promote": " promo-strm-chunk-1",
        "db-backup": " /tmp/brain-i-ui-18-backup.sqlite3",
    }
    routed_verbs: set[str] = set()
    for verb in LOCAL_COMMAND_VERBS:
        line = "/" + verb + _arg_verbs.get(verb, "")
        result = parser.parse(line)
        if isinstance(result, Command):
            routed_verbs.add(verb)
        elif isinstance(result, LocalCommandError):
            raise AssertionError(
                f"I-UI-18: enumerated verb /{verb} did not parse: {result.message!r}"
            )
    assert routed_verbs == set(LOCAL_COMMAND_VERBS), (
        f"I-UI-18: verb coverage drift "
        f"(routed={sorted(routed_verbs)!r}, expected={sorted(LOCAL_COMMAND_VERBS)!r})"
    )

    # ---- LOCAL_COMMAND_HELP is aligned with LOCAL_COMMAND_VERBS.
    # Every verb appears once in the help table (with optional argspec).
    help_keys = [entry[0].split()[0].lstrip("/") for entry in LOCAL_COMMAND_HELP]
    assert set(help_keys) == set(LOCAL_COMMAND_VERBS), (
        "I-UI-18: LOCAL_COMMAND_HELP keys drift from LOCAL_COMMAND_VERBS "
        f"(help={sorted(help_keys)!r}, verbs={sorted(LOCAL_COMMAND_VERBS)!r})"
    )

    # ---- Defaults match the corrigenda-mandated defaults.
    assert LOCAL_CMD_DEFAULT_RHO == Fraction(1, 2)
    assert LOCAL_CMD_DEFAULT_CONTENT_STATE.available is True
    assert LOCAL_CMD_DEFAULT_CONTENT_STATE.verification_path is True
    assert LOCAL_CMD_DEFAULT_CONTENT_STATE.retrievable is True
    assert LOCAL_CMD_DEFAULT_CONTENT_STATE.operative is True


__all__ = [
    "check_I_UI_17_composer_edit_model_is_deterministic",
    "check_I_UI_18_local_command_line_is_finite_and_typed",
]
