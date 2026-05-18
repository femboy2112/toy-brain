"""Fixture for I-GROW-13..I-GROW-18: session integration.

* I-GROW-13 — ``OperatorSession.growth_ledger`` exists, defaults to an
  empty :class:`GrowthLedger`, is type-checked in ``__post_init__``,
  and is listed in ``_ALLOWED_SESSION_ATTRS``.
* I-GROW-14 — both persistence resource-audit fixtures declare a
  ``_PHASE_3_13_SESSION_ATTRS = frozenset({"growth_ledger"})`` tier
  that is folded into the ``allowed`` union compared against
  ``_ALLOWED_SESSION_ATTRS``.
* I-GROW-15 — a successful ``/stream`` append emits
  ``STREAM_CHUNK_ACCEPTED`` and, when the Pattern Ledger delta
  produces a created-or-updated entry, also emits
  ``PATTERN_ENTRY_CREATED`` or ``PATTERN_ENTRY_UPDATED``. Failures,
  parse errors, and read-only paths do not emit.
* I-GROW-16 — a successful ``/stream-promote`` emits
  ``STREAM_PROMOTION_QUEUED``. Failures do not emit.
* I-GROW-17 — a successful ``/step`` emits ``TICK_SUCCEEDED`` and
  derives ``PROFILE_DOMAIN_ADDED`` / ``MSI_MEMBER_ADDED`` from
  pre/post bounded set deltas; tick failures emit nothing.
* I-GROW-18 — deferred event types (``SESSION_SAVED``,
  ``SESSION_LOADED``, ``COHERENCE_REPORT_BUILT``) are not emitted by
  any v1 path. ``/save-session``, ``/load-session``, and
  :func:`build_full_coherence_report` leave the Growth Ledger free
  of events of those types.
"""
from __future__ import annotations

from brain.development.coherence_monitor import (
    build_full_coherence_report,
)
from brain.development.growth_ledger import (
    GROWTH_LEDGER_MAX_EVENTS,
    GrowthEventSource,
    GrowthEventType,
    GrowthLedger,
)
from brain.invariants import register
from brain.tlica.profile import COGITO_ID
from brain.ui.command_line import LocalCommandLine
from brain.ui.commands import (
    OperatorCommand,
    StreamAppendPayload,
    make_command,
)
from brain.ui.fixtures._stream_helpers import make_session
from brain.ui.session import OperatorSession, _ALLOWED_SESSION_ATTRS


_DEFERRED_EVENT_TYPE_VALUES: frozenset[str] = frozenset({
    GrowthEventType.SESSION_SAVED.value,
    GrowthEventType.SESSION_LOADED.value,
    GrowthEventType.COHERENCE_REPORT_BUILT.value,
})


def _offline_client():
    from brain.ui.__main__ import OfflineStandInClient  # noqa: PLC0415
    return OfflineStandInClient()


def _emitted_types(ledger: GrowthLedger) -> tuple[str, ...]:
    return tuple(evt.event_type.value for evt in ledger.events)


@register("I-GROW-13", status="REQUIRED")
def check_growth_ledger_session_field() -> None:
    session = make_session()

    # Default field shape.
    assert isinstance(session.growth_ledger, GrowthLedger), (
        "I-GROW-13 violated: session.growth_ledger is not a GrowthLedger"
    )
    assert session.growth_ledger.events == (), (
        "I-GROW-13 violated: fresh session has non-empty growth_ledger"
    )

    # _ALLOWED_SESSION_ATTRS contains "growth_ledger".
    assert "growth_ledger" in _ALLOWED_SESSION_ATTRS, (
        "I-GROW-13 violated: growth_ledger missing from "
        "_ALLOWED_SESSION_ATTRS"
    )

    # __post_init__ rejects a non-GrowthLedger value.
    try:
        OperatorSession(
            state=session.state,
            growth_ledger="not-a-ledger",  # type: ignore[arg-type]
        )
    except TypeError as exc:
        assert "growth_ledger" in str(exc)
    else:
        raise AssertionError(
            "I-GROW-13 violated: __post_init__ accepted non-GrowthLedger"
        )

    # Explicit empty ledger continues to work.
    explicit = OperatorSession(
        state=session.state, growth_ledger=GrowthLedger()
    )
    assert isinstance(explicit.growth_ledger, GrowthLedger)
    assert explicit.growth_ledger.events == ()


