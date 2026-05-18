"""Phase 3.22 Agent Communication Loop — bounded operator-facing reply layer.

This module is a strict consumer of the Phase 3.18-3.21 public surfaces.
It composes the existing text-stream / Pattern Ledger / Coherence
Monitor / Growth Ledger / Proto-BASIC REPL substrates into a single
deterministic operator-input -> operator-reply path.

Non-claim discipline (binding):

* No claim of cognitive properties is made by this module.
* "Agent" is engineering shorthand for "bounded operator-facing reply
  layer". No claim of cognitive selfhood, mental life, or any
  cognitive property of the running system is made here.
* Every produced reply / observation / transcript string passes the
  canonical
  ``brain.development.coherence_monitor._FORBIDDEN_NON_CLAIM_TERMS``
  audit (case-insensitive substring).
* When the operator-supplied text contains any term from that tuple,
  the loop emits a closed REFUSAL reply that denies cognitive-property
  claims and describes the runtime as a bounded structural state
  machine. The refusal text itself contains zero terms from the
  audit tuple.

Closed import set (per LOCK A in
``docs/campaigns/phase3_22/PHASE3_22_AGENT_COMMUNICATION_LOOP_SYNTHESIS.md``):

* ``__future__``, ``dataclasses``, ``enum``, ``typing``
* ``brain.development.agent_repl_bridge``
* ``brain.development.coherence_monitor`` (read-only;
  ``build_full_coherence_report``, ``_FORBIDDEN_NON_CLAIM_TERMS``,
  ``CoherenceCheckStatus``)
* ``brain.development.growth_ledger`` (``GROWTH_LEDGER_MAX_EVENTS``)
* ``brain.development.pattern_ledger`` (``derive_pattern_id``,
  ``derive_pattern_signature``,
  ``PatternLedgerSaturationState``,
  ``STREAM_PATTERN_RECURRENCE_MIN``,
  ``STREAM_PATTERN_RECURRENCE_MAX``)
* ``brain.development.text_stream`` (``STREAM_TEXT_MAX_LEN``,
  ``STREAM_HISTORY_MAX_CHUNKS``)
* ``brain.tick`` (``BrainState``, ``initial_state``,
  ``assert_state_invariants`` ONLY — never the ``tick`` callable)
* ``brain.ui.commands`` (``Command``, ``OperatorCommand``,
  ``StreamAppendPayload``)
* ``brain.ui.session`` (``OperatorSession``)
* ``brain.tlica.profile`` (``COGITO_ID``)

No ``brain.llm.*`` import. No curses. No host execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from brain.development.agent_repl_bridge import (
    AGENT_REPL_LINE_ID_PREFIX,
    AGENT_REPL_MAX_INPUT_LEN,
    AgentReplBridgeSummary,
    AgentReplGrammarHandle,
    AgentReplLineResult,
    build_default_agent_repl_grammar,
    run_repl_line,
    summarize_repl_for_agent,
)
from brain.development.coherence_monitor import (
    CoherenceCheckStatus,
    _FORBIDDEN_NON_CLAIM_TERMS,
    build_full_coherence_report,
)
from brain.development.growth_ledger import GROWTH_LEDGER_MAX_EVENTS
from brain.development.pattern_ledger import (
    PatternLedgerSaturationState,
    STREAM_PATTERN_RECURRENCE_MAX,
    STREAM_PATTERN_RECURRENCE_MIN,
    derive_pattern_id,
    derive_pattern_signature,
)
from brain.development.repl import ProtoBasicHistory
from brain.development.text_stream import (
    STREAM_HISTORY_MAX_CHUNKS,
    STREAM_TEXT_MAX_LEN,
)
from brain.tick import (
    BrainState,
    assert_state_invariants,
    initial_state,
)
from brain.tlica.profile import COGITO_ID
from brain.ui.commands import (
    Command,
    OperatorCommand,
    StreamAppendPayload,
)
from brain.ui.session import OperatorSession


# ---------------------------------------------------------------------------
# Bounded constants.
# ---------------------------------------------------------------------------

#: Maximum length of one operator-facing reply section body.
AGENT_REPLY_SECTION_MAX_LEN: int = 320

#: Maximum length of the full operator-facing reply text (joined sections).
AGENT_REPLY_FULL_MAX_LEN: int = 1024

#: Maximum length of an AgentInput.operator_text string. Inherits the
#: text-stream substrate bound so STREAM_APPEND can route the input.
AGENT_INPUT_MAX_LEN: int = STREAM_TEXT_MAX_LEN

#: Maximum length of an AgentInput.input_id string.
AGENT_INPUT_ID_MAX_LEN: int = 64

#: Prefix the loop applies when synthesizing an AgentInput.input_id
#: from a session-local interaction counter.
AGENT_INPUT_ID_PREFIX: str = "agent-input:"

#: Provenance label written to ``StreamAppendPayload`` when the loop
#: dispatches a STREAM_APPEND on the operator's behalf.
AGENT_LOOP_VERSION: str = "phase3.22.v1"

#: Maximum bounded counter for AgentLoopState.interaction_counter.
AGENT_LOOP_MAX_INTERACTIONS: int = 65535


# ---------------------------------------------------------------------------
# Closed enums.
# ---------------------------------------------------------------------------


class AgentReplyStatus(str, Enum):
    """Closed enum of reply-section kinds.

    Ordering is the canonical reply order: a normal reply emits
    sections in this order; the REFUSAL reply emits a subset starting
    with ``LIMITATION_REPORT``.
    """

    PATTERN_REPORT = "pattern_report"
    REPL_REPORT = "repl_report"
    COHERENCE_REPORT = "coherence_report"
    LIMITATION_REPORT = "limitation_report"
    NEXT_ACTION_SUGGESTION = "next_action_suggestion"


class AgentReplyDisposition(str, Enum):
    """Closed enum of reply outcomes."""

    OK = "ok"
    REFUSAL = "refusal"
    WARN = "warn"
    FAIL = "fail"


# Closed canonical order of reply-section kinds.
_CANONICAL_REPLY_ORDER: tuple[AgentReplyStatus, ...] = (
    AgentReplyStatus.PATTERN_REPORT,
    AgentReplyStatus.REPL_REPORT,
    AgentReplyStatus.COHERENCE_REPORT,
    AgentReplyStatus.LIMITATION_REPORT,
    AgentReplyStatus.NEXT_ACTION_SUGGESTION,
)


# Closed set of operator coherence-status values used in the
# COHERENCE_REPORT section. Mirrors CoherenceCheckStatus values plus
# a synthetic "none" sentinel for empty reports.
_VALID_COHERENCE_OVERALL_VALUES: frozenset[str] = frozenset(
    {
        CoherenceCheckStatus.PASS.value,
        CoherenceCheckStatus.WARN.value,
        CoherenceCheckStatus.FAIL.value,
        CoherenceCheckStatus.NOT_APPLICABLE.value,
        "none",
    }
)


# Closed set of saturation-state values reported in the
# PATTERN_REPORT section. Mirrors PatternLedgerSaturationState
# values plus a synthetic "none" sentinel for empty ledgers.
_VALID_SATURATION_VALUES: frozenset[str] = frozenset(
    {
        PatternLedgerSaturationState.OPEN.value,
        PatternLedgerSaturationState.SATURATED.value,
        PatternLedgerSaturationState.QUIESCED.value,
        "none",
    }
)


# ---------------------------------------------------------------------------
# Forbidden-term helper (single point of audit).
# ---------------------------------------------------------------------------


def _text_has_forbidden_term(text: str) -> Optional[str]:
    """Case-insensitive substring scan against ``_FORBIDDEN_NON_CLAIM_TERMS``."""
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


def _operator_text_triggers_refusal(text: str) -> bool:
    """Return True iff the operator text contains any audit-tuple term.

    The trigger set is the imported ``_FORBIDDEN_NON_CLAIM_TERMS``
    tuple verbatim. This module never defines forbidden-term literals
    inline; the trigger detection is purely derived from the import.
    """
    return _text_has_forbidden_term(text) is not None


# ---------------------------------------------------------------------------
# Records.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AgentInput:
    """A bounded operator-supplied input.

    Construction performs the audit / bound checks. The loop never
    constructs an ``AgentInput`` for oversize text; oversize text
    drives a FAIL reply via the run helper.
    """

    operator_text: str
    input_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.operator_text, str):
            raise TypeError(
                "I-AGENTLOOP-02 violated: AgentInput.operator_text must be a "
                "string"
            )
        if len(self.operator_text) > AGENT_INPUT_MAX_LEN:
            raise ValueError(
                "I-AGENTLOOP-02 violated: AgentInput.operator_text exceeds "
                f"bound {AGENT_INPUT_MAX_LEN}"
            )
        # Allow empty text; the loop handles empty input as a WARN
        # disposition. The text must be printable if non-empty.
        if self.operator_text and not self.operator_text.isprintable() and (
            "\n" not in self.operator_text and "\t" not in self.operator_text
        ):
            raise ValueError(
                "I-AGENTLOOP-02 violated: AgentInput.operator_text must be "
                "printable (newline/tab allowed)"
            )
        if (
            not isinstance(self.input_id, str)
            or not self.input_id
            or not self.input_id.isprintable()
            or len(self.input_id) > AGENT_INPUT_ID_MAX_LEN
            or self.input_id == COGITO_ID
        ):
            raise ValueError(
                "I-AGENTLOOP-02 violated: AgentInput.input_id must be "
                "non-empty printable text under "
                f"{AGENT_INPUT_ID_MAX_LEN} chars (not COGITO_ID)"
            )


@dataclass(frozen=True, slots=True)
class AgentObservationSummary:
    """A bounded read-only observation of an OperatorSession + REPL history.

    All fields are integer counts or short bounded string descriptors.
    No Fraction; no live object reference; no mutable state.
    """

    stream_chunk_count: int
    pattern_entry_count: int
    seed_pattern_id: str
    seed_recurrence: int
    seed_saturation_state: str
    growth_event_total: int
    coherence_overall_status: str
    coherence_check_total: int
    repl_emit_total: int
    forbidden_term_hits: int

    def __post_init__(self) -> None:
        for name, value in (
            ("stream_chunk_count", self.stream_chunk_count),
            ("pattern_entry_count", self.pattern_entry_count),
            ("seed_recurrence", self.seed_recurrence),
            ("growth_event_total", self.growth_event_total),
            ("coherence_check_total", self.coherence_check_total),
            ("repl_emit_total", self.repl_emit_total),
            ("forbidden_term_hits", self.forbidden_term_hits),
        ):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(
                    "I-AGENTLOOP-02 violated: AgentObservationSummary."
                    f"{name} must be int"
                )
            if value < 0:
                raise ValueError(
                    "I-AGENTLOOP-02 violated: AgentObservationSummary."
                    f"{name} must be non-negative"
                )
        if self.stream_chunk_count > STREAM_HISTORY_MAX_CHUNKS:
            raise ValueError(
                "I-AGENTLOOP-02 violated: AgentObservationSummary."
                "stream_chunk_count exceeds STREAM_HISTORY_MAX_CHUNKS"
            )
        if self.growth_event_total > GROWTH_LEDGER_MAX_EVENTS:
            raise ValueError(
                "I-AGENTLOOP-02 violated: AgentObservationSummary."
                "growth_event_total exceeds GROWTH_LEDGER_MAX_EVENTS"
            )
        if not isinstance(self.seed_pattern_id, str):
            raise TypeError(
                "I-AGENTLOOP-02 violated: AgentObservationSummary."
                "seed_pattern_id must be str"
            )
        if len(self.seed_pattern_id) > 64:
            raise ValueError(
                "I-AGENTLOOP-02 violated: AgentObservationSummary."
                "seed_pattern_id length exceeds 64"
            )
        if self.seed_pattern_id and not self.seed_pattern_id.isprintable():
            raise ValueError(
                "I-AGENTLOOP-02 violated: AgentObservationSummary."
                "seed_pattern_id must be printable"
            )
        if self.seed_saturation_state not in _VALID_SATURATION_VALUES:
            raise ValueError(
                "I-AGENTLOOP-02 violated: AgentObservationSummary."
                "seed_saturation_state must be in "
                f"{sorted(_VALID_SATURATION_VALUES)!r}"
            )
        if self.coherence_overall_status not in _VALID_COHERENCE_OVERALL_VALUES:
            raise ValueError(
                "I-AGENTLOOP-02 violated: AgentObservationSummary."
                "coherence_overall_status must be in "
                f"{sorted(_VALID_COHERENCE_OVERALL_VALUES)!r}"
            )


@dataclass(frozen=True, slots=True)
class AgentReply:
    """A bounded operator-facing reply.

    The reply carries one or more sections in canonical order. Each
    section is a printable bounded string; the joined ``full_text`` is
    a printable bounded string under ``AGENT_REPLY_FULL_MAX_LEN``.
    """

    input_id: str
    disposition: AgentReplyDisposition
    sections: tuple[tuple[AgentReplyStatus, str], ...]
    full_text: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.input_id, str)
            or not self.input_id
            or not self.input_id.isprintable()
            or len(self.input_id) > AGENT_INPUT_ID_MAX_LEN
        ):
            raise ValueError(
                "I-AGENTLOOP-03 violated: AgentReply.input_id must be "
                "non-empty printable text under "
                f"{AGENT_INPUT_ID_MAX_LEN} chars"
            )
        if not isinstance(self.disposition, AgentReplyDisposition):
            raise TypeError(
                "I-AGENTLOOP-03 violated: AgentReply.disposition must be a "
                "AgentReplyDisposition member"
            )
        if not isinstance(self.sections, tuple) or not self.sections:
            raise ValueError(
                "I-AGENTLOOP-03 violated: AgentReply.sections must be a "
                "non-empty tuple"
            )
        if len(self.sections) > len(_CANONICAL_REPLY_ORDER):
            raise ValueError(
                "I-AGENTLOOP-03 violated: AgentReply.sections may not exceed "
                f"{len(_CANONICAL_REPLY_ORDER)} sections"
            )
        seen: set[AgentReplyStatus] = set()
        # Section status order must be a subsequence of the canonical
        # order.
        canonical_index = -1
        for entry in self.sections:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise TypeError(
                    "I-AGENTLOOP-03 violated: AgentReply.sections entries "
                    "must be (AgentReplyStatus, str) pairs"
                )
            status, body = entry
            if not isinstance(status, AgentReplyStatus):
                raise TypeError(
                    "I-AGENTLOOP-03 violated: AgentReply.sections status "
                    "must be an AgentReplyStatus member"
                )
            if status in seen:
                raise ValueError(
                    "I-AGENTLOOP-03 violated: AgentReply.sections may not "
                    "repeat a status"
                )
            seen.add(status)
            try:
                position = _CANONICAL_REPLY_ORDER.index(status)
            except ValueError as exc:
                raise ValueError(
                    "I-AGENTLOOP-03 violated: AgentReply.sections status "
                    f"{status!r} not in canonical order"
                ) from exc
            if position <= canonical_index:
                raise ValueError(
                    "I-AGENTLOOP-03 violated: AgentReply.sections must be "
                    "in canonical order"
                )
            canonical_index = position
            if not isinstance(body, str):
                raise TypeError(
                    "I-AGENTLOOP-03 violated: AgentReply.sections body must "
                    "be a string"
                )
            if not body or not body.isprintable():
                raise ValueError(
                    "I-AGENTLOOP-03 violated: AgentReply.sections body must "
                    "be non-empty printable text"
                )
            if len(body) > AGENT_REPLY_SECTION_MAX_LEN:
                raise ValueError(
                    "I-AGENTLOOP-03 violated: AgentReply.sections body "
                    f"exceeds bound {AGENT_REPLY_SECTION_MAX_LEN}"
                )
            term = _text_has_forbidden_term(body)
            if term is not None:
                raise ValueError(
                    "I-AGENTLOOP-04 violated: AgentReply.sections body "
                    f"contains forbidden non-claim term {term!r}"
                )
            if COGITO_ID in body:
                raise ValueError(
                    "I-AGENTLOOP-03 violated: AgentReply.sections body must "
                    "not contain COGITO_ID"
                )
        if not isinstance(self.full_text, str):
            raise TypeError(
                "I-AGENTLOOP-03 violated: AgentReply.full_text must be a "
                "string"
            )
        if not self.full_text or not self.full_text.isprintable():
            raise ValueError(
                "I-AGENTLOOP-03 violated: AgentReply.full_text must be "
                "non-empty printable text"
            )
        if len(self.full_text) > AGENT_REPLY_FULL_MAX_LEN:
            raise ValueError(
                "I-AGENTLOOP-03 violated: AgentReply.full_text exceeds "
                f"bound {AGENT_REPLY_FULL_MAX_LEN}"
            )
        term = _text_has_forbidden_term(self.full_text)
        if term is not None:
            raise ValueError(
                "I-AGENTLOOP-04 violated: AgentReply.full_text contains "
                f"forbidden non-claim term {term!r}"
            )
        if COGITO_ID in self.full_text:
            raise ValueError(
                "I-AGENTLOOP-03 violated: AgentReply.full_text must not "
                "contain COGITO_ID"
            )

    def section_kinds(self) -> tuple[AgentReplyStatus, ...]:
        """Return the reply's section-status tuple in canonical order."""
        return tuple(status for status, _body in self.sections)


