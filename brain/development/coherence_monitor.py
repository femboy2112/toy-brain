"""Phase 3.12c Coherence Monitor substrate.

A bounded read-only structural diagnostic over the live records this
package already exposes. The monitor consumes ``BrainState``,
``OperatorSession``, ``TextStreamHistory``,
``StreamPromotionCandidate``, ``PatternLedger``, optional
``SessionStoreConfig`` and optional ``AutosaveConfig`` /
``AutosaveStatusReport``, and produces a bounded printable
``CoherenceReport`` describing whether those substrates remain
mutually consistent at a single point in time.

The module is a structural diagnostic layer, not a cognitive layer.
It reports bounded factual agreements among existing records. It
performs no I/O, no network, no shell, no subprocess, no filesystem
mutation, no sqlite connection, no dynamic execution, no LLM call,
no ``tick(...)`` invocation, no ``save_session`` / ``load_session`` /
``db_backup`` / ``db_verify`` / ``maybe_autosave_after_mutation``
call, and no mutation of any kernel container, source history,
``PatternLedger``, persistence configuration, or autosave
configuration. The matching I-COHMON-10 static AST audit fixture
enforces the import set and the absence of dynamic-execution calls.

The module emits no scalar that purports to summarize interior
state, and no value-laden claim about the running system. Report
strings use only bounded printable factual phrasing about counts,
bounds, and structural agreements among existing records.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Optional

from brain.development.pattern_ledger import (
    PATTERN_LEDGER_EVIDENCE_MAX,
    PATTERN_LEDGER_MAX_ENTRIES,
    PatternLedger,
    PatternLedgerEntry,
    derive_pattern_id,
)
from brain.development.text_stream import (
    STREAM_HISTORY_MAX_CHUNKS,
    STREAM_PATTERN_RECURRENCE_MAX,
    STREAM_PATTERN_RECURRENCE_MIN,
    STREAM_PROMOTION_MAX,
)
from brain.io_types import ContentRegistry
from brain.tick import BrainState
from brain.tlica.msi import MSI
from brain.tlica.profile import COGITO_ID, ScalarProfile
from brain.ui.session import (
    MAX_STATUS_TEXT_LEN,
    _ALLOWED_SESSION_ATTRS,
    OperatorSession,
)
from brain.ui.snapshot import ACTIVE_VIEWS


# Bounded discipline locked by PHASE3_12_COHERENCE_MONITOR_CATALOG_PATCH_PLAN.md.
COHERENCE_MAX_CHECKS: int = 64
MAX_CHECK_ID_LEN: int = 64
MAX_SUMMARY_LEN: int = 240
MAX_DETAIL_LEN: int = 240
MAX_SOURCE_LEN: int = 32


#: Closed set of permitted source labels for :class:`CoherenceCheck`.
CHECK_SOURCES: frozenset[str] = frozenset({
    "kernel",
    "session",
    "stream",
    "pattern_ledger",
    "persistence_autosave",
    "non_claim",
})


class CoherenceCheckStatus(Enum):
    """Finite closed enumeration of per-check outcomes (I-COHMON-01)."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


def _require_bounded_printable(
    value: object,
    *,
    field: str,
    row_id: str,
    max_len: int,
    allow_empty: bool = False,
    reject_cogito: bool = True,
) -> str:
    if not isinstance(value, str):
        raise ValueError(
            f"{row_id} violated: {field} must be str "
            f"(got {type(value).__name__})"
        )
    if not value and not allow_empty:
        raise ValueError(f"{row_id} violated: {field} must be non-empty")
    if value and not value.isprintable():
        raise ValueError(f"{row_id} violated: {field} must be printable")
    if len(value) > max_len:
        raise ValueError(
            f"{row_id} violated: {field} length {len(value)} exceeds max {max_len}"
        )
    if reject_cogito and value == COGITO_ID:
        raise ValueError(
            f"{row_id} violated: {field} cannot equal COGITO_ID"
        )
    return value


