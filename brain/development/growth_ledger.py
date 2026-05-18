"""Phase 3.13 Growth Ledger substrate.

A bounded developmental record of accepted, constructor-validated growth
events produced by explicit successful runtime / developmental
transitions. The ledger sits strictly *below* mode-eval dispatch,
``PtCns``, ``MSI``, and any semantic interpretation, and strictly
*above* the operator session dispatcher surface that emits its events.
It is a referencing layer over bounded printable record identifiers, not
a runtime control surface.

The module exposes frozen records and pure constructors:

* :class:`GrowthEventType` — closed enum of v1 event types plus deferred
  members (deferred members exist in the enum for future compatibility
  but are never emitted by v1 dispatcher call sites).
* :class:`GrowthEventSource` — closed enum of v1 event sources plus
  deferred members on the same compatibility shape.
* :class:`GrowthEvent` — strict frozen / slotted record for one
  accepted event with a bounded printable ``event_id``,
  ``COGITO_ID`` rejection on every id-bearing field, closed-enum
  membership, non-negative int ``tick``, tuple references, and
  bounded printable ``provenance``.
* :class:`GrowthLedger` — copy-on-write bounded collection with the
  sole non-construction entry point :meth:`GrowthLedger.observe`.

The module is deliberately closed: no I/O, no network, no file, no
shell, no LLM, no TLICA runtime, no ``brain.tick`` import, no
``brain.ui`` import, no Pattern Ledger import, no Coherence Monitor
import, no ``brain.development.text_stream`` import, no curses, no
threading / asyncio / atexit / signal / importlib / math / fractions.
It imports only ``dataclasses``, ``enum``, ``hashlib``, ``typing``,
and ``COGITO_ID`` from :mod:`brain.tlica.profile` for rejection
checks.

The ledger records bounded historical evidence of accepted events. It
never produces parse trees, language semantics, mode-eval witnesses,
aggregate quality scores, growth scores, capability scores, maturity
scores, or any other scalar summary of interior state. Events store
bounded printable record identifier strings only; raw chunk text
already lives in the source histories and is never copied into a
ledger field. Profile and MSI addition events record bounded
identifier deltas only, not any kind of value judgement.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Optional

from brain.tlica.profile import COGITO_ID


# Bounded discipline locked by PHASE3_13_GROWTH_LEDGER_CORRIGENDA.md and
# PHASE3_13_GROWTH_LEDGER_CATALOG_PATCH_PLAN.md.
GROWTH_LEDGER_MAX_EVENTS: int = 256
GROWTH_LEDGER_REFERENCE_MAX: int = 8
GROWTH_LEDGER_ID_MAX: int = 64
GROWTH_LEDGER_PROVENANCE_MAX: int = 64
GROWTH_LEDGER_SOURCE_MAX: int = 64


class GrowthEventType(str, Enum):
    """Finite closed enumeration of growth event types (I-GROW-01).

    The seven v1 members below are the ones emitted by Phase 3.13
    dispatcher call sites:

    * ``STREAM_CHUNK_ACCEPTED``
    * ``PATTERN_ENTRY_CREATED``
    * ``PATTERN_ENTRY_UPDATED``
    * ``STREAM_PROMOTION_QUEUED``
    * ``TICK_SUCCEEDED``
    * ``PROFILE_DOMAIN_ADDED``
    * ``MSI_MEMBER_ADDED``

    The three deferred members (``SESSION_SAVED``, ``SESSION_LOADED``,
    ``COHERENCE_REPORT_BUILT``) exist on the closed enum for future
    compatibility but must not be emitted by any v1 call site. The
    Phase 3.13 session integration fixture asserts that
    ``/save-session``, ``/load-session``, and the coherence-report
    build path never produce events of those types.
    """

    STREAM_CHUNK_ACCEPTED = "stream_chunk_accepted"
    PATTERN_ENTRY_CREATED = "pattern_entry_created"
    PATTERN_ENTRY_UPDATED = "pattern_entry_updated"
    STREAM_PROMOTION_QUEUED = "stream_promotion_queued"
    TICK_SUCCEEDED = "tick_succeeded"
    PROFILE_DOMAIN_ADDED = "profile_domain_added"
    MSI_MEMBER_ADDED = "msi_member_added"
    SESSION_SAVED = "session_saved"
    SESSION_LOADED = "session_loaded"
    COHERENCE_REPORT_BUILT = "coherence_report_built"


class GrowthEventSource(str, Enum):
    """Finite closed enumeration of growth event sources (I-GROW-02).

    The four v1 members below label the dispatchers and helpers that
    emit events in Phase 3.13:

    * ``STREAM_APPEND``         — emitted by ``_dispatch_stream_append``
    * ``PATTERN_LEDGER_OBSERVE`` — emitted alongside a Pattern Ledger
      delta inside ``_dispatch_stream_append``
    * ``STREAM_PROMOTE``        — emitted by ``_dispatch_stream_promote``
    * ``STEP_DISPATCH``         — emitted by ``_dispatch_step``

    The three deferred sources (``PERSISTENCE_SAVE``,
    ``PERSISTENCE_LOAD``, ``COHERENCE_MONITOR``) exist on the closed
    enum for future compatibility but must not be emitted by any v1
    call site.
    """

    STREAM_APPEND = "stream_append"
    PATTERN_LEDGER_OBSERVE = "pattern_ledger_observe"
    STREAM_PROMOTE = "stream_promote"
    STEP_DISPATCH = "step_dispatch"
    PERSISTENCE_SAVE = "persistence_save"
    PERSISTENCE_LOAD = "persistence_load"
    COHERENCE_MONITOR = "coherence_monitor"


# ---------------------------------------------------------------------------
# Bounded primitive validators.
# ---------------------------------------------------------------------------


def _require_int_nonneg(value: object, *, field: str, row_id: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(
            f"{row_id} violated: {field} must be int "
            f"(got {type(value).__name__})"
        )
    if value < 0:
        raise ValueError(
            f"{row_id} violated: {field} must be >= 0 (got {value})"
        )
    return value


def _require_bounded_printable(
    value: object,
    *,
    field: str,
    row_id: str,
    max_len: int,
) -> str:
    if not isinstance(value, str):
        raise ValueError(
            f"{row_id} violated: {field} must be str "
            f"(got {type(value).__name__})"
        )
    if not value:
        raise ValueError(f"{row_id} violated: {field} must be non-empty")
    if not value.isprintable():
        raise ValueError(
            f"{row_id} violated: {field} must be printable text"
        )
    if len(value) > max_len:
        raise ValueError(
            f"{row_id} violated: {field} length {len(value)} exceeds "
            f"max {max_len}"
        )
    if value == COGITO_ID:
        raise ValueError(
            f"{row_id} violated: {field} cannot equal COGITO_ID"
        )
    return value


def _require_references(
    value: object,
    *,
    row_id: str,
) -> tuple[str, ...]:
    """Validate the references tuple shape AND uniqueness.

    Drives I-GROW-03 and LOCK G's fixed validation order: references
    uniqueness is checked BEFORE any ``event_id`` derivation, so a
    duplicate within one tuple raises before the deterministic hash
    is computed.
    """
    if not isinstance(value, tuple):
        raise ValueError(
            f"{row_id} violated: references must be a tuple "
            f"(got {type(value).__name__})"
        )
    if len(value) > GROWTH_LEDGER_REFERENCE_MAX:
        raise ValueError(
            f"{row_id} violated: references length {len(value)} exceeds "
            f"GROWTH_LEDGER_REFERENCE_MAX={GROWTH_LEDGER_REFERENCE_MAX}"
        )
    seen: set[str] = set()
    for item in value:
        _require_bounded_printable(
            item,
            field="references entry",
            row_id=row_id,
            max_len=GROWTH_LEDGER_ID_MAX,
        )
        if item in seen:
            raise ValueError(
                f"{row_id} violated: duplicate references entry {item!r}"
            )
        seen.add(item)
    return value


# ---------------------------------------------------------------------------
# Deterministic event id (I-GROW-04).
# ---------------------------------------------------------------------------


def derive_growth_event_id(
    *,
    event_type: GrowthEventType,
    tick: int,
    source: GrowthEventSource,
    references: tuple[str, ...],
    provenance: str,
) -> str:
    """Deterministic event_id derivation (I-GROW-04).

    Returns ``"growth:" + sha256(repr((event_type.value, tick,
    source.value, references, provenance)).encode("utf-8")).hexdigest()[:16]``.
    The inputs are the closed immutable acceptance payload; no
    ``dict`` / ``set`` / raw object / time / random / PID / hostname /
    ``id(...)`` / env lookup participates. Same payload yields the same
    id across runs, processes, and operating systems.
    """
    if not isinstance(event_type, GrowthEventType):
        raise ValueError(
            "I-GROW-04 violated: event_type must be a GrowthEventType "
            f"(got {type(event_type).__name__})"
        )
    if not isinstance(source, GrowthEventSource):
        raise ValueError(
            "I-GROW-04 violated: source must be a GrowthEventSource "
            f"(got {type(source).__name__})"
        )
    payload = (
        event_type.value,
        tick,
        source.value,
        references,
        provenance,
    )
    digest = sha256(repr(payload).encode("utf-8")).hexdigest()[:16]
    return "growth:" + digest


# ---------------------------------------------------------------------------
# GrowthEvent record.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GrowthEvent:
    """Strict frozen record for one accepted growth event.

    Drives I-GROW-03 (constructor enforces every bound), I-GROW-12
    (no callable / handle / client field), I-GROW-19 (no banned
    label appears on any bounded printable surface).

    Fields are exactly the closed immutable acceptance payload:

    * ``event_id`` — bounded printable, non-empty, not equal to
      ``COGITO_ID``, ``len <= GROWTH_LEDGER_ID_MAX``.
    * ``event_type`` — a :class:`GrowthEventType` member.
    * ``tick`` — non-negative int (and not ``bool``).
    * ``source`` — a :class:`GrowthEventSource` member.
    * ``references`` — ``tuple[str, ...]`` with at most
      ``GROWTH_LEDGER_REFERENCE_MAX`` entries; each entry is a bounded
      printable identifier, non-empty, not equal to ``COGITO_ID``,
      ``len <= GROWTH_LEDGER_ID_MAX``; entries are pairwise unique.
    * ``provenance`` — bounded printable, non-empty, not equal to
      ``COGITO_ID``, ``len <= GROWTH_LEDGER_PROVENANCE_MAX``.

    No field is a callable, file handle, socket, subprocess handle,
    ``pathlib.Path``, ``sqlite3.Connection`` / ``Cursor``, curses
    object, LLM client-shaped object, or object exposing
    ``eval_consistency``.
    """

    event_id: str
    event_type: GrowthEventType
    tick: int
    source: GrowthEventSource
    references: tuple[str, ...]
    provenance: str

    def __post_init__(self) -> None:
        _require_bounded_printable(
            self.event_id,
            field="GrowthEvent.event_id",
            row_id="I-GROW-03",
            max_len=GROWTH_LEDGER_ID_MAX,
        )
        if not isinstance(self.event_type, GrowthEventType):
            raise ValueError(
                "I-GROW-03 violated: event_type must be a GrowthEventType "
                f"(got {type(self.event_type).__name__})"
            )
        _require_int_nonneg(
            self.tick,
            field="GrowthEvent.tick",
            row_id="I-GROW-03",
        )
        if not isinstance(self.source, GrowthEventSource):
            raise ValueError(
                "I-GROW-03 violated: source must be a GrowthEventSource "
                f"(got {type(self.source).__name__})"
            )
        _require_references(self.references, row_id="I-GROW-03")
        _require_bounded_printable(
            self.provenance,
            field="GrowthEvent.provenance",
            row_id="I-GROW-03",
            max_len=GROWTH_LEDGER_PROVENANCE_MAX,
        )


# ---------------------------------------------------------------------------
# GrowthLedger collection.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GrowthLedger:
    """Copy-on-write bounded ledger of :class:`GrowthEvent`.

    Drives I-GROW-05 (frozen / slotted / copy-on-write), I-GROW-06
    (idempotent duplicate observe), I-GROW-07 (direct construction
    with duplicate ``event_id`` rejects), I-GROW-08 (hard refusal at
    ``GROWTH_LEDGER_MAX_EVENTS``), I-GROW-09 (deterministic
    ``counts_by_type``), I-GROW-12 (no unsafe resources in any field),
    I-GROW-20 (no runtime coupling).

    The record stores no callable, file handle, socket, subprocess
    handle, ``pathlib.Path``, ``sqlite3.Connection``, curses object,
    or LLM client. :meth:`observe` is the sole non-construction entry
    point.
    """

    events: tuple[GrowthEvent, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.events, tuple):
            raise ValueError(
                "I-GROW-05 violated: GrowthLedger.events must be a tuple "
                f"(got {type(self.events).__name__})"
            )
        for evt in self.events:
            if not isinstance(evt, GrowthEvent):
                raise ValueError(
                    "I-GROW-05 violated: GrowthLedger.events must contain "
                    f"GrowthEvent values (got {type(evt).__name__})"
                )
        if len(self.events) > GROWTH_LEDGER_MAX_EVENTS:
            raise ValueError(
                "I-GROW-05 violated: GrowthLedger has "
                f"{len(self.events)} events; max is "
                f"GROWTH_LEDGER_MAX_EVENTS={GROWTH_LEDGER_MAX_EVENTS}"
            )
        seen: set[str] = set()
        for evt in self.events:
            if evt.event_id in seen:
                raise ValueError(
                    "I-GROW-07 violated: duplicate event_id "
                    f"{evt.event_id!r} in GrowthLedger.events"
                )
            seen.add(evt.event_id)

    def find(self, event_id: str) -> Optional[GrowthEvent]:
        """Return the event whose ``event_id`` matches, or ``None``."""
        for evt in self.events:
            if evt.event_id == event_id:
                return evt
        return None

    def observe(
        self,
        *,
        event_type: GrowthEventType,
        tick: int,
        source: GrowthEventSource,
        references: tuple[str, ...],
        provenance: str,
    ) -> "GrowthLedger":
        """Record one observation; return a new :class:`GrowthLedger`.

        Drives I-GROW-04 (deterministic event_id), I-GROW-05
        (copy-on-write), I-GROW-06 (idempotent on duplicate event_id),
        I-GROW-08 (hard refusal at cap), I-GROW-09 (counts surface),
        I-GROW-20 (no runtime coupling).

        Fixed validation order (LOCK G):

        1. saturation check (if at cap, return ``self`` unchanged with
           no further work)
        2. ``event_type`` and ``source`` enum membership
        3. ``tick`` non-negative int (and not ``bool``)
        4. ``references`` tuple shape
        5. ``references`` pairwise uniqueness (BEFORE event_id derivation)
        6. ``provenance`` bounded printable
        7. ``event_id`` derivation via :func:`derive_growth_event_id`
        8. duplicate-event idempotency check (if ``event_id`` is
           already present, return ``self`` unchanged)
        9. append (copy-on-write; return a new :class:`GrowthLedger`)

        :meth:`observe` never mutates ``self`` and never reaches into
        ``BrainState``, ``MSI``, ``PtCns``, ``ContentRegistry``,
        ``latest_tick``, ``tick_counter``, ``event_queue``, source
        histories, the Pattern Ledger, the Coherence Monitor records,
        the persistence config, the autosave config, ``tick()``, any
        LLM client, or any I/O surface. The saturation early-return
        does not change the dispatcher's return value, the
        user-facing status / error text, or any kernel surface; it
        only refuses to append a new event to the ledger.
        """
        # Step 1: saturation.
        if len(self.events) >= GROWTH_LEDGER_MAX_EVENTS:
            return self
        # Step 2: enum membership for event_type and source.
        if not isinstance(event_type, GrowthEventType):
            raise ValueError(
                "I-GROW-03 violated: event_type must be a GrowthEventType "
                f"(got {type(event_type).__name__})"
            )
        if not isinstance(source, GrowthEventSource):
            raise ValueError(
                "I-GROW-03 violated: source must be a GrowthEventSource "
                f"(got {type(source).__name__})"
            )
        # Step 3: non-negative int tick.
        _require_int_nonneg(
            tick,
            field="GrowthLedger.observe.tick",
            row_id="I-GROW-03",
        )
        # Steps 4 + 5: references shape and uniqueness BEFORE id derivation.
        _require_references(references, row_id="I-GROW-03")
        # Step 6: provenance.
        _require_bounded_printable(
            provenance,
            field="GrowthLedger.observe.provenance",
            row_id="I-GROW-03",
            max_len=GROWTH_LEDGER_PROVENANCE_MAX,
        )
        # Step 7: derive event_id.
        event_id = derive_growth_event_id(
            event_type=event_type,
            tick=tick,
            source=source,
            references=references,
            provenance=provenance,
        )
        # Step 8: duplicate-event idempotency.
        if self.find(event_id) is not None:
            return self
        # Step 9: copy-on-write append.
        new_event = GrowthEvent(
            event_id=event_id,
            event_type=event_type,
            tick=tick,
            source=source,
            references=references,
            provenance=provenance,
        )
        return GrowthLedger(events=self.events + (new_event,))

    def counts_by_type(self) -> tuple[tuple[str, int], ...]:
        """Deterministic counts over the closed :class:`GrowthEventType`.

        Returns a ``tuple[tuple[str, int], ...]`` ordered by the closed
        enum's declaration order. One pair per member, including
        deferred members (count of ``0`` when never emitted). This is
        a factual summary, NOT a score; no scalar field summarizes the
        ledger.
        """
        counts: dict[str, int] = {
            member.value: 0 for member in GrowthEventType
        }
        for evt in self.events:
            counts[evt.event_type.value] += 1
        return tuple(
            (member.value, counts[member.value]) for member in GrowthEventType
        )


__all__ = [
    "GROWTH_LEDGER_ID_MAX",
    "GROWTH_LEDGER_MAX_EVENTS",
    "GROWTH_LEDGER_PROVENANCE_MAX",
    "GROWTH_LEDGER_REFERENCE_MAX",
    "GROWTH_LEDGER_SOURCE_MAX",
    "GrowthEvent",
    "GrowthEventSource",
    "GrowthEventType",
    "GrowthLedger",
    "derive_growth_event_id",
]