@register("I-GROW-14", status="REQUIRED")
def check_growth_ledger_audit_tier() -> None:
    # The Phase 3.13 audit tier is declared in both persistence
    # resource-audit fixtures and folded into the allowed union.
    from brain.ui.fixtures.persistence_observe_resource_audit import (  # noqa: PLC0415
        _PHASE_3_9_SESSION_ATTRS as _OBSERVE_PHASE_3_9,
        _PHASE_3_10C_SESSION_ATTRS as _OBSERVE_PHASE_3_10C,
        _PHASE_3_12C_SESSION_ATTRS as _OBSERVE_PHASE_3_12C,
        _PHASE_3_13_SESSION_ATTRS as _OBSERVE_PHASE_3_13,
    )
    from brain.ui.fixtures.persistence_ops_resource_audit import (  # noqa: PLC0415
        _PHASE_3_9_SESSION_ATTRS as _OPS_PHASE_3_9,
        _PHASE_3_10C_SESSION_ATTRS as _OPS_PHASE_3_10C,
        _PHASE_3_12C_SESSION_ATTRS as _OPS_PHASE_3_12C,
        _PHASE_3_13_SESSION_ATTRS as _OPS_PHASE_3_13,
    )

    assert _OBSERVE_PHASE_3_13 == frozenset({"growth_ledger"}), (
        "I-GROW-14 violated: persistence_observe_resource_audit's "
        "_PHASE_3_13_SESSION_ATTRS drifted "
        f"(got {sorted(_OBSERVE_PHASE_3_13)!r})"
    )
    assert _OPS_PHASE_3_13 == frozenset({"growth_ledger"}), (
        "I-GROW-14 violated: persistence_ops_resource_audit's "
        "_PHASE_3_13_SESSION_ATTRS drifted "
        f"(got {sorted(_OPS_PHASE_3_13)!r})"
    )

    # The folded union must equal _ALLOWED_SESSION_ATTRS exactly.
    observe_allowed = (
        _OBSERVE_PHASE_3_9
        | _OBSERVE_PHASE_3_10C
        | _OBSERVE_PHASE_3_12C
        | _OBSERVE_PHASE_3_13
    )
    ops_allowed = (
        _OPS_PHASE_3_9
        | _OPS_PHASE_3_10C
        | _OPS_PHASE_3_12C
        | _OPS_PHASE_3_13
    )
    assert observe_allowed == frozenset(_ALLOWED_SESSION_ATTRS), (
        "I-GROW-14 violated: persistence_observe allowed union does not "
        "match _ALLOWED_SESSION_ATTRS "
        f"(observe={sorted(observe_allowed)!r}, "
        f"allowed={sorted(_ALLOWED_SESSION_ATTRS)!r})"
    )
    assert ops_allowed == frozenset(_ALLOWED_SESSION_ATTRS), (
        "I-GROW-14 violated: persistence_ops allowed union does not "
        "match _ALLOWED_SESSION_ATTRS "
        f"(ops={sorted(ops_allowed)!r}, "
        f"allowed={sorted(_ALLOWED_SESSION_ATTRS)!r})"
    )


@register("I-GROW-15", status="REQUIRED")
def check_growth_ledger_stream_append_observes() -> None:
    session = make_session()
    initial_ledger = session.growth_ledger
    assert initial_ledger.events == ()

    # Successful /stream emits STREAM_CHUNK_ACCEPTED plus exactly one
    # PATTERN_ENTRY_CREATED (new pattern signature).
    session.dispatch(
        make_command(OperatorCommand.STREAM_APPEND, stream_text="alpha")
    )
    types = _emitted_types(session.growth_ledger)
    assert types == (
        GrowthEventType.STREAM_CHUNK_ACCEPTED.value,
        GrowthEventType.PATTERN_ENTRY_CREATED.value,
    ), (
        f"I-GROW-15 violated: emitted types after first /stream "
        f"{types!r}"
    )
    # COGITO_ID never appears in any reference.
    for evt in session.growth_ledger.events:
        for ref in evt.references:
            assert ref != COGITO_ID
        assert evt.event_id != COGITO_ID
        assert evt.provenance != COGITO_ID

    # A second identical /stream advances the existing Pattern Ledger
    # entry's recurrence_count -> emits PATTERN_ENTRY_UPDATED.
    session.dispatch(
        make_command(OperatorCommand.STREAM_APPEND, stream_text="alpha")
    )
    types = _emitted_types(session.growth_ledger)
    assert types[-2:] == (
        GrowthEventType.STREAM_CHUNK_ACCEPTED.value,
        GrowthEventType.PATTERN_ENTRY_UPDATED.value,
    ), (
        f"I-GROW-15 violated: second /stream emit shape {types[-2:]!r}"
    )

    # Read-only commands do not emit.
    ledger_after = session.growth_ledger
    for kind in (
        OperatorCommand.INSPECT_STATE,
        OperatorCommand.INSPECT_TICK,
        OperatorCommand.INSPECT_STREAM_SUMMARY,
        OperatorCommand.INSPECT_STREAM_CANDIDATES,
        OperatorCommand.SESSION_STATUS,
        OperatorCommand.HELP,
    ):
        session.dispatch(make_command(kind))
        assert session.growth_ledger is ledger_after, (
            "I-GROW-15 violated: read-only command "
            f"{kind.value!r} mutated the Growth Ledger"
        )

    # Parse failure does not emit.
    err = LocalCommandLine().parse("/not-a-real-verb")
    assert err.__class__.__name__ == "LocalCommandError"
    assert session.growth_ledger is ledger_after

    # Dispatch failure (malformed payload) does not emit.
    try:
        StreamAppendPayload(text="")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-GROW-15 expectation: StreamAppendPayload should reject "
            "empty text"
        )
    assert session.growth_ledger is ledger_after