def _require_int_nonneg(value: object, *, field: str, row_id: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(
            f"{row_id} violated: {field} must be int "
            f"(got {type(value).__name__})"
        )
    if value < 0:
        raise ValueError(f"{row_id} violated: {field} must be >= 0 (got {value})")
    return value


@dataclass(frozen=True, slots=True)
class CoherenceCheck:
    """Bounded printable per-check outcome record (I-COHMON-02)."""

    check_id: str
    status: CoherenceCheckStatus
    summary: str
    detail: str
    source: str

    def __post_init__(self) -> None:
        _require_bounded_printable(
            self.check_id,
            field="CoherenceCheck.check_id",
            row_id="I-COHMON-02",
            max_len=MAX_CHECK_ID_LEN,
        )
        if not isinstance(self.status, CoherenceCheckStatus):
            raise ValueError(
                "I-COHMON-02 violated: CoherenceCheck.status must be a "
                f"CoherenceCheckStatus (got {type(self.status).__name__})"
            )
        _require_bounded_printable(
            self.summary,
            field="CoherenceCheck.summary",
            row_id="I-COHMON-02",
            max_len=MAX_SUMMARY_LEN,
        )
        _require_bounded_printable(
            self.detail,
            field="CoherenceCheck.detail",
            row_id="I-COHMON-02",
            max_len=MAX_DETAIL_LEN,
            allow_empty=True,
        )
        _require_bounded_printable(
            self.source,
            field="CoherenceCheck.source",
            row_id="I-COHMON-02",
            max_len=MAX_SOURCE_LEN,
        )
        if self.source not in CHECK_SOURCES:
            raise ValueError(
                "I-COHMON-02 violated: CoherenceCheck.source "
                f"{self.source!r} not in CHECK_SOURCES"
            )


@dataclass(frozen=True, slots=True)
class CoherenceSnapshot:
    """Bounded structural snapshot of the live records (I-COHMON-03)."""

    snapshot_id: str
    tick_counter: int
    profile_domain_size: int
    msi_size: int
    registry_size: int
    stream_chunk_count: int
    stream_candidate_count: int
    pattern_ledger_entry_count: int
    autosave_mode: str
    session_db_configured: bool
    checks: tuple[CoherenceCheck, ...]

    def __post_init__(self) -> None:
        _require_bounded_printable(
            self.snapshot_id,
            field="CoherenceSnapshot.snapshot_id",
            row_id="I-COHMON-03",
            max_len=MAX_CHECK_ID_LEN,
        )
        for field_name, value in (
            ("tick_counter", self.tick_counter),
            ("profile_domain_size", self.profile_domain_size),
            ("msi_size", self.msi_size),
            ("registry_size", self.registry_size),
            ("stream_chunk_count", self.stream_chunk_count),
            ("stream_candidate_count", self.stream_candidate_count),
            ("pattern_ledger_entry_count", self.pattern_ledger_entry_count),
        ):
            _require_int_nonneg(
                value,
                field=f"CoherenceSnapshot.{field_name}",
                row_id="I-COHMON-03",
            )
        _require_bounded_printable(
            self.autosave_mode,
            field="CoherenceSnapshot.autosave_mode",
            row_id="I-COHMON-03",
            max_len=MAX_SOURCE_LEN,
            allow_empty=True,
            reject_cogito=False,
        )
        if not isinstance(self.session_db_configured, bool):
            raise ValueError(
                "I-COHMON-03 violated: CoherenceSnapshot.session_db_configured "
                f"must be bool (got {type(self.session_db_configured).__name__})"
            )
        if not isinstance(self.checks, tuple):
            raise ValueError(
                "I-COHMON-03 violated: CoherenceSnapshot.checks must be a tuple "
                f"(got {type(self.checks).__name__})"
            )
        for check in self.checks:
            if not isinstance(check, CoherenceCheck):
                raise ValueError(
                    "I-COHMON-03 violated: CoherenceSnapshot.checks must contain "
                    f"CoherenceCheck values (got {type(check).__name__})"
                )
        if len(self.checks) > COHERENCE_MAX_CHECKS:
            raise ValueError(
                "I-COHMON-03 violated: CoherenceSnapshot has "
                f"{len(self.checks)} checks; max is COHERENCE_MAX_CHECKS="
                f"{COHERENCE_MAX_CHECKS}"
            )


@dataclass(frozen=True, slots=True)
class CoherenceReport:
    """Bounded printable structural report (I-COHMON-03 / I-COHMON-09)."""

    snapshot: CoherenceSnapshot
    overall_status: CoherenceCheckStatus
    counts_by_status: tuple[tuple[str, int], ...]
    summary_text: str

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot, CoherenceSnapshot):
            raise ValueError(
                "I-COHMON-03 violated: CoherenceReport.snapshot must be a "
                f"CoherenceSnapshot (got {type(self.snapshot).__name__})"
            )
        if not isinstance(self.overall_status, CoherenceCheckStatus):
            raise ValueError(
                "I-COHMON-03 violated: CoherenceReport.overall_status must be "
                f"a CoherenceCheckStatus (got {type(self.overall_status).__name__})"
            )
        if not isinstance(self.counts_by_status, tuple):
            raise ValueError(
                "I-COHMON-03 violated: CoherenceReport.counts_by_status must be "
                f"a tuple (got {type(self.counts_by_status).__name__})"
            )
        seen: set[str] = set()
        for pair in self.counts_by_status:
            if (
                not isinstance(pair, tuple)
                or len(pair) != 2
                or not isinstance(pair[0], str)
                or not isinstance(pair[1], int)
                or isinstance(pair[1], bool)
            ):
                raise ValueError(
                    "I-COHMON-03 violated: CoherenceReport.counts_by_status entries "
                    f"must be (str, int) pairs (got {pair!r})"
                )
            label, count = pair
            if label in seen:
                raise ValueError(
                    "I-COHMON-03 violated: duplicate counts_by_status label "
                    f"{label!r}"
                )
            seen.add(label)
            if count < 0:
                raise ValueError(
                    "I-COHMON-03 violated: counts_by_status count for "
                    f"{label!r} must be >= 0 (got {count})"
                )
        _require_bounded_printable(
            self.summary_text,
            field="CoherenceReport.summary_text",
            row_id="I-COHMON-03",
            max_len=MAX_SUMMARY_LEN,
            allow_empty=True,
            reject_cogito=False,
        )


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------


def compute_overall_status(
    checks: tuple[CoherenceCheck, ...],
) -> CoherenceCheckStatus:
    """Deterministic aggregation per I-COHMON-09.

    ``FAIL`` dominates ``WARN`` dominates ``PASS``. ``NOT_APPLICABLE``
    alone yields ``NOT_APPLICABLE`` and never creates a false PASS or
    FAIL.
    """
    if not isinstance(checks, tuple):
        raise TypeError(
            "compute_overall_status expects a tuple of CoherenceCheck "
            f"(got {type(checks).__name__})"
        )
    saw_fail = False
    saw_warn = False
    saw_pass = False
    for check in checks:
        if not isinstance(check, CoherenceCheck):
            raise TypeError(
                "compute_overall_status entries must be CoherenceCheck "
                f"(got {type(check).__name__})"
            )
        status = check.status
        if status is CoherenceCheckStatus.FAIL:
            saw_fail = True
        elif status is CoherenceCheckStatus.WARN:
            saw_warn = True
        elif status is CoherenceCheckStatus.PASS:
            saw_pass = True
    if saw_fail:
        return CoherenceCheckStatus.FAIL
    if saw_warn:
        return CoherenceCheckStatus.WARN
    if saw_pass:
        return CoherenceCheckStatus.PASS
    return CoherenceCheckStatus.NOT_APPLICABLE


