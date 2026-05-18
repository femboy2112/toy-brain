"""Phase 3.22 Agent benchmark static audit fixture.

Drives ``I-AGENTLOOP-11`` (STRUCTURAL). Audits
``brain.development.agent_benchmark`` for:

* closed enum membership of ``BenchmarkAxis`` and
  ``BenchmarkCaseStatus``;
* ``__slots__`` of every frozen / slotted record matches the
  declared shape;
* ``MODULE_PRODUCED_STRINGS`` is bounded printable and non-claim-
  clean;
* the module source contains no forbidden non-claim term literal;
* no forbidden import appears in the source (no ``brain.llm``, no
  ``brain.tick.tick``, no curses / subprocess / socket / network).
"""
from __future__ import annotations

import inspect

from brain.development import agent_benchmark as _AGENT_BENCHMARK_MODULE
from brain.development.agent_benchmark import (
    AxisResult,
    BenchmarkAxis,
    BenchmarkCaseResult,
    BenchmarkCaseStatus,
    BenchmarkRun,
    MODULE_PRODUCED_STRINGS,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.invariants import register


_EXPECTED_AXIS_VALUES = frozenset(
    {
        "pattern_recognition",
        "cross_input_structural",
        "coherence_variation",
        "repl_coherence",
        "communication",
        "session_continuity",
        "blind_transcript",
    }
)


_EXPECTED_STATUS_VALUES = frozenset({"pass", "warn", "fail"})


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
)


def _has_forbidden_term(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-AGENTLOOP-11", status="STRUCTURAL")
def check_agent_benchmark_static_audit() -> None:
    """Static audit on agent_benchmark.py."""

    # 1. BenchmarkAxis enum membership.
    assert issubclass(BenchmarkAxis, str)
    actual = frozenset(a.value for a in BenchmarkAxis)
    assert actual == _EXPECTED_AXIS_VALUES, (
        f"I-AGENTLOOP-11 violated: BenchmarkAxis value set drifted "
        f"(got {sorted(actual)!r}, expected "
        f"{sorted(_EXPECTED_AXIS_VALUES)!r})"
    )

    # 2. BenchmarkCaseStatus enum membership.
    assert issubclass(BenchmarkCaseStatus, str)
    actual = frozenset(s.value for s in BenchmarkCaseStatus)
    assert actual == _EXPECTED_STATUS_VALUES, (
        f"I-AGENTLOOP-11 violated: BenchmarkCaseStatus value set drifted "
        f"(got {sorted(actual)!r}, expected "
        f"{sorted(_EXPECTED_STATUS_VALUES)!r})"
    )

    # 3. Slot shape of frozen / slotted records.
    expected_slots = {
        BenchmarkCaseResult: (
            "case_id",
            "axis",
            "status",
            "summary",
            "primary_metric",
            "secondary_metric",
            "notes",
        ),
        AxisResult: ("axis", "status", "cases"),
        BenchmarkRun: (
            "battery_version",
            "axes",
            "case_total",
            "case_passed",
            "case_warned",
            "case_failed",
            "determinism_failures",
            "invariant_failures",
            "real_model_calls",
            "cache_writes",
            "forbidden_term_hits",
            "transcript_digest_hex16",
            "transcripts",
        ),
    }
    for cls, expected in expected_slots.items():
        assert cls.__slots__ == expected, (
            "I-AGENTLOOP-11 violated: "
            f"{cls.__name__}.__slots__ drifted "
            f"(got {cls.__slots__!r}, expected {expected!r})"
        )

    # 4. MODULE_PRODUCED_STRINGS audit.
    for produced in MODULE_PRODUCED_STRINGS:
        assert isinstance(produced, str) and produced.isprintable()
        term = _has_forbidden_term(produced)
        assert term is None, (
            f"I-AGENTLOOP-11 violated: MODULE_PRODUCED_STRINGS entry "
            f"{produced!r} contains forbidden term {term!r}"
        )

    # 5. Module source audit.
    src = inspect.getsource(_AGENT_BENCHMARK_MODULE)
    term = _has_forbidden_term(src)
    assert term is None, (
        "I-AGENTLOOP-11 violated: agent_benchmark.py source contains "
        f"forbidden non-claim term {term!r}"
    )
    lowered = src.lower()
    for fragment in _EXPECTED_FORBIDDEN_IMPORT_FRAGMENTS:
        assert fragment not in lowered, (
            "I-AGENTLOOP-11 violated: agent_benchmark.py source contains "
            f"forbidden import fragment {fragment!r}"
        )
