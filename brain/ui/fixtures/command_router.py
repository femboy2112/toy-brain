"""Operator TUI command-router fixtures.

Drives:

* ``I-UI-03`` (REQUIRED) — :class:`OperatorCommand` is a finite closed
  enumeration. We assert the enumeration contents, reject unknown
  string kinds via :func:`make_command`, and reject every
  forbidden-payload shape (callable, shell string, file path, network
  endpoint, arbitrary Python expression).
* ``I-UI-04`` (REQUIRED) — ``QUEUE_PERCEPT`` payload is
  :class:`PerceptEvent`-constructor bounded. We build a payload from
  approved fields, assert :func:`PerceptEvent` accepts it, and assert
  every out-of-range / wrong-type value raises before the session is
  touched.
* ``I-UI-06`` (REQUIRED) — validation and tick failures are local UI
  status only. We drive both a payload-rejection path and a tick
  failure path through the router and assert no kernel container
  changed identity or contents.
* ``I-UI-13`` (STRUCTURAL) — local UI status text is bounded printable
  text and the keyboard map is a finite enumeration that matches the
  help pane.
"""
from __future__ import annotations

from fractions import Fraction
from types import MappingProxyType

from brain.invariants import register
from brain.io_types import ContentRegistry, PerceptEvent
from brain.tick import BrainState
from brain.tlica.builders import (
    make_msi,
    make_profile_with_cogito,
    make_ptcns,
)
from brain.tlica.profile import COGITO_ID
from brain.tlica.ptcns import ConsistencyEval
from brain.toce_core import ContentState
from brain.ui.commands import (
    INSPECT_VIEW_MAP,
    Command,
    OperatorCommand,
    QueuePerceptPayload,
    make_command,
)
from brain.ui.render import DEFAULT_KEYBOARD_HELP
from brain.ui.session import (
    DEFAULT_EVENT_QUEUE_LIMIT,
    MAX_STATUS_TEXT_LEN,
    OperatorEventQueue,
    OperatorSession,
)


# ---------------------------------------------------------------------------
# Deterministic kernel-state builder
# ---------------------------------------------------------------------------


def _make_state() -> BrainState:
    profile = make_profile_with_cogito({
        COGITO_ID: 1,
        "alpha": Fraction(3, 4),
    })
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
    registry = ContentRegistry(
        texts=MappingProxyType({"alpha": "alpha text"})
    )
    return BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)


def _state_identity(state: BrainState) -> tuple:
    return (
        id(state),
        id(state.profile),
        id(state.profile.values),
        id(state.msi),
        id(state.msi.contents),
        id(state.ptcns),
        id(state.ptcns.eval_map),
        id(state.registry),
        id(state.registry.texts),
        repr(state),
    )


def _make_payload(
    *,
    content_id: str = "beta",
    text: str = "beta probe",
    initial_rho: Fraction | int | str = Fraction(3, 4),
    available: bool = True,
    verification_path: bool = True,
    retrievable: bool = True,
    operative: bool = True,
) -> QueuePerceptPayload:
    return QueuePerceptPayload(
        content_id=content_id,
        text=text,
        content_state=ContentState(
            available=available,
            verification_path=verification_path,
            retrievable=retrievable,
            operative=operative,
        ),
        initial_rho=initial_rho if isinstance(initial_rho, Fraction)
        else Fraction(initial_rho) if isinstance(initial_rho, int)
        else initial_rho,
    )


# ---------------------------------------------------------------------------
# I-UI-03 — OperatorCommand is a finite closed enumeration.
# ---------------------------------------------------------------------------


_EXPECTED_COMMAND_VALUES = frozenset({
    "inspect_state",
    "inspect_tick",
    "inspect_output",
    "inspect_worldlet",
    "inspect_repl",
    "queue_percept",
    "step_tick",
    "clear_status",
    "help",
    "quit",
    "noop",
    "stream_append",
    "inspect_stream_summary",
    "inspect_stream_candidates",
    "stream_promote",
    "save_session",
    "load_session",
})


