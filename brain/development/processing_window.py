"""Phase 3.18 Bounded Internal Processing Window substrate
(extended by Phase 3.19 Internal Feedback Loop).

A session-level rehearsal + feedback helper. After a successful
external STREAM_APPEND dispatch, the session fires up to N
internal STREAM_APPEND events whose text is the EXACT text of the
most recent operator chunk (the Phase 3.18 rehearsal path).
When :class:`FeedbackMode` is :data:`FeedbackMode.PATTERN_LEDGER`,
each rehearsal is followed by a deterministic Pattern Ledger
summary chunk whose text is built by
:func:`build_pledger_summary_text` and re-enters the same
STREAM_APPEND path. The summary chunk's structural signature
differs from the seed chunk's, so Pattern Ledger.observe records
a second-order pattern entry distinct from the seed entry.

The module is deliberately closed:

* No I/O, no network, no shell, no LLM, no ``brain.tick`` import,
  no ``brain.ui.session`` import (one-way dependency), no curses,
  no threading / asyncio / atexit / signal / importlib / time /
  random.
* No callable / handle / client field appears on any record this
  module produces.
* Every bounded printable string this module produces is audited
  against ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``
  by the static-audit fixtures; the module's own assertion is a
  matching list at the bottom of the file.

Drives Phase 3.18 catalog rows ``I-PWND-01`` and ``I-PWND-02``
and Phase 3.19 catalog rows ``I-IFBK-01`` and ``I-IFBK-02``.
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

    Phase 3.18 shipped ``REHEARSAL`` only — exact-text duplication
    of the most recent operator chunk under a fresh chunk_id.
    Phase 3.19 widens the v1-emitted set to also include
    ``PLEDGER_SUMMARY``: a deterministic Pattern Ledger summary
    chunk produced by :func:`build_pledger_summary_text`. The
    third member ``COHMON_SUMMARY`` remains reserved per LOCK F
    and continues to raise from
    :func:`build_rehearsal_provenance`. Drives ``I-PWND-02`` and
    ``I-IFBK-02``.
    """

    REHEARSAL = "rehearsal"
    PLEDGER_SUMMARY = "pledger_summary"  # Phase 3.19 v1-emitted
    COHMON_SUMMARY = "cohmon_summary"  # reserved (Phase 3.19 LOCK F)


_V1_EMITTED_SOURCES: frozenset[InternalEventSource] = frozenset({
    InternalEventSource.REHEARSAL,
    InternalEventSource.PLEDGER_SUMMARY,
})


class FeedbackMode(str, Enum):
    """Finite closed enumeration of internal feedback modes (I-IFBK-02).

    Phase 3.19 v1 ships exactly two members:

    * ``OFF`` — no feedback chunk is generated; the processing
      window's rehearsal path is bit-identical to Phase 3.18.
    * ``PATTERN_LEDGER`` — after each rehearsal, one deterministic
      Pattern Ledger summary chunk re-enters the STREAM_APPEND
      path under provenance
      ``"internal_processing_window:<k>:pledger_summary"``.

    Coherence-monitor feedback (architecture C) is DEFERRED per
    LOCK F; no ``COHERENCE`` member is exposed.
    """

    OFF = "off"
    PATTERN_LEDGER = "pattern_ledger"


_FEEDBACK_MODE_VALID: frozenset[FeedbackMode] = frozenset({
    FeedbackMode.OFF,
    FeedbackMode.PATTERN_LEDGER,
})


#: Bounded printable prefix that every feedback summary text begins
#: with. Locked to a non-claim-clean structural marker.
PLEDGER_SUMMARY_TEXT_PREFIX: str = "pledger_summary"


#: Bounded printable max length of the deterministic summary text
#: produced by :func:`build_pledger_summary_text`. Computed
#: conservatively over the legal input domain: the prefix
#: (15 chars) + " pattern_id=" (12) + max-length pattern_id (64)
#: + " recurrence=" (12) + 3-digit count (3) + "/256" (4) +
#: " sat=" (5) + "quiesced" (8) = 123. Well under
#: STREAM_TEXT_MAX_LEN = 1024.
PLEDGER_SUMMARY_TEXT_MAX_LEN: int = 240


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


def validate_feedback_mode(value: object) -> "FeedbackMode":
    """Validate ``OperatorSession.feedback_mode`` (I-IFBK-02).

    Accepts only :class:`FeedbackMode` members in the v1-allowed
    set ``{OFF, PATTERN_LEDGER}``. Rejects ``bool``, ``int``,
    ``str``, ``None``, and any other type with a typed ``ValueError``.
    """
    if not isinstance(value, FeedbackMode):
        raise ValueError(
            "processing window: feedback_mode must be a FeedbackMode "
            f"(got {type(value).__name__})"
        )
    if value not in _FEEDBACK_MODE_VALID:
        raise ValueError(
            "processing window: feedback_mode "
            f"{value.value!r} is not in the v1-allowed set "
            f"{sorted(m.value for m in _FEEDBACK_MODE_VALID)!r}"
        )
    return value


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


#: Bounded printable closed set of valid saturation-state suffix
#: values for :func:`build_pledger_summary_text`. Mirrors the
#: ``PatternLedgerSaturationState`` enum values without importing
#: the enum itself (the audit forbids
#: ``brain.development.pattern_ledger`` imports here; the bounded
#: helper accepts the string value the caller already extracted).
_PLEDGER_SUMMARY_VALID_SAT_STATES: frozenset[str] = frozenset({
    "open",
    "saturated",
    "quiesced",
})


