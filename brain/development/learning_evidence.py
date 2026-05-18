"""Phase 3.22b Learning Evidence — bounded session-local evidence layer.

This module records observable state transitions of the operator
session and the REPL bridge as bounded, deterministic, printable
``LearningEvidenceRecord`` rows. Its purpose is to make the
operational claim "this runtime accumulates structural records and
reuses them in later interactions" auditable and replayable.

This is NOT memory in the psychological sense. This is NOT semantic
understanding. This is NOT agency, will, desire, belief, or intent.

Non-claim discipline (binding):

* No claim of cognitive properties is made by this module.
* Every produced string passes the canonical
  ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``
  audit (case-insensitive substring).

Closed import set:

* ``__future__``, ``dataclasses``, ``enum``, ``hashlib``, ``typing``
* ``brain.development.abstract_pattern``
* ``brain.development.coherence_monitor`` (``_FORBIDDEN_NON_CLAIM_TERMS``)

No ``brain.llm.*``. No ``brain.tick``. No curses, subprocess, socket,
urllib, http, requests, tempfile, shutil, threading, asyncio,
atexit, signal, importlib, time, random.

Drives ``I-AGENTLEARN-02..07`` and contributes to ``I-AGENTLEARN-11``.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from brain.development.abstract_pattern import (
    ABSTRACT_PATTERN_DIGEST_HEX_LEN,
    AbstractPatternSignature,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS


# ---------------------------------------------------------------------------
# Bounded constants.
# ---------------------------------------------------------------------------

LEARNING_TRACE_MAX_RECORDS: int = 256
LEARNING_RECORD_SUMMARY_MAX_LEN: int = 240
LEARNING_FACT_KEY_MAX_LEN: int = 32
LEARNING_FACT_VALUE_MAX_LEN: int = 64
LEARNING_FACTS_MAX_ENTRIES: int = 8
LEARNING_DIGEST_HEX_LEN: int = 16
LEARNING_INTERACTION_ID_MAX_LEN: int = 64
LEARNING_REPORT_SUMMARY_MAX_LEN: int = 320
LEARNING_EVIDENCE_MODULE_VERSION: str = "phase3.22b.v1"


# ---------------------------------------------------------------------------
# Forbidden-term audit (single point).
# ---------------------------------------------------------------------------


def _text_has_forbidden_term(text: str) -> Optional[str]:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


# ---------------------------------------------------------------------------
# Closed enum.
# ---------------------------------------------------------------------------


class LearningEvidenceKind(str, Enum):
    """Closed enum of evidence-record kinds.

    See docs/campaigns/phase3_22/PHASE3_22B_LEARNING_PROOF_SPEC.md
    for per-kind semantics.
    """

    OBSERVED = "observed"
    RECURRENCE_INCREASED = "recurrence_increased"
    ABSTRACT_PATTERN_ACQUIRED = "abstract_pattern_acquired"
    ABSTRACT_PATTERN_REUSED = "abstract_pattern_reused"
    TRANSFER_RECOGNIZED = "transfer_recognized"
    REPL_CORRECTION_APPLIED = "repl_correction_applied"
    DIMINISHING_RETURNS_UPDATED = "diminishing_returns_updated"
    LIMITATION_RECORDED = "limitation_recorded"


# ---------------------------------------------------------------------------
# Frozen records.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LearningEvidenceRecord:
    """One bounded record describing a single state transition.

    The record is the only evidence shape; higher-level "knowledge"
    or "memory" is NOT modelled. Every field is bounded; nothing
    references mutable state.
    """

    kind: LearningEvidenceKind
    interaction_id: str
    abstract_pattern_digest: str
    pattern_id: str
    pre_facts: tuple[tuple[str, str], ...]
    post_facts: tuple[tuple[str, str], ...]
    summary: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, LearningEvidenceKind):
            raise TypeError(
                "I-AGENTLEARN-03 violated: LearningEvidenceRecord.kind must "
                "be a LearningEvidenceKind member"
            )
        if (
            not isinstance(self.interaction_id, str)
            or not self.interaction_id
            or not self.interaction_id.isprintable()
            or len(self.interaction_id) > LEARNING_INTERACTION_ID_MAX_LEN
        ):
            raise ValueError(
                "I-AGENTLEARN-03 violated: LearningEvidenceRecord."
                "interaction_id must be non-empty printable text under "
                f"{LEARNING_INTERACTION_ID_MAX_LEN} chars"
            )
        if not isinstance(self.abstract_pattern_digest, str) or len(
            self.abstract_pattern_digest
        ) not in (0, ABSTRACT_PATTERN_DIGEST_HEX_LEN):
            raise ValueError(
                "I-AGENTLEARN-03 violated: LearningEvidenceRecord."
                "abstract_pattern_digest must be empty or "
                f"{ABSTRACT_PATTERN_DIGEST_HEX_LEN}-char hex"
            )
        if not isinstance(self.pattern_id, str) or len(self.pattern_id) > 64:
            raise ValueError(
                "I-AGENTLEARN-03 violated: LearningEvidenceRecord."
                "pattern_id must be a string under 64 chars"
            )
        if self.pattern_id and not self.pattern_id.isprintable():
            raise ValueError(
                "I-AGENTLEARN-03 violated: LearningEvidenceRecord."
                "pattern_id must be printable"
            )
        for name, facts in (
            ("pre_facts", self.pre_facts),
            ("post_facts", self.post_facts),
        ):
            if not isinstance(facts, tuple):
                raise TypeError(
                    "I-AGENTLEARN-03 violated: LearningEvidenceRecord."
                    f"{name} must be a tuple"
                )
            if len(facts) > LEARNING_FACTS_MAX_ENTRIES:
                raise ValueError(
                    "I-AGENTLEARN-03 violated: LearningEvidenceRecord."
                    f"{name} length exceeds {LEARNING_FACTS_MAX_ENTRIES}"
                )
            for entry in facts:
                if not isinstance(entry, tuple) or len(entry) != 2:
                    raise TypeError(
                        "I-AGENTLEARN-03 violated: LearningEvidenceRecord."
                        f"{name} entries must be (str, str) pairs"
                    )
                key, value = entry
                if (
                    not isinstance(key, str)
                    or not key
                    or not key.isprintable()
                    or len(key) > LEARNING_FACT_KEY_MAX_LEN
                ):
                    raise ValueError(
                        "I-AGENTLEARN-03 violated: LearningEvidenceRecord."
                        f"{name} key must be non-empty printable under "
                        f"{LEARNING_FACT_KEY_MAX_LEN} chars"
                    )
                if (
                    not isinstance(value, str)
                    or len(value) > LEARNING_FACT_VALUE_MAX_LEN
                ):
                    raise ValueError(
                        "I-AGENTLEARN-03 violated: LearningEvidenceRecord."
                        f"{name} value must be a string under "
                        f"{LEARNING_FACT_VALUE_MAX_LEN} chars"
                    )
                if value and not value.isprintable():
                    raise ValueError(
                        "I-AGENTLEARN-03 violated: LearningEvidenceRecord."
                        f"{name} value must be printable"
                    )
                term = _text_has_forbidden_term(value)
                if term is not None:
                    raise ValueError(
                        "I-AGENTLEARN-03 violated: LearningEvidenceRecord."
                        f"{name} value contains forbidden non-claim term "
                        f"{term!r}"
                    )
        if (
            not isinstance(self.summary, str)
            or not self.summary
            or not self.summary.isprintable()
            or len(self.summary) > LEARNING_RECORD_SUMMARY_MAX_LEN
        ):
            raise ValueError(
                "I-AGENTLEARN-03 violated: LearningEvidenceRecord.summary "
                "must be non-empty printable text under "
                f"{LEARNING_RECORD_SUMMARY_MAX_LEN} chars"
            )
        term = _text_has_forbidden_term(self.summary)
        if term is not None:
            raise ValueError(
                "I-AGENTLEARN-03 violated: LearningEvidenceRecord.summary "
                f"contains forbidden non-claim term {term!r}"
            )


@dataclass(frozen=True, slots=True)
class LearningEvidenceTrace:
    """A bounded tuple of LearningEvidenceRecord entries."""

    records: tuple[LearningEvidenceRecord, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.records, tuple):
            raise TypeError(
                "I-AGENTLEARN-03 violated: LearningEvidenceTrace.records "
                "must be a tuple"
            )
        if len(self.records) > LEARNING_TRACE_MAX_RECORDS:
            raise ValueError(
                "I-AGENTLEARN-03 violated: LearningEvidenceTrace.records "
                f"length exceeds {LEARNING_TRACE_MAX_RECORDS}"
            )
        for r in self.records:
            if not isinstance(r, LearningEvidenceRecord):
                raise TypeError(
                    "I-AGENTLEARN-03 violated: LearningEvidenceTrace.records "
                    "entries must be LearningEvidenceRecord"
                )

    def filter_kind(
        self, kind: LearningEvidenceKind
    ) -> "LearningEvidenceTrace":
        return LearningEvidenceTrace(
            records=tuple(r for r in self.records if r.kind is kind)
        )

    def first_for_digest(
        self, abstract_pattern_digest: str
    ) -> Optional[LearningEvidenceRecord]:
        for r in self.records:
            if r.abstract_pattern_digest == abstract_pattern_digest:
                return r
        return None

    def kind_counts(self) -> dict[LearningEvidenceKind, int]:
        counts: dict[LearningEvidenceKind, int] = {}
        for r in self.records:
            counts[r.kind] = counts.get(r.kind, 0) + 1
        return counts


@dataclass(frozen=True, slots=True)
class LearningProofReport:
    """A bounded printable proof-style report over a trace."""

    trace: LearningEvidenceTrace
    record_total: int
    observed_count: int
    recurrence_increased_count: int
    abstract_pattern_acquired_count: int
    abstract_pattern_reused_count: int
    transfer_recognized_count: int
    repl_correction_applied_count: int
    diminishing_returns_updated_count: int
    limitation_recorded_count: int
    digest_hex16: str
    summary_line: str

    def __post_init__(self) -> None:
        if not isinstance(self.trace, LearningEvidenceTrace):
            raise TypeError(
                "I-AGENTLEARN-04 violated: LearningProofReport.trace must "
                "be a LearningEvidenceTrace"
            )
        for name, value in (
            ("record_total", self.record_total),
            ("observed_count", self.observed_count),
            ("recurrence_increased_count", self.recurrence_increased_count),
            (
                "abstract_pattern_acquired_count",
                self.abstract_pattern_acquired_count,
            ),
            (
                "abstract_pattern_reused_count",
                self.abstract_pattern_reused_count,
            ),
            (
                "transfer_recognized_count",
                self.transfer_recognized_count,
            ),
            (
                "repl_correction_applied_count",
                self.repl_correction_applied_count,
            ),
            (
                "diminishing_returns_updated_count",
                self.diminishing_returns_updated_count,
            ),
            ("limitation_recorded_count", self.limitation_recorded_count),
        ):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(
                    "I-AGENTLEARN-04 violated: LearningProofReport."
                    f"{name} must be int"
                )
            if value < 0:
                raise ValueError(
                    "I-AGENTLEARN-04 violated: LearningProofReport."
                    f"{name} must be non-negative"
                )
        if (
            not isinstance(self.digest_hex16, str)
            or len(self.digest_hex16) != LEARNING_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-AGENTLEARN-04 violated: LearningProofReport."
                "digest_hex16 must be a 16-char hex string"
            )
        if (
            not isinstance(self.summary_line, str)
            or not self.summary_line
            or not self.summary_line.isprintable()
            or len(self.summary_line) > LEARNING_REPORT_SUMMARY_MAX_LEN
        ):
            raise ValueError(
                "I-AGENTLEARN-04 violated: LearningProofReport."
                "summary_line must be non-empty printable text under "
                f"{LEARNING_REPORT_SUMMARY_MAX_LEN} chars"
            )
        term = _text_has_forbidden_term(self.summary_line)
        if term is not None:
            raise ValueError(
                "I-AGENTLEARN-04 violated: LearningProofReport."
                f"summary_line contains forbidden non-claim term {term!r}"
            )


# ---------------------------------------------------------------------------
# Constructors / pure helpers.
# ---------------------------------------------------------------------------


def empty_trace() -> LearningEvidenceTrace:
    return LearningEvidenceTrace(records=())


def append_record(
    trace: LearningEvidenceTrace,
    record: LearningEvidenceRecord,
) -> LearningEvidenceTrace:
    """Return a new trace with one record appended (bounded)."""
    if not isinstance(trace, LearningEvidenceTrace):
        raise TypeError(
            "I-AGENTLEARN-03 violated: append_record trace must be a "
            "LearningEvidenceTrace"
        )
    if not isinstance(record, LearningEvidenceRecord):
        raise TypeError(
            "I-AGENTLEARN-03 violated: append_record record must be a "
            "LearningEvidenceRecord"
        )
    if len(trace.records) >= LEARNING_TRACE_MAX_RECORDS:
        # Bounded ledger: drop the oldest record (FIFO).
        new_records = trace.records[1:] + (record,)
    else:
        new_records = trace.records + (record,)
    return LearningEvidenceTrace(records=new_records)


def _facts_str(facts: tuple[tuple[str, str], ...]) -> str:
    parts = [f"{k}={v}" for k, v in facts]
    return ",".join(parts)


def _serialize_record(r: LearningEvidenceRecord) -> str:
    return (
        f"kind={r.kind.value}|"
        f"iid={r.interaction_id}|"
        f"adg={r.abstract_pattern_digest}|"
        f"pid={r.pattern_id}|"
        f"pre={_facts_str(r.pre_facts)}|"
        f"post={_facts_str(r.post_facts)}|"
        f"sum={r.summary}"
    )


def _compute_trace_digest(trace: LearningEvidenceTrace) -> str:
    payload = "\n".join(_serialize_record(r) for r in trace.records).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()[:LEARNING_DIGEST_HEX_LEN]


def build_learning_proof_report(
    trace: LearningEvidenceTrace,
) -> LearningProofReport:
    """Deterministically build a proof-style report over the trace."""
    if not isinstance(trace, LearningEvidenceTrace):
        raise TypeError(
            "I-AGENTLEARN-04 violated: build_learning_proof_report trace "
            "must be a LearningEvidenceTrace"
        )
    counts = trace.kind_counts()
    observed = counts.get(LearningEvidenceKind.OBSERVED, 0)
    recurrence_increased = counts.get(
        LearningEvidenceKind.RECURRENCE_INCREASED, 0
    )
    abstract_acquired = counts.get(
        LearningEvidenceKind.ABSTRACT_PATTERN_ACQUIRED, 0
    )
    abstract_reused = counts.get(
        LearningEvidenceKind.ABSTRACT_PATTERN_REUSED, 0
    )
    transfer = counts.get(LearningEvidenceKind.TRANSFER_RECOGNIZED, 0)
    correction = counts.get(LearningEvidenceKind.REPL_CORRECTION_APPLIED, 0)
    diminishing = counts.get(
        LearningEvidenceKind.DIMINISHING_RETURNS_UPDATED, 0
    )
    limitation = counts.get(LearningEvidenceKind.LIMITATION_RECORDED, 0)
    record_total = len(trace.records)
    digest = _compute_trace_digest(trace)
    summary = (
        f"learning-proof records={record_total} "
        f"observed={observed} "
        f"recurrence_increased={recurrence_increased} "
        f"abstract_acquired={abstract_acquired} "
        f"abstract_reused={abstract_reused} "
        f"transfer={transfer} "
        f"corrections={correction} "
        f"diminishing={diminishing} "
        f"limitations={limitation} "
        f"digest={digest}"
    )
    if len(summary) > LEARNING_REPORT_SUMMARY_MAX_LEN:
        summary = summary[: LEARNING_REPORT_SUMMARY_MAX_LEN - 4] + " ..."
    return LearningProofReport(
        trace=trace,
        record_total=record_total,
        observed_count=observed,
        recurrence_increased_count=recurrence_increased,
        abstract_pattern_acquired_count=abstract_acquired,
        abstract_pattern_reused_count=abstract_reused,
        transfer_recognized_count=transfer,
        repl_correction_applied_count=correction,
        diminishing_returns_updated_count=diminishing,
        limitation_recorded_count=limitation,
        digest_hex16=digest,
        summary_line=summary,
    )


# ---------------------------------------------------------------------------
# Builder helpers for specific record kinds.
# ---------------------------------------------------------------------------


def _bounded_value(value: str) -> str:
    if len(value) > LEARNING_FACT_VALUE_MAX_LEN:
        return value[: LEARNING_FACT_VALUE_MAX_LEN - 3] + "..."
    return value


def make_observed_record(
    *,
    interaction_id: str,
    signature: AbstractPatternSignature,
    pattern_id: str,
    pre_entry_count: int,
    post_entry_count: int,
) -> LearningEvidenceRecord:
    summary = (
        f"observed novel input shape={signature.shape!r} "
        f"class={signature.classification} "
        f"digest={signature.digest_hex16}"
    )
    return LearningEvidenceRecord(
        kind=LearningEvidenceKind.OBSERVED,
        interaction_id=interaction_id,
        abstract_pattern_digest=signature.digest_hex16,
        pattern_id=pattern_id,
        pre_facts=(("entries", str(pre_entry_count)),),
        post_facts=(("entries", str(post_entry_count)),),
        summary=summary,
    )


def make_recurrence_increased_record(
    *,
    interaction_id: str,
    signature: AbstractPatternSignature,
    pattern_id: str,
    pre_recurrence: int,
    post_recurrence: int,
) -> LearningEvidenceRecord:
    summary = (
        f"seed recurrence climbed from {pre_recurrence} to "
        f"{post_recurrence} for pid={pattern_id}"
    )
    return LearningEvidenceRecord(
        kind=LearningEvidenceKind.RECURRENCE_INCREASED,
        interaction_id=interaction_id,
        abstract_pattern_digest=signature.digest_hex16,
        pattern_id=pattern_id,
        pre_facts=(("seed_recur", str(pre_recurrence)),),
        post_facts=(("seed_recur", str(post_recurrence)),),
        summary=summary,
    )


def make_abstract_pattern_acquired_record(
    *,
    interaction_id: str,
    signature: AbstractPatternSignature,
    pattern_id: str,
) -> LearningEvidenceRecord:
    summary = (
        f"abstract pattern {signature.digest_hex16} acquired "
        f"shape={signature.shape!r} class={signature.classification}"
    )
    return LearningEvidenceRecord(
        kind=LearningEvidenceKind.ABSTRACT_PATTERN_ACQUIRED,
        interaction_id=interaction_id,
        abstract_pattern_digest=signature.digest_hex16,
        pattern_id=pattern_id,
        pre_facts=(("acquired_digests_before", "0"),),
        post_facts=(("acquired_digests_after", "1"),),
        summary=summary,
    )


def make_abstract_pattern_reused_record(
    *,
    interaction_id: str,
    signature: AbstractPatternSignature,
    pattern_id: str,
    reuse_count: int,
) -> LearningEvidenceRecord:
    summary = (
        f"abstract pattern {signature.digest_hex16} reused "
        f"(this is reuse {reuse_count})"
    )
    return LearningEvidenceRecord(
        kind=LearningEvidenceKind.ABSTRACT_PATTERN_REUSED,
        interaction_id=interaction_id,
        abstract_pattern_digest=signature.digest_hex16,
        pattern_id=pattern_id,
        pre_facts=(("reuse_before", str(reuse_count - 1)),),
        post_facts=(("reuse_after", str(reuse_count)),),
        summary=summary,
    )


def make_transfer_recognized_record(
    *,
    interaction_id: str,
    signature: AbstractPatternSignature,
    prior_pattern_id: str,
    new_pattern_id: str,
) -> LearningEvidenceRecord:
    summary = (
        f"abstract pattern {signature.digest_hex16} transferred from "
        f"{prior_pattern_id} to {new_pattern_id}"
    )
    return LearningEvidenceRecord(
        kind=LearningEvidenceKind.TRANSFER_RECOGNIZED,
        interaction_id=interaction_id,
        abstract_pattern_digest=signature.digest_hex16,
        pattern_id=new_pattern_id,
        pre_facts=(
            ("prior_pid", _bounded_value(prior_pattern_id)),
        ),
        post_facts=(
            ("new_pid", _bounded_value(new_pattern_id)),
        ),
        summary=summary,
    )


def make_repl_correction_record(
    *,
    interaction_id: str,
    prior_hint_summary: str,
    canonical_form: str,
) -> LearningEvidenceRecord:
    summary = (
        f"near-miss correction applied: "
        f"{_bounded_value(prior_hint_summary)} -> {canonical_form}"
    )
    return LearningEvidenceRecord(
        kind=LearningEvidenceKind.REPL_CORRECTION_APPLIED,
        interaction_id=interaction_id,
        abstract_pattern_digest="",
        pattern_id="",
        pre_facts=(("hint", _bounded_value(prior_hint_summary)),),
        post_facts=(("canonical", _bounded_value(canonical_form)),),
        summary=summary,
    )


def make_diminishing_returns_record(
    *,
    interaction_id: str,
    canonical_form: str,
    prior_drf_str: str,
    current_drf_str: str,
) -> LearningEvidenceRecord:
    summary = (
        f"diminishing-returns factor {prior_drf_str} -> "
        f"{current_drf_str} for {canonical_form}"
    )
    return LearningEvidenceRecord(
        kind=LearningEvidenceKind.DIMINISHING_RETURNS_UPDATED,
        interaction_id=interaction_id,
        abstract_pattern_digest="",
        pattern_id="",
        pre_facts=(("drf_before", prior_drf_str),),
        post_facts=(("drf_after", current_drf_str),),
        summary=summary,
    )


def make_limitation_recorded_record(
    *,
    interaction_id: str,
    disposition_value: str,
    reason_category: str,
) -> LearningEvidenceRecord:
    summary = (
        f"limitation recorded: disposition={disposition_value} "
        f"reason={reason_category}"
    )
    return LearningEvidenceRecord(
        kind=LearningEvidenceKind.LIMITATION_RECORDED,
        interaction_id=interaction_id,
        abstract_pattern_digest="",
        pattern_id="",
        pre_facts=(("disposition", disposition_value),),
        post_facts=(("reason", reason_category),),
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Trace querying.
# ---------------------------------------------------------------------------


def has_acquired_digest(
    trace: LearningEvidenceTrace, digest: str
) -> bool:
    for r in trace.records:
        if (
            r.kind is LearningEvidenceKind.ABSTRACT_PATTERN_ACQUIRED
            and r.abstract_pattern_digest == digest
        ):
            return True
    return False


def count_reuses_for_digest(
    trace: LearningEvidenceTrace, digest: str
) -> int:
    n = 0
    for r in trace.records:
        if (
            r.kind is LearningEvidenceKind.ABSTRACT_PATTERN_REUSED
            and r.abstract_pattern_digest == digest
        ):
            n += 1
    return n


def last_near_miss_hint(
    trace: LearningEvidenceTrace,
) -> Optional[LearningEvidenceRecord]:
    """Return the most recent OBSERVED-near-miss record.

    A near-miss is encoded directly via the
    ``REPL_CORRECTION_APPLIED`` record when followed by a valid
    command; this helper returns the most recent
    ``REPL_CORRECTION_APPLIED`` record for citation.
    """
    for r in reversed(trace.records):
        if r.kind is LearningEvidenceKind.REPL_CORRECTION_APPLIED:
            return r
    return None


# ---------------------------------------------------------------------------
# Module-produced strings (audited).
# ---------------------------------------------------------------------------

MODULE_PRODUCED_STRINGS: tuple[str, ...] = (
    LEARNING_EVIDENCE_MODULE_VERSION,
    LearningEvidenceKind.OBSERVED.value,
    LearningEvidenceKind.RECURRENCE_INCREASED.value,
    LearningEvidenceKind.ABSTRACT_PATTERN_ACQUIRED.value,
    LearningEvidenceKind.ABSTRACT_PATTERN_REUSED.value,
    LearningEvidenceKind.TRANSFER_RECOGNIZED.value,
    LearningEvidenceKind.REPL_CORRECTION_APPLIED.value,
    LearningEvidenceKind.DIMINISHING_RETURNS_UPDATED.value,
    LearningEvidenceKind.LIMITATION_RECORDED.value,
)


__all__ = (
    "LEARNING_DIGEST_HEX_LEN",
    "LEARNING_EVIDENCE_MODULE_VERSION",
    "LEARNING_FACTS_MAX_ENTRIES",
    "LEARNING_FACT_KEY_MAX_LEN",
    "LEARNING_FACT_VALUE_MAX_LEN",
    "LEARNING_INTERACTION_ID_MAX_LEN",
    "LEARNING_RECORD_SUMMARY_MAX_LEN",
    "LEARNING_REPORT_SUMMARY_MAX_LEN",
    "LEARNING_TRACE_MAX_RECORDS",
    "LearningEvidenceKind",
    "LearningEvidenceRecord",
    "LearningEvidenceTrace",
    "LearningProofReport",
    "MODULE_PRODUCED_STRINGS",
    "append_record",
    "build_learning_proof_report",
    "count_reuses_for_digest",
    "empty_trace",
    "has_acquired_digest",
    "last_near_miss_hint",
    "make_abstract_pattern_acquired_record",
    "make_abstract_pattern_reused_record",
    "make_diminishing_returns_record",
    "make_limitation_recorded_record",
    "make_observed_record",
    "make_recurrence_increased_record",
    "make_repl_correction_record",
    "make_transfer_recognized_record",
)
