"""Deterministic probe protocol for Phase 3.1."""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from fractions import Fraction

from brain.development.drives import require_unit_fraction
from brain.development.history import SubstrateHistory, TraceEventID, require_printable_id
from brain.development.stream import FrameSource, FrameSourceKind, PhenomenalFrame


class ProbeKind(str, Enum):
    """Active Phase 3.1 probe kinds."""

    SIMILARITY = "similarity"
    FOCUS_CONTACT = "focus_contact"


SIMILARITY = ProbeKind.SIMILARITY
FOCUS_CONTACT = ProbeKind.FOCUS_CONTACT


@dataclass(frozen=True, slots=True)
class ProbeUse:
    """A single deterministic probe use below the promotion boundary."""

    probe_id: TraceEventID
    kind: ProbeKind
    target_channel: str
    budget_cost: Fraction
    result_frame: PhenomenalFrame

    def __post_init__(self) -> None:
        require_printable_id(self.probe_id, field="ProbeUse.probe_id")
        if not isinstance(self.kind, ProbeKind):
            raise TypeError(f"ProbeUse.kind must be ProbeKind (got {type(self.kind).__name__})")
        require_printable_id(self.target_channel, field="ProbeUse.target_channel")
        require_unit_fraction(self.budget_cost, field="ProbeUse.budget_cost")
        if not isinstance(self.result_frame, PhenomenalFrame):
            raise TypeError("ProbeUse.result_frame must be PhenomenalFrame")
        source = self.result_frame.sources.get(self.target_channel)
        if source is None or source.kind is not FrameSourceKind.PROBE_ECHO:
            raise ValueError(
                "ProbeUse.result_frame must contain a PROBE_ECHO source for target_channel"
            )


@dataclass(frozen=True, slots=True)
class ProbePolicyState:
    """Focus-budget and use history for deterministic probes."""

    focus_budget: Fraction
    uses: tuple[ProbeUse, ...] = ()

    def __post_init__(self) -> None:
        require_unit_fraction(self.focus_budget, field="ProbePolicyState.focus_budget")
        if not isinstance(self.uses, tuple):
            raise TypeError("ProbePolicyState.uses must be a tuple")
        for use in self.uses:
            if not isinstance(use, ProbeUse):
                raise TypeError(
                    f"ProbePolicyState.uses must contain ProbeUse values (got {type(use).__name__})"
                )

    @classmethod
    def with_full_focus(cls) -> "ProbePolicyState":
        return cls(focus_budget=Fraction(1))

    def record_use(self, use: ProbeUse) -> "ProbePolicyState":
        if not isinstance(use, ProbeUse):
            raise TypeError(f"use must be ProbeUse (got {type(use).__name__})")
        if use.budget_cost > self.focus_budget:
            raise ValueError("FOCUS_CONTACT budget exhausted")
        return replace(
            self,
            focus_budget=self.focus_budget - use.budget_cost,
            uses=self.uses + (use,),
        )


def focus_contact(
    policy: ProbePolicyState,
    history: SubstrateHistory,
    *,
    probe_id: TraceEventID,
    target_channel: str,
    echo_value: Fraction,
    budget_cost: Fraction = Fraction(1, 4),
    confidence: Fraction = Fraction(1),
) -> tuple[ProbePolicyState, SubstrateHistory, ProbeUse, None]:
    """Record a focus-contact probe without creating promoted content."""
    if not isinstance(policy, ProbePolicyState):
        raise TypeError(f"policy must be ProbePolicyState (got {type(policy).__name__})")
    if not isinstance(history, SubstrateHistory):
        raise TypeError(f"history must be SubstrateHistory (got {type(history).__name__})")
    require_printable_id(target_channel, field="target_channel")
    require_unit_fraction(echo_value, field="echo_value")
    require_unit_fraction(budget_cost, field="budget_cost")
    require_unit_fraction(confidence, field="confidence")

    frame = PhenomenalFrame(
        channels={target_channel: echo_value},
        sources={
            target_channel: FrameSource(
                channel=target_channel,
                kind=FrameSourceKind.PROBE_ECHO,
                confidence=confidence,
            )
        },
    )
    use = ProbeUse(
        probe_id=probe_id,
        kind=FOCUS_CONTACT,
        target_channel=target_channel,
        budget_cost=budget_cost,
        result_frame=frame,
    )
    return policy.record_use(use), history.with_frame(frame), use, None


def probe_output_is_knowledge(use: ProbeUse) -> bool:
    """Boundary predicate: probe echo alone is never knowledge."""
    if not isinstance(use, ProbeUse):
        raise TypeError(f"use must be ProbeUse (got {type(use).__name__})")
    return False


def probe_output_promotes_by_itself(use: ProbeUse) -> bool:
    """Boundary predicate: probe echo alone never crosses into runtime content."""
    if not isinstance(use, ProbeUse):
        raise TypeError(f"use must be ProbeUse (got {type(use).__name__})")
    return False
