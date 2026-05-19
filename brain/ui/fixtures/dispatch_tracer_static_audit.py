"""Phase 3.23 dispatch tracer static audit fixture.

Drives ``I-DTRACE-12`` (STRUCTURAL). Audits the closed enum membership,
slot shape, ``MODULE_PRODUCED_STRINGS`` non-claim-clean discipline,
module source non-claim-clean discipline, and closed import discipline
of ``brain/development/dispatch_tracer.py``.
"""
from __future__ import annotations

import inspect

from brain.development import dispatch_tracer as _DISPATCH_TRACER
from brain.development.coherence_monitor import _FORBIDDEN_NON_CLAIM_TERMS
from brain.development.dispatch_tracer import (
    DispatchMutationKind,
    DispatchTrace,
    DispatchTraceConfig,
    DispatchTraceDigest,
    DispatchTraceKind,
    DispatchTraceReport,
    DispatchTraceStatus,
    DispatchTraceStep,
    MODULE_PRODUCED_STRINGS as DISPATCH_TRACER_PRODUCED,
)
from brain.invariants import register


_EXPECTED_DISPATCH_TRACE_KIND_VALUES = frozenset(
    {
        "command_received",
        "route_selected",
        "pre_state_snapshot",
        "handler_entered",
        "handler_returned",
        "post_state_snapshot",
        "mutation_classified",
        "autosave_checked",
        "resource_audit_checked",
        "trace_finalized",
        "error_recorded",
        "noop_recorded",
    }
)


_EXPECTED_DISPATCH_MUTATION_KIND_VALUES = frozenset(
    {
        "none",
        "ui_only",
        "stream_append",
        "stream_window_internal",
        "stream_promote",
        "queue_mutation",
        "step_tick",
        "session_persistence",
        "autosave",
        "db_observe",
        "db_backup",
        "view_change",
        "quit_flag",
        "error_only",
    }
)


_EXPECTED_DISPATCH_TRACE_STATUS_VALUES = frozenset(
    {"pass", "warn", "fail", "not_applicable"}
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
    "import pathlib",
    "import math",
    "import os",
)


def _has_forbidden(text: str):
    lowered = text.lower()
    for term in _FORBIDDEN_NON_CLAIM_TERMS:
        if term in lowered:
            return term
    return None


@register("I-DTRACE-12", status="STRUCTURAL")
def check_dispatch_tracer_static_audit() -> None:
    """Audit dispatch_tracer.py for closed-enum + slot + import discipline."""

    # 1. Enum membership.
    assert issubclass(DispatchTraceKind, str)
    actual_kind = frozenset(k.value for k in DispatchTraceKind)
    assert actual_kind == _EXPECTED_DISPATCH_TRACE_KIND_VALUES, sorted(
        actual_kind
    )

    assert issubclass(DispatchMutationKind, str)
    actual_mut = frozenset(k.value for k in DispatchMutationKind)
    assert actual_mut == _EXPECTED_DISPATCH_MUTATION_KIND_VALUES, sorted(
        actual_mut
    )

    assert issubclass(DispatchTraceStatus, str)
    actual_sts = frozenset(k.value for k in DispatchTraceStatus)
    assert actual_sts == _EXPECTED_DISPATCH_TRACE_STATUS_VALUES, sorted(
        actual_sts
    )

    # 2. Slot shape.
    expected_slots = {
        DispatchTraceStep: (
            "step_index",
            "kind",
            "command_kind",
            "mutation_kind",
            "status",
            "route_label",
            "before_facts",
            "after_facts",
            "derived_facts",
            "limitation_label",
            "digest_contribution",
        ),
        DispatchTrace: ("steps", "interaction_id"),
        DispatchTraceDigest: (
            "digest_hex16",
            "command_kind",
            "mutation_kind",
            "route_path",
        ),
        DispatchTraceReport: (
            "trace",
            "step_total",
            "command_received_count",
            "route_selected_count",
            "pre_state_snapshot_count",
            "handler_entered_count",
            "handler_returned_count",
            "post_state_snapshot_count",
            "mutation_classified_count",
            "autosave_checked_count",
            "resource_audit_checked_count",
            "trace_finalized_count",
            "error_recorded_count",
            "noop_recorded_count",
            "command_kind",
            "mutation_kind",
            "overall_status",
            "route_path",
            "trace_digest_hex16",
            "summary_line",
        ),
        DispatchTraceConfig: ("module_version",),
    }
    for cls, expected in expected_slots.items():
        assert cls.__slots__ == expected, (
            "I-DTRACE-12 violated: "
            f"{cls.__name__}.__slots__ drifted "
            f"(got {cls.__slots__!r}, expected {expected!r})"
        )

    # 3. MODULE_PRODUCED_STRINGS audit.
    for produced in DISPATCH_TRACER_PRODUCED:
        assert isinstance(produced, str)
        assert produced.isprintable()
        term = _has_forbidden(produced)
        assert term is None, (
            "I-DTRACE-12 violated: MODULE_PRODUCED_STRINGS contains "
            f"forbidden non-claim term {term!r}: {produced!r}"
        )

    # 4. Module source non-claim-clean.
    src = inspect.getsource(_DISPATCH_TRACER)
    term = _has_forbidden(src)
    assert term is None, (
        "I-DTRACE-12 violated: dispatch_tracer module source contains "
        f"forbidden non-claim term {term!r}"
    )

    # 5. Forbidden imports.
    lowered = src.lower()
    for fragment in _EXPECTED_FORBIDDEN_IMPORT_FRAGMENTS:
        assert fragment not in lowered, (
            "I-DTRACE-12 violated: dispatch_tracer module source contains "
            f"forbidden import fragment {fragment!r}"
        )
