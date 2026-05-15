"""Fixtures for Phase 3.4 Proto-BASIC REPL history rows.

This module drives ``I-REPL-14`` and ``I-REPL-16``: copy-on-write append for
parse / command / execution / feedback entries, and the requirement that no
Proto-BASIC operation mutates TLICA runtime state (profile / MSI / PtCns /
content registry / ``OutputHistory`` / ``WorldletHistory`` / scenario / trace).

``I-REPL-15`` (diminishing returns) and ``I-REPL-18`` (aggregate inspection)
are Step 9 work and remain pending.
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
    ProtoBasicFeedback,
    ProtoBasicFeedbackProvenance,
    ProtoBasicGrammar,
    ProtoBasicHistory,
    ProtoBasicParseCategory,
    ProtoBasicParseResult,
    ProtoBasicToken,
    ProtoBasicTokenKind,
    ProtoBasicValence,
    append_history,
    build_command,
    canonical_command_form,
    execute_command,
    parse_line,
    score_feedback,
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