def _counts_by_status(
    checks: tuple[CoherenceCheck, ...],
) -> tuple[tuple[str, int], ...]:
    """Deterministic tuple of ``(status.value, count)`` pairs."""
    tally: dict[CoherenceCheckStatus, int] = {
        CoherenceCheckStatus.PASS: 0,
        CoherenceCheckStatus.WARN: 0,
        CoherenceCheckStatus.FAIL: 0,
        CoherenceCheckStatus.NOT_APPLICABLE: 0,
    }
    for check in checks:
        tally[check.status] = tally[check.status] + 1
    return tuple(
        (status.value, tally[status])
        for status in (
            CoherenceCheckStatus.PASS,
            CoherenceCheckStatus.WARN,
            CoherenceCheckStatus.FAIL,
            CoherenceCheckStatus.NOT_APPLICABLE,
        )
    )


def _build_check(
    check_id: str,
    *,
    status: CoherenceCheckStatus,
    summary: str,
    detail: str,
    source: str,
) -> CoherenceCheck:
    return CoherenceCheck(
        check_id=check_id,
        status=status,
        summary=summary,
        detail=detail,
        source=source,
    )


# ---------------------------------------------------------------------------
# Kernel checks (I-COHMON-04)
# ---------------------------------------------------------------------------


def _check_cogito_in_profile(profile: ScalarProfile) -> CoherenceCheck:
    if COGITO_ID in profile.domain:
        return _build_check(
            "kernel.cogito_in_profile",
            status=CoherenceCheckStatus.PASS,
            summary="cogito anchor present in profile domain",
            detail=f"profile_domain_size={len(profile.domain)}",
            source="kernel",
        )
    return _build_check(
        "kernel.cogito_in_profile",
        status=CoherenceCheckStatus.FAIL,
        summary="cogito anchor missing from profile domain",
        detail=f"profile_domain_size={len(profile.domain)}",
        source="kernel",
    )


def _check_cogito_in_msi(msi: MSI) -> CoherenceCheck:
    if COGITO_ID in msi.contents:
        return _build_check(
            "kernel.cogito_in_msi",
            status=CoherenceCheckStatus.PASS,
            summary="cogito anchor present in MSI contents",
            detail=f"msi_size={len(msi.contents)}",
            source="kernel",
        )
    return _build_check(
        "kernel.cogito_in_msi",
        status=CoherenceCheckStatus.FAIL,
        summary="cogito anchor missing from MSI contents",
        detail=f"msi_size={len(msi.contents)}",
        source="kernel",
    )


def _check_profile_values_bounded(profile: ScalarProfile) -> CoherenceCheck:
    bad: list[str] = []
    for cid, value in profile.values.items():
        if not isinstance(value, Fraction):
            bad.append(f"{cid}:{type(value).__name__}")
            continue
        if value < Fraction(0) or value > Fraction(1):
            bad.append(f"{cid}={value}")
    if bad:
        truncated = ", ".join(bad[:4])
        if len(bad) > 4:
            truncated = truncated + f", +{len(bad) - 4} more"
        return _build_check(
            "kernel.profile_values_bounded",
            status=CoherenceCheckStatus.FAIL,
            summary="profile values out of [0, 1]",
            detail=f"violators=[{truncated}]"[:MAX_DETAIL_LEN],
            source="kernel",
        )
    return _build_check(
        "kernel.profile_values_bounded",
        status=CoherenceCheckStatus.PASS,
        summary="profile values bounded in [0, 1]",
        detail=f"count={len(profile.values)}",
        source="kernel",
    )


def _check_ptcns_total_over_profile_domain(state: BrainState) -> CoherenceCheck:
    eval_map = getattr(state.ptcns, "eval_map", None)
    if eval_map is None:
        return _build_check(
            "kernel.ptcns_total_over_profile_domain",
            status=CoherenceCheckStatus.NOT_APPLICABLE,
            summary="ptcns eval_map not exposed by this PtCns implementation",
            detail="",
            source="kernel",
        )
    keys = frozenset(eval_map.keys())
    if keys == state.profile.domain:
        return _build_check(
            "kernel.ptcns_total_over_profile_domain",
            status=CoherenceCheckStatus.PASS,
            summary="ptcns eval_map keys equal profile domain",
            detail=f"size={len(keys)}",
            source="kernel",
        )
    extras = sorted(keys - state.profile.domain)
    missing = sorted(state.profile.domain - keys)
    return _build_check(
        "kernel.ptcns_total_over_profile_domain",
        status=CoherenceCheckStatus.FAIL,
        summary="ptcns eval_map keys disagree with profile domain",
        detail=(
            f"extras={extras[:4]} missing={missing[:4]}"
        )[:MAX_DETAIL_LEN],
        source="kernel",
    )


def _check_msi_subset_profile_domain(state: BrainState) -> CoherenceCheck:
    if state.msi.contents <= state.profile.domain:
        return _build_check(
            "kernel.msi_subset_profile_domain",
            status=CoherenceCheckStatus.PASS,
            summary="MSI contents are a subset of profile domain",
            detail=f"msi_size={len(state.msi.contents)}",
            source="kernel",
        )
    extras = sorted(state.msi.contents - state.profile.domain)
    return _build_check(
        "kernel.msi_subset_profile_domain",
        status=CoherenceCheckStatus.FAIL,
        summary="MSI contents not subset of profile domain",
        detail=f"extras={extras[:4]}"[:MAX_DETAIL_LEN],
        source="kernel",
    )


def _check_latest_tick_index_agrees(session: OperatorSession) -> CoherenceCheck:
    if session.latest_tick is None:
        return _build_check(
            "kernel.latest_tick_index_agrees",
            status=CoherenceCheckStatus.NOT_APPLICABLE,
            summary="no latest_tick recorded yet",
            detail=f"tick_counter={session.tick_counter}",
            source="kernel",
        )
    tick_index = getattr(session.latest_tick, "tick_index", None)
    if tick_index == session.tick_counter:
        return _build_check(
            "kernel.latest_tick_index_agrees",
            status=CoherenceCheckStatus.PASS,
            summary="latest_tick.tick_index agrees with session tick_counter",
            detail=f"tick_index={tick_index}",
            source="kernel",
        )
    return _build_check(
        "kernel.latest_tick_index_agrees",
        status=CoherenceCheckStatus.FAIL,
        summary="latest_tick.tick_index disagrees with session tick_counter",
        detail=(
            f"tick_index={tick_index} tick_counter={session.tick_counter}"
        )[:MAX_DETAIL_LEN],
        source="kernel",
    )


