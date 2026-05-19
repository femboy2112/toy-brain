"""Phase 3.24 OperatorSession worldlet feedback step + processing window.

Drives ``I-WFDBK-04`` (REQUIRED), ``I-WFDBK-05`` (REQUIRED), and
``I-WFDBK-06`` (REQUIRED).
"""
from __future__ import annotations

from fractions import Fraction

from brain.development.processing_window import FeedbackMode
from brain.development.stream import FrameSourceKind
from brain.development.worldlet import (
    WorldletAttempt,
    WorldletHistory,
    WorldletObject,
    WorldletProvenance,
    WorldletState,
    respond_worldlet,
)
from brain.invariants import register
from brain.tick import initial_state
from brain.ui.commands import Command, OperatorCommand, StreamAppendPayload
from brain.ui.session import OperatorSession


def _fresh_session(
    *, feedback_mode: FeedbackMode, window_size: int = 2,
    worldlet_history: WorldletHistory | None = None,
) -> OperatorSession:
    return OperatorSession(
        state=initial_state(),
        processing_window_size=window_size,
        feedback_mode=feedback_mode,
        worldlet_history=worldlet_history,
    )


def _append(session: OperatorSession, text: str) -> None:
    session.dispatch(
        Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text=text),
        )
    )


def _build_populated_worldlet_history() -> WorldletHistory:
    state = WorldletState(
        state_id="wld:state:test1",
        objects={
            "tgt1": WorldletObject(
                object_id="tgt1",
                label="target1",
                available=True,
                accepted_token_ids=frozenset({"tk1"}),
            ),
        },
        step_index=0,
    )
    provenance = WorldletProvenance(
        source_kind=FrameSourceKind.OPERATOR_INJECTION,
        confidence=Fraction(3, 4),
    )
    history = WorldletHistory(latest_state=state)
    a1 = WorldletAttempt(
        attempt_id="att1",
        token_id="tk1",
        pattern_id="pt1",
        target_id="tgt1",
        provenance=provenance,
    )
    history, _ = respond_worldlet(history, a1)
    a2 = WorldletAttempt(
        attempt_id="att2",
        token_id="tk2",
        pattern_id="pt2",
        target_id="tgt1",
        provenance=provenance,
    )
    history, _ = respond_worldlet(history, a2)
    return history


@register("I-WFDBK-04", status="REQUIRED")
def check_session_worldlet_feedback_step() -> None:
    """Audit OperatorSession._run_worldlet_feedback_step."""

    # 1. worldlet_history is None -> absent sentinel triple.
    session = _fresh_session(feedback_mode=FeedbackMode.WORLDLET)
    pre_history = session.worldlet_history
    _append(session, "alpha none")

    worldlet_chunks = [
        c
        for c in session.stream_history.chunks
        if c.provenance.endswith(":worldlet_summary")
    ]
    assert len(worldlet_chunks) == 2, (
        f"I-WFDBK-04 violated: expected 2 worldlet_summary chunks, got "
        f"{len(worldlet_chunks)}"
    )
    for ch in worldlet_chunks:
        assert ch.text.startswith("worldlet_summary "), (
            f"I-WFDBK-04 violated: worldlet_summary chunk text malformed: "
            f"{ch.text!r}"
        )
        assert "state=absent" in ch.text, (
            "I-WFDBK-04 violated: None-history summary missing state=absent"
        )
        assert "last_reason=absent" in ch.text, (
            "I-WFDBK-04 violated: None-history summary missing "
            "last_reason=absent"
        )
    # Helper does not mutate worldlet_history.
    assert session.worldlet_history is pre_history

    # 2. worldlet_history populated -> bounded counts.
    populated = _build_populated_worldlet_history()
    session2 = _fresh_session(
        feedback_mode=FeedbackMode.WORLDLET,
        worldlet_history=populated,
    )
    _append(session2, "alpha populated")
    worldlet_chunks2 = [
        c
        for c in session2.stream_history.chunks
        if c.provenance.endswith(":worldlet_summary")
    ]
    assert len(worldlet_chunks2) == 2
    for ch in worldlet_chunks2:
        # Should not contain "absent" since history is populated.
        assert "state=absent" not in ch.text, (
            "I-WFDBK-04 violated: populated-history summary has absent state"
        )
        # populated history has 2 responses, 1 accepted (tk1), 1 rejected.
        assert "responses=2" in ch.text
        assert "accepted=1" in ch.text
        assert "pushback=1" in ch.text
    # Helper does not mutate worldlet_history.
    assert session2.worldlet_history is populated


