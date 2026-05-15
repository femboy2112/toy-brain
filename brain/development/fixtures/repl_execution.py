"""Fixtures for Phase 3.4 Proto-BASIC REPL execution rows.

This module drives ``I-REPL-11``, ``I-REPL-12``, and ``I-REPL-13``: the
agency/language/host-execution/trace-field exclusion on ``ProtoBasicCommand``,
the construction discipline (valid parse plus enumerated tokens plus
``LearnedOutputToken`` backing when required), and the bounded execution
category set with the ``effective`` derivation.
"""
from __future__ import annotations

from fractions import Fraction

from brain.development.output import (
    LearnedOutputToken,
    OutputHistory,
    OutputTokenCandidate,
)
from brain.development.repl import (
    ProtoBasicCommand,
    ProtoBasicExecutionCategory,
    ProtoBasicExecutionResult,
    ProtoBasicGrammar,
    ProtoBasicParseCategory,
    ProtoBasicParseResult,
    ProtoBasicToken,
    ProtoBasicTokenKind,
    build_command,
    execute_command,
    parse_line,
    tokenize,
)
from brain.development.stream import FrameSourceKind
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


def _learned_token(text: str, *, token_id: str) -> LearnedOutputToken:
    candidate = OutputTokenCandidate(
        token_id=token_id,
        pattern_id=f"out-pattern:{token_id}",
        text=text,
        support_count=2,
        impulse_ids=(f"imp:{token_id}:0", f"imp:{token_id}:1"),
        echo_ids=(f"echo:{token_id}:0", f"echo:{token_id}:1"),
        source_kinds=frozenset({FrameSourceKind.GENERATED}),
    )
    return LearnedOutputToken(token_id=token_id, candidate=candidate)


def _output_history_with_verbs() -> OutputHistory:
    learned = {
        "out-token:print": _learned_token("PRINT", token_id="out-token:print"),
        "out-token:let": _learned_token("LET", token_id="out-token:let"),
    }
    return OutputHistory(learned_tokens=learned)


def _parse_valid(raw: str, *, line_id: str) -> ProtoBasicParseResult:
    grammar = _grammar()
    line = tokenize(raw, line_id=line_id)
    result = parse_line(grammar, line)
    assert result.category is ProtoBasicParseCategory.VALID, (
        f"fixture invariant: expected VALID parse for {raw!r}, got "
        f"{result.category}"
    )
    return result


@register("I-REPL-11", status="STRUCTURAL")
def check_proto_basic_command_carries_no_forbidden_fields() -> None:
    # The dataclass slot inventory must not contain any agency / language /
    # host-execution / trace field name.
    forbidden = {
        "act",
        "mode_op",
        "agency_witness",
        "percept_event",
        "selected_action",
        "feasible_projected_pce",
        "tick",
        "tick_callback",
        "interpreter",
        "interpreter_handle",
        "subprocess",
        "subprocess_handle",
        "file_descriptor",
        "fd",
        "socket",
        "network_socket",
        "teacher_utterance",
        "teacher",
        "social_register",
        "readability_score",
        "readability",
        "expression",
        "expression_handle",
        "mode_b_plan",
        "mode_b",
        "trace_event",
        "trace_event_id",
        "free_will_branch",
    }
    slots = set(ProtoBasicCommand.__slots__)
    leak = slots & forbidden
    assert not leak, (
        f"I-REPL-11 violated: ProtoBasicCommand slots include {sorted(leak)}"
    )

    # A constructed command's public attributes must also be a subset of the
    # declared slots (no extra agency surface bolted on at runtime).
    parse_result = _parse_valid("PRINT X", line_id="repl:line:no-leak")
    command = build_command(
        grammar=_grammar(),
        parse_result=parse_result,
        command_id="repl:command:no-leak",
    )
    public = {n for n in dir(command) if not n.startswith("_")}
    assert not (public & forbidden), (
        "I-REPL-11 violated: ProtoBasicCommand instance exposes forbidden "
        f"attributes {public & forbidden}"
    )

    # Each declared slot is allowed: command_id, source_line_id, matched_shape,
    # matched_token_ids, canonical_form. Anything else would be a scope leak.
    expected_slots = {
        "command_id",
        "source_line_id",
        "matched_shape",
        "matched_token_ids",
        "canonical_form",
    }
    assert slots == expected_slots, (
        "I-REPL-11 violated: unexpected ProtoBasicCommand slot set "
        f"{slots ^ expected_slots}"
    )