@register("I-GROW-16", status="REQUIRED")
def check_growth_ledger_stream_promote_observes() -> None:
    session = make_session()
    session.dispatch(
        make_command(OperatorCommand.STREAM_APPEND, stream_text="alpha")
    )
    ledger_after_append = session.growth_ledger

    # Successful /stream-promote emits STREAM_PROMOTION_QUEUED.
    session.dispatch(
        make_command(
            OperatorCommand.STREAM_PROMOTE,
            candidate_id="promo-strm-chunk-1",
        )
    )
    types = _emitted_types(session.growth_ledger)
    assert types[-1] == GrowthEventType.STREAM_PROMOTION_QUEUED.value, (
        f"I-GROW-16 violated: last emitted type {types[-1]!r}"
    )
    last_event = session.growth_ledger.events[-1]
    assert last_event.references == ("promo-strm-chunk-1",)
    assert last_event.source is GrowthEventSource.STREAM_PROMOTE
    assert last_event.provenance == "stream_promote:_dispatch_stream_promote"

    # Failed /stream-promote (unknown candidate) does not emit.
    ledger_after_promote = session.growth_ledger
    session.dispatch(
        make_command(
            OperatorCommand.STREAM_PROMOTE,
            candidate_id="no-such-candidate",
        )
    )
    assert session.growth_ledger is ledger_after_promote, (
        "I-GROW-16 violated: failed /stream-promote mutated the Growth Ledger"
    )
    # initial ledger after the append is still a prefix.
    assert (
        session.growth_ledger.events[: len(ledger_after_append.events)]
        == ledger_after_append.events
    )


