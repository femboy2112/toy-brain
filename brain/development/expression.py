"""Phase 3.5 Expression + ReadabilityPredictor primitives.

A bounded local layer over Phase 3.1-3.4 developmental histories
(`OutputHistory`, `WorldletHistory`, `ProtoBasicHistory`) and the Operator
TUI transcript (`OperatorTranscript`). Inspects, summarizes, and predicts
readability of local printable text items. Not language, not truth, not
agency: see `PHASE3_5_EXPRESSION_READABILITY_SYNTHESIS.md`.

The module is deliberately closed: it imports no I/O, network, file,
shell, or LLM surface, performs no module-level side effect, does not
register any callback, and uses only `int` and `Fraction` arithmetic on
the score path. The bridge constructors below are pure functions that
read source records via duck-typed attributes and return new
`ExpressionRecord` values without calling any source-history mutator.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from types import MappingProxyType
from typing import Mapping

from brain.development.history import require_printable_id

# Bounded local discipline (corrigenda-locked ranges in
# PHASE3_5_EXPRESSION_READABILITY_CATALOG_PATCH_PLAN.md section 12).
EXPRESSION_TEXT_MAX_LEN: int = 1024
EXPRESSION_TOKEN_MAX_COUNT: int = 256
EXPRESSION_HISTORY_MAX_ENTRIES: int = 256
LENGTH_SATURATION_BOUND: int = 64

W_PRINTABLE: Fraction = Fraction(1, 4)
W_SHAPE: Fraction = Fraction(1, 4)
W_DISTINCT: Fraction = Fraction(1, 2)
W_REPEAT: Fraction = Fraction(1, 4)

PREDICTOR_ID: str = "phase3_5/readability/v0"


class ExpressionSource(Enum):
    """Finite closed enumeration of expression source kinds (I-EXP-01)."""

    OUTPUT_HISTORY = "output_history"
    WORLDLET_HISTORY = "worldlet_history"
    PROTO_BASIC_HISTORY = "proto_basic_history"
    OPERATOR_TRANSCRIPT = "operator_transcript"


@dataclass(frozen=True, slots=True)
class ExpressionItem:
    """Bounded printable local evidence item (I-EXP-02)."""

    item_id: str
    text: str
    source: ExpressionSource

    def __post_init__(self) -> None:
        try:
            require_printable_id(self.item_id, field="ExpressionItem.item_id")
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-EXP-02 violated: ExpressionItem.item_id must be non-empty "
                "and printable"
            ) from exc
        if not isinstance(self.text, str):
            raise TypeError(
                "I-EXP-02 violated: ExpressionItem.text must be a string "
                f"(got {type(self.text).__name__})"
            )
        if self.text and not self.text.isprintable():
            raise ValueError(
                "I-EXP-02 violated: ExpressionItem.text must be printable"
            )
        if len(self.text) > EXPRESSION_TEXT_MAX_LEN:
            raise ValueError(
                f"I-EXP-02 violated: ExpressionItem.text length "
                f"{len(self.text)} exceeds "
                f"EXPRESSION_TEXT_MAX_LEN={EXPRESSION_TEXT_MAX_LEN}"
            )
        if not isinstance(self.source, ExpressionSource):
            raise TypeError(
                "I-EXP-01 violated: ExpressionItem.source must be an "
                f"ExpressionSource (got {type(self.source).__name__})"
            )


def _tokenize(text: str) -> tuple[str, ...]:
    if not text:
        return ()
    tokens = tuple(text.split())
    if len(tokens) > EXPRESSION_TOKEN_MAX_COUNT:
        tokens = tokens[:EXPRESSION_TOKEN_MAX_COUNT]
    return tokens


@dataclass(frozen=True, slots=True)
class ExpressionFeatureVector:
    """Deterministic exact feature vector for an `ExpressionItem` (I-EXP-03)."""

    char_count: int
    token_count: int
    printable_non_space_count: int
    distinct_token_count: int
    max_run_length: int
    whitespace_only: bool


def extract_features(item: ExpressionItem) -> ExpressionFeatureVector:
    if not isinstance(item, ExpressionItem):
        raise TypeError(
            f"extract_features expects ExpressionItem (got {type(item).__name__})"
        )
    text = item.text
    tokens = _tokenize(text)
    printable_non_space = sum(
        1 for ch in text if ch.isprintable() and not ch.isspace()
    )
    distinct = len(set(tokens))
    max_run = 0
    current_run = 0
    prev: str | None = None
    for tok in tokens:
        if tok == prev:
            current_run += 1
        else:
            current_run = 1
            prev = tok
        if current_run > max_run:
            max_run = current_run
    whitespace_only = (not text) or (not text.strip())
    return ExpressionFeatureVector(
        char_count=len(text),
        token_count=len(tokens),
        printable_non_space_count=printable_non_space,
        distinct_token_count=distinct,
        max_run_length=max_run,
        whitespace_only=whitespace_only,
    )


@dataclass(frozen=True, slots=True)
class ReadabilityScore:
    """Exact `Fraction` score in `[0, 1]` (I-EXP-04)."""

    value: Fraction

    def __post_init__(self) -> None:
        if not isinstance(self.value, Fraction):
            raise TypeError(
                "I-EXP-04 violated: ReadabilityScore.value must be a Fraction "
                f"(got {type(self.value).__name__})"
            )
        if self.value < Fraction(0) or self.value > Fraction(1):
            raise ValueError(
                f"I-EXP-04 violated: ReadabilityScore.value {self.value} is "
                "outside [0, 1]"
            )


@dataclass(frozen=True, slots=True)
class ReadabilityPrediction:
    """Source-tagged and predictor-tagged readability prediction (I-EXP-05)."""

    item_id: str
    source: ExpressionSource
    predictor_id: str
    score: ReadabilityScore

    def __post_init__(self) -> None:
        try:
            require_printable_id(
                self.item_id, field="ReadabilityPrediction.item_id"
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-EXP-05 violated: ReadabilityPrediction.item_id must be "
                "non-empty and printable"
            ) from exc
        if not isinstance(self.source, ExpressionSource):
            raise TypeError(
                "I-EXP-05 violated: ReadabilityPrediction.source must be "
                "an ExpressionSource"
            )
        try:
            require_printable_id(
                self.predictor_id, field="ReadabilityPrediction.predictor_id"
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-EXP-05 violated: ReadabilityPrediction.predictor_id must "
                "be non-empty and printable"
            ) from exc
        if not isinstance(self.score, ReadabilityScore):
            raise TypeError(
                "I-EXP-05 violated: ReadabilityPrediction.score must be a "
                "ReadabilityScore"
            )


def predict_readability(item: ExpressionItem) -> ReadabilityPrediction:
    """Deterministic readability prediction.

    This module computes a bounded structural score over a local
    expression item. It does NOT model language.
    """
    if not isinstance(item, ExpressionItem):
        raise TypeError(
            "predict_readability expects ExpressionItem "
            f"(got {type(item).__name__})"
        )
    features = extract_features(item)
    if features.whitespace_only or features.token_count == 0:
        value = Fraction(0)
    else:
        capped_tokens = features.token_count
        if capped_tokens > LENGTH_SATURATION_BOUND:
            capped_tokens = LENGTH_SATURATION_BOUND
        length_component = Fraction(capped_tokens, LENGTH_SATURATION_BOUND)
        distinct_component = Fraction(
            features.distinct_token_count, features.token_count
        )
        if features.char_count > 0:
            shape_component = Fraction(
                features.printable_non_space_count, features.char_count
            )
        else:
            shape_component = Fraction(0)
        if features.token_count > 1:
            run_excess = features.max_run_length - 1
            if run_excess < 0:
                run_excess = 0
            repeat_penalty = Fraction(run_excess, features.token_count)
        else:
            repeat_penalty = Fraction(0)
        positive = (
            W_PRINTABLE * shape_component
            + W_SHAPE * length_component
            + W_DISTINCT * distinct_component
        )
        value = positive - W_REPEAT * repeat_penalty
        if value < Fraction(0):
            value = Fraction(0)
        if value > Fraction(1):
            value = Fraction(1)
    return ReadabilityPrediction(
        item_id=item.item_id,
        source=item.source,
        predictor_id=PREDICTOR_ID,
        score=ReadabilityScore(value=value),
    )


@dataclass(frozen=True, slots=True)
class ExpressionRecord:
    """Local record bundling an item, its features, and its prediction."""

    item: ExpressionItem
    features: ExpressionFeatureVector
    prediction: ReadabilityPrediction

    def __post_init__(self) -> None:
        if not isinstance(self.item, ExpressionItem):
            raise TypeError("ExpressionRecord.item must be ExpressionItem")
        if not isinstance(self.features, ExpressionFeatureVector):
            raise TypeError(
                "ExpressionRecord.features must be ExpressionFeatureVector"
            )
        if not isinstance(self.prediction, ReadabilityPrediction):
            raise TypeError(
                "ExpressionRecord.prediction must be ReadabilityPrediction"
            )
        if self.prediction.item_id != self.item.item_id:
            raise ValueError(
                "ExpressionRecord.prediction.item_id must match item.item_id"
            )
        if self.prediction.source is not self.item.source:
            raise ValueError(
                "ExpressionRecord.prediction.source must match item.source"
            )


def make_expression_record(item: ExpressionItem) -> ExpressionRecord:
    features = extract_features(item)
    prediction = predict_readability(item)
    return ExpressionRecord(item=item, features=features, prediction=prediction)


@dataclass(frozen=True, slots=True)
class ExpressionHistory:
    """Copy-on-write bounded local history of expression records (I-EXP-06)."""

    records: tuple[ExpressionRecord, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.records, tuple):
            raise TypeError("ExpressionHistory.records must be a tuple")
        for r in self.records:
            if not isinstance(r, ExpressionRecord):
                raise TypeError(
                    "ExpressionHistory.records must contain ExpressionRecord values "
                    f"(got {type(r).__name__})"
                )
        if len(self.records) > EXPRESSION_HISTORY_MAX_ENTRIES:
            raise ValueError(
                "I-EXP-06 violated: ExpressionHistory.records exceeds "
                f"EXPRESSION_HISTORY_MAX_ENTRIES={EXPRESSION_HISTORY_MAX_ENTRIES}"
            )

    def append(self, record: ExpressionRecord) -> "ExpressionHistory":
        if not isinstance(record, ExpressionRecord):
            raise TypeError(
                "ExpressionHistory.append expects ExpressionRecord "
                f"(got {type(record).__name__})"
            )
        records = self.records + (record,)
        if len(records) > EXPRESSION_HISTORY_MAX_ENTRIES:
            records = records[-EXPRESSION_HISTORY_MAX_ENTRIES:]
        return ExpressionHistory(records=records)


# ---------------------------------------------------------------------------
# Bridge constructors (one-way, pure, no callbacks).
#
# Each accepts a duck-typed source record and returns an ExpressionRecord.
# They do not mutate the source object or any source-history container.
# ---------------------------------------------------------------------------


def expression_record_from_output_entry(impulse: object) -> ExpressionRecord:
    """Build an `ExpressionRecord` from an `OutputImpulse`-like object."""
    impulse_id = getattr(impulse, "impulse_id", None)
    text = getattr(impulse, "text", None)
    if not isinstance(impulse_id, str) or not isinstance(text, str):
        raise TypeError(
            "expression_record_from_output_entry requires impulse_id/text strings"
        )
    item = ExpressionItem(
        item_id=f"output:{impulse_id}",
        text=text,
        source=ExpressionSource.OUTPUT_HISTORY,
    )
    return make_expression_record(item)


def expression_record_from_worldlet_response(response: object) -> ExpressionRecord:
    """Build an `ExpressionRecord` from a `WorldletResponse`-like object."""
    response_id = getattr(response, "response_id", None)
    reason = getattr(response, "reason", None)
    if not isinstance(response_id, str) or not isinstance(reason, str):
        raise TypeError(
            "expression_record_from_worldlet_response requires "
            "response_id/reason strings"
        )
    item = ExpressionItem(
        item_id=f"worldlet:{response_id}",
        text=reason,
        source=ExpressionSource.WORLDLET_HISTORY,
    )
    return make_expression_record(item)


def expression_record_from_proto_basic_line(line: object) -> ExpressionRecord:
    """Build an `ExpressionRecord` from a `ProtoBasicLine`-like object."""
    line_id = getattr(line, "line_id", None)
    raw_text = getattr(line, "raw_text", None)
    if not isinstance(line_id, str) or not isinstance(raw_text, str):
        raise TypeError(
            "expression_record_from_proto_basic_line requires "
            "line_id/raw_text strings"
        )
    item = ExpressionItem(
        item_id=f"repl:{line_id}",
        text=raw_text,
        source=ExpressionSource.PROTO_BASIC_HISTORY,
    )
    return make_expression_record(item)


def expression_record_from_transcript_entry(entry: object) -> ExpressionRecord:
    """Build an `ExpressionRecord` from a `TranscriptEntry`-like object."""
    text = getattr(entry, "text", None)
    tick_at_event = getattr(entry, "tick_at_event", None)
    if not isinstance(text, str) or not isinstance(tick_at_event, int):
        raise TypeError(
            "expression_record_from_transcript_entry requires "
            "text/tick_at_event"
        )
    item = ExpressionItem(
        item_id=f"transcript:tick{tick_at_event}",
        text=text,
        source=ExpressionSource.OPERATOR_TRANSCRIPT,
    )
    return make_expression_record(item)


# ---------------------------------------------------------------------------
# Aggregate summary view (I-EXP-17 OBSERVED).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExpressionHistorySummary:
    count: int
    counts_by_source: Mapping[ExpressionSource, int]
    score_min: Fraction
    score_max: Fraction
    score_mean: Fraction


def summarize_expression_history(
    history: ExpressionHistory,
) -> ExpressionHistorySummary:
    if not isinstance(history, ExpressionHistory):
        raise TypeError(
            "summarize_expression_history expects ExpressionHistory "
            f"(got {type(history).__name__})"
        )
    counts: dict[ExpressionSource, int] = {s: 0 for s in ExpressionSource}
    if not history.records:
        return ExpressionHistorySummary(
            count=0,
            counts_by_source=MappingProxyType(counts),
            score_min=Fraction(0),
            score_max=Fraction(0),
            score_mean=Fraction(0),
        )
    score_values: list[Fraction] = []
    for record in history.records:
        counts[record.item.source] = counts.get(record.item.source, 0) + 1
        score_values.append(record.prediction.score.value)
    s_min = min(score_values)
    s_max = max(score_values)
    s_sum = sum(score_values, Fraction(0))
    s_mean = s_sum / Fraction(len(score_values))
    return ExpressionHistorySummary(
        count=len(history.records),
        counts_by_source=MappingProxyType(counts),
        score_min=s_min,
        score_max=s_max,
        score_mean=s_mean,
    )
