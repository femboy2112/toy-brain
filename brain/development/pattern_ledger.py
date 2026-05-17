"""Phase 3.12c Pattern Ledger substrate.

A bounded developmental ledger of recurring structural patterns observed
in stream/developmental histories. The ledger sits strictly *below*
truth, agency, ``PtCns``, ``MSI``, and semantic interpretation, and
strictly *above* ``TextStreamChunk`` / ``TextStreamHistory`` /
``StreamPromotionCandidate``. It is a summary substrate, not a runtime
control surface.

The module exposes frozen records and pure constructors:

* :class:`PatternLedgerSourceKind` — closed enum of accepted source
  kinds (``OPERATOR``, ``SYSTEM``, ``PROBE_ECHO``, ``GENERATED``).
* :class:`PatternLedgerSaturationState` — closed enum (``OPEN``,
  ``SATURATED``, ``QUIESCED``).
* :class:`PatternLedgerEntry` — strict frozen record for one
  recognized pattern, bounded printable identifiers, exact
  ``Fraction`` confidence, ``COGITO_ID`` rejection.
* :class:`PatternLedger` — copy-on-write bounded collection with the
  sole non-construction entry point ``observe(...)``.

The module is deliberately closed: no I/O, no network, no file, no
shell, no LLM, no TLICA runtime, no ``brain.tick`` import, no
``brain.ui`` import, no curses, no threading / asyncio / atexit /
signal / importlib. It imports only ``dataclasses``, ``enum``,
``fractions``, ``hashlib``, ``typing``, the bounded constants and
record types from :mod:`brain.development.text_stream`, and
``COGITO_ID`` from :mod:`brain.tlica.profile` for rejection checks.

The ledger surfaces bounded structural recurrence evidence; it does
NOT produce parse trees, language meaning, truth claims, ``PRESERVE``
/ ``DAMAGE`` judgments, agency witnesses, aggregate quality scores,
consciousness scores, sentience labels, or any subjective claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from hashlib import sha256
from typing import Optional

from brain.development.text_stream import (
    STREAM_PATTERN_RECURRENCE_MAX,
    STREAM_PATTERN_RECURRENCE_MIN,
    STREAM_PATTERN_SIG_MAX,
    STREAM_PROVENANCE_MAX_LEN,
    StreamPromotionCandidate,
    TextStreamChunk,
    TextStreamSource,
    extract_stream_features,
)
from brain.tlica.profile import COGITO_ID


# Bounded discipline locked by PHASE3_12_PATTERN_LEDGER_CATALOG_PATCH_PLAN.md.
PATTERN_LEDGER_MAX_ENTRIES: int = 64
PATTERN_LEDGER_EVIDENCE_MAX: int = 32
PATTERN_LEDGER_ID_MAX: int = 64
PATTERN_LEDGER_SIGNATURE_ELEM_MAX: int = 64


class PatternLedgerSourceKind(Enum):
    """Finite closed enumeration of pattern source kinds (I-PLEDGER-01).

    Mirrors :class:`TextStreamSource` so that every accepted
    ``TextStreamChunk.source`` value maps to exactly one ledger
    ``source_kind``.
    """

    OPERATOR = "operator"
    SYSTEM = "system"
    PROBE_ECHO = "probe_echo"
    GENERATED = "generated"


class PatternLedgerSaturationState(Enum):
    """Finite closed enumeration of saturation states (I-PLEDGER-02).

    ``OPEN`` — ``recurrence_count`` is strictly below
    ``STREAM_PATTERN_RECURRENCE_MAX``.

    ``SATURATED`` — ``recurrence_count`` is equal to
    ``STREAM_PATTERN_RECURRENCE_MAX``; further observations cannot
    advance the count.

    ``QUIESCED`` — reserved for a future quiescence rule (no new
    evidence within a bounded tick window). v1 ``observe(...)`` does
    not assign this state; direct construction with it is valid for
    callers who maintain quiescence externally.
    """

    OPEN = "open"
    SATURATED = "saturated"
    QUIESCED = "quiesced"


def _source_kind_from_stream_source(
    source: TextStreamSource,
) -> PatternLedgerSourceKind:
    """Map a :class:`TextStreamSource` value to its ledger counterpart.

    The two enums share value strings (``"operator"`` / ``"system"`` /
    ``"probe_echo"`` / ``"generated"``); this helper resolves by value
    so the runtime cannot silently drift if the upstream enum is
    re-ordered.
    """
    return PatternLedgerSourceKind(source.value)


def _require_int_nonneg(value: object, *, field: str, row_id: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(
            f"{row_id} violated: {field} must be int "
            f"(got {type(value).__name__})"
        )
    if value < 0:
        raise ValueError(f"{row_id} violated: {field} must be >= 0 (got {value})")
    return value


def _require_bounded_printable_id(
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
        raise ValueError(f"{row_id} violated: {field} must be printable")
    if len(value) > max_len:
        raise ValueError(
            f"{row_id} violated: {field} length {len(value)} exceeds max {max_len}"
        )
    if value == COGITO_ID:
        raise ValueError(
            f"{row_id} violated: {field} cannot equal COGITO_ID"
        )
    return value


def _require_signature(
    signature: object,
    *,
    row_id: str,
) -> tuple[str, ...]:
    if not isinstance(signature, tuple):
        raise ValueError(
            f"{row_id} violated: signature must be a tuple "
            f"(got {type(signature).__name__})"
        )
    if not signature:
        raise ValueError(f"{row_id} violated: signature must be non-empty")
    if len(signature) > STREAM_PATTERN_SIG_MAX:
        raise ValueError(
            f"{row_id} violated: signature length {len(signature)} exceeds "
            f"STREAM_PATTERN_SIG_MAX={STREAM_PATTERN_SIG_MAX}"
        )
    for item in signature:
        if not isinstance(item, str):
            raise ValueError(
                f"{row_id} violated: signature entries must be str "
                f"(got {type(item).__name__})"
            )
        if not item or not item.isprintable():
            raise ValueError(
                f"{row_id} violated: signature entries must be bounded "
                f"non-empty printable strings (got {item!r})"
            )
        if len(item) > PATTERN_LEDGER_SIGNATURE_ELEM_MAX:
            raise ValueError(
                f"{row_id} violated: signature entry length {len(item)} exceeds "
                f"PATTERN_LEDGER_SIGNATURE_ELEM_MAX="
                f"{PATTERN_LEDGER_SIGNATURE_ELEM_MAX}"
            )
        if item == COGITO_ID:
            raise ValueError(
                f"{row_id} violated: signature entry cannot equal COGITO_ID"
            )
    return signature


def _require_evidence_ids(
    ids: object,
    *,
    field: str,
    row_id: str,
) -> tuple[str, ...]:
    if not isinstance(ids, tuple):
        raise ValueError(
            f"{row_id} violated: {field} must be a tuple "
            f"(got {type(ids).__name__})"
        )
    if len(ids) > PATTERN_LEDGER_EVIDENCE_MAX:
        raise ValueError(
            f"{row_id} violated: {field} length {len(ids)} exceeds "
            f"PATTERN_LEDGER_EVIDENCE_MAX={PATTERN_LEDGER_EVIDENCE_MAX}"
        )
    seen: set[str] = set()
    for item in ids:
        _require_bounded_printable_id(
            item,
            field=f"{field} entry",
            row_id=row_id,
            max_len=STREAM_PROVENANCE_MAX_LEN,
        )
        if item in seen:
            raise ValueError(
                f"{row_id} violated: duplicate {field} entry {item!r}"
            )
        seen.add(item)
    return ids


def _confidence_for(recurrence_count: int) -> Fraction:
    """Exact ``Fraction`` confidence formula (I-PLEDGER-07).

    ``confidence = Fraction(recurrence_count, STREAM_PATTERN_RECURRENCE_MAX)``
    bounded in ``[0, 1]`` because callers cap ``recurrence_count`` at
    ``STREAM_PATTERN_RECURRENCE_MAX``. Uses no ``float``, no ``round``,
    no ``math.*`` — pure ``Fraction`` construction.
    """
    return Fraction(recurrence_count, STREAM_PATTERN_RECURRENCE_MAX)


def _saturation_for(recurrence_count: int) -> PatternLedgerSaturationState:
    """Return the ``OPEN`` / ``SATURATED`` state for a given count.

    v1 ``observe(...)`` never emits ``QUIESCED``; that state is
    reserved for a future quiescence rule.
    """
    if recurrence_count >= STREAM_PATTERN_RECURRENCE_MAX:
        return PatternLedgerSaturationState.SATURATED
    return PatternLedgerSaturationState.OPEN


def derive_pattern_signature(chunk: TextStreamChunk) -> tuple[str, ...]:
    """Derive the structural non-semantic signature for a chunk (I-PLEDGER-04).

    Uses only the exact ``int`` / ``Fraction`` features exposed by
    :func:`extract_stream_features`. No raw text payload is included.
    No semantic label, language label, readability score, or truth
    flag participates in the signature.
    """
    features = extract_stream_features(chunk)
    return (
        f"source:{chunk.source.value}",
        f"len:{len(chunk.text)}",
        f"lines:{features.line_count}",
        f"ws:{features.whitespace_run_count}",
        f"distinct:{features.distinct_char_count}",
        f"repeat:{features.repeat_ratio.numerator}/{features.repeat_ratio.denominator}",
    )


def derive_pattern_id(signature: tuple[str, ...]) -> str:
    """Deterministic pattern id (I-PLEDGER-05).

    ``pattern_id = "pledger:" + sha256(repr(signature).encode("utf-8")).hexdigest()[:16]``

    Same signature -> same pattern_id across runs, processes, and
    operating systems. No nondeterministic input (time, randomness,
    PID, hostname, ``id(...)``, env lookup) appears on this path.
    """
    _require_signature(signature, row_id="I-PLEDGER-05")
    digest = sha256(repr(signature).encode("utf-8")).hexdigest()[:16]
    return "pledger:" + digest


@dataclass(frozen=True, slots=True)
class PatternLedgerEntry:
    """Strict frozen record for one recognized structural pattern.

    Drives I-PLEDGER-03 (constructor enforces every bound),
    I-PLEDGER-06 (recurrence range), I-PLEDGER-07 (confidence
    formula), I-PLEDGER-10 (duplicate evidence rejection),
    I-PLEDGER-16 (no callable / handle / client field).
    """

    pattern_id: str
    signature: tuple[str, ...]
    evidence_chunk_ids: tuple[str, ...]
    evidence_candidate_ids: tuple[str, ...]
    recurrence_count: int
    first_seen_tick: int
    last_seen_tick: int
    source_kind: PatternLedgerSourceKind
    confidence: Fraction
    saturation_state: PatternLedgerSaturationState
    provenance: str

    def __post_init__(self) -> None:
        _require_bounded_printable_id(
            self.pattern_id,
            field="PatternLedgerEntry.pattern_id",
            row_id="I-PLEDGER-03",
            max_len=PATTERN_LEDGER_ID_MAX,
        )
        _require_signature(self.signature, row_id="I-PLEDGER-03")
        _require_evidence_ids(
            self.evidence_chunk_ids,
            field="PatternLedgerEntry.evidence_chunk_ids",
            row_id="I-PLEDGER-03",
        )
        _require_evidence_ids(
            self.evidence_candidate_ids,
            field="PatternLedgerEntry.evidence_candidate_ids",
            row_id="I-PLEDGER-03",
        )

        _require_int_nonneg(
            self.recurrence_count,
            field="PatternLedgerEntry.recurrence_count",
            row_id="I-PLEDGER-03",
        )
        if self.recurrence_count < STREAM_PATTERN_RECURRENCE_MIN:
            raise ValueError(
                "I-PLEDGER-03 violated: recurrence_count "
                f"{self.recurrence_count} below STREAM_PATTERN_RECURRENCE_MIN="
                f"{STREAM_PATTERN_RECURRENCE_MIN}"
            )
        if self.recurrence_count > STREAM_PATTERN_RECURRENCE_MAX:
            raise ValueError(
                "I-PLEDGER-03 violated: recurrence_count "
                f"{self.recurrence_count} exceeds STREAM_PATTERN_RECURRENCE_MAX="
                f"{STREAM_PATTERN_RECURRENCE_MAX}"
            )

        _require_int_nonneg(
            self.first_seen_tick,
            field="PatternLedgerEntry.first_seen_tick",
            row_id="I-PLEDGER-03",
        )
        _require_int_nonneg(
            self.last_seen_tick,
            field="PatternLedgerEntry.last_seen_tick",
            row_id="I-PLEDGER-03",
        )
        if self.last_seen_tick < self.first_seen_tick:
            raise ValueError(
                "I-PLEDGER-03 violated: last_seen_tick "
                f"{self.last_seen_tick} must be >= first_seen_tick "
                f"{self.first_seen_tick}"
            )

        if not isinstance(self.source_kind, PatternLedgerSourceKind):
            raise ValueError(
                "I-PLEDGER-03 violated: source_kind must be a "
                "PatternLedgerSourceKind "
                f"(got {type(self.source_kind).__name__})"
            )
        if not isinstance(self.saturation_state, PatternLedgerSaturationState):
            raise ValueError(
                "I-PLEDGER-03 violated: saturation_state must be a "
                "PatternLedgerSaturationState "
                f"(got {type(self.saturation_state).__name__})"
            )

        if not isinstance(self.confidence, Fraction):
            raise ValueError(
                "I-PLEDGER-03 violated: confidence must be Fraction "
                f"(got {type(self.confidence).__name__})"
            )
        if self.confidence < 0 or self.confidence > 1:
            raise ValueError(
                "I-PLEDGER-03 violated: confidence must lie in [0, 1] "
                f"(got {self.confidence})"
            )
        expected = _confidence_for(self.recurrence_count)
        if self.confidence != expected:
            raise ValueError(
                "I-PLEDGER-03 violated: confidence "
                f"{self.confidence} is not consistent with recurrence_count "
                f"{self.recurrence_count} "
                f"(expected {expected})"
            )

        _require_bounded_printable_id(
            self.provenance,
            field="PatternLedgerEntry.provenance",
            row_id="I-PLEDGER-03",
            max_len=STREAM_PROVENANCE_MAX_LEN,
        )


@dataclass(frozen=True, slots=True)
class PatternLedger:
    """Copy-on-write bounded ledger of :class:`PatternLedgerEntry`.

    Drives I-PLEDGER-08 (CoW + frozen + slotted), I-PLEDGER-11
    (evidence-list cap), I-PLEDGER-12 (max-entry refusal), and
    I-PLEDGER-09 (idempotent observe over duplicate evidence). The
    record stores no callable, file handle, socket, subprocess
    handle, ``pathlib.Path``, ``sqlite3.Connection``, curses object,
    or LLM client (I-PLEDGER-16).
    """

    entries: tuple[PatternLedgerEntry, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple):
            raise ValueError(
                "I-PLEDGER-08 violated: PatternLedger.entries must be a tuple "
                f"(got {type(self.entries).__name__})"
            )
        for entry in self.entries:
            if not isinstance(entry, PatternLedgerEntry):
                raise ValueError(
                    "I-PLEDGER-08 violated: PatternLedger.entries must contain "
                    f"PatternLedgerEntry values (got {type(entry).__name__})"
                )
        if len(self.entries) > PATTERN_LEDGER_MAX_ENTRIES:
            raise ValueError(
                "I-PLEDGER-08 violated: PatternLedger has "
                f"{len(self.entries)} entries; max is PATTERN_LEDGER_MAX_ENTRIES="
                f"{PATTERN_LEDGER_MAX_ENTRIES}"
            )
        # Pattern IDs are deterministic from signatures; the ledger
        # cannot host two entries with the same pattern_id.
        seen: set[str] = set()
        for entry in self.entries:
            if entry.pattern_id in seen:
                raise ValueError(
                    "I-PLEDGER-08 violated: duplicate pattern_id "
                    f"{entry.pattern_id!r} in PatternLedger.entries"
                )
            seen.add(entry.pattern_id)

    def find(self, pattern_id: str) -> Optional[PatternLedgerEntry]:
        """Return the entry whose ``pattern_id`` matches, or ``None``."""
        for entry in self.entries:
            if entry.pattern_id == pattern_id:
                return entry
        return None

    def observe(
        self,
        chunk: TextStreamChunk,
        candidate: StreamPromotionCandidate,
        *,
        current_tick: int,
    ) -> "PatternLedger":
        """Record one observation; return a new :class:`PatternLedger`.

        Drives I-PLEDGER-05 (deterministic id), I-PLEDGER-06
        (recurrence saturation), I-PLEDGER-07 (exact Fraction
        confidence), I-PLEDGER-08 (copy-on-write), I-PLEDGER-09
        (duplicate-evidence idempotence), I-PLEDGER-11 (evidence-list
        cap), I-PLEDGER-12 (max-entry refusal), and I-PLEDGER-13
        (sole non-construction entry point).

        Behavior:

        - Computes a structural signature from ``chunk`` features.
        - Computes a deterministic ``pattern_id``.
        - If the signature matches an existing entry, increments
          ``recurrence_count`` saturating at
          ``STREAM_PATTERN_RECURRENCE_MAX``, bumps ``last_seen_tick``,
          appends unique evidence ids while each evidence list is
          below ``PATTERN_LEDGER_EVIDENCE_MAX``, and recomputes
          ``confidence`` and ``saturation_state``. Duplicate
          ``chunk_id`` / ``candidate_id`` against the same entry is a
          no-op for evidence; ``recurrence_count`` still advances.
        - If the signature is new and ``len(self.entries) <
          PATTERN_LEDGER_MAX_ENTRIES``, constructs a fresh entry with
          ``recurrence_count = STREAM_PATTERN_RECURRENCE_MIN``.
        - If the signature is new and the ledger is at capacity,
          returns ``self`` unchanged. No eviction. No pruning. No
          overwrite.

        The method never mutates ``self`` and never reaches into
        ``BrainState``, ``MSI``, ``PtCns``, ``ContentRegistry``,
        ``latest_tick``, ``tick_counter``, ``event_queue``, source
        histories, ``tick()``, any LLM client, or any I/O surface.
        """
        if not isinstance(chunk, TextStreamChunk):
            raise TypeError(
                "PatternLedger.observe expects TextStreamChunk "
                f"(got {type(chunk).__name__})"
            )
        if not isinstance(candidate, StreamPromotionCandidate):
            raise TypeError(
                "PatternLedger.observe expects StreamPromotionCandidate "
                f"(got {type(candidate).__name__})"
            )
        _require_int_nonneg(
            current_tick,
            field="PatternLedger.observe.current_tick",
            row_id="I-PLEDGER-13",
        )

        signature = derive_pattern_signature(chunk)
        pattern_id = derive_pattern_id(signature)

        existing = self.find(pattern_id)
        if existing is not None:
            new_count = existing.recurrence_count + 1
            if new_count > STREAM_PATTERN_RECURRENCE_MAX:
                new_count = STREAM_PATTERN_RECURRENCE_MAX

            new_chunk_ids = existing.evidence_chunk_ids
            if (
                chunk.chunk_id not in new_chunk_ids
                and len(new_chunk_ids) < PATTERN_LEDGER_EVIDENCE_MAX
            ):
                new_chunk_ids = new_chunk_ids + (chunk.chunk_id,)

            new_cand_ids = existing.evidence_candidate_ids
            if (
                candidate.candidate_id not in new_cand_ids
                and len(new_cand_ids) < PATTERN_LEDGER_EVIDENCE_MAX
            ):
                new_cand_ids = new_cand_ids + (candidate.candidate_id,)

            new_last_tick = (
                current_tick
                if current_tick >= existing.last_seen_tick
                else existing.last_seen_tick
            )

            new_entry = PatternLedgerEntry(
                pattern_id=existing.pattern_id,
                signature=existing.signature,
                evidence_chunk_ids=new_chunk_ids,
                evidence_candidate_ids=new_cand_ids,
                recurrence_count=new_count,
                first_seen_tick=existing.first_seen_tick,
                last_seen_tick=new_last_tick,
                source_kind=existing.source_kind,
                confidence=_confidence_for(new_count),
                saturation_state=_saturation_for(new_count),
                provenance=existing.provenance,
            )
            new_entries = tuple(
                new_entry if entry.pattern_id == pattern_id else entry
                for entry in self.entries
            )
            return PatternLedger(entries=new_entries)

        # New signature.
        if len(self.entries) >= PATTERN_LEDGER_MAX_ENTRIES:
            # Hard refusal: do not evict, do not prune, do not
            # replace. Drives I-PLEDGER-12.
            return self

        initial_count = STREAM_PATTERN_RECURRENCE_MIN
        new_entry = PatternLedgerEntry(
            pattern_id=pattern_id,
            signature=signature,
            evidence_chunk_ids=(chunk.chunk_id,),
            evidence_candidate_ids=(candidate.candidate_id,),
            recurrence_count=initial_count,
            first_seen_tick=current_tick,
            last_seen_tick=current_tick,
            source_kind=_source_kind_from_stream_source(chunk.source),
            confidence=_confidence_for(initial_count),
            saturation_state=_saturation_for(initial_count),
            provenance=chunk.provenance,
        )
        return PatternLedger(entries=self.entries + (new_entry,))
