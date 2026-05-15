"""Proto-content promotion boundary for Phase 3.1."""
from __future__ import annotations

from fractions import Fraction

from brain.development.drives import require_unit_fraction
from brain.development.proto_content import ProtoContent
from brain.io_types import PerceptEvent
from brain.tlica.profile import COGITO_ID
from brain.toce_core import ContentState


def proto_content_text(content: ProtoContent) -> str:
    """Build a printable event text from a proto-content signature."""
    if not isinstance(content, ProtoContent):
        raise TypeError(f"content must be ProtoContent (got {type(content).__name__})")
    parts = ", ".join(f"{channel}={value}" for channel, value in content.signature)
    return f"developmental content {content.content_id}: {parts}"


def can_promote_proto_content(content: ProtoContent) -> bool:
    """Return whether a proto-content candidate has independent support."""
    if not isinstance(content, ProtoContent):
        raise TypeError(f"content must be ProtoContent (got {type(content).__name__})")
    return (
        content.content_id != COGITO_ID
        and content.eligible_for_promotion
        and bool(content.provenance.trace_event_ids)
    )


def promote_proto_content(
    content: ProtoContent,
    *,
    content_state: ContentState | None = None,
    initial_rho: Fraction | None = None,
) -> PerceptEvent:
    """Convert stable proto-content into a single tick-boundary event."""
    if not isinstance(content, ProtoContent):
        raise TypeError(f"content must be ProtoContent (got {type(content).__name__})")
    if content.content_id == COGITO_ID:
        raise ValueError("I-DEV-06 violated: developmental content cannot produce COGITO_ID")
    if not content.eligible_for_promotion:
        raise ValueError(
            "I-DEV-05 violated: promotion requires stability and positive prediction gain"
        )
    if not content.provenance.trace_event_ids:
        raise ValueError("I-DEV-05 violated: promotion requires probe provenance")

    rho_value = content.stability if initial_rho is None else initial_rho
    require_unit_fraction(rho_value, field="initial_rho")
    state = content_state or ContentState(
        available=True,
        verification_path=True,
        retrievable=True,
        operative=True,
    )
    if not isinstance(state, ContentState):
        raise TypeError("content_state must be ContentState")
    return PerceptEvent(
        content_id=content.content_id,
        text=proto_content_text(content),
        content_state=state,
        initial_rho=rho_value,
    )
