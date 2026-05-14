"""I/O boundary types.

Catalog rows owned (cross-cutting):
  - I-RT-01: COGITO_ID does not appear in any user-supplied PerceptEvent.
  - I-RT-05: tick log is append-only (TickRecord frozen).

This is the only module where ``float`` is permitted, and even there only
in the optional ``display_values`` field of ``TickRecord`` — never for any
quantity an invariant reads.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Mapping

from brain.tlica.builders import rho
from brain.tlica.profile import COGITO_ID, ContentID
from brain.tlica.ptcns import ConsistencyEval


@dataclass(frozen=True, slots=True)
class PerceptEvent:
    """A single percept emitted into a tick.

    Per I-RT-01: ``content_id`` must not equal the reserved ``COGITO_ID``
    sentinel. ``value`` is normalized through ``rho()`` at construction so
    downstream code can rely on the ``Fraction`` invariant.
    """

    content_id: ContentID
    value: Fraction
    eval: ConsistencyEval | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.content_id, str):
            raise TypeError(
                f"PerceptEvent.content_id must be str (got {type(self.content_id).__name__})"
            )
        if self.content_id == COGITO_ID:
            raise ValueError(
                "I-RT-01 violated: PerceptEvent.content_id must not equal "
                f"COGITO_ID ({COGITO_ID!r}) — that sentinel is reserved."
            )
        # Normalize ``value`` if it leaked in as float/int/str.
        if not isinstance(self.value, Fraction):
            object.__setattr__(self, "value", rho(self.value))


@dataclass(frozen=True, slots=True)
class TickRecord:
    """Append-only record of a single tick's externally-observable state.

    Per I-RT-05: instances are frozen dataclasses; no field is mutated
    after construction. Float views (``display_values``) are present for
    UI/debug only and never read by invariants.
    """

    tick_index: int
    profile_values: Mapping[ContentID, Fraction]
    msi_contents: frozenset[ContentID]
    eval_map: Mapping[ContentID, ConsistencyEval]
    boundary: frozenset[ContentID]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def display_values(self) -> dict[str, float]:
        """Convenience float view for display only. Never used by invariants."""
        return {str(k): float(v) for k, v in self.profile_values.items()}
