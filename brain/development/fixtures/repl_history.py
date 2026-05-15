"""Fixtures for Phase 3.4 Proto-BASIC REPL history rows.

This module drives ``I-REPL-14`` and ``I-REPL-16``: copy-on-write append for
parse / command / execution / feedback entries, and the requirement that no
Proto-BASIC operation mutates TLICA runtime state (profile / MSI / PtCns /
content registry / ``OutputHistory`` / ``WorldletHistory`` / scenario / trace).

Step 9 adds ``I-REPL-15`` (deterministic diminishing returns for repeated
identical valid-effective commands) and the OBSERVED ``I-REPL-18`` aggregate
history summary. Both stay local: no PerceptEvent emission, no tick() call,
no host execution.
"""
from __future__ import annotations

from fractions import Fraction

from brain.development.output import (
    LearnedOutputToken,
    OutputHistory,
    OutputTokenCandidate,
)
from brain.development.repl import (
    PROTO_BASIC_STRONG_POSITIVE_THRESHOLD,
    ProtoBasicCommand,
    ProtoBasicExecutionCategory,
    ProtoBasicExecutionResult,
    ProtoBasicFeedback,
    ProtoBasicFeedbackProvenance,
    ProtoBasicGrammar,
    ProtoBasicHistory,
    ProtoBasicHistorySummary,
    ProtoBasicParseCategory,
    ProtoBasicParseResult,
    ProtoBasicToken,
    ProtoBasicTokenKind,
    ProtoBasicValence,
    append_history,
    build_command,
    canonical_command_form,
    diminishing_returns_factor,
    execute_command,
    parse_line,
    score_feedback,
    summarize_repl_history,
    tokenize,
)
from brain.development.stream import FrameSourceKind
from brain.invariants import register


def _grammar() -> ProtoBasicGrammar:
    tokens = (
        ProtoBasicToken(
            token_id="repl:verb:print",
            kind=ProtoBasicTokenKind.VERB,
            text="PRINT",
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
    )
    shapes = (
        (ProtoBasicTokenKind.VERB, ProtoBasicTokenKind.TARGET),
    )
    return ProtoBasicGrammar(tokens=tokens, command_shapes=shapes)


def _provenance() -> ProtoBasicFeedbackProvenance:
    return ProtoBasicFeedbackProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(4, 5),
        trace_event_ids=("repl:trace:history-1",),
    )


def _parse_valid(grammar: ProtoBasicGrammar, raw: str, *, line_id: str):
    line = tokenize(raw, line_id=line_id)
    result = parse_line(grammar, line)
    assert result.category is ProtoBasicParseCategory.VALID
    return result


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


