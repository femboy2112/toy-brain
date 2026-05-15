"""Fixtures for Phase 3.4 Proto-BASIC REPL grammar and parser rows.

This module drives the v0.9 ``I-REPL-01``..``I-REPL-05`` and ``I-REPL-17``
catalog rows. The checks construct a small enumerated grammar and exercise
``tokenize`` / ``parse_line`` over the seven parse categories, including the
near-miss correction-hint discipline and the program-wrapper bound.
"""
from __future__ import annotations

from brain.development.repl import (
    PROTO_BASIC_MAX_EDIT_DISTANCE,
    PROTO_BASIC_MAX_LINE_LENGTH,
    PROTO_BASIC_MAX_LINE_TOKENS,
    PROTO_BASIC_MAX_TOKEN_LENGTH,
    ProtoBasicCorrectionHint,
    ProtoBasicEditKind,
    ProtoBasicGrammar,
    ProtoBasicLine,
    ProtoBasicParseCategory,
    ProtoBasicParseResult,
    ProtoBasicProgram,
    ProtoBasicToken,
    ProtoBasicTokenKind,
    parse_line,
    tokenize,
)
from brain.invariants import register
from brain.tlica.profile import COGITO_ID


def _grammar() -> ProtoBasicGrammar:
    tokens = (
        ProtoBasicToken(
            token_id="repl:verb:print",
            kind=ProtoBasicTokenKind.VERB,
            text="PRINT",
        ),
        ProtoBasicToken(
            token_id="repl:verb:let",
            kind=ProtoBasicTokenKind.VERB,
            text="LET",
        ),
        ProtoBasicToken(
            token_id="repl:target:x",
            kind=ProtoBasicTokenKind.TARGET,
            text="X",
        ),
        ProtoBasicToken(
            token_id="repl:target:y",
            kind=ProtoBasicTokenKind.TARGET,
            text="Y",
        ),
        ProtoBasicToken(
            token_id="repl:object:one",
            kind=ProtoBasicTokenKind.OBJECT,
            text="ONE",
        ),
    )
    shapes = (
        (ProtoBasicTokenKind.VERB, ProtoBasicTokenKind.TARGET),
        (
            ProtoBasicTokenKind.VERB,
            ProtoBasicTokenKind.TARGET,
            ProtoBasicTokenKind.OBJECT,
        ),
    )
    return ProtoBasicGrammar(tokens=tokens, command_shapes=shapes)


def _line(raw: str, *, line_id: str) -> ProtoBasicLine:
    return tokenize(raw, line_id=line_id)


@register("I-REPL-01", status="STRUCTURAL")
def check_proto_basic_token_enumeration_is_finite_and_bounded() -> None:
    grammar = _grammar()
    assert len(grammar.tokens) == 5
    # Per-kind enumeration is deterministic.
    verbs = grammar.tokens_of_kind(ProtoBasicTokenKind.VERB)
    targets = grammar.tokens_of_kind(ProtoBasicTokenKind.TARGET)
    assert {t.text for t in verbs} == {"PRINT", "LET"}
    assert {t.text for t in targets} == {"X", "Y"}

    # Bounded token text: empty/whitespace-only/non-printable text is rejected.
    for bad_text in ("", "   ", "X" * (PROTO_BASIC_MAX_TOKEN_LENGTH + 1)):
        try:
            ProtoBasicToken(
                token_id="repl:verb:bad",
                kind=ProtoBasicTokenKind.VERB,
                text=bad_text,
            )
        except ValueError as exc:
            assert "I-REPL-01" in str(exc)
        else:
            raise AssertionError(
                "I-REPL-01 violated: token text bound check missed: "
                f"{bad_text!r}"
            )

    # Whitespace in token text is rejected.
    try:
        ProtoBasicToken(
            token_id="repl:verb:bad",
            kind=ProtoBasicTokenKind.VERB,
            text="PRI NT",
        )
    except ValueError as exc:
        assert "I-REPL-01" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-01 violated: whitespace-bearing token text passed"
        )

    # Reserved COGITO_ID rejected.
    try:
        ProtoBasicToken(
            token_id=COGITO_ID,
            kind=ProtoBasicTokenKind.VERB,
            text="PRINT",
        )
    except ValueError as exc:
        assert "I-REPL-01" in str(exc)
    else:
        raise AssertionError("I-REPL-01 violated: reserved token_id accepted")

    # Duplicate canonical text rejected at grammar build time.
    try:
        ProtoBasicGrammar(
            tokens=(
                ProtoBasicToken(
                    token_id="repl:verb:print",
                    kind=ProtoBasicTokenKind.VERB,
                    text="PRINT",
                ),
                ProtoBasicToken(
                    token_id="repl:verb:print-dup",
                    kind=ProtoBasicTokenKind.VERB,
                    text="print",
                ),
            ),
            command_shapes=((ProtoBasicTokenKind.VERB,),),
        )
    except ValueError as exc:
        assert "I-REPL-01" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-01 violated: duplicate canonical text accepted"
        )


