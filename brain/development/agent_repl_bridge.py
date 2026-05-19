"""Phase 3.22 Agent REPL bridge — pure helpers over the Proto-BASIC REPL.

This module is a strict consumer of ``brain.development.repl`` and
exposes a small bounded helper layer that the Phase 3.22 agent
communication loop can call without touching the existing
``OperatorSession`` REPL surface.

The bridge is **pure**: every helper accepts an immutable
``ProtoBasicHistory`` and returns a new immutable
``ProtoBasicHistory`` plus a bounded result record. No global state.
No ``OperatorSession`` reference at this layer. No host execution,
subprocess, file I/O, network I/O, randomness, time source, or LLM
import. Bit-deterministic across two invocations.

Drives ``I-AGENTLOOP-01`` (Phase 3 Engineering hypothesis).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional

from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.repl import (
    PROTO_BASIC_MAX_LINE_LENGTH,
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


# ---------------------------------------------------------------------------
# Bounded constants.
# ---------------------------------------------------------------------------

AGENT_REPL_MAX_INPUT_LEN: int = PROTO_BASIC_MAX_LINE_LENGTH
AGENT_REPL_LINE_ID_PREFIX: str = "agent-repl:line:"
AGENT_REPL_COMMAND_ID_PREFIX: str = "agent-repl:command:"
AGENT_REPL_PROVENANCE_CHANNEL: str = "agent-repl-bridge"
AGENT_REPL_BRIDGE_VERSION: str = "phase3.22.v1"

#: Maximum number of lines an agent loop call may process through the bridge
#: in a single invocation. The bridge is one-line-per-call, but the agent
#: loop may call it repeatedly inside one operator interaction. The cap
#: keeps the bridge from being used as an unbounded driver.
AGENT_REPL_MAX_LINES_PER_INVOCATION: int = 1


# ---------------------------------------------------------------------------
# Module-produced strings (subject to forbidden-term audit).
# ---------------------------------------------------------------------------

MODULE_PRODUCED_STRINGS: tuple[str, ...] = (
    AGENT_REPL_LINE_ID_PREFIX,
    AGENT_REPL_COMMAND_ID_PREFIX,
    AGENT_REPL_PROVENANCE_CHANNEL,
    AGENT_REPL_BRIDGE_VERSION,
)


def _text_has_forbidden_term(text: str) -> Optional[str]:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


# ---------------------------------------------------------------------------
# Grammar handle.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AgentReplGrammarHandle:
    """A frozen wrapper around a ``ProtoBasicGrammar``.

    The agent loop holds one handle for the duration of a session. The
    bridge never mutates the underlying grammar.
    """

    grammar: ProtoBasicGrammar
    handle_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.grammar, ProtoBasicGrammar):
            raise TypeError(
                "I-AGENTLOOP-01 violated: AgentReplGrammarHandle.grammar must "
                "be a ProtoBasicGrammar"
            )
        if (
            not isinstance(self.handle_id, str)
            or not self.handle_id
            or not self.handle_id.isprintable()
            or len(self.handle_id) > 64
        ):
            raise ValueError(
                "I-AGENTLOOP-01 violated: AgentReplGrammarHandle.handle_id "
                "must be non-empty printable text under 64 chars"
            )


def build_default_agent_repl_grammar(
    *, handle_id: str = "agent-repl:grammar:default"
) -> AgentReplGrammarHandle:
    """Construct the closed default Proto-BASIC grammar used by the bridge.

    Tokens (exact enumeration; verbs / targets / objects):

      * verbs   : ``EMIT``, ``NOTE``
      * targets : ``ALPHA``, ``BETA``
      * objects : ``ONE``, ``TWO``

    Command shapes:

      * (VERB, TARGET)
      * (VERB, TARGET, OBJECT)

    Returns a frozen handle. Two calls return equal handles (the
    underlying grammar is value-equal).
    """
    tokens = (
        ProtoBasicToken(
            token_id="agent-repl:verb:emit",
            kind=ProtoBasicTokenKind.VERB,
            text="EMIT",
        ),
        ProtoBasicToken(
            token_id="agent-repl:verb:note",
            kind=ProtoBasicTokenKind.VERB,
            text="NOTE",
        ),
        ProtoBasicToken(
            token_id="agent-repl:target:alpha",
            kind=ProtoBasicTokenKind.TARGET,
            text="ALPHA",
        ),
        ProtoBasicToken(
            token_id="agent-repl:target:beta",
            kind=ProtoBasicTokenKind.TARGET,
            text="BETA",
        ),
        ProtoBasicToken(
            token_id="agent-repl:object:one",
            kind=ProtoBasicTokenKind.OBJECT,
            text="ONE",
        ),
        ProtoBasicToken(
            token_id="agent-repl:object:two",
            kind=ProtoBasicTokenKind.OBJECT,
            text="TWO",
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
    grammar = ProtoBasicGrammar(tokens=tokens, command_shapes=shapes)
    return AgentReplGrammarHandle(grammar=grammar, handle_id=handle_id)


# ---------------------------------------------------------------------------
# Bridge result record.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AgentReplLineResult:
    """One bounded result record for one bridge call.

    Fields are deterministically derived from the input + grammar +
    prior history. Strings only, primitive ints; no Fraction leaks
    upward (the bridge value-converts ``Fraction`` instances to
    bounded printable strings at this boundary).
    """

    line_id: str
    parse_category_value: str
    command_canonical: str
    execution_category_value: str
    effective: bool
    feedback_valence_str: str
    feedback_is_strong_positive: bool
    near_miss_hint_summary: str
    diminishing_returns_factor_str: str
    history: ProtoBasicHistory

    def __post_init__(self) -> None:
        for name, value in (
            ("line_id", self.line_id),
            ("parse_category_value", self.parse_category_value),
            ("command_canonical", self.command_canonical),
            ("execution_category_value", self.execution_category_value),
            ("feedback_valence_str", self.feedback_valence_str),
            ("near_miss_hint_summary", self.near_miss_hint_summary),
            ("diminishing_returns_factor_str",
             self.diminishing_returns_factor_str),
        ):
            if not isinstance(value, str):
                raise TypeError(
                    "I-AGENTLOOP-01 violated: AgentReplLineResult."
                    f"{name} must be a string"
                )
            if not value.isprintable() and value != "":
                raise ValueError(
                    "I-AGENTLOOP-01 violated: AgentReplLineResult."
                    f"{name} must be printable"
                )
            term = _text_has_forbidden_term(value)
            if term is not None:
                raise ValueError(
                    "I-AGENTLOOP-01 violated: AgentReplLineResult."
                    f"{name} contains forbidden non-claim term {term!r}"
                )
        if not isinstance(self.effective, bool):
            raise TypeError(
                "I-AGENTLOOP-01 violated: AgentReplLineResult.effective "
                "must be bool"
            )
        if not isinstance(self.feedback_is_strong_positive, bool):
            raise TypeError(
                "I-AGENTLOOP-01 violated: AgentReplLineResult."
                "feedback_is_strong_positive must be bool"
            )
        if not isinstance(self.history, ProtoBasicHistory):
            raise TypeError(
                "I-AGENTLOOP-01 violated: AgentReplLineResult.history "
                "must be a ProtoBasicHistory"
            )


# ---------------------------------------------------------------------------
# Bridge summary record.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AgentReplBridgeSummary:
    """A bounded printable summary of an agent-bridge REPL history.

    Reuses ``ProtoBasicHistorySummary`` internally; surfaces a small
    set of integer counters and a single bounded printable line for
    the agent loop's reply layer.
    """

    parse_valid_count: int
    parse_near_miss_count: int
    parse_syntax_invalid_count: int
    execution_valid_effective_count: int
    execution_valid_ineffective_count: int
    emit_total: int
    most_repeated_canonical: str
    most_repeated_emit_count: int
    summary_line: str

    def __post_init__(self) -> None:
        for name, value in (
            ("parse_valid_count", self.parse_valid_count),
            ("parse_near_miss_count", self.parse_near_miss_count),
            ("parse_syntax_invalid_count", self.parse_syntax_invalid_count),
            ("execution_valid_effective_count",
             self.execution_valid_effective_count),
            ("execution_valid_ineffective_count",
             self.execution_valid_ineffective_count),
            ("emit_total", self.emit_total),
            ("most_repeated_emit_count", self.most_repeated_emit_count),
        ):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(
                    "I-AGENTLOOP-01 violated: AgentReplBridgeSummary."
                    f"{name} must be int"
                )
            if value < 0:
                raise ValueError(
                    "I-AGENTLOOP-01 violated: AgentReplBridgeSummary."
                    f"{name} must be non-negative"
                )
        for name, value in (
            ("most_repeated_canonical", self.most_repeated_canonical),
            ("summary_line", self.summary_line),
        ):
            if not isinstance(value, str):
                raise TypeError(
                    "I-AGENTLOOP-01 violated: AgentReplBridgeSummary."
                    f"{name} must be str"
                )
            if value and not value.isprintable():
                raise ValueError(
                    "I-AGENTLOOP-01 violated: AgentReplBridgeSummary."
                    f"{name} must be printable"
                )
            term = _text_has_forbidden_term(value)
            if term is not None:
                raise ValueError(
                    "I-AGENTLOOP-01 violated: AgentReplBridgeSummary."
                    f"{name} contains forbidden term {term!r}"
                )


# ---------------------------------------------------------------------------
# Internal helpers.
# ---------------------------------------------------------------------------


def _fraction_to_str(value: Fraction) -> str:
    if not isinstance(value, Fraction):
        raise TypeError(
            "I-AGENTLOOP-01 violated: _fraction_to_str requires a Fraction"
        )
    return f"{value.numerator}/{value.denominator}"


def _near_miss_summary(parse_result: ProtoBasicParseResult) -> str:
    if parse_result.category is not ProtoBasicParseCategory.NEAR_MISS:
        return ""
    hint = parse_result.correction_hint
    if hint is None:
        return ""
    expected = hint.expected_token_id or ""
    return (
        f"hint kind={hint.edit_kind.value} pos={hint.edit_position} "
        f"expect={expected} dist={hint.edit_distance}"
    )


# ---------------------------------------------------------------------------
# Public bridge helpers.
# ---------------------------------------------------------------------------


def run_repl_line(
    *,
    handle: AgentReplGrammarHandle,
    history: ProtoBasicHistory,
    raw_text: str,
    line_id: str,
) -> AgentReplLineResult:
    """Bridge one operator-supplied line through the Proto-BASIC pipeline.

    Pure deterministic helper. Accepts an immutable history; returns a
    new immutable history plus a bounded result record. Never calls
    ``tick``, never invokes an LLM, never touches the filesystem,
    network, or any operator session.

    Order of operations (deterministic):

      1. tokenize raw_text into a ``ProtoBasicLine``;
      2. parse the line against the grammar;
      3. append the parse_result to history;
      4. if VALID, build a ``ProtoBasicCommand`` and append it to history;
      5. if a command was built, execute it (category =
         VALID_EFFECTIVE) and append the execution_result to history
         (this also increments the canonical-form emit count);
      6. compute the diminishing-returns factor over the post-execution
         history;
      7. score feedback over the parse_result OR the execution_result
         (execution preferred when present, with the diminishing-returns
         factor) and append the feedback to history;
      8. assemble and return ``AgentReplLineResult``.
    """
    if not isinstance(handle, AgentReplGrammarHandle):
        raise TypeError(
            "I-AGENTLOOP-01 violated: run_repl_line handle must be an "
            "AgentReplGrammarHandle"
        )
    if not isinstance(history, ProtoBasicHistory):
        raise TypeError(
            "I-AGENTLOOP-01 violated: run_repl_line history must be a "
            "ProtoBasicHistory"
        )
    if not isinstance(raw_text, str):
        raise TypeError(
            "I-AGENTLOOP-01 violated: run_repl_line raw_text must be a string"
        )
    if not isinstance(line_id, str) or not line_id:
        raise ValueError(
            "I-AGENTLOOP-01 violated: run_repl_line line_id must be a "
            "non-empty string"
        )
    if not line_id.startswith(AGENT_REPL_LINE_ID_PREFIX):
        raise ValueError(
            "I-AGENTLOOP-01 violated: run_repl_line line_id must begin with "
            f"{AGENT_REPL_LINE_ID_PREFIX!r}"
        )
    if len(raw_text) > AGENT_REPL_MAX_INPUT_LEN:
        raise ValueError(
            "I-AGENTLOOP-01 violated: run_repl_line raw_text exceeds bound "
            f"{AGENT_REPL_MAX_INPUT_LEN}"
        )

    grammar = handle.grammar
    line = tokenize(raw_text, line_id=line_id)
    parse_result = parse_line(grammar, line)
    new_history = append_history(history, parse_result=parse_result)

    command: Optional[ProtoBasicCommand] = None
    execution_result: Optional[ProtoBasicExecutionResult] = None
    command_canonical = ""
    if parse_result.category is ProtoBasicParseCategory.VALID:
        command_id = (
            f"{AGENT_REPL_COMMAND_ID_PREFIX}{line_id.rsplit(':', 1)[-1]}"
        )
        command = build_command(
            grammar=grammar,
            parse_result=parse_result,
            command_id=command_id,
        )
        command_canonical = command.canonical_form
        new_history = append_history(new_history, command=command)
        execution_result = execute_command(command)
        new_history = append_history(
            new_history, execution_result=execution_result
        )

    # Diminishing-returns factor over the post-execution history.
    if execution_result is not None and command is not None:
        emit_count = new_history.emit_count_for(command.canonical_form)
        # emit_count is the count INCLUDING this execution; the
        # diminishing-returns convention scores BEFORE the execution
        # contributes, so subtract 1 from the post-append count to
        # get the prior count.
        prior = max(0, emit_count - 1)
        drf = diminishing_returns_factor(prior)
    else:
        drf = Fraction(1, 1)

    provenance = ProtoBasicFeedbackProvenance(
        source_kind=FrameSourceKind.OPERATOR_INJECTION,
        confidence=Fraction(1, 1),
        trace_event_ids=(),
    )
    if execution_result is not None:
        feedback = score_feedback(
            execution_result=execution_result,
            provenance=provenance,
            diminishing_returns_factor=drf,
        )
    else:
        feedback = score_feedback(
            parse_result=parse_result,
            provenance=provenance,
        )
    new_history = append_history(new_history, feedback=feedback)

    valence_value: Fraction = feedback.valence.value
    is_strong = valence_value >= PROTO_BASIC_STRONG_POSITIVE_THRESHOLD

    if execution_result is not None:
        execution_category_value = execution_result.category.value
        effective = execution_result.effective
    else:
        execution_category_value = ""
        effective = False

    return AgentReplLineResult(
        line_id=line_id,
        parse_category_value=parse_result.category.value,
        command_canonical=command_canonical,
        execution_category_value=execution_category_value,
        effective=effective,
        feedback_valence_str=_fraction_to_str(valence_value),
        feedback_is_strong_positive=is_strong,
        near_miss_hint_summary=_near_miss_summary(parse_result),
        diminishing_returns_factor_str=_fraction_to_str(drf),
        history=new_history,
    )


def summarize_repl_for_agent(
    history: ProtoBasicHistory,
) -> AgentReplBridgeSummary:
    """Build a bounded printable summary from a Proto-BASIC history.

    Reuses ``summarize_repl_history`` and projects its output into a
    bounded record carrying only the integer counts and one bounded
    printable summary line. The anti-Goodhart sketch is mapped into
    a bounded printable line without forbidden non-claim terms.
    """
    if not isinstance(history, ProtoBasicHistory):
        raise TypeError(
            "I-AGENTLOOP-01 violated: summarize_repl_for_agent requires a "
            "ProtoBasicHistory"
        )
    base: ProtoBasicHistorySummary = summarize_repl_history(history)
    parse_valid = base.parse_counts.get(ProtoBasicParseCategory.VALID, 0)
    parse_near_miss = base.parse_counts.get(
        ProtoBasicParseCategory.NEAR_MISS, 0
    )
    parse_syntax_invalid = base.parse_counts.get(
        ProtoBasicParseCategory.SYNTAX_INVALID, 0
    )
    exec_valid_effective = base.execution_counts.get(
        ProtoBasicExecutionCategory.VALID_EFFECTIVE, 0
    )
    exec_valid_ineffective = base.execution_counts.get(
        ProtoBasicExecutionCategory.VALID_INEFFECTIVE, 0
    )
    emit_total = sum(base.emit_counts.values())
    if base.emit_counts:
        most_repeated, most_count = max(
            base.emit_counts.items(), key=lambda kv: (kv[1], kv[0])
        )
    else:
        most_repeated, most_count = "", 0

    summary_line = (
        f"agent_repl parse_valid={parse_valid} near_miss={parse_near_miss} "
        f"syntax_invalid={parse_syntax_invalid} "
        f"exec_effective={exec_valid_effective} "
        f"exec_ineffective={exec_valid_ineffective} "
        f"emit_total={emit_total} top={most_repeated!r}/{most_count}"
    )
    return AgentReplBridgeSummary(
        parse_valid_count=parse_valid,
        parse_near_miss_count=parse_near_miss,
        parse_syntax_invalid_count=parse_syntax_invalid,
        execution_valid_effective_count=exec_valid_effective,
        execution_valid_ineffective_count=exec_valid_ineffective,
        emit_total=emit_total,
        most_repeated_canonical=most_repeated,
        most_repeated_emit_count=most_count,
        summary_line=summary_line,
    )


__all__ = (
    "AGENT_REPL_BRIDGE_VERSION",
    "AGENT_REPL_COMMAND_ID_PREFIX",
    "AGENT_REPL_LINE_ID_PREFIX",
    "AGENT_REPL_MAX_INPUT_LEN",
    "AGENT_REPL_MAX_LINES_PER_INVOCATION",
    "AGENT_REPL_PROVENANCE_CHANNEL",
    "AgentReplBridgeSummary",
    "AgentReplGrammarHandle",
    "AgentReplLineResult",
    "MODULE_PRODUCED_STRINGS",
    "build_default_agent_repl_grammar",
    "run_repl_line",
    "summarize_repl_for_agent",
)
