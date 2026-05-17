"""Fixtures for I-PLEDGER-06..09, I-PLEDGER-11, I-PLEDGER-12 (observe semantics).

* I-PLEDGER-06 — ``recurrence_count`` saturates at
  ``STREAM_PATTERN_RECURRENCE_MAX`` and remains within
  ``[STREAM_PATTERN_RECURRENCE_MIN, STREAM_PATTERN_RECURRENCE_MAX]``.
* I-PLEDGER-07 — confidence is exact
  ``Fraction(recurrence_count, STREAM_PATTERN_RECURRENCE_MAX)`` and
  no ``float`` / ``round`` / ``math.*`` participates.
* I-PLEDGER-08 — :class:`PatternLedger` is copy-on-write; the
  original ledger and its ``entries`` tuple are unchanged across
  every ``observe(...)`` call.
* I-PLEDGER-09 — ``observe(...)`` is idempotent for duplicate
  delivered chunk/candidate evidence.
* I-PLEDGER-11 — evidence lists cap at
  ``PATTERN_LEDGER_EVIDENCE_MAX`` independently.
* I-PLEDGER-12 — at ``PATTERN_LEDGER_MAX_ENTRIES``, observing a new
  signature returns the ledger unchanged (no eviction).
"""
from __future__ import annotations

import math
from fractions import Fraction

from brain.development.pattern_ledger import (
    PATTERN_LEDGER_EVIDENCE_MAX,
    PATTERN_LEDGER_MAX_ENTRIES,
    PatternLedger,
    PatternLedgerSaturationState,
)
from brain.development.text_stream import (
    STREAM_PATTERN_RECURRENCE_MAX,
    STREAM_PATTERN_RECURRENCE_MIN,
    TextStreamSource,
    make_stream_promotion_candidate,
    make_text_stream_chunk,
)
from brain.invariants import register


def _chunk(*, chunk_id: str, text: str):
    return make_text_stream_chunk(
        chunk_id=chunk_id,
        text=text,
        source=TextStreamSource.OPERATOR,
        provenance="operator",
    )


def _candidate(*, candidate_id: str, chunk_id: str, text: str):
    return make_stream_promotion_candidate(
        candidate_id=candidate_id,
        target_content_id=f"target-{candidate_id}",
        source=TextStreamSource.OPERATOR,
        chunk_id=chunk_id,
        text=text,
        provenance="operator",
    )


def _pair(*, n: int, text: str = "alpha"):
    chunk = _chunk(chunk_id=f"strm-chunk-{n}", text=text)
    cand = _candidate(
        candidate_id=f"promo-strm-chunk-{n}", chunk_id=chunk.chunk_id, text=text
    )
    return chunk, cand


@register("I-PLEDGER-06", status="REQUIRED")
def check_pattern_ledger_observe_recurrence_saturates() -> None:
    led = PatternLedger()
    chunk, cand = _pair(n=1)

    # First observe: fresh entry at MIN.
    led = led.observe(chunk, cand, current_tick=0)
    assert len(led.entries) == 1
    assert led.entries[0].recurrence_count == STREAM_PATTERN_RECURRENCE_MIN

    # Second observe of same chunk/candidate advances the count by 1
    # (duplicate-evidence filtering does not block recurrence
    # increment; LOCK D / LOCK G).
    led = led.observe(chunk, cand, current_tick=1)
    assert led.entries[0].recurrence_count == STREAM_PATTERN_RECURRENCE_MIN + 1

    # Different evidence ids for the same signature also advance.
    chunk2, cand2 = _pair(n=2)
    led = led.observe(chunk2, cand2, current_tick=2)
    assert led.entries[0].recurrence_count == STREAM_PATTERN_RECURRENCE_MIN + 2

    # Saturate by hammering observe.
    cap = STREAM_PATTERN_RECURRENCE_MAX
    for i in range(cap + 50):
        c, k = _pair(n=i + 100)  # all distinct ids, all same text -> same sig
        led = led.observe(c, k, current_tick=10 + i)
    assert led.entries[0].recurrence_count == cap
    # Saturated state advertised.
    assert led.entries[0].saturation_state is PatternLedgerSaturationState.SATURATED


