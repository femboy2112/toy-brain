"""Phase 3.23 Dispatch Tracer — bounded audit trail of dispatch routes.

"Dispatch trace" in Phase 3.23 means an **explicit audit record of the
public route** taken through :meth:`brain.ui.session.OperatorSession.dispatch`
and the **structural effects** observed. It is bounded, deterministic,
externally inspectable, and non-claim-clean. It is NOT private
chain-of-thought. It is NOT a metacognitive description of any "inner
experience" of the running system.

Non-claim discipline (binding):

* No claim of cognitive properties is made by this module.
* Every produced string passes the canonical
  ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``
  audit (case-insensitive substring).

Closed import set:

* ``__future__``, ``dataclasses``, ``enum``, ``hashlib``, ``typing``
* ``brain.development.coherence_monitor`` (``_FORBIDDEN_NON_CLAIM_TERMS``)

No ``brain.llm.*``. No ``brain.tick``. No curses, subprocess, socket,
urllib, http, requests, tempfile, shutil, threading, asyncio,
atexit, signal, importlib, time, random.

Drives ``I-DTRACE-01..12`` (the dispatch tracer row family).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS


# ---------------------------------------------------------------------------
# Bounded constants.
# ---------------------------------------------------------------------------

DISPATCH_TRACE_MAX_STEPS: int = 16
DISPATCH_TRACE_STEP_FIELD_MAX_LEN: int = 160
DISPATCH_TRACE_BEFORE_AFTER_MAX_ENTRIES: int = 12
DISPATCH_TRACE_FACT_KEY_MAX_LEN: int = 32
DISPATCH_TRACE_FACT_VALUE_MAX_LEN: int = 64
DISPATCH_TRACE_DIGEST_HEX_LEN: int = 16
DISPATCH_TRACE_REPORT_SUMMARY_MAX_LEN: int = 320
DISPATCH_TRACE_INTERACTION_ID_MAX_LEN: int = 64
DISPATCH_TRACE_ROUTE_LABEL_MAX_LEN: int = 64
DISPATCH_TRACE_ROUTE_PATH_MAX_LEN: int = 240
DISPATCH_TRACE_COMMAND_KIND_MAX_LEN: int = 64
DISPATCH_TRACE_MODULE_VERSION: str = "phase3.23.v1"

DISPATCH_TRACE_DISCLAIMER: str = (
    "audit trail of deterministic structural dispatch routing only; "
    "no claim about the runtime's nature is made"
)


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
# Closed enums.
# ---------------------------------------------------------------------------


class DispatchTraceKind(str, Enum):
    """Closed enum of dispatch trace step kinds."""

    COMMAND_RECEIVED = "command_received"
    ROUTE_SELECTED = "route_selected"
    PRE_STATE_SNAPSHOT = "pre_state_snapshot"
    HANDLER_ENTERED = "handler_entered"
    HANDLER_RETURNED = "handler_returned"
    POST_STATE_SNAPSHOT = "post_state_snapshot"
    MUTATION_CLASSIFIED = "mutation_classified"
    AUTOSAVE_CHECKED = "autosave_checked"
    RESOURCE_AUDIT_CHECKED = "resource_audit_checked"
    TRACE_FINALIZED = "trace_finalized"
    ERROR_RECORDED = "error_recorded"
    NOOP_RECORDED = "noop_recorded"


class DispatchMutationKind(str, Enum):
    """Closed enum of mutation classifications."""

    NONE = "none"
    UI_ONLY = "ui_only"
    STREAM_APPEND = "stream_append"
    STREAM_WINDOW_INTERNAL = "stream_window_internal"
    STREAM_PROMOTE = "stream_promote"
    QUEUE_MUTATION = "queue_mutation"
    STEP_TICK = "step_tick"
    SESSION_PERSISTENCE = "session_persistence"
    AUTOSAVE = "autosave"
    DB_OBSERVE = "db_observe"
    DB_BACKUP = "db_backup"
    VIEW_CHANGE = "view_change"
    QUIT_FLAG = "quit_flag"
    ERROR_ONLY = "error_only"


class DispatchTraceStatus(str, Enum):
    """Closed enum of dispatch trace step statuses."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


# ---------------------------------------------------------------------------
# Frozen records.
# ---------------------------------------------------------------------------


