"""Phase 3.25 osmotic learning probe static audit fixture.

Drives ``I-OSMO-14`` (STRUCTURAL). Audits the new
``brain/development/osmotic_learning_probe.py`` module for closed-set
discipline, bounded printability, non-claim cleanliness, and
import discipline.
"""
from __future__ import annotations

import inspect

from brain.development import osmotic_learning_probe as _osmotic_module
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.osmotic_learning_probe import (
    MODULE_PRODUCED_STRINGS,
    OsmoticCondition,
    OsmoticExposureEvent,
    OsmoticLiveTestReport,
    OsmoticProbeResult,
    OsmoticProbeStatus,
    OsmoticProbeTrial,
)
from brain.invariants import register


_EXPECTED_OSMOTIC_CONDITION_VALUES = frozenset(
    {
        "control_no_exposure",
        "true_exposure",
        "sham_exposure",
        "distractor_interference",
    }
)

_EXPECTED_OSMOTIC_PROBE_STATUS_VALUES = frozenset(
    {"pass", "warn", "fail", "not_applicable"}
)


_FORBIDDEN_IMPORT_FRAGMENTS = (
    "import brain.llm",
    "from brain.llm",
    "from brain.tick import tick",
    "from brain.tick import (tick",
    "import brain.tick",
    "import brain.ui",
    "from brain.ui",
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
    "import os\n",
    "import os.",
    "import pathlib",
    "import math",
    "import time",
    "import random",
    "import importlib",
)


_EXPECTED_SLOTS = {
    OsmoticExposureEvent: (
        "text",
        "interaction_id",
        "abstract_digest_hex16",
        "classification",
        "shape",
    ),
    OsmoticProbeTrial: (
        "trial_id",
        "condition",
        "exposure_texts",
        "probe_text",
        "expected_target_digest",
        "expected_target_shape",
        "expected_prior_acquired",
        "expected_transfer",
    ),
    OsmoticProbeResult: (
        "trial_id",
        "condition",
        "status",
        "exposure_events",
        "probe_digest",
        "probe_shape",
        "probe_classification",
        "prior_acquired_observed",
        "transfer_observed",
        "expected_prior_acquired",
        "expected_transfer",
        "false_positive",
        "false_negative",
        "learning_evidence_digest",
        "reasoning_trace_digest",
        "dispatch_trace_digests",
        "reply_excerpt",
        "summary_line",
    ),
    OsmoticLiveTestReport: (
        "battery_version",
        "trials",
        "pass_count",
        "warn_count",
        "fail_count",
        "not_applicable_count",
        "false_positive_count",
        "false_negative_count",
        "transfer_success_count",
        "real_model_calls",
        "cache_writes",
        "forbidden_term_hits",
        "digest_hex16",
        "summary_line",
    ),
}


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-OSMO-14", status="STRUCTURAL")
def check_osmotic_probe_static_audit() -> None:
    """Static audit on the Phase 3.25 osmotic_learning_probe module."""

    # 1. Closed enum membership.
    assert issubclass(OsmoticCondition, str)
    actual_conditions = frozenset(c.value for c in OsmoticCondition)
    assert actual_conditions == _EXPECTED_OSMOTIC_CONDITION_VALUES, (
        f"I-OSMO-14 violated: OsmoticCondition value set drifted "
        f"(got {sorted(actual_conditions)!r})"
    )
    assert issubclass(OsmoticProbeStatus, str)
    actual_statuses = frozenset(s.value for s in OsmoticProbeStatus)
    assert actual_statuses == _EXPECTED_OSMOTIC_PROBE_STATUS_VALUES, (
        f"I-OSMO-14 violated: OsmoticProbeStatus value set drifted "
        f"(got {sorted(actual_statuses)!r})"
    )

    # 2. Slot shape.
    for cls, expected in _EXPECTED_SLOTS.items():
        assert cls.__slots__ == expected, (
            f"I-OSMO-14 violated: {cls.__name__}.__slots__ drifted "
            f"(got {cls.__slots__!r}, expected {expected!r})"
        )

    # 3. MODULE_PRODUCED_STRINGS non-claim-clean.
    for produced in MODULE_PRODUCED_STRINGS:
        term = _has_forbidden(produced)
        assert term is None, (
            f"I-OSMO-14 violated: MODULE_PRODUCED_STRINGS entry "
            f"{produced!r} contains forbidden non-claim term {term!r}"
        )

    # 4. Module source non-claim-clean.
    src = inspect.getsource(_osmotic_module)
    term = _has_forbidden(src)
    assert term is None, (
        f"I-OSMO-14 violated: osmotic_learning_probe source contains "
        f"forbidden non-claim term {term!r}"
    )

    # 5. Restricted import discipline.
    lowered = src.lower()
    for fragment in _FORBIDDEN_IMPORT_FRAGMENTS:
        assert fragment not in lowered, (
            f"I-OSMO-14 violated: osmotic_learning_probe source "
            f"contains forbidden import fragment {fragment!r}"
        )
