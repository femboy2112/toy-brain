"""Operator TUI bottom-up tick fixtures.

Drives:

* ``I-UI-05`` (REQUIRED) — ``STEP_TICK`` route uses the public
  :func:`brain.tick.tick` path only. We queue a single operator percept,
  dispatch ``STEP_TICK`` with an injected deterministic LLM stand-in,
  and assert ``tick()`` was invoked exactly once with the queued event,
  that the returned :class:`TickRecord` is stored on the session, that
  the session's :class:`BrainState` is replaced with the returned new
  state, and that no other kernel mutation route is taken.
* ``I-UI-10`` (STRUCTURAL) — :class:`OperatorSession` holds no unsafe
  resources. We assert the session's declared attribute surface, that
  no attribute is callable / LLM-client-shaped / file-/socket-/process-
  like, and that the active LLM client is supplied as a method argument
  rather than stored on the session.
"""
from __future__ import annotations

from dataclasses import fields
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING

from brain.invariants import register
from brain.io_types import ContentRegistry, PerceptEvent, TickRecord
from brain.tick import BrainState
from brain.tlica.builders import (
    make_msi,
    make_profile_with_cogito,
    make_ptcns,
)
from brain.tlica.modes import ModeOp
from brain.tlica.profile import COGITO_ID
from brain.tlica.ptcns import ConsistencyEval
from brain.toce_core import ContentState
from brain.ui import session as session_module
from brain.ui.commands import (
    Command,
    OperatorCommand,
    QueuePerceptPayload,
    make_command,
)
from brain.ui.session import (
    DEFAULT_EVENT_QUEUE_LIMIT,
    OperatorEventQueue,
    OperatorSession,
    _ALLOWED_SESSION_ATTRS,
)

if TYPE_CHECKING:  # pragma: no cover
    pass


# ---------------------------------------------------------------------------
# Deterministic builders
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


def _make_payload(
    *,
    content_id: str = "beta",
    text: str = "beta probe",
    initial_rho: Fraction = Fraction(3, 4),
) -> QueuePerceptPayload:
    return QueuePerceptPayload(
        content_id=content_id,
        text=text,
        content_state=ContentState(True, True, True, True),
        initial_rho=initial_rho,
    )


class _PreserveClient:
    """Deterministic LLM stand-in: every call returns ``PRESERVE``.

    The brain's :class:`LLMBackedPtCns` retry shell parses this exact
    string into :data:`ConsistencyEval.PRESERVE`. The client records
    each ``eval_consistency`` call so the fixture can assert ``tick()``
    invoked it exactly once.
    """

    def __init__(self) -> None:
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        return "PRESERVE"


# ---------------------------------------------------------------------------
# I-UI-05 — STEP_TICK route uses the public tick() path only.
# ---------------------------------------------------------------------------