@register("I-REPL-12", status="REQUIRED")
def check_proto_basic_command_requires_valid_parse_and_support() -> None:
    grammar = _grammar()

    # Happy path: valid parse plus enumerated tokens builds a command.
    parse_result = _parse_valid("PRINT X", line_id="repl:line:build-ok")
    command = build_command(
        grammar=grammar,
        parse_result=parse_result,
        command_id="repl:command:build-ok",
    )
    assert command.source_line_id == "repl:line:build-ok"
    assert command.matched_token_ids == ("repl:verb:print", "repl:target:x")

    # Non-VALID parse results are rejected with the row tag.
    syntax_invalid = ProtoBasicParseResult(
        line_id="repl:line:syn-invalid",
        category=ProtoBasicParseCategory.SYNTAX_INVALID,
    )
    try:
        build_command(
            grammar=grammar,
            parse_result=syntax_invalid,
            command_id="repl:command:bad-syntax",
        )
    except ValueError as exc:
        assert "I-REPL-12" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-12 violated: build_command accepted non-VALID parse result"
        )

    # Parse results referencing non-enumerated tokens are rejected.
    rogue_parse = ProtoBasicParseResult(
        line_id="repl:line:rogue-token",
        category=ProtoBasicParseCategory.VALID,
        matched_shape=(
            ProtoBasicTokenKind.VERB,
            ProtoBasicTokenKind.TARGET,
        ),
        matched_token_ids=("repl:verb:print", "repl:target:nonexistent"),
    )
    try:
        build_command(
            grammar=grammar,
            parse_result=rogue_parse,
            command_id="repl:command:rogue",
        )
    except ValueError as exc:
        assert "I-REPL-12" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-12 violated: build_command accepted non-enumerated token"
        )

    # Reserved command IDs are rejected.
    for bad_id in (COGITO_ID, "tick", "PerceptEvent", "feasibleProjectedPCE"):
        try:
            build_command(
                grammar=grammar,
                parse_result=parse_result,
                command_id=bad_id,
            )
        except ValueError as exc:
            assert "I-REPL-12" in str(exc), (
                f"I-REPL-12 violated: wrong row tag rejecting {bad_id!r}: {exc}"
            )
        else:
            raise AssertionError(
                f"I-REPL-12 violated: reserved command_id {bad_id!r} accepted"
            )

    # Non-printable command IDs are rejected.
    for bad_id in ("", "   ", "bad\x00id"):
        try:
            build_command(
                grammar=grammar,
                parse_result=parse_result,
                command_id=bad_id,
            )
        except (TypeError, ValueError) as exc:
            assert "I-REPL-12" in str(exc), (
                f"I-REPL-12 violated: wrong row tag rejecting {bad_id!r}: {exc}"
            )
        else:
            raise AssertionError(
                f"I-REPL-12 violated: non-printable command_id {bad_id!r} "
                "accepted"
            )

    # Learned-output gating: when a kind requires LearnedOutputToken support,
    # build_command rejects construction without OutputHistory backing.
    try:
        build_command(
            grammar=grammar,
            parse_result=parse_result,
            command_id="repl:command:no-output-history",
            require_learned_kinds=frozenset({ProtoBasicTokenKind.VERB}),
        )
    except ValueError as exc:
        assert "I-REPL-12" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-12 violated: missing OutputHistory accepted when "
            "require_learned_kinds is non-empty"
        )

    # With matching learned tokens, construction succeeds.
    history = _output_history_with_verbs()
    command_with_support = build_command(
        grammar=grammar,
        parse_result=parse_result,
        command_id="repl:command:supported",
        output_history=history,
        require_learned_kinds=frozenset({ProtoBasicTokenKind.VERB}),
    )
    assert command_with_support.matched_token_ids == (
        "repl:verb:print",
        "repl:target:x",
    )

    # When a required kind has no learned-output entry, construction fails.
    empty_history = OutputHistory()
    try:
        build_command(
            grammar=grammar,
            parse_result=parse_result,
            command_id="repl:command:unsupported",
            output_history=empty_history,
            require_learned_kinds=frozenset({ProtoBasicTokenKind.VERB}),
        )
    except ValueError as exc:
        assert "I-REPL-12" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-12 violated: missing LearnedOutputToken support accepted"
        )

    # Readiness / parse-validity alone is insufficient: a VALID parse whose
    # tokens lack required learned-output backing must be rejected even when
    # an OutputHistory exists but is missing the right token.
    half_learned = OutputHistory(
        learned_tokens={
            "out-token:print": _learned_token("PRINT", token_id="out-token:print"),
        }
    )
    parse_let = _parse_valid("LET Y", line_id="repl:line:let-y")
    try:
        build_command(
            grammar=grammar,
            parse_result=parse_let,
            command_id="repl:command:let-y",
            output_history=half_learned,
            require_learned_kinds=frozenset({ProtoBasicTokenKind.VERB}),
        )
    except ValueError as exc:
        assert "I-REPL-12" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-12 violated: partial learned-output support accepted"
        )


