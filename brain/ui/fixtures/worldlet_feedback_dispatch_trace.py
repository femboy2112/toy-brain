"""Phase 3.24 dispatch trace + worldlet feedback fixture.

Drives ``I-WFDBK-07`` (REQUIRED). Audits the dispatch tracer's
worldlet-feedback facts and mutation classification.
"""
from __future__ import annotations

from brain.development.dispatch_tracer import (
    DispatchMutationKind,
    DispatchTraceKind,
)
from brain.development.processing_window import FeedbackMode
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.commands import Command, OperatorCommand, StreamAppendPayload
from brain.ui.session import OperatorSession


_EXPECTED_MUTATION_KIND_VALUES = frozenset(
    {
        "none",
        "ui_only",
        "stream_append",
        "stream_window_internal",
        "stream_promote",
        "queue_mutation",
        "step_tick",
        "session_persistence",
        "autosave",
        "db_observe",
        "db_backup",
        "view_change",
        "quit_flag",
        "error_only",
    }
)


def _facts_lookup(facts):
    return {k: v for k, v in facts}


@register("I-WFDBK-07", status="REQUIRED")
def check_dispatch_trace_worldlet_route() -> None:
    """Audit dispatch tracer worldlet feedback recording."""

    # Closed DispatchMutationKind set is unchanged at 14 values.
    actual = frozenset(m.value for m in DispatchMutationKind)
    assert actual == _EXPECTED_MUTATION_KIND_VALUES, (
        "I-WFDBK-07 violated: DispatchMutationKind value set drifted "
        f"(got {sorted(actual)!r})"
    )

    # WORLDLET mode: dispatch trace records feedback_mode=worldlet and
    # mutation_kind=STREAM_WINDOW_INTERNAL.
    session = OperatorSession(
        state=initial_state(),
        processing_window_size=2,
        feedback_mode=FeedbackMode.WORLDLET,
    )
    session.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text="alpha worldlet trace"),
        )
    )
    report = session.latest_dispatch_trace
    assert report is not None
    assert report.mutation_kind is DispatchMutationKind.STREAM_WINDOW_INTERNAL

    # Walk every step and extract the feedback_mode + worldlet_summary_chunks
    # facts.
    feedback_mode_facts = []
    worldlet_chunk_facts = []
    for step in report.trace.steps:
        before = _facts_lookup(step.before_facts)
        after = _facts_lookup(step.after_facts)
        if "feedback_mode" in before:
            feedback_mode_facts.append(before["feedback_mode"])
        if "feedback_mode" in after:
            feedback_mode_facts.append(after["feedback_mode"])
        if "worldlet_summary_chunks" in before:
            worldlet_chunk_facts.append(before["worldlet_summary_chunks"])
        if "worldlet_summary_chunks" in after:
            worldlet_chunk_facts.append(after["worldlet_summary_chunks"])

    assert "worldlet" in feedback_mode_facts, (
        f"I-WFDBK-07 violated: dispatch trace missing feedback_mode=worldlet; "
        f"saw {feedback_mode_facts!r}"
    )
    # worldlet_summary_chunks should be 0 in pre-state (before dispatch fires
    # the rehearsals) and 2 in post-state.
    assert "0" in worldlet_chunk_facts, (
        f"I-WFDBK-07 violated: dispatch trace missing pre-state "
        f"worldlet_summary_chunks=0; saw {worldlet_chunk_facts!r}"
    )
    assert "2" in worldlet_chunk_facts, (
        f"I-WFDBK-07 violated: dispatch trace missing post-state "
        f"worldlet_summary_chunks=2; saw {worldlet_chunk_facts!r}"
    )

    # The PRE_STATE_SNAPSHOT step should specifically carry the worldlet
    # mode + count=0.
    pre_step = None
    for step in report.trace.steps:
        if step.kind is DispatchTraceKind.PRE_STATE_SNAPSHOT:
            pre_step = step
            break
    assert pre_step is not None
    pre_lookup = _facts_lookup(pre_step.before_facts)
    assert pre_lookup.get("feedback_mode") == "worldlet"
    assert pre_lookup.get("worldlet_summary_chunks") == "0"

    # The POST_STATE_SNAPSHOT step carries count=2.
    post_step = None
    for step in report.trace.steps:
        if step.kind is DispatchTraceKind.POST_STATE_SNAPSHOT:
            post_step = step
            break
    assert post_step is not None
    post_lookup = _facts_lookup(post_step.after_facts)
    assert post_lookup.get("worldlet_summary_chunks") == "2"

    # Combined PATTERN_COHERENCE_WORLDLET mode is also captured.
    session2 = OperatorSession(
        state=initial_state(),
        processing_window_size=1,
        feedback_mode=FeedbackMode.PATTERN_COHERENCE_WORLDLET,
    )
    session2.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text="alpha combined trace"),
        )
    )
    report2 = session2.latest_dispatch_trace
    assert report2 is not None
    feedback_mode_facts2 = []
    for step in report2.trace.steps:
        for k, v in step.before_facts:
            if k == "feedback_mode":
                feedback_mode_facts2.append(v)
    assert "pattern_coherence_worldlet" in feedback_mode_facts2, (
        f"I-WFDBK-07 violated: combined mode dispatch trace missing "
        f"feedback_mode=pattern_coherence_worldlet; saw {feedback_mode_facts2!r}"
    )
