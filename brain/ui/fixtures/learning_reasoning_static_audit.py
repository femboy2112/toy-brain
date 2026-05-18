"""Phase 3.22b learning + reasoning static audit fixture.

Drives ``I-AGENTLEARN-11`` (STRUCTURAL). Audits the three new
Phase 3.22b modules for closed enum membership, slot shape,
``MODULE_PRODUCED_STRINGS`` non-claim-clean discipline, module source
non-claim-clean discipline, and closed import discipline.
"""
from __future__ import annotations

import inspect

from brain.development import abstract_pattern as _ABSTRACT_PATTERN
from brain.development import learning_evidence as _LEARNING_EVIDENCE
from brain.development import reasoning_trace as _REASONING_TRACE
from brain.development.abstract_pattern import (
    AbstractPatternSignature,
    MODULE_PRODUCED_STRINGS as ABSTRACT_PATTERN_PRODUCED,
)
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.learning_evidence import (
    LearningEvidenceKind,
    LearningEvidenceRecord,
    LearningEvidenceTrace,
    LearningProofReport,
    MODULE_PRODUCED_STRINGS as LEARNING_EVIDENCE_PRODUCED,
)
from brain.development.reasoning_trace import (
    MODULE_PRODUCED_STRINGS as REASONING_TRACE_PRODUCED,
    ReasoningStepKind,
    ReasoningTrace,
    ReasoningTraceReport,
    ReasoningTraceStep,
)
from brain.invariants import register


_EXPECTED_LEARNING_EVIDENCE_KIND_VALUES = frozenset(
    {
        "observed",
        "recurrence_increased",
        "abstract_pattern_acquired",
        "abstract_pattern_reused",
        "transfer_recognized",
        "repl_correction_applied",
        "diminishing_returns_updated",
        "limitation_recorded",
    }
)


_EXPECTED_REASONING_STEP_KIND_VALUES = frozenset(
    {
        "observe_input",
        "classify_refusal",
        "derive_pattern",
        "lookup_prior_structure",
        "compare_structure",
        "check_coherence",
        "check_repl",
        "select_reply_disposition",
        "check_limitation",
        "emit_reply",
    }
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
)


def _has_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


def _audit_module_source(module) -> None:
    src = inspect.getsource(module)
    term = _has_forbidden(src)
    assert term is None, (
        "I-AGENTLEARN-11 violated: module "
        f"{module.__name__} source contains forbidden non-claim "
        f"term {term!r}"
    )
    lowered = src.lower()
    for fragment in _EXPECTED_FORBIDDEN_IMPORT_FRAGMENTS:
        assert fragment not in lowered, (
            "I-AGENTLEARN-11 violated: module "
            f"{module.__name__} source contains forbidden import "
            f"fragment {fragment!r}"
        )


@register("I-AGENTLEARN-11", status="STRUCTURAL")
def check_learning_reasoning_static_audit() -> None:
    """Static audit on Phase 3.22b modules."""

    # 1. Enum membership.
    assert issubclass(LearningEvidenceKind, str)
    actual = frozenset(k.value for k in LearningEvidenceKind)
    assert actual == _EXPECTED_LEARNING_EVIDENCE_KIND_VALUES, (
        f"I-AGENTLEARN-11 violated: LearningEvidenceKind drifted: "
        f"got {sorted(actual)!r}"
    )

    assert issubclass(ReasoningStepKind, str)
    actual = frozenset(k.value for k in ReasoningStepKind)
    assert actual == _EXPECTED_REASONING_STEP_KIND_VALUES, (
        f"I-AGENTLEARN-11 violated: ReasoningStepKind drifted: "
        f"got {sorted(actual)!r}"
    )

    # 2. Slot shape.
    expected_slots = {
        AbstractPatternSignature: (
            "token_count",
            "distinct_token_count",
            "shape",
            "classification",
            "valid",
            "digest_hex16",
            "explanation",
        ),
        LearningEvidenceRecord: (
            "kind",
            "interaction_id",
            "abstract_pattern_digest",
            "pattern_id",
            "pre_facts",
            "post_facts",
            "summary",
        ),
        LearningEvidenceTrace: ("records",),
        LearningProofReport: (
            "trace",
            "record_total",
            "observed_count",
            "recurrence_increased_count",
            "abstract_pattern_acquired_count",
            "abstract_pattern_reused_count",
            "transfer_recognized_count",
            "repl_correction_applied_count",
            "diminishing_returns_updated_count",
            "limitation_recorded_count",
            "digest_hex16",
            "summary_line",
        ),
        ReasoningTraceStep: (
            "step_number",
            "kind",
            "input_facts",
            "derived_facts",
            "next_action",
        ),
        ReasoningTrace: ("steps", "input_id"),
        ReasoningTraceReport: (
            "trace",
            "step_total",
            "observe_input_count",
            "classify_refusal_count",
            "derive_pattern_count",
            "lookup_prior_structure_count",
            "compare_structure_count",
            "check_coherence_count",
            "check_repl_count",
            "select_reply_disposition_count",
            "check_limitation_count",
            "emit_reply_count",
            "trace_digest_hex16",
            "summary_line",
        ),
    }
    for cls, expected in expected_slots.items():
        assert cls.__slots__ == expected, (
            "I-AGENTLEARN-11 violated: "
            f"{cls.__name__}.__slots__ drifted "
            f"(got {cls.__slots__!r}, expected {expected!r})"
        )

    # 3. MODULE_PRODUCED_STRINGS audit on each module.
    for label, produced_tuple in (
        ("abstract_pattern", ABSTRACT_PATTERN_PRODUCED),
        ("learning_evidence", LEARNING_EVIDENCE_PRODUCED),
        ("reasoning_trace", REASONING_TRACE_PRODUCED),
    ):
        for produced in produced_tuple:
            assert isinstance(produced, str) and produced.isprintable()
            term = _has_forbidden(produced)
            assert term is None, (
                f"I-AGENTLEARN-11 violated: {label} MODULE_PRODUCED_STRINGS "
                f"entry {produced!r} contains forbidden term {term!r}"
            )

    # 4. Module source audit on each module.
    _audit_module_source(_ABSTRACT_PATTERN)
    _audit_module_source(_LEARNING_EVIDENCE)
    _audit_module_source(_REASONING_TRACE)
