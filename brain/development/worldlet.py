"""Minimal Worldlet primitives for Phase 3.3.

The v0.8 worldlet surface is a deterministic local harness. It can record
bounded consequence evidence in developmental history, but it does not emit
``PerceptEvent`` values, call ``tick()``, or mutate TLICA runtime state.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from types import MappingProxyType
from typing import Mapping

from brain.development.drives import require_unit_fraction
from brain.development.history import TraceEventID, require_printable_id
from brain.development.output import (
    LearnedOutputToken,
    OutputHistory,
    OutputPatternID,
    OutputTokenID,
    ProtoOutputActionReadiness,
)
from brain.development.stream import FrameSourceKind
from brain.tlica.profile import COGITO_ID

WorldletAttemptID = str
WorldletObjectID = str
WorldletResponseID = str
WorldletStateID = str


def require_worldlet_valence(value: Fraction, *, field: str) -> Fraction:
    """Validate an exact bounded worldlet valence without clamping."""
    if not isinstance(value, Fraction):
        raise TypeError(f"{field} must be a Fraction (got {type(value).__name__})")
    if not (Fraction(-1) <= value <= Fraction(1)):
        raise ValueError(f"{field} must be in [-1, 1] (got {value})")
    return value


@dataclass(frozen=True, slots=True)
class WorldletValence:
    """Exact local response valence for the deterministic harness."""

    value: Fraction

    def __post_init__(self) -> None:
        try:
            require_worldlet_valence(self.value, field="WorldletValence.value")
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-WLD-02 violated: WorldletValence.value must be a "
                "Fraction in [-1, 1]"
            ) from exc


@dataclass(frozen=True, slots=True)
class WorldletProvenance:
    """Source metadata for local worldlet harness evidence."""

    source_kind: FrameSourceKind
    confidence: Fraction
    trace_event_ids: tuple[TraceEventID, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source_kind, FrameSourceKind):
            raise TypeError(
                "I-WLD-03 violated: WorldletProvenance.source_kind must be a "
                f"FrameSourceKind (got {type(self.source_kind).__name__})"
            )
        try:
            require_unit_fraction(
                self.confidence,
                field="WorldletProvenance.confidence",
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "I-WLD-03 violated: WorldletProvenance.confidence must be a "
                "Fraction in [0, 1]"
            ) from exc
        if not isinstance(self.trace_event_ids, tuple):
            raise TypeError("WorldletProvenance.trace_event_ids must be a tuple")
        for event_id in self.trace_event_ids:
            require_printable_id(
                event_id,
                field="WorldletProvenance.trace_event_id",
            )


def _require_non_reserved_id(value: str, *, field: str, row_id: str) -> str:
    require_printable_id(value, field=field)
    if value == COGITO_ID:
        raise ValueError(f"{row_id} violated: {field} cannot be COGITO_ID")
    return value


@dataclass(frozen=True, slots=True)
class WorldletObject:
    """Finite deterministic target surface for the local worldlet harness."""

    object_id: WorldletObjectID
    label: str
    available: bool
    accepted_token_ids: frozenset[OutputTokenID] | tuple[OutputTokenID, ...] = frozenset()

    def __post_init__(self) -> None:
        _require_non_reserved_id(
            self.object_id,
            field="WorldletObject.object_id",
            row_id="I-WLD-01",
        )
        require_printable_id(self.label, field="WorldletObject.label")
        if not isinstance(self.available, bool):
            raise TypeError("I-WLD-01 violated: WorldletObject.available must be bool")
        if not isinstance(self.accepted_token_ids, (frozenset, tuple)):
            raise TypeError(
                "I-WLD-01 violated: WorldletObject.accepted_token_ids must be "
                "a tuple or frozenset"
            )
        accepted = frozenset(self.accepted_token_ids)
        for token_id in accepted:
            _require_non_reserved_id(
                token_id,
                field="WorldletObject.accepted_token_id",
                row_id="I-WLD-01",
            )
        object.__setattr__(self, "accepted_token_ids", accepted)


@dataclass(frozen=True, slots=True)
class WorldletState:
    """Immutable finite snapshot of the deterministic worldlet harness."""

    state_id: WorldletStateID
    objects: Mapping[WorldletObjectID, WorldletObject] | None = None
    step_index: int = 0

    def __post_init__(self) -> None:
        _require_non_reserved_id(
            self.state_id,
            field="WorldletState.state_id",
            row_id="I-WLD-01",
        )
        if not isinstance(self.step_index, int) or self.step_index < 0:
            raise ValueError(
                "I-WLD-01 violated: WorldletState.step_index must be a "
                "non-negative integer"
            )
        objects = dict(self.objects or {})
        for key, obj in objects.items():
            _require_non_reserved_id(
                key,
                field="WorldletState.objects key",
                row_id="I-WLD-01",
            )
            if not isinstance(obj, WorldletObject):
                raise TypeError("WorldletState.objects values must be WorldletObject")
            if key != obj.object_id:
                raise ValueError(
                    "I-WLD-01 violated: WorldletState object key must match object_id"
                )
        object.__setattr__(self, "objects", MappingProxyType(objects))

    def object_for_target(self, target_id: WorldletObjectID | None) -> WorldletObject | None:
        """Deterministic object lookup for a target identifier."""
        if target_id is None:
            return None
        require_printable_id(target_id, field="target_id")
        return self.objects.get(target_id)


@dataclass(frozen=True, slots=True)
class WorldletAttempt:
    """Below-agency attempt record.

    Step 8 adds the learned-token support constructor for I-WLD-07. The record
    itself is already useful for Step 7 copy-on-write history checks.
    """

    attempt_id: WorldletAttemptID
    token_id: OutputTokenID
    pattern_id: OutputPatternID
    target_id: WorldletObjectID | None
    provenance: WorldletProvenance

    def __post_init__(self) -> None:
        _require_non_reserved_id(
            self.attempt_id,
            field="WorldletAttempt.attempt_id",
            row_id="I-WLD-04",
        )
        _require_non_reserved_id(
            self.token_id,
            field="WorldletAttempt.token_id",
            row_id="I-WLD-04",
        )
        _require_non_reserved_id(
            self.pattern_id,
            field="WorldletAttempt.pattern_id",
            row_id="I-WLD-04",
        )
        if self.target_id is not None:
            _require_non_reserved_id(
                self.target_id,
                field="WorldletAttempt.target_id",
                row_id="I-WLD-04",
            )
        if not isinstance(self.provenance, WorldletProvenance):
            raise TypeError("WorldletAttempt.provenance must be WorldletProvenance")


def construct_worldlet_attempt(
    history: OutputHistory,
    readiness: ProtoOutputActionReadiness,
    learned_token: LearnedOutputToken,
    *,
    attempt_id: WorldletAttemptID,
    target_id: WorldletObjectID | None,
    provenance: WorldletProvenance,
) -> WorldletAttempt:
    """Construct a worldlet attempt only from mature local output support."""
    if not isinstance(history, OutputHistory):
        raise TypeError(
            f"history must be OutputHistory (got {type(history).__name__})"
        )
    if not isinstance(readiness, ProtoOutputActionReadiness):
        raise ValueError(
            "I-WLD-07 violated: worldlet attempt requires "
            "ProtoOutputActionReadiness support"
        )
    if not readiness.ready:
        raise ValueError(
            "I-WLD-07 violated: worldlet attempt requires ready readiness"
        )
    if not isinstance(learned_token, LearnedOutputToken):
        raise ValueError(
            "I-WLD-07 violated: worldlet attempt requires LearnedOutputToken support"
        )
    if history.learned_tokens.get(learned_token.token_id) is not learned_token:
        raise ValueError(
            "I-WLD-07 violated: learned token must be registered in OutputHistory"
        )
    if history.token_candidates.get(learned_token.token_id) is not learned_token.candidate:
        raise ValueError(
            "I-WLD-07 violated: learned token candidate must be registered in OutputHistory"
        )
    if learned_token.token_id != readiness.token_id:
        raise ValueError(
            "I-WLD-07 violated: readiness token_id must match learned token"
        )
    if learned_token.pattern_id != readiness.pattern_id:
        raise ValueError(
            "I-WLD-07 violated: readiness pattern_id must match learned token"
        )
    if learned_token.support_count != readiness.support_count:
        raise ValueError(
            "I-WLD-07 violated: readiness support_count must match learned token"
        )
    if learned_token.source_kinds != readiness.source_kinds:
        raise ValueError(
            "I-WLD-07 violated: readiness source_kinds must match learned token"
        )
    if not isinstance(provenance, WorldletProvenance):
        raise ValueError(
            "I-WLD-07 violated: worldlet attempt requires worldlet provenance"
        )

    try:
        return WorldletAttempt(
            attempt_id=attempt_id,
            token_id=learned_token.token_id,
            pattern_id=learned_token.pattern_id,
            target_id=target_id,
            provenance=provenance,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "I-WLD-07 violated: invalid worldlet attempt identifier"
        ) from exc


@dataclass(frozen=True, slots=True)
class WorldletResponse:
    """Source-tagged local consequence record returned by the harness."""

    response_id: WorldletResponseID
    attempt_id: WorldletAttemptID
    accepted: bool
    reason: str
    valence: WorldletValence
    provenance: WorldletProvenance

    def __post_init__(self) -> None:
        _require_non_reserved_id(
            self.response_id,
            field="WorldletResponse.response_id",
            row_id="I-WLD-05",
        )
        _require_non_reserved_id(
            self.attempt_id,
            field="WorldletResponse.attempt_id",
            row_id="I-WLD-05",
        )
        if not isinstance(self.accepted, bool):
            raise TypeError("I-WLD-05 violated: WorldletResponse.accepted must be bool")
        require_printable_id(self.reason, field="WorldletResponse.reason")
        if not isinstance(self.valence, WorldletValence):
            raise TypeError("WorldletResponse.valence must be WorldletValence")
        if not isinstance(self.provenance, WorldletProvenance):
            raise TypeError("WorldletResponse.provenance must be WorldletProvenance")


@dataclass(frozen=True, slots=True)
class WorldletHistory:
    """Copy-on-write local worldlet attempt/response history."""

    latest_state: WorldletState
    attempts: tuple[WorldletAttempt, ...] = ()
    responses: tuple[WorldletResponse, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.latest_state, WorldletState):
            raise TypeError("WorldletHistory.latest_state must be WorldletState")
        if not isinstance(self.attempts, tuple):
            raise TypeError("WorldletHistory.attempts must be a tuple")
        for attempt in self.attempts:
            if not isinstance(attempt, WorldletAttempt):
                raise TypeError("WorldletHistory.attempts must contain WorldletAttempt")
        if not isinstance(self.responses, tuple):
            raise TypeError("WorldletHistory.responses must be a tuple")
        for response in self.responses:
            if not isinstance(response, WorldletResponse):
                raise TypeError(
                    "WorldletHistory.responses must contain WorldletResponse"
                )


def append_worldlet_attempt(
    history: WorldletHistory,
    attempt: WorldletAttempt,
    *,
    latest_state: WorldletState | None = None,
) -> WorldletHistory:
    """Append one attempt without mutating prior worldlet history."""
    if not isinstance(history, WorldletHistory):
        raise TypeError(
            f"history must be WorldletHistory (got {type(history).__name__})"
        )
    if not isinstance(attempt, WorldletAttempt):
        raise TypeError(
            f"attempt must be WorldletAttempt (got {type(attempt).__name__})"
        )
    next_state = latest_state or history.latest_state
    if not isinstance(next_state, WorldletState):
        raise TypeError("latest_state must be WorldletState")
    return WorldletHistory(
        latest_state=next_state,
        attempts=history.attempts + (attempt,),
        responses=history.responses,
    )


def append_worldlet_response(
    history: WorldletHistory,
    response: WorldletResponse,
    *,
    latest_state: WorldletState | None = None,
) -> WorldletHistory:
    """Append one response without mutating prior worldlet history."""
    if not isinstance(history, WorldletHistory):
        raise TypeError(
            f"history must be WorldletHistory (got {type(history).__name__})"
        )
    if not isinstance(response, WorldletResponse):
        raise TypeError(
            f"response must be WorldletResponse (got {type(response).__name__})"
        )
    next_state = latest_state or history.latest_state
    if not isinstance(next_state, WorldletState):
        raise TypeError("latest_state must be WorldletState")
    return WorldletHistory(
        latest_state=next_state,
        attempts=history.attempts,
        responses=history.responses + (response,),
    )


def _worldlet_digest(*parts: object) -> str:
    return sha256(repr(parts).encode("utf-8")).hexdigest()[:16]


def _worldlet_response_id(
    state: WorldletState,
    attempt: WorldletAttempt,
    reason: str,
) -> WorldletResponseID:
    digest = _worldlet_digest(
        "response",
        state.state_id,
        state.step_index,
        attempt.attempt_id,
        attempt.token_id,
        attempt.target_id,
        reason,
    )
    return f"wld:response:{digest}"


def _worldlet_next_state(
    state: WorldletState,
    attempt: WorldletAttempt,
    reason: str,
) -> WorldletState:
    digest = _worldlet_digest(
        "state",
        state.state_id,
        state.step_index,
        attempt.attempt_id,
        attempt.token_id,
        attempt.target_id,
        reason,
    )
    return WorldletState(
        state_id=f"wld:state:{digest}",
        objects=state.objects,
        step_index=state.step_index + 1,
    )


def respond_worldlet(
    history: WorldletHistory,
    attempt: WorldletAttempt,
) -> tuple[WorldletHistory, WorldletResponse]:
    """Apply one valid attempt to the local deterministic worldlet harness."""
    if not isinstance(history, WorldletHistory):
        raise TypeError(
            f"history must be WorldletHistory (got {type(history).__name__})"
        )
    if not isinstance(attempt, WorldletAttempt):
        raise TypeError(
            f"attempt must be WorldletAttempt (got {type(attempt).__name__})"
        )

    state = history.latest_state
    target = state.object_for_target(attempt.target_id)
    if target is None:
        accepted = False
        reason = "missing-target"
        valence = Fraction(-1, 2)
    elif not target.available:
        accepted = False
        reason = "target-unavailable"
        valence = Fraction(-1, 2)
    elif attempt.token_id in target.accepted_token_ids:
        accepted = True
        reason = "accepted"
        valence = Fraction(1, 2)
    else:
        accepted = False
        reason = "rejected"
        valence = Fraction(-1, 2)

    response = WorldletResponse(
        response_id=_worldlet_response_id(state, attempt, reason),
        attempt_id=attempt.attempt_id,
        accepted=accepted,
        reason=reason,
        valence=WorldletValence(valence),
        provenance=attempt.provenance,
    )
    next_state = _worldlet_next_state(state, attempt, reason)
    with_attempt = append_worldlet_attempt(history, attempt)
    with_response = append_worldlet_response(
        with_attempt,
        response,
        latest_state=next_state,
    )
    return with_response, response