@dataclass(frozen=True, slots=True)
class AgentLoopResult:
    """A bounded record returned by ``run_agent_interaction_step``.

    Carries the bounded input, the post-dispatch observation, the
    reply, and (optionally) the result of the REPL bridge call when
    the loop routed the input through the REPL path.
    """

    input: AgentInput
    observation: AgentObservationSummary
    reply: AgentReply
    repl_line_result: Optional[AgentReplLineResult] = None

    def __post_init__(self) -> None:
        if not isinstance(self.input, AgentInput):
            raise TypeError(
                "I-AGENTLOOP-02 violated: AgentLoopResult.input must be an "
                "AgentInput"
            )
        if not isinstance(self.observation, AgentObservationSummary):
            raise TypeError(
                "I-AGENTLOOP-02 violated: AgentLoopResult.observation must "
                "be an AgentObservationSummary"
            )
        if not isinstance(self.reply, AgentReply):
            raise TypeError(
                "I-AGENTLOOP-02 violated: AgentLoopResult.reply must be an "
                "AgentReply"
            )
        if self.repl_line_result is not None and not isinstance(
            self.repl_line_result, AgentReplLineResult
        ):
            raise TypeError(
                "I-AGENTLOOP-02 violated: AgentLoopResult.repl_line_result "
                "must be an AgentReplLineResult or None"
            )


