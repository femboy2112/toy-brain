"""Phase 3.18 Bounded Internal Processing Window substrate.

A session-level rehearsal helper for architecture A from the
Phase 3.17 synthesis: after a successful external STREAM_APPEND
dispatch, the session may fire up to N internal STREAM_APPEND
events whose text is the EXACT text of the most recent operator
chunk. This drives ``brain.development.pattern_ledger`` recurrence
counts up deterministically without touching the kernel, the LLM,
the parser, or the cache.

The module is deliberately closed:

* No I/O, no network, no shell, no LLM, no ``brain.tick`` import,
  no ``brain.ui.session`` import (one-way dependency), no curses,
  no threading / asyncio / atexit / signal / importlib / time /
  random.
* No callable / handle / client field appears on any record this
  module produces.
* Every bounded printable string this module produces is audited
  against ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``
  by the static-audit fixture; the module's own assertion is a
  matching list at the bottom of the file.

Drives Phase 3.18 catalog rows ``I-PWND-01`` and ``I-PWND-02``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from brain.development.text_stream import (
    STREAM_PROVENANCE_MAX_LEN,
    STREAM_TEXT_MAX_LEN,
)
from brain.tlica.profile import COGITO_ID


# ---------------------------------------------------------------------------
# Bounded constants locked by PHASE3_18_HUMAN_DEVELOPMENT_SYNTHESIS.md
# ---------------------------------------------------------------------------


#: Maximum allowed ``processing_window_size`` on an OperatorSession.
#: Chosen to be exactly one less than
#: ``STREAM_PATTERN_RECURRENCE_MAX`` (256) so a single external
#: append plus N internal rehearsals at N == PROCESSING_WINDOW_SIZE_MAX
#: produces ``recurrence_count == STREAM_PATTERN_RECURRENCE_MAX``
#: exactly (the SATURATED state). Any larger N would still be safe
#: because ``PatternLedger.observe`` saturates at the cap; the
#: limit here is an explicit operator-side guardrail.
PROCESSING_WINDOW_SIZE_MAX: int = 255


#: Maximum allowed ``processing_window_call_budget``. Bounded but
#: large enough to encode a small int budget for a future
#: STEP_TICK-driven path (S3 from the Phase 3.17 synthesis); the v1
#: REHEARSAL source under STREAM_APPEND consumes zero real model
#: calls, so this field is unused on the v1 path. Kept as a bounded
#: int so the I-UI-10 surface (no callable / handle / client field)
#: stays intact.
PROCESSING_WINDOW_CALL_BUDGET_MAX: int = 65535


#: Provenance prefix every internal rehearsal stamps onto its
#: chunk's ``provenance`` field. The bounded printable string
#: ``"internal_processing_window:<tick_index>:<source_value>"``
#: lets external observers filter internal-source ledger entries
#: from operator-source ones.
PROCESSING_WINDOW_PROVENANCE_PREFIX: str = "internal_processing_window"


# ---------------------------------------------------------------------------
# Closed enum of internal-event sources (v1 ships REHEARSAL only).
# ---------------------------------------------------------------------------


class InternalEventSource(str, Enum):
    """Finite closed enumeration of internal-event source kinds.

    v1 ships ``REHEARSAL`` only — exact-text duplication of the
    most recent operator chunk under a fresh chunk_id. The two
    reserved members ``PLEDGER_SUMMARY`` and ``COHMON_SUMMARY``
    exist for future compatibility but must not be emitted by any
    v1 call site. Drives ``I-PWND-02``.
    """

    REHEARSAL = "rehearsal"
    PLEDGER_SUMMARY = "pledger_summary"  # reserved for a future S1 expansion
    COHMON_SUMMARY = "cohmon_summary"  # reserved for a future S2 expansion


_V1_EMITTED_SOURCES: frozenset[InternalEventSource] = frozenset({
    InternalEventSource.REHEARSAL,
})


# ---------------------------------------------------------------------------
# Bounded primitive validators.
# ---------------------------------------------------------------------------


def _require_int_in_range(
    value: object,
    *,
    field: str,
    lo: int,
    hi: int,
) -> int:
    """Return ``value`` if it's an int (not bool) in ``[lo, hi]``."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(
            f"processing window: {field} must be int "
            f"(got {type(value).__name__})"
        )
    if value < lo or value > hi:
        raise ValueError(
            f"processing window: {field} must be in [{lo}, {hi}] "
            f"(got {value})"
        )
    return value