def build_pledger_summary_text(
    *,
    pattern_id: str,
    recurrence_count: int,
    saturation_state_value: str,
) -> str:
    """Build the deterministic Pattern Ledger summary text (I-IFBK-02).

    Produces a bounded printable string of the locked shape::

        "pledger_summary pattern_id=<pattern_id> recurrence=<n>/256 sat=<state>"

    Pure function: no I/O, no time, no random, no PID, no hostname,
    no ``id()``. Same inputs yield the same output across runs /
    processes / OSes. Caller responsibilities:

    * ``pattern_id`` is the bounded printable id of the Pattern
      Ledger entry the rehearsal just updated (typically
      ``"pledger:<16hex>"``). The helper re-validates the bound
      and rejects ``COGITO_ID``.
    * ``recurrence_count`` is an int in
      ``[0, STREAM_PATTERN_RECURRENCE_MAX]`` (no bool).
    * ``saturation_state_value`` is a member of the closed set
      ``{"open", "saturated", "quiesced"}``.

    Output non-claim audit (LOCK I) is checked by the
    static-audit fixture; the helper itself enforces only
    bounded-shape invariants.
    """
    if not isinstance(pattern_id, str):
        raise ValueError(
            "processing window: pattern_id must be str "
            f"(got {type(pattern_id).__name__})"
        )
    if not pattern_id:
        raise ValueError("processing window: pattern_id must be non-empty")
    if not pattern_id.isprintable():
        raise ValueError("processing window: pattern_id must be printable")
    if pattern_id == COGITO_ID:
        raise ValueError(
            "processing window: pattern_id must not equal COGITO_ID"
        )

    if not isinstance(recurrence_count, int) or isinstance(recurrence_count, bool):
        raise ValueError(
            "processing window: recurrence_count must be int "
            f"(got {type(recurrence_count).__name__})"
        )
    if recurrence_count < 0:
        raise ValueError(
            "processing window: recurrence_count must be >= 0 "
            f"(got {recurrence_count})"
        )
    # Upper bound is STREAM_PATTERN_RECURRENCE_MAX = 256 in the
    # Pattern Ledger; the helper accepts that exact ceiling.
    # Larger values raise so a future cap change cannot silently
    # widen the produced text.
    if recurrence_count > 256:
        raise ValueError(
            "processing window: recurrence_count must be <= 256 "
            f"(got {recurrence_count})"
        )

    if not isinstance(saturation_state_value, str):
        raise ValueError(
            "processing window: saturation_state_value must be str "
            f"(got {type(saturation_state_value).__name__})"
        )
    if saturation_state_value not in _PLEDGER_SUMMARY_VALID_SAT_STATES:
        raise ValueError(
            "processing window: saturation_state_value "
            f"{saturation_state_value!r} not in "
            f"{sorted(_PLEDGER_SUMMARY_VALID_SAT_STATES)!r}"
        )

    composed = (
        f"{PLEDGER_SUMMARY_TEXT_PREFIX} pattern_id={pattern_id} "
        f"recurrence={recurrence_count}/256 sat={saturation_state_value}"
    )
    if len(composed) > PLEDGER_SUMMARY_TEXT_MAX_LEN:
        raise ValueError(
            f"processing window: composed summary length {len(composed)} "
            f"exceeds PLEDGER_SUMMARY_TEXT_MAX_LEN="
            f"{PLEDGER_SUMMARY_TEXT_MAX_LEN}"
        )
    if len(composed) > STREAM_TEXT_MAX_LEN:
        raise ValueError(
            f"processing window: composed summary length {len(composed)} "
            f"exceeds STREAM_TEXT_MAX_LEN={STREAM_TEXT_MAX_LEN}"
        )
    if not composed or not composed.isprintable():
        raise ValueError(
            "processing window: composed summary must be bounded printable"
        )
    if composed == COGITO_ID:
        raise ValueError(
            "processing window: composed summary must not equal COGITO_ID"
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
#: The static-audit fixtures import that tuple and exhaustively
#: scan (a) the module source, (b) every member of
#: :class:`InternalEventSource`, (c) every member of
#: :class:`FeedbackMode`, (d) the constant strings here, (e) the
#: output of :func:`build_rehearsal_provenance` over the v1 source
#: set, and (f) the output of :func:`build_pledger_summary_text`
#: over a representative input set.
MODULE_PRODUCED_STRINGS: tuple[str, ...] = (
    PROCESSING_WINDOW_PROVENANCE_PREFIX,
    PLEDGER_SUMMARY_TEXT_PREFIX,
    InternalEventSource.REHEARSAL.value,
    InternalEventSource.PLEDGER_SUMMARY.value,
    InternalEventSource.COHMON_SUMMARY.value,
    FeedbackMode.OFF.value,
    FeedbackMode.PATTERN_LEDGER.value,
)


__all__ = [
    "FeedbackMode",
    "InternalEventSource",
    "MODULE_PRODUCED_STRINGS",
    "PLEDGER_SUMMARY_TEXT_MAX_LEN",
    "PLEDGER_SUMMARY_TEXT_PREFIX",
    "PROCESSING_WINDOW_CALL_BUDGET_MAX",
    "PROCESSING_WINDOW_PROVENANCE_PREFIX",
    "PROCESSING_WINDOW_SIZE_MAX",
    "RehearsalStep",
    "build_pledger_summary_text",
    "build_rehearsal_provenance",
    "plan_rehearsals",
    "validate_feedback_mode",
    "validate_processing_window_call_budget",
    "validate_processing_window_size",
    "validate_rehearsal_text",
]
