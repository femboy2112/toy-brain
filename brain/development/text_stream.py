"""Phase 3.7 Text Stream Ingress primitives.

A bounded local substrate over operator / system / probe-echo / generated
raw text. The substrate exposes frozen records and pure constructors:
``TextStreamChunk`` (bounded printable text with `COGITO_ID` rejected on
identifiers and on text), ``TextStreamHistory`` (copy-on-write bounded ring
that drops the oldest chunk on full append), and ``StreamFeatureVector``
(deterministic exact `int` / `Fraction` counts).

Phase 3.7 also exposes a structural-only ``SegmentCandidate`` (closed
vocabulary span), a recurrence-backed ``StreamPattern`` carrying no truth /
``PRESERVE`` / agency field, and a ``StreamPromotionCandidate`` that is not a
``PerceptEvent``. None of these construct a ``PerceptEvent``, call
``tick()``, append to ``OperatorSession.event_queue``, mutate ``BrainState``
/ MSI / PtCns / ``ContentRegistry``, or mutate any existing source history.

The module is deliberately closed: no I/O, network, file, shell, TLICA,
tick, LLM, or UI import; no module-level side effect; no callback
registration; no ``float`` / ``round`` / ``math`` on the count / statistic
path. The text stream substrate surfaces bounded raw text evidence; it
does NOT produce parse trees, language meaning, truth claims, ``PRESERVE``
/ ``DAMAGE`` judgments, agency witnesses, or aggregate quality scores.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Optional

from brain.development.history import require_printable_id

# Reserved cogito sentinel value. Duplicated locally so that text_stream.py
# satisfies I-STRM-12 (no brain.tlica import). The fixture
# ``text_stream_chunk_bounded.py`` verifies that this constant equals
# ``brain.tlica.profile.COGITO_ID`` at import time, so a kernel-side rename
# fails the runner instead of silently diverging.
_COGITO_RESERVED_ID: str = "__cogito__"

# Bounded local discipline (corrigenda-locked ranges in
# PHASE3_7_TEXT_STREAM_INGRESS_CATALOG_PATCH_PLAN.md section 11).
STREAM_TEXT_MAX_LEN: int = 1024
STREAM_PROVENANCE_MAX_LEN: int = 64
STREAM_HISTORY_MAX_CHUNKS: int = 256
STREAM_SEGMENTS_MAX: int = 32
STREAM_PATTERN_RECURRENCE_MIN: int = 2
STREAM_PATTERN_RECURRENCE_MAX: int = 256
STREAM_PATTERN_SIG_MAX: int = 16
STREAM_PROMOTION_MAX: int = 64
ALLOWED_SEGMENT_KINDS: tuple[str, ...] = ("line", "delimited_span", "whitespace_run")

# Whitespace characters allowed inside chunk text in addition to Python's
# ``str.isprintable()`` true-positives. Newlines and horizontal tabs are
# meaningful raw-text separators (drive line/whitespace-run features) and
# are not security-sensitive.
_ALLOWED_TEXT_WHITESPACE: frozenset[str] = frozenset({"\n", "\t"})


def _text_is_acceptable(text: str) -> bool:
    """Return True when ``text`` is bounded raw chunk text content.

    Allows Python printable characters plus ``\\n`` and ``\\t`` (which are
    technically non-printable per ``str.isprintable()`` but are valid raw
    text separators). Rejects every other control character.
    """
    for ch in text:
        if ch in _ALLOWED_TEXT_WHITESPACE:
            continue
        if not ch.isprintable():
            return False
    return True


class TextStreamSource(Enum):
    """Finite closed enumeration of text-stream source kinds (I-STRM-01)."""

    OPERATOR = "operator"
    SYSTEM = "system"
    PROBE_ECHO = "probe_echo"
    GENERATED = "generated"


def _require_int_nonneg(value: object, *, field: str, row_id: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(
            f"{row_id} violated: {field} must be int "
            f"(got {type(value).__name__})"
        )
    if value < 0:
        raise ValueError(f"{row_id} violated: {field} must be >= 0 (got {value})")
    return value


def _require_bounded_printable(
    value: object,
    *,
    field: str,
    row_id: str,
    max_len: int,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str):
        raise ValueError(
            f"{row_id} violated: {field} must be str "
            f"(got {type(value).__name__})"
        )
    if not value and not allow_empty:
        raise ValueError(f"{row_id} violated: {field} must be non-empty")
    if not value.isprintable() and value != "":
        raise ValueError(f"{row_id} violated: {field} must be printable")
    if len(value) > max_len:
        raise ValueError(
            f"{row_id} violated: {field} length {len(value)} exceeds max {max_len}"
        )
    if value == _COGITO_RESERVED_ID:
        raise ValueError(
            f"{row_id} violated: {field} cannot equal COGITO_ID"
        )
    return value


@dataclass(frozen=True, slots=True)
class TextStreamChunk:
    """Bounded printable raw-text chunk (I-STRM-02, I-STRM-13).

    Construction requires a printable text within ``STREAM_TEXT_MAX_LEN``,
    a printable ``chunk_id`` distinct from ``COGITO_ID``, a known
    ``TextStreamSource``, and a printable bounded ``provenance``. The chunk
    holds no callable, file handle, socket, LLM client, or path object.
    """

    chunk_id: str
    text: str
    source: TextStreamSource
    provenance: str

    def __post_init__(self) -> None:
        if not isinstance(self.source, TextStreamSource):
            raise ValueError(
                "I-STRM-02 violated: TextStreamChunk.source must be a "
                f"TextStreamSource (got {type(self.source).__name__})"
            )
        try:
            require_printable_id(self.chunk_id, field="TextStreamChunk.chunk_id")
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-STRM-02 violated: TextStreamChunk.chunk_id must be "
                "non-empty and printable"
            ) from exc
        if len(self.chunk_id) > STREAM_PROVENANCE_MAX_LEN:
            raise ValueError(
                "I-STRM-02 violated: chunk_id length "
                f"{len(self.chunk_id)} exceeds STREAM_PROVENANCE_MAX_LEN="
                f"{STREAM_PROVENANCE_MAX_LEN}"
            )
        if self.chunk_id == _COGITO_RESERVED_ID:
            raise ValueError(
                "I-STRM-02 violated: chunk_id cannot equal COGITO_ID"
            )

        if not isinstance(self.text, str):
            raise ValueError(
                "I-STRM-02 violated: TextStreamChunk.text must be str "
                f"(got {type(self.text).__name__})"
            )
        if not self.text:
            raise ValueError("I-STRM-02 violated: TextStreamChunk.text must be non-empty")
        if not _text_is_acceptable(self.text):
            raise ValueError("I-STRM-02 violated: TextStreamChunk.text must be printable")
        if len(self.text) > STREAM_TEXT_MAX_LEN:
            raise ValueError(
                "I-STRM-11 violated: TextStreamChunk.text length "
                f"{len(self.text)} exceeds STREAM_TEXT_MAX_LEN="
                f"{STREAM_TEXT_MAX_LEN}; no silent truncation"
            )
        if self.text == _COGITO_RESERVED_ID:
            raise ValueError(
                "I-STRM-02 violated: TextStreamChunk.text cannot equal COGITO_ID"
            )

        _require_bounded_printable(
            self.provenance,
            field="TextStreamChunk.provenance",
            row_id="I-STRM-02",
            max_len=STREAM_PROVENANCE_MAX_LEN,
        )


@dataclass(frozen=True, slots=True)
class TextStreamHistory:
    """Copy-on-write bounded ring of `TextStreamChunk` (I-STRM-03, I-STRM-13).

    ``append(chunk)`` returns a new history with prior chunks preserved
    exactly and the new chunk appended; when ``len(chunks) >=
    STREAM_HISTORY_MAX_CHUNKS`` the oldest chunk is dropped before append.
    """

    chunks: tuple[TextStreamChunk, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.chunks, tuple):
            raise ValueError(
                "I-STRM-03 violated: TextStreamHistory.chunks must be a tuple "
                f"(got {type(self.chunks).__name__})"
            )
        for chunk in self.chunks:
            if not isinstance(chunk, TextStreamChunk):
                raise ValueError(
                    "I-STRM-03 violated: TextStreamHistory.chunks must contain "
                    f"TextStreamChunk values (got {type(chunk).__name__})"
                )
        if len(self.chunks) > STREAM_HISTORY_MAX_CHUNKS:
            raise ValueError(
                f"I-STRM-03 violated: TextStreamHistory has {len(self.chunks)} "
                f"chunks; max is STREAM_HISTORY_MAX_CHUNKS="
                f"{STREAM_HISTORY_MAX_CHUNKS}"
            )

    def append(self, chunk: TextStreamChunk) -> "TextStreamHistory":
        if not isinstance(chunk, TextStreamChunk):
            raise TypeError(
                "TextStreamHistory.append expects TextStreamChunk "
                f"(got {type(chunk).__name__})"
            )
        if len(self.chunks) >= STREAM_HISTORY_MAX_CHUNKS:
            kept = self.chunks[1:]
        else:
            kept = self.chunks
        return TextStreamHistory(chunks=kept + (chunk,))


@dataclass(frozen=True, slots=True)
class StreamFeatureVector:
    """Deterministic exact feature vector for one chunk (I-STRM-04, I-STRM-13).

    Every field is an exact ``int`` count or a ``Fraction`` ratio. No
    ``float`` arithmetic, no ``round``, no ``math.*``, and no
    nondeterministic data source participates in extraction.
    """

    chunk_id: str
    text_length: int
    printable_length: int
    line_count: int
    whitespace_run_count: int
    distinct_char_count: int
    repeat_ratio: Fraction

    def __post_init__(self) -> None:
        try:
            require_printable_id(self.chunk_id, field="StreamFeatureVector.chunk_id")
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-STRM-04 violated: StreamFeatureVector.chunk_id must be "
                "non-empty and printable"
            ) from exc
        for field_name, value in (
            ("text_length", self.text_length),
            ("printable_length", self.printable_length),
            ("line_count", self.line_count),
            ("whitespace_run_count", self.whitespace_run_count),
            ("distinct_char_count", self.distinct_char_count),
        ):
            _require_int_nonneg(
                value,
                field=f"StreamFeatureVector.{field_name}",
                row_id="I-STRM-04",
            )
        if not isinstance(self.repeat_ratio, Fraction):
            raise ValueError(
                "I-STRM-04 violated: repeat_ratio must be Fraction "
                f"(got {type(self.repeat_ratio).__name__})"
            )
        if self.repeat_ratio < 0 or self.repeat_ratio > 1:
            raise ValueError(
                "I-STRM-04 violated: repeat_ratio must lie in [0, 1] "
                f"(got {self.repeat_ratio})"
            )


def make_text_stream_chunk(
    *,
    chunk_id: str,
    text: str,
    source: TextStreamSource,
    provenance: str,
) -> TextStreamChunk:
    """Pure constructor for `TextStreamChunk` (I-STRM-02)."""
    return TextStreamChunk(
        chunk_id=chunk_id,
        text=text,
        source=source,
        provenance=provenance,
    )


def extract_stream_features(chunk: TextStreamChunk) -> StreamFeatureVector:
    """Exact deterministic feature extraction (I-STRM-04).

    Uses only ``int`` and ``Fraction`` arithmetic: counts characters, lines,
    whitespace runs, and distinct characters; computes the repeat ratio as
    ``Fraction(text_length - distinct_char_count, text_length)`` (or 0 when
    text is empty, which cannot occur because chunks are non-empty).
    """
    if not isinstance(chunk, TextStreamChunk):
        raise TypeError(
            f"extract_stream_features expects TextStreamChunk (got {type(chunk).__name__})"
        )
    text = chunk.text
    text_length = len(text)
    printable_length = 0
    for ch in text:
        if ch.isprintable():
            printable_length += 1
    line_count = 1
    for ch in text:
        if ch == "\n":
            line_count += 1
    whitespace_run_count = 0
    in_run = False
    for ch in text:
        if ch.isspace():
            if not in_run:
                whitespace_run_count += 1
                in_run = True
        else:
            in_run = False
    distinct: set[str] = set()
    for ch in text:
        distinct.add(ch)
    distinct_char_count = len(distinct)
    if text_length == 0:
        repeat_ratio = Fraction(0)
    else:
        repeat_ratio = Fraction(text_length - distinct_char_count, text_length)
    return StreamFeatureVector(
        chunk_id=chunk.chunk_id,
        text_length=text_length,
        printable_length=printable_length,
        line_count=line_count,
        whitespace_run_count=whitespace_run_count,
        distinct_char_count=distinct_char_count,
        repeat_ratio=repeat_ratio,
    )


@dataclass(frozen=True, slots=True)
class SegmentCandidate:
    """Structural (start, end, segment_kind) span (I-STRM-05, I-STRM-13).

    Carries no payload text, parse tree, AST, semantic value, language
    label, truth flag, or readability score. ``segment_kind`` must be one
    of ``ALLOWED_SEGMENT_KINDS``.
    """

    candidate_id: str
    chunk_id: str
    start: int
    end: int
    segment_kind: str

    def __post_init__(self) -> None:
        try:
            require_printable_id(self.candidate_id, field="SegmentCandidate.candidate_id")
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-STRM-05 violated: candidate_id must be non-empty and printable"
            ) from exc
        if len(self.candidate_id) > STREAM_PROVENANCE_MAX_LEN:
            raise ValueError(
                "I-STRM-05 violated: candidate_id length "
                f"{len(self.candidate_id)} exceeds STREAM_PROVENANCE_MAX_LEN="
                f"{STREAM_PROVENANCE_MAX_LEN}"
            )
        try:
            require_printable_id(self.chunk_id, field="SegmentCandidate.chunk_id")
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-STRM-05 violated: chunk_id must be non-empty and printable"
            ) from exc
        _require_int_nonneg(self.start, field="SegmentCandidate.start", row_id="I-STRM-05")
        _require_int_nonneg(self.end, field="SegmentCandidate.end", row_id="I-STRM-05")
        if self.end < self.start:
            raise ValueError(
                "I-STRM-05 violated: SegmentCandidate.end "
                f"({self.end}) must be >= start ({self.start})"
            )
        if self.segment_kind not in ALLOWED_SEGMENT_KINDS:
            raise ValueError(
                "I-STRM-05 violated: segment_kind "
                f"{self.segment_kind!r} not in {ALLOWED_SEGMENT_KINDS}"
            )


def extract_segment_candidates(
    chunk: TextStreamChunk,
) -> tuple[SegmentCandidate, ...]:
    """Deterministic structural segmentation (I-STRM-05).

    Emits at most ``STREAM_SEGMENTS_MAX`` ``line`` segments. The vocabulary
    ``("line", "delimited_span", "whitespace_run")`` is closed; this
    implementation surfaces ``line`` segments split on newline characters.
    """
    if not isinstance(chunk, TextStreamChunk):
        raise TypeError(
            f"extract_segment_candidates expects TextStreamChunk (got {type(chunk).__name__})"
        )
    text = chunk.text
    out: list[SegmentCandidate] = []
    cursor = 0
    index = 0
    for ch in text:
        if ch == "\n":
            if len(out) >= STREAM_SEGMENTS_MAX:
                break
            out.append(
                SegmentCandidate(
                    candidate_id=f"seg:{chunk.chunk_id}:{len(out)}",
                    chunk_id=chunk.chunk_id,
                    start=cursor,
                    end=index,
                    segment_kind="line",
                )
            )
            cursor = index + 1
        index += 1
    if len(out) < STREAM_SEGMENTS_MAX:
        out.append(
            SegmentCandidate(
                candidate_id=f"seg:{chunk.chunk_id}:{len(out)}",
                chunk_id=chunk.chunk_id,
                start=cursor,
                end=len(text),
                segment_kind="line",
            )
        )
    return tuple(out)


@dataclass(frozen=True, slots=True)
class StreamPattern:
    """Recurrence-backed structural pattern (I-STRM-06, I-STRM-13).

    StreamPattern is recurrence-backed structural evidence. It does NOT
    enter PtCns.evaluate, does NOT contribute to MSI.contents, and does
    NOT carry PRESERVE / DAMAGE / PCE / ProjectedPCE / Act / ModeOp /
    AgencyWitness fields.
    """

    pattern_id: str
    signature: tuple[str, ...]
    recurrence_count: int

    def __post_init__(self) -> None:
        try:
            require_printable_id(self.pattern_id, field="StreamPattern.pattern_id")
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-STRM-06 violated: pattern_id must be non-empty and printable"
            ) from exc
        if len(self.pattern_id) > STREAM_PROVENANCE_MAX_LEN:
            raise ValueError(
                "I-STRM-06 violated: pattern_id length "
                f"{len(self.pattern_id)} exceeds STREAM_PROVENANCE_MAX_LEN="
                f"{STREAM_PROVENANCE_MAX_LEN}"
            )
        if self.pattern_id == _COGITO_RESERVED_ID:
            raise ValueError(
                "I-STRM-06 violated: pattern_id cannot equal COGITO_ID"
            )
        if not isinstance(self.signature, tuple):
            raise ValueError(
                "I-STRM-06 violated: signature must be a tuple "
                f"(got {type(self.signature).__name__})"
            )
        if not self.signature:
            raise ValueError(
                "I-STRM-06 violated: signature must be non-empty"
            )
        if len(self.signature) > STREAM_PATTERN_SIG_MAX:
            raise ValueError(
                "I-STRM-06 violated: signature length "
                f"{len(self.signature)} exceeds STREAM_PATTERN_SIG_MAX="
                f"{STREAM_PATTERN_SIG_MAX}"
            )
        for item in self.signature:
            if not isinstance(item, str) or not item or not item.isprintable():
                raise ValueError(
                    "I-STRM-06 violated: signature entries must be bounded "
                    f"non-empty printable strings (got {item!r})"
                )
            if len(item) > STREAM_PROVENANCE_MAX_LEN:
                raise ValueError(
                    "I-STRM-06 violated: signature entry length "
                    f"{len(item)} exceeds STREAM_PROVENANCE_MAX_LEN="
                    f"{STREAM_PROVENANCE_MAX_LEN}"
                )
        _require_int_nonneg(
            self.recurrence_count,
            field="StreamPattern.recurrence_count",
            row_id="I-STRM-06",
        )
        if self.recurrence_count < STREAM_PATTERN_RECURRENCE_MIN:
            raise ValueError(
                "I-STRM-06 violated: recurrence_count "
                f"{self.recurrence_count} below STREAM_PATTERN_RECURRENCE_MIN="
                f"{STREAM_PATTERN_RECURRENCE_MIN}"
            )
        if self.recurrence_count > STREAM_PATTERN_RECURRENCE_MAX:
            raise ValueError(
                "I-STRM-06 violated: recurrence_count "
                f"{self.recurrence_count} exceeds STREAM_PATTERN_RECURRENCE_MAX="
                f"{STREAM_PATTERN_RECURRENCE_MAX}"
            )


def make_stream_pattern(
    *,
    pattern_id: str,
    signature: tuple[str, ...],
    recurrence_count: int,
) -> StreamPattern:
    """Pure constructor; saturates ``recurrence_count`` at the configured max."""
    if isinstance(recurrence_count, int) and not isinstance(recurrence_count, bool):
        if recurrence_count > STREAM_PATTERN_RECURRENCE_MAX:
            recurrence_count = STREAM_PATTERN_RECURRENCE_MAX
    return StreamPattern(
        pattern_id=pattern_id,
        signature=signature,
        recurrence_count=recurrence_count,
    )


@dataclass(frozen=True, slots=True)
class StreamPromotionCandidate:
    """Explicit promotion candidate (I-STRM-07, I-STRM-13).

    StreamPromotionCandidate is not a PerceptEvent. The substrate never
    appends candidates to OperatorSession.event_queue and never calls
    tick(). The Phase 3.8 /stream-promote route owns event-queue append.
    """

    candidate_id: str
    target_content_id: str
    source: TextStreamSource
    chunk_id: str
    text: str
    provenance: str
    pattern_id: Optional[str] = None

    def __post_init__(self) -> None:
        try:
            require_printable_id(
                self.candidate_id, field="StreamPromotionCandidate.candidate_id"
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-STRM-07 violated: candidate_id must be non-empty and printable"
            ) from exc
        if len(self.candidate_id) > STREAM_PROVENANCE_MAX_LEN:
            raise ValueError(
                "I-STRM-07 violated: candidate_id length "
                f"{len(self.candidate_id)} exceeds STREAM_PROVENANCE_MAX_LEN="
                f"{STREAM_PROVENANCE_MAX_LEN}"
            )
        try:
            require_printable_id(
                self.target_content_id,
                field="StreamPromotionCandidate.target_content_id",
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-STRM-07 violated: target_content_id must be non-empty "
                "and printable"
            ) from exc
        if self.target_content_id == _COGITO_RESERVED_ID:
            raise ValueError(
                "I-STRM-07 violated: target_content_id cannot equal COGITO_ID"
            )
        if len(self.target_content_id) > STREAM_PROVENANCE_MAX_LEN:
            raise ValueError(
                "I-STRM-07 violated: target_content_id length "
                f"{len(self.target_content_id)} exceeds STREAM_PROVENANCE_MAX_LEN="
                f"{STREAM_PROVENANCE_MAX_LEN}"
            )
        if not isinstance(self.source, TextStreamSource):
            raise ValueError(
                "I-STRM-07 violated: source must be a TextStreamSource "
                f"(got {type(self.source).__name__})"
            )
        try:
            require_printable_id(
                self.chunk_id, field="StreamPromotionCandidate.chunk_id"
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-STRM-07 violated: chunk_id must be non-empty and printable"
            ) from exc
        if not isinstance(self.text, str):
            raise ValueError(
                "I-STRM-07 violated: text must be str "
                f"(got {type(self.text).__name__})"
            )
        if not self.text:
            raise ValueError(
                "I-STRM-07 violated: text must be non-empty"
            )
        if len(self.text) > STREAM_TEXT_MAX_LEN:
            raise ValueError(
                "I-STRM-07 violated: text length "
                f"{len(self.text)} exceeds STREAM_TEXT_MAX_LEN="
                f"{STREAM_TEXT_MAX_LEN}"
            )
        if not _text_is_acceptable(self.text):
            raise ValueError(
                "I-STRM-07 violated: text must be printable"
            )
        if self.text == _COGITO_RESERVED_ID:
            raise ValueError(
                "I-STRM-07 violated: text cannot equal COGITO_ID"
            )
        _require_bounded_printable(
            self.provenance,
            field="StreamPromotionCandidate.provenance",
            row_id="I-STRM-07",
            max_len=STREAM_PROVENANCE_MAX_LEN,
        )
        if self.pattern_id is not None:
            try:
                require_printable_id(
                    self.pattern_id,
                    field="StreamPromotionCandidate.pattern_id",
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "I-STRM-07 violated: pattern_id, when present, must be "
                    "non-empty and printable"
                ) from exc
            if len(self.pattern_id) > STREAM_PROVENANCE_MAX_LEN:
                raise ValueError(
                    "I-STRM-07 violated: pattern_id length "
                    f"{len(self.pattern_id)} exceeds STREAM_PROVENANCE_MAX_LEN="
                    f"{STREAM_PROVENANCE_MAX_LEN}"
                )


def make_stream_promotion_candidate(
    *,
    candidate_id: str,
    target_content_id: str,
    source: TextStreamSource,
    chunk_id: str,
    text: str,
    provenance: str,
    pattern_id: Optional[str] = None,
) -> StreamPromotionCandidate:
    """Pure constructor for `StreamPromotionCandidate` (I-STRM-07)."""
    return StreamPromotionCandidate(
        candidate_id=candidate_id,
        target_content_id=target_content_id,
        source=source,
        chunk_id=chunk_id,
        text=text,
        provenance=provenance,
        pattern_id=pattern_id,
    )