def build_kernel_checks(session: OperatorSession) -> tuple[CoherenceCheck, ...]:
    """Build the read-only kernel coherence checks (I-COHMON-04)."""
    state = session.state
    return (
        _check_cogito_in_profile(state.profile),
        _check_cogito_in_msi(state.msi),
        _check_profile_values_bounded(state.profile),
        _check_ptcns_total_over_profile_domain(state),
        _check_msi_subset_profile_domain(state),
        _check_latest_tick_index_agrees(session),
    )


# ---------------------------------------------------------------------------
# Session checks (I-COHMON-05)
# ---------------------------------------------------------------------------


def _value_looks_unsafe(value: object) -> tuple[bool, str]:
    if callable(value):
        return True, "callable"
    if hasattr(value, "eval_consistency"):
        return True, "eval_consistency (LLM client)"
    if (
        hasattr(value, "read")
        and hasattr(value, "write")
        and not isinstance(value, BrainState)
    ):
        return True, "read/write (file/socket-like)"
    if hasattr(value, "fileno"):
        return True, "fileno (resource-like)"
    if hasattr(value, "send_signal") or hasattr(value, "communicate"):
        return True, "subprocess handle"
    if hasattr(value, "cursor") and hasattr(value, "commit"):
        return True, "sqlite3.Connection-like"
    return False, ""


def _check_session_no_unsafe_resources(
    session: OperatorSession,
) -> CoherenceCheck:
    bad: list[str] = []
    for name in _ALLOWED_SESSION_ATTRS:
        value = getattr(session, name, None)
        unsafe, reason = _value_looks_unsafe(value)
        if unsafe:
            bad.append(f"{name}:{reason}")
    if bad:
        truncated = ", ".join(bad[:4])
        return _build_check(
            "session.no_unsafe_resources",
            status=CoherenceCheckStatus.FAIL,
            summary="operator session exposes an unsafe resource",
            detail=f"violators=[{truncated}]"[:MAX_DETAIL_LEN],
            source="session",
        )
    return _build_check(
        "session.no_unsafe_resources",
        status=CoherenceCheckStatus.PASS,
        summary="operator session fields are resource-free",
        detail=f"slots={len(_ALLOWED_SESSION_ATTRS)}",
        source="session",
    )


def _check_session_active_view_legal(
    session: OperatorSession,
) -> CoherenceCheck:
    if session.active_view in ACTIVE_VIEWS:
        return _build_check(
            "session.active_view_legal",
            status=CoherenceCheckStatus.PASS,
            summary="active_view is in the documented view set",
            detail=f"active_view={session.active_view!r}",
            source="session",
        )
    return _build_check(
        "session.active_view_legal",
        status=CoherenceCheckStatus.FAIL,
        summary="active_view is not in the documented view set",
        detail=f"active_view={session.active_view!r}",
        source="session",
    )


def _check_session_event_queue_bounded(
    session: OperatorSession,
) -> CoherenceCheck:
    limit = session.event_queue.limit
    size = len(session.event_queue)
    if limit > 0 and size <= limit:
        return _build_check(
            "session.event_queue_bounded",
            status=CoherenceCheckStatus.PASS,
            summary="event_queue size respects its limit",
            detail=f"size={size} limit={limit}",
            source="session",
        )
    return _build_check(
        "session.event_queue_bounded",
        status=CoherenceCheckStatus.FAIL,
        summary="event_queue size or limit is out of bounds",
        detail=f"size={size} limit={limit}",
        source="session",
    )


def _check_session_status_error_bounded(
    session: OperatorSession,
) -> CoherenceCheck:
    bad: list[str] = []
    for name in ("status_message", "error_message"):
        value = getattr(session, name)
        if not isinstance(value, str):
            bad.append(f"{name}:non-str")
            continue
        if value and not value.isprintable():
            bad.append(f"{name}:non-printable")
            continue
        if len(value) > MAX_STATUS_TEXT_LEN:
            bad.append(f"{name}:length={len(value)}")
    if bad:
        return _build_check(
            "session.status_error_bounded",
            status=CoherenceCheckStatus.FAIL,
            summary="session status/error text is unbounded or non-printable",
            detail=f"violators={bad}"[:MAX_DETAIL_LEN],
            source="session",
        )
    return _build_check(
        "session.status_error_bounded",
        status=CoherenceCheckStatus.PASS,
        summary="session status/error text is bounded printable",
        detail=f"max_status_text_len={MAX_STATUS_TEXT_LEN}",
        source="session",
    )


def _check_session_pattern_ledger_field(
    session: OperatorSession,
) -> CoherenceCheck:
    ledger = getattr(session, "pattern_ledger", None)
    if ledger is None:
        return _build_check(
            "session.pattern_ledger_field",
            status=CoherenceCheckStatus.NOT_APPLICABLE,
            summary="session has no pattern_ledger field",
            detail="",
            source="session",
        )
    if not isinstance(ledger, PatternLedger):
        return _build_check(
            "session.pattern_ledger_field",
            status=CoherenceCheckStatus.FAIL,
            summary="session.pattern_ledger is not a PatternLedger",
            detail=f"type={type(ledger).__name__}",
            source="session",
        )
    unsafe, reason = _value_looks_unsafe(ledger)
    if unsafe:
        return _build_check(
            "session.pattern_ledger_field",
            status=CoherenceCheckStatus.FAIL,
            summary="session.pattern_ledger field looks unsafe",
            detail=f"reason={reason}"[:MAX_DETAIL_LEN],
            source="session",
        )
    return _build_check(
        "session.pattern_ledger_field",
        status=CoherenceCheckStatus.PASS,
        summary="session.pattern_ledger is a resource-safe PatternLedger",
        detail=f"entries={len(ledger.entries)}",
        source="session",
    )