def _validate_facts(name: str, facts: tuple[tuple[str, str], ...]) -> None:
    if not isinstance(facts, tuple):
        raise TypeError(
            f"I-DTRACE-01 violated: DispatchTraceStep.{name} must be a tuple"
        )
    if len(facts) > DISPATCH_TRACE_BEFORE_AFTER_MAX_ENTRIES:
        raise ValueError(
            f"I-DTRACE-01 violated: DispatchTraceStep.{name} length "
            f"exceeds {DISPATCH_TRACE_BEFORE_AFTER_MAX_ENTRIES}"
        )
    for entry in facts:
        if not isinstance(entry, tuple) or len(entry) != 2:
            raise TypeError(
                f"I-DTRACE-01 violated: DispatchTraceStep.{name} entries "
                "must be (str, str) pairs"
            )
        key, value = entry
        if (
            not isinstance(key, str)
            or not key
            or not key.isprintable()
            or len(key) > DISPATCH_TRACE_FACT_KEY_MAX_LEN
        ):
            raise ValueError(
                f"I-DTRACE-01 violated: DispatchTraceStep.{name} key must be "
                f"non-empty printable under {DISPATCH_TRACE_FACT_KEY_MAX_LEN} "
                "chars"
            )
        if (
            not isinstance(value, str)
            or len(value) > DISPATCH_TRACE_FACT_VALUE_MAX_LEN
        ):
            raise ValueError(
                f"I-DTRACE-01 violated: DispatchTraceStep.{name} value must "
                f"be a string under {DISPATCH_TRACE_FACT_VALUE_MAX_LEN} chars"
            )
        if value and not value.isprintable():
            raise ValueError(
                f"I-DTRACE-01 violated: DispatchTraceStep.{name} value must "
                "be printable"
            )
        term = _text_has_forbidden_term(value)
        if term is not None:
            raise ValueError(
                f"I-DTRACE-01 violated: DispatchTraceStep.{name} value "
                f"contains forbidden non-claim term {term!r}"
            )


def _validate_bounded_string(name: str, value: str, *, max_len: int) -> None:
    if not isinstance(value, str):
        raise TypeError(
            f"I-DTRACE-01 violated: DispatchTraceStep.{name} must be a string"
        )
    if len(value) > max_len:
        raise ValueError(
            f"I-DTRACE-01 violated: DispatchTraceStep.{name} length exceeds "
            f"{max_len}"
        )
    if value and not value.isprintable():
        raise ValueError(
            f"I-DTRACE-01 violated: DispatchTraceStep.{name} must be "
            "printable"
        )
    term = _text_has_forbidden_term(value)
    if term is not None:
        raise ValueError(
            f"I-DTRACE-01 violated: DispatchTraceStep.{name} contains "
            f"forbidden non-claim term {term!r}"
        )


@dataclass(frozen=True, slots=True)
class DispatchTraceStep:
    """One bounded step in a dispatch trace."""

    step_index: int
    kind: DispatchTraceKind
    command_kind: str
    mutation_kind: DispatchMutationKind
    status: DispatchTraceStatus
    route_label: str
    before_facts: tuple[tuple[str, str], ...]
    after_facts: tuple[tuple[str, str], ...]
    derived_facts: str
    limitation_label: str
    digest_contribution: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.step_index, int)
            or isinstance(self.step_index, bool)
            or self.step_index < 1
            or self.step_index > DISPATCH_TRACE_MAX_STEPS
        ):
            raise ValueError(
                "I-DTRACE-01 violated: DispatchTraceStep.step_index must be "
                f"an int in [1, {DISPATCH_TRACE_MAX_STEPS}]"
            )
        if not isinstance(self.kind, DispatchTraceKind):
            raise TypeError(
                "I-DTRACE-01 violated: DispatchTraceStep.kind must be a "
                "DispatchTraceKind member"
            )
        if not isinstance(self.mutation_kind, DispatchMutationKind):
            raise TypeError(
                "I-DTRACE-01 violated: DispatchTraceStep.mutation_kind must "
                "be a DispatchMutationKind member"
            )
        if not isinstance(self.status, DispatchTraceStatus):
            raise TypeError(
                "I-DTRACE-01 violated: DispatchTraceStep.status must be a "
                "DispatchTraceStatus member"
            )
        _validate_bounded_string(
            "command_kind",
            self.command_kind,
            max_len=DISPATCH_TRACE_COMMAND_KIND_MAX_LEN,
        )
        _validate_bounded_string(
            "route_label",
            self.route_label,
            max_len=DISPATCH_TRACE_ROUTE_LABEL_MAX_LEN,
        )
        _validate_facts("before_facts", self.before_facts)
        _validate_facts("after_facts", self.after_facts)
        _validate_bounded_string(
            "derived_facts",
            self.derived_facts,
            max_len=DISPATCH_TRACE_STEP_FIELD_MAX_LEN,
        )
        _validate_bounded_string(
            "limitation_label",
            self.limitation_label,
            max_len=DISPATCH_TRACE_STEP_FIELD_MAX_LEN,
        )
        _validate_bounded_string(
            "digest_contribution",
            self.digest_contribution,
            max_len=DISPATCH_TRACE_STEP_FIELD_MAX_LEN,
        )