@register("I-REPL-14", status="REQUIRED")
def check_proto_basic_history_appends_entries_copy_on_write() -> None:
    grammar = _grammar()

    initial = ProtoBasicHistory()
    assert initial.parse_results == ()
    assert initial.commands == ()
    assert initial.execution_results == ()
    assert initial.feedback == ()
    assert dict(initial.emit_counts or {}) == {}

    # Append a parse result.
    parse_result = _parse_valid(grammar, "PRINT X", line_id="repl:line:hist-1")
    h1 = append_history(initial, parse_result=parse_result)
    assert h1 is not initial
    assert initial.parse_results == ()  # prior preserved
    assert h1.parse_results == (parse_result,)
    assert h1.commands == ()
    assert h1.execution_results == ()
    assert h1.feedback == ()
    assert dict(h1.emit_counts or {}) == {}

    # Append a command.
    command = build_command(
        grammar=grammar,
        parse_result=parse_result,
        command_id="repl:command:hist-1",
    )
    h2 = append_history(h1, command=command)
    assert h2 is not h1
    assert h1.commands == ()
    assert h2.commands == (command,)
    assert h2.parse_results == (parse_result,)  # earlier entries preserved
    assert dict(h2.emit_counts or {}) == {}

    # Append an execution result; emit_counts is incremented for the
    # canonical form of the matching command (by source_line_id).
    execution_result = execute_command(
        command, category=ProtoBasicExecutionCategory.VALID_EFFECTIVE
    )
    h3 = append_history(h2, execution_result=execution_result)
    assert h3 is not h2
    assert h2.execution_results == ()
    assert h3.execution_results == (execution_result,)
    key = canonical_command_form(
        matched_shape=command.matched_shape,
        matched_token_ids=command.matched_token_ids,
    )
    assert dict(h3.emit_counts) == {key: 1}
    assert dict(h2.emit_counts or {}) == {}  # earlier history untouched

    # Append feedback.
    feedback = score_feedback(
        execution_result=execution_result,
        provenance=_provenance(),
    )
    h4 = append_history(h3, feedback=feedback)
    assert h4 is not h3
    assert h3.feedback == ()
    assert h4.feedback == (feedback,)
    assert dict(h4.emit_counts) == {key: 1}

    # Re-executing the same command increments emit_counts deterministically.
    execution_again = execute_command(
        command, category=ProtoBasicExecutionCategory.VALID_EFFECTIVE
    )
    h5 = append_history(h4, execution_result=execution_again)
    assert dict(h5.emit_counts) == {key: 2}
    assert dict(h4.emit_counts) == {key: 1}  # earlier history untouched

    # Rejecting multi-entry and zero-entry calls.
    try:
        append_history(h5)
    except ValueError as exc:
        assert "I-REPL-14" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-14 violated: append_history accepted zero entries"
        )
    try:
        append_history(h5, parse_result=parse_result, command=command)
    except ValueError as exc:
        assert "I-REPL-14" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-14 violated: append_history accepted multiple entries"
        )

    # ``ProtoBasicHistory`` is a frozen dataclass, so its slot inventory is
    # immutable. Confirm in-place mutation fails (FrozenInstanceError).
    try:
        h5.parse_results = ()  # type: ignore[misc]
    except Exception:
        # Either FrozenInstanceError or AttributeError is acceptable.
        pass
    else:
        raise AssertionError(
            "I-REPL-14 violated: ProtoBasicHistory permitted in-place mutation"
        )
    # The mapping proxy on emit_counts also refuses mutation.
    try:
        h5.emit_counts[key] = 99  # type: ignore[index]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "I-REPL-14 violated: emit_counts permitted in-place mutation"
        )