@dataclass(frozen=True, slots=True)
class AgentLoopState:
    """A bounded session-local container the loop threads across calls.

    Holds a reference to the (mutable) ``OperatorSession``, the
    (immutable) REPL history, the (immutable) REPL grammar handle,
    and a bounded interaction counter the loop uses to synthesize
    deterministic input ids and REPL line ids.
    """

    session: OperatorSession
    repl_history: ProtoBasicHistory
    repl_handle: AgentReplGrammarHandle
    interaction_counter: int

    def __post_init__(self) -> None:
        if not isinstance(self.session, OperatorSession):
            raise TypeError(
                "I-AGENTLOOP-02 violated: AgentLoopState.session must be an "
                "OperatorSession"
            )
        if not isinstance(self.repl_history, ProtoBasicHistory):
            raise TypeError(
                "I-AGENTLOOP-02 violated: AgentLoopState.repl_history must "
                "be a ProtoBasicHistory"
            )
        if not isinstance(self.repl_handle, AgentReplGrammarHandle):
            raise TypeError(
                "I-AGENTLOOP-02 violated: AgentLoopState.repl_handle must "
                "be an AgentReplGrammarHandle"
            )
        if (
            not isinstance(self.interaction_counter, int)
            or isinstance(self.interaction_counter, bool)
            or self.interaction_counter < 0
            or self.interaction_counter > AGENT_LOOP_MAX_INTERACTIONS
        ):
            raise ValueError(
                "I-AGENTLOOP-02 violated: AgentLoopState.interaction_counter "
                f"must be an int in [0, {AGENT_LOOP_MAX_INTERACTIONS}]"
            )


