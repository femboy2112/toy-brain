"""Phase 3.26 active hypothesis probe static-audit fixture.

Drives ``I-AHYP-14`` (STRUCTURAL).
"""
from __future__ import annotations

import inspect

import brain.development.active_hypothesis_probe as _ahyp
from brain.development.active_hypothesis_probe import (
    ActiveHypothesisCandidate,
    ActiveHypothesisLiveTestReport,
    ActiveHypothesisResult,
    ActiveHypothesisStatus,
    ActiveHypothesisTrial,
    ActiveProbeStep,
    AmbiguityCondition,
    MODULE_PRODUCED_STRINGS,
    ProbeConstructionRule,
    ProbeOutcome,
    TrialVerdict,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.invariants import register


_EXPECTED_AMBIGUITY_VALUES = frozenset({
    "control_no_ambiguity",
    "single_hypothesis_converges",
    "multi_hypothesis_narrows",
    "no_hypothesis_survives",
    "reuse_cached_hypothesis",
})

_EXPECTED_STATUS_VALUES = frozenset({
    "pending", "surviving", "falsified", "selected",
})

_EXPECTED_PROBE_RULE_VALUES = frozenset({
    "rename_only",
    "append_pos0_token",
    "append_pos1_token",
    "append_last_token",
    "append_new_token",
    "rename_and_double",
})

_EXPECTED_VERDICT_VALUES = frozenset({"pass", "warn", "fail", "not_applicable"})

_EXPECTED_OUTCOME_VALUES = frozenset({"confirmed", "falsified"})

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


@register("I-AHYP-14", status="STRUCTURAL")
def check_active_hypothesis_static_audit() -> None:
    """Static audit on brain/development/active_hypothesis_probe.py."""
    # 1. Closed enums.
    assert issubclass(AmbiguityCondition, str)
    assert frozenset(c.value for c in AmbiguityCondition) == _EXPECTED_AMBIGUITY_VALUES

    assert issubclass(ActiveHypothesisStatus, str)
    assert frozenset(s.value for s in ActiveHypothesisStatus) == _EXPECTED_STATUS_VALUES

    assert issubclass(ProbeConstructionRule, str)
    assert frozenset(r.value for r in ProbeConstructionRule) == _EXPECTED_PROBE_RULE_VALUES

    assert issubclass(TrialVerdict, str)
    assert frozenset(v.value for v in TrialVerdict) == _EXPECTED_VERDICT_VALUES

    assert issubclass(ProbeOutcome, str)
    assert frozenset(o.value for o in ProbeOutcome) == _EXPECTED_OUTCOME_VALUES

    # 2. Slot shapes of frozen records.
    expected_slots = {
        ActiveHypothesisCandidate: (
            "candidate_id",
            "predicted_shape_name",
            "predicted_shape",
            "predicted_classification",
            "predicted_digest_hex16",
            "probe_construction_rule",
            "status",
        ),
        ActiveProbeStep: (
            "candidate_id",
            "probe_text",
            "probe_digest_hex16",
            "probe_shape",
            "probe_classification",
            "predicted_digest_hex16",
            "outcome",
            "interaction_id",
            "dispatch_trace_digest",
            "reasoning_trace_digest",
            "reply_excerpt",
        ),
        ActiveHypothesisTrial: (
            "trial_id",
            "condition",
            "input_text",
            "expected_survivors_count",
            "expected_winner_id",
            "expected_no_hypothesis_survives",
            "expected_second_visit_cache_hit",
        ),
        ActiveHypothesisResult: (
            "trial_id",
            "condition",
            "verdict",
            "input_digest_hex16",
            "candidates",
            "probe_steps",
            "survivors_count",
            "winner_id",
            "no_hypothesis_survives",
            "second_visit_cache_hit",
            "second_visit_probe_count",
            "false_positive",
            "false_negative",
            "learning_evidence_digest",
            "reasoning_trace_digest",
            "dispatch_trace_digests",
            "summary_line",
        ),
        ActiveHypothesisLiveTestReport: (
            "battery_version",
            "trials",
            "pass_count",
            "warn_count",
            "fail_count",
            "not_applicable_count",
            "false_positive_count",
            "false_negative_count",
            "winner_selected_count",
            "no_hypothesis_survives_count",
            "cache_reuse_count",
            "real_model_calls",
            "cache_writes",
            "forbidden_term_hits",
            "digest_hex16",
            "summary_line",
        ),
    }
    for cls, slots in expected_slots.items():
        assert cls.__slots__ == slots, (
            f"I-AHYP-14 violated: {cls.__name__}.__slots__ drifted: "
            f"got {cls.__slots__!r}, expected {slots!r}"
        )

    # 3. MODULE_PRODUCED_STRINGS non-claim-clean.
    for s in MODULE_PRODUCED_STRINGS:
        assert isinstance(s, str)
        assert s.isprintable()
        term = _has_forbidden_term(s)
        assert term is None, (
            f"I-AHYP-14 violated: MODULE_PRODUCED_STRINGS entry {s!r} "
            f"contains forbidden non-claim term {term!r}"
        )

    # 4. Module source non-claim-clean.
    src = inspect.getsource(_ahyp)
    term = _has_forbidden_term(src)
    assert term is None, (
        f"I-AHYP-14 violated: module source contains forbidden non-claim "
        f"term {term!r}"
    )

    # 5. Closed import discipline.
    for fragment in _FORBIDDEN_IMPORT_FRAGMENTS:
        assert fragment not in src, (
            f"I-AHYP-14 violated: module source contains forbidden import "
            f"fragment {fragment!r}"
        )
