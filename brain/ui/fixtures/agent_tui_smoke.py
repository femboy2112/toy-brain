"""Agent-style curses wrapper fixtures.

Drives:

* ``I-UI-21`` (STRUCTURAL) — :mod:`brain.ui.tui` translates curses key
  events into :class:`brain.ui.composer.ComposerAction` calls on
  :class:`brain.ui.composer.BottomComposer` and, on ``SUBMIT``, into
  :meth:`brain.ui.command_line.LocalCommandLine.parse` followed by
  :meth:`brain.ui.session.OperatorSession.dispatch`. The wrapper never
  appends directly to :attr:`brain.ui.session.OperatorSession.event_queue`,
  never mutates :class:`brain.tick.BrainState`, never imports
  :mod:`brain.tick` / :mod:`brain.tlica` / :mod:`brain.llm`, and never
  writes a trace / scenario / developmental-history file. The fixture
  exercises :func:`brain.ui.tui.step_agent_loop` over a scripted sequence
  of raw curses key codes and asserts each delegation property.
* ``I-UI-23`` (OBSERVED) — a scripted agent-style operator walk
  (type ``/queue ...``, press Enter, type ``/step``, press Enter, type
  ``/state``, ``/tick``, ``/help``, ``/quit``) is inspectable: the
  fixture records the sequence of
  :class:`brain.ui.tui.AgentKeyKind` transitions, the parsed
  :class:`brain.ui.commands.Command` records, the dispatched
  :class:`brain.ui.session.OperatorSession` routes, the appended
  :class:`brain.ui.transcript.TranscriptKind` tags, the view transitions,
  and the absence of kernel-boundary leaks. OBSERVED rows do not gate the
  runner.

The fixtures are pure: they construct the wrapper helpers directly,
exercise every documented path, and assert the pre/post invariants
without invoking real curses, the kernel, the LLM seam, the filesystem,
the network, or any developmental history.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Optional

from brain.invariants import register
from brain.io_types import ContentRegistry, TickRecord
from brain.tick import BrainState
from brain.tlica.builders import (
    make_msi,
    make_profile_with_cogito,
    make_ptcns,
)
from brain.tlica.profile import COGITO_ID
from brain.tlica.ptcns import ConsistencyEval
from brain.ui import tui as ui_tui
from brain.ui.command_line import LocalCommandLine
from brain.ui.commands import (
    Command,
    OperatorCommand,
    QueuePerceptPayload,
)
from brain.ui.composer import (
    BottomComposer,
    ComposerAction,
    ComposerState,
)
from brain.ui.session import OperatorSession
from brain.ui.transcript import (
    OperatorTranscript,
    TranscriptKind,
)
from brain.ui.tui import (
    AgentKeyKind,
    AgentKeyRoute,
    AgentStepResult,
    AGENT_HELP_HINT,
    build_agent_keystroke_router,
    build_agent_view_for_session,
    route_agent_keystroke,
    step_agent_loop,
)


# ---------------------------------------------------------------------------
# Deterministic builders.
# ---------------------------------------------------------------------------


def _make_state() -> BrainState:
    profile = make_profile_with_cogito({COGITO_ID: 1, "alpha": Fraction(3, 4)})
    msi = make_msi(
        profile,
        contents={COGITO_ID, "alpha"},
        threshold=Fraction(1, 2),
    )
    ptcns = make_ptcns(
        msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "alpha": ConsistencyEval.PRESERVE,
        },
    )
    registry = ContentRegistry(texts=MappingProxyType({"alpha": "alpha text"}))
    return BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)


class _PreserveClient:
    """Deterministic local LLM stand-in (mirrors bottom_up_tick fixture)."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        return "PRESERVE"


def _codes_for(line: str) -> list[int]:
    """Return the raw key codes for typing *line* into the composer.

    Each printable character maps to its ASCII code; the caller is
    responsible for appending the ENTER code separately so SUBMIT can be
    asserted on its own keystroke.
    """
    return [ord(ch) for ch in line]