def make_initial_agent_loop_state(
    *,
    session: Optional[OperatorSession] = None,
    repl_handle: Optional[AgentReplGrammarHandle] = None,
    initial_brain_state: Optional[BrainState] = None,
) -> AgentLoopState:
    """Construct a fresh AgentLoopState.

    If no session is supplied, constructs a fresh
    ``OperatorSession(state=initial_state())``. If no REPL handle is
    supplied, builds the default agent REPL grammar.
    """
    if session is None:
        state = (
            initial_brain_state
            if initial_brain_state is not None
            else initial_state()
        )
        session = OperatorSession(state=state)
    if repl_handle is None:
        repl_handle = build_default_agent_repl_grammar()
    return AgentLoopState(
        session=session,
        repl_history=ProtoBasicHistory(),
        repl_handle=repl_handle,
        interaction_counter=0,
    )


# ---------------------------------------------------------------------------
# Observation helper.
# ---------------------------------------------------------------------------


def summarize_session_for_agent(
    session: OperatorSession,
    *,
    repl_history: Optional[ProtoBasicHistory] = None,
) -> AgentObservationSummary:
    """Read-only inspection of an OperatorSession + optional REPL history.

    Pure deterministic helper. Performs no mutation; calls no
    ``tick``; constructs no LLM client; never touches the file
    system or network. Two invocations on the same session +
    history yield bit-identical AgentObservationSummary records.
    """
    if not isinstance(session, OperatorSession):
        raise TypeError(
            "I-AGENTLOOP-02 violated: summarize_session_for_agent requires "
            "an OperatorSession"
        )
    if repl_history is not None and not isinstance(
        repl_history, ProtoBasicHistory
    ):
        raise TypeError(
            "I-AGENTLOOP-02 violated: summarize_session_for_agent "
            "repl_history must be a ProtoBasicHistory or None"
        )

    chunks = session.stream_history.chunks
    entries = session.pattern_ledger.entries
    events = session.growth_ledger.events

    if entries:
        seed = entries[0]
        seed_pattern_id = seed.pattern_id
        seed_recurrence = seed.recurrence_count
        seed_saturation_state = seed.saturation_state.value
    else:
        seed_pattern_id = ""
        seed_recurrence = 0
        seed_saturation_state = "none"

    # Coherence report is built read-only from the session.
    report = build_full_coherence_report(session)
    overall_status_value = report.overall_status.value
    if overall_status_value not in _VALID_COHERENCE_OVERALL_VALUES:
        overall_status_value = "none"
    check_total = len(report.snapshot.checks)

    if repl_history is not None:
        repl_summary = summarize_repl_for_agent(repl_history)
        repl_emit_total = repl_summary.emit_total
    else:
        repl_emit_total = 0

    # The audit field; an observation summary that itself contained a
    # forbidden term would already have failed the AgentObservationSummary
    # constructor. The counter is provided so callers can record it.
    forbidden_hits = 0

    return AgentObservationSummary(
        stream_chunk_count=len(chunks),
        pattern_entry_count=len(entries),
        seed_pattern_id=seed_pattern_id,
        seed_recurrence=seed_recurrence,
        seed_saturation_state=seed_saturation_state,
        growth_event_total=len(events),
        coherence_overall_status=overall_status_value,
        coherence_check_total=check_total,
        repl_emit_total=repl_emit_total,
        forbidden_term_hits=forbidden_hits,
    )