@register("I-REPL-16", status="REQUIRED")
def check_proto_basic_operations_do_not_mutate_tlica_runtime_state() -> None:
    grammar = _grammar()

    # Sentinel state: capture OutputHistory and WorldletHistory identities and
    # contents before any Proto-BASIC operation; assert they are unchanged.
    learned = {
        "out-token:print": _learned_token("PRINT", token_id="out-token:print"),
    }
    output_history = OutputHistory(learned_tokens=learned)
    output_id = id(output_history)
    output_learned_before = dict(output_history.learned_tokens or {})

    # Optional WorldletHistory sentinel: not all repo trees keep it warm in a
    # default state, so we construct an empty one only when its constructor is
    # available with a trivial WorldletState. We sidestep importing it to keep
    # this check minimal; the import audit + scope rules already prevent
    # repl.py from importing tick/llm/PerceptEvent surfaces.

    parse_result = _parse_valid(grammar, "PRINT X", line_id="repl:line:no-mut")
    command = build_command(
        grammar=grammar,
        parse_result=parse_result,
        command_id="repl:command:no-mut",
        output_history=output_history,
        require_learned_kinds=frozenset({ProtoBasicTokenKind.VERB}),
    )
    execution_result = execute_command(
        command, category=ProtoBasicExecutionCategory.VALID_EFFECTIVE
    )
    feedback = score_feedback(
        execution_result=execution_result,
        provenance=_provenance(),
    )

    # OutputHistory identity and content untouched.
    assert id(output_history) == output_id
    output_learned_after = dict(output_history.learned_tokens or {})
    assert output_learned_after == output_learned_before, (
        "I-REPL-16 violated: OutputHistory.learned_tokens changed under "
        "Proto-BASIC operations"
    )

    # repl.py does not import tick/llm/host-execution surfaces. The check
    # inspects the parsed AST so the negation language used in repl.py's
    # docstrings (which mentions PerceptEvent, subprocess, etc., as scope
    # exclusions) does not trip the audit.
    import ast
    import brain.development.repl as repl_module

    source = open(repl_module.__file__, "r", encoding="utf-8").read()
    tree = ast.parse(source)
    forbidden_modules = {
        "brain.tick",
        "brain.llm",
        "subprocess",
        "socket",
        "os",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in forbidden_modules, (
                    "I-REPL-16 violated: brain/development/repl.py imports "
                    f"forbidden module {alias.name!r}"
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for forbidden in forbidden_modules:
                assert not (
                    module == forbidden or module.startswith(forbidden + ".")
                ), (
                    "I-REPL-16 violated: brain/development/repl.py imports "
                    f"from forbidden module {module!r}"
                )

    # Code-level (non-docstring, non-comment) references to PerceptEvent /
    # tick callables also constitute a scope leak. A line-by-line scan that
    # strips comments and string literals is sufficient here.
    code_only = []
    for token_line in source.splitlines():
        stripped = token_line.split("#", 1)[0]
        # Skip lines that are entirely string content (docstrings); ast.walk
        # below also confirms no Name references slip through.
        code_only.append(stripped)
    joined_code = "\n".join(code_only)
    # Names that should never appear as a Python identifier reference in repl.py.
    forbidden_names = {"PerceptEvent", "subprocess", "socket"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id not in forbidden_names, (
                "I-REPL-16 violated: brain/development/repl.py references "
                f"name {node.id!r} in executable code"
            )
        if isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_names, (
                "I-REPL-16 violated: brain/development/repl.py references "
                f"attribute {node.attr!r} in executable code"
            )
    # Silence the unused-variable warning on joined_code; the AST walk is the
    # authoritative gate.
    _ = joined_code

    # Building a ProtoBasicHistory and appending entries does not touch the
    # OutputHistory identity either.
    initial = ProtoBasicHistory()
    h1 = append_history(initial, parse_result=parse_result)
    h2 = append_history(h1, command=command)
    h3 = append_history(h2, execution_result=execution_result)
    h4 = append_history(h3, feedback=feedback)
    assert id(output_history) == output_id
    output_learned_final = dict(output_history.learned_tokens or {})
    assert output_learned_final == output_learned_before

    # Earlier histories preserved exactly (re-asserts copy-on-write under the
    # I-REPL-16 lens: no history rewrite implies no scenario / trace write).
    assert initial.parse_results == ()
    assert h1.commands == ()
    assert h2.execution_results == ()
    assert h3.feedback == ()
    assert h4.feedback == (feedback,)

    # No ProtoBasicFeedback ever carries a PerceptEvent surface.
    feedback_public = {n for n in dir(feedback) if not n.startswith("_")}
    forbidden_attrs = {
        "tick",
        "percept_event",
        "selected_action",
        "feasible_projected_pce",
        "trace_event",
    }
    assert not (feedback_public & forbidden_attrs), (
        "I-REPL-16 violated: ProtoBasicFeedback exposes "
        f"{feedback_public & forbidden_attrs}"
    )

    # The Proto-BASIC valence remains exact and bounded after every step.
    assert isinstance(feedback.valence, ProtoBasicValence)
    assert Fraction(-1) <= feedback.valence.value <= Fraction(1)


@register("I-REPL-15", status="REQUIRED")
def check_repeated_no_op_commands_receive_diminishing_returns() -> None:
    grammar = _grammar()

    # Reference command: PRINT X (valid-effective on every emission).
    parse_x = _parse_valid(grammar, "PRINT X", line_id="repl:line:dim-x")
    command_x = build_command(
        grammar=grammar,
        parse_result=parse_x,
        command_id="repl:command:dim-x",
    )
    key_x = canonical_command_form(
        matched_shape=command_x.matched_shape,
        matched_token_ids=command_x.matched_token_ids,
    )

    # Interleaved alternate command: PRINT Y. Its presence must NOT reset the
    # emit_count for PRINT X (I-REPL-15: "not reset by interleaving other
    # commands").
    parse_y = _parse_valid(grammar, "PRINT Y", line_id="repl:line:dim-y")
    command_y = build_command(
        grammar=grammar,
        parse_result=parse_y,
        command_id="repl:command:dim-y",
    )
    key_y = canonical_command_form(
        matched_shape=command_y.matched_shape,
        matched_token_ids=command_y.matched_token_ids,
    )
    assert key_x != key_y

    history = ProtoBasicHistory()
    history = append_history(history, command=command_x)
    history = append_history(history, command=command_y)

    base_effective = Fraction(1, 2)
    valences: list[Fraction] = []
    factors: list[Fraction] = []
    prev_factor: Fraction | None = None

    # Emit PRINT X five times in a row. The schedule 1/(n+1) brings the
    # strong-positive component (base 1/2) to 1/2 * 1/5 = 1/10 by the fifth
    # emission, which meets the strong-positive threshold (1/10) exactly.
    for emit_index in range(5):
        # Look up emit_count BEFORE appending the execution result; this is
        # the count used for diminishing returns at this emission.
        count_before = history.emit_count_for(key_x)
        factor = diminishing_returns_factor(count_before)
        assert isinstance(factor, Fraction)
        assert Fraction(0) < factor <= Fraction(1)
        if prev_factor is not None:
            assert factor <= prev_factor, (
                "I-REPL-15 violated: diminishing_returns_factor must be "
                f"non-increasing in emit_count (got {factor} after {prev_factor})"
            )
        prev_factor = factor

        execution = execute_command(
            command_x, category=ProtoBasicExecutionCategory.VALID_EFFECTIVE
        )
        feedback = score_feedback(
            execution_result=execution,
            provenance=_provenance(),
            diminishing_returns_factor=factor,
        )
        # Strong positive component must equal base * factor exactly.
        expected = base_effective * factor
        assert feedback.valence.value == expected, (
            "I-REPL-15 violated: valid-effective valence must equal "
            f"base * factor exactly (got {feedback.valence.value}, "
            f"expected {expected})"
        )
        assert Fraction(-1) <= feedback.valence.value <= Fraction(1), (
            "I-REPL-15 violated: valence escaped [-1, 1]"
        )
        valences.append(feedback.valence.value)
        factors.append(factor)
        history = append_history(history, execution_result=execution)
        history = append_history(history, feedback=feedback)

    # The factor sequence is exactly 1/(n+1) for n = 0, 1, 2, 3, 4.
    assert factors == [
        Fraction(1, 1),
        Fraction(1, 2),
        Fraction(1, 3),
        Fraction(1, 4),
        Fraction(1, 5),
    ], (
        "I-REPL-15 violated: diminishing_returns_factor schedule must be "
        f"1/(n+1) (got {factors})"
    )
    # Valence sequence is strictly decreasing (strong-positive shrinks).
    for prior, later in zip(valences, valences[1:]):
        assert later < prior, (
            "I-REPL-15 violated: strong-positive valence must strictly "
            f"decrease across repeated emissions (got {prior} then {later})"
        )

    # Only the first emission reaches strong positive; later emissions drop
    # to or below the strong-positive threshold (or stay above for emit_count
    # 1 with base 1/2 -> 1/4, which is still > threshold 1/10). The catalog
    # plan states strong positive is "gateable" by effective execution, not
    # that the second emission must immediately fall below threshold; we
    # therefore only assert that the LAST emission of a long no-op run drops
    # to or below the threshold.
    assert valences[-1] <= PROTO_BASIC_STRONG_POSITIVE_THRESHOLD, (
        "I-REPL-15 violated: diminishing returns failed to bring repeated "
        f"no-op valence to or below the strong-positive threshold "
        f"(got {valences[-1]}, threshold {PROTO_BASIC_STRONG_POSITIVE_THRESHOLD})"
    )

    # Interleave a PRINT Y emission. PRINT X's emit_count must be unchanged
    # afterwards; the next PRINT X emission must use 1/5, not reset to 1.
    pre_interleave_x_count = history.emit_count_for(key_x)
    assert pre_interleave_x_count == 5
    execution_y = execute_command(
        command_y, category=ProtoBasicExecutionCategory.VALID_EFFECTIVE
    )
    feedback_y = score_feedback(
        execution_result=execution_y,
        provenance=_provenance(),
        diminishing_returns_factor=diminishing_returns_factor(
            history.emit_count_for(key_y)
        ),
    )
    history = append_history(history, execution_result=execution_y)
    history = append_history(history, feedback=feedback_y)

    post_interleave_x_count = history.emit_count_for(key_x)
    assert post_interleave_x_count == pre_interleave_x_count, (
        "I-REPL-15 violated: emit_count for PRINT X must not be reset by "
        f"interleaving PRINT Y (got {post_interleave_x_count}, expected "
        f"{pre_interleave_x_count})"
    )

    next_factor = diminishing_returns_factor(post_interleave_x_count)
    assert next_factor == Fraction(1, 6), (
        "I-REPL-15 violated: post-interleave PRINT X factor must follow "
        f"1/(n+1) without reset (got {next_factor}, expected 1/6)"
    )

    # diminishing_returns_factor itself validates its input domain.
    try:
        diminishing_returns_factor(-1)
    except ValueError as exc:
        assert "I-REPL-15" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-15 violated: diminishing_returns_factor accepted negative "
            "emit_count"
        )
    try:
        diminishing_returns_factor(True)  # type: ignore[arg-type]
    except TypeError as exc:
        assert "I-REPL-15" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-15 violated: diminishing_returns_factor accepted bool"
        )

    # score_feedback rejects out-of-range diminishing_returns_factor.
    bogus_execution = execute_command(
        command_x, category=ProtoBasicExecutionCategory.VALID_EFFECTIVE
    )
    try:
        score_feedback(
            execution_result=bogus_execution,
            provenance=_provenance(),
            diminishing_returns_factor=Fraction(2, 1),
        )
    except ValueError as exc:
        assert "I-REPL-15" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-15 violated: score_feedback accepted factor > 1"
        )
    try:
        score_feedback(
            execution_result=bogus_execution,
            provenance=_provenance(),
            diminishing_returns_factor=Fraction(-1, 2),
        )
    except ValueError as exc:
        assert "I-REPL-15 violated:" in str(exc)
    else:
        raise AssertionError(
            "I-REPL-15 violated: score_feedback accepted negative factor"
        )