@register("I-REPL-02", status="STRUCTURAL")
def check_proto_basic_line_is_bounded_and_tokenize_is_total() -> None:
    line = _line("PRINT X", line_id="repl:line:print-x")
    assert isinstance(line, ProtoBasicLine)
    assert line.tokens == ("PRINT", "X")
    assert len(line.tokens) <= PROTO_BASIC_MAX_LINE_TOKENS
    assert len(line.raw_text) <= PROTO_BASIC_MAX_LINE_LENGTH

    # Empty line tokenizes to an empty token tuple without raising.
    blank = _line("", line_id="repl:line:blank")
    assert blank.tokens == ()

    # Whitespace-only line tokenizes to an empty tuple.
    spaces = _line("   ", line_id="repl:line:spaces")
    assert spaces.tokens == ()

    # Determinism: same input + same line_id yields the same line.
    again = _line("PRINT X", line_id="repl:line:print-x")
    assert again == line

    # Over-long raw text is rejected at tokenize.
    try:
        tokenize("X" * (PROTO_BASIC_MAX_LINE_LENGTH + 1), line_id="repl:line:big")
    except ValueError as exc:
        assert "I-REPL-02" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-02 violated: over-length raw_text accepted"
        )

    # Tokens beyond the count cap are truncated.
    crowded = tokenize(
        "PRINT X Y ONE EXTRA",
        line_id="repl:line:crowded",
    )
    assert len(crowded.tokens) == PROTO_BASIC_MAX_LINE_TOKENS

    # Per-token length cap: oversized piece is truncated, not unbounded.
    over_token = "Z" * (PROTO_BASIC_MAX_TOKEN_LENGTH + 5)
    big_piece = tokenize(
        f"PRINT {over_token}",
        line_id="repl:line:big-piece",
    )
    assert all(len(p) <= PROTO_BASIC_MAX_TOKEN_LENGTH for p in big_piece.tokens)


@register("I-REPL-03", status="REQUIRED")
def check_parse_line_is_total_and_deterministic() -> None:
    grammar = _grammar()

    samples = (
        ("PRINT X", "repl:line:s1"),
        ("print x", "repl:line:s2"),  # case-fold near-miss
        ("PRINT", "repl:line:s3"),  # missing target
        ("PRINT FOO", "repl:line:s4"),  # unknown token substitution
        ("PRINT X EXTRA", "repl:line:s5"),  # extra token (delete near-miss)
        ("X PRINT", "repl:line:s6"),  # known tokens, wrong shape
        ("", "repl:line:s7"),
    )
    seen: list[ProtoBasicParseResult] = []
    for raw, line_id in samples:
        line = tokenize(raw, line_id=line_id)
        result = parse_line(grammar, line)
        assert isinstance(result, ProtoBasicParseResult)
        assert result.line_id == line.line_id
        seen.append(result)

    # Determinism: re-parsing yields equal results.
    for (raw, line_id), prior in zip(samples, seen):
        line = tokenize(raw, line_id=line_id)
        again = parse_line(grammar, line)
        assert again == prior


@register("I-REPL-04", status="REQUIRED")
def check_parse_categories_partition_outcomes_without_overlap() -> None:
    grammar = _grammar()

    expected = {
        "PRINT X": ProtoBasicParseCategory.VALID,
        "print x": ProtoBasicParseCategory.NEAR_MISS,
        "PRINT FOO": ProtoBasicParseCategory.NEAR_MISS,
        "PRINT X EXTRA": ProtoBasicParseCategory.NEAR_MISS,
        "X PRINT": ProtoBasicParseCategory.SEMANTIC_INVALID,
        "FOO BAR": ProtoBasicParseCategory.SYNTAX_INVALID,
        "": ProtoBasicParseCategory.SYNTAX_INVALID,
    }
    for index, (raw, category) in enumerate(expected.items()):
        line = tokenize(raw, line_id=f"repl:line:partition:{index}")
        result = parse_line(grammar, line)
        assert result.category is category, (
            f"I-REPL-04 violated: {raw!r} category was {result.category}"
        )

    # Every category is exactly one ProtoBasicParseCategory member.
    for raw in expected:
        line = tokenize(raw, line_id=f"repl:line:single:{raw!r}")
        result = parse_line(grammar, line)
        match_count = sum(
            1
            for category in ProtoBasicParseCategory
            if result.category is category
        )
        assert match_count == 1, (
            f"I-REPL-04 violated: line {raw!r} matched {match_count} "
            "categories"
        )

    # The union of category members covers every line: parser is total.
    members = {category for category in ProtoBasicParseCategory}
    for raw in expected:
        line = tokenize(raw, line_id=f"repl:line:cover:{raw!r}")
        result = parse_line(grammar, line)
        assert result.category in members