@register("I-UI-05", status="REQUIRED")
def check_I_UI_05_step_tick_uses_public_tick_path() -> None:
    state = _make_state()
    session = OperatorSession(state=state)
    assert session.tick_counter == 0
    assert session.latest_tick is None
    pre_state = session.state

    # 1. Queue one operator percept.
    queue_cmd = make_command(
        OperatorCommand.QUEUE_PERCEPT,
        content_id="beta",
        text="beta probe",
        content_state=ContentState(True, True, True, True),
        initial_rho=Fraction(3, 4),
    )
    session.dispatch(queue_cmd)
    assert len(session.event_queue) == 1, (
        "I-UI-05 violated: queue did not accept a valid payload"
    )

    # 2. Patch brain.ui.session.tick to a spy that delegates to the real
    #    tick(). This proves the router calls the public public ``tick()``
    #    entrypoint exactly once and with the operator-queued event.
    real_tick = session_module.tick
    invocations: list[tuple[BrainState, tuple[PerceptEvent, ...], object, int]] = []

    def _spy_tick(state_arg, events_arg, client_arg, tick_id=0):  # noqa: ANN001
        invocations.append((state_arg, tuple(events_arg), client_arg, tick_id))
        return real_tick(state_arg, events_arg, client_arg, tick_id=tick_id)

    session_module.tick = _spy_tick  # type: ignore[assignment]
    try:
        client = _PreserveClient()
        session.dispatch(make_command(OperatorCommand.STEP_TICK), client=client)
    finally:
        session_module.tick = real_tick  # type: ignore[assignment]

    # 3. tick() invoked exactly once with the operator-queued event.
    assert len(invocations) == 1, (
        "I-UI-05 violated: tick() invocation count "
        f"{len(invocations)} != 1"
    )
    state_arg, events_arg, client_arg, tick_id_arg = invocations[0]
    assert state_arg is pre_state, (
        "I-UI-05 violated: tick() received a different BrainState object "
        "than the session held before STEP_TICK"
    )
    assert client_arg is client, (
        "I-UI-05 violated: tick() received a different LLM client than the "
        "one passed to dispatch()"
    )
    assert len(events_arg) == 1, (
        "I-UI-05 violated: tick() received "
        f"{len(events_arg)} events; expected exactly 1"
    )
    event = events_arg[0]
    assert isinstance(event, PerceptEvent)
    assert event.content_id == "beta"
    assert event.text == "beta probe"
    assert event.initial_rho == Fraction(3, 4)
    assert isinstance(tick_id_arg, int) and tick_id_arg == 1, (
        "I-UI-05 violated: tick_id must be a positive int identifying the "
        f"step (got {tick_id_arg!r})"
    )

    # 4. The session stored the returned TickRecord.
    record = session.latest_tick
    assert isinstance(record, TickRecord), (
        "I-UI-05 violated: latest_tick is not a TickRecord"
    )
    assert record.tick_index == 1, (
        "I-UI-05 violated: stored TickRecord has tick_index "
        f"{record.tick_index!r}; expected 1"
    )

    # 5. The session's BrainState is the returned new state, and the
    #    pre-step state is no longer referenced.
    assert session.state is not pre_state, (
        "I-UI-05 violated: session.state was not replaced by the new state"
    )
    assert isinstance(session.state, BrainState)
    # "beta" must now be in the post-tick profile domain.
    assert "beta" in session.state.profile.domain, (
        "I-UI-05 violated: post-tick profile lacks the queued content_id"
    )
    # And the percept text is preserved in the registry (I-RT-10 path).
    assert session.state.registry.texts.get("beta") == "beta probe"

    # 6. The queue lost exactly one event.
    assert len(session.event_queue) == 0, (
        "I-UI-05 violated: STEP_TICK did not consume one queued event "
        f"(queue size = {len(session.event_queue)})"
    )

    # 7. Tick counter advanced by one and the active view changed to "tick".
    assert session.tick_counter == 1
    assert session.active_view == "tick"

    # 8. The injected LLM stand-in was called at least once during the
    #    tick (proving the public path actually ran).
    assert client.calls, (
        "I-UI-05 violated: tick() did not invoke client.eval_consistency"
    )

    # 9. A second STEP_TICK on an empty queue does NOT call tick() again.
    invocations.clear()
    session_module.tick = _spy_tick  # type: ignore[assignment]
    try:
        session.dispatch(make_command(OperatorCommand.STEP_TICK), client=client)
    finally:
        session_module.tick = real_tick  # type: ignore[assignment]
    assert invocations == [], (
        "I-UI-05 violated: STEP_TICK on empty queue invoked tick()"
    )
    # And the tick_counter stayed put.
    assert session.tick_counter == 1, (
        "I-UI-05 violated: tick_counter advanced on empty STEP_TICK"
    )

    # 10. The mode trace recorded the deterministic dispatch.
    assert record.triggered_mode in (
        ModeOp.MODE_C,
        ModeOp.MODE_A,
        ModeOp.NEUTRAL,
    )


# ---------------------------------------------------------------------------
# I-UI-10 — OperatorSession holds no unsafe resources.
# ---------------------------------------------------------------------------


_FORBIDDEN_ATTR_NAMES = frozenset({
    "client",
    "llm_client",
    "subprocess",
    "process",
    "fd",
    "socket",
    "shell_cmd",
    "host_callback",
    "callback",
})


