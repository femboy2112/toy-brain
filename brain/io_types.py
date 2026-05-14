"""I/O boundary types (Phase 2 v1).

Catalog rows owned (cross-cutting):
  - I-RT-01: COGITO_ID does not appear in any user-supplied PerceptEvent.
  - I-RT-05: tick log is append-only (TickRecord frozen).
  - I-RT-09: PerceptEvent.text is non-empty and printable.
  - I-RT-10: ContentRegistry retains text metadata across ticks.

This is the only module where ``float`` is permitted, and even there only
in the optional ``display_values`` field of ``TickRecord`` — never for any
quantity an invariant reads.

Phase 2 v1 changes from v0:
  - PerceptEvent gains ``text`` (LLM input) and ``content_state`` (TOCE
    classification). The v0 ``value`` and ``eval`` fields are removed:
    rho normalization happens via the new ``initial_rho`` field, and
    consistency evaluation is now LLM-backed (not user-supplied).
  - ContentRegistry: persistent map of ContentID → str across ticks so
    ``LLMBackedPtCns`` prompts can include text for existing MSI members.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from types import MappingProxyType
from typing import Mapping

from brain.tlica.builders import rho
from brain.tlica.modes import ModeOp
from brain.tlica.profile import COGITO_ID, ContentID
from brain.tlica.ptcns import ConsistencyEval
from brain.toce_core import ContentState


@dataclass(frozen=True, slots=True)
class PerceptEvent:
    """A single percept emitted into a tick (Phase 2 v1 shape).

    Fields:
      - ``content_id``: stable ID; must not equal ``COGITO_ID`` (I-RT-01).
      - ``text``: human-readable description fed to the LLM; must be
        non-empty and printable (I-RT-09).
      - ``content_state``: TOCE Boolean classification of the content.
      - ``initial_rho``: Fraction in ``[0, 1]``; the value at which the
        content enters the profile. Normalized via ``rho()`` if a
        non-Fraction leaks in.
    """

    content_id: ContentID
    text: str
    content_state: ContentState
    initial_rho: Fraction

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
        if not isinstance(self.text, str) or not self.text or not self.text.isprintable():
            raise ValueError(
                "I-RT-09 violated: PerceptEvent.text must be a non-empty "
                f"printable string (got {self.text!r})"
            )
        if not isinstance(self.content_state, ContentState):
            raise TypeError(
                "PerceptEvent.content_state must be a ContentState "
                f"(got {type(self.content_state).__name__})"
            )
        if not isinstance(self.initial_rho, Fraction):
            object.__setattr__(self, "initial_rho", rho(self.initial_rho))
        elif not (Fraction(0) <= self.initial_rho <= Fraction(1)):
            raise ValueError(
                f"PerceptEvent.initial_rho must be in [0, 1]; got {self.initial_rho}"
            )


@dataclass(frozen=True, slots=True)
class ContentRegistry:
    """Persistent ContentID → text map across ticks (I-RT-10).

    Frozen and immutable; ``with_added`` returns a new ContentRegistry
    with the supplied entry merged in. The cogito has no text and is
    intentionally absent.
    """

    texts: Mapping[ContentID, str]

    def __post_init__(self) -> None:
        if not isinstance(self.texts, MappingProxyType):
            object.__setattr__(self, "texts", MappingProxyType(dict(self.texts)))
        for k, v in self.texts.items():
            if not isinstance(k, str):
                raise TypeError(f"ContentRegistry key must be str (got {type(k).__name__})")
            if k == COGITO_ID:
                raise ValueError(
                    f"ContentRegistry must not store text for COGITO_ID ({COGITO_ID!r})"
                )
            if not isinstance(v, str) or not v:
                raise ValueError(f"ContentRegistry text for {k!r} must be non-empty str")

    def with_added(self, content_id: ContentID, text: str) -> "ContentRegistry":
        merged = dict(self.texts)
        merged[content_id] = text
        return ContentRegistry(texts=MappingProxyType(merged))

    @classmethod
    def empty(cls) -> "ContentRegistry":
        return cls(texts=MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class TickRecord:
    """Append-only record of a single tick's externally-observable state.

    Per I-RT-05: instances are frozen dataclasses; no field is mutated
    after construction. Float views (``display_values``) are present for
    UI/debug only and never read by invariants.

    triggered_mode: The single mode dispatched in this tick. ``None`` if
    ``events`` was empty (a no-op tick). In v1, the scenario format
    constrains every tick to exactly one PerceptEvent, so
    ``triggered_mode == mode_trace[0]`` when events is non-empty.
    Multi-percept-per-tick semantics are out of scope for v1; a future
    catalog patch will define dominance rules if needed.
    """

    tick_index: int
    profile_values: Mapping[ContentID, Fraction]
    msi_contents: frozenset[ContentID]
    eval_map: Mapping[ContentID, ConsistencyEval]
    boundary: frozenset[ContentID]
    mode_trace: tuple[ModeOp, ...]
    triggered_mode: ModeOp | None
    registry: ContentRegistry
    notes: tuple[str, ...] = field(default_factory=tuple)

    def display_values(self) -> dict[str, float]:
        """Convenience float view for display only. Never used by invariants."""
        return {str(k): float(v) for k, v in self.profile_values.items()}
