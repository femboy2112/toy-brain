"""Fixtures for I-GROW-01, I-GROW-02, I-GROW-03, I-GROW-07.

* I-GROW-01 — :class:`GrowthEventType` is a finite closed enumeration
  containing the v1 emit-shapes plus the deferred members reserved for
  future compatibility.
* I-GROW-02 — :class:`GrowthEventSource` is a finite closed enumeration
  containing the v1 dispatcher labels plus the deferred sources.
* I-GROW-03 — :class:`GrowthEvent` constructor enforces bounded
  printable identifiers, ``COGITO_ID`` rejection, closed-enum
  membership, non-negative int ``tick`` (and not ``bool``), tuple
  references, pairwise-unique references, bounded provenance, and no
  silent normalization.
* I-GROW-07 — direct :class:`GrowthLedger` construction with two
  events sharing the same ``event_id`` rejects rather than silently
  normalizing.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass

from brain.development.growth_ledger import (
    GROWTH_LEDGER_ID_MAX,
    GROWTH_LEDGER_PROVENANCE_MAX,
    GROWTH_LEDGER_REFERENCE_MAX,
    GrowthEvent,
    GrowthEventSource,
    GrowthEventType,
    GrowthLedger,
    derive_growth_event_id,
)
from brain.invariants import register
from brain.tlica.profile import COGITO_ID


_V1_EVENT_TYPE_VALUES: frozenset[str] = frozenset({
    "stream_chunk_accepted",
    "pattern_entry_created",
    "pattern_entry_updated",
    "stream_promotion_queued",
    "tick_succeeded",
    "profile_domain_added",
    "msi_member_added",
})

_DEFERRED_EVENT_TYPE_VALUES: frozenset[str] = frozenset({
    "session_saved",
    "session_loaded",
    "coherence_report_built",
})

_V1_EVENT_SOURCE_VALUES: frozenset[str] = frozenset({
    "stream_append",
    "pattern_ledger_observe",
    "stream_promote",
    "step_dispatch",
})

_DEFERRED_EVENT_SOURCE_VALUES: frozenset[str] = frozenset({
    "persistence_save",
    "persistence_load",
    "coherence_monitor",
})


def _valid_event_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        event_id="growth:abc1234567890def",
        event_type=GrowthEventType.STREAM_CHUNK_ACCEPTED,
        tick=1,
        source=GrowthEventSource.STREAM_APPEND,
        references=("strm-chunk-1",),
        provenance="stream_append:_dispatch_stream_append",
    )
    base.update(overrides)
    return base


def _assert_rejects(call, tag: str) -> None:
    try:
        call()
    except (TypeError, ValueError) as exc:
        assert tag in str(exc), (
            f"{tag} negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            f"{tag} violated: invalid GrowthEvent was accepted"
        )


@register("I-GROW-01", status="REQUIRED")
def check_growth_event_type_closed() -> None:
    members = {m.value for m in GrowthEventType}
    expected = _V1_EVENT_TYPE_VALUES | _DEFERRED_EVENT_TYPE_VALUES
    assert members == expected, (
        f"I-GROW-01 violated: GrowthEventType membership drifted "
        f"(got {members!r}, expected {expected!r})"
    )

    # v1-emitted set membership.
    for value in _V1_EVENT_TYPE_VALUES:
        assert GrowthEventType(value).value == value

    # Deferred members exist and round-trip.
    for value in _DEFERRED_EVENT_TYPE_VALUES:
        assert GrowthEventType(value).value == value

    # Unknown value construction rejects.
    try:
        GrowthEventType("not-an-event-type")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-GROW-01 violated: GrowthEventType accepted unknown value"
        )


@register("I-GROW-02", status="REQUIRED")
def check_growth_event_source_closed() -> None:
    members = {m.value for m in GrowthEventSource}
    expected = _V1_EVENT_SOURCE_VALUES | _DEFERRED_EVENT_SOURCE_VALUES
    assert members == expected, (
        f"I-GROW-02 violated: GrowthEventSource membership drifted "
        f"(got {members!r}, expected {expected!r})"
    )

    for value in _V1_EVENT_SOURCE_VALUES:
        assert GrowthEventSource(value).value == value
    for value in _DEFERRED_EVENT_SOURCE_VALUES:
        assert GrowthEventSource(value).value == value

    try:
        GrowthEventSource("not-a-source")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-GROW-02 violated: GrowthEventSource accepted unknown value"
        )


@register("I-GROW-03", status="REQUIRED")
def check_growth_event_constructor() -> None:
    # Valid construction over every v1 event type.
    for member in GrowthEventType:
        if member.value not in _V1_EVENT_TYPE_VALUES:
            continue
        event = GrowthEvent(**_valid_event_kwargs(event_type=member))
        assert event.event_type is member
        assert event.tick == 1
        assert event.source is GrowthEventSource.STREAM_APPEND
        assert event.references == ("strm-chunk-1",)
        assert event.provenance == "stream_append:_dispatch_stream_append"
        assert event.event_id == "growth:abc1234567890def"

    # Frozen / slotted.
    base = GrowthEvent(**_valid_event_kwargs())
    assert is_dataclass(base)
    assert getattr(type(base), "__dataclass_params__").frozen
    try:
        base.event_id = "mutated"  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "I-GROW-03 violated: GrowthEvent is not frozen"
        )

    # COGITO_ID rejection on every id-bearing field.
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(event_id=COGITO_ID)),
        tag="I-GROW-03",
    )
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(references=(COGITO_ID,))),
        tag="I-GROW-03",
    )
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(provenance=COGITO_ID)),
        tag="I-GROW-03",
    )

    # Malformed event_id (empty / non-printable / over-length / non-str).
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(event_id="")),
        tag="I-GROW-03",
    )
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(event_id="bad\x00id")),
        tag="I-GROW-03",
    )
    _assert_rejects(
        lambda: GrowthEvent(
            **_valid_event_kwargs(event_id="x" * (GROWTH_LEDGER_ID_MAX + 1))
        ),
        tag="I-GROW-03",
    )
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(event_id=12345)),
        tag="I-GROW-03",
    )

    # Closed enum membership.
    _assert_rejects(
        lambda: GrowthEvent(
            **_valid_event_kwargs(event_type="stream_chunk_accepted")
        ),
        tag="I-GROW-03",
    )
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(source="stream_append")),
        tag="I-GROW-03",
    )

    # tick must be int and not bool, and must be non-negative.
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(tick=-1)),
        tag="I-GROW-03",
    )
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(tick=True)),
        tag="I-GROW-03",
    )
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(tick=1.5)),
        tag="I-GROW-03",
    )
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(tick="1")),
        tag="I-GROW-03",
    )

    # references must be a tuple of bounded printable strings.
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(references=["strm-chunk-1"])),
        tag="I-GROW-03",
    )
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(references=("",))),
        tag="I-GROW-03",
    )
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(references=("bad\x00ref",))),
        tag="I-GROW-03",
    )
    _assert_rejects(
        lambda: GrowthEvent(
            **_valid_event_kwargs(
                references=("x" * (GROWTH_LEDGER_ID_MAX + 1),)
            )
        ),
        tag="I-GROW-03",
    )
    # References tuple cap.
    _assert_rejects(
        lambda: GrowthEvent(
            **_valid_event_kwargs(
                references=tuple(
                    f"r-{i}" for i in range(GROWTH_LEDGER_REFERENCE_MAX + 1)
                )
            )
        ),
        tag="I-GROW-03",
    )
    # Duplicate references entries rejected (LOCK G).
    _assert_rejects(
        lambda: GrowthEvent(
            **_valid_event_kwargs(references=("strm-chunk-1", "strm-chunk-1"))
        ),
        tag="I-GROW-03",
    )

    # provenance must be a bounded printable non-empty string.
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(provenance="")),
        tag="I-GROW-03",
    )
    _assert_rejects(
        lambda: GrowthEvent(**_valid_event_kwargs(provenance="bad\x00prov")),
        tag="I-GROW-03",
    )
    _assert_rejects(
        lambda: GrowthEvent(
            **_valid_event_kwargs(
                provenance="x" * (GROWTH_LEDGER_PROVENANCE_MAX + 1)
            )
        ),
        tag="I-GROW-03",
    )

    # Valid construction with empty references tuple is accepted.
    empty_refs = GrowthEvent(**_valid_event_kwargs(references=()))
    assert empty_refs.references == ()

    # Multiple distinct references accepted.
    multi = GrowthEvent(
        **_valid_event_kwargs(references=("a-1", "a-2", "a-3"))
    )
    assert multi.references == ("a-1", "a-2", "a-3")

    # No silent normalization: strings with surrounding whitespace are
    # kept as-is (still printable, still accepted exactly).
    spaced_id = derive_growth_event_id(
        event_type=GrowthEventType.STREAM_CHUNK_ACCEPTED,
        tick=0,
        source=GrowthEventSource.STREAM_APPEND,
        references=("strm-chunk-1",),
        provenance="x ",
    )
    spaced = GrowthEvent(
        event_id=spaced_id,
        event_type=GrowthEventType.STREAM_CHUNK_ACCEPTED,
        tick=0,
        source=GrowthEventSource.STREAM_APPEND,
        references=("strm-chunk-1",),
        provenance="x ",
    )
    assert spaced.provenance == "x "

    # GrowthEvent must not expose any score / claim / label field.
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
        "rank",
        "ranking",
        "total",
    )
    for name in forbidden_attrs:
        assert not hasattr(base, name), (
            f"I-GROW-03 violated: GrowthEvent exposes forbidden field "
            f"{name!r}"
        )


@register("I-GROW-07", status="REQUIRED")
def check_growth_ledger_rejects_duplicate_event_id() -> None:
    """Direct GrowthLedger construction with duplicate event_id rejects."""
    valid = GrowthEvent(**_valid_event_kwargs())

    # Same instance twice -> duplicate event_id.
    _assert_rejects(
        lambda: GrowthLedger(events=(valid, valid)),
        tag="I-GROW-07",
    )

    # Two distinct events sharing event_id.
    twin = GrowthEvent(**_valid_event_kwargs())
    assert twin.event_id == valid.event_id
    _assert_rejects(
        lambda: GrowthLedger(events=(valid, twin)),
        tag="I-GROW-07",
    )

    # Two events with different event_ids are accepted side by side.
    other = GrowthEvent(
        **_valid_event_kwargs(
            event_id="growth:0000000000000001",
            references=("strm-chunk-2",),
        )
    )
    ok = GrowthLedger(events=(valid, other))
    assert ok.events == (valid, other)
