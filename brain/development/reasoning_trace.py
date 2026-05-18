"""Phase 3.22b Reasoning Trace — explicit audit trail of structural ops.

"Reasoning trace" in Phase 3.22b means an **explicit audit trail of
deterministic structural operations**. The trace is externally
inspectable, bounded, printable, and non-claim-clean. It is NOT
private chain-of-thought. It is NOT a metacognitive description of
any "inner experience" of the running system.

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

Drives ``I-AGENTLEARN-08`` and ``I-AGENTLEARN-09`` (integration) and
contributes to ``I-AGENTLEARN-11`` (static audit).
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

REASONING_TRACE_MAX_STEPS: int = 32
REASONING_STEP_FIELD_MAX_LEN: int = 160
REASONING_TRACE_DIGEST_HEX_LEN: int = 16
REASONING_REPORT_SUMMARY_MAX_LEN: int = 320
REASONING_TRACE_MODULE_VERSION: str = "phase3.22b.v1"

REASONING_TRACE_DISCLAIMER: str = (
    "audit trail of deterministic structural operations only; "
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
# Closed enum.
# ---------------------------------------------------------------------------


class ReasoningStepKind(str, Enum):
    """Closed enum of trace-step kinds."""

    OBSERVE_INPUT = "observe_input"
    CLASSIFY_REFUSAL = "classify_refusal"
    DERIVE_PATTERN = "derive_pattern"
    LOOKUP_PRIOR_STRUCTURE = "lookup_prior_structure"
    COMPARE_STRUCTURE = "compare_structure"
    CHECK_COHERENCE = "check_coherence"
    CHECK_REPL = "check_repl"
    SELECT_REPLY_DISPOSITION = "select_reply_disposition"
    CHECK_LIMITATION = "check_limitation"
    # Phase 3.23 (I-DTRACE-09): record the dispatch trace digest that
    # accompanies this reasoning trace. Inserted immediately before
    # EMIT_REPLY so the reply can cite the dispatch route via the
    # bounded dispatch trace digest.
    CHECK_DISPATCH_TRACE = "check_dispatch_trace"
    EMIT_REPLY = "emit_reply"


# ---------------------------------------------------------------------------
# Frozen records.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ReasoningTraceStep:
    """One bounded step in a reasoning trace."""

    step_number: int
    kind: ReasoningStepKind
    input_facts: str
    derived_facts: str
    next_action: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.step_number, int)
            or isinstance(self.step_number, bool)
            or self.step_number < 1
            or self.step_number > REASONING_TRACE_MAX_STEPS
        ):
            raise ValueError(
                "I-AGENTLEARN-08 violated: ReasoningTraceStep.step_number "
                f"must be an int in [1, {REASONING_TRACE_MAX_STEPS}]"
            )
        if not isinstance(self.kind, ReasoningStepKind):
            raise TypeError(
                "I-AGENTLEARN-08 violated: ReasoningTraceStep.kind must be "
                "a ReasoningStepKind member"
            )
        for name, value in (
            ("input_facts", self.input_facts),
            ("derived_facts", self.derived_facts),
            ("next_action", self.next_action),
        ):
            if not isinstance(value, str):
                raise TypeError(
                    "I-AGENTLEARN-08 violated: ReasoningTraceStep."
                    f"{name} must be a string"
                )
            if len(value) > REASONING_STEP_FIELD_MAX_LEN:
                raise ValueError(
                    "I-AGENTLEARN-08 violated: ReasoningTraceStep."
                    f"{name} length exceeds {REASONING_STEP_FIELD_MAX_LEN}"
                )
            if value and not value.isprintable():
                raise ValueError(
                    "I-AGENTLEARN-08 violated: ReasoningTraceStep."
                    f"{name} must be printable"
                )
            term = _text_has_forbidden_term(value)
            if term is not None:
                raise ValueError(
                    "I-AGENTLEARN-08 violated: ReasoningTraceStep."
                    f"{name} contains forbidden non-claim term {term!r}"
                )


@dataclass(frozen=True, slots=True)
class ReasoningTrace:
    """A bounded tuple of ReasoningTraceStep entries."""

    steps: tuple[ReasoningTraceStep, ...]
    input_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.steps, tuple):
            raise TypeError(
                "I-AGENTLEARN-08 violated: ReasoningTrace.steps must be a "
                "tuple"
            )
        if not self.steps:
            raise ValueError(
                "I-AGENTLEARN-08 violated: ReasoningTrace.steps must be "
                "non-empty"
            )
        if len(self.steps) > REASONING_TRACE_MAX_STEPS:
            raise ValueError(
                "I-AGENTLEARN-08 violated: ReasoningTrace.steps length "
                f"exceeds {REASONING_TRACE_MAX_STEPS}"
            )
        for i, s in enumerate(self.steps, start=1):
            if not isinstance(s, ReasoningTraceStep):
                raise TypeError(
                    "I-AGENTLEARN-08 violated: ReasoningTrace.steps "
                    "entries must be ReasoningTraceStep"
                )
            if s.step_number != i:
                raise ValueError(
                    "I-AGENTLEARN-08 violated: ReasoningTrace.steps "
                    "step_number sequence must be 1..len(steps)"
                )
        if (
            not isinstance(self.input_id, str)
            or not self.input_id
            or not self.input_id.isprintable()
            or len(self.input_id) > 64
        ):
            raise ValueError(
                "I-AGENTLEARN-08 violated: ReasoningTrace.input_id must "
                "be non-empty printable text under 64 chars"
            )

    def filter_kind(self, kind: ReasoningStepKind) -> "ReasoningTrace":
        # Returns a new ReasoningTrace with steps renumbered. The
        # renumbering maintains the invariant that step_number is
        # 1..len(steps).
        kept = tuple(s for s in self.steps if s.kind is kind)
        renumbered = tuple(
            ReasoningTraceStep(
                step_number=i,
                kind=s.kind,
                input_facts=s.input_facts,
                derived_facts=s.derived_facts,
                next_action=s.next_action,
            )
            for i, s in enumerate(kept, start=1)
        )
        if not renumbered:
            return self
        return ReasoningTrace(steps=renumbered, input_id=self.input_id)

    def step_kinds(self) -> tuple[ReasoningStepKind, ...]:
        return tuple(s.kind for s in self.steps)


@dataclass(frozen=True, slots=True)
class ReasoningTraceReport:
    """A bounded printable report over a ReasoningTrace."""

    trace: ReasoningTrace
    step_total: int
    observe_input_count: int
    classify_refusal_count: int
    derive_pattern_count: int
    lookup_prior_structure_count: int
    compare_structure_count: int
    check_coherence_count: int
    check_repl_count: int
    select_reply_disposition_count: int
    check_limitation_count: int
    check_dispatch_trace_count: int
    emit_reply_count: int
    trace_digest_hex16: str
    summary_line: str

    def __post_init__(self) -> None:
        if not isinstance(self.trace, ReasoningTrace):
            raise TypeError(
                "I-AGENTLEARN-09 violated: ReasoningTraceReport.trace must "
                "be a ReasoningTrace"
            )
        for name, value in (
            ("step_total", self.step_total),
            ("observe_input_count", self.observe_input_count),
            ("classify_refusal_count", self.classify_refusal_count),
            ("derive_pattern_count", self.derive_pattern_count),
            ("lookup_prior_structure_count", self.lookup_prior_structure_count),
            ("compare_structure_count", self.compare_structure_count),
            ("check_coherence_count", self.check_coherence_count),
            ("check_repl_count", self.check_repl_count),
            ("select_reply_disposition_count", self.select_reply_disposition_count),
            ("check_limitation_count", self.check_limitation_count),
            ("check_dispatch_trace_count", self.check_dispatch_trace_count),
            ("emit_reply_count", self.emit_reply_count),
        ):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(
                    "I-AGENTLEARN-09 violated: ReasoningTraceReport."
                    f"{name} must be int"
                )
            if value < 0:
                raise ValueError(
                    "I-AGENTLEARN-09 violated: ReasoningTraceReport."
                    f"{name} must be non-negative"
                )
        if (
            not isinstance(self.trace_digest_hex16, str)
            or len(self.trace_digest_hex16)
            != REASONING_TRACE_DIGEST_HEX_LEN
        ):
            raise ValueError(
                "I-AGENTLEARN-09 violated: ReasoningTraceReport."
                "trace_digest_hex16 must be a 16-char hex string"
            )
        if (
            not isinstance(self.summary_line, str)
            or not self.summary_line
            or not self.summary_line.isprintable()
            or len(self.summary_line) > REASONING_REPORT_SUMMARY_MAX_LEN
        ):
            raise ValueError(
                "I-AGENTLEARN-09 violated: ReasoningTraceReport."
                "summary_line must be non-empty printable text under "
                f"{REASONING_REPORT_SUMMARY_MAX_LEN} chars"
            )
        term = _text_has_forbidden_term(self.summary_line)
        if term is not None:
            raise ValueError(
                "I-AGENTLEARN-09 violated: ReasoningTraceReport."
                f"summary_line contains forbidden non-claim term {term!r}"
            )


# ---------------------------------------------------------------------------
# Builder helpers.
# ---------------------------------------------------------------------------


def _bounded(text: str, *, limit: int = REASONING_STEP_FIELD_MAX_LEN) -> str:
    if len(text) > limit:
        return text[: limit - 4] + " ..."
    return text


@dataclass(slots=True)
class _ReasoningTraceBuilder:
    """Mutable builder for assembling a ReasoningTrace.

    Internal helper. Outside callers construct the bounded
    ``ReasoningTrace`` directly via ``build_reasoning_trace`` or by
    constructing each step explicitly. The builder is NOT a leaked
    runtime state — it is consumed in-place by the agent loop in one
    call.
    """

    input_id: str
    steps: list[ReasoningTraceStep]

    def add(
        self,
        kind: ReasoningStepKind,
        *,
        input_facts: str = "",
        derived_facts: str = "",
        next_action: str = "",
    ) -> ReasoningTraceStep:
        step_number = len(self.steps) + 1
        if step_number > REASONING_TRACE_MAX_STEPS:
            raise ValueError(
                "I-AGENTLEARN-08 violated: reasoning trace exceeded "
                f"{REASONING_TRACE_MAX_STEPS} steps"
            )
        step = ReasoningTraceStep(
            step_number=step_number,
            kind=kind,
            input_facts=_bounded(input_facts),
            derived_facts=_bounded(derived_facts),
            next_action=_bounded(next_action),
        )
        self.steps.append(step)
        return step

    def freeze(self) -> ReasoningTrace:
        return ReasoningTrace(
            steps=tuple(self.steps), input_id=self.input_id
        )


def new_trace_builder(input_id: str) -> _ReasoningTraceBuilder:
    return _ReasoningTraceBuilder(input_id=input_id, steps=[])


def build_reasoning_trace(
    *,
    input_id: str,
    steps: tuple[tuple[ReasoningStepKind, str, str, str], ...],
) -> ReasoningTrace:
    """Construct a ReasoningTrace from a bounded tuple of tuples.

    Each tuple is (kind, input_facts, derived_facts, next_action).
    """
    builder = new_trace_builder(input_id)
    for entry in steps:
        kind, input_facts, derived_facts, next_action = entry
        builder.add(
            kind,
            input_facts=input_facts,
            derived_facts=derived_facts,
            next_action=next_action,
        )
    return builder.freeze()


def _serialize_step(s: ReasoningTraceStep) -> str:
    return (
        f"n={s.step_number}|kind={s.kind.value}|"
        f"in={s.input_facts}|drv={s.derived_facts}|nxt={s.next_action}"
    )


def _compute_trace_digest(trace: ReasoningTrace) -> str:
    payload = (trace.input_id + "\n").encode("utf-8") + "\n".join(
        _serialize_step(s) for s in trace.steps
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[
        :REASONING_TRACE_DIGEST_HEX_LEN
    ]


def build_reasoning_trace_report(
    trace: ReasoningTrace,
) -> ReasoningTraceReport:
    """Deterministically build a report over the trace."""
    if not isinstance(trace, ReasoningTrace):
        raise TypeError(
            "I-AGENTLEARN-09 violated: build_reasoning_trace_report trace "
            "must be a ReasoningTrace"
        )
    counts: dict[ReasoningStepKind, int] = {}
    for s in trace.steps:
        counts[s.kind] = counts.get(s.kind, 0) + 1

    digest = _compute_trace_digest(trace)
    step_total = len(trace.steps)
    summary = (
        f"reasoning-trace iid={trace.input_id} steps={step_total} "
        f"obs={counts.get(ReasoningStepKind.OBSERVE_INPUT, 0)} "
        f"clf={counts.get(ReasoningStepKind.CLASSIFY_REFUSAL, 0)} "
        f"drv={counts.get(ReasoningStepKind.DERIVE_PATTERN, 0)} "
        f"lkp={counts.get(ReasoningStepKind.LOOKUP_PRIOR_STRUCTURE, 0)} "
        f"cmp={counts.get(ReasoningStepKind.COMPARE_STRUCTURE, 0)} "
        f"coh={counts.get(ReasoningStepKind.CHECK_COHERENCE, 0)} "
        f"rpl={counts.get(ReasoningStepKind.CHECK_REPL, 0)} "
        f"sel={counts.get(ReasoningStepKind.SELECT_REPLY_DISPOSITION, 0)} "
        f"lim={counts.get(ReasoningStepKind.CHECK_LIMITATION, 0)} "
        f"dtr={counts.get(ReasoningStepKind.CHECK_DISPATCH_TRACE, 0)} "
        f"emit={counts.get(ReasoningStepKind.EMIT_REPLY, 0)} "
        f"digest={digest}"
    )
    if len(summary) > REASONING_REPORT_SUMMARY_MAX_LEN:
        summary = summary[: REASONING_REPORT_SUMMARY_MAX_LEN - 4] + " ..."
    return ReasoningTraceReport(
        trace=trace,
        step_total=step_total,
        observe_input_count=counts.get(ReasoningStepKind.OBSERVE_INPUT, 0),
        classify_refusal_count=counts.get(
            ReasoningStepKind.CLASSIFY_REFUSAL, 0
        ),
        derive_pattern_count=counts.get(
            ReasoningStepKind.DERIVE_PATTERN, 0
        ),
        lookup_prior_structure_count=counts.get(
            ReasoningStepKind.LOOKUP_PRIOR_STRUCTURE, 0
        ),
        compare_structure_count=counts.get(
            ReasoningStepKind.COMPARE_STRUCTURE, 0
        ),
        check_coherence_count=counts.get(
            ReasoningStepKind.CHECK_COHERENCE, 0
        ),
        check_repl_count=counts.get(ReasoningStepKind.CHECK_REPL, 0),
        select_reply_disposition_count=counts.get(
            ReasoningStepKind.SELECT_REPLY_DISPOSITION, 0
        ),
        check_limitation_count=counts.get(
            ReasoningStepKind.CHECK_LIMITATION, 0
        ),
        check_dispatch_trace_count=counts.get(
            ReasoningStepKind.CHECK_DISPATCH_TRACE, 0
        ),
        emit_reply_count=counts.get(ReasoningStepKind.EMIT_REPLY, 0),
        trace_digest_hex16=digest,
        summary_line=summary,
    )


# ---------------------------------------------------------------------------
# Formatting.
# ---------------------------------------------------------------------------


def format_reasoning_trace_table(trace: ReasoningTrace) -> str:
    """Return a printable bounded table projection of the trace."""
    if not isinstance(trace, ReasoningTrace):
        raise TypeError(
            "I-AGENTLEARN-08 violated: format_reasoning_trace_table trace "
            "must be a ReasoningTrace"
        )
    lines: list[str] = []
    for s in trace.steps:
        lines.append(
            f"{s.step_number:02d} {s.kind.value:24s} "
            f"in={s.input_facts!r} drv={s.derived_facts!r} "
            f"nxt={s.next_action!r}"
        )
    body = "\n".join(lines)
    return body


# ---------------------------------------------------------------------------
# Module-produced strings (audited).
# ---------------------------------------------------------------------------

MODULE_PRODUCED_STRINGS: tuple[str, ...] = (
    REASONING_TRACE_MODULE_VERSION,
    REASONING_TRACE_DISCLAIMER,
    ReasoningStepKind.OBSERVE_INPUT.value,
    ReasoningStepKind.CLASSIFY_REFUSAL.value,
    ReasoningStepKind.DERIVE_PATTERN.value,
    ReasoningStepKind.LOOKUP_PRIOR_STRUCTURE.value,
    ReasoningStepKind.COMPARE_STRUCTURE.value,
    ReasoningStepKind.CHECK_COHERENCE.value,
    ReasoningStepKind.CHECK_REPL.value,
    ReasoningStepKind.SELECT_REPLY_DISPOSITION.value,
    ReasoningStepKind.CHECK_LIMITATION.value,
    ReasoningStepKind.CHECK_DISPATCH_TRACE.value,
    ReasoningStepKind.EMIT_REPLY.value,
)


__all__ = (
    "MODULE_PRODUCED_STRINGS",
    "REASONING_REPORT_SUMMARY_MAX_LEN",
    "REASONING_STEP_FIELD_MAX_LEN",
    "REASONING_TRACE_DIGEST_HEX_LEN",
    "REASONING_TRACE_DISCLAIMER",
    "REASONING_TRACE_MAX_STEPS",
    "REASONING_TRACE_MODULE_VERSION",
    "ReasoningStepKind",
    "ReasoningTrace",
    "ReasoningTraceReport",
    "ReasoningTraceStep",
    "build_reasoning_trace",
    "build_reasoning_trace_report",
    "format_reasoning_trace_table",
    "new_trace_builder",
)