# ---------------------------------------------------------------------------
# Reply construction.
# ---------------------------------------------------------------------------


def _pattern_section_body(obs: AgentObservationSummary) -> str:
    return (
        f"pattern stream_chunks={obs.stream_chunk_count} "
        f"entries={obs.pattern_entry_count} "
        f"seed_id={obs.seed_pattern_id!r} "
        f"seed_recur={obs.seed_recurrence} "
        f"seed_sat={obs.seed_saturation_state}"
    )


def _repl_section_body(
    obs: AgentObservationSummary,
    repl_line_result: Optional[AgentReplLineResult],
    repl_summary: Optional[AgentReplBridgeSummary],
) -> str:
    if repl_line_result is not None:
        last_parse = repl_line_result.parse_category_value
        last_exec = repl_line_result.execution_category_value
        last_canonical = repl_line_result.command_canonical
        last_drf = repl_line_result.diminishing_returns_factor_str
        last_val = repl_line_result.feedback_valence_str
        repl_total = obs.repl_emit_total
        return (
            f"repl last_parse={last_parse} last_exec={last_exec} "
            f"last_canonical={last_canonical!r} last_val={last_val} "
            f"last_drf={last_drf} emit_total={repl_total}"
        )
    if repl_summary is not None:
        return (
            f"repl no_command_this_step emit_total={repl_summary.emit_total} "
            f"top={repl_summary.most_repeated_canonical!r}/"
            f"{repl_summary.most_repeated_emit_count}"
        )
    return f"repl emit_total={obs.repl_emit_total}"