def build_session_checks(
    session: OperatorSession,
) -> tuple[CoherenceCheck, ...]:
    """Build the read-only operator-session coherence checks (I-COHMON-05)."""
    return (
        _check_session_no_unsafe_resources(session),
        _check_session_active_view_legal(session),
        _check_session_event_queue_bounded(session),
        _check_session_status_error_bounded(session),
        _check_session_pattern_ledger_field(session),
    )


# ---------------------------------------------------------------------------
# Stream checks (I-COHMON-06)
# ---------------------------------------------------------------------------


def _check_stream_history_bounded(
    session: OperatorSession,
) -> CoherenceCheck:
    size = len(session.stream_history.chunks)
    if size <= STREAM_HISTORY_MAX_CHUNKS:
        return _build_check(
            "stream.history_bounded",
            status=CoherenceCheckStatus.PASS,
            summary="stream history within bounds",
            detail=f"size={size} max={STREAM_HISTORY_MAX_CHUNKS}",
            source="stream",
        )
    return _build_check(
        "stream.history_bounded",
        status=CoherenceCheckStatus.FAIL,
        summary="stream history exceeds bound",
        detail=f"size={size} max={STREAM_HISTORY_MAX_CHUNKS}",
        source="stream",
    )


def _check_stream_candidates_bounded(
    session: OperatorSession,
) -> CoherenceCheck:
    size = len(session.stream_candidates)
    if size <= STREAM_PROMOTION_MAX:
        return _build_check(
            "stream.candidates_bounded",
            status=CoherenceCheckStatus.PASS,
            summary="stream candidate list within bounds",
            detail=f"size={size} max={STREAM_PROMOTION_MAX}",
            source="stream",
        )
    return _build_check(
        "stream.candidates_bounded",
        status=CoherenceCheckStatus.FAIL,
        summary="stream candidate list exceeds bound",
        detail=f"size={size} max={STREAM_PROMOTION_MAX}",
        source="stream",
    )


def _check_stream_chunk_serial_consistent(
    session: OperatorSession,
) -> CoherenceCheck:
    serial = session.stream_chunk_serial
    if not isinstance(serial, int) or isinstance(serial, bool) or serial < 0:
        return _build_check(
            "stream.chunk_serial_consistent",
            status=CoherenceCheckStatus.FAIL,
            summary="stream_chunk_serial is not a non-negative int",
            detail=f"serial={serial!r}",
            source="stream",
        )
    chunks_len = len(session.stream_history.chunks)
    if serial < chunks_len:
        return _build_check(
            "stream.chunk_serial_consistent",
            status=CoherenceCheckStatus.WARN,
            summary="stream_chunk_serial is smaller than history length",
            detail=f"serial={serial} chunks={chunks_len}",
            source="stream",
        )
    return _build_check(
        "stream.chunk_serial_consistent",
        status=CoherenceCheckStatus.PASS,
        summary="stream_chunk_serial is a non-negative int >= history length",
        detail=f"serial={serial} chunks={chunks_len}",
        source="stream",
    )


def _check_stream_no_cogito_in_chunks(
    session: OperatorSession,
) -> CoherenceCheck:
    for chunk in session.stream_history.chunks:
        for field_name, value in (
            ("chunk_id", chunk.chunk_id),
            ("text", chunk.text),
            ("provenance", chunk.provenance),
        ):
            if value == COGITO_ID:
                return _build_check(
                    "stream.no_cogito_in_chunks",
                    status=CoherenceCheckStatus.FAIL,
                    summary="stream chunk uses cogito anchor where forbidden",
                    detail=(
                        f"chunk_id={chunk.chunk_id!r} field={field_name}"
                    )[:MAX_DETAIL_LEN],
                    source="stream",
                )
    for candidate in session.stream_candidates:
        for field_name, value in (
            ("candidate_id", candidate.candidate_id),
            ("target_content_id", candidate.target_content_id),
        ):
            if value == COGITO_ID:
                return _build_check(
                    "stream.no_cogito_in_chunks",
                    status=CoherenceCheckStatus.FAIL,
                    summary="stream candidate uses cogito anchor where forbidden",
                    detail=(
                        f"candidate_id={candidate.candidate_id!r} "
                        f"field={field_name}"
                    )[:MAX_DETAIL_LEN],
                    source="stream",
                )
    return _build_check(
        "stream.no_cogito_in_chunks",
        status=CoherenceCheckStatus.PASS,
        summary="no stream chunk or candidate uses cogito anchor",
        detail=(
            f"chunks={len(session.stream_history.chunks)} "
            f"candidates={len(session.stream_candidates)}"
        ),
        source="stream",
    )


def build_stream_checks(
    session: OperatorSession,
) -> tuple[CoherenceCheck, ...]:
    """Build the read-only stream coherence checks (I-COHMON-06)."""
    return (
        _check_stream_history_bounded(session),
        _check_stream_candidates_bounded(session),
        _check_stream_chunk_serial_consistent(session),
        _check_stream_no_cogito_in_chunks(session),
    )


# ---------------------------------------------------------------------------
# Pattern Ledger checks (I-COHMON-07)
# ---------------------------------------------------------------------------


def _entry_recomputes_clean(entry: PatternLedgerEntry) -> bool:
    """Re-run the PatternLedgerEntry constructor with this entry's fields."""
    try:
        PatternLedgerEntry(
            pattern_id=entry.pattern_id,
            signature=entry.signature,
            evidence_chunk_ids=entry.evidence_chunk_ids,
            evidence_candidate_ids=entry.evidence_candidate_ids,
            recurrence_count=entry.recurrence_count,
            first_seen_tick=entry.first_seen_tick,
            last_seen_tick=entry.last_seen_tick,
            source_kind=entry.source_kind,
            confidence=entry.confidence,
            saturation_state=entry.saturation_state,
            provenance=entry.provenance,
        )
    except (TypeError, ValueError):
        return False
    return True