@register("I-WFDBK-05", status="REQUIRED")
def check_processing_window_worldlet_modes() -> None:
    """Audit _run_processing_window WORLDLET / combined mode wiring."""

    # WORLDLET mode: chunks in expected order (operator + alternating
    # rehearsal + worldlet_summary).
    session = _fresh_session(feedback_mode=FeedbackMode.WORLDLET)
    _append(session, "alpha worldlet only")
    provenances = [c.provenance for c in session.stream_history.chunks]
    expected = [
        "operator",
        "internal_processing_window:1:rehearsal",
        "internal_processing_window:1:worldlet_summary",
        "internal_processing_window:2:rehearsal",
        "internal_processing_window:2:worldlet_summary",
    ]
    assert provenances == expected, (
        f"I-WFDBK-05 violated: WORLDLET provenances drifted: {provenances!r}"
    )

    # PATTERN_COHERENCE_WORLDLET: rehearsal -> pledger -> cohmon -> worldlet.
    session2 = _fresh_session(feedback_mode=FeedbackMode.PATTERN_COHERENCE_WORLDLET)
    _append(session2, "alpha combined")
    provenances2 = [c.provenance for c in session2.stream_history.chunks]
    expected2 = ["operator"]
    for k in (1, 2):
        expected2.extend(
            [
                f"internal_processing_window:{k}:rehearsal",
                f"internal_processing_window:{k}:pledger_summary",
                f"internal_processing_window:{k}:cohmon_summary",
                f"internal_processing_window:{k}:worldlet_summary",
            ]
        )
    assert provenances2 == expected2, (
        f"I-WFDBK-05 violated: combined provenances drifted: {provenances2!r}"
    )

    # OFF / PATTERN_LEDGER / COHERENCE / PATTERN_AND_COHERENCE do NOT
    # emit any worldlet_summary chunks.
    for mode in (
        FeedbackMode.OFF,
        FeedbackMode.PATTERN_LEDGER,
        FeedbackMode.COHERENCE,
        FeedbackMode.PATTERN_AND_COHERENCE,
    ):
        s = _fresh_session(feedback_mode=mode)
        _append(s, "alpha non-worldlet")
        worldlet_chunks = [
            c
            for c in s.stream_history.chunks
            if c.provenance.endswith(":worldlet_summary")
        ]
        assert len(worldlet_chunks) == 0, (
            f"I-WFDBK-05 violated: mode {mode!r} produced worldlet chunks"
        )


@register("I-WFDBK-06", status="REQUIRED")
def check_worldlet_summary_pattern_ledger_observation() -> None:
    """Audit Pattern Ledger observation of worldlet_summary chunks."""

    session = _fresh_session(feedback_mode=FeedbackMode.WORLDLET)
    _append(session, "alpha pattern ledger")

    # At least 2 ledger entries: one for the seed chunk's signature
    # and one for the (distinct) worldlet_summary signature.
    assert len(session.pattern_ledger.entries) >= 2, (
        f"I-WFDBK-06 violated: expected >= 2 pattern ledger entries, "
        f"got {len(session.pattern_ledger.entries)}"
    )

    # Two fresh sessions advanced through the same operator sequence
    # produce equal ledger entries (determinism).
    s_a = _fresh_session(feedback_mode=FeedbackMode.WORLDLET)
    s_b = _fresh_session(feedback_mode=FeedbackMode.WORLDLET)
    _append(s_a, "delta deterministic")
    _append(s_b, "delta deterministic")
    pids_a = tuple(e.pattern_id for e in s_a.pattern_ledger.entries)
    pids_b = tuple(e.pattern_id for e in s_b.pattern_ledger.entries)
    assert pids_a == pids_b, (
        f"I-WFDBK-06 violated: pattern_id tuples diverged across two fresh "
        f"sessions: {pids_a!r} vs {pids_b!r}"
    )
    assert len(s_a.stream_history.chunks) == len(s_b.stream_history.chunks)
