"""Phase 3.22b reasoning trace construction fixture.

Drives ``I-AGENTLEARN-08`` (REQUIRED). Audits ``ReasoningTrace`` /
``ReasoningTraceStep`` construction discipline, ``new_trace_builder``
deterministic step numbering, and bounded-printable field discipline.
"""
from __future__ import annotations

from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.reasoning_trace import (
    REASONING_STEP_FIELD_MAX_LEN,
    REASONING_TRACE_MAX_STEPS,
    ReasoningStepKind,
    ReasoningTrace,
    ReasoningTraceStep,
    build_reasoning_trace,
    format_reasoning_trace_table,
    new_trace_builder,
)
from brain.invariants import register


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-AGENTLEARN-08", status="REQUIRED")
def check_reasoning_trace_construction() -> None:
    """Audit ReasoningTrace / ReasoningTraceStep discipline."""

    # 1. Build a trace via the builder.
    builder = new_trace_builder("agent-input:00001")
    builder.add(
        ReasoningStepKind.OBSERVE_INPUT,
        input_facts="len=15",
        derived_facts="path=stream",
        next_action="classify_refusal",
    )
    builder.add(
        ReasoningStepKind.CLASSIFY_REFUSAL,
        derived_facts="matched=False",
    )
    builder.add(ReasoningStepKind.EMIT_REPLY, derived_facts="sections=5")
    trace = builder.freeze()
    assert isinstance(trace, ReasoningTrace)
    assert len(trace.steps) == 3
    assert tuple(s.step_number for s in trace.steps) == (1, 2, 3)
    assert trace.step_kinds() == (
        ReasoningStepKind.OBSERVE_INPUT,
        ReasoningStepKind.CLASSIFY_REFUSAL,
        ReasoningStepKind.EMIT_REPLY,
    )

    # 2. Equivalent traces compare equal.
    again = build_reasoning_trace(
        input_id="agent-input:00001",
        steps=(
            (ReasoningStepKind.OBSERVE_INPUT, "len=15", "path=stream", "classify_refusal"),
            (ReasoningStepKind.CLASSIFY_REFUSAL, "", "matched=False", ""),
            (ReasoningStepKind.EMIT_REPLY, "", "sections=5", ""),
        ),
    )
    assert again == trace

    # 3. ReasoningTraceStep rejects overlong fields.
    raised = False
    try:
        ReasoningTraceStep(
            step_number=1,
            kind=ReasoningStepKind.OBSERVE_INPUT,
            input_facts="x" * (REASONING_STEP_FIELD_MAX_LEN + 1),
            derived_facts="",
            next_action="",
        )
    except (ValueError, TypeError):
        raised = True
    assert raised

    # 4. ReasoningTrace rejects out-of-order step numbers.
    raised = False
    try:
        ReasoningTrace(
            steps=(
                ReasoningTraceStep(
                    step_number=2,
                    kind=ReasoningStepKind.OBSERVE_INPUT,
                    input_facts="",
                    derived_facts="",
                    next_action="",
                ),
            ),
            input_id="agent-input:00001",
        )
    except (ValueError, TypeError):
        raised = True
    assert raised

    # 5. ReasoningTrace rejects empty step tuple.
    raised = False
    try:
        ReasoningTrace(steps=(), input_id="agent-input:00001")
    except (ValueError, TypeError):
        raised = True
    assert raised

    # 6. format_reasoning_trace_table produces a bounded multi-line
    # table. Each line (split on newlines) is printable.
    table = format_reasoning_trace_table(trace)
    assert table
    for line in table.split("\n"):
        assert line.isprintable()
    assert "observe_input" in table

    # 7. Trace fields contain no forbidden non-claim terms.
    for s in trace.steps:
        for text in (s.input_facts, s.derived_facts, s.next_action):
            term = _has_forbidden(text)
            assert term is None

    # 8. Builder enforces REASONING_TRACE_MAX_STEPS.
    big_builder = new_trace_builder("agent-input:overflow")
    for _ in range(REASONING_TRACE_MAX_STEPS):
        big_builder.add(ReasoningStepKind.OBSERVE_INPUT)
    raised = False
    try:
        big_builder.add(ReasoningStepKind.OBSERVE_INPUT)
    except (ValueError, TypeError):
        raised = True
    assert raised