@dataclass(frozen=True, slots=True)
class DispatchTrace:
    """A bounded tuple of DispatchTraceStep entries."""

    steps: tuple[DispatchTraceStep, ...]
    interaction_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.steps, tuple):
            raise TypeError(
                "I-DTRACE-01 violated: DispatchTrace.steps must be a tuple"
            )
        if not self.steps:
            raise ValueError(
                "I-DTRACE-01 violated: DispatchTrace.steps must be non-empty"
            )
        if len(self.steps) > DISPATCH_TRACE_MAX_STEPS:
            raise ValueError(
                "I-DTRACE-01 violated: DispatchTrace.steps length exceeds "
                f"{DISPATCH_TRACE_MAX_STEPS}"
            )
        for i, s in enumerate(self.steps, start=1):
            if not isinstance(s, DispatchTraceStep):
                raise TypeError(
                    "I-DTRACE-01 violated: DispatchTrace.steps entries must "
                    "be DispatchTraceStep"
                )
            if s.step_index != i:
                raise ValueError(
                    "I-DTRACE-01 violated: DispatchTrace.steps step_index "
                    "sequence must be 1..len(steps)"
                )
        if (
            not isinstance(self.interaction_id, str)
            or not self.interaction_id
            or not self.interaction_id.isprintable()
            or len(self.interaction_id)
            > DISPATCH_TRACE_INTERACTION_ID_MAX_LEN
        ):
            raise ValueError(
                "I-DTRACE-01 violated: DispatchTrace.interaction_id must be "
                "non-empty printable text under "
                f"{DISPATCH_TRACE_INTERACTION_ID_MAX_LEN} chars"
            )

    def step_kinds(self) -> tuple[DispatchTraceKind, ...]:
        return tuple(s.kind for s in self.steps)

    def mutation_kinds(self) -> tuple[DispatchMutationKind, ...]:
        return tuple(s.mutation_kind for s in self.steps)


@dataclass(frozen=True, slots=True)
class DispatchTraceDigest:
    """A tiny citation record over a DispatchTrace.

    Callers (the reasoning trace and the learning evidence ledger) cite
    a dispatch trace via this record so they need not serialize the
    full trace.
    """

    digest_hex16: str
    command_kind: str
    mutation_kind: DispatchMutationKind
    route_path: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.digest_hex16, str)
            or len(self.digest_hex16) != DISPATCH_TRACE_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-DTRACE-02 violated: DispatchTraceDigest.digest_hex16 must "
                f"be a {DISPATCH_TRACE_DIGEST_HEX_LEN}-char hex string"
            )
        if not isinstance(self.mutation_kind, DispatchMutationKind):
            raise TypeError(
                "I-DTRACE-02 violated: DispatchTraceDigest.mutation_kind "
                "must be a DispatchMutationKind member"
            )
        for field_name, max_len in (
            ("command_kind", DISPATCH_TRACE_COMMAND_KIND_MAX_LEN),
            ("route_path", DISPATCH_TRACE_ROUTE_PATH_MAX_LEN),
        ):
            value = getattr(self, field_name)
            if (
                not isinstance(value, str)
                or not value
                or not value.isprintable()
                or len(value) > max_len
            ):
                raise ValueError(
                    f"I-DTRACE-02 violated: DispatchTraceDigest.{field_name} "
                    f"must be non-empty printable text under {max_len} chars"
                )
            term = _text_has_forbidden_term(value)
            if term is not None:
                raise ValueError(
                    f"I-DTRACE-02 violated: DispatchTraceDigest.{field_name} "
                    f"contains forbidden non-claim term {term!r}"
                )


