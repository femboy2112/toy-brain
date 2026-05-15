"""Phase 3.6 Reflective Inspection primitives.

A bounded local read-only summary layer over Phase 3.1-3.5 developmental
histories (`OutputHistory`, `WorldletHistory`, `ProtoBasicHistory`,
`ExpressionHistory`) and the Operator TUI transcript (`OperatorTranscript`).
The layer walks existing source records and produces frozen summary records
for inspection. It is not Mode B, not language, not truth, not agency, not a
UI surface in Phase 3.6: see ``PHASE3_6_REFLECTIVE_INSPECTION_SYNTHESIS.md``.

The module is deliberately closed: it imports no I/O, network, file, shell,
TLICA, tick, or LLM surface, performs no module-level side effect, does not
register any callback, and uses only ``int`` and ``Fraction`` arithmetic on
the count / statistic path. The bridge constructors below are pure functions
that read source records via duck-typed attributes and return new
``ReflectiveSummaryItem`` values without calling any source-history mutator.

The reflective layer surfaces counts and source-supplied exact statistics; it
does NOT produce an aggregate score, quality estimate, intelligence measure,
social-success measure, or truth claim (I-REF-08). Source-supplied score
passthroughs are explicitly tagged via the ``source_supplied_scores`` field.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from types import MappingProxyType
from typing import Mapping

from brain.development.history import require_printable_id

# Bounded local discipline (corrigenda-locked ranges in
# PHASE3_6_REFLECTIVE_INSPECTION_CATALOG_PATCH_PLAN.md section 11).
REFLECTIVE_NOTES_MAX_NOTES: int = 8
REFLECTIVE_NOTES_MAX_LEN: int = 64
REFLECTIVE_CATEGORY_MAX_KEYS: int = 8
REFLECTIVE_CATEGORY_KEY_MAX_LEN: int = 64
REFLECTIVE_SCORES_MAX: int = 256
REFLECTIVE_SUMMARY_ID_MAX_LEN: int = 64


class ReflectiveSource(Enum):
    """Finite closed enumeration of reflective source kinds (I-REF-01)."""

    OUTPUT_HISTORY = "output_history"
    WORLDLET_HISTORY = "worldlet_history"
    PROTO_BASIC_HISTORY = "proto_basic_history"
    EXPRESSION_HISTORY = "expression_history"
    OPERATOR_TRANSCRIPT = "operator_transcript"


def _require_int_nonneg(value: object, *, field: str, row_id: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(
            f"{row_id} violated: {field} must be int "
            f"(got {type(value).__name__})"
        )
    if value < 0:
        raise ValueError(f"{row_id} violated: {field} must be >= 0 (got {value})")
    return value


@dataclass(frozen=True, slots=True)
class ReflectiveSummaryItem:
    """Bounded read-only summary of one source-tagged developmental history.

    Drives I-REF-02, I-REF-03, I-REF-04, I-REF-08, I-REF-10. Fields are
    bounded primitives, tuples of bounded primitives, ``Fraction``, or
    immutable mappings. No callable, file handle, socket, LLM client,
    path object, or aggregate-score field appears here.
    """

    source: ReflectiveSource
    summary_id: str
    entry_count: int
    distinct_id_count: int
    counts_by_category: Mapping[str, int]
    source_supplied_scores: tuple[Fraction, ...]
    notes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source, ReflectiveSource):
            raise ValueError(
                "I-REF-02 violated: ReflectiveSummaryItem.source must be a "
                f"ReflectiveSource (got {type(self.source).__name__})"
            )
        try:
            require_printable_id(
                self.summary_id, field="ReflectiveSummaryItem.summary_id"
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-REF-02 violated: ReflectiveSummaryItem.summary_id must be "
                "non-empty and printable"
            ) from exc
        if len(self.summary_id) > REFLECTIVE_SUMMARY_ID_MAX_LEN:
            raise ValueError(
                f"I-REF-02 violated: summary_id length {len(self.summary_id)} "
                f"exceeds REFLECTIVE_SUMMARY_ID_MAX_LEN="
                f"{REFLECTIVE_SUMMARY_ID_MAX_LEN}"
            )

        _require_int_nonneg(
            self.entry_count,
            field="ReflectiveSummaryItem.entry_count",
            row_id="I-REF-02",
        )
        _require_int_nonneg(
            self.distinct_id_count,
            field="ReflectiveSummaryItem.distinct_id_count",
            row_id="I-REF-02",
        )
        if self.distinct_id_count > self.entry_count:
            raise ValueError(
                "I-REF-04 violated: distinct_id_count "
                f"{self.distinct_id_count} exceeds entry_count "
                f"{self.entry_count}"
            )

        if not isinstance(self.counts_by_category, Mapping):
            raise ValueError(
                "I-REF-02 violated: counts_by_category must be a Mapping "
                f"(got {type(self.counts_by_category).__name__})"
            )
        cat_dict: dict[str, int] = {}
        for key, value in self.counts_by_category.items():
            if (
                not isinstance(key, str)
                or not key
                or not key.isprintable()
                or len(key) > REFLECTIVE_CATEGORY_KEY_MAX_LEN
            ):
                raise ValueError(
                    "I-REF-02 violated: counts_by_category key must be a "
                    "bounded non-empty printable string "
                    f"(got {key!r})"
                )
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                raise ValueError(
                    "I-REF-02 violated: counts_by_category value must be a "
                    f"non-negative int (got {value!r})"
                )
            cat_dict[key] = value
        if len(cat_dict) > REFLECTIVE_CATEGORY_MAX_KEYS:
            raise ValueError(
                f"I-REF-02 violated: counts_by_category has {len(cat_dict)} "
                f"entries; max is REFLECTIVE_CATEGORY_MAX_KEYS="
                f"{REFLECTIVE_CATEGORY_MAX_KEYS}"
            )
        if cat_dict:
            cat_total = 0
            for v in cat_dict.values():
                cat_total += v
            if cat_total != self.entry_count:
                raise ValueError(
                    "I-REF-03 violated: counts_by_category sums to "
                    f"{cat_total} but entry_count is {self.entry_count}"
                )

        if not isinstance(self.source_supplied_scores, tuple):
            raise ValueError(
                "I-REF-02 violated: source_supplied_scores must be a tuple "
                f"(got {type(self.source_supplied_scores).__name__})"
            )
        if len(self.source_supplied_scores) > REFLECTIVE_SCORES_MAX:
            raise ValueError(
                "I-REF-02 violated: source_supplied_scores has "
                f"{len(self.source_supplied_scores)} entries; max is "
                f"REFLECTIVE_SCORES_MAX={REFLECTIVE_SCORES_MAX}"
            )
        for s in self.source_supplied_scores:
            if not isinstance(s, Fraction):
                raise ValueError(
                    "I-REF-02 violated: source_supplied_scores entries must "
                    f"be Fraction (got {type(s).__name__})"
                )

        if not isinstance(self.notes, tuple):
            raise ValueError(
                "I-REF-02 violated: notes must be a tuple "
                f"(got {type(self.notes).__name__})"
            )
        if len(self.notes) > REFLECTIVE_NOTES_MAX_NOTES:
            raise ValueError(
                f"I-REF-02 violated: notes has {len(self.notes)} entries; "
                f"max is REFLECTIVE_NOTES_MAX_NOTES="
                f"{REFLECTIVE_NOTES_MAX_NOTES}"
            )
        for note in self.notes:
            if not isinstance(note, str):
                raise ValueError(
                    "I-REF-02 violated: notes entries must be str "
                    f"(got {type(note).__name__})"
                )
            if not note or not note.isprintable():
                raise ValueError(
                    "I-REF-02 violated: notes entries must be non-empty "
                    "printable strings"
                )
            if len(note) > REFLECTIVE_NOTES_MAX_LEN:
                raise ValueError(
                    f"I-REF-02 violated: note length {len(note)} exceeds "
                    f"REFLECTIVE_NOTES_MAX_LEN={REFLECTIVE_NOTES_MAX_LEN}"
                )

        object.__setattr__(
            self, "counts_by_category", MappingProxyType(cat_dict)
        )


@dataclass(frozen=True, slots=True)
class ReflectiveInspectionSnapshot:
    """Frozen snapshot composing one ReflectiveSummaryItem per source.

    Drives I-REF-05, I-REF-10. The snapshot holds only frozen records and
    bounded primitives. Construction is deterministic for the same source
    histories.
    """

    snapshot_id: str
    items: tuple[ReflectiveSummaryItem, ...]

    def __post_init__(self) -> None:
        try:
            require_printable_id(
                self.snapshot_id, field="ReflectiveInspectionSnapshot.snapshot_id"
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-REF-05 violated: snapshot_id must be non-empty and printable"
            ) from exc
        if len(self.snapshot_id) > REFLECTIVE_SUMMARY_ID_MAX_LEN:
            raise ValueError(
                f"I-REF-05 violated: snapshot_id length {len(self.snapshot_id)} "
                f"exceeds REFLECTIVE_SUMMARY_ID_MAX_LEN="
                f"{REFLECTIVE_SUMMARY_ID_MAX_LEN}"
            )
        if not isinstance(self.items, tuple):
            raise ValueError(
                "I-REF-05 violated: items must be a tuple "
                f"(got {type(self.items).__name__})"
            )
        seen_sources: set[ReflectiveSource] = set()
        for item in self.items:
            if not isinstance(item, ReflectiveSummaryItem):
                raise ValueError(
                    "I-REF-05 violated: items must contain "
                    "ReflectiveSummaryItem values "
                    f"(got {type(item).__name__})"
                )
            if item.source in seen_sources:
                raise ValueError(
                    "I-REF-05 violated: snapshot has duplicate source "
                    f"{item.source.name}"
                )
            seen_sources.add(item.source)


@dataclass(frozen=True, slots=True)
class ReflectiveInspectionSummary:
    """Frozen aggregate over one ReflectiveInspectionSnapshot.

    Drives I-REF-10, I-REF-13. Records source-tagged item counts, total
    entry / distinct-id counts, source-supplied score counts, and note
    counts. No aggregate score, quality estimate, intelligence measure,
    or social-success measure is produced (I-REF-08).
    """

    snapshot_id: str
    item_count: int
    counts_by_source: Mapping[ReflectiveSource, int]
    total_entry_count: int
    aggregate_distinct_id_count: int
    source_supplied_score_count: int
    notes_total: int

    def __post_init__(self) -> None:
        try:
            require_printable_id(
                self.snapshot_id, field="ReflectiveInspectionSummary.snapshot_id"
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-REF-05 violated: ReflectiveInspectionSummary.snapshot_id "
                "must be non-empty and printable"
            ) from exc
        for field_name, value in (
            ("item_count", self.item_count),
            ("total_entry_count", self.total_entry_count),
            ("aggregate_distinct_id_count", self.aggregate_distinct_id_count),
            ("source_supplied_score_count", self.source_supplied_score_count),
            ("notes_total", self.notes_total),
        ):
            _require_int_nonneg(
                value,
                field=f"ReflectiveInspectionSummary.{field_name}",
                row_id="I-REF-02",
            )
        if not isinstance(self.counts_by_source, Mapping):
            raise ValueError(
                "I-REF-02 violated: counts_by_source must be a Mapping "
                f"(got {type(self.counts_by_source).__name__})"
            )
        cs: dict[ReflectiveSource, int] = {}
        for key, value in self.counts_by_source.items():
            if not isinstance(key, ReflectiveSource):
                raise ValueError(
                    "I-REF-02 violated: counts_by_source key must be a "
                    f"ReflectiveSource (got {type(key).__name__})"
                )
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(
                    "I-REF-02 violated: counts_by_source value must be a "
                    f"non-negative int (got {value!r})"
                )
            cs[key] = value
        object.__setattr__(self, "counts_by_source", MappingProxyType(cs))


# ---------------------------------------------------------------------------
# Bridge constructors (pure, no callbacks, no source-history mutation).
#
# Each bridge accepts a duck-typed source record container and returns a
# ReflectiveSummaryItem. They never call a source-history mutator and never
# read environment variables, time sources, network endpoints, or files.
# ---------------------------------------------------------------------------


def _enum_kind_name(value: object) -> str:
    name = getattr(value, "name", None)
    if isinstance(name, str) and name and name.isprintable():
        if len(name) > REFLECTIVE_CATEGORY_KEY_MAX_LEN:
            return name[:REFLECTIVE_CATEGORY_KEY_MAX_LEN]
        return name
    return "unknown"


def make_reflective_item_from_output_history(history: object) -> ReflectiveSummaryItem:
    """Build a ReflectiveSummaryItem from an OutputHistory-like object."""
    impulses = getattr(history, "impulses", None)
    if not isinstance(impulses, tuple):
        raise TypeError(
            "make_reflective_item_from_output_history requires history.impulses "
            f"to be a tuple (got {type(impulses).__name__})"
        )
    counts: dict[str, int] = {}
    distinct_ids: set[str] = set()
    for impulse in impulses:
        impulse_id = getattr(impulse, "impulse_id", None)
        if isinstance(impulse_id, str) and impulse_id:
            distinct_ids.add(impulse_id)
        provenance = getattr(impulse, "provenance", None)
        kind = getattr(provenance, "source_kind", None)
        key = _enum_kind_name(kind)
        counts[key] = counts.get(key, 0) + 1
    return ReflectiveSummaryItem(
        source=ReflectiveSource.OUTPUT_HISTORY,
        summary_id="reflective:output_history",
        entry_count=len(impulses),
        distinct_id_count=len(distinct_ids),
        counts_by_category=counts,
        source_supplied_scores=(),
        notes=(),
    )


def make_reflective_item_from_worldlet_history(
    history: object,
) -> ReflectiveSummaryItem:
    """Build a ReflectiveSummaryItem from a WorldletHistory-like object."""
    responses = getattr(history, "responses", None)
    if not isinstance(responses, tuple):
        raise TypeError(
            "make_reflective_item_from_worldlet_history requires "
            f"history.responses to be a tuple (got {type(responses).__name__})"
        )
    counts: dict[str, int] = {}
    distinct_ids: set[str] = set()
    valences: list[Fraction] = []
    for response in responses:
        response_id = getattr(response, "response_id", None)
        if isinstance(response_id, str) and response_id:
            distinct_ids.add(response_id)
        accepted = getattr(response, "accepted", None)
        key = "accepted" if bool(accepted) else "rejected"
        counts[key] = counts.get(key, 0) + 1
        valence = getattr(response, "valence", None)
        v = getattr(valence, "value", None)
        if isinstance(v, Fraction):
            valences.append(v)
    if len(valences) > REFLECTIVE_SCORES_MAX:
        valences = valences[-REFLECTIVE_SCORES_MAX:]
    return ReflectiveSummaryItem(
        source=ReflectiveSource.WORLDLET_HISTORY,
        summary_id="reflective:worldlet_history",
        entry_count=len(responses),
        distinct_id_count=len(distinct_ids),
        counts_by_category=counts,
        source_supplied_scores=tuple(valences),
        notes=(),
    )


def make_reflective_item_from_proto_basic_history(
    history: object,
) -> ReflectiveSummaryItem:
    """Build a ReflectiveSummaryItem from a ProtoBasicHistory-like object."""
    parse_results = getattr(history, "parse_results", None)
    commands = getattr(history, "commands", None)
    execution_results = getattr(history, "execution_results", None)
    feedback = getattr(history, "feedback", None)
    for label, value in (
        ("parse_results", parse_results),
        ("commands", commands),
        ("execution_results", execution_results),
        ("feedback", feedback),
    ):
        if not isinstance(value, tuple):
            raise TypeError(
                "make_reflective_item_from_proto_basic_history requires "
                f"history.{label} to be a tuple (got {type(value).__name__})"
            )
    counts: dict[str, int] = {}
    if parse_results:
        counts["parse_results"] = len(parse_results)
    if commands:
        counts["commands"] = len(commands)
    if execution_results:
        counts["execution_results"] = len(execution_results)
    if feedback:
        counts["feedback"] = len(feedback)
    distinct_ids: set[str] = set()
    for line in parse_results:
        line_id = getattr(getattr(line, "line", None), "line_id", None)
        if isinstance(line_id, str) and line_id:
            distinct_ids.add(line_id)
    entry_count = (
        len(parse_results) + len(commands) + len(execution_results) + len(feedback)
    )
    distinct_capped = min(len(distinct_ids), entry_count)
    return ReflectiveSummaryItem(
        source=ReflectiveSource.PROTO_BASIC_HISTORY,
        summary_id="reflective:proto_basic_history",
        entry_count=entry_count,
        distinct_id_count=distinct_capped,
        counts_by_category=counts,
        source_supplied_scores=(),
        notes=(),
    )


def make_reflective_item_from_expression_history(
    history: object,
) -> ReflectiveSummaryItem:
    """Build a ReflectiveSummaryItem from an ExpressionHistory-like object."""
    records = getattr(history, "records", None)
    if not isinstance(records, tuple):
        raise TypeError(
            "make_reflective_item_from_expression_history requires "
            f"history.records to be a tuple (got {type(records).__name__})"
        )
    counts: dict[str, int] = {}
    distinct_ids: set[str] = set()
    scores: list[Fraction] = []
    for record in records:
        item = getattr(record, "item", None)
        item_id = getattr(item, "item_id", None)
        source = getattr(item, "source", None)
        if isinstance(item_id, str) and item_id:
            distinct_ids.add(item_id)
        key = _enum_kind_name(source)
        counts[key] = counts.get(key, 0) + 1
        prediction = getattr(record, "prediction", None)
        score = getattr(prediction, "score", None)
        v = getattr(score, "value", None)
        if isinstance(v, Fraction):
            scores.append(v)
    if len(scores) > REFLECTIVE_SCORES_MAX:
        scores = scores[-REFLECTIVE_SCORES_MAX:]
    return ReflectiveSummaryItem(
        source=ReflectiveSource.EXPRESSION_HISTORY,
        summary_id="reflective:expression_history",
        entry_count=len(records),
        distinct_id_count=len(distinct_ids),
        counts_by_category=counts,
        source_supplied_scores=tuple(scores),
        notes=(),
    )


def make_reflective_item_from_operator_transcript(
    transcript: object,
) -> ReflectiveSummaryItem:
    """Build a ReflectiveSummaryItem from an OperatorTranscript-like object."""
    entries = getattr(transcript, "entries", None)
    if not isinstance(entries, tuple):
        raise TypeError(
            "make_reflective_item_from_operator_transcript requires "
            f"transcript.entries to be a tuple (got {type(entries).__name__})"
        )
    counts: dict[str, int] = {}
    distinct_ticks: set[int] = set()
    for entry in entries:
        kind = getattr(entry, "kind", None)
        key = _enum_kind_name(kind)
        counts[key] = counts.get(key, 0) + 1
        tick_at_event = getattr(entry, "tick_at_event", None)
        if isinstance(tick_at_event, int) and not isinstance(tick_at_event, bool):
            distinct_ticks.add(tick_at_event)
    distinct_capped = min(len(distinct_ticks), len(entries))
    return ReflectiveSummaryItem(
        source=ReflectiveSource.OPERATOR_TRANSCRIPT,
        summary_id="reflective:operator_transcript",
        entry_count=len(entries),
        distinct_id_count=distinct_capped,
        counts_by_category=counts,
        source_supplied_scores=(),
        notes=(),
    )


# Canonical bridge order — used by ``make_reflective_snapshot`` so the
# resulting snapshot is deterministic for the same set of source histories.
_BRIDGE_ORDER: tuple[ReflectiveSource, ...] = (
    ReflectiveSource.OUTPUT_HISTORY,
    ReflectiveSource.WORLDLET_HISTORY,
    ReflectiveSource.PROTO_BASIC_HISTORY,
    ReflectiveSource.EXPRESSION_HISTORY,
    ReflectiveSource.OPERATOR_TRANSCRIPT,
)


def make_reflective_snapshot(
    *,
    snapshot_id: str = "reflective:snapshot",
    output_history: object | None = None,
    worldlet_history: object | None = None,
    proto_basic_history: object | None = None,
    expression_history: object | None = None,
    operator_transcript: object | None = None,
) -> ReflectiveInspectionSnapshot:
    """Compose a deterministic ReflectiveInspectionSnapshot.

    Each present source contributes one ``ReflectiveSummaryItem``. Items
    appear in the canonical ``_BRIDGE_ORDER`` so equal source histories
    always yield equal snapshots (I-REF-05).
    """
    by_source: dict[ReflectiveSource, ReflectiveSummaryItem] = {}
    if output_history is not None:
        by_source[ReflectiveSource.OUTPUT_HISTORY] = (
            make_reflective_item_from_output_history(output_history)
        )
    if worldlet_history is not None:
        by_source[ReflectiveSource.WORLDLET_HISTORY] = (
            make_reflective_item_from_worldlet_history(worldlet_history)
        )
    if proto_basic_history is not None:
        by_source[ReflectiveSource.PROTO_BASIC_HISTORY] = (
            make_reflective_item_from_proto_basic_history(proto_basic_history)
        )
    if expression_history is not None:
        by_source[ReflectiveSource.EXPRESSION_HISTORY] = (
            make_reflective_item_from_expression_history(expression_history)
        )
    if operator_transcript is not None:
        by_source[ReflectiveSource.OPERATOR_TRANSCRIPT] = (
            make_reflective_item_from_operator_transcript(operator_transcript)
        )
    items = tuple(by_source[s] for s in _BRIDGE_ORDER if s in by_source)
    return ReflectiveInspectionSnapshot(snapshot_id=snapshot_id, items=items)


def make_reflective_summary(
    snapshot: ReflectiveInspectionSnapshot,
) -> ReflectiveInspectionSummary:
    """Aggregate one snapshot into a ReflectiveInspectionSummary.

    No aggregate score is produced (I-REF-08); the summary only counts
    items, total entries, distinct ids, source-supplied score passthroughs,
    and notes.
    """
    if not isinstance(snapshot, ReflectiveInspectionSnapshot):
        raise TypeError(
            "make_reflective_summary expects ReflectiveInspectionSnapshot "
            f"(got {type(snapshot).__name__})"
        )
    counts_by_source: dict[ReflectiveSource, int] = {s: 0 for s in ReflectiveSource}
    total_entry_count = 0
    aggregate_distinct = 0
    score_count = 0
    notes_total = 0
    for item in snapshot.items:
        counts_by_source[item.source] = counts_by_source[item.source] + 1
        total_entry_count += item.entry_count
        aggregate_distinct += item.distinct_id_count
        score_count += len(item.source_supplied_scores)
        notes_total += len(item.notes)
    return ReflectiveInspectionSummary(
        snapshot_id=snapshot.snapshot_id,
        item_count=len(snapshot.items),
        counts_by_source=counts_by_source,
        total_entry_count=total_entry_count,
        aggregate_distinct_id_count=aggregate_distinct,
        source_supplied_score_count=score_count,
        notes_total=notes_total,
    )