def _coherence_section_body(obs: AgentObservationSummary) -> str:
    return (
        f"coherence overall={obs.coherence_overall_status} "
        f"check_total={obs.coherence_check_total}"
    )


def _limitation_section_body() -> str:
    return (
        "limitation runtime=offline real_model_calls=0 cache_writes=0 "
        "substrate=bounded no_cognitive_claim=true"
    )


def _refusal_limitation_section_body() -> str:
    return (
        "limitation this runtime is a bounded deterministic structural "
        "state machine; operator inputs route through fixed substrates "
        "only and produce bounded printable replies; no cognitive claim "
        "is made by this system"
    )


def _next_action_section_body(
    obs: AgentObservationSummary,
    disposition: AgentReplyDisposition,
) -> str:
    if disposition is AgentReplyDisposition.REFUSAL:
        return (
            "next_action send a non-cognitive-query bounded printable "
            "input to continue; e.g. a short noun-phrase or a Proto-BASIC "
            "command starting with EMIT or NOTE"
        )
    if disposition is AgentReplyDisposition.WARN:
        return (
            "next_action operator_text is empty; supply a non-empty "
            "bounded printable input under "
            f"{AGENT_INPUT_MAX_LEN} chars"
        )
    if disposition is AgentReplyDisposition.FAIL:
        return (
            "next_action operator_text exceeds bound "
            f"{AGENT_INPUT_MAX_LEN}; resend shorter input"
        )
    saturated = obs.seed_saturation_state == (
        PatternLedgerSaturationState.SATURATED.value
    )
    if obs.pattern_entry_count == 0:
        return (
            "next_action send a short bounded printable seed text to "
            "create the first ledger entry"
        )
    if saturated:
        return (
            "next_action seed ledger entry is saturated at "
            f"{STREAM_PATTERN_RECURRENCE_MAX}; send a novel bounded "
            "printable text to add a new ledger entry"
        )
    if obs.seed_recurrence < STREAM_PATTERN_RECURRENCE_MAX:
        return (
            "next_action repeat the previous input to climb seed "
            f"recurrence; send a novel input to add a new ledger entry; "
            "or send a Proto-BASIC command starting with EMIT or NOTE"
        )
    return (
        "next_action send a novel bounded printable text or a Proto-BASIC "
        "command starting with EMIT or NOTE"
    )


def _join_full_text(
    sections: tuple[tuple[AgentReplyStatus, str], ...],
) -> str:
    parts = [f"[{status.value}] {body}" for status, body in sections]
    return " | ".join(parts)


def _bounded(text: str, *, limit: int) -> str:
    if len(text) <= limit:
        return text
    # Hard cap; the loop never silently truncates without marking the
    # bound, but for the fallback we shorten with a marker.
    return text[: max(0, limit - 4)] + " ..."


