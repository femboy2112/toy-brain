"""Phase 3.31 proto-speech static-audit fixture.

Drives ``I-PSPEECH-19`` (STRUCTURAL).
"""
from __future__ import annotations

import inspect

import brain.development.proto_speech_acquisition as _pspeech
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.proto_speech_acquisition import (
    CaregiverFeedback,
    CaregiverFeedbackKind,
    MODULE_PRODUCED_STRINGS,
    ProtoSpeechAcquisitionReport,
    ProtoSpeechCondition,
    ProtoSpeechContext,
    ProtoSpeechContextKind,
    ProtoSpeechDriveFrame,
    ProtoSpeechDriveKind,
    ProtoSpeechDriveStream,
    ProtoSpeechEvidenceRecord,
    ProtoSpeechEvidenceTable,
    ProtoSpeechStatus,
    ProtoSpeechTurn,
    ProtoUtterance,
    ProtoUtteranceDisposition,
    ProtoVocalToken,
)
from brain.invariants import register


_EXPECTED_VOCAL_VALUES = frozenset({
    "ba", "ma", "da", "na", "la",
    "same", "more", "again", "no", "yes",
    "look", "this", "that", "help", "done",
})

_EXPECTED_FEEDBACK_VALUES = frozenset({
    "accepted", "ignored", "echo", "corrected", "expanded", "ambient_only",
})

_EXPECTED_CTX_VALUES = frozenset({
    "abstract_pattern", "worldlet", "repl", "dispatch_trace",
    "reasoning_trace", "learning_evidence", "active_hypothesis",
    "curriculum", "unknown",
})

_EXPECTED_DISPOSITION_VALUES = frozenset({
    "babble", "candidate", "reinforced", "suppressed",
    "stable_single", "stable_combination", "transferred", "rejected",
})

_EXPECTED_DRIVE_VALUES = frozenset({
    "low_evidence", "recurrence_pressure", "novelty_pressure",
    "transfer_pressure", "unresolved_hypothesis",
    "worldlet_feedback_present", "repl_feedback_present",
    "caregiver_ambient_prime", "caregiver_feedback_prime",
    "suppression_pressure", "combination_pressure", "refusal_guard",
})

_EXPECTED_STATUS_VALUES = frozenset({
    "pass", "warn", "fail", "not_applicable",
})

_EXPECTED_CONDITION_VALUES = frozenset({
    "babble_baseline", "ambient_imprinting", "feedback_reinforcement",
    "correction_shaping", "holophrase_transfer", "two_token_combination",
    "suppression", "turn_taking", "refusal_held", "drive_stream_pressure",
})


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