@dataclass(frozen=True, slots=True)
class DispatchTraceReport:
    """A bounded printable report over a DispatchTrace."""

    trace: DispatchTrace
    step_total: int
    command_received_count: int
    route_selected_count: int
    pre_state_snapshot_count: int
    handler_entered_count: int
    handler_returned_count: int
    post_state_snapshot_count: int
    mutation_classified_count: int
    autosave_checked_count: int
    resource_audit_checked_count: int
    trace_finalized_count: int
    error_recorded_count: int
    noop_recorded_count: int
    command_kind: str
    mutation_kind: DispatchMutationKind
    overall_status: DispatchTraceStatus
    route_path: str
    trace_digest_hex16: str
    summary_line: str

    def __post_init__(self) -> None:
        if not isinstance(self.trace, DispatchTrace):
            raise TypeError(
                "I-DTRACE-02 violated: DispatchTraceReport.trace must be a "
                "DispatchTrace"
            )
        for count_name in (
            "step_total",
            "command_received_count",
            "route_selected_count",
            "pre_state_snapshot_count",
            "handler_entered_count",
            "handler_returned_count",
            "post_state_snapshot_count",
            "mutation_classified_count",
            "autosave_checked_count",
            "resource_audit_checked_count",
            "trace_finalized_count",
            "error_recorded_count",
            "noop_recorded_count",
        ):
            value = getattr(self, count_name)
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(
                    f"I-DTRACE-02 violated: DispatchTraceReport.{count_name} "
                    "must be int"
                )
            if value < 0:
                raise ValueError(
                    f"I-DTRACE-02 violated: DispatchTraceReport.{count_name} "
                    "must be non-negative"
                )
        if not isinstance(self.mutation_kind, DispatchMutationKind):
            raise TypeError(
                "I-DTRACE-02 violated: DispatchTraceReport.mutation_kind "
                "must be a DispatchMutationKind member"
            )
        if not isinstance(self.overall_status, DispatchTraceStatus):
            raise TypeError(
                "I-DTRACE-02 violated: DispatchTraceReport.overall_status "
                "must be a DispatchTraceStatus member"
            )
        if (
            not isinstance(self.trace_digest_hex16, str)
            or len(self.trace_digest_hex16) != DISPATCH_TRACE_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-DTRACE-02 violated: DispatchTraceReport.trace_digest_hex16 "
                f"must be a {DISPATCH_TRACE_DIGEST_HEX_LEN}-char hex string"
            )
        for field_name, max_len in (
            ("command_kind", DISPATCH_TRACE_COMMAND_KIND_MAX_LEN),
            ("route_path", DISPATCH_TRACE_ROUTE_PATH_MAX_LEN),
            ("summary_line", DISPATCH_TRACE_REPORT_SUMMARY_MAX_LEN),
        ):
            value = getattr(self, field_name)
            if (
                not isinstance(value, str)
                or not value
                or not value.isprintable()
                or len(value) > max_len
            ):
                raise ValueError(
                    f"I-DTRACE-02 violated: DispatchTraceReport.{field_name} "
                    f"must be non-empty printable text under {max_len} chars"
                )
            term = _text_has_forbidden_term(value)
            if term is not None:
                raise ValueError(
                    f"I-DTRACE-02 violated: DispatchTraceReport.{field_name} "
                    f"contains forbidden non-claim term {term!r}"
                )


# ---------------------------------------------------------------------------
# Optional configuration (currently a documentation surface).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DispatchTraceConfig:
    """Bounded configuration record for the dispatch tracer.

    Currently a documentation surface: the tracer's bounds are hard
    constants in this module, so the only field exposed here is
    ``module_version`` (the version label baked into every produced
    summary line). Future tracer extensions should add new fields here
    rather than touching :class:`DispatchTraceStep` or
    :class:`DispatchTrace`.
    """

    module_version: str = DISPATCH_TRACE_MODULE_VERSION

    def __post_init__(self) -> None:
        if (
            not isinstance(self.module_version, str)
            or not self.module_version
            or not self.module_version.isprintable()
            or len(self.module_version) > DISPATCH_TRACE_COMMAND_KIND_MAX_LEN
        ):
            raise ValueError(
                "I-DTRACE-02 violated: DispatchTraceConfig.module_version "
                "must be non-empty printable text"
            )


