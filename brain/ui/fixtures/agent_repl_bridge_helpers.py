"""Phase 3.22 Agent REPL bridge fixture.

Drives ``I-AGENTLOOP-01`` (REQUIRED). Audits the bounded pure helpers
in ``brain.development.agent_repl_bridge`` end-to-end:

* the default grammar handle constructs and is value-equal across
  two calls,
* valid input flows through tokenize -> parse -> build -> execute ->
  feedback with the correct deterministic outputs,
* near-miss input lands in NEAR_MISS with a bounded correction-hint
  summary string,
* syntax-invalid input lands in SYNTAX_INVALID without mutating
  command / execution history,
* repeated valid-effective input produces diminishing-returns
  feedback (1/(n+1) factor),
* ``summarize_repl_for_agent`` returns a bounded printable summary
  consistent with the underlying ``summarize_repl_history``,
* every produced string is non-claim-clean,
* two independent invocations on identical inputs produce
  bit-identical ``AgentReplLineResult`` records (determinism).

The audit consumes zero real model calls; no `OperatorSession` is
constructed; no kernel tick is invoked.
"""
from __future__ import annotations

from fractions import Fraction

from brain.development.agent_repl_bridge import (
    AGENT_REPL_LINE_ID_PREFIX,
    AGENT_REPL_MAX_INPUT_LEN,
    AgentReplBridgeSummary,
    AgentReplGrammarHandle,
    AgentReplLineResult,
    MODULE_PRODUCED_STRINGS,
    build_default_agent_repl_grammar,
    run_repl_line,
    summarize_repl_for_agent,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.repl import (
    PROTO_BASIC_STRONG_POSITIVE_THRESHOLD,
    ProtoBasicHistory,
)
from brain.invariants import register


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-AGENTLOOP-01", status="REQUIRED")
def check_agent_repl_bridge_helpers() -> None:
    """Audit the agent REPL bridge helpers end-to-end."""

    # 1. Default grammar handle is constructible and stable.
    handle_a = build_default_agent_repl_grammar()
    handle_b = build_default_agent_repl_grammar()
    assert isinstance(handle_a, AgentReplGrammarHandle), (
        "I-AGENTLOOP-01 violated: build_default_agent_repl_grammar must "
        "return an AgentReplGrammarHandle"
    )
    assert handle_a == handle_b, (
        "I-AGENTLOOP-01 violated: default grammar handle drifted across "
        "two construction calls"
    )
    grammar = handle_a.grammar
    expected_token_texts = {"EMIT", "NOTE", "ALPHA", "BETA", "ONE", "TWO"}
    actual_token_texts = {t.text for t in grammar.tokens}
    assert actual_token_texts == expected_token_texts, (
        "I-AGENTLOOP-01 violated: default grammar token-text set drifted "
        f"(got {sorted(actual_token_texts)!r}, expected "
        f"{sorted(expected_token_texts)!r})"
    )

    # 2. Valid input: full pipeline.
    line_id_v = f"{AGENT_REPL_LINE_ID_PREFIX}valid-001"
    valid = run_repl_line(
        handle=handle_a,
        history=ProtoBasicHistory(),
        raw_text="EMIT ALPHA",
        line_id=line_id_v,
    )
    assert isinstance(valid, AgentReplLineResult)
    assert valid.parse_category_value == "valid"
    assert valid.execution_category_value == "valid-effective"
    assert valid.effective is True
    assert valid.feedback_valence_str == "1/2"
    assert valid.feedback_is_strong_positive is True
    assert valid.diminishing_returns_factor_str == "1/1"
    assert valid.near_miss_hint_summary == ""
    assert valid.command_canonical.startswith("shape=verb|target;tokens=")
    # History gained a parse_result, a command, an execution_result,
    # and a feedback record.
    assert len(valid.history.parse_results) == 1
    assert len(valid.history.commands) == 1
    assert len(valid.history.execution_results) == 1
    assert len(valid.history.feedback) == 1

    # 3. Near-miss input.
    line_id_n = f"{AGENT_REPL_LINE_ID_PREFIX}near-001"
    near = run_repl_line(
        handle=handle_a,
        history=ProtoBasicHistory(),
        raw_text="emit alpha",
        line_id=line_id_n,
    )
    assert near.parse_category_value == "near-miss"
    assert near.execution_category_value == ""
    assert near.effective is False
    # Near-miss valence is non-positive and below the strong threshold.
    assert Fraction(*map(int, near.feedback_valence_str.split("/"))) < (
        PROTO_BASIC_STRONG_POSITIVE_THRESHOLD
    )
    assert near.feedback_is_strong_positive is False
    assert near.near_miss_hint_summary.startswith("hint kind=")
    # No command/execution history was added.
    assert len(near.history.commands) == 0
    assert len(near.history.execution_results) == 0
    assert len(near.history.parse_results) == 1
    assert len(near.history.feedback) == 1

    # 4. Syntax-invalid input.
    line_id_s = f"{AGENT_REPL_LINE_ID_PREFIX}synt-001"
    synt = run_repl_line(
        handle=handle_a,
        history=ProtoBasicHistory(),
        raw_text="",
        line_id=line_id_s,
    )
    assert synt.parse_category_value == "syntax-invalid"
    assert synt.execution_category_value == ""
    assert synt.effective is False
    assert synt.near_miss_hint_summary == ""
    assert len(synt.history.commands) == 0
    assert len(synt.history.execution_results) == 0

    # 5. Diminishing-returns sequence: feedback valence shrinks as
    # 1/(n+1) on repeated valid-effective emissions.
    history = ProtoBasicHistory()
    valences: list[Fraction] = []
    drfs: list[Fraction] = []
    for index in range(5):
        line_id = f"{AGENT_REPL_LINE_ID_PREFIX}rep-{index:03d}"
        result = run_repl_line(
            handle=handle_a,
            history=history,
            raw_text="EMIT ALPHA",
            line_id=line_id,
        )
        valences.append(
            Fraction(*map(int, result.feedback_valence_str.split("/")))
        )
        drfs.append(
            Fraction(*map(int, result.diminishing_returns_factor_str.split("/")))
        )
        history = result.history
    # Diminishing-returns factor sequence is non-increasing.
    for i in range(1, len(drfs)):
        assert drfs[i] <= drfs[i - 1]
    # Valences are non-increasing on repeated valid-effective input.
    for i in range(1, len(valences)):
        assert valences[i] <= valences[i - 1]
    # The first valence equals base 1/2; subsequent valences are
    # 1/2 * 1/(n+1) where n is the prior emit count.
    expected = [Fraction(1, 2) * Fraction(1, n + 1) for n in range(5)]
    assert valences == expected, (
        f"I-AGENTLOOP-01 violated: valence sequence drifted "
        f"(got {valences}, expected {expected})"
    )

    # 6. summarize_repl_for_agent produces a bounded printable summary.
    summary = summarize_repl_for_agent(history)
    assert isinstance(summary, AgentReplBridgeSummary)
    assert summary.parse_valid_count == 5
    assert summary.execution_valid_effective_count == 5
    assert summary.emit_total == 5
    assert summary.most_repeated_emit_count == 5
    assert summary.summary_line.startswith("agent_repl ")
    assert summary.summary_line.isprintable()
    assert _has_forbidden(summary.summary_line) is None

    # 7. MODULE_PRODUCED_STRINGS audit.
    for produced in MODULE_PRODUCED_STRINGS:
        assert isinstance(produced, str) and produced.isprintable()
        assert _has_forbidden(produced) is None, (
            "I-AGENTLOOP-01 violated: MODULE_PRODUCED_STRINGS entry "
            f"{produced!r} contains a forbidden non-claim term"
        )

    # 8. Determinism: two independent invocations on identical inputs
    # produce equal AgentReplLineResult records and equal final
    # histories.
    a = run_repl_line(
        handle=handle_a,
        history=ProtoBasicHistory(),
        raw_text="EMIT ALPHA",
        line_id=f"{AGENT_REPL_LINE_ID_PREFIX}det-001",
    )
    b = run_repl_line(
        handle=handle_a,
        history=ProtoBasicHistory(),
        raw_text="EMIT ALPHA",
        line_id=f"{AGENT_REPL_LINE_ID_PREFIX}det-001",
    )
    assert a == b, "I-AGENTLOOP-01 violated: bridge is not deterministic"
    assert a.history == b.history

    # 9. Bound enforcement on raw_text.
    over = "X" * (AGENT_REPL_MAX_INPUT_LEN + 1)
    raised = False
    try:
        run_repl_line(
            handle=handle_a,
            history=ProtoBasicHistory(),
            raw_text=over,
            line_id=f"{AGENT_REPL_LINE_ID_PREFIX}over",
        )
    except ValueError:
        raised = True
    assert raised, (
        "I-AGENTLOOP-01 violated: bridge accepted oversize raw_text"
    )

    # 10. line_id prefix discipline.
    raised = False
    try:
        run_repl_line(
            handle=handle_a,
            history=ProtoBasicHistory(),
            raw_text="EMIT ALPHA",
            line_id="some:other:prefix:001",
        )
    except ValueError:
        raised = True
    assert raised, (
        "I-AGENTLOOP-01 violated: bridge accepted out-of-prefix line_id"
    )