def _has_forbidden_term(text: str):
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-PSPEECH-19", status="STRUCTURAL")
def check_proto_speech_static_audit() -> None:
    """Static audit: closed enums, slot shapes, source / produced strings."""
    # 1. Closed enums.
    assert issubclass(ProtoVocalToken, str)
    assert frozenset(t.value for t in ProtoVocalToken) == (
        _EXPECTED_VOCAL_VALUES
    )

    assert issubclass(CaregiverFeedbackKind, str)
    assert frozenset(k.value for k in CaregiverFeedbackKind) == (
        _EXPECTED_FEEDBACK_VALUES
    )

    assert issubclass(ProtoSpeechContextKind, str)
    assert frozenset(c.value for c in ProtoSpeechContextKind) == (
        _EXPECTED_CTX_VALUES
    )

    assert issubclass(ProtoUtteranceDisposition, str)
    assert frozenset(d.value for d in ProtoUtteranceDisposition) == (
        _EXPECTED_DISPOSITION_VALUES
    )

    assert issubclass(ProtoSpeechDriveKind, str)
    assert frozenset(k.value for k in ProtoSpeechDriveKind) == (
        _EXPECTED_DRIVE_VALUES
    )

    assert issubclass(ProtoSpeechStatus, str)
    assert frozenset(s.value for s in ProtoSpeechStatus) == (
        _EXPECTED_STATUS_VALUES
    )

    assert issubclass(ProtoSpeechCondition, str)
    assert frozenset(c.value for c in ProtoSpeechCondition) == (
        _EXPECTED_CONDITION_VALUES
    )

    # 2. Slot shape of every frozen record.
    expected_slots = {
        ProtoUtterance: (
            "tokens",
            "text",
            "token_count",
            "reduplicated",
            "digest_hex16",
        ),
        CaregiverFeedback: (
            "kind",
            "offered_utterance",
            "ambient_utterance",
            "context_label",
            "evidence_delta",
        ),
        ProtoSpeechContext: (
            "context_kind",
            "abstract_pattern_digest",
            "abstract_pattern_shape",
            "worldlet_feedback_present",
            "repl_result_present",
            "dispatch_trace_digest",
            "reasoning_trace_digest",
            "learning_evidence_digest",
            "active_hypothesis_digest",
            "curriculum_digest",
            "context_signature",
        ),
        ProtoSpeechDriveFrame: (
            "drive_kind",
            "source_surface",
            "context_signature",
            "input_digest_hex16",
            "evidence_digest_hex16",
            "reasoning_trace_digest_hex16",
            "dispatch_trace_digest_hex16",
            "caregiver_utterance_digest_hex16",
            "weight_hint",
            "suggested_token_set",
            "explanation",
        ),
        ProtoSpeechDriveStream: (
            "frames",
            "max_frames",
            "digest_hex16",
            "status",
        ),
        ProtoSpeechEvidenceRecord: (
            "context_signature",
            "utterance_digest",
            "utterance_text",
            "feedback_kind",
            "weight_before",
            "weight_after",
            "disposition",
            "update_reason",
            "drive_stream_digest_hex16",
            "digest_hex16",
        ),
        ProtoSpeechEvidenceTable: (
            "entries",
            "max_records",
            "digest_hex16",
        ),
        ProtoSpeechTurn: (
            "turn_id",
            "condition",
            "context",
            "drive_stream",
            "caregiver_ambient",
            "selected_utterance",
            "selected_disposition_before",
            "feedback",
            "evidence_records_added",
            "learning_evidence_digest",
            "reasoning_trace_digest",
            "dispatch_trace_digest",
            "refusal_taken",
            "transfer_taken",
            "summary_line",
        ),
        ProtoSpeechAcquisitionReport: (
            "battery_version",
            "turns",
            "condition_statuses",
            "stable_single_count",
            "stable_combination_count",
            "suppressed_count",
            "transfer_success_count",
            "false_positive_count",
            "false_negative_count",
            "pass_count",
            "warn_count",
            "fail_count",
            "not_applicable_count",
            "drive_stream_count",
            "drive_stream_digest_hex16",
            "digest_hex16",
            "real_model_calls",
            "cache_writes",
            "forbidden_term_hits",
            "summary_line",
            "status",
            # Phase 3.33 (I-PSPEECH-20 + I-PROBE-02) diagnostic fields.
            # Outside the digest input by construction.
            "stable_combination_count_strict",
            "strict_count_warnings",
        ),
    }
    for cls, slots in expected_slots.items():
        assert cls.__slots__ == slots, (
            f"I-PSPEECH-19 violated: {cls.__name__}.__slots__ drifted: "
            f"got {cls.__slots__!r}, expected {slots!r}"
        )

    # 3. MODULE_PRODUCED_STRINGS non-claim-clean.
    for s in MODULE_PRODUCED_STRINGS:
        assert isinstance(s, str)
        assert s.isprintable()
        term = _has_forbidden_term(s)
        assert term is None, (
            f"I-PSPEECH-19 violated: MODULE_PRODUCED_STRINGS entry "
            f"{s!r} contains forbidden non-claim term {term!r}"
        )

    # 4. Module source non-claim-clean.
    src = inspect.getsource(_pspeech)
    term = _has_forbidden_term(src)
    assert term is None, (
        f"I-PSPEECH-19 violated: module source contains forbidden "
        f"non-claim term {term!r}"
    )

    # 5. Closed import discipline.
    for fragment in _FORBIDDEN_IMPORT_FRAGMENTS:
        assert fragment not in src, (
            f"I-PSPEECH-19 violated: module source contains forbidden "
            f"import fragment {fragment!r}"
        )