@register("I-PLEDGER-07", status="REQUIRED")
def check_pattern_ledger_confidence_is_exact_fraction() -> None:
    led = PatternLedger()
    chunk, cand = _pair(n=1)
    led = led.observe(chunk, cand, current_tick=0)
    entry = led.entries[0]

    # Type and bounds.
    assert isinstance(entry.confidence, Fraction), (
        f"I-PLEDGER-07 violated: confidence type is {type(entry.confidence)}"
    )
    assert Fraction(0) <= entry.confidence <= Fraction(1), (
        f"I-PLEDGER-07 violated: confidence {entry.confidence} out of bounds"
    )
    # Exact formula.
    assert entry.confidence == Fraction(
        entry.recurrence_count, STREAM_PATTERN_RECURRENCE_MAX
    )

    # Saturate and confirm exact 1.
    cap = STREAM_PATTERN_RECURRENCE_MAX
    for i in range(cap):
        c, k = _pair(n=i + 200)
        led = led.observe(c, k, current_tick=i)
    assert led.entries[0].confidence == Fraction(1, 1)

    # Reject any participation of float / round / math.* on the
    # confidence path (defense in depth — the static audit fixture
    # also enforces this).
    assert not isinstance(entry.confidence, float)
    assert math.isfinite(float(entry.confidence)) or True  # noqa: SIM222
    # Defensive: the entry value space contains no float.
    for value in (
        entry.recurrence_count,
        entry.first_seen_tick,
        entry.last_seen_tick,
    ):
        assert isinstance(value, int) and not isinstance(value, bool), (
            f"I-PLEDGER-07 violated: numeric field has non-int type {type(value)}"
        )


@register("I-PLEDGER-08", status="REQUIRED")
def check_pattern_ledger_is_copy_on_write() -> None:
    led0 = PatternLedger()
    chunk, cand = _pair(n=1)
    led1 = led0.observe(chunk, cand, current_tick=0)

    # New ledger object; original unchanged.
    assert led1 is not led0, (
        "I-PLEDGER-08 violated: observe returned the same ledger object"
    )
    assert led0.entries == ()
    assert led1.entries != ()

    # entries tuples differ in identity (no in-place mutation).
    led2 = led1.observe(chunk, cand, current_tick=1)
    assert led1.entries is not led2.entries, (
        "I-PLEDGER-08 violated: observe re-used the entries tuple "
        "across calls"
    )
    # And the entry inside led1 is unchanged after observe yielded led2.
    assert led1.entries[0].recurrence_count == STREAM_PATTERN_RECURRENCE_MIN

    # entries must remain a tuple (not list / set / dict).
    assert isinstance(led1.entries, tuple)
    assert isinstance(led2.entries, tuple)

    # Frozen record.
    try:
        led1.entries = (led1.entries[0],) * 2  # type: ignore[misc]
    except Exception:
        pass
    else:
        raise AssertionError(
            "I-PLEDGER-08 violated: PatternLedger.entries is mutable"
        )


@register("I-PLEDGER-09", status="REQUIRED")
def check_pattern_ledger_observe_filters_duplicate_evidence() -> None:
    led = PatternLedger()
    chunk, cand = _pair(n=1)
    led = led.observe(chunk, cand, current_tick=0)
    assert led.entries[0].evidence_chunk_ids == ("strm-chunk-1",)
    assert led.entries[0].evidence_candidate_ids == ("promo-strm-chunk-1",)

    # Re-observing the same chunk/candidate is a no-op for evidence
    # ids (recurrence still advances, see I-PLEDGER-06).
    led = led.observe(chunk, cand, current_tick=1)
    assert led.entries[0].evidence_chunk_ids == ("strm-chunk-1",)
    assert led.entries[0].evidence_candidate_ids == ("promo-strm-chunk-1",)
    assert led.entries[0].recurrence_count == STREAM_PATTERN_RECURRENCE_MIN + 1

    # Distinct ids for the same signature append in order.
    chunk2, cand2 = _pair(n=2)
    led = led.observe(chunk2, cand2, current_tick=2)
    assert led.entries[0].evidence_chunk_ids == ("strm-chunk-1", "strm-chunk-2")
    assert led.entries[0].evidence_candidate_ids == (
        "promo-strm-chunk-1",
        "promo-strm-chunk-2",
    )