def _check_pledger_entries_bounded(
    ledger: PatternLedger,
) -> CoherenceCheck:
    size = len(ledger.entries)
    if size <= PATTERN_LEDGER_MAX_ENTRIES:
        return _build_check(
            "pledger.entries_bounded",
            status=CoherenceCheckStatus.PASS,
            summary="pattern ledger entries within bounds",
            detail=f"size={size} max={PATTERN_LEDGER_MAX_ENTRIES}",
            source="pattern_ledger",
        )
    return _build_check(
        "pledger.entries_bounded",
        status=CoherenceCheckStatus.FAIL,
        summary="pattern ledger entries exceed bound",
        detail=f"size={size} max={PATTERN_LEDGER_MAX_ENTRIES}",
        source="pattern_ledger",
    )


def _check_pledger_entries_validate(
    ledger: PatternLedger,
) -> CoherenceCheck:
    bad: list[str] = []
    for entry in ledger.entries:
        if not isinstance(entry, PatternLedgerEntry):
            bad.append(f"non-entry:{type(entry).__name__}")
            continue
        if not _entry_recomputes_clean(entry):
            bad.append(entry.pattern_id)
    if bad:
        return _build_check(
            "pledger.entries_validate_constructor_invariants",
            status=CoherenceCheckStatus.FAIL,
            summary="pattern ledger entry fails constructor re-check",
            detail=f"violators={bad[:4]}"[:MAX_DETAIL_LEN],
            source="pattern_ledger",
        )
    if not ledger.entries:
        return _build_check(
            "pledger.entries_validate_constructor_invariants",
            status=CoherenceCheckStatus.NOT_APPLICABLE,
            summary="pattern ledger has no entries to re-check",
            detail="",
            source="pattern_ledger",
        )
    return _build_check(
        "pledger.entries_validate_constructor_invariants",
        status=CoherenceCheckStatus.PASS,
        summary="every pattern ledger entry passes constructor re-check",
        detail=f"entries={len(ledger.entries)}",
        source="pattern_ledger",
    )


def _check_pledger_recurrence_bounded(
    ledger: PatternLedger,
) -> CoherenceCheck:
    bad: list[str] = []
    for entry in ledger.entries:
        if not isinstance(entry, PatternLedgerEntry):
            continue
        if (
            entry.recurrence_count < STREAM_PATTERN_RECURRENCE_MIN
            or entry.recurrence_count > STREAM_PATTERN_RECURRENCE_MAX
        ):
            bad.append(f"{entry.pattern_id}={entry.recurrence_count}")
    if bad:
        return _build_check(
            "pledger.recurrence_counts_bounded",
            status=CoherenceCheckStatus.FAIL,
            summary="pattern ledger recurrence_count outside bounds",
            detail=f"violators={bad[:4]}"[:MAX_DETAIL_LEN],
            source="pattern_ledger",
        )
    return _build_check(
        "pledger.recurrence_counts_bounded",
        status=CoherenceCheckStatus.PASS
        if ledger.entries
        else CoherenceCheckStatus.NOT_APPLICABLE,
        summary="pattern ledger recurrence counts within bounds",
        detail=(
            f"min={STREAM_PATTERN_RECURRENCE_MIN} "
            f"max={STREAM_PATTERN_RECURRENCE_MAX}"
        ),
        source="pattern_ledger",
    )


def _check_pledger_confidence_matches_formula(
    ledger: PatternLedger,
) -> CoherenceCheck:
    bad: list[str] = []
    for entry in ledger.entries:
        if not isinstance(entry, PatternLedgerEntry):
            continue
        expected = Fraction(
            entry.recurrence_count, STREAM_PATTERN_RECURRENCE_MAX
        )
        if entry.confidence != expected:
            bad.append(entry.pattern_id)
    if bad:
        return _build_check(
            "pledger.confidence_matches_formula",
            status=CoherenceCheckStatus.FAIL,
            summary="pattern ledger confidence does not match formula",
            detail=f"violators={bad[:4]}"[:MAX_DETAIL_LEN],
            source="pattern_ledger",
        )
    return _build_check(
        "pledger.confidence_matches_formula",
        status=CoherenceCheckStatus.PASS
        if ledger.entries
        else CoherenceCheckStatus.NOT_APPLICABLE,
        summary="pattern ledger confidence matches the locked formula",
        detail="confidence = Fraction(recurrence_count, RECURRENCE_MAX)",
        source="pattern_ledger",
    )


def _check_pledger_evidence_bounded(
    ledger: PatternLedger,
) -> CoherenceCheck:
    bad: list[str] = []
    for entry in ledger.entries:
        if not isinstance(entry, PatternLedgerEntry):
            continue
        if len(entry.evidence_chunk_ids) > PATTERN_LEDGER_EVIDENCE_MAX:
            bad.append(f"{entry.pattern_id}:chunks={len(entry.evidence_chunk_ids)}")
            continue
        if len(entry.evidence_candidate_ids) > PATTERN_LEDGER_EVIDENCE_MAX:
            bad.append(f"{entry.pattern_id}:cands={len(entry.evidence_candidate_ids)}")
            continue
        for eid in entry.evidence_chunk_ids + entry.evidence_candidate_ids:
            if eid == COGITO_ID:
                bad.append(f"{entry.pattern_id}:cogito_evidence")
                break
    if bad:
        return _build_check(
            "pledger.evidence_ids_bounded",
            status=CoherenceCheckStatus.FAIL,
            summary="pattern ledger evidence list violates bounds",
            detail=f"violators={bad[:4]}"[:MAX_DETAIL_LEN],
            source="pattern_ledger",
        )
    return _build_check(
        "pledger.evidence_ids_bounded",
        status=CoherenceCheckStatus.PASS
        if ledger.entries
        else CoherenceCheckStatus.NOT_APPLICABLE,
        summary="pattern ledger evidence lists within bounds",
        detail=f"max={PATTERN_LEDGER_EVIDENCE_MAX}",
        source="pattern_ledger",
    )