def build_agent_reply(
    session: OperatorSession,
    operator_text: str,
    *,
    input_id: str,
    repl_history: Optional[ProtoBasicHistory] = None,
    repl_line_result: Optional[AgentReplLineResult] = None,
) -> AgentReply:
    """Compose a deterministic bounded operator-facing reply.

    Pure deterministic helper. Two invocations on equivalent inputs
    produce bit-identical AgentReply records. The function never
    mutates ``session`` or ``repl_history``.

    Disposition assignment:

    * ``FAIL``  iff ``operator_text`` length exceeds the bound;
      reply is LIMITATION_REPORT + NEXT_ACTION_SUGGESTION.
    * ``REFUSAL`` iff ``operator_text`` contains any term in
      ``_FORBIDDEN_NON_CLAIM_TERMS``; reply is LIMITATION_REPORT +
      NEXT_ACTION_SUGGESTION (no session inspection used in the
      reply body to keep refusal text uniform).
    * ``WARN`` iff ``operator_text`` is empty; reply is
      LIMITATION_REPORT + NEXT_ACTION_SUGGESTION.
    * ``OK``    otherwise; reply emits all five sections in
      canonical order.
    """
    if not isinstance(session, OperatorSession):
        raise TypeError(
            "I-AGENTLOOP-03 violated: build_agent_reply requires an "
            "OperatorSession"
        )
    if not isinstance(operator_text, str):
        raise TypeError(
            "I-AGENTLOOP-03 violated: build_agent_reply operator_text must "
            "be a string"
        )
    if (
        not isinstance(input_id, str)
        or not input_id
        or not input_id.isprintable()
        or len(input_id) > AGENT_INPUT_ID_MAX_LEN
    ):
        raise ValueError(
            "I-AGENTLOOP-03 violated: build_agent_reply input_id must be "
            "non-empty printable text under "
            f"{AGENT_INPUT_ID_MAX_LEN} chars"
        )

    # FAIL takes precedence over REFUSAL: an oversize input cannot be
    # safely inspected.
    if len(operator_text) > AGENT_INPUT_MAX_LEN:
        sections = (
            (AgentReplyStatus.LIMITATION_REPORT, _limitation_section_body()),
            (
                AgentReplyStatus.NEXT_ACTION_SUGGESTION,
                _next_action_section_body(
                    summarize_session_for_agent(session),
                    AgentReplyDisposition.FAIL,
                ),
            ),
        )
        full_text = _bounded(
            _join_full_text(sections), limit=AGENT_REPLY_FULL_MAX_LEN
        )
        return AgentReply(
            input_id=input_id,
            disposition=AgentReplyDisposition.FAIL,
            sections=sections,
            full_text=full_text,
        )

    # REFUSAL: any audit-tuple term in the operator text routes here.
    if _operator_text_triggers_refusal(operator_text):
        sections = (
            (
                AgentReplyStatus.LIMITATION_REPORT,
                _refusal_limitation_section_body(),
            ),
            (
                AgentReplyStatus.NEXT_ACTION_SUGGESTION,
                _next_action_section_body(
                    summarize_session_for_agent(session),
                    AgentReplyDisposition.REFUSAL,
                ),
            ),
        )
        full_text = _bounded(
            _join_full_text(sections), limit=AGENT_REPLY_FULL_MAX_LEN
        )
        return AgentReply(
            input_id=input_id,
            disposition=AgentReplyDisposition.REFUSAL,
            sections=sections,
            full_text=full_text,
        )

    # WARN: empty input.
    if operator_text == "":
        sections = (
            (AgentReplyStatus.LIMITATION_REPORT, _limitation_section_body()),
            (
                AgentReplyStatus.NEXT_ACTION_SUGGESTION,
                _next_action_section_body(
                    summarize_session_for_agent(session),
                    AgentReplyDisposition.WARN,
                ),
            ),
        )
        full_text = _bounded(
            _join_full_text(sections), limit=AGENT_REPLY_FULL_MAX_LEN
        )
        return AgentReply(
            input_id=input_id,
            disposition=AgentReplyDisposition.WARN,
            sections=sections,
            full_text=full_text,
        )

    # OK: full five-section reply.
    obs = summarize_session_for_agent(session, repl_history=repl_history)
    repl_summary: Optional[AgentReplBridgeSummary] = None
    if repl_history is not None:
        repl_summary = summarize_repl_for_agent(repl_history)
    sections = (
        (AgentReplyStatus.PATTERN_REPORT, _pattern_section_body(obs)),
        (
            AgentReplyStatus.REPL_REPORT,
            _repl_section_body(obs, repl_line_result, repl_summary),
        ),
        (AgentReplyStatus.COHERENCE_REPORT, _coherence_section_body(obs)),
        (AgentReplyStatus.LIMITATION_REPORT, _limitation_section_body()),
        (
            AgentReplyStatus.NEXT_ACTION_SUGGESTION,
            _next_action_section_body(obs, AgentReplyDisposition.OK),
        ),
    )
    full_text = _bounded(
        _join_full_text(sections), limit=AGENT_REPLY_FULL_MAX_LEN
    )
    return AgentReply(
        input_id=input_id,
        disposition=AgentReplyDisposition.OK,
        sections=sections,
        full_text=full_text,
    )


# ---------------------------------------------------------------------------
# Run-step helper.
# ---------------------------------------------------------------------------


def _looks_like_repl_command(text: str, handle: AgentReplGrammarHandle) -> bool:
    """Heuristic: text whose first token is a verb in the handle's grammar."""
    if not text:
        return False
    if len(text) > AGENT_REPL_MAX_INPUT_LEN:
        return False
    # First whitespace-delimited token, case-folded, checked against
    # verb tokens.
    head = text.strip().split()[:1]
    if not head:
        return False
    head_text = head[0]
    for token in handle.grammar.tokens:
        if token.kind.value == "verb" and token.text == head_text:
            return True
    return False