@register("I-REPL-13", status="STRUCTURAL")
def check_proto_basic_execution_result_exposes_declared_category_set() -> None:
    grammar = _grammar()
    parse_result = _parse_valid("PRINT X", line_id="repl:line:exec")
    command = build_command(
        grammar=grammar,
        parse_result=parse_result,
        command_id="repl:command:exec",
    )

    # Every declared category is acceptable to execute_command, and effective
    # is True iff category == VALID_EFFECTIVE.
    declared = {
        ProtoBasicExecutionCategory.VALID_EFFECTIVE,
        ProtoBasicExecutionCategory.VALID_INEFFECTIVE,
        ProtoBasicExecutionCategory.TOOL_UNAVAILABLE,
        ProtoBasicExecutionCategory.RESOURCE_LIMIT,
        ProtoBasicExecutionCategory.SANDBOX_FAULT,
    }
    for category in declared:
        result = execute_command(command, category=category)
        assert isinstance(result, ProtoBasicExecutionResult)
        assert result.category is category
        assert result.effective is (
            category is ProtoBasicExecutionCategory.VALID_EFFECTIVE
        )
        assert result.line_id == command.source_line_id

    # The category enum is exactly the declared set; no member has been added.
    members = {member for member in ProtoBasicExecutionCategory}
    assert members == declared, (
        "I-REPL-13 violated: ProtoBasicExecutionCategory drifted from the "
        f"declared set: {members ^ declared}"
    )

    # Direct construction rejects mismatched effective/category combinations.
    for category in declared:
        non_effective_value = category is not ProtoBasicExecutionCategory.VALID_EFFECTIVE
        try:
            ProtoBasicExecutionResult(
                line_id="repl:line:mismatch",
                category=category,
                effective=non_effective_value
                if category is ProtoBasicExecutionCategory.VALID_EFFECTIVE
                else True,
            )
        except ValueError as exc:
            assert "I-REPL-13" in str(exc)
        else:
            raise AssertionError(
                "I-REPL-13 violated: mismatched effective flag accepted for "
                f"{category}"
            )

    # ProtoBasicExecutionResult exposes no host-execution / PerceptEvent
    # surface.
    result = execute_command(
        command, category=ProtoBasicExecutionCategory.VALID_EFFECTIVE
    )
    forbidden = {
        "tick",
        "percept_event",
        "PerceptEvent",
        "subprocess",
        "subprocess_handle",
        "interpreter",
        "interpreter_handle",
        "file_descriptor",
        "fd",
        "socket",
        "network_socket",
    }
    public = {n for n in dir(result) if not n.startswith("_")}
    assert not (public & forbidden), (
        "I-REPL-13 violated: ProtoBasicExecutionResult exposes forbidden "
        f"surface {public & forbidden}"
    )

    # Determinism: re-executing the same command with the same category yields
    # an equal result.
    again = execute_command(
        command, category=ProtoBasicExecutionCategory.VALID_EFFECTIVE
    )
    assert again == result

    # Silence the Fraction-unused warning while keeping the import; the
    # provenance discipline test in repl_feedback.py covers Fraction usage.
    _ = Fraction(0)