@register("I-REPL-05", status="REQUIRED")
def check_near_miss_correction_hints_respect_bounded_edit_distance() -> None:
    grammar = _grammar()

    # CASE_FOLD near-miss.
    case_line = tokenize("print x", line_id="repl:line:casefold")
    case_result = parse_line(grammar, case_line)
    assert case_result.category is ProtoBasicParseCategory.NEAR_MISS
    assert isinstance(case_result.correction_hint, ProtoBasicCorrectionHint)
    hint = case_result.correction_hint
    assert hint.edit_kind is ProtoBasicEditKind.CASE_FOLD
    assert 0 <= hint.edit_position <= PROTO_BASIC_MAX_LINE_TOKENS
    assert hint.expected_token_id is not None
    assert any(
        t.token_id == hint.expected_token_id for t in grammar.tokens
    ), "I-REPL-05 violated: hint references unknown token"
    assert 0 < hint.edit_distance <= PROTO_BASIC_MAX_EDIT_DISTANCE
    assert 0 < hint.edit_distance <= grammar.max_edit_distance

    # SUBSTITUTE_TOKEN near-miss.
    sub_line = tokenize("PRINT FOO", line_id="repl:line:substitute")
    sub_result = parse_line(grammar, sub_line)
    assert sub_result.category is ProtoBasicParseCategory.NEAR_MISS
    assert sub_result.correction_hint is not None
    assert (
        sub_result.correction_hint.edit_kind
        is ProtoBasicEditKind.SUBSTITUTE_TOKEN
    )
    assert (
        sub_result.correction_hint.expected_token_id is not None
    )
    assert (
        0
        < sub_result.correction_hint.edit_distance
        <= grammar.max_edit_distance
    )

    # INSERT_TOKEN near-miss (line is shorter than a valid shape).
    insert_line = tokenize("PRINT", line_id="repl:line:insert")
    insert_result = parse_line(grammar, insert_line)
    assert insert_result.category is ProtoBasicParseCategory.NEAR_MISS
    assert insert_result.correction_hint is not None
    assert (
        insert_result.correction_hint.edit_kind
        is ProtoBasicEditKind.INSERT_TOKEN
    )

    # DELETE_TOKEN near-miss (line has one extra known token).
    delete_line = tokenize("PRINT X ONE Y", line_id="repl:line:delete")
    # All four tokens are enumerated; the valid 3-token shape
    # VERB-TARGET-OBJECT matches the first three, leaving the trailing Y as a
    # delete near-miss.
    delete_result = parse_line(grammar, delete_line)
    assert delete_result.category is ProtoBasicParseCategory.NEAR_MISS, (
        f"I-REPL-05 violated: expected near-miss, got "
        f"{delete_result.category}"
    )
    assert delete_result.correction_hint is not None
    assert (
        delete_result.correction_hint.edit_kind
        is ProtoBasicEditKind.DELETE_TOKEN
    )

    # Only near-miss results may carry a correction_hint.
    valid_line = tokenize("PRINT X", line_id="repl:line:valid")
    valid_result = parse_line(grammar, valid_line)
    assert valid_result.category is ProtoBasicParseCategory.VALID
    assert valid_result.correction_hint is None

    # Construction of a near-miss result without a hint is rejected.
    try:
        ProtoBasicParseResult(
            line_id="repl:line:bad-near",
            category=ProtoBasicParseCategory.NEAR_MISS,
            matched_shape=None,
            matched_token_ids=(),
            correction_hint=None,
        )
    except ValueError as exc:
        assert "I-REPL-05" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-05 violated: near-miss without hint accepted"
        )

    # Construction of a non-near-miss result with a hint is rejected.
    stray_hint = ProtoBasicCorrectionHint(
        edit_kind=ProtoBasicEditKind.CASE_FOLD,
        edit_position=0,
        expected_token_id="repl:verb:print",
        edit_distance=1,
    )
    try:
        ProtoBasicParseResult(
            line_id="repl:line:bad-valid",
            category=ProtoBasicParseCategory.SYNTAX_INVALID,
            matched_shape=None,
            matched_token_ids=(),
            correction_hint=stray_hint,
        )
    except ValueError as exc:
        assert "I-REPL-05" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-05 violated: non-near-miss with hint accepted"
        )


@register("I-REPL-17", status="STRUCTURAL")
def check_proto_basic_program_is_one_line_wrapper_only() -> None:
    line = tokenize("PRINT X", line_id="repl:line:program")
    program = ProtoBasicProgram(
        program_id="repl:program:one-line",
        line=line,
    )
    assert program.line is line

    # The wrapper exposes no control-flow / multi-line surface.
    forbidden = {
        "goto",
        "gosub",
        "lines",
        "loop",
        "loops",
        "branches",
        "blocks",
        "program_memory",
        "control_flow",
        "subroutines",
    }
    public = {n for n in dir(program) if not n.startswith("_")}
    assert not (public & forbidden), (
        "I-REPL-17 violated: program exposes control-flow surface "
        f"{public & forbidden}"
    )
    # Only one underlying line is stored; ProtoBasicProgram has exactly two
    # dataclass slots (program_id, line).
    assert ProtoBasicProgram.__slots__ == ("program_id", "line"), (
        "I-REPL-17 violated: ProtoBasicProgram should wrap exactly one "
        "ProtoBasicLine"
    )

    # Constructing a program with a non-line value is rejected.
    try:
        ProtoBasicProgram(
            program_id="repl:program:bad",
            line=("PRINT", "X"),  # type: ignore[arg-type]
        )
    except TypeError as exc:
        assert "I-REPL-17" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-17 violated: program accepted non-line payload"
        )
