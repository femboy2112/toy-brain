"""Phase 3.24 worldlet feedback static audit fixture.

Drives ``I-WFDBK-12`` (STRUCTURAL). Audits the Phase 3.24 additions
to ``brain/development/processing_window.py`` for closed-set
discipline, bounded printability, non-claim cleanliness, and
import discipline.
"""
from __future__ import annotations

import inspect

from brain.development import processing_window as _pw_module
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.processing_window import (
    MODULE_PRODUCED_STRINGS,
    WORLDLET_SUMMARY_ABSENT_SENTINEL,
    WORLDLET_SUMMARY_TEXT_MAX_LEN,
    WORLDLET_SUMMARY_TEXT_PREFIX,
    build_worldlet_summary_text,
)
from brain.invariants import register
from brain.tlica.profile import COGITO_ID


_EXPECTED_VALID_LAST_REASONS = frozenset(
    {"accepted", "missing-target", "rejected", "target-unavailable", "absent"}
)


_FORBIDDEN_IMPORT_FRAGMENTS = (
    "import brain.llm",
    "from brain.llm",
    "from brain.tick import tick",
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
    "import os",
    "from brain.development.worldlet",
    "import brain.development.worldlet",
)


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


_REPRESENTATIVE_INPUTS = (
    dict(
        state_id_value="absent",
        step_index=0,
        object_count=0,
        attempt_count=0,
        response_count=0,
        accepted_count=0,
        pushback_count=0,
        last_reason_value="absent",
    ),
    dict(
        state_id_value="wld:state:abcdef0123456789",
        step_index=255,
        object_count=2,
        attempt_count=8,
        response_count=8,
        accepted_count=4,
        pushback_count=4,
        last_reason_value="rejected",
    ),
    dict(
        state_id_value="wld:state:ffffffffffffffff",
        step_index=65535,
        object_count=256,
        attempt_count=256,
        response_count=256,
        accepted_count=128,
        pushback_count=128,
        last_reason_value="target-unavailable",
    ),
)


@register("I-WFDBK-12", status="STRUCTURAL")
def check_worldlet_feedback_static_audit() -> None:
    """Static audit on the Phase 3.24 processing_window additions."""

    # 1. Constants.
    assert WORLDLET_SUMMARY_TEXT_PREFIX == "worldlet_summary", (
        f"I-WFDBK-12 violated: WORLDLET_SUMMARY_TEXT_PREFIX drifted "
        f"({WORLDLET_SUMMARY_TEXT_PREFIX!r})"
    )
    assert WORLDLET_SUMMARY_TEXT_MAX_LEN == 240, (
        f"I-WFDBK-12 violated: WORLDLET_SUMMARY_TEXT_MAX_LEN drifted "
        f"({WORLDLET_SUMMARY_TEXT_MAX_LEN!r})"
    )
    assert WORLDLET_SUMMARY_ABSENT_SENTINEL == "absent", (
        f"I-WFDBK-12 violated: WORLDLET_SUMMARY_ABSENT_SENTINEL drifted "
        f"({WORLDLET_SUMMARY_ABSENT_SENTINEL!r})"
    )

    # 2. Closed set _WORLDLET_SUMMARY_VALID_LAST_REASONS.
    actual_reasons = _pw_module._WORLDLET_SUMMARY_VALID_LAST_REASONS
    assert actual_reasons == _EXPECTED_VALID_LAST_REASONS, (
        f"I-WFDBK-12 violated: _WORLDLET_SUMMARY_VALID_LAST_REASONS drifted "
        f"(got {sorted(actual_reasons)!r}, expected "
        f"{sorted(_EXPECTED_VALID_LAST_REASONS)!r})"
    )

    # 3. MODULE_PRODUCED_STRINGS contains every new Phase 3.24 string and
    # is non-claim-clean.
    must_have = {
        WORLDLET_SUMMARY_TEXT_PREFIX,
        WORLDLET_SUMMARY_ABSENT_SENTINEL,
        "worldlet_summary",
        "worldlet",
        "pattern_coherence_worldlet",
    }
    actual_strings = set(MODULE_PRODUCED_STRINGS)
    missing = must_have - actual_strings
    assert not missing, (
        f"I-WFDBK-12 violated: MODULE_PRODUCED_STRINGS missing entries "
        f"{sorted(missing)!r}"
    )
    for produced in MODULE_PRODUCED_STRINGS:
        term = _has_forbidden(produced)
        assert term is None, (
            f"I-WFDBK-12 violated: MODULE_PRODUCED_STRINGS entry "
            f"{produced!r} contains forbidden non-claim term {term!r}"
        )

    # 4. Helper outputs over representative inputs.
    for kwargs in _REPRESENTATIVE_INPUTS:
        text = build_worldlet_summary_text(**kwargs)
        assert text.startswith(WORLDLET_SUMMARY_TEXT_PREFIX + " ")
        assert text.isprintable()
        assert len(text) <= WORLDLET_SUMMARY_TEXT_MAX_LEN
        assert COGITO_ID not in text
        term = _has_forbidden(text)
        assert term is None, (
            f"I-WFDBK-12 violated: helper output {text!r} contains "
            f"forbidden non-claim term {term!r}"
        )

    # 5. Module source non-claim-clean.
    src = inspect.getsource(_pw_module)
    term = _has_forbidden(src)
    assert term is None, (
        f"I-WFDBK-12 violated: processing_window source contains forbidden "
        f"non-claim term {term!r}"
    )
    # 6. Module source has no forbidden import fragment.
    lowered = src.lower()
    for fragment in _FORBIDDEN_IMPORT_FRAGMENTS:
        assert fragment not in lowered, (
            f"I-WFDBK-12 violated: processing_window source contains "
            f"forbidden import fragment {fragment!r}"
        )