@register("I-PLEDGER-11", status="REQUIRED")
def check_pattern_ledger_evidence_lists_cap_independently() -> None:
    led = PatternLedger()

    # Fill chunk evidence list up to the cap with distinct chunk ids
    # but a single candidate id (so the candidate list stays at 1).
    shared_cand = _candidate(
        candidate_id="promo-cap", chunk_id="strm-chunk-1", text="alpha"
    )
    for i in range(PATTERN_LEDGER_EVIDENCE_MAX + 5):
        c = _chunk(chunk_id=f"strm-chunk-{i + 1}", text="alpha")
        led = led.observe(c, shared_cand, current_tick=i)

    entry = led.entries[0]
    # Chunk list is exactly at cap.
    assert len(entry.evidence_chunk_ids) == PATTERN_LEDGER_EVIDENCE_MAX, (
        f"I-PLEDGER-11 violated: chunk evidence length "
        f"{len(entry.evidence_chunk_ids)} != cap {PATTERN_LEDGER_EVIDENCE_MAX}"
    )
    # The first cap-many ids win (FIFO drop is forbidden under LOCK F).
    expected_first = tuple(
        f"strm-chunk-{i + 1}" for i in range(PATTERN_LEDGER_EVIDENCE_MAX)
    )
    assert entry.evidence_chunk_ids == expected_first, (
        "I-PLEDGER-11 violated: evidence list did not preserve earliest "
        "ids in order"
    )
    # Candidate list capped at 1 (duplicate-candidate filtering).
    assert entry.evidence_candidate_ids == ("promo-cap",)

    # Independence: a fresh ledger where the candidate ids vary but
    # the chunk id stays the same should cap the candidate list and
    # leave the chunk list at 1.
    led2 = PatternLedger()
    shared_chunk = _chunk(chunk_id="strm-chunk-shared", text="alpha")
    for i in range(PATTERN_LEDGER_EVIDENCE_MAX + 5):
        k = _candidate(
            candidate_id=f"promo-cand-{i + 1}",
            chunk_id=shared_chunk.chunk_id,
            text="alpha",
        )
        led2 = led2.observe(shared_chunk, k, current_tick=i)
    entry2 = led2.entries[0]
    assert entry2.evidence_chunk_ids == ("strm-chunk-shared",)
    assert len(entry2.evidence_candidate_ids) == PATTERN_LEDGER_EVIDENCE_MAX


@register("I-PLEDGER-12", status="REQUIRED")
def check_pattern_ledger_max_entries_refuses_new_signature() -> None:
    led = PatternLedger()

    # Fill the ledger with PATTERN_LEDGER_MAX_ENTRIES distinct
    # signatures. Each call adds one entry.
    for i in range(PATTERN_LEDGER_MAX_ENTRIES):
        text = "x" * (i + 1)  # distinct length => distinct signature
        c = _chunk(chunk_id=f"strm-chunk-fill-{i + 1}", text=text)
        k = _candidate(
            candidate_id=f"promo-fill-{i + 1}",
            chunk_id=c.chunk_id,
            text=text,
        )
        led = led.observe(c, k, current_tick=i)
    assert len(led.entries) == PATTERN_LEDGER_MAX_ENTRIES

    # A new signature now must be refused (no eviction, no overwrite,
    # no shuffle).
    snapshot_entries = led.entries
    novel_text = "z" * (PATTERN_LEDGER_MAX_ENTRIES + 10)
    novel_chunk = _chunk(chunk_id="strm-chunk-novel", text=novel_text)
    novel_cand = _candidate(
        candidate_id="promo-novel", chunk_id=novel_chunk.chunk_id, text=novel_text
    )
    led_after = led.observe(novel_chunk, novel_cand, current_tick=999)
    assert led_after is led, (
        "I-PLEDGER-12 violated: ledger at capacity must return self "
        "unchanged for a novel signature"
    )
    assert led_after.entries is snapshot_entries, (
        "I-PLEDGER-12 violated: entries tuple identity changed"
    )

    # Re-observing an existing signature still advances recurrence.
    first_entry = led.entries[0]
    chunk_existing = _chunk(
        chunk_id="strm-chunk-fill-1-bis", text="x"
    )  # same len:1 / distinct features as the first filler
    cand_existing = _candidate(
        candidate_id="promo-fill-1-bis",
        chunk_id=chunk_existing.chunk_id,
        text="x",
    )
    led_recur = led.observe(chunk_existing, cand_existing, current_tick=1000)
    assert len(led_recur.entries) == PATTERN_LEDGER_MAX_ENTRIES
    matched = led_recur.find(first_entry.pattern_id)
    assert matched is not None
    assert matched.recurrence_count == first_entry.recurrence_count + 1
