"""Phase 3.22 Agent loop static audit fixture.

Drives ``I-AGENTLOOP-10`` (STRUCTURAL). Audits
``brain.development.agent_loop`` and
``brain.development.agent_repl_bridge`` for:

* closed enum membership of ``AgentReplyStatus`` and
  ``AgentReplyDisposition``;
* ``__slots__`` of every frozen / slotted record matches the
  declared shape;
* ``MODULE_PRODUCED_STRINGS`` audit on both modules
  (bounded printable, no forbidden non-claim term);
* the agent_loop module source contains no forbidden non-claim
  term literal;
* the agent_repl_bridge module source contains no forbidden
  non-claim term literal;
* no forbidden import appears in either module source
  (no ``brain.llm`` import, no ``brain.tick.tick`` import, no
  ``curses``, ``subprocess``, ``socket``, ``urllib``, ``http``,
  ``requests``, ``pathlib``, ``tempfile``, ``shutil``,
  ``threading``, ``asyncio``, ``atexit``, ``signal``,
  ``importlib``, ``time``, ``random``, ``hashlib``, ``math``).

No real model calls. No tick invocation.
"""
from __future__ import annotations

import inspect

from brain.development import agent_loop as _AGENT_LOOP_MODULE
from brain.development import agent_repl_bridge as _AGENT_REPL_BRIDGE_MODULE
from brain.development.agent_loop import (
    AgentInput,
    AgentLoopResult,
    AgentLoopState,
    AgentObservationSummary,
    AgentReply,
    AgentReplyDisposition,
    AgentReplyStatus,
    MODULE_PRODUCED_STRINGS as AGENT_LOOP_MODULE_PRODUCED,
)
from brain.development.agent_repl_bridge import (
    AgentReplBridgeSummary,
    AgentReplGrammarHandle,
    AgentReplLineResult,
    MODULE_PRODUCED_STRINGS as AGENT_REPL_BRIDGE_MODULE_PRODUCED,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.invariants import register


_EXPECTED_REPLY_STATUS_VALUES = frozenset(
    {
        "pattern_report",
        "repl_report",
        "coherence_report",
        "limitation_report",
        "next_action_suggestion",
    }
)


_EXPECTED_REPLY_DISPOSITION_VALUES = frozenset(
    {"ok", "refusal", "warn", "fail"}
)


_EXPECTED_FORBIDDEN_IMPORT_FRAGMENTS = (
    "import brain.llm",
    "from brain.llm",
    "from brain.tick import tick",
    "from brain.tick import (tick",
    "import curses",
    "import subprocess",
    "import socket",
    "import urllib",
    "import http",
    "import requests",
    "import tempfile",
    "import shutil",
    "import threading",
    "import asyncio",
    "import atexit",
    "import signal",
    "import importlib",
    "import time",
    "import random",
    "import hashlib",
    "import math",
)


def _has_forbidden_term(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


def _audit_module_source(module) -> None:
    src = inspect.getsource(module)
    term = _has_forbidden_term(src)
    assert term is None, (
        "I-AGENTLOOP-10 violated: module "
        f"{module.__name__} source contains forbidden non-claim "
        f"term {term!r}"
    )
    lowered = src.lower()
    for fragment in _EXPECTED_FORBIDDEN_IMPORT_FRAGMENTS:
        assert fragment not in lowered, (
            "I-AGENTLOOP-10 violated: module "
            f"{module.__name__} source contains forbidden import "
            f"fragment {fragment!r}"
        )


@register("I-AGENTLOOP-10", status="STRUCTURAL")
def check_agent_loop_static_audit() -> None:
    """Static audit on agent_loop.py and agent_repl_bridge.py."""

    # 1. AgentReplyStatus enum membership.
    assert issubclass(AgentReplyStatus, str)
    actual = frozenset(s.value for s in AgentReplyStatus)
    assert actual == _EXPECTED_REPLY_STATUS_VALUES, (
        "I-AGENTLOOP-10 violated: AgentReplyStatus value set drifted "
        f"(got {sorted(actual)!r}, expected "
        f"{sorted(_EXPECTED_REPLY_STATUS_VALUES)!r})"
    )

    # 2. AgentReplyDisposition enum membership.
    assert issubclass(AgentReplyDisposition, str)
    actual = frozenset(d.value for d in AgentReplyDisposition)
    assert actual == _EXPECTED_REPLY_DISPOSITION_VALUES, (
        "I-AGENTLOOP-10 violated: AgentReplyDisposition value set drifted "
        f"(got {sorted(actual)!r}, expected "
        f"{sorted(_EXPECTED_REPLY_DISPOSITION_VALUES)!r})"
    )

    # 3. Slot shape of every frozen / slotted record.
    expected_slots = {
        AgentInput: ("operator_text", "input_id"),
        AgentObservationSummary: (
            "stream_chunk_count",
            "pattern_entry_count",
            "seed_pattern_id",
            "seed_recurrence",
            "seed_saturation_state",
            "growth_event_total",
            "coherence_overall_status",
            "coherence_check_total",
            "repl_emit_total",
            "forbidden_term_hits",
        ),
        AgentReply: (
            "input_id",
            "disposition",
            "sections",
            "full_text",
        ),
        AgentLoopResult: (
            "input",
            "observation",
            "reply",
            "repl_line_result",
            "learning_evidence_trace",
            "reasoning_trace",
        ),
        AgentLoopState: (
            "session",
            "repl_history",
            "repl_handle",
            "interaction_counter",
            "learning_trace",
        ),
        AgentReplGrammarHandle: ("grammar", "handle_id"),
        AgentReplLineResult: (
            "line_id",
            "parse_category_value",
            "command_canonical",
            "execution_category_value",
            "effective",
            "feedback_valence_str",
            "feedback_is_strong_positive",
            "near_miss_hint_summary",
            "diminishing_returns_factor_str",
            "history",
        ),
        AgentReplBridgeSummary: (
            "parse_valid_count",
            "parse_near_miss_count",
            "parse_syntax_invalid_count",
            "execution_valid_effective_count",
            "execution_valid_ineffective_count",
            "emit_total",
            "most_repeated_canonical",
            "most_repeated_emit_count",
            "summary_line",
        ),
    }
    for cls, expected in expected_slots.items():
        assert cls.__slots__ == expected, (
            "I-AGENTLOOP-10 violated: "
            f"{cls.__name__}.__slots__ drifted "
            f"(got {cls.__slots__!r}, expected {expected!r})"
        )

    # 4. MODULE_PRODUCED_STRINGS audit on both modules.
    for produced in AGENT_LOOP_MODULE_PRODUCED:
        assert isinstance(produced, str) and produced.isprintable()
        term = _has_forbidden_term(produced)
        assert term is None, (
            "I-AGENTLOOP-10 violated: agent_loop MODULE_PRODUCED_STRINGS "
            f"entry {produced!r} contains forbidden term {term!r}"
        )
    for produced in AGENT_REPL_BRIDGE_MODULE_PRODUCED:
        assert isinstance(produced, str) and produced.isprintable()
        term = _has_forbidden_term(produced)
        assert term is None, (
            "I-AGENTLOOP-10 violated: agent_repl_bridge "
            f"MODULE_PRODUCED_STRINGS entry {produced!r} contains "
            f"forbidden term {term!r}"
        )

    # 5. Module source audit on both modules.
    _audit_module_source(_AGENT_LOOP_MODULE)
    _audit_module_source(_AGENT_REPL_BRIDGE_MODULE)