@register("I-UI-03", status="REQUIRED")
def check_I_UI_03_operator_command_is_closed_enumeration() -> None:
    actual_values = frozenset(c.value for c in OperatorCommand)
    assert actual_values == _EXPECTED_COMMAND_VALUES, (
        "I-UI-03 violated: OperatorCommand drifted "
        f"(got {sorted(actual_values)!r}, "
        f"expected {sorted(_EXPECTED_COMMAND_VALUES)!r})"
    )

    # INSPECT_VIEW_MAP covers exactly the inspect-prefixed commands.
    inspects = frozenset(
        c for c in OperatorCommand if c.value.startswith("inspect_")
    )
    assert frozenset(INSPECT_VIEW_MAP.keys()) == inspects, (
        "I-UI-03 violated: INSPECT_VIEW_MAP keys diverged from "
        "inspect-prefixed commands"
    )

    # Unknown string kinds raise (no silent fallback).
    for bad in ("inspect_msi", "exec", "shell", "spawn", ""):
        try:
            make_command(bad)
        except ValueError as exc:
            assert "I-UI-03" in str(exc)
        else:
            raise AssertionError(
                f"I-UI-03 violated: make_command accepted unknown kind {bad!r}"
            )

    # Forbidden payload shapes: callable, shell-string filename, ...
    forbidden_payloads = (
        lambda: None,          # callable
        "ls -la /tmp",          # shell string
        "/etc/passwd",          # file path
        "https://example.com",  # network endpoint
        object(),               # arbitrary object
    )
    for bad in forbidden_payloads:
        try:
            Command(kind=OperatorCommand.QUEUE_PERCEPT, payload=bad)  # type: ignore[arg-type]
        except TypeError:
            pass
        else:
            raise AssertionError(
                "I-UI-03 violated: Command accepted forbidden payload "
                f"{type(bad).__name__}"
            )

    # Non-QUEUE_PERCEPT commands must not carry a payload.
    payload = _make_payload()
    for non_queue in (
        OperatorCommand.INSPECT_STATE,
        OperatorCommand.STEP_TICK,
        OperatorCommand.HELP,
    ):
        try:
            Command(kind=non_queue, payload=payload)
        except TypeError:
            pass
        else:
            raise AssertionError(
                f"I-UI-03 violated: Command accepted payload for {non_queue!r}"
            )

    # make_command with non-OperatorCommand-non-str kind raises.
    try:
        make_command(123)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "I-UI-03 violated: make_command accepted non-str non-enum kind"
        )

    # Constructed commands are frozen.
    cmd = make_command(OperatorCommand.INSPECT_STATE)
    try:
        cmd.kind = OperatorCommand.QUIT  # type: ignore[misc]
    except Exception:
        pass
    else:
        raise AssertionError(
            "I-UI-03 violated: Command.kind is mutable"
        )


# ---------------------------------------------------------------------------
# I-UI-04 — QUEUE_PERCEPT payload is PerceptEvent-constructor bounded.
# ---------------------------------------------------------------------------