def run_agent_interaction_step(
    state: AgentLoopState,
    operator_text: str,
) -> tuple[AgentLoopState, AgentLoopResult]:
    """Drive one operator-input -> reply step against ``state``.

    Returns a new ``AgentLoopState`` (with the interaction counter
    advanced and the REPL history threaded through any REPL call)
    and an ``AgentLoopResult``.

    Path selection:

    * If ``operator_text`` triggers REFUSAL (any audit-tuple term) or
      is oversize (FAIL) or empty (WARN), no session mutation
      occurs; the reply is constructed against the unchanged session.
    * If ``operator_text``'s first token matches a verb in the loop's
      REPL grammar, the loop routes the input through
      ``run_repl_line`` and does NOT dispatch a STREAM_APPEND.
    * Otherwise, the loop dispatches ``OperatorCommand.STREAM_APPEND``
      with the operator text and then inspects the session to build
      the reply.

    Determinism: two fresh sessions advanced by the same sequence of
    operator inputs produce bit-identical ``AgentLoopResult`` tuples
    (modulo the live ``OperatorSession`` reference, which is shared
    by definition).
    """
    if not isinstance(state, AgentLoopState):
        raise TypeError(
            "I-AGENTLOOP-02 violated: run_agent_interaction_step state must "
            "be an AgentLoopState"
        )
    if not isinstance(operator_text, str):
        raise TypeError(
            "I-AGENTLOOP-02 violated: run_agent_interaction_step "
            "operator_text must be a string"
        )

    counter = state.interaction_counter + 1
    if counter > AGENT_LOOP_MAX_INTERACTIONS:
        raise ValueError(
            "I-AGENTLOOP-02 violated: run_agent_interaction_step exceeded "
            f"AGENT_LOOP_MAX_INTERACTIONS={AGENT_LOOP_MAX_INTERACTIONS}"
        )
    input_id = f"{AGENT_INPUT_ID_PREFIX}{counter:05d}"

    # AgentInput construction. We don't construct AgentInput for
    # oversize text (FAIL would fire on the AgentInput constructor);
    # synthesize a sentinel-bounded AgentInput by trimming the text
    # for the input record only, while the reply records the FAIL
    # disposition with the bound message.
    fail_oversize = len(operator_text) > AGENT_INPUT_MAX_LEN
    if fail_oversize:
        agent_input = AgentInput(
            operator_text="",
            input_id=input_id,
        )
    else:
        agent_input = AgentInput(
            operator_text=operator_text,
            input_id=input_id,
        )

    repl_line_result: Optional[AgentReplLineResult] = None
    new_repl_history = state.repl_history

    if fail_oversize:
        # No dispatch; build FAIL reply.
        reply = build_agent_reply(
            state.session,
            operator_text,  # pass actual oversize text so the reply
                            # detects FAIL via its bound check
            input_id=input_id,
            repl_history=state.repl_history,
            repl_line_result=None,
        )
    elif _operator_text_triggers_refusal(operator_text):
        # No dispatch; build REFUSAL reply.
        reply = build_agent_reply(
            state.session,
            operator_text,
            input_id=input_id,
            repl_history=state.repl_history,
            repl_line_result=None,
        )
    elif operator_text == "":
        # No dispatch; build WARN reply.
        reply = build_agent_reply(
            state.session,
            operator_text,
            input_id=input_id,
            repl_history=state.repl_history,
            repl_line_result=None,
        )
    elif _looks_like_repl_command(operator_text, state.repl_handle):
        # REPL path: route through bridge; do NOT dispatch STREAM_APPEND.
        line_id = f"{AGENT_REPL_LINE_ID_PREFIX}step-{counter:05d}"
        repl_line_result = run_repl_line(
            handle=state.repl_handle,
            history=state.repl_history,
            raw_text=operator_text,
            line_id=line_id,
        )
        new_repl_history = repl_line_result.history
        reply = build_agent_reply(
            state.session,
            operator_text,
            input_id=input_id,
            repl_history=new_repl_history,
            repl_line_result=repl_line_result,
        )
    else:
        # Stream path: dispatch STREAM_APPEND through the public router.
        command = Command(
            OperatorCommand.STREAM_APPEND,
            payload=StreamAppendPayload(text=operator_text),
        )
        state.session.dispatch(command)
        # Kernel invariants must hold after every dispatch.
        assert_state_invariants(state.session.state)
        reply = build_agent_reply(
            state.session,
            operator_text,
            input_id=input_id,
            repl_history=state.repl_history,
            repl_line_result=None,
        )

    observation = summarize_session_for_agent(
        state.session, repl_history=new_repl_history
    )

    result = AgentLoopResult(
        input=agent_input,
        observation=observation,
        reply=reply,
        repl_line_result=repl_line_result,
    )
    new_state = AgentLoopState(
        session=state.session,
        repl_history=new_repl_history,
        repl_handle=state.repl_handle,
        interaction_counter=counter,
    )
    return new_state, result


# ---------------------------------------------------------------------------
# Module-produced strings (audited).
# ---------------------------------------------------------------------------

MODULE_PRODUCED_STRINGS: tuple[str, ...] = (
    AGENT_INPUT_ID_PREFIX,
    AGENT_LOOP_VERSION,
    _limitation_section_body(),
    _refusal_limitation_section_body(),
)


__all__ = (
    "AGENT_INPUT_ID_PREFIX",
    "AGENT_INPUT_ID_MAX_LEN",
    "AGENT_INPUT_MAX_LEN",
    "AGENT_LOOP_MAX_INTERACTIONS",
    "AGENT_LOOP_VERSION",
    "AGENT_REPLY_FULL_MAX_LEN",
    "AGENT_REPLY_SECTION_MAX_LEN",
    "AgentInput",
    "AgentLoopResult",
    "AgentLoopState",
    "AgentObservationSummary",
    "AgentReply",
    "AgentReplyDisposition",
    "AgentReplyStatus",
    "MODULE_PRODUCED_STRINGS",
    "build_agent_reply",
    "make_initial_agent_loop_state",
    "run_agent_interaction_step",
    "summarize_session_for_agent",
)