_KEY_ENTER: int = 10


# ---------------------------------------------------------------------------
# I-UI-21 — curses wrapper delegates to composer / parser / router.
# ---------------------------------------------------------------------------


@register("I-UI-21", status="STRUCTURAL")
def check_I_UI_21_wrapper_delegates_to_composer_parser_router() -> None:
    # ---- The agent keystroke router is a finite pure-data table. -------
    router = build_agent_keystroke_router()
    assert isinstance(router, dict)
    assert router, "I-UI-21: agent keystroke router is empty"
    for code, route in router.items():
        assert isinstance(code, int), (
            f"I-UI-21: router key {code!r} must be int"
        )
        assert isinstance(route, AgentKeyRoute), (
            f"I-UI-21: router value {route!r} must be AgentKeyRoute"
        )
    # Every ASCII printable maps to CHAR; the closed control-character
    # set maps to its specific AgentKeyKind.
    for ascii_code in range(32, 127):
        route = router[ascii_code]
        assert route.kind is AgentKeyKind.CHAR, (
            f"I-UI-21: ASCII {ascii_code} should be a CHAR route "
            f"(got {route.kind!r})"
        )
        assert route.char == chr(ascii_code)
    for ctrl_code in (3, 21):  # ^C / ^U
        assert router[ctrl_code].kind is AgentKeyKind.CLEAR_BUFFER
    for ctrl_code in (10, 13):  # LF / CR
        assert router[ctrl_code].kind is AgentKeyKind.SUBMIT
    assert router[16].kind is AgentKeyKind.HISTORY_PREV
    assert router[14].kind is AgentKeyKind.HISTORY_NEXT
    for bs_code in (8, 127):
        assert router[bs_code].kind is AgentKeyKind.BACKSPACE

    # ---- Reserved accelerator fires only on empty buffer + non-"/". ----
    empty = ComposerState.empty()
    # ``s`` on empty buffer -> ACCEL(INSPECT_STATE)
    route = route_agent_keystroke(ord("s"), empty, router=router)
    assert route.kind is AgentKeyKind.ACCEL
    assert route.accel is OperatorCommand.INSPECT_STATE
    # ``q`` on empty buffer -> ACCEL(QUIT)
    route = route_agent_keystroke(ord("q"), empty, router=router)
    assert route.kind is AgentKeyKind.ACCEL
    assert route.accel is OperatorCommand.QUIT
    # ``space`` on empty buffer -> ACCEL(STEP_TICK)
    route = route_agent_keystroke(ord(" "), empty, router=router)
    assert route.kind is AgentKeyKind.ACCEL
    assert route.accel is OperatorCommand.STEP_TICK
    # ``n`` on empty buffer -> OPEN_PROMPT (legacy curses prompt)
    route = route_agent_keystroke(ord("n"), empty, router=router)
    assert route.kind is AgentKeyKind.OPEN_PROMPT
    # ``/`` on empty buffer -> CHAR (typed-command prefix)
    route = route_agent_keystroke(ord("/"), empty, router=router)
    assert route.kind is AgentKeyKind.CHAR
    assert route.char == "/"
    # ``/`` followed by anything: once buffer non-empty, every printable
    # is CHAR even for letters that would otherwise accelerate.
    composer = BottomComposer()
    after_slash = composer.apply(empty, ComposerAction.INSERT_CHAR, char="/")
    assert isinstance(after_slash, ComposerState)
    route = route_agent_keystroke(ord("s"), after_slash, router=router)
    assert route.kind is AgentKeyKind.CHAR, (
        "I-UI-21: once composer has any input, every printable must be CHAR "
        f"(got {route.kind!r})"
    )

    # ---- Static import audit on brain/ui/tui.py: the wrapper still ----
    # imports no kernel / LLM / shell / network surface (defence in depth
    # against ruling drift). I-UI-11 already runs the same audit at
    # gate time; we re-check here so I-UI-21 fails specifically when the
    # wrapper grows a forbidden import.
    tui_path = Path(ui_tui.__file__).resolve()
    source = tui_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(tui_path))
    forbidden_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if alias.name.startswith("brain.tick") or alias.name == "brain.tlica" or alias.name.startswith("brain.tlica.") or alias.name == "brain.llm" or alias.name.startswith("brain.llm."):
                    forbidden_roots.add(alias.name)
                if root in {"subprocess", "socket", "urllib", "http", "requests"}:
                    forbidden_roots.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if (
                mod == "brain.tick"
                or mod.startswith("brain.tick.")
                or mod == "brain.tlica"
                or mod.startswith("brain.tlica.")
                or mod == "brain.llm"
                or mod.startswith("brain.llm.")
            ):
                # TYPE_CHECKING-only imports are allowed.
                if not _is_type_checking_line(tree, node.lineno):
                    forbidden_roots.add(mod)
            root = mod.split(".")[0] if mod else ""
            if root in {"subprocess", "socket", "urllib", "http", "requests"}:
                forbidden_roots.add(mod)
    assert not forbidden_roots, (
        f"I-UI-21 violated: brain/ui/tui.py imports forbidden modules "
        f"{sorted(forbidden_roots)!r}"
    )

    # ---- step_agent_loop forwards CHAR codes to BottomComposer. --------
    session = OperatorSession(state=_make_state())
    composer_state = ComposerState.empty()
    transcript = OperatorTranscript.empty()
    pre_state = session.state
    pre_queue_len = len(session.event_queue)
    pre_tick = session.tick_counter
    # Type "/queue beta hello-world" one character at a time.
    typed = "/queue beta hello-world"
    for ch in typed:
        result = step_agent_loop(
            session,
            composer_state,
            transcript,
            ord(ch),
        )
        assert isinstance(result, AgentStepResult)
        assert result.route_kind is AgentKeyKind.CHAR, (
            f"I-UI-21: CHAR routing drifted for {ch!r} "
            f"(got {result.route_kind!r})"
        )
        # No dispatch should happen during typing.
        assert not result.dispatched, (
            f"I-UI-21: CHAR dispatch leak on {ch!r}"
        )
        assert session.state is pre_state, (
            f"I-UI-21: typing {ch!r} mutated session.state"
        )
        assert len(session.event_queue) == pre_queue_len, (
            f"I-UI-21: typing {ch!r} mutated session.event_queue"
        )
        composer_state = result.composer_state
        transcript = result.transcript
    assert composer_state.buffer == typed, (
        f"I-UI-21: composer buffer drifted after typing "
        f"({composer_state.buffer!r} vs {typed!r})"
    )
    # No transcript entries during typing.
    assert len(transcript) == 0, (
        f"I-UI-21: transcript grew during pure-typing "
        f"(len={len(transcript)})"
    )

    # ---- SUBMIT path: composer -> parser -> session.dispatch. ----------
    client = _PreserveClient()
    submit_result = step_agent_loop(
        session,
        composer_state,
        transcript,
        _KEY_ENTER,
        client=client,
    )
    assert submit_result.route_kind is AgentKeyKind.SUBMIT
    assert submit_result.submitted_line == typed
    assert isinstance(submit_result.parsed_command, Command)
    assert submit_result.parsed_command.kind is OperatorCommand.QUEUE_PERCEPT
    assert isinstance(submit_result.parsed_command.payload, QueuePerceptPayload)
    assert submit_result.parsed_command.payload.content_id == "beta"
    assert submit_result.parsed_command.payload.text == "hello-world"
    assert submit_result.dispatched
    assert submit_result.dispatched_kind is OperatorCommand.QUEUE_PERCEPT
    # The wrapper appended SUBMIT then QUEUED to the transcript.
    assert submit_result.transcript_appends == [
        TranscriptKind.SUBMIT,
        TranscriptKind.QUEUED,
    ], (
        "I-UI-21: SUBMIT path did not append SUBMIT then QUEUED "
        f"(got {submit_result.transcript_appends!r})"
    )
    composer_state = submit_result.composer_state
    transcript = submit_result.transcript
    # Buffer cleared after submit; history grew by one.
    assert composer_state.buffer == ""
    assert composer_state.history == (typed,)
    # Session reflects the QUEUE_PERCEPT dispatch: event queue has one
    # payload, active view is "queue".
    assert len(session.event_queue) == pre_queue_len + 1
    head = session.event_queue.peek()
    assert isinstance(head, QueuePerceptPayload)
    assert head.content_id == "beta"
    assert session.active_view == "queue"

    # ---- /step path: typed command -> parser -> STEP_TICK -> tick. -----
    for ch in "/step":
        result = step_agent_loop(
            session, composer_state, transcript, ord(ch), client=client
        )
        composer_state = result.composer_state
        transcript = result.transcript
    step_result = step_agent_loop(
        session, composer_state, transcript, _KEY_ENTER, client=client
    )
    assert step_result.route_kind is AgentKeyKind.SUBMIT
    assert step_result.dispatched
    assert step_result.dispatched_kind is OperatorCommand.STEP_TICK
    assert step_result.transcript_appends == [
        TranscriptKind.SUBMIT,
        TranscriptKind.STEP,
    ], (
        "I-UI-21: /step did not append SUBMIT then STEP "
        f"(got {step_result.transcript_appends!r})"
    )
    composer_state = step_result.composer_state
    transcript = step_result.transcript
    # Tick advanced; the LLM client recorded at least one call.
    assert session.tick_counter == pre_tick + 1, (
        "I-UI-21: STEP_TICK did not advance the session tick counter"
    )
    assert isinstance(session.latest_tick, TickRecord)
    assert client.calls, "I-UI-21: STEP_TICK did not call the LLM client"
    # The wrapper consumed the queued payload via the public dispatch
    # path (we do not appendq directly to event_queue).
    assert len(session.event_queue) == pre_queue_len, (
        "I-UI-21: STEP_TICK did not drain the queue through dispatch"
    )

    # ---- /state, /help paths: pure VIEW dispatches. --------------------
    for line in ("/state", "/help"):
        for ch in line:
            result = step_agent_loop(
                session, composer_state, transcript, ord(ch), client=client
            )
            composer_state = result.composer_state
            transcript = result.transcript
        submit = step_agent_loop(
            session, composer_state, transcript, _KEY_ENTER, client=client
        )
        assert submit.dispatched
        assert submit.transcript_appends == [
            TranscriptKind.SUBMIT,
            TranscriptKind.VIEW,
        ], (
            f"I-UI-21: {line!r} did not append SUBMIT then VIEW "
            f"(got {submit.transcript_appends!r})"
        )
        composer_state = submit.composer_state
        transcript = submit.transcript

    # ---- Invalid input becomes a LocalCommandError, no kernel mutation.
    pre_state2 = session.state
    pre_tick2 = session.tick_counter
    bad = "/nope"
    for ch in bad:
        result = step_agent_loop(
            session, composer_state, transcript, ord(ch), client=client
        )
        composer_state = result.composer_state
        transcript = result.transcript
    bad_submit = step_agent_loop(
        session, composer_state, transcript, _KEY_ENTER, client=client
    )
    assert bad_submit.parse_error is not None, (
        "I-UI-21: invalid command did not surface a parse_error"
    )
    assert "unknown command" in bad_submit.parse_error
    assert not bad_submit.dispatched, (
        "I-UI-21: invalid command must not dispatch"
    )
    assert bad_submit.transcript_appends == [
        TranscriptKind.SUBMIT,
        TranscriptKind.ERROR,
    ], (
        f"I-UI-21: invalid command did not append SUBMIT then ERROR "
        f"(got {bad_submit.transcript_appends!r})"
    )
    assert session.state is pre_state2, (
        "I-UI-21: parse error mutated kernel state"
    )
    assert session.tick_counter == pre_tick2, (
        "I-UI-21: parse error advanced the tick counter"
    )

    # ---- Backspace deletes a typed character without dispatch. ---------
    composer_state = bad_submit.composer_state
    transcript = bad_submit.transcript
    bs_state = step_agent_loop(
        session, composer_state, transcript, ord("a"), client=client
    ).composer_state
    assert bs_state.buffer == "a"
    bs_state2 = step_agent_loop(
        session, bs_state, transcript, 127, client=client
    ).composer_state
    assert bs_state2.buffer == "", (
        f"I-UI-21: backspace did not clear single-char buffer "
        f"(got {bs_state2.buffer!r})"
    )

    # ---- ^U clears the composer buffer (without /clear semantics). ----
    typed_state = step_agent_loop(
        session, ComposerState.empty(), transcript, ord("a"), client=client
    ).composer_state
    typed_state = step_agent_loop(
        session, typed_state, transcript, ord("b"), client=client
    ).composer_state
    assert typed_state.buffer == "ab"
    cleared = step_agent_loop(
        session, typed_state, transcript, 21, client=client
    ).composer_state
    assert cleared.buffer == "", (
        f"I-UI-21: ^U did not clear the buffer (got {cleared.buffer!r})"
    )

    # ---- build_agent_view_for_session is a pure projection. -----------
    view_session = OperatorSession(state=_make_state())
    view_composer = ComposerState.empty()
    view_transcript = OperatorTranscript.empty()
    view = build_agent_view_for_session(
        view_session, view_composer, view_transcript, width=80, height=24
    )
    assert view.active_view == "state"
    assert view.layout.width == 80
    assert view.layout.height == 24
    # Building the view did not mutate anything.
    assert view_session.state is view_session.state  # tautology / sanity
    assert view_session.tick_counter == 0
    assert view_session.status_message == ""

    # ---- AGENT_HELP_HINT is bounded printable. -------------------------
    assert isinstance(AGENT_HELP_HINT, str) and AGENT_HELP_HINT.isprintable()
    assert "help" in AGENT_HELP_HINT