def validate_processing_window_size(value: object) -> int:
    """Validate ``OperatorSession.processing_window_size``.

    Returns the validated int. Drives ``I-PWND-01`` boundary
    handling on the session record.
    """
    return _require_int_in_range(
        value,
        field="processing_window_size",
        lo=0,
        hi=PROCESSING_WINDOW_SIZE_MAX,
    )


def validate_processing_window_call_budget(value: object) -> int:
    """Validate ``OperatorSession.processing_window_call_budget``."""
    return _require_int_in_range(
        value,
        field="processing_window_call_budget",
        lo=0,
        hi=PROCESSING_WINDOW_CALL_BUDGET_MAX,
    )


# ---------------------------------------------------------------------------
# Rehearsal text / provenance generators.
# ---------------------------------------------------------------------------


def build_rehearsal_provenance(
    *,
    tick_index: int,
    source: InternalEventSource = InternalEventSource.REHEARSAL,
) -> str:
    """Build the bounded printable provenance string for one internal tick.

    Format: ``"internal_processing_window:<tick_index>:<source.value>"``.

    Validation order (drives ``I-PWND-02``):
      1. ``tick_index`` is a non-negative int (and not bool).
      2. ``source`` is an :class:`InternalEventSource` member.
      3. ``source`` is in the v1-emitted set
         (``REHEARSAL`` only); the reserved members raise so the
         v1 dispatcher cannot accidentally widen the source set
         without a fresh review gate.
      4. The composed string is bounded by
         :data:`STREAM_PROVENANCE_MAX_LEN`.
      5. The composed string is bounded printable and is not equal
         to :data:`COGITO_ID`.
    """
    if not isinstance(tick_index, int) or isinstance(tick_index, bool):
        raise ValueError(
            "processing window: tick_index must be int "
            f"(got {type(tick_index).__name__})"
        )
    if tick_index < 0:
        raise ValueError(
            f"processing window: tick_index must be >= 0 (got {tick_index})"
        )
    if not isinstance(source, InternalEventSource):
        raise ValueError(
            "processing window: source must be an InternalEventSource "
            f"(got {type(source).__name__})"
        )
    if source not in _V1_EMITTED_SOURCES:
        raise ValueError(
            "processing window: source "
            f"{source.value!r} is reserved for a future review-gated "
            "expansion and must not be emitted by the v1 dispatcher"
        )
    composed = f"{PROCESSING_WINDOW_PROVENANCE_PREFIX}:{tick_index}:{source.value}"
    if len(composed) > STREAM_PROVENANCE_MAX_LEN:
        raise ValueError(
            f"processing window: composed provenance length {len(composed)} "
            f"exceeds STREAM_PROVENANCE_MAX_LEN={STREAM_PROVENANCE_MAX_LEN}"
        )
    if not composed or not composed.isprintable():
        raise ValueError(
            "processing window: composed provenance is not bounded printable"
        )
    if composed == COGITO_ID:
        raise ValueError(
            "processing window: composed provenance must not equal COGITO_ID"
        )
    return composed


def validate_rehearsal_text(text: object) -> str:
    """Validate the text the internal rehearsal will replay verbatim.

    The text must be a bounded printable string under
    :data:`STREAM_TEXT_MAX_LEN`, non-empty, not equal to
    :data:`COGITO_ID`. The same constraints that
    :func:`brain.development.text_stream.make_text_stream_chunk`
    enforces — duplicated here so the processing-window helper can
    short-circuit before constructing the chunk if the source text
    is malformed.
    """
    if not isinstance(text, str):
        raise ValueError(
            "processing window: rehearsal text must be str "
            f"(got {type(text).__name__})"
        )
    if not text:
        raise ValueError("processing window: rehearsal text must be non-empty")
    if len(text) > STREAM_TEXT_MAX_LEN:
        raise ValueError(
            "processing window: rehearsal text length "
            f"{len(text)} exceeds STREAM_TEXT_MAX_LEN={STREAM_TEXT_MAX_LEN}"
        )
    for ch in text:
        if ch in ("\n", "\t"):
            continue
        if not ch.isprintable():
            raise ValueError(
                "processing window: rehearsal text must be printable raw text"
            )
    if text == COGITO_ID:
        raise ValueError(
            "processing window: rehearsal text must not equal COGITO_ID"
        )
    return text