# ---------------------------------------------------------------------------
# Builder helpers.
# ---------------------------------------------------------------------------


def _bounded(text: str, *, limit: int = DISPATCH_TRACE_STEP_FIELD_MAX_LEN) -> str:
    if len(text) > limit:
        return text[: limit - 4] + " ..."
    return text


def _bounded_value(value: str) -> str:
    if len(value) > DISPATCH_TRACE_FACT_VALUE_MAX_LEN:
        return value[: DISPATCH_TRACE_FACT_VALUE_MAX_LEN - 3] + "..."
    return value


def _bounded_facts(
    pairs: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    bounded: list[tuple[str, str]] = []
    for key, value in pairs[:DISPATCH_TRACE_BEFORE_AFTER_MAX_ENTRIES]:
        bounded.append((key, _bounded_value(value)))
    return tuple(bounded)


@dataclass(slots=True)
class _DispatchTraceBuilder:
    """Mutable builder for assembling a DispatchTrace.

    Internal helper. Outside callers go through
    :func:`new_dispatch_trace_builder` and consume the builder in one
    call. The builder is NOT a leaked runtime state — it is frozen
    into a :class:`DispatchTrace` by :meth:`freeze`.
    """

    interaction_id: str
    steps: list[DispatchTraceStep]

    def add(
        self,
        kind: DispatchTraceKind,
        *,
        command_kind: str = "",
        mutation_kind: DispatchMutationKind = DispatchMutationKind.NONE,
        status: DispatchTraceStatus = DispatchTraceStatus.NOT_APPLICABLE,
        route_label: str = "",
        before_facts: tuple[tuple[str, str], ...] = (),
        after_facts: tuple[tuple[str, str], ...] = (),
        derived_facts: str = "",
        limitation_label: str = "",
        digest_contribution: str = "",
    ) -> DispatchTraceStep:
        step_index = len(self.steps) + 1
        if step_index > DISPATCH_TRACE_MAX_STEPS:
            raise ValueError(
                "I-DTRACE-01 violated: dispatch trace exceeded "
                f"{DISPATCH_TRACE_MAX_STEPS} steps"
            )
        step = DispatchTraceStep(
            step_index=step_index,
            kind=kind,
            command_kind=_bounded(
                command_kind, limit=DISPATCH_TRACE_COMMAND_KIND_MAX_LEN
            ),
            mutation_kind=mutation_kind,
            status=status,
            route_label=_bounded(
                route_label, limit=DISPATCH_TRACE_ROUTE_LABEL_MAX_LEN
            ),
            before_facts=_bounded_facts(before_facts),
            after_facts=_bounded_facts(after_facts),
            derived_facts=_bounded(derived_facts),
            limitation_label=_bounded(limitation_label),
            digest_contribution=_bounded(digest_contribution),
        )
        self.steps.append(step)
        return step

    def freeze(self) -> DispatchTrace:
        return DispatchTrace(
            steps=tuple(self.steps), interaction_id=self.interaction_id
        )


def new_dispatch_trace_builder(interaction_id: str) -> _DispatchTraceBuilder:
    """Return a fresh builder for assembling a DispatchTrace."""
    return _DispatchTraceBuilder(interaction_id=interaction_id, steps=[])


def _facts_str(facts: tuple[tuple[str, str], ...]) -> str:
    parts = [f"{k}={v}" for k, v in facts]
    return ",".join(parts)


def _serialize_step(s: DispatchTraceStep) -> str:
    return (
        f"n={s.step_index}|kind={s.kind.value}|"
        f"cmd={s.command_kind}|mut={s.mutation_kind.value}|"
        f"sts={s.status.value}|route={s.route_label}|"
        f"pre={_facts_str(s.before_facts)}|"
        f"post={_facts_str(s.after_facts)}|"
        f"drv={s.derived_facts}|lim={s.limitation_label}|"
        f"dgc={s.digest_contribution}"
    )


def _compute_trace_digest(trace: DispatchTrace) -> str:
    payload = (trace.interaction_id + "\n").encode("utf-8") + "\n".join(
        _serialize_step(s) for s in trace.steps
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[
        :DISPATCH_TRACE_DIGEST_HEX_LEN
    ]


def _primary_command_kind(trace: DispatchTrace) -> str:
    """Return the bounded command_kind label of the trace.

    Picks the first non-empty ``command_kind`` field across the steps.
    Falls back to ``"<unspecified>"`` if every step carries an empty
    command_kind (should not happen in practice because
    :data:`DispatchTraceKind.COMMAND_RECEIVED` always populates it).
    """
    for s in trace.steps:
        if s.command_kind:
            return s.command_kind
    return "<unspecified>"


def _primary_mutation_kind(trace: DispatchTrace) -> DispatchMutationKind:
    """Return the bounded mutation_kind classification of the trace.

    Prefers the kind on the ``MUTATION_CLASSIFIED`` step (if present).
    Falls back to the ``ERROR_RECORDED`` step's kind on error paths.
    Falls back to :data:`DispatchMutationKind.NONE` for NOOP.
    """
    for s in trace.steps:
        if s.kind is DispatchTraceKind.MUTATION_CLASSIFIED:
            return s.mutation_kind
    for s in trace.steps:
        if s.kind is DispatchTraceKind.ERROR_RECORDED:
            return s.mutation_kind
    return DispatchMutationKind.NONE


def _overall_status(trace: DispatchTrace) -> DispatchTraceStatus:
    """Aggregate the per-step status into an overall trace status.

    FAIL dominates. WARN is next. Otherwise PASS unless every step is
    NOT_APPLICABLE.
    """
    saw_fail = False
    saw_warn = False
    saw_pass = False
    for s in trace.steps:
        if s.status is DispatchTraceStatus.FAIL:
            saw_fail = True
        elif s.status is DispatchTraceStatus.WARN:
            saw_warn = True
        elif s.status is DispatchTraceStatus.PASS:
            saw_pass = True
    if saw_fail:
        return DispatchTraceStatus.FAIL
    if saw_warn:
        return DispatchTraceStatus.WARN
    if saw_pass:
        return DispatchTraceStatus.PASS
    return DispatchTraceStatus.NOT_APPLICABLE


def _route_path(trace: DispatchTrace) -> str:
    """Return a bounded ``->``-joined path of distinct route_labels."""
    seen: list[str] = []
    for s in trace.steps:
        if s.route_label and s.route_label not in seen:
            seen.append(s.route_label)
    if not seen:
        return "<no-route>"
    joined = "->".join(seen)
    return _bounded(joined, limit=DISPATCH_TRACE_ROUTE_PATH_MAX_LEN)


def build_dispatch_trace_report(
    trace: DispatchTrace,
) -> DispatchTraceReport:
    """Deterministically build a bounded report over the trace."""
    if not isinstance(trace, DispatchTrace):
        raise TypeError(
            "I-DTRACE-02 violated: build_dispatch_trace_report trace must be "
            "a DispatchTrace"
        )
    counts: dict[DispatchTraceKind, int] = {}
    for s in trace.steps:
        counts[s.kind] = counts.get(s.kind, 0) + 1

    digest = _compute_trace_digest(trace)
    step_total = len(trace.steps)
    command_kind = _primary_command_kind(trace)
    mutation_kind = _primary_mutation_kind(trace)
    overall_status = _overall_status(trace)
    route_path = _route_path(trace)

    summary = (
        f"dispatch-trace iid={trace.interaction_id} steps={step_total} "
        f"cmd={command_kind} mut={mutation_kind.value} "
        f"sts={overall_status.value} route={route_path} "
        f"digest={digest}"
    )
    if len(summary) > DISPATCH_TRACE_REPORT_SUMMARY_MAX_LEN:
        summary = summary[: DISPATCH_TRACE_REPORT_SUMMARY_MAX_LEN - 4] + " ..."
    return DispatchTraceReport(
        trace=trace,
        step_total=step_total,
        command_received_count=counts.get(
            DispatchTraceKind.COMMAND_RECEIVED, 0
        ),
        route_selected_count=counts.get(
            DispatchTraceKind.ROUTE_SELECTED, 0
        ),
        pre_state_snapshot_count=counts.get(
            DispatchTraceKind.PRE_STATE_SNAPSHOT, 0
        ),
        handler_entered_count=counts.get(
            DispatchTraceKind.HANDLER_ENTERED, 0
        ),
        handler_returned_count=counts.get(
            DispatchTraceKind.HANDLER_RETURNED, 0
        ),
        post_state_snapshot_count=counts.get(
            DispatchTraceKind.POST_STATE_SNAPSHOT, 0
        ),
        mutation_classified_count=counts.get(
            DispatchTraceKind.MUTATION_CLASSIFIED, 0
        ),
        autosave_checked_count=counts.get(
            DispatchTraceKind.AUTOSAVE_CHECKED, 0
        ),
        resource_audit_checked_count=counts.get(
            DispatchTraceKind.RESOURCE_AUDIT_CHECKED, 0
        ),
        trace_finalized_count=counts.get(
            DispatchTraceKind.TRACE_FINALIZED, 0
        ),
        error_recorded_count=counts.get(
            DispatchTraceKind.ERROR_RECORDED, 0
        ),
        noop_recorded_count=counts.get(
            DispatchTraceKind.NOOP_RECORDED, 0
        ),
        command_kind=command_kind,
        mutation_kind=mutation_kind,
        overall_status=overall_status,
        route_path=route_path,
        trace_digest_hex16=digest,
        summary_line=summary,
    )


def dispatch_trace_digest_from_report(
    report: DispatchTraceReport,
) -> DispatchTraceDigest:
    """Return a tiny citation record over a DispatchTraceReport."""
    if not isinstance(report, DispatchTraceReport):
        raise TypeError(
            "I-DTRACE-02 violated: dispatch_trace_digest_from_report report "
            "must be a DispatchTraceReport"
        )
    return DispatchTraceDigest(
        digest_hex16=report.trace_digest_hex16,
        command_kind=report.command_kind,
        mutation_kind=report.mutation_kind,
        route_path=report.route_path,
    )


def format_dispatch_trace_table(trace: DispatchTrace) -> str:
    """Return a printable bounded table projection of the trace."""
    if not isinstance(trace, DispatchTrace):
        raise TypeError(
            "I-DTRACE-01 violated: format_dispatch_trace_table trace must be "
            "a DispatchTrace"
        )
    lines: list[str] = []
    for s in trace.steps:
        lines.append(
            f"{s.step_index:02d} {s.kind.value:24s} "
            f"cmd={s.command_kind!r} mut={s.mutation_kind.value} "
            f"sts={s.status.value} route={s.route_label!r}"
        )
    body = "\n".join(lines)
    return body


# ---------------------------------------------------------------------------
# Convenience: synthetic dispatch trace for no-dispatch agent-loop paths.
# ---------------------------------------------------------------------------


def build_synthetic_no_dispatch_report(
    *,
    interaction_id: str,
    route_label: str,
    limitation_label: str = "",
) -> DispatchTraceReport:
    """Build a synthetic dispatch trace report for a no-dispatch path.

    The Phase 3.22 agent loop has four no-dispatch paths (REFUSAL,
    FAIL-oversize, WARN-empty, REPL bridge). Those paths bypass
    ``OperatorSession.dispatch`` entirely; this helper produces a
    bounded trace that documents the route without touching any
    session.

    Drives ``I-DTRACE-08`` (AgentLoopResult carries a dispatch trace
    even when no real dispatch happens).
    """
    builder = new_dispatch_trace_builder(interaction_id)
    builder.add(
        DispatchTraceKind.COMMAND_RECEIVED,
        command_kind="<no-dispatch>",
        mutation_kind=DispatchMutationKind.NONE,
        status=DispatchTraceStatus.NOT_APPLICABLE,
        route_label=route_label,
        derived_facts="no-dispatch path; OperatorSession.dispatch not called",
        limitation_label=_bounded(limitation_label),
        digest_contribution=f"no-dispatch:{route_label}",
    )
    builder.add(
        DispatchTraceKind.MUTATION_CLASSIFIED,
        command_kind="<no-dispatch>",
        mutation_kind=DispatchMutationKind.NONE,
        status=DispatchTraceStatus.NOT_APPLICABLE,
        route_label=route_label,
        derived_facts="mutation_kind=none",
        limitation_label=_bounded(limitation_label),
        digest_contribution="mutation:none",
    )
    builder.add(
        DispatchTraceKind.TRACE_FINALIZED,
        command_kind="<no-dispatch>",
        mutation_kind=DispatchMutationKind.NONE,
        status=DispatchTraceStatus.NOT_APPLICABLE,
        route_label=route_label,
        derived_facts="trace-finalized",
        digest_contribution="trace-finalized",
    )
    trace = builder.freeze()
    return build_dispatch_trace_report(trace)


# ---------------------------------------------------------------------------
# Module-produced strings (audited).
# ---------------------------------------------------------------------------

MODULE_PRODUCED_STRINGS: tuple[str, ...] = (
    DISPATCH_TRACE_MODULE_VERSION,
    DISPATCH_TRACE_DISCLAIMER,
    DispatchTraceKind.COMMAND_RECEIVED.value,
    DispatchTraceKind.ROUTE_SELECTED.value,
    DispatchTraceKind.PRE_STATE_SNAPSHOT.value,
    DispatchTraceKind.HANDLER_ENTERED.value,
    DispatchTraceKind.HANDLER_RETURNED.value,
    DispatchTraceKind.POST_STATE_SNAPSHOT.value,
    DispatchTraceKind.MUTATION_CLASSIFIED.value,
    DispatchTraceKind.AUTOSAVE_CHECKED.value,
    DispatchTraceKind.RESOURCE_AUDIT_CHECKED.value,
    DispatchTraceKind.TRACE_FINALIZED.value,
    DispatchTraceKind.ERROR_RECORDED.value,
    DispatchTraceKind.NOOP_RECORDED.value,
    DispatchMutationKind.NONE.value,
    DispatchMutationKind.UI_ONLY.value,
    DispatchMutationKind.STREAM_APPEND.value,
    DispatchMutationKind.STREAM_WINDOW_INTERNAL.value,
    DispatchMutationKind.STREAM_PROMOTE.value,
    DispatchMutationKind.QUEUE_MUTATION.value,
    DispatchMutationKind.STEP_TICK.value,
    DispatchMutationKind.SESSION_PERSISTENCE.value,
    DispatchMutationKind.AUTOSAVE.value,
    DispatchMutationKind.DB_OBSERVE.value,
    DispatchMutationKind.DB_BACKUP.value,
    DispatchMutationKind.VIEW_CHANGE.value,
    DispatchMutationKind.QUIT_FLAG.value,
    DispatchMutationKind.ERROR_ONLY.value,
    DispatchTraceStatus.PASS.value,
    DispatchTraceStatus.WARN.value,
    DispatchTraceStatus.FAIL.value,
    DispatchTraceStatus.NOT_APPLICABLE.value,
)


__all__ = (
    "DISPATCH_TRACE_BEFORE_AFTER_MAX_ENTRIES",
    "DISPATCH_TRACE_COMMAND_KIND_MAX_LEN",
    "DISPATCH_TRACE_DIGEST_HEX_LEN",
    "DISPATCH_TRACE_DISCLAIMER",
    "DISPATCH_TRACE_FACT_KEY_MAX_LEN",
    "DISPATCH_TRACE_FACT_VALUE_MAX_LEN",
    "DISPATCH_TRACE_INTERACTION_ID_MAX_LEN",
    "DISPATCH_TRACE_MAX_STEPS",
    "DISPATCH_TRACE_MODULE_VERSION",
    "DISPATCH_TRACE_REPORT_SUMMARY_MAX_LEN",
    "DISPATCH_TRACE_ROUTE_LABEL_MAX_LEN",
    "DISPATCH_TRACE_ROUTE_PATH_MAX_LEN",
    "DISPATCH_TRACE_STEP_FIELD_MAX_LEN",
    "DispatchMutationKind",
    "DispatchTrace",
    "DispatchTraceConfig",
    "DispatchTraceDigest",
    "DispatchTraceKind",
    "DispatchTraceReport",
    "DispatchTraceStatus",
    "DispatchTraceStep",
    "MODULE_PRODUCED_STRINGS",
    "build_dispatch_trace_report",
    "build_synthetic_no_dispatch_report",
    "dispatch_trace_digest_from_report",
    "format_dispatch_trace_table",
    "new_dispatch_trace_builder",
)