def _is_type_checking_line(tree: ast.Module, line: int) -> bool:
    """Return ``True`` when *line* falls inside an ``if TYPE_CHECKING:`` block."""
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            is_tc = (
                (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING")
                or (
                    isinstance(test, ast.Attribute)
                    and test.attr == "TYPE_CHECKING"
                )
            )
            if is_tc:
                for child in ast.walk(node):
                    if getattr(child, "lineno", None) == line:
                        return True
    return False


# ---------------------------------------------------------------------------
# I-UI-23 — scripted agent-style operator walk is inspectable (OBSERVED).
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class _AgentWalkSummary:
    """Inspection summary recorded by the OBSERVED agent walk."""

    keystrokes: int = 0
    char_routes: int = 0
    submit_routes: int = 0
    submitted_lines: list[str] = field(default_factory=list)
    parsed_commands: list[str] = field(default_factory=list)
    dispatched_kinds: list[str] = field(default_factory=list)
    transcript_kinds: list[str] = field(default_factory=list)
    view_transitions: list[tuple[str, str]] = field(default_factory=list)
    final_status: str = ""
    final_error: str = ""
    tick_counter_final: int = 0
    state_identity_drift: bool = False


@register("I-UI-23", status="OBSERVED")
def check_I_UI_23_scripted_agent_walk_is_inspectable() -> None:
    session = OperatorSession(state=_make_state())
    composer_state = ComposerState.empty()
    transcript = OperatorTranscript.empty()
    client = _PreserveClient()
    summary = _AgentWalkSummary()
    pre_state_id = id(session.state)
    prior_view = session.active_view

    # Scripted operator walk per kickoff section 15. Each entry is one
    # raw curses key code: typed characters are ASCII; SUBMIT is _KEY_ENTER.
    typed_lines = (
        "/queue beta hello-world",
        "/step",
        "/state",
        "/tick",
        "/help",
        "/quit",
    )
    script_codes: list[int] = []
    for line in typed_lines:
        script_codes.extend(_codes_for(line))
        script_codes.append(_KEY_ENTER)

    for code in script_codes:
        result = step_agent_loop(
            session,
            composer_state,
            transcript,
            code,
            client=client,
        )
        summary.keystrokes += 1
        if result.route_kind is AgentKeyKind.CHAR:
            summary.char_routes += 1
        elif result.route_kind is AgentKeyKind.SUBMIT:
            summary.submit_routes += 1
            if result.submitted_line is not None:
                summary.submitted_lines.append(result.submitted_line)
            if result.parsed_command is not None:
                summary.parsed_commands.append(result.parsed_command.kind.value)
            if result.dispatched and result.dispatched_kind is not None:
                summary.dispatched_kinds.append(result.dispatched_kind.value)
            for tag in result.transcript_appends:
                summary.transcript_kinds.append(tag.value)
            if session.active_view != prior_view:
                summary.view_transitions.append((prior_view, session.active_view))
                prior_view = session.active_view
        composer_state = result.composer_state
        transcript = result.transcript

    summary.final_status = session.status_message
    summary.final_error = session.error_message
    summary.tick_counter_final = session.tick_counter
    summary.state_identity_drift = id(session.state) != pre_state_id

    # OBSERVED rows do not gate the runner, but we still assert the walk
    # produced a coherent summary so the row stays diagnostic.
    assert summary.submit_routes == len(typed_lines), (
        f"I-UI-23: expected {len(typed_lines)} SUBMIT routes "
        f"(got {summary.submit_routes})"
    )
    assert summary.submitted_lines == list(typed_lines), (
        f"I-UI-23: submitted lines drifted ({summary.submitted_lines!r})"
    )
    assert summary.parsed_commands == [
        OperatorCommand.QUEUE_PERCEPT.value,
        OperatorCommand.STEP_TICK.value,
        OperatorCommand.INSPECT_STATE.value,
        OperatorCommand.INSPECT_TICK.value,
        OperatorCommand.HELP.value,
        OperatorCommand.QUIT.value,
    ], (
        f"I-UI-23: parsed command sequence drifted "
        f"({summary.parsed_commands!r})"
    )
    assert summary.dispatched_kinds == summary.parsed_commands, (
        "I-UI-23: every parsed command should have dispatched "
        f"(parsed={summary.parsed_commands!r}, "
        f"dispatched={summary.dispatched_kinds!r})"
    )
    # Each SUBMIT appends SUBMIT then either QUEUED / STEP / VIEW / QUIT.
    expected_transcript_kinds = [
        "SUBMIT", "QUEUED",
        "SUBMIT", "STEP",
        "SUBMIT", "VIEW",
        "SUBMIT", "VIEW",
        "SUBMIT", "VIEW",
        "SUBMIT", "QUIT",
    ]
    assert summary.transcript_kinds == expected_transcript_kinds, (
        f"I-UI-23: transcript-kind sequence drifted "
        f"({summary.transcript_kinds!r})"
    )
    # The /step run advanced tick_counter to 1 exactly (one PerceptEvent
    # was queued, then dispatched through tick).
    assert summary.tick_counter_final == 1, (
        f"I-UI-23: tick_counter drifted ({summary.tick_counter_final!r})"
    )
    # /step replaced the kernel BrainState identity.
    assert summary.state_identity_drift, (
        "I-UI-23: STEP_TICK did not replace the kernel BrainState identity"
    )
    # The walk ended on /quit, which flipped the session's quit flag.
    assert session.quit_flag, (
        "I-UI-23: scripted walk did not reach QUIT (quit_flag=False)"
    )
    # The transcript ring is bounded; the walk produced exactly 12
    # appends (two per SUBMIT). The transcript ring carried all of them
    # because the bound is 64.
    assert len(transcript) == len(expected_transcript_kinds), (
        f"I-UI-23: transcript length drifted (got {len(transcript)})"
    )


__all__ = [
    "check_I_UI_21_wrapper_delegates_to_composer_parser_router",
    "check_I_UI_23_scripted_agent_walk_is_inspectable",
]
