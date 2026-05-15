"""Proto-BASIC REPL primitives for Phase 3.4.

This module is a deliberately constrained local output-worldlet interface. It
teaches deterministic syntax, near-miss correction, and bounded consequence
feedback without:

  * running a real BASIC interpreter,
  * invoking host execution, subprocesses, shells, file I/O, or networks,
  * calling ``tick()`` or emitting ``PerceptEvent`` values,
  * mutating profile, MSI, PtCns, content registry, scenario, or trace state,
  * introducing language understanding, social register, expression layer,
    readability scoring, or Mode B reflective agency.

The Phase 3.4 catalog ties the public surface here to the ``I-REPL-*`` rows.
Step 7 of the campaign covers I-REPL-01..10 and I-REPL-17 (grammar/parser/
feedback boundary). Step 8 will add command construction/execution/history
(I-REPL-11..14, I-REPL-16). Step 9 will tighten diminishing-returns and
aggregate inspection (I-REPL-15, I-REPL-18).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from types import MappingProxyType
from typing import Mapping

from brain.development.drives import require_unit_fraction
from brain.development.history import TraceEventID, require_printable_id
from brain.development.stream import FrameSourceKind
from brain.tlica.profile import COGITO_ID

# ---------------------------------------------------------------------------
# Identifier and bound declarations.
#
# The Proto-BASIC grammar is intentionally tiny. Every bound is a small fixed
# integer so the parser, the near-miss search, and the history layer are all
# total over a finite, enumerable input domain.
# ---------------------------------------------------------------------------

ProtoBasicTokenID = str
ProtoBasicLineID = str

# Maximum printable length of a raw line. Keeps tokenize total over any
# reasonable user-supplied string and prevents unbounded parser work.
PROTO_BASIC_MAX_LINE_LENGTH: int = 80

# Maximum number of tokens permitted on a single line. The grammar uses only
# verb-target or verb-target-object forms, so 4 tokens is generous.
PROTO_BASIC_MAX_LINE_TOKENS: int = 4

# Maximum printable length of an individual token's canonical text.
PROTO_BASIC_MAX_TOKEN_LENGTH: int = 16

# Bounded edit distance for near-miss correction hints. The hint generator only
# proposes a single bounded edit; this constant is the cap.
PROTO_BASIC_MAX_EDIT_DISTANCE: int = 1

# Threshold separating weak/zero feedback from strong positive feedback.
# I-REPL-09 / I-REPL-10 are stated in terms of this exact bound.
PROTO_BASIC_STRONG_POSITIVE_THRESHOLD: Fraction = Fraction(1, 10)


class ProtoBasicTokenKind(str, Enum):
    """Finite enumeration of token kinds in the Proto-BASIC grammar.

    Kinds are intentionally generic ("VERB", "TARGET", "OBJECT") so the
    grammar can be enumerated at build time. There is no dynamic registration
    after grammar construction (I-REPL-01).
    """

    VERB = "verb"
    TARGET = "target"
    OBJECT = "object"


class ProtoBasicParseCategory(str, Enum):
    """Parse outcome partition (I-REPL-04).

    Every ``ProtoBasicLine`` resolves to exactly one of these categories.
    """

    VALID = "valid"
    NEAR_MISS = "near-miss"
    SYNTAX_INVALID = "syntax-invalid"
    SEMANTIC_INVALID = "semantic-invalid"
    TOOL_UNAVAILABLE = "tool-unavailable"
    RESOURCE_LIMIT = "resource-limit"
    SANDBOX_FAULT = "sandbox-fault"


PARSE_CATEGORIES: frozenset[ProtoBasicParseCategory] = frozenset(
    ProtoBasicParseCategory
)


class ProtoBasicExecutionCategory(str, Enum):
    """Execution outcome partition (I-REPL-13).

    Execution does not call into hosts; it merely classifies a constructed
    command into a bounded local result. ``valid-effective`` is the only
    category that earns strong positive feedback (I-REPL-10).
    """

    VALID_EFFECTIVE = "valid-effective"
    VALID_INEFFECTIVE = "valid-ineffective"
    TOOL_UNAVAILABLE = "tool-unavailable"
    RESOURCE_LIMIT = "resource-limit"
    SANDBOX_FAULT = "sandbox-fault"


EXECUTION_CATEGORIES: frozenset[ProtoBasicExecutionCategory] = frozenset(
    ProtoBasicExecutionCategory
)


class ProtoBasicEditKind(str, Enum):
    """Permitted near-miss edit operations (I-REPL-05)."""

    SUBSTITUTE_TOKEN = "SUBSTITUTE_TOKEN"
    INSERT_TOKEN = "INSERT_TOKEN"
    DELETE_TOKEN = "DELETE_TOKEN"
    CASE_FOLD = "CASE_FOLD"


_EDIT_KINDS: frozenset[ProtoBasicEditKind] = frozenset(ProtoBasicEditKind)


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _require_non_reserved_id(value: str, *, field: str, row_id: str) -> str:
    require_printable_id(value, field=field)
    if value == COGITO_ID:
        raise ValueError(f"{row_id} violated: {field} cannot be COGITO_ID")
    return value


def _require_printable_text(
    value: str, *, field: str, row_id: str, max_length: int
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{row_id} violated: {field} must be a string "
            f"(got {type(value).__name__})"
        )
    if not value or not value.strip() or not value.isprintable():
        raise ValueError(
            f"{row_id} violated: {field} must be non-empty and printable"
        )
    if len(value) > max_length:
        raise ValueError(
            f"{row_id} violated: {field} exceeds max length {max_length}"
        )
    return value


def require_proto_basic_valence(value: Fraction, *, field: str) -> Fraction:
    """Validate an exact bounded Proto-BASIC valence without clamping."""
    if not isinstance(value, Fraction):
        raise TypeError(
            f"{field} must be a Fraction (got {type(value).__name__})"
        )
    if not (Fraction(-1) <= value <= Fraction(1)):
        raise ValueError(f"{field} must be in [-1, 1] (got {value})")
    return value


# ---------------------------------------------------------------------------
# Token / line / grammar.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProtoBasicToken:
    """One enumerated token in the Proto-BASIC grammar (I-REPL-01)."""

    token_id: ProtoBasicTokenID
    kind: ProtoBasicTokenKind
    text: str

    def __post_init__(self) -> None:
        _require_non_reserved_id(
            self.token_id,
            field="ProtoBasicToken.token_id",
            row_id="I-REPL-01",
        )
        if not isinstance(self.kind, ProtoBasicTokenKind):
            raise TypeError(
                "I-REPL-01 violated: ProtoBasicToken.kind must be a "
                "ProtoBasicTokenKind"
            )
        _require_printable_text(
            self.text,
            field="ProtoBasicToken.text",
            row_id="I-REPL-01",
            max_length=PROTO_BASIC_MAX_TOKEN_LENGTH,
        )
        if self.text == COGITO_ID:
            raise ValueError(
                "I-REPL-01 violated: ProtoBasicToken.text cannot be COGITO_ID"
            )
        if any(ch.isspace() for ch in self.text):
            raise ValueError(
                "I-REPL-01 violated: ProtoBasicToken.text must not contain "
                "whitespace"
            )

    @property
    def canonical(self) -> str:
        """Canonical case-folded text used for parser dispatch and dedup."""
        return self.text.casefold()


@dataclass(frozen=True, slots=True)
class ProtoBasicGrammar:
    """Finite enumerated grammar of Proto-BASIC tokens and command shapes.

    The legal token set is fixed at construction time. There is no dynamic
    registration after build (I-REPL-01).
    """

    tokens: tuple[ProtoBasicToken, ...]
    command_shapes: tuple[tuple[ProtoBasicTokenKind, ...], ...]
    max_line_length: int = PROTO_BASIC_MAX_LINE_LENGTH
    max_line_tokens: int = PROTO_BASIC_MAX_LINE_TOKENS
    max_edit_distance: int = PROTO_BASIC_MAX_EDIT_DISTANCE

    def __post_init__(self) -> None:
        if not isinstance(self.tokens, tuple) or not self.tokens:
            raise ValueError(
                "I-REPL-01 violated: ProtoBasicGrammar.tokens must be a "
                "non-empty tuple"
            )
        seen_ids: set[str] = set()
        seen_canonical: set[str] = set()
        for token in self.tokens:
            if not isinstance(token, ProtoBasicToken):
                raise TypeError(
                    "I-REPL-01 violated: ProtoBasicGrammar.tokens must hold "
                    "ProtoBasicToken values"
                )
            if token.token_id in seen_ids:
                raise ValueError(
                    "I-REPL-01 violated: ProtoBasicGrammar tokens must have "
                    "unique token_id"
                )
            seen_ids.add(token.token_id)
            if token.canonical in seen_canonical:
                raise ValueError(
                    "I-REPL-01 violated: ProtoBasicGrammar tokens must have "
                    "unique canonical text"
                )
            seen_canonical.add(token.canonical)

        if (
            not isinstance(self.command_shapes, tuple)
            or not self.command_shapes
        ):
            raise ValueError(
                "I-REPL-01 violated: ProtoBasicGrammar.command_shapes must be "
                "a non-empty tuple"
            )
        for shape in self.command_shapes:
            if not isinstance(shape, tuple) or not shape:
                raise ValueError(
                    "I-REPL-01 violated: command_shape must be a non-empty "
                    "tuple"
                )
            if len(shape) > self.max_line_tokens:
                raise ValueError(
                    "I-REPL-01 violated: command_shape length exceeds "
                    "max_line_tokens"
                )
            for kind in shape:
                if not isinstance(kind, ProtoBasicTokenKind):
                    raise TypeError(
                        "I-REPL-01 violated: command_shape entries must be "
                        "ProtoBasicTokenKind"
                    )

        for field_name, bound in (
            ("max_line_length", self.max_line_length),
            ("max_line_tokens", self.max_line_tokens),
            ("max_edit_distance", self.max_edit_distance),
        ):
            if not isinstance(bound, int) or bound <= 0:
                raise ValueError(
                    f"I-REPL-01 violated: ProtoBasicGrammar.{field_name} must "
                    "be a positive integer"
                )
        if self.max_edit_distance > PROTO_BASIC_MAX_EDIT_DISTANCE:
            raise ValueError(
                "I-REPL-05 violated: max_edit_distance exceeds the declared "
                f"bound {PROTO_BASIC_MAX_EDIT_DISTANCE}"
            )

    def tokens_of_kind(
        self, kind: ProtoBasicTokenKind
    ) -> tuple[ProtoBasicToken, ...]:
        return tuple(t for t in self.tokens if t.kind is kind)

    def token_by_canonical(self, canonical: str) -> ProtoBasicToken | None:
        for token in self.tokens:
            if token.canonical == canonical:
                return token
        return None


@dataclass(frozen=True, slots=True)
class ProtoBasicLine:
    """A single bounded REPL input line (I-REPL-02)."""

    line_id: ProtoBasicLineID
    raw_text: str
    tokens: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_non_reserved_id(
            self.line_id,
            field="ProtoBasicLine.line_id",
            row_id="I-REPL-02",
        )
        if not isinstance(self.raw_text, str):
            raise TypeError(
                "I-REPL-02 violated: ProtoBasicLine.raw_text must be a string"
            )
        # raw_text may legitimately be empty/whitespace-only -- the parser is
        # total over any well-formed string. Cap its size so tokenize is also
        # bounded.
        if not self.raw_text.isprintable() and self.raw_text != "":
            raise ValueError(
                "I-REPL-02 violated: ProtoBasicLine.raw_text must be printable"
            )
        if len(self.raw_text) > PROTO_BASIC_MAX_LINE_LENGTH:
            raise ValueError(
                "I-REPL-02 violated: ProtoBasicLine.raw_text exceeds max "
                f"length {PROTO_BASIC_MAX_LINE_LENGTH}"
            )
        if not isinstance(self.tokens, tuple):
            raise TypeError(
                "I-REPL-02 violated: ProtoBasicLine.tokens must be a tuple"
            )
        if len(self.tokens) > PROTO_BASIC_MAX_LINE_TOKENS:
            raise ValueError(
                "I-REPL-02 violated: ProtoBasicLine.tokens exceeds max count "
                f"{PROTO_BASIC_MAX_LINE_TOKENS}"
            )
        for piece in self.tokens:
            if not isinstance(piece, str):
                raise TypeError(
                    "I-REPL-02 violated: ProtoBasicLine.tokens must hold "
                    "strings"
                )
            if not piece or len(piece) > PROTO_BASIC_MAX_TOKEN_LENGTH:
                raise ValueError(
                    "I-REPL-02 violated: ProtoBasicLine.tokens entries must "
                    "be non-empty and bounded"
                )


def tokenize(raw_text: str, *, line_id: ProtoBasicLineID) -> ProtoBasicLine:
    """Deterministically split ``raw_text`` into bounded tokens (I-REPL-02).

    The tokenizer is total over any well-formed printable string within the
    grammar's length cap. It is intentionally simple: split on whitespace,
    truncate to the token-count cap, and skip tokens that would exceed the
    per-token length cap.
    """
    if not isinstance(raw_text, str):
        raise TypeError(
            "I-REPL-02 violated: tokenize raw_text must be a string"
        )
    if len(raw_text) > PROTO_BASIC_MAX_LINE_LENGTH:
        raise ValueError(
            "I-REPL-02 violated: tokenize raw_text exceeds max length"
        )
    if raw_text and not raw_text.isprintable():
        raise ValueError(
            "I-REPL-02 violated: tokenize raw_text must be printable"
        )
    pieces: list[str] = []
    for piece in raw_text.split():
        if not piece:
            continue
        if len(piece) > PROTO_BASIC_MAX_TOKEN_LENGTH:
            # Truncate at the boundary; downstream parser sees an unknown
            # token and produces a deterministic syntax-invalid result.
            piece = piece[:PROTO_BASIC_MAX_TOKEN_LENGTH]
        pieces.append(piece)
        if len(pieces) >= PROTO_BASIC_MAX_LINE_TOKENS:
            break
    return ProtoBasicLine(
        line_id=line_id,
        raw_text=raw_text,
        tokens=tuple(pieces),
    )


# ---------------------------------------------------------------------------
# Correction hints.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProtoBasicCorrectionHint:
    """A bounded, deterministic near-miss edit hint (I-REPL-05).

    The hint is a single edit operation drawn from a fixed set. It is local
    structured feedback, never natural-language explanation and never produced
    by an external corrector, teacher, or language model.
    """

    edit_kind: ProtoBasicEditKind
    edit_position: int
    expected_token_id: ProtoBasicTokenID | None
    edit_distance: int

    def __post_init__(self) -> None:
        if not isinstance(self.edit_kind, ProtoBasicEditKind):
            raise TypeError(
                "I-REPL-05 violated: correction edit_kind must be a "
                "ProtoBasicEditKind"
            )
        if (
            not isinstance(self.edit_position, int)
            or self.edit_position < 0
            or self.edit_position > PROTO_BASIC_MAX_LINE_TOKENS
        ):
            raise ValueError(
                "I-REPL-05 violated: correction edit_position must be a "
                "non-negative integer within the line's token-count bound"
            )
        if self.expected_token_id is not None:
            _require_non_reserved_id(
                self.expected_token_id,
                field="ProtoBasicCorrectionHint.expected_token_id",
                row_id="I-REPL-05",
            )
        if (
            not isinstance(self.edit_distance, int)
            or self.edit_distance <= 0
            or self.edit_distance > PROTO_BASIC_MAX_EDIT_DISTANCE
        ):
            raise ValueError(
                "I-REPL-05 violated: correction edit_distance must be in "
                f"(0, {PROTO_BASIC_MAX_EDIT_DISTANCE}]"
            )


# ---------------------------------------------------------------------------
# Parse result.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProtoBasicParseResult:
    """The deterministic outcome of parsing one ``ProtoBasicLine`` (I-REPL-03)."""

    line_id: ProtoBasicLineID
    category: ProtoBasicParseCategory
    matched_shape: tuple[ProtoBasicTokenKind, ...] | None = None
    matched_token_ids: tuple[ProtoBasicTokenID, ...] = ()
    correction_hint: ProtoBasicCorrectionHint | None = None
    detail: str = ""

    def __post_init__(self) -> None:
        _require_non_reserved_id(
            self.line_id,
            field="ProtoBasicParseResult.line_id",
            row_id="I-REPL-03",
        )
        if not isinstance(self.category, ProtoBasicParseCategory):
            raise TypeError(
                "I-REPL-04 violated: ProtoBasicParseResult.category must be a "
                "ProtoBasicParseCategory"
            )
        if self.matched_shape is not None:
            if not isinstance(self.matched_shape, tuple):
                raise TypeError(
                    "ProtoBasicParseResult.matched_shape must be a tuple"
                )
            for kind in self.matched_shape:
                if not isinstance(kind, ProtoBasicTokenKind):
                    raise TypeError(
                        "matched_shape entries must be ProtoBasicTokenKind"
                    )
        if not isinstance(self.matched_token_ids, tuple):
            raise TypeError(
                "ProtoBasicParseResult.matched_token_ids must be a tuple"
            )
        for tok_id in self.matched_token_ids:
            _require_non_reserved_id(
                tok_id,
                field="ProtoBasicParseResult.matched_token_id",
                row_id="I-REPL-04",
            )
        if self.category is ProtoBasicParseCategory.NEAR_MISS:
            if not isinstance(self.correction_hint, ProtoBasicCorrectionHint):
                raise ValueError(
                    "I-REPL-05 violated: near-miss parse must carry exactly "
                    "one ProtoBasicCorrectionHint"
                )
        else:
            if self.correction_hint is not None:
                raise ValueError(
                    "I-REPL-05 violated: only near-miss parse results may "
                    "carry a correction_hint"
                )
        if self.category is ProtoBasicParseCategory.VALID:
            if self.matched_shape is None or not self.matched_token_ids:
                raise ValueError(
                    "I-REPL-04 violated: valid parse must record matched "
                    "shape and tokens"
                )
        if not isinstance(self.detail, str):
            raise TypeError(
                "ProtoBasicParseResult.detail must be a string"
            )


def _classify_line(
    grammar: ProtoBasicGrammar,
    line: ProtoBasicLine,
) -> tuple[
    ProtoBasicParseCategory,
    tuple[ProtoBasicTokenKind, ...] | None,
    tuple[ProtoBasicTokenID, ...],
    ProtoBasicCorrectionHint | None,
    str,
]:
    """Pure deterministic classifier returning the partition assignment."""
    pieces = line.tokens
    if not pieces:
        # Empty line: classified as syntax-invalid (no shape to match).
        return (
            ProtoBasicParseCategory.SYNTAX_INVALID,
            None,
            (),
            None,
            "empty-line",
        )

    # Bound-violation cases (covered by ProtoBasicLine, but defensive).
    if len(pieces) > grammar.max_line_tokens:
        return (
            ProtoBasicParseCategory.RESOURCE_LIMIT,
            None,
            (),
            None,
            "token-count-exceeded",
        )

    # Exact lookup against the enumerated grammar, with case-fold awareness.
    exact_matches: list[ProtoBasicToken | None] = []
    case_fold_matches: list[ProtoBasicToken | None] = []
    for piece in pieces:
        canonical = piece.casefold()
        exact = next(
            (t for t in grammar.tokens if t.text == piece),
            None,
        )
        case_fold = grammar.token_by_canonical(canonical)
        exact_matches.append(exact)
        case_fold_matches.append(case_fold)

    # Strict valid: every token matches a known token exactly, and the kinds
    # form one of the enumerated command shapes.
    all_exact = all(t is not None for t in exact_matches)
    if all_exact:
        kinds = tuple(t.kind for t in exact_matches)  # type: ignore[union-attr]
        token_ids = tuple(t.token_id for t in exact_matches)  # type: ignore[union-attr]
        if kinds in grammar.command_shapes:
            return (
                ProtoBasicParseCategory.VALID,
                kinds,
                token_ids,
                None,
                "ok",
            )
        # Insert / delete near-miss before falling back to semantic-invalid:
        # the line's known tokens may form a prefix or extension of a valid
        # shape by exactly one token.
        for shape in grammar.command_shapes:
            if len(shape) == len(pieces) + 1 and tuple(
                t.kind for t in exact_matches  # type: ignore[union-attr]
            ) == shape[: len(pieces)]:
                expected_kind = shape[len(pieces)]
                candidates = grammar.tokens_of_kind(expected_kind)
                if not candidates:
                    continue
                expected_token = candidates[0]
                hint = ProtoBasicCorrectionHint(
                    edit_kind=ProtoBasicEditKind.INSERT_TOKEN,
                    edit_position=len(pieces),
                    expected_token_id=expected_token.token_id,
                    edit_distance=1,
                )
                return (
                    ProtoBasicParseCategory.NEAR_MISS,
                    shape,
                    token_ids + (expected_token.token_id,),
                    hint,
                    "insert-token",
                )
            if (
                len(shape) == len(pieces) - 1
                and len(shape) >= 1
                and tuple(
                    t.kind for t in exact_matches[: len(shape)]  # type: ignore[union-attr]
                )
                == shape
            ):
                hint = ProtoBasicCorrectionHint(
                    edit_kind=ProtoBasicEditKind.DELETE_TOKEN,
                    edit_position=len(shape),
                    expected_token_id=None,
                    edit_distance=1,
                )
                return (
                    ProtoBasicParseCategory.NEAR_MISS,
                    shape,
                    token_ids[: len(shape)],
                    hint,
                    "delete-token",
                )
        # Known tokens but wrong shape and no length-1 near-miss -> semantic-invalid.
        return (
            ProtoBasicParseCategory.SEMANTIC_INVALID,
            kinds,
            token_ids,
            None,
            "shape-mismatch",
        )

    # Case-fold-only matches: deterministic single-edit near-miss.
    if all(t is not None for t in case_fold_matches):
        # Identify the first position whose exact form differs.
        for position, (exact, folded) in enumerate(
            zip(exact_matches, case_fold_matches)
        ):
            if exact is None and folded is not None:
                hint = ProtoBasicCorrectionHint(
                    edit_kind=ProtoBasicEditKind.CASE_FOLD,
                    edit_position=position,
                    expected_token_id=folded.token_id,
                    edit_distance=1,
                )
                kinds = tuple(
                    t.kind for t in case_fold_matches  # type: ignore[union-attr]
                )
                token_ids = tuple(
                    t.token_id for t in case_fold_matches  # type: ignore[union-attr]
                )
                if kinds in grammar.command_shapes:
                    return (
                        ProtoBasicParseCategory.NEAR_MISS,
                        kinds,
                        token_ids,
                        hint,
                        "case-fold",
                    )
                # Even after case fold the shape is wrong -> semantic-invalid.
                return (
                    ProtoBasicParseCategory.SEMANTIC_INVALID,
                    kinds,
                    token_ids,
                    None,
                    "shape-mismatch-after-case-fold",
                )

    # Single-token-substitute near-miss: exactly one position has an unknown
    # token while the remaining positions exactly match. Propose any token of
    # any expected kind that fits a known command shape.
    unknown_positions = [
        i for i, t in enumerate(exact_matches) if t is None
    ]
    if len(unknown_positions) == 1:
        position = unknown_positions[0]
        known_kinds = [
            (i, t.kind, t.token_id)
            for i, t in enumerate(exact_matches)
            if t is not None
        ]
        for shape in grammar.command_shapes:
            if len(shape) != len(pieces):
                continue
            if any(
                shape[i] != kind for i, kind, _ in known_kinds
            ):
                continue
            expected_kind = shape[position]
            candidates = grammar.tokens_of_kind(expected_kind)
            if not candidates:
                continue
            expected_token = candidates[0]
            hint = ProtoBasicCorrectionHint(
                edit_kind=ProtoBasicEditKind.SUBSTITUTE_TOKEN,
                edit_position=position,
                expected_token_id=expected_token.token_id,
                edit_distance=1,
            )
            return (
                ProtoBasicParseCategory.NEAR_MISS,
                shape,
                tuple(
                    t.token_id if t is not None else expected_token.token_id
                    for t in exact_matches
                ),
                hint,
                "substitute-token",
            )

    # Fallback: syntax-invalid for any other shape we cannot interpret.
    return (
        ProtoBasicParseCategory.SYNTAX_INVALID,
        None,
        tuple(
            t.token_id for t in exact_matches if t is not None
        ),
        None,
        "unknown-tokens",
    )


def parse_line(
    grammar: ProtoBasicGrammar,
    line: ProtoBasicLine,
) -> ProtoBasicParseResult:
    """Deterministic total parser over ``ProtoBasicLine`` (I-REPL-03).

    Guarantees:

      * never raises for any ``ProtoBasicLine`` constructed under the grammar
        bounds,
      * returns exactly one ``ProtoBasicParseResult``,
      * yields the same result for the same line under the same grammar.
    """
    if not isinstance(grammar, ProtoBasicGrammar):
        raise TypeError(
            "I-REPL-03 violated: parse_line grammar must be ProtoBasicGrammar"
        )
    if not isinstance(line, ProtoBasicLine):
        raise TypeError(
            "I-REPL-03 violated: parse_line line must be ProtoBasicLine"
        )

    (
        category,
        matched_shape,
        matched_token_ids,
        correction_hint,
        detail,
    ) = _classify_line(grammar, line)
    return ProtoBasicParseResult(
        line_id=line.line_id,
        category=category,
        matched_shape=matched_shape,
        matched_token_ids=matched_token_ids,
        correction_hint=correction_hint,
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Execution result (the partial slice needed for Step 7 feedback wiring).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProtoBasicExecutionResult:
    """A bounded local execution outcome (I-REPL-13).

    Step 7 needs this surface so feedback scoring (I-REPL-08/09/10) can
    reference an execution category and the ``effective`` flag. The full
    construction discipline (parse + token + learned-output dependence) lands
    in Step 8 (I-REPL-11/12/13).
    """

    line_id: ProtoBasicLineID
    category: ProtoBasicExecutionCategory
    effective: bool
    detail: str = ""

    def __post_init__(self) -> None:
        _require_non_reserved_id(
            self.line_id,
            field="ProtoBasicExecutionResult.line_id",
            row_id="I-REPL-13",
        )
        if not isinstance(self.category, ProtoBasicExecutionCategory):
            raise TypeError(
                "I-REPL-13 violated: ProtoBasicExecutionResult.category must "
                "be a ProtoBasicExecutionCategory"
            )
        if not isinstance(self.effective, bool):
            raise TypeError(
                "I-REPL-13 violated: ProtoBasicExecutionResult.effective must "
                "be bool"
            )
        is_effective_category = (
            self.category is ProtoBasicExecutionCategory.VALID_EFFECTIVE
        )
        if self.effective is not is_effective_category:
            raise ValueError(
                "I-REPL-13 violated: ProtoBasicExecutionResult.effective must "
                "be True iff category == valid-effective"
            )
        if not isinstance(self.detail, str):
            raise TypeError(
                "ProtoBasicExecutionResult.detail must be a string"
            )


# ---------------------------------------------------------------------------
# Feedback layer (I-REPL-06..10).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProtoBasicValence:
    """Exact bounded Proto-BASIC feedback valence (I-REPL-06)."""

    value: Fraction

    def __post_init__(self) -> None:
        try:
            require_proto_basic_valence(
                self.value,
                field="ProtoBasicValence.value",
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-REPL-06 violated: ProtoBasicValence.value must be a "
                "Fraction in [-1, 1]"
            ) from exc


@dataclass(frozen=True, slots=True)
class ProtoBasicFeedbackProvenance:
    """Provenance for one Proto-BASIC feedback record (I-REPL-07).

    Reuses ``FrameSourceKind`` and the Fraction-in-[0,1] confidence
    discipline; adds no Proto-BASIC-specific source-kind enum member.
    """

    source_kind: FrameSourceKind
    confidence: Fraction
    trace_event_ids: tuple[TraceEventID, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source_kind, FrameSourceKind):
            raise TypeError(
                "I-REPL-07 violated: ProtoBasicFeedbackProvenance.source_kind "
                "must be a FrameSourceKind"
            )
        try:
            require_unit_fraction(
                self.confidence,
                field="ProtoBasicFeedbackProvenance.confidence",
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-REPL-07 violated: ProtoBasicFeedbackProvenance.confidence "
                "must be a Fraction in [0, 1]"
            ) from exc
        if not isinstance(self.trace_event_ids, tuple):
            raise TypeError(
                "ProtoBasicFeedbackProvenance.trace_event_ids must be a tuple"
            )
        for event_id in self.trace_event_ids:
            require_printable_id(
                event_id,
                field="ProtoBasicFeedbackProvenance.trace_event_id",
            )


@dataclass(frozen=True, slots=True)
class ProtoBasicFeedback:
    """One bounded local feedback record (I-REPL-06/07/08/09/10)."""

    line_id: ProtoBasicLineID
    valence: ProtoBasicValence
    provenance: ProtoBasicFeedbackProvenance
    parse_category: ProtoBasicParseCategory | None = None
    execution_category: ProtoBasicExecutionCategory | None = None
    detail: str = ""

    def __post_init__(self) -> None:
        _require_non_reserved_id(
            self.line_id,
            field="ProtoBasicFeedback.line_id",
            row_id="I-REPL-07",
        )
        if not isinstance(self.valence, ProtoBasicValence):
            raise TypeError(
                "I-REPL-06 violated: ProtoBasicFeedback.valence must be a "
                "ProtoBasicValence"
            )
        if not isinstance(self.provenance, ProtoBasicFeedbackProvenance):
            raise TypeError(
                "I-REPL-07 violated: ProtoBasicFeedback.provenance must be a "
                "ProtoBasicFeedbackProvenance"
            )
        if self.parse_category is not None and not isinstance(
            self.parse_category, ProtoBasicParseCategory
        ):
            raise TypeError(
                "ProtoBasicFeedback.parse_category must be a "
                "ProtoBasicParseCategory or None"
            )
        if self.execution_category is not None and not isinstance(
            self.execution_category, ProtoBasicExecutionCategory
        ):
            raise TypeError(
                "ProtoBasicFeedback.execution_category must be a "
                "ProtoBasicExecutionCategory or None"
            )
        if self.parse_category is None and self.execution_category is None:
            raise ValueError(
                "ProtoBasicFeedback must reference either a parse_category or "
                "an execution_category"
            )
        if not isinstance(self.detail, str):
            raise TypeError("ProtoBasicFeedback.detail must be a string")


# Parse-only valence convention (Section 6 of the catalog patch plan). These
# are intentionally weak so anti-Goodhart pressure can grow from them later
# without retroactively breaking I-REPL-09.
_PARSE_VALENCE_TABLE: Mapping[ProtoBasicParseCategory, Fraction] = (
    MappingProxyType(
        {
            ProtoBasicParseCategory.VALID: Fraction(0),
            ProtoBasicParseCategory.NEAR_MISS: Fraction(-1, 10),
            ProtoBasicParseCategory.SYNTAX_INVALID: Fraction(-1, 4),
            ProtoBasicParseCategory.SEMANTIC_INVALID: Fraction(-1, 4),
            ProtoBasicParseCategory.TOOL_UNAVAILABLE: Fraction(-1, 4),
            ProtoBasicParseCategory.RESOURCE_LIMIT: Fraction(-1, 4),
            ProtoBasicParseCategory.SANDBOX_FAULT: Fraction(-1, 2),
        }
    )
)

# Execution valence convention. ``valid-effective`` is the only category that
# can earn strong positive feedback (I-REPL-10). The diminishing-returns
# multiplier comes from Step 9 / I-REPL-15; Step 7 exposes the first-emission
# value.
_EXECUTION_VALENCE_TABLE: Mapping[ProtoBasicExecutionCategory, Fraction] = (
    MappingProxyType(
        {
            ProtoBasicExecutionCategory.VALID_EFFECTIVE: Fraction(1, 2),
            ProtoBasicExecutionCategory.VALID_INEFFECTIVE: Fraction(0),
            ProtoBasicExecutionCategory.TOOL_UNAVAILABLE: Fraction(-1, 4),
            ProtoBasicExecutionCategory.RESOURCE_LIMIT: Fraction(-1, 4),
            ProtoBasicExecutionCategory.SANDBOX_FAULT: Fraction(-1, 2),
        }
    )
)


def score_feedback(
    *,
    parse_result: ProtoBasicParseResult | None = None,
    execution_result: ProtoBasicExecutionResult | None = None,
    provenance: ProtoBasicFeedbackProvenance,
    diminishing_returns_factor: Fraction = Fraction(1),
) -> ProtoBasicFeedback:
    """Return a deterministic bounded ``ProtoBasicFeedback`` (I-REPL-06..10).

    Exactly one of ``parse_result`` or ``execution_result`` must be provided.
    Strong positive valence (>= ``PROTO_BASIC_STRONG_POSITIVE_THRESHOLD``)
    is only producible when the source is a valid-effective execution result
    (I-REPL-10).

    ``diminishing_returns_factor`` is a hook reserved for Step 9's
    ``I-REPL-15``. It must be a ``Fraction`` in ``[0, 1]``. Step 7 callers
    leave it at ``Fraction(1)``; this still satisfies I-REPL-09/I-REPL-10
    because valid-ineffective and parse-only categories cannot reach the
    strong threshold regardless of the factor.
    """
    if (parse_result is None) == (execution_result is None):
        raise ValueError(
            "score_feedback requires exactly one of parse_result or "
            "execution_result"
        )
    if not isinstance(provenance, ProtoBasicFeedbackProvenance):
        raise TypeError(
            "I-REPL-07 violated: score_feedback provenance must be a "
            "ProtoBasicFeedbackProvenance"
        )
    if not isinstance(diminishing_returns_factor, Fraction):
        raise TypeError(
            "I-REPL-15 violated: diminishing_returns_factor must be a "
            "Fraction"
        )
    if not (Fraction(0) <= diminishing_returns_factor <= Fraction(1)):
        raise ValueError(
            "I-REPL-15 violated: diminishing_returns_factor must be in [0, 1]"
        )

    if execution_result is not None:
        base = _EXECUTION_VALENCE_TABLE[execution_result.category]
        if execution_result.category is (
            ProtoBasicExecutionCategory.VALID_EFFECTIVE
        ):
            value = base * diminishing_returns_factor
        else:
            value = base
        # Defensive clamp-by-rejection: the table values combined with the
        # bounded factor cannot leave [-1, 1], but we still validate.
        require_proto_basic_valence(
            value,
            field="score_feedback execution valence",
        )
        return ProtoBasicFeedback(
            line_id=execution_result.line_id,
            valence=ProtoBasicValence(value),
            provenance=provenance,
            parse_category=None,
            execution_category=execution_result.category,
            detail=execution_result.detail,
        )

    assert parse_result is not None  # for type-narrowing
    value = _PARSE_VALENCE_TABLE[parse_result.category]
    # Strong positive valence is unreachable from a parse_result alone:
    # the VALID parse maps to Fraction(0), and every other category is
    # strictly non-positive. This is the I-REPL-09/I-REPL-10 gate.
    require_proto_basic_valence(
        value,
        field="score_feedback parse valence",
    )
    return ProtoBasicFeedback(
        line_id=parse_result.line_id,
        valence=ProtoBasicValence(value),
        provenance=provenance,
        parse_category=parse_result.category,
        execution_category=None,
        detail=parse_result.detail,
    )


# ---------------------------------------------------------------------------
# Program wrapper (I-REPL-17).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProtoBasicProgram:
    """A thin one-line wrapper around ``ProtoBasicLine`` (I-REPL-17).

    The Phase 3.4 Proto-BASIC surface intentionally has no GOTO, GOSUB,
    branching line numbers, loops, stored-program memory beyond
    ``ProtoBasicHistory``, nested blocks, or multi-line semantics.
    """

    program_id: str
    line: ProtoBasicLine

    def __post_init__(self) -> None:
        _require_non_reserved_id(
            self.program_id,
            field="ProtoBasicProgram.program_id",
            row_id="I-REPL-17",
        )
        if not isinstance(self.line, ProtoBasicLine):
            raise TypeError(
                "I-REPL-17 violated: ProtoBasicProgram.line must be a "
                "ProtoBasicLine"
            )


__all__ = [
    "PROTO_BASIC_MAX_EDIT_DISTANCE",
    "PROTO_BASIC_MAX_LINE_LENGTH",
    "PROTO_BASIC_MAX_LINE_TOKENS",
    "PROTO_BASIC_MAX_TOKEN_LENGTH",
    "PROTO_BASIC_STRONG_POSITIVE_THRESHOLD",
    "EXECUTION_CATEGORIES",
    "PARSE_CATEGORIES",
    "ProtoBasicCorrectionHint",
    "ProtoBasicEditKind",
    "ProtoBasicExecutionCategory",
    "ProtoBasicExecutionResult",
    "ProtoBasicFeedback",
    "ProtoBasicFeedbackProvenance",
    "ProtoBasicGrammar",
    "ProtoBasicLine",
    "ProtoBasicParseCategory",
    "ProtoBasicParseResult",
    "ProtoBasicProgram",
    "ProtoBasicToken",
    "ProtoBasicTokenKind",
    "ProtoBasicValence",
    "parse_line",
    "require_proto_basic_valence",
    "score_feedback",
    "tokenize",
]