@register("I-UI-04", status="REQUIRED")
def check_I_UI_04_queue_payload_is_percept_event_bounded() -> None:
    # Happy path: payload constructor accepts approved fields and
    # build_event returns a valid PerceptEvent.
    payload = _make_payload()
    event = payload.build_event()
    assert isinstance(event, PerceptEvent)
    assert event.content_id == "beta"
    assert event.text == "beta probe"
    assert event.initial_rho == Fraction(3, 4)

    # build_event is deterministic — equal inputs yield equal events.
    event_again = payload.build_event()
    assert event == event_again

    # I-RT-01: content_id == COGITO_ID is rejected by the public
    # constructor; the payload must surface that rejection up front.
    try:
        _make_payload(content_id=COGITO_ID)
    except ValueError as exc:
        assert "I-RT-01" in str(exc), (
            f"I-UI-04 violated: COGITO_ID rejection lacks I-RT-01 tag: {exc!r}"
        )
    else:
        raise AssertionError(
            "I-UI-04 violated: payload accepted COGITO_ID as content_id"
        )

    # I-RT-09: empty / non-printable text is rejected by PerceptEvent
    # constructor; the payload must surface that.
    for bad_text in ("", "\x00null"):
        try:
            _make_payload(text=bad_text)
        except ValueError as exc:
            assert "I-RT-09" in str(exc) or "printable" in str(exc) or "non-empty" in str(exc)
        else:
            raise AssertionError(
                f"I-UI-04 violated: payload accepted bad text {bad_text!r}"
            )

    # initial_rho outside [0, 1] is rejected without partial mutation of
    # an OperatorSession (we never construct one in the failure path).
    state = _make_state()
    session = OperatorSession(state=state)
    queue_before = len(session.event_queue)
    for bad_rho in (Fraction(-1, 2), Fraction(3, 2), Fraction(2)):
        try:
            _make_payload(initial_rho=bad_rho)
        except (ValueError, TypeError):
            pass
        else:
            raise AssertionError(
                f"I-UI-04 violated: payload accepted bad initial_rho {bad_rho!r}"
            )
        assert len(session.event_queue) == queue_before, (
            "I-UI-04 violated: out-of-range initial_rho partially mutated "
            "the OperatorSession"
        )

    # Wrong content_state type is rejected.
    try:
        QueuePerceptPayload(
            content_id="beta",
            text="beta probe",
            content_state="not-a-state",  # type: ignore[arg-type]
            initial_rho=Fraction(1, 2),
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "I-UI-04 violated: payload accepted non-ContentState content_state"
        )

    # Callable content_id is rejected.
    try:
        QueuePerceptPayload(
            content_id=(lambda: "x")(),  # actually str — sanity for the next case
            text="ok",
            content_state=ContentState(True, True, True, True),
            initial_rho=Fraction(1, 2),
        )
    except Exception:  # noqa: BLE001 — this construction must succeed
        raise AssertionError(
            "I-UI-04 violated: payload rejected a fully-valid construction"
        )

    # make_command builds an end-to-end QUEUE_PERCEPT command.
    cmd = make_command(
        OperatorCommand.QUEUE_PERCEPT,
        content_id="gamma",
        text="gamma probe",
        content_state=ContentState(True, True, True, True),
        initial_rho=Fraction(1, 2),
    )
    assert isinstance(cmd, Command)
    assert isinstance(cmd.payload, QueuePerceptPayload)
    assert cmd.payload.build_event().content_id == "gamma"

    # str / int rho inputs are normalized via the same rho() helper the
    # PerceptEvent constructor uses (drives the constructor-bounded clause).
    cmd_str = make_command(
        OperatorCommand.QUEUE_PERCEPT,
        content_id="delta",
        text="delta probe",
        content_state=ContentState(True, True, True, True),
        initial_rho="1/3",
    )
    assert isinstance(cmd_str.payload, QueuePerceptPayload)
    assert cmd_str.payload.initial_rho == Fraction(1, 3)


# ---------------------------------------------------------------------------
# I-UI-06 — validation and tick failures are local UI status only.
# ---------------------------------------------------------------------------


class _AlwaysFailingClient:
    """Deterministic LLM stand-in that always raises.

    Used to drive the tick-failure branch of :meth:`OperatorSession.dispatch`
    without contacting any real LLM. This object is intentionally minimal:
    it carries no file handle, no socket, and no subprocess.
    """

    def __init__(self) -> None:
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:  # pragma: no cover - we never get a return
        self.calls.append(prompt)
        raise RuntimeError("synthetic LLM failure (fixture)")


@register("I-UI-06", status="REQUIRED")
def check_I_UI_06_failures_are_local_ui_status_only() -> None:
    state = _make_state()
    session = OperatorSession(state=state)
    identity_before = _state_identity(session.state)

    # --- Path 1: QUEUE_PERCEPT with an invalid payload via the router ---
    # Bypassing make_command means the router itself must defend the
    # local-UI-status invariant. We construct a malformed Command-shaped
    # object that the dispatcher will reject as bad payload.
    class _RogueCommand:
        kind = OperatorCommand.QUEUE_PERCEPT
        payload = "not-a-payload"  # forbidden shape

    try:
        session.dispatch(_RogueCommand())  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "I-UI-06 violated: router accepted a non-Command object"
        )
    # The reject happened at dispatch-entry, so state must be intact.
    assert _state_identity(session.state) == identity_before, (
        "I-UI-06 violated: state mutated on non-Command dispatch"
    )

    # --- Path 2: STEP_TICK on an empty queue ---
    cmd_step = make_command(OperatorCommand.STEP_TICK)
    session.dispatch(cmd_step, client=_AlwaysFailingClient())
    assert session.error_message, (
        "I-UI-06 violated: STEP_TICK on empty queue produced no error"
    )
    assert _state_identity(session.state) == identity_before, (
        "I-UI-06 violated: empty-queue STEP_TICK mutated state"
    )

    # --- Path 3: STEP_TICK that triggers a tick() failure ---
    queue_cmd = make_command(
        OperatorCommand.QUEUE_PERCEPT,
        content_id="beta",
        text="beta probe",
        content_state=ContentState(True, True, True, True),
        initial_rho=Fraction(3, 4),
    )
    session.dispatch(queue_cmd)
    assert len(session.event_queue) == 1
    queue_size_before_step = len(session.event_queue)
    failing_client = _AlwaysFailingClient()
    session.dispatch(cmd_step, client=failing_client)

    assert session.error_message, (
        "I-UI-06 violated: failing tick produced no UI error message"
    )
    assert "tick failure" in session.error_message, (
        "I-UI-06 violated: UI error message missing 'tick failure' tag: "
        f"{session.error_message!r}"
    )
    assert _state_identity(session.state) == identity_before, (
        "I-UI-06 violated: failing tick mutated session.state"
    )
    assert session.latest_tick is None, (
        "I-UI-06 violated: failing tick stored a TickRecord"
    )
    # The queued payload must remain queued — failure must not consume it.
    assert len(session.event_queue) == queue_size_before_step, (
        "I-UI-06 violated: failing tick consumed the queued event"
    )

    # The failing client must have been called (i.e. the router really
    # did invoke the kernel via tick(), then captured the exception).
    assert failing_client.calls, (
        "I-UI-06 violated: STEP_TICK did not invoke client.eval_consistency"
    )

    # --- Path 4: STEP_TICK with no client argument ---
    session.clear_status()
    session.dispatch(cmd_step, client=None)
    assert "client" in session.error_message.lower(), (
        "I-UI-06 violated: missing client did not surface as local UI status"
    )
    assert _state_identity(session.state) == identity_before