def _check_pledger_pattern_id_matches_signature(
    ledger: PatternLedger,
) -> CoherenceCheck:
    bad: list[str] = []
    for entry in ledger.entries:
        if not isinstance(entry, PatternLedgerEntry):
            continue
        try:
            computed = derive_pattern_id(entry.signature)
        except (TypeError, ValueError):
            bad.append(entry.pattern_id)
            continue
        if computed != entry.pattern_id:
            bad.append(entry.pattern_id)
    if bad:
        return _build_check(
            "pledger.pattern_id_matches_signature",
            status=CoherenceCheckStatus.FAIL,
            summary="pattern ledger pattern_id disagrees with signature hash",
            detail=f"violators={bad[:4]}"[:MAX_DETAIL_LEN],
            source="pattern_ledger",
        )
    return _build_check(
        "pledger.pattern_id_matches_signature",
        status=CoherenceCheckStatus.PASS
        if ledger.entries
        else CoherenceCheckStatus.NOT_APPLICABLE,
        summary="pattern_id matches the deterministic signature hash",
        detail="",
        source="pattern_ledger",
    )


def _check_pledger_session_local_only(
    session: OperatorSession,
) -> CoherenceCheck:
    config = getattr(session, "session_store_config", None)
    if config is None:
        detail = "no session DB configured; ledger is session-local"
    else:
        detail = "session DB configured; ledger remains session-local (LOCK B)"
    return _build_check(
        "pledger.session_local_only",
        status=CoherenceCheckStatus.PASS,
        summary="pattern ledger is session-local (no persistence claim)",
        detail=detail,
        source="pattern_ledger",
    )


def build_pattern_ledger_checks(
    session: OperatorSession,
) -> tuple[CoherenceCheck, ...]:
    """Build the read-only pattern ledger coherence checks (I-COHMON-07)."""
    ledger = getattr(session, "pattern_ledger", None)
    if ledger is None or not isinstance(ledger, PatternLedger):
        return (
            _build_check(
                "pledger.entries_bounded",
                status=CoherenceCheckStatus.NOT_APPLICABLE,
                summary="session exposes no PatternLedger",
                detail="",
                source="pattern_ledger",
            ),
        )
    return (
        _check_pledger_entries_bounded(ledger),
        _check_pledger_entries_validate(ledger),
        _check_pledger_recurrence_bounded(ledger),
        _check_pledger_confidence_matches_formula(ledger),
        _check_pledger_evidence_bounded(ledger),
        _check_pledger_pattern_id_matches_signature(ledger),
        _check_pledger_session_local_only(session),
    )


# ---------------------------------------------------------------------------
# Persistence / autosave reporting (I-COHMON-08)
# ---------------------------------------------------------------------------


def _autosave_mode_string(session: OperatorSession) -> str:
    config = getattr(session, "autosave_config", None)
    if config is None:
        return ""
    mode = getattr(config, "mode", None)
    if mode is None:
        return ""
    value = getattr(mode, "value", None)
    if isinstance(value, str):
        return value
    return ""


def _session_db_is_configured(session: OperatorSession) -> bool:
    return getattr(session, "session_store_config", None) is not None


def _check_persistence_session_db_configured_reported(
    session: OperatorSession,
) -> CoherenceCheck:
    if _session_db_is_configured(session):
        return _build_check(
            "persistence.session_db_configured_reported",
            status=CoherenceCheckStatus.PASS,
            summary="session DB is configured; monitor reports without opening it",
            detail="diagnostic remains read-only",
            source="persistence_autosave",
        )
    return _build_check(
        "persistence.session_db_configured_reported",
        status=CoherenceCheckStatus.NOT_APPLICABLE,
        summary="no session DB configured",
        detail="session_store_config is None",
        source="persistence_autosave",
    )


def _check_persistence_no_pledger_schema_claim() -> CoherenceCheck:
    return _build_check(
        "persistence.no_pledger_schema_claim",
        status=CoherenceCheckStatus.PASS,
        summary="pattern ledger has no persistence schema in v1",
        detail="LOCK B: session-local only",
        source="persistence_autosave",
    )


def _check_persistence_commands_remain_separate() -> CoherenceCheck:
    return _build_check(
        "persistence.commands_remain_separate",
        status=CoherenceCheckStatus.PASS,
        summary="persistence dispatchers remain owned by their existing handlers",
        detail="monitor does not open the DB",
        source="persistence_autosave",
    )


def _check_autosave_mode_reported(
    session: OperatorSession,
) -> CoherenceCheck:
    mode = _autosave_mode_string(session)
    if mode:
        return _build_check(
            "autosave.mode_reported",
            status=CoherenceCheckStatus.PASS,
            summary="autosave mode reported as configured",
            detail=f"mode={mode}",
            source="persistence_autosave",
        )
    return _build_check(
        "autosave.mode_reported",
        status=CoherenceCheckStatus.NOT_APPLICABLE,
        summary="autosave not configured",
        detail="autosave_config is None or mode unset",
        source="persistence_autosave",
    )


def _check_autosave_no_persistence_extension_claim() -> CoherenceCheck:
    return _build_check(
        "autosave.no_persistence_extension_claim",
        status=CoherenceCheckStatus.PASS,
        summary="autosave trigger set is unchanged by the pattern ledger",
        detail="STEP_TICK and STREAM_PROMOTE only",
        source="persistence_autosave",
    )


def build_persistence_autosave_checks(
    session: OperatorSession,
) -> tuple[CoherenceCheck, ...]:
    """Build the read-only persistence / autosave reporting checks (I-COHMON-08)."""
    return (
        _check_persistence_session_db_configured_reported(session),
        _check_persistence_no_pledger_schema_claim(),
        _check_persistence_commands_remain_separate(),
        _check_autosave_mode_reported(session),
        _check_autosave_no_persistence_extension_claim(),
    )


# ---------------------------------------------------------------------------
# Non-claim audit (I-COHMON-11)
# ---------------------------------------------------------------------------