@register("I-UI-10", status="STRUCTURAL")
def check_I_UI_10_session_holds_no_unsafe_resources() -> None:
    state = _make_state()
    session = OperatorSession(state=state)

    # 1. The declared slot list matches the campaign-approved set.
    declared = set(session.__slots__)
    assert declared == set(_ALLOWED_SESSION_ATTRS), (
        "I-UI-10 violated: OperatorSession slot list drifted "
        f"(declared={sorted(declared)!r}, "
        f"expected={sorted(_ALLOWED_SESSION_ATTRS)!r})"
    )

    # 2. Dataclass fields match the slot list exactly (no shadow fields).
    declared_fields = {f.name for f in fields(session)}
    assert declared_fields == set(_ALLOWED_SESSION_ATTRS), (
        "I-UI-10 violated: dataclass field set diverged from slot list "
        f"(fields={sorted(declared_fields)!r})"
    )

    # 3. None of the slot names matches a forbidden surface.
    for name in declared:
        assert name not in _FORBIDDEN_ATTR_NAMES, (
            f"I-UI-10 violated: OperatorSession declares forbidden slot {name!r}"
        )

    # 4. Each declared attribute is either an immutable kernel /
    #    developmental record, the bounded queue, a bounded primitive,
    #    or None — never a callable / file handle / socket / subprocess.
    for name in declared:
        value = getattr(session, name)
        assert not callable(value), (
            f"I-UI-10 violated: OperatorSession.{name} is callable"
        )
        assert not hasattr(value, "eval_consistency"), (
            f"I-UI-10 violated: OperatorSession.{name} looks like an LLM client"
        )
        if hasattr(value, "read") and hasattr(value, "write"):
            # BrainState exposes neither read nor write, so this should
            # only trip on a real resource handle.
            raise AssertionError(
                f"I-UI-10 violated: OperatorSession.{name} exposes read/write"
            )
        assert not hasattr(value, "fileno"), (
            f"I-UI-10 violated: OperatorSession.{name} exposes fileno()"
        )
        assert not hasattr(value, "send_signal"), (
            f"I-UI-10 violated: OperatorSession.{name} looks like a subprocess"
        )

    # 5. Adding an arbitrary attribute to a slotted dataclass is rejected,
    #    so a runtime caller cannot smuggle a forbidden resource onto the
    #    session record.
    for forbidden in ("llm_client", "subprocess", "socket"):
        try:
            setattr(session, forbidden, object())
        except AttributeError:
            pass
        else:
            raise AssertionError(
                "I-UI-10 violated: OperatorSession accepted a new attribute "
                f"{forbidden!r}"
            )

    # 6. The bounded event queue is the only mutation surface for
    #    operator-supplied data, and it stores only payload records.
    assert isinstance(session.event_queue, OperatorEventQueue)
    assert session.event_queue.limit == DEFAULT_EVENT_QUEUE_LIMIT
    session.event_queue.enqueue(_make_payload(content_id="probe-1"))
    snap = session.event_queue.snapshot()
    assert isinstance(snap, tuple) and len(snap) == 1
    assert isinstance(snap[0], QueuePerceptPayload)
    assert not callable(snap[0]) and not hasattr(snap[0], "eval_consistency")

    # 7. The active LLM client is supplied as a method argument, not a
    #    field on the session. A successful STEP_TICK with an injected
    #    client must not leave the client referenced anywhere on the
    #    session afterwards (drives the "no LLM client" clause).
    client = _PreserveClient()
    session.dispatch(make_command(OperatorCommand.STEP_TICK), client=client)
    for name in declared:
        value = getattr(session, name)
        assert value is not client, (
            f"I-UI-10 violated: OperatorSession.{name} captured the LLM client"
        )

    # 8. Session is constructed with no developmental histories by default;
    #    histories may be attached but their slot type tolerates None.
    fresh = OperatorSession(state=_make_state())
    assert fresh.output_history is None
    assert fresh.worldlet_history is None
    assert fresh.repl_history is None


# ---------------------------------------------------------------------------
# Anti-regression: the router cannot reach a non-public mutation path.
# ---------------------------------------------------------------------------


def _module_imports() -> frozenset[str]:
    """Return the set of top-level module names :mod:`brain.ui.session`
    references via its module-level globals.
    """
    import sys
    out: set[str] = set()
    mod = sys.modules.get("brain.ui.session")
    if mod is None:
        return frozenset()
    for value in vars(mod).values():
        m = getattr(value, "__module__", None)
        if isinstance(m, str):
            out.add(m.split(".")[0])
    return frozenset(out)
