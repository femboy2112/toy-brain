"""Cognition trace fixture (Phase 2 v1.1).

Drives: I-TRACE-01 (STRUCTURAL) — observation-only determinism.

Runs the first scenario three times — once per tracer backend
(``NullTracer``, ``MemoryTracer``, ``FileTracer``) — with the same
``MockClient`` seed each time. Asserts that the resulting final
``BrainState`` and ``mode_trace`` are equal across all three runs.

A passing fixture proves that the tracer has no observable effect on
``tick()`` output. The MemoryTracer also serves as an inspection
artifact: we verify it captured the expected taxonomy of event types.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from brain.fixtures.scenario_v1 import SCENARIO_PATH
from brain.invariants import register
from brain.llm.client import MockClient
from brain.scenario import load_scenario, run_scenario
from brain.trace import (
    CognitionTracer,
    FileTracer,
    MemoryTracer,
    NullTracer,
)


def _fresh_mock_responses() -> list[str]:
    """Same sequence the scenario_v1 fixture uses: one expected_eval per tick."""
    spec = load_scenario(SCENARIO_PATH)
    return [t.expected_eval.name for t in spec.ticks]


def _run_with_tracer(tracer: CognitionTracer):
    spec = load_scenario(SCENARIO_PATH)
    client = MockClient(_fresh_mock_responses())
    return run_scenario(spec, client, tracer=tracer)


@register("I-TRACE-01", status="STRUCTURAL")
def check_I_TRACE_01() -> None:
    """Tracer is observation-only: identical output across three backends."""
    null_result = _run_with_tracer(NullTracer())
    mem_tracer = MemoryTracer()
    mem_result = _run_with_tracer(mem_tracer)

    with tempfile.TemporaryDirectory() as tmp:
        file_path = Path(tmp) / "trace.jsonl"
        file_tracer = FileTracer(file_path)
        file_result = _run_with_tracer(file_tracer)
        # FileTracer.close was called in run_scenario's finally; double
        # close is a no-op.
        assert file_path.exists(), "FileTracer produced no output file"
        line_count = sum(1 for _ in file_path.open("r", encoding="utf-8"))
        assert line_count > 0, "FileTracer produced empty file"

    # Final BrainState must be byte-identical across all three runs.
    assert null_result.final_state == mem_result.final_state, (
        "I-TRACE-01 violated: NullTracer vs MemoryTracer produced different BrainState"
    )
    assert null_result.final_state == file_result.final_state, (
        "I-TRACE-01 violated: NullTracer vs FileTracer produced different BrainState"
    )

    # Mode traces must match exactly.
    assert null_result.actual_modes == mem_result.actual_modes, (
        f"I-TRACE-01 violated: mode_trace drift "
        f"null={[m.name for m in null_result.actual_modes]} "
        f"mem={[m.name for m in mem_result.actual_modes]}"
    )
    assert null_result.actual_modes == file_result.actual_modes, (
        f"I-TRACE-01 violated: mode_trace drift "
        f"null={[m.name for m in null_result.actual_modes]} "
        f"file={[m.name for m in file_result.actual_modes]}"
    )

    # MemoryTracer captured the expected taxonomy (sanity for the
    # observation surface, not part of I-TRACE-01 itself).
    captured_types = {e["type"] for e in mem_tracer.events}
    expected_subset = {
        "tick.start",
        "tick.end",
        "llm.request",
        "llm.response",
        "parse.success",
        "eval.complete",
        "mode.dispatch",
        "state.update",
        "invariant.check",
    }
    missing = expected_subset - captured_types
    assert not missing, (
        f"MemoryTracer missing expected event types: {sorted(missing)}"
    )