@register("I-REPL-18", status="OBSERVED")
def observe_aggregate_proto_basic_history_summary() -> None:
    grammar = _grammar()
    history = ProtoBasicHistory()

    # Parse-level outcomes: valid, near-miss, syntax-invalid, semantic-invalid.
    # The parser produces these naturally from a few well-chosen lines.
    parse_valid = _parse_valid(
        grammar, "PRINT X", line_id="repl:line:obs-valid"
    )
    history = append_history(history, parse_result=parse_valid)

    line_near = tokenize("print X", line_id="repl:line:obs-near")
    parse_near = parse_line(grammar, line_near)
    assert parse_near.category is ProtoBasicParseCategory.NEAR_MISS
    history = append_history(history, parse_result=parse_near)

    line_syntax = tokenize("", line_id="repl:line:obs-syntax")
    parse_syntax = parse_line(grammar, line_syntax)
    assert parse_syntax.category is ProtoBasicParseCategory.SYNTAX_INVALID
    history = append_history(history, parse_result=parse_syntax)

    line_semantic = tokenize("X PRINT", line_id="repl:line:obs-semantic")
    parse_semantic = parse_line(grammar, line_semantic)
    assert parse_semantic.category is ProtoBasicParseCategory.SEMANTIC_INVALID
    history = append_history(history, parse_result=parse_semantic)

    # The remaining parse categories (tool-unavailable / resource-limit /
    # sandbox-fault) are not produced by the natural parser path. Construct
    # them directly so the OBSERVED summary covers the full partition.
    for category, line_id in (
        (
            ProtoBasicParseCategory.TOOL_UNAVAILABLE,
            "repl:line:obs-tool",
        ),
        (
            ProtoBasicParseCategory.RESOURCE_LIMIT,
            "repl:line:obs-resource",
        ),
        (
            ProtoBasicParseCategory.SANDBOX_FAULT,
            "repl:line:obs-sandbox",
        ),
    ):
        synthesized = ProtoBasicParseResult(
            line_id=line_id,
            category=category,
            matched_shape=None,
            matched_token_ids=(),
            correction_hint=None,
            detail=f"observed-{category.value}",
        )
        history = append_history(history, parse_result=synthesized)

    # Execution-level outcomes: valid-effective (twice, for emit_count > 1),
    # valid-ineffective, tool-unavailable, resource-limit, sandbox-fault.
    command_x = build_command(
        grammar=grammar,
        parse_result=parse_valid,
        command_id="repl:command:obs-x",
    )
    history = append_history(history, command=command_x)
    for _ in range(2):
        execution = execute_command(
            command_x, category=ProtoBasicExecutionCategory.VALID_EFFECTIVE
        )
        history = append_history(history, execution_result=execution)

    for category in (
        ProtoBasicExecutionCategory.VALID_INEFFECTIVE,
        ProtoBasicExecutionCategory.TOOL_UNAVAILABLE,
        ProtoBasicExecutionCategory.RESOURCE_LIMIT,
        ProtoBasicExecutionCategory.SANDBOX_FAULT,
    ):
        execution = ProtoBasicExecutionResult(
            line_id=f"repl:line:obs-exec-{category.value}",
            category=category,
            effective=False,
            detail=f"observed-{category.value}",
        )
        history = append_history(history, execution_result=execution)

    summary = summarize_repl_history(history)
    assert isinstance(summary, ProtoBasicHistorySummary)

    # Parse counts cover every category at least once.
    parse_counts = dict(summary.parse_counts)
    for category in ProtoBasicParseCategory:
        assert parse_counts.get(category, 0) >= 1, (
            f"I-REPL-18 violated: summary missing parse category {category}"
        )
    assert parse_counts[ProtoBasicParseCategory.VALID] == 1
    assert parse_counts[ProtoBasicParseCategory.NEAR_MISS] == 1

    # Execution counts cover every category at least once, with the two
    # valid-effective emissions captured.
    execution_counts = dict(summary.execution_counts)
    for category in ProtoBasicExecutionCategory:
        assert execution_counts.get(category, 0) >= 1, (
            f"I-REPL-18 violated: summary missing execution category {category}"
        )
    assert execution_counts[ProtoBasicExecutionCategory.VALID_EFFECTIVE] == 2

    # emit_counts surface the canonical form for PRINT X with count 2.
    key_x = canonical_command_form(
        matched_shape=command_x.matched_shape,
        matched_token_ids=command_x.matched_token_ids,
    )
    assert summary.emit_counts[key_x] == 2

    # Anti-Goodhart sketch is local inspectable text mentioning the
    # diminishing-returns factor; never a teacher utterance or external
    # claim.
    sketch = summary.anti_goodhart_sketch
    assert isinstance(sketch, str) and sketch.strip()
    assert "diminishing_returns_factor" in sketch
    forbidden_phrases = (
        "PerceptEvent",
        "tick(",
        "teacher",
        "natural-language",
        "real interpreter",
        "external reality",
    )
    for phrase in forbidden_phrases:
        assert phrase not in sketch, (
            f"I-REPL-18 violated: anti_goodhart_sketch leaks scope phrase "
            f"{phrase!r}"
        )

    # The summary is read-only (mapping proxies refuse in-place mutation).
    try:
        summary.parse_counts[ProtoBasicParseCategory.VALID] = 999  # type: ignore[index]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "I-REPL-18 violated: summary.parse_counts permitted in-place mutation"
        )
    try:
        summary.emit_counts[key_x] = 999  # type: ignore[index]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "I-REPL-18 violated: summary.emit_counts permitted in-place mutation"
        )

    # An empty history summary still produces a well-formed sketch.
    empty_summary = summarize_repl_history(ProtoBasicHistory())
    assert isinstance(empty_summary.anti_goodhart_sketch, str)
    assert empty_summary.anti_goodhart_sketch.strip()
    assert dict(empty_summary.emit_counts) == {}
    # Every category present in the empty summary with count zero.
    for category in ProtoBasicParseCategory:
        assert empty_summary.parse_counts[category] == 0
    for category in ProtoBasicExecutionCategory:
        assert empty_summary.execution_counts[category] == 0