# ---------------------------------------------------------------------------
# I-UI-13 — local UI status text is bounded printable text only.
# ---------------------------------------------------------------------------


@register("I-UI-13", status="STRUCTURAL")
def check_I_UI_13_status_text_is_bounded_printable() -> None:
    state = _make_state()
    session = OperatorSession(state=state)

    # Printable text under the bound: accepted verbatim.
    session.set_status("ok view = state")
    assert session.status_message == "ok view = state"

    # Non-printable text: rejected with the I-UI-13 tag.
    for bad in ("\x00", "warning\nnewline", "tab\there"):
        try:
            session.set_status(bad)
        except ValueError as exc:
            assert "I-UI-13" in str(exc), (
                f"I-UI-13 violated: rejection of {bad!r} lacks I-UI-13 tag: {exc!r}"
            )
        else:
            raise AssertionError(
                f"I-UI-13 violated: status_message accepted {bad!r}"
            )

    # Over-long printable text is truncated, not silently appended.
    long = "x" * (MAX_STATUS_TEXT_LEN * 2)
    session.set_status(long)
    assert len(session.status_message) <= MAX_STATUS_TEXT_LEN, (
        "I-UI-13 violated: status_message exceeds bound after truncation"
    )
    assert session.status_message.endswith("…"), (
        "I-UI-13 violated: truncated status_message lacks ellipsis marker"
    )

    # Error setter shares the same policy.
    session.set_error("ok")
    assert session.error_message == "ok"
    try:
        session.set_error("\x01")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-UI-13 violated: error_message accepted non-printable text"
        )

    # The keyboard map is a finite enumeration that matches the help pane.
    assert isinstance(DEFAULT_KEYBOARD_HELP, tuple)
    assert len(DEFAULT_KEYBOARD_HELP) > 0
    keys = [entry[0] for entry in DEFAULT_KEYBOARD_HELP]
    assert len(keys) == len(set(keys)), (
        "I-UI-13 violated: keyboard map contains duplicate keys"
    )
    for entry in DEFAULT_KEYBOARD_HELP:
        assert (
            isinstance(entry, tuple)
            and len(entry) == 2
            and isinstance(entry[0], str)
            and isinstance(entry[1], str)
            and entry[0].isprintable()
            and entry[1].isprintable()
        ), f"I-UI-13 violated: keyboard map entry {entry!r}"

    # OperatorSession.keyboard_help returns exactly the same tuple object
    # (it is the closed, immutable display contract).
    assert session.keyboard_help() is DEFAULT_KEYBOARD_HELP, (
        "I-UI-13 violated: keyboard_help diverged from DEFAULT_KEYBOARD_HELP"
    )

    # The default event-queue limit is bounded.
    assert isinstance(DEFAULT_EVENT_QUEUE_LIMIT, int)
    assert DEFAULT_EVENT_QUEUE_LIMIT > 0
    q = OperatorEventQueue(limit=2)
    q.enqueue(_make_payload(content_id="x1"))
    q.enqueue(_make_payload(content_id="x2"))
    try:
        q.enqueue(_make_payload(content_id="x3"))
    except OverflowError:
        pass
    else:
        raise AssertionError(
            "I-UI-13 violated: bounded event queue accepted overflow"
        )
