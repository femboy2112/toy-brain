"""Fixtures for I-PLEDGER-01..03, I-PLEDGER-10 (constructor bounds).

Covers:

* I-PLEDGER-01 — :class:`PatternLedgerSourceKind` is a finite closed
  enumeration whose members match the accepted text-stream source
  surface.
* I-PLEDGER-02 — :class:`PatternLedgerSaturationState` is a finite
  closed enumeration with exactly ``OPEN``, ``SATURATED``,
  ``QUIESCED``.
* I-PLEDGER-03 — :class:`PatternLedgerEntry` constructor enforces
  bounded printable identifiers, ``COGITO_ID`` rejection, tuple
  evidence shape, exact ``Fraction`` confidence, tick order, source
  kind, saturation state, and provenance bounds.
* I-PLEDGER-10 — direct :class:`PatternLedgerEntry` construction with
  duplicate evidence ids rejects rather than silently normalizing.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass
from fractions import Fraction

from brain.development.pattern_ledger import (
    PATTERN_LEDGER_ID_MAX,
    PATTERN_LEDGER_SIGNATURE_ELEM_MAX,
    PatternLedgerEntry,
    PatternLedgerSaturationState,
    PatternLedgerSourceKind,
)
from brain.development.text_stream import (
    STREAM_PATTERN_RECURRENCE_MAX,
    STREAM_PATTERN_RECURRENCE_MIN,
    STREAM_PROVENANCE_MAX_LEN,
    TextStreamSource,
)
from brain.invariants import register
from brain.tlica.profile import COGITO_ID


def _valid_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        pattern_id="pledger:abc123",
        signature=("source:operator", "len:5", "lines:1"),
        evidence_chunk_ids=("strm-chunk-1",),
        evidence_candidate_ids=("promo-strm-chunk-1",),
        recurrence_count=STREAM_PATTERN_RECURRENCE_MIN,
        first_seen_tick=0,
        last_seen_tick=0,
        source_kind=PatternLedgerSourceKind.OPERATOR,
        confidence=Fraction(
            STREAM_PATTERN_RECURRENCE_MIN, STREAM_PATTERN_RECURRENCE_MAX
        ),
        saturation_state=PatternLedgerSaturationState.OPEN,
        provenance="operator",
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
            f"{tag} violated: invalid PatternLedgerEntry was accepted"
        )


@register("I-PLEDGER-01", status="REQUIRED")
def check_pattern_ledger_source_kind_closed() -> None:
    members = {m.value for m in PatternLedgerSourceKind}
    expected = {"operator", "system", "probe_echo", "generated"}
    assert members == expected, (
        f"I-PLEDGER-01 violated: PatternLedgerSourceKind membership "
        f"drifted (got {members!r}, expected {expected!r})"
    )

    # Parity with TextStreamSource: every accepted text-stream source
    # value must map to a ledger source kind value.
    stream_values = {m.value for m in TextStreamSource}
    assert stream_values == expected, (
        "I-PLEDGER-01 violated: PatternLedgerSourceKind does not match "
        f"TextStreamSource membership (got stream={stream_values!r}, "
        f"expected {expected!r})"
    )

    # Unknown value construction rejects.
    try:
        PatternLedgerSourceKind("not-a-source")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-PLEDGER-01 violated: PatternLedgerSourceKind accepted "
            "unknown value"
        )


@register("I-PLEDGER-02", status="REQUIRED")
def check_pattern_ledger_saturation_state_closed() -> None:
    members = {m.value for m in PatternLedgerSaturationState}
    expected = {"open", "saturated", "quiesced"}
    assert members == expected, (
        f"I-PLEDGER-02 violated: PatternLedgerSaturationState membership "
        f"drifted (got {members!r}, expected {expected!r})"
    )

    try:
        PatternLedgerSaturationState("transient")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-PLEDGER-02 violated: PatternLedgerSaturationState accepted "
            "unknown value"
        )


@register("I-PLEDGER-03", status="REQUIRED")
def check_pattern_ledger_entry_constructor() -> None:
    # Valid construction.
    entry = PatternLedgerEntry(**_valid_kwargs())
    assert entry.pattern_id == "pledger:abc123"
    assert entry.signature == ("source:operator", "len:5", "lines:1")
    assert entry.evidence_chunk_ids == ("strm-chunk-1",)
    assert entry.evidence_candidate_ids == ("promo-strm-chunk-1",)
    assert entry.recurrence_count == STREAM_PATTERN_RECURRENCE_MIN
    assert entry.first_seen_tick == 0
    assert entry.last_seen_tick == 0
    assert entry.source_kind is PatternLedgerSourceKind.OPERATOR
    assert entry.saturation_state is PatternLedgerSaturationState.OPEN
    assert entry.provenance == "operator"
    assert entry.confidence == Fraction(
        STREAM_PATTERN_RECURRENCE_MIN, STREAM_PATTERN_RECURRENCE_MAX
    )

    # Frozen / slotted.
    assert is_dataclass(entry)
    assert getattr(type(entry), "__dataclass_params__").frozen
    try:
        entry.pattern_id = "mutated"  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "I-PLEDGER-03 violated: PatternLedgerEntry is not frozen"
        )

    # COGITO_ID rejection on every id-bearing field.
    _assert_rejects(
        lambda: PatternLedgerEntry(**_valid_kwargs(pattern_id=COGITO_ID)),
        tag="I-PLEDGER-03",
    )
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(signature=(COGITO_ID, "len:5"))
        ),
        tag="I-PLEDGER-03",
    )
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(evidence_chunk_ids=(COGITO_ID,))
        ),
        tag="I-PLEDGER-03",
    )
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(evidence_candidate_ids=(COGITO_ID,))
        ),
        tag="I-PLEDGER-03",
    )
    _assert_rejects(
        lambda: PatternLedgerEntry(**_valid_kwargs(provenance=COGITO_ID)),
        tag="I-PLEDGER-03",
    )

    # Malformed identifiers (empty / non-printable / over-length).
    _assert_rejects(
        lambda: PatternLedgerEntry(**_valid_kwargs(pattern_id="")),
        tag="I-PLEDGER-03",
    )
    _assert_rejects(
        lambda: PatternLedgerEntry(**_valid_kwargs(pattern_id="bad\x00id")),
        tag="I-PLEDGER-03",
    )
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(pattern_id="p" * (PATTERN_LEDGER_ID_MAX + 1))
        ),
        tag="I-PLEDGER-03",
    )
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(provenance="p" * (STREAM_PROVENANCE_MAX_LEN + 1))
        ),
        tag="I-PLEDGER-03",
    )
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(
                signature=("s" * (PATTERN_LEDGER_SIGNATURE_ELEM_MAX + 1),)
            )
        ),
        tag="I-PLEDGER-03",
    )

    # Tuple shape required.
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(signature=["source:operator"])
        ),
        tag="I-PLEDGER-03",
    )
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(evidence_chunk_ids=["strm-chunk-1"])
        ),
        tag="I-PLEDGER-03",
    )

    # Empty signature.
    _assert_rejects(
        lambda: PatternLedgerEntry(**_valid_kwargs(signature=())),
        tag="I-PLEDGER-03",
    )

    # recurrence_count out of range.
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(
                recurrence_count=STREAM_PATTERN_RECURRENCE_MIN - 1,
                confidence=Fraction(
                    STREAM_PATTERN_RECURRENCE_MIN - 1,
                    STREAM_PATTERN_RECURRENCE_MAX,
                ),
            )
        ),
        tag="I-PLEDGER-03",
    )
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(
                recurrence_count=STREAM_PATTERN_RECURRENCE_MAX + 1,
            )
        ),
        tag="I-PLEDGER-03",
    )

    # confidence mismatch with recurrence_count.
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(confidence=Fraction(99, 100))
        ),
        tag="I-PLEDGER-03",
    )

    # confidence outside [0, 1].
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(
                recurrence_count=STREAM_PATTERN_RECURRENCE_MAX,
                confidence=Fraction(257, 256),
            )
        ),
        tag="I-PLEDGER-03",
    )
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(
                recurrence_count=STREAM_PATTERN_RECURRENCE_MIN,
                confidence=Fraction(-1, 256),
            )
        ),
        tag="I-PLEDGER-03",
    )

    # confidence must be Fraction (not float).
    _assert_rejects(
        lambda: PatternLedgerEntry(**_valid_kwargs(confidence=0.5)),
        tag="I-PLEDGER-03",
    )

    # tick order violation.
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(first_seen_tick=5, last_seen_tick=3)
        ),
        tag="I-PLEDGER-03",
    )
    _assert_rejects(
        lambda: PatternLedgerEntry(**_valid_kwargs(first_seen_tick=-1)),
        tag="I-PLEDGER-03",
    )

    # source_kind / saturation_state must be the closed enums.
    _assert_rejects(
        lambda: PatternLedgerEntry(**_valid_kwargs(source_kind="operator")),
        tag="I-PLEDGER-03",
    )
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(saturation_state="open")
        ),
        tag="I-PLEDGER-03",
    )

    # Empty provenance.
    _assert_rejects(
        lambda: PatternLedgerEntry(**_valid_kwargs(provenance="")),
        tag="I-PLEDGER-03",
    )

    # Pattern Ledger entries must not expose any truth / agency /
    # semantic / readability field. Mirrors the I-STRM-06 forbidden
    # attribute audit.
    forbidden_attrs = (
        "preserve",
        "damage",
        "pce",
        "projected_pce",
        "feasible_projected_pce",
        "feasibleProjectedPCE",
        "act",
        "mode_op",
        "mode",
        "agency_witness",
        "agency",
        "truth",
        "validity",
        "readability_score",
        "language",
        "meaning",
        "tick_callback",
        "consciousness",
        "sentience",
        "awareness",
    )
    for name in forbidden_attrs:
        assert not hasattr(entry, name), (
            f"I-PLEDGER-03 violated: PatternLedgerEntry exposes forbidden "
            f"field {name!r}"
        )


@register("I-PLEDGER-10", status="REQUIRED")
def check_pattern_ledger_entry_rejects_duplicate_evidence() -> None:
    """Direct constructor with duplicate evidence ids rejects."""
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(
                evidence_chunk_ids=("strm-chunk-1", "strm-chunk-1"),
            )
        ),
        tag="I-PLEDGER-03",
    )
    _assert_rejects(
        lambda: PatternLedgerEntry(
            **_valid_kwargs(
                evidence_candidate_ids=(
                    "promo-strm-chunk-1",
                    "promo-strm-chunk-1",
                ),
            )
        ),
        tag="I-PLEDGER-03",
    )

    # A constructor that allowed duplicates would silently normalize;
    # the I-PLEDGER-10 contract is that normalization is the
    # responsibility of PatternLedger.observe(...), not the strict
    # constructor.
    valid_kwargs = _valid_kwargs(
        evidence_chunk_ids=("strm-chunk-1", "strm-chunk-2"),
        evidence_candidate_ids=("promo-strm-chunk-1", "promo-strm-chunk-2"),
    )
    entry = PatternLedgerEntry(**valid_kwargs)
    assert entry.evidence_chunk_ids == ("strm-chunk-1", "strm-chunk-2")
    assert entry.evidence_candidate_ids == (
        "promo-strm-chunk-1",
        "promo-strm-chunk-2",
    )