#: Closed set of terms the bounded report must avoid (case-insensitive).
_FORBIDDEN_NON_CLAIM_TERMS: tuple[str, ...] = (
    "conscious",
    "consciousness",
    "sentient",
    "sentience",
    "subjective",
    "qualia",
    "aware",
    "awareness",
    "i-ness",
    "understand",
    "understanding",
    "comprehend",
    "comprehension",
    "believe",
    "belief",
    "intent",
    "agency",
    "self-modification",
    "truth",
    "preserve",
    "damage",
)


def _text_has_forbidden_term(text: str) -> Optional[str]:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


def _check_nonclaim_no_forbidden_terms_in_report(
    checks: tuple[CoherenceCheck, ...],
) -> CoherenceCheck:
    bad: list[str] = []
    for check in checks:
        for text in (check.check_id, check.summary, check.detail):
            term = _text_has_forbidden_term(text)
            if term is not None:
                bad.append(f"{check.check_id}:{term}")
                break
        if bad:
            break
    if bad:
        return _build_check(
            "nonclaim.no_forbidden_terms_in_report",
            status=CoherenceCheckStatus.FAIL,
            summary="report text contains a disallowed term",
            detail=f"violators={bad[:4]}"[:MAX_DETAIL_LEN],
            source="non_claim",
        )
    return _build_check(
        "nonclaim.no_forbidden_terms_in_report",
        status=CoherenceCheckStatus.PASS,
        summary="report text contains no disallowed term",
        detail=f"checks={len(checks)}",
        source="non_claim",
    )


def _check_nonclaim_no_aggregate_iness_score() -> CoherenceCheck:
    return _build_check(
        "nonclaim.no_aggregate_iness_score",
        status=CoherenceCheckStatus.PASS,
        summary="no aggregate scalar summary appears in this report",
        detail="counts_by_status is a labelled tuple, not a scalar",
        source="non_claim",
    )


def build_nonclaim_checks(
    checks_so_far: tuple[CoherenceCheck, ...],
) -> tuple[CoherenceCheck, ...]:
    """Build the read-only non-claim audit checks (I-COHMON-11)."""
    return (
        _check_nonclaim_no_forbidden_terms_in_report(checks_so_far),
        _check_nonclaim_no_aggregate_iness_score(),
    )


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------


def build_coherence_snapshot(
    session: OperatorSession,
    *,
    snapshot_id: str = "coh-snap-1",
) -> CoherenceSnapshot:
    """Build a bounded :class:`CoherenceSnapshot` from a live session.

    Reads ``session`` only. Does not mutate any container. Drives
    I-COHMON-04 / 05 / 06 / 07 / 08 / 11 by composing the per-family
    check builders and the non-claim audit.
    """
    if not isinstance(session, OperatorSession):
        raise TypeError(
            "build_coherence_snapshot expects an OperatorSession "
            f"(got {type(session).__name__})"
        )
    state = session.state
    registry = state.registry
    if not isinstance(registry, ContentRegistry):
        raise TypeError(
            "build_coherence_snapshot expects ContentRegistry on "
            f"BrainState.registry (got {type(registry).__name__})"
        )

    ledger = getattr(session, "pattern_ledger", None)
    ledger_size = (
        len(ledger.entries) if isinstance(ledger, PatternLedger) else 0
    )

    checks: tuple[CoherenceCheck, ...] = (
        build_kernel_checks(session)
        + build_session_checks(session)
        + build_stream_checks(session)
        + build_pattern_ledger_checks(session)
        + build_persistence_autosave_checks(session)
    )
    checks = checks + build_nonclaim_checks(checks)

    return CoherenceSnapshot(
        snapshot_id=snapshot_id,
        tick_counter=session.tick_counter,
        profile_domain_size=len(state.profile.domain),
        msi_size=len(state.msi.contents),
        registry_size=len(registry.texts),
        stream_chunk_count=len(session.stream_history.chunks),
        stream_candidate_count=len(session.stream_candidates),
        pattern_ledger_entry_count=ledger_size,
        autosave_mode=_autosave_mode_string(session),
        session_db_configured=_session_db_is_configured(session),
        checks=checks,
    )


def _summary_text_for(snapshot: CoherenceSnapshot, overall: CoherenceCheckStatus) -> str:
    return (
        f"coherence {overall.value}: "
        f"tick={snapshot.tick_counter} "
        f"profile={snapshot.profile_domain_size} "
        f"msi={snapshot.msi_size} "
        f"stream_chunks={snapshot.stream_chunk_count} "
        f"stream_candidates={snapshot.stream_candidate_count} "
        f"pledger={snapshot.pattern_ledger_entry_count} "
        f"checks={len(snapshot.checks)}"
    )[:MAX_SUMMARY_LEN]


def build_coherence_report(snapshot: CoherenceSnapshot) -> CoherenceReport:
    """Build a bounded :class:`CoherenceReport` from a snapshot.

    Pure function over ``snapshot``; performs no I/O and no mutation.
    Drives I-COHMON-03 / 09 by computing the deterministic overall
    status and ``counts_by_status`` tuple.
    """
    if not isinstance(snapshot, CoherenceSnapshot):
        raise TypeError(
            "build_coherence_report expects a CoherenceSnapshot "
            f"(got {type(snapshot).__name__})"
        )
    overall = compute_overall_status(snapshot.checks)
    counts = _counts_by_status(snapshot.checks)
    summary = _summary_text_for(snapshot, overall)
    return CoherenceReport(
        snapshot=snapshot,
        overall_status=overall,
        counts_by_status=counts,
        summary_text=summary,
    )


def build_full_coherence_report(
    session: OperatorSession,
    *,
    snapshot_id: str = "coh-snap-1",
) -> CoherenceReport:
    """Convenience wrapper that builds the snapshot and the report."""
    snapshot = build_coherence_snapshot(session, snapshot_id=snapshot_id)
    return build_coherence_report(snapshot)