@register("I-GROW-17", status="REQUIRED")
def check_growth_ledger_step_observes() -> None:
    session = make_session()
    # Queue and promote one stream candidate so /step has a payload.
    session.dispatch(
        make_command(OperatorCommand.STREAM_APPEND, stream_text="beta")
    )
    session.dispatch(
        make_command(
            OperatorCommand.STREAM_PROMOTE,
            candidate_id="promo-strm-chunk-1",
        )
    )
    pre_state = session.state
    pre_profile_domain = frozenset(pre_state.profile.domain)
    pre_msi_contents = frozenset(pre_state.msi.contents)
    ledger_before_step = session.growth_ledger

    # Successful /step emits TICK_SUCCEEDED plus zero-or-more
    # PROFILE_DOMAIN_ADDED / MSI_MEMBER_ADDED events.
    session.dispatch(
        make_command(OperatorCommand.STEP_TICK), client=_offline_client()
    )

    new_events = session.growth_ledger.events[len(ledger_before_step.events):]
    new_types = tuple(evt.event_type.value for evt in new_events)
    assert new_types, (
        "I-GROW-17 violated: /step emitted no Growth Ledger events"
    )
    assert new_types[0] == GrowthEventType.TICK_SUCCEEDED.value, (
        f"I-GROW-17 violated: first /step emit is {new_types[0]!r}"
    )
    tick_event = new_events[0]
    assert tick_event.source is GrowthEventSource.STEP_DISPATCH
    assert tick_event.provenance == "step_dispatch:_dispatch_step"
    assert tick_event.references == (
        f"tick-{session.latest_tick.tick_index}",
    )

    # Profile / MSI deltas exactly match pre/post bounded set deltas.
    post_profile_added = sorted(
        session.state.profile.domain - pre_profile_domain
    )
    post_msi_added = sorted(
        session.state.msi.contents - pre_msi_contents
    )
    profile_events = [
        evt for evt in new_events
        if evt.event_type is GrowthEventType.PROFILE_DOMAIN_ADDED
    ]
    msi_events = [
        evt for evt in new_events
        if evt.event_type is GrowthEventType.MSI_MEMBER_ADDED
    ]
    assert [evt.references[0] for evt in profile_events] == post_profile_added, (
        f"I-GROW-17 violated: PROFILE_DOMAIN_ADDED references "
        f"{[evt.references[0] for evt in profile_events]!r} differ from "
        f"post/pre delta {post_profile_added!r}"
    )
    assert [evt.references[0] for evt in msi_events] == post_msi_added, (
        f"I-GROW-17 violated: MSI_MEMBER_ADDED references "
        f"{[evt.references[0] for evt in msi_events]!r} differ from "
        f"post/pre delta {post_msi_added!r}"
    )

    # Failed /step (empty queue) does not emit.
    ledger_after_step = session.growth_ledger
    session.dispatch(
        make_command(OperatorCommand.STEP_TICK), client=_offline_client()
    )
    assert session.growth_ledger is ledger_after_step, (
        "I-GROW-17 violated: failed /step mutated the Growth Ledger"
    )


@register("I-GROW-18", status="REQUIRED")
def check_growth_ledger_deferred_paths_emit_nothing() -> None:
    """Deferred event types are not emitted in v1.

    /save-session / /load-session / coherence-report build paths must
    not produce SESSION_SAVED / SESSION_LOADED / COHERENCE_REPORT_BUILT
    events on the v1 ledger.
    """
    session = make_session()
    session.dispatch(
        make_command(OperatorCommand.STREAM_APPEND, stream_text="gamma")
    )
    baseline_ledger = session.growth_ledger

    # /save-session without a session_store_config fails locally and
    # leaves the Growth Ledger identity-stable.
    session.dispatch(make_command(OperatorCommand.SAVE_SESSION))
    assert session.growth_ledger is baseline_ledger, (
        "I-GROW-18 violated: /save-session mutated the Growth Ledger"
    )
    # /load-session: same.
    session.dispatch(make_command(OperatorCommand.LOAD_SESSION))
    assert session.growth_ledger is baseline_ledger, (
        "I-GROW-18 violated: /load-session mutated the Growth Ledger"
    )

    # build_full_coherence_report runs over the session and produces a
    # bounded read-only diagnostic. It must not mutate the Growth
    # Ledger or emit deferred Growth Ledger events.
    report = build_full_coherence_report(session)
    assert report is not None
    assert session.growth_ledger is baseline_ledger, (
        "I-GROW-18 violated: build_full_coherence_report mutated the "
        "Growth Ledger"
    )

    # No event in the ledger has a deferred event_type.
    for evt in session.growth_ledger.events:
        assert evt.event_type.value not in _DEFERRED_EVENT_TYPE_VALUES, (
            "I-GROW-18 violated: deferred event_type "
            f"{evt.event_type.value!r} was emitted"
        )

    # The deferred enum members are still present on the closed enum
    # for future compatibility.
    for value in _DEFERRED_EVENT_TYPE_VALUES:
        assert GrowthEventType(value).value == value

    # Spam test: re-issuing the same /stream alpha 257 times does not
    # advance the ledger beyond GROWTH_LEDGER_MAX_EVENTS. Combines with
    # LOCK F / LOCK H to make the anti-Goodhart guarantee observable.
    spam_session = make_session()
    for _ in range(GROWTH_LEDGER_MAX_EVENTS + 1):
        spam_session.dispatch(
            make_command(OperatorCommand.STREAM_APPEND, stream_text="alpha")
        )
    assert len(spam_session.growth_ledger.events) <= GROWTH_LEDGER_MAX_EVENTS, (
        "I-GROW-18 violated: ledger exceeded GROWTH_LEDGER_MAX_EVENTS "
        f"({len(spam_session.growth_ledger.events)} > "
        f"{GROWTH_LEDGER_MAX_EVENTS})"
    )
