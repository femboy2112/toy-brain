"""Phase 3.30 curriculum probe static-audit fixture.

Drives ``I-CURR-14`` (STRUCTURAL).
"""
from __future__ import annotations

import inspect

import brain.development.curriculum_consolidation_probe as _curr
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.curriculum_consolidation_probe import (
    AdmissionOutcome,
    AuditDisposition,
    CurriculumConsolidationReport,
    CurriculumCondition,
    CurriculumExposure,
    CurriculumProbeStep,
    CurriculumStructureRecord,
    CurriculumTrial,
    CurriculumTrialResult,
    MODULE_PRODUCED_STRINGS,
    TrialVerdict,
)
from brain.invariants import register


_EXPECTED_CONDITION_VALUES = frozenset({
    "single_structure",
    "sequential_noninterfering",
    "sequential_interfering",
    "decay_on_disuse",
    "reuse_after_newer",
})

_EXPECTED_DISPOSITION_VALUES = frozenset({
    "survived", "decayed", "rejected",
})

_EXPECTED_ADMISSION_VALUES = frozenset({
    "admitted", "rejected_collision", "rejected_nonprintable",
})

_EXPECTED_VERDICT_VALUES = frozenset({"pass", "warn", "fail", "not_applicable"})


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
    "import importlib",
    "import time",
    "import random",
    "import pathlib",
    "import math",
    "import os\n",
    "import os ",
    "from os ",
    "from brain.ui",
)


def _has_forbidden_term(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-CURR-14", status="STRUCTURAL")
def check_curriculum_static_audit() -> None:
    """Static audit on brain/development/curriculum_consolidation_probe.py."""
    # 1. Closed enums.
    assert issubclass(CurriculumCondition, str)
    assert frozenset(c.value for c in CurriculumCondition) == _EXPECTED_CONDITION_VALUES

    assert issubclass(AuditDisposition, str)
    assert frozenset(d.value for d in AuditDisposition) == _EXPECTED_DISPOSITION_VALUES

    assert issubclass(AdmissionOutcome, str)
    assert frozenset(o.value for o in AdmissionOutcome) == _EXPECTED_ADMISSION_VALUES

    assert issubclass(TrialVerdict, str)
    assert frozenset(v.value for v in TrialVerdict) == _EXPECTED_VERDICT_VALUES

    # 2. Slot shapes of frozen records.
    expected_slots = {
        CurriculumExposure: (
            "exposure_id",
            "input_text",
        ),
        CurriculumStructureRecord: (
            "structure_id",
            "source_digest_hex16",
            "admitted_at_step",
            "last_access_step",
            "disposition",
        ),
        CurriculumProbeStep: (
            "probe_input",
            "probe_digest_hex16",
            "reuse_observed",
            "probe_reused_structure_id",
            "interaction_id",
            "dispatch_trace_digest",
            "reasoning_trace_digest",
            "reply_excerpt",
            "summary_line",
        ),
        CurriculumTrial: (
            "trial_id",
            "condition",
            "exposures",
            "probe_input",
            "slate_max_entries",
            "expected_survived_count",
            "expected_decayed_count",
            "expected_rejected_count",
            "expected_reuse_observed",
        ),
        CurriculumTrialResult: (
            "trial_id",
            "condition",
            "verdict",
            "audit_records",
            "probe_step",
            "survived_count",
            "decayed_count",
            "rejected_count",
            "reuse_observed",
            "false_positive",
            "false_negative",
            "learning_evidence_digest",
            "reasoning_trace_digest",
            "dispatch_trace_digests",
            "summary_line",
        ),
        CurriculumConsolidationReport: (
            "battery_version",
            "trials",
            "pass_count",
            "warn_count",
            "fail_count",
            "not_applicable_count",
            "false_positive_count",
            "false_negative_count",
            "total_survived_count",
            "total_decayed_count",
            "total_rejected_count",
            "reuse_observed_count",
            "real_model_calls",
            "cache_writes",
            "forbidden_term_hits",
            "digest_hex16",
            "summary_line",
        ),
    }
    for cls, slots in expected_slots.items():
        assert cls.__slots__ == slots, (
            f"I-CURR-14 violated: {cls.__name__}.__slots__ drifted: "
            f"got {cls.__slots__!r}, expected {slots!r}"
        )

    # 3. MODULE_PRODUCED_STRINGS non-claim-clean.
    for s in MODULE_PRODUCED_STRINGS:
        assert isinstance(s, str)
        assert s.isprintable()
        term = _has_forbidden_term(s)
        assert term is None, (
            f"I-CURR-14 violated: MODULE_PRODUCED_STRINGS entry {s!r} "
            f"contains forbidden non-claim term {term!r}"
        )

    # 4. Module source non-claim-clean.
    src = inspect.getsource(_curr)
    term = _has_forbidden_term(src)
    assert term is None, (
        f"I-CURR-14 violated: module source contains forbidden non-claim "
        f"term {term!r}"
    )

    # 5. Closed import discipline.
    for fragment in _FORBIDDEN_IMPORT_FRAGMENTS:
        assert fragment not in src, (
            f"I-CURR-14 violated: module source contains forbidden import "
            f"fragment {fragment!r}"
        )