# ---------------------------------------------------------------------------
# Plan record returned by the planner.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RehearsalStep:
    """One planned internal rehearsal step (drives ``I-PWND-02``).

    Fields are all bounded primitives. No callable / handle /
    client / file / socket / path appears here.
    """

    tick_index: int
    source: InternalEventSource
    provenance: str
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.tick_index, int) or isinstance(self.tick_index, bool):
            raise ValueError(
                "RehearsalStep.tick_index must be int "
                f"(got {type(self.tick_index).__name__})"
            )
        if self.tick_index < 1:
            raise ValueError(
                "RehearsalStep.tick_index must be >= 1 "
                f"(got {self.tick_index})"
            )
        if not isinstance(self.source, InternalEventSource):
            raise ValueError(
                "RehearsalStep.source must be an InternalEventSource "
                f"(got {type(self.source).__name__})"
            )
        if self.source not in _V1_EMITTED_SOURCES:
            raise ValueError(
                "RehearsalStep.source "
                f"{self.source.value!r} is reserved; v1 only emits "
                f"{sorted(s.value for s in _V1_EMITTED_SOURCES)!r}"
            )
        # Re-validate provenance + text shape so the record itself
        # cannot be constructed with malformed bounded strings.
        expected_prov = build_rehearsal_provenance(
            tick_index=self.tick_index, source=self.source
        )
        if self.provenance != expected_prov:
            raise ValueError(
                "RehearsalStep.provenance must equal the deterministic "
                f"build_rehearsal_provenance output (got {self.provenance!r}, "
                f"expected {expected_prov!r})"
            )
        validate_rehearsal_text(self.text)


def plan_rehearsals(
    *,
    seed_text: str,
    window_size: int,
    source: InternalEventSource = InternalEventSource.REHEARSAL,
) -> tuple[RehearsalStep, ...]:
    """Return the deterministic tuple of internal rehearsals to fire.

    Pure function: no I/O, no time, no random, no PID. Same input
    yields the same output across runs / processes / OSes. Drives
    ``I-PWND-01`` (count) and ``I-PWND-02`` (shape).

    Returns an empty tuple when ``window_size == 0`` (the OFF
    state).
    """
    n = validate_processing_window_size(window_size)
    text = validate_rehearsal_text(seed_text)
    if n == 0:
        return ()
    steps: list[RehearsalStep] = []
    for k in range(1, n + 1):
        provenance = build_rehearsal_provenance(tick_index=k, source=source)
        steps.append(
            RehearsalStep(
                tick_index=k,
                source=source,
                provenance=provenance,
                text=text,
            )
        )
    return tuple(steps)


# ---------------------------------------------------------------------------
# Module-level non-claim audit surface (drives I-PWND-02).
# ---------------------------------------------------------------------------


#: Every bounded printable string this module *produces* must avoid
#: every term in ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``.
#: The static-audit fixture imports that tuple and exhaustively
#: scans (a) the module source, (b) every member of
#: :class:`InternalEventSource`, (c) the constant strings here, and
#: (d) the output of :func:`build_rehearsal_provenance` over the v1
#: source set.
MODULE_PRODUCED_STRINGS: tuple[str, ...] = (
    PROCESSING_WINDOW_PROVENANCE_PREFIX,
    InternalEventSource.REHEARSAL.value,
    InternalEventSource.PLEDGER_SUMMARY.value,
    InternalEventSource.COHMON_SUMMARY.value,
)


__all__ = [
    "InternalEventSource",
    "MODULE_PRODUCED_STRINGS",
    "PROCESSING_WINDOW_CALL_BUDGET_MAX",
    "PROCESSING_WINDOW_PROVENANCE_PREFIX",
    "PROCESSING_WINDOW_SIZE_MAX",
    "RehearsalStep",
    "build_rehearsal_provenance",
    "plan_rehearsals",
    "validate_processing_window_call_budget",
    "validate_processing_window_size",
    "validate_rehearsal_text",
]
