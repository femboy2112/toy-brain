"""Phase 3.24 FeedbackMode + InternalEventSource validation fixture.

Drives ``I-WFDBK-02`` and ``I-WFDBK-03`` (REQUIRED). Audits the closed
enum extensions and the bounded worldlet-summary provenance helper.
"""
from __future__ import annotations

from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.processing_window import (
    FeedbackMode,
    InternalEventSource,
    PROCESSING_WINDOW_PROVENANCE_PREFIX,
    build_rehearsal_provenance,
    validate_feedback_mode,
)
from brain.development.text_stream import STREAM_PROVENANCE_MAX_LEN
from brain.invariants import register
from brain.tlica.profile import COGITO_ID


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


_EXPECTED_FEEDBACK_MODE_VALUES = frozenset(
    {
        "off",
        "pattern_ledger",
        "coherence",
        "pattern_and_coherence",
        "worldlet",
        "pattern_coherence_worldlet",
    }
)


_EXPECTED_INTERNAL_EVENT_SOURCE_VALUES = frozenset(
    {"rehearsal", "pledger_summary", "cohmon_summary", "worldlet_summary"}
)


@register("I-WFDBK-02", status="REQUIRED")
def check_feedback_mode_worldlet_validation() -> None:
    """Audit FeedbackMode closed-set widening + validation."""

    assert issubclass(FeedbackMode, str)
    actual = frozenset(m.value for m in FeedbackMode)
    assert actual == _EXPECTED_FEEDBACK_MODE_VALUES, (
        "I-WFDBK-02 violated: FeedbackMode value set drifted "
        f"(got {sorted(actual)!r}, expected "
        f"{sorted(_EXPECTED_FEEDBACK_MODE_VALUES)!r})"
    )

    # Identity-return on every closed-set member.
    for member in FeedbackMode:
        assert validate_feedback_mode(member) is member, (
            f"I-WFDBK-02 violated: validate_feedback_mode did not return "
            f"identity for {member!r}"
        )

    # Phase 3.24 members specifically:
    assert validate_feedback_mode(FeedbackMode.WORLDLET) is FeedbackMode.WORLDLET
    assert (
        validate_feedback_mode(FeedbackMode.PATTERN_COHERENCE_WORLDLET)
        is FeedbackMode.PATTERN_COHERENCE_WORLDLET
    )

    # Rejection: non-FeedbackMode input raises typed ValueError.
    rejection_inputs = (
        "worldlet",
        "pattern_coherence_worldlet",
        0,
        1,
        True,
        False,
        None,
        (),
        [],
        object(),
    )
    for bad in rejection_inputs:
        raised = False
        try:
            validate_feedback_mode(bad)  # type: ignore[arg-type]
        except ValueError:
            raised = True
        assert raised, (
            f"I-WFDBK-02 violated: validate_feedback_mode accepted "
            f"non-FeedbackMode input {bad!r}"
        )


@register("I-WFDBK-03", status="REQUIRED")
def check_internal_event_source_worldlet_provenance() -> None:
    """Audit InternalEventSource.WORLDLET_SUMMARY provenance."""

    assert issubclass(InternalEventSource, str)
    actual = frozenset(m.value for m in InternalEventSource)
    assert actual == _EXPECTED_INTERNAL_EVENT_SOURCE_VALUES, (
        "I-WFDBK-03 violated: InternalEventSource value set drifted "
        f"(got {sorted(actual)!r}, expected "
        f"{sorted(_EXPECTED_INTERNAL_EVENT_SOURCE_VALUES)!r})"
    )

    # build_rehearsal_provenance produces the bounded printable
    # worldlet_summary provenance.
    for k in (1, 2, 3, 42, 255):
        provenance = build_rehearsal_provenance(
            tick_index=k,
            source=InternalEventSource.WORLDLET_SUMMARY,
        )
        expected = (
            f"{PROCESSING_WINDOW_PROVENANCE_PREFIX}:{k}:worldlet_summary"
        )
        assert provenance == expected, (
            f"I-WFDBK-03 violated: build_rehearsal_provenance returned "
            f"{provenance!r}, expected {expected!r}"
        )
        assert provenance.isprintable(), (
            f"I-WFDBK-03 violated: provenance {provenance!r} is not printable"
        )
        assert len(provenance) <= STREAM_PROVENANCE_MAX_LEN, (
            f"I-WFDBK-03 violated: provenance length {len(provenance)} > "
            f"STREAM_PROVENANCE_MAX_LEN={STREAM_PROVENANCE_MAX_LEN}"
        )
        assert provenance != COGITO_ID
        term = _has_forbidden(provenance)
        assert term is None, (
            f"I-WFDBK-03 violated: provenance {provenance!r} contains "
            f"forbidden non-claim term {term!r}"
        )
