"""Fixtures for I-REF-02, I-REF-03, I-REF-04, and I-REF-10 (shared)."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from fractions import Fraction

from brain.development.reflective import (
    REFLECTIVE_CATEGORY_KEY_MAX_LEN,
    REFLECTIVE_CATEGORY_MAX_KEYS,
    REFLECTIVE_NOTES_MAX_LEN,
    REFLECTIVE_NOTES_MAX_NOTES,
    REFLECTIVE_SCORES_MAX,
    REFLECTIVE_SUMMARY_ID_MAX_LEN,
    ReflectiveInspectionSnapshot,
    ReflectiveInspectionSummary,
    ReflectiveSource,
    ReflectiveSummaryItem,
)
from brain.invariants import register


def _assert_rejects(call, tag: str) -> None:
    try:
        call()
    except (TypeError, ValueError) as exc:
        assert tag in str(exc), (
            f"{tag} negative-case message lacks row tag: {exc!r}"
        )
    else:
        raise AssertionError(
            f"{tag} violated: invalid ReflectiveSummaryItem was accepted"
        )


@register("I-REF-02", status="REQUIRED")
def check_reflective_summary_item_is_bounded() -> None:
    item = ReflectiveSummaryItem(
        source=ReflectiveSource.OUTPUT_HISTORY,
        summary_id="reflective:item-1",
        entry_count=3,
        distinct_id_count=2,
        counts_by_category={"GENERATED": 2, "OPERATOR_INJECTION": 1},
        source_supplied_scores=(Fraction(1, 2),),
        notes=("ok",),
    )
    assert item.summary_id == "reflective:item-1"
    assert item.entry_count == 3
    assert item.distinct_id_count == 2

    empty = ReflectiveSummaryItem(
        source=ReflectiveSource.OUTPUT_HISTORY,
        summary_id="reflective:empty",
        entry_count=0,
        distinct_id_count=0,
        counts_by_category={},
        source_supplied_scores=(),
        notes=(),
    )
    assert empty.entry_count == 0

    _assert_rejects(
        lambda: ReflectiveSummaryItem(
            source=ReflectiveSource.OUTPUT_HISTORY,
            summary_id="",
            entry_count=0,
            distinct_id_count=0,
            counts_by_category={},
            source_supplied_scores=(),
            notes=(),
        ),
        tag="I-REF-02",
    )
    _assert_rejects(
        lambda: ReflectiveSummaryItem(
            source=ReflectiveSource.OUTPUT_HISTORY,
            summary_id="bad\nid",
            entry_count=0,
            distinct_id_count=0,
            counts_by_category={},
            source_supplied_scores=(),
            notes=(),
        ),
        tag="I-REF-02",
    )
    _assert_rejects(
        lambda: ReflectiveSummaryItem(
            source=ReflectiveSource.OUTPUT_HISTORY,
            summary_id="x" * (REFLECTIVE_SUMMARY_ID_MAX_LEN + 1),
            entry_count=0,
            distinct_id_count=0,
            counts_by_category={},
            source_supplied_scores=(),
            notes=(),
        ),
        tag="I-REF-02",
    )
    _assert_rejects(
        lambda: ReflectiveSummaryItem(
            source=ReflectiveSource.OUTPUT_HISTORY,
            summary_id="reflective:neg",
            entry_count=-1,
            distinct_id_count=0,
            counts_by_category={},
            source_supplied_scores=(),
            notes=(),
        ),
        tag="I-REF-02",
    )
    _assert_rejects(
        lambda: ReflectiveSummaryItem(
            source=ReflectiveSource.OUTPUT_HISTORY,
            summary_id="reflective:notmap",
            entry_count=0,
            distinct_id_count=0,
            counts_by_category=(),  # type: ignore[arg-type]
            source_supplied_scores=(),
            notes=(),
        ),
        tag="I-REF-02",
    )
    too_many_categories = {
        f"k{i}": 1 for i in range(REFLECTIVE_CATEGORY_MAX_KEYS + 1)
    }
    _assert_rejects(
        lambda: ReflectiveSummaryItem(
            source=ReflectiveSource.OUTPUT_HISTORY,
            summary_id="reflective:cat-overflow",
            entry_count=len(too_many_categories),
            distinct_id_count=0,
            counts_by_category=too_many_categories,
            source_supplied_scores=(),
            notes=(),
        ),
        tag="I-REF-02",
    )
    long_key = "k" * (REFLECTIVE_CATEGORY_KEY_MAX_LEN + 1)
    _assert_rejects(
        lambda: ReflectiveSummaryItem(
            source=ReflectiveSource.OUTPUT_HISTORY,
            summary_id="reflective:longkey",
            entry_count=1,
            distinct_id_count=0,
            counts_by_category={long_key: 1},
            source_supplied_scores=(),
            notes=(),
        ),
        tag="I-REF-02",
    )
    _assert_rejects(
        lambda: ReflectiveSummaryItem(
            source=ReflectiveSource.OUTPUT_HISTORY,
            summary_id="reflective:badscore",
            entry_count=0,
            distinct_id_count=0,
            counts_by_category={},
            source_supplied_scores=(0.5,),  # type: ignore[arg-type]
            notes=(),
        ),
        tag="I-REF-02",
    )
    too_many_scores = tuple(
        Fraction(0) for _ in range(REFLECTIVE_SCORES_MAX + 1)
    )
    _assert_rejects(
        lambda: ReflectiveSummaryItem(
            source=ReflectiveSource.OUTPUT_HISTORY,
            summary_id="reflective:scoreoverflow",
            entry_count=0,
            distinct_id_count=0,
            counts_by_category={},
            source_supplied_scores=too_many_scores,
            notes=(),
        ),
        tag="I-REF-02",
    )
    too_many_notes = tuple(f"n{i}" for i in range(REFLECTIVE_NOTES_MAX_NOTES + 1))
    _assert_rejects(
        lambda: ReflectiveSummaryItem(
            source=ReflectiveSource.OUTPUT_HISTORY,
            summary_id="reflective:notesoverflow",
            entry_count=0,
            distinct_id_count=0,
            counts_by_category={},
            source_supplied_scores=(),
            notes=too_many_notes,
        ),
        tag="I-REF-02",
    )
    _assert_rejects(
        lambda: ReflectiveSummaryItem(
            source=ReflectiveSource.OUTPUT_HISTORY,
            summary_id="reflective:longnote",
            entry_count=0,
            distinct_id_count=0,
            counts_by_category={},
            source_supplied_scores=(),
            notes=("x" * (REFLECTIVE_NOTES_MAX_LEN + 1),),
        ),
        tag="I-REF-02",
    )
    _assert_rejects(
        lambda: ReflectiveSummaryItem(
            source=ReflectiveSource.OUTPUT_HISTORY,
            summary_id="reflective:nonprintnote",
            entry_count=0,
            distinct_id_count=0,
            counts_by_category={},
            source_supplied_scores=(),
            notes=("bad\nnote",),
        ),
        tag="I-REF-02",
    )


@register("I-REF-03", status="REQUIRED")
def check_counts_by_category_sums_to_entry_count() -> None:
    valid = ReflectiveSummaryItem(
        source=ReflectiveSource.WORLDLET_HISTORY,
        summary_id="reflective:cat-ok",
        entry_count=4,
        distinct_id_count=2,
        counts_by_category={"accepted": 3, "rejected": 1},
        source_supplied_scores=(),
        notes=(),
    )
    assert sum(valid.counts_by_category.values()) == valid.entry_count

    _assert_rejects(
        lambda: ReflectiveSummaryItem(
            source=ReflectiveSource.WORLDLET_HISTORY,
            summary_id="reflective:cat-mismatch",
            entry_count=3,
            distinct_id_count=0,
            counts_by_category={"accepted": 2, "rejected": 2},
            source_supplied_scores=(),
            notes=(),
        ),
        tag="I-REF-03",
    )

    # Entry-count 0 with empty counts is permitted.
    zero = ReflectiveSummaryItem(
        source=ReflectiveSource.WORLDLET_HISTORY,
        summary_id="reflective:cat-zero",
        entry_count=0,
        distinct_id_count=0,
        counts_by_category={},
        source_supplied_scores=(),
        notes=(),
    )
    assert zero.entry_count == 0


@register("I-REF-04", status="REQUIRED")
def check_distinct_id_count_le_entry_count() -> None:
    ok = ReflectiveSummaryItem(
        source=ReflectiveSource.PROTO_BASIC_HISTORY,
        summary_id="reflective:distinct-ok",
        entry_count=5,
        distinct_id_count=5,
        counts_by_category={},
        source_supplied_scores=(),
        notes=(),
    )
    assert ok.distinct_id_count == 5

    _assert_rejects(
        lambda: ReflectiveSummaryItem(
            source=ReflectiveSource.PROTO_BASIC_HISTORY,
            summary_id="reflective:distinct-bad",
            entry_count=2,
            distinct_id_count=3,
            counts_by_category={},
            source_supplied_scores=(),
            notes=(),
        ),
        tag="I-REF-04",
    )


@register("I-REF-10", status="STRUCTURAL")
def check_reflective_records_are_frozen_dataclasses() -> None:
    item = ReflectiveSummaryItem(
        source=ReflectiveSource.OUTPUT_HISTORY,
        summary_id="reflective:frozen",
        entry_count=0,
        distinct_id_count=0,
        counts_by_category={},
        source_supplied_scores=(),
        notes=(),
    )
    snapshot = ReflectiveInspectionSnapshot(snapshot_id="snap:frozen", items=(item,))
    summary = ReflectiveInspectionSummary(
        snapshot_id="snap:frozen",
        item_count=1,
        counts_by_source={ReflectiveSource.OUTPUT_HISTORY: 1},
        total_entry_count=0,
        aggregate_distinct_id_count=0,
        source_supplied_score_count=0,
        notes_total=0,
    )

    for record in (item, snapshot, summary):
        assert is_dataclass(record), (
            f"I-REF-10 violated: {type(record).__name__} is not a dataclass"
        )
        params = getattr(record, "__dataclass_params__", None)
        assert params is not None and params.frozen, (
            f"I-REF-10 violated: {type(record).__name__} is not a frozen dataclass"
        )
        try:
            record.__dict__  # type: ignore[attr-defined]
        except AttributeError:
            pass
        else:
            raise AssertionError(
                f"I-REF-10 violated: {type(record).__name__} should use slots"
            )

        for f in fields(record):
            value = getattr(record, f.name)
            try:
                setattr(record, f.name, value)
            except FrozenInstanceError:
                pass
            else:
                raise AssertionError(
                    f"I-REF-10 violated: {type(record).__name__}.{f.name} "
                    "is mutable on a frozen dataclass"
                )
