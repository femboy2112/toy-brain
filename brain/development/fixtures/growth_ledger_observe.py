"""Fixtures for I-GROW-05, I-GROW-06, I-GROW-08, I-GROW-09.

* I-GROW-05 — :class:`GrowthLedger` is frozen / slotted /
  copy-on-write; :meth:`observe` returns a new ledger unless the
  duplicate idempotency rule or the cap refusal rule returns
  ``self`` unchanged.
* I-GROW-06 — :meth:`observe` is idempotent on duplicate event
  payloads: a second observe with the same payload returns ``self``
  unchanged (object identity).
* I-GROW-08 — at ``len(events) >= GROWTH_LEDGER_MAX_EVENTS``,
  :meth:`observe` of any new event returns ``self`` unchanged. No
  eviction, no FIFO / LIFO drop, no overwrite, no random replacement.
* I-GROW-09 — :meth:`counts_by_type` is deterministic over the closed
  :class:`GrowthEventType` enum and exposes no aggregate scalar
  score; ``GrowthEvent`` / ``GrowthLedger`` carry no scalar score
  field.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass

from brain.development.growth_ledger import (
    GROWTH_LEDGER_MAX_EVENTS,
    GrowthEvent,
    GrowthEventSource,
    GrowthEventType,
    GrowthLedger,
)
from brain.invariants import register


def _observe_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        event_type=GrowthEventType.STREAM_CHUNK_ACCEPTED,
        tick=1,
        source=GrowthEventSource.STREAM_APPEND,
        references=("strm-chunk-1",),
        provenance="stream_append:_dispatch_stream_append",
    )
    base.update(overrides)
    return base


@register("I-GROW-05", status="REQUIRED")
def check_growth_ledger_frozen_slotted_cow() -> None:
    led = GrowthLedger()
    assert is_dataclass(led)
    assert getattr(type(led), "__dataclass_params__").frozen
    assert hasattr(type(led), "__slots__")
    assert "events" in type(led).__slots__

    # events tuple by default.
    assert isinstance(led.events, tuple)
    assert led.events == ()

    # Frozen: cannot reassign events.
    try:
        led.events = (None,)  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "I-GROW-05 violated: GrowthLedger.events is not frozen"
        )

    # observe returns a NEW GrowthLedger; old events tuple unchanged.
    new_led = led.observe(**_observe_kwargs())
    assert isinstance(new_led, GrowthLedger)
    assert new_led is not led
    assert led.events == (), (
        "I-GROW-05 violated: original ledger events mutated by observe"
    )
    assert len(new_led.events) == 1
    assert isinstance(new_led.events[0], GrowthEvent)

    # GrowthEvent records carry no aggregate scalar / score field.
    forbidden_attrs = (
        "score",
        "growth_score",
        "growth_total",
        "growth_index",
        "growth_rate",
        "iness_score",
        "i_score",
        "capability_score",
        "maturity_score",
        "intelligence_score",
        "quality_score",
    )
    for name in forbidden_attrs:
        assert not hasattr(new_led, name), (
            f"I-GROW-05 violated: GrowthLedger exposes forbidden field {name!r}"
        )
        assert not hasattr(new_led.events[0], name), (
            f"I-GROW-05 violated: GrowthEvent exposes forbidden field {name!r}"
        )


@register("I-GROW-06", status="REQUIRED")
def check_growth_ledger_observe_idempotent() -> None:
    led = GrowthLedger()
    first = led.observe(**_observe_kwargs())
    assert len(first.events) == 1

    # Same payload again -> returns the same ledger object (id-equal).
    second = first.observe(**_observe_kwargs())
    assert second is first, (
        "I-GROW-06 violated: duplicate observe did not return self "
        "(object identity)"
    )
    assert len(second.events) == 1
    # No exception was raised on the duplicate observe.

    # Same event_id observed from a different ledger instance still
    # idempotent (event_id collapse is identity-driven by the closed
    # payload, not by ledger identity).
    twin = GrowthLedger(events=first.events)
    twin_again = twin.observe(**_observe_kwargs())
    assert twin_again is twin

    # A different payload (different tick) is not a duplicate.
    other = first.observe(**_observe_kwargs(tick=2))
    assert other is not first
    assert len(other.events) == 2
    assert {e.event_id for e in other.events} == {
        first.events[0].event_id,
        other.events[1].event_id,
    }
    assert first.events[0].event_id != other.events[1].event_id


@register("I-GROW-08", status="REQUIRED")
def check_growth_ledger_hard_refusal_at_cap() -> None:
    # Build a ledger exactly at the cap using distinct payloads (one
    # per tick value 0..MAX-1) so every event_id is unique.
    led = GrowthLedger()
    for i in range(GROWTH_LEDGER_MAX_EVENTS):
        led = led.observe(**_observe_kwargs(tick=i))
    assert len(led.events) == GROWTH_LEDGER_MAX_EVENTS
    saturated = led

    # New event at cap -> returns self unchanged.
    refused = saturated.observe(**_observe_kwargs(tick=GROWTH_LEDGER_MAX_EVENTS))
    assert refused is saturated, (
        "I-GROW-08 violated: observe at cap did not return self"
    )
    assert len(saturated.events) == GROWTH_LEDGER_MAX_EVENTS

    # Even an "obviously different" event must still be refused.
    refused2 = saturated.observe(
        **_observe_kwargs(
            event_type=GrowthEventType.TICK_SUCCEEDED,
            source=GrowthEventSource.STEP_DISPATCH,
            references=(f"tick-{GROWTH_LEDGER_MAX_EVENTS + 1}",),
            provenance="step_dispatch:_dispatch_step",
            tick=GROWTH_LEDGER_MAX_EVENTS + 1,
        )
    )
    assert refused2 is saturated
    assert len(saturated.events) == GROWTH_LEDGER_MAX_EVENTS

    # No eviction: the original first event is still present.
    assert saturated.events[0].tick == 0
    assert saturated.events[-1].tick == GROWTH_LEDGER_MAX_EVENTS - 1


@register("I-GROW-09", status="REQUIRED")
def check_growth_ledger_counts_by_type_deterministic() -> None:
    led = GrowthLedger()
    counts0 = led.counts_by_type()
    # One pair per closed enum member, in declaration order.
    expected_order = [m.value for m in GrowthEventType]
    actual_order = [pair[0] for pair in counts0]
    assert actual_order == expected_order, (
        f"I-GROW-09 violated: counts_by_type order drifted "
        f"(got {actual_order!r}, expected {expected_order!r})"
    )
    # All counts zero on an empty ledger.
    for label, count in counts0:
        assert count == 0, (
            f"I-GROW-09 violated: empty ledger has non-zero count for {label!r}"
        )

    # After one observe, exactly one count is 1 and the rest are 0.
    led = led.observe(**_observe_kwargs())
    counts1 = led.counts_by_type()
    by_label = {label: count for label, count in counts1}
    assert by_label["stream_chunk_accepted"] == 1
    for label, count in counts1:
        if label == "stream_chunk_accepted":
            continue
        assert count == 0, (
            f"I-GROW-09 violated: unexpected non-zero count for {label!r}"
        )

    # Two different event types -> two non-zero counts.
    led = led.observe(
        **_observe_kwargs(
            event_type=GrowthEventType.TICK_SUCCEEDED,
            source=GrowthEventSource.STEP_DISPATCH,
            references=("tick-1",),
            provenance="step_dispatch:_dispatch_step",
        )
    )
    counts2 = led.counts_by_type()
    by_label2 = {label: count for label, count in counts2}
    assert by_label2["stream_chunk_accepted"] == 1
    assert by_label2["tick_succeeded"] == 1
    # Deferred members exist with count 0.
    for deferred in ("session_saved", "session_loaded", "coherence_report_built"):
        assert by_label2[deferred] == 0

    # counts_by_type is deterministic across repeated calls.
    counts2_again = led.counts_by_type()
    assert counts2 == counts2_again

    # counts_by_type returns tuples, not lists, dicts, or scalars.
    assert isinstance(counts2, tuple)
    for pair in counts2:
        assert isinstance(pair, tuple)
        assert len(pair) == 2
        label, count = pair
        assert isinstance(label, str)
        assert isinstance(count, int) and not isinstance(count, bool)

    # No aggregate-scalar attribute appears anywhere on the surface.
    forbidden_attrs = (
        "score",
        "growth_score",
        "growth_total",
        "growth_index",
        "growth_rate",
        "iness_score",
        "i_score",
        "capability_score",
        "maturity_score",
        "intelligence_score",
        "quality_score",
        "summary_scalar",
        "summary_score",
    )
    for name in forbidden_attrs:
        assert not hasattr(led, name), (
            f"I-GROW-09 violated: GrowthLedger exposes forbidden field {name!r}"
        )
        for evt in led.events:
            assert not hasattr(evt, name), (
                f"I-GROW-09 violated: GrowthEvent exposes forbidden field "
                f"{name!r}"
            )
