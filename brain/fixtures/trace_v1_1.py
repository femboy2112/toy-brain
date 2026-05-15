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
from typing import Callable

from brain.fixtures.scenario_v1 import SCENARIO_PATH
from brain.invariants import register
from brain.llm.client import MockClient
from brain.scenario import load_scenario, run_scenario
from brain.trace import (
    CognitionTracer,
    FileTracer,
    MemoryTracer,
    NullTracer,
    SafeTracer,
)


class _TracerThatAlwaysRaises:
    """Sink that fails on every call. Wrapped in SafeTracer for I-TRACE-02."""

    def record(self, *args, **kwargs):
        raise RuntimeError("simulated sink failure: record")

    def set_tick(self, *args, **kwargs):
        raise RuntimeError("simulated sink failure: set_tick")

    def clear_tick(self, *args, **kwargs):
        raise RuntimeError("simulated sink failure: clear_tick")

    def close(self, *args, **kwargs):
        raise RuntimeError("simulated sink failure: close")


def _fresh_mock_responses() -> list[str]:
    """Same sequence the scenario_v1 fixture uses: one expected_eval per tick."""
    spec = load_scenario(SCENARIO_PATH)
    return [t.expected_eval.name for t in spec.ticks]


def _run_with_tracer(tracer: CognitionTracer):
    spec = load_scenario(SCENARIO_PATH)
    client = MockClient(_fresh_mock_responses())
    return run_scenario(spec, client, tracer=tracer)


def _assert_trace_03_value_error(call: Callable[[], None]) -> None:
    try:
        call()
    except ValueError as exc:
        assert "I-TRACE-03" in str(exc), (
            f"reserved-key rejection did not name I-TRACE-03: {exc!r}"
        )
    else:
        raise AssertionError("I-TRACE-03 violated: reserved trace key accepted")


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


@register("I-TRACE-02", status="STRUCTURAL")
def check_I_TRACE_02() -> None:
    """Tracer failures must not propagate.

    Two sub-cases:

    1. Pre-wrapped: ``SafeTracer(_TracerThatAlwaysRaises())`` produces
       the same BrainState and mode_trace as the NullTracer baseline.
       This was the original I-TRACE-02 contract.

    2. (Phase 2 v1.2 corrigenda C2) Boundary-wrapped: a raw
       ``_TracerThatAlwaysRaises`` passed directly to ``tick()`` must
       *also* not propagate, because ``tick()`` now wraps any
       non-SafeTracer in SafeTracer at the kernel boundary. Confirms
       that explicit ``--trace`` paths and other call sites cannot
       bypass the fail-open guarantee.
    """
    # Sub-case 1: factory-wrapped path.
    null_result = _run_with_tracer(NullTracer())
    failing = SafeTracer(_TracerThatAlwaysRaises())
    failing_result = _run_with_tracer(failing)
    assert null_result.final_state == failing_result.final_state, (
        "I-TRACE-02 violated: SafeTracer(raising) produced different BrainState"
    )
    assert null_result.actual_modes == failing_result.actual_modes, (
        "I-TRACE-02 violated: SafeTracer(raising) produced different mode_trace "
        f"null={[m.name for m in null_result.actual_modes]} "
        f"failing={[m.name for m in failing_result.actual_modes]}"
    )

    # Sub-case 2: boundary-wrapping path. Pass an UNWRAPPED raising
    # tracer directly to tick(); tick() must wrap it internally.
    from brain.tick import initial_state, tick
    from brain.fixtures.scenario_v1 import _dummy_event

    state = initial_state()
    events = [_dummy_event("c2_boundary_test")]
    client = MockClient(["PRESERVE"])
    raw_raising = _TracerThatAlwaysRaises()  # NOT wrapped
    new_state, record = tick(state, events, client, tracer=raw_raising)
    assert record is not None, (
        "I-TRACE-02 corrigenda C2 violated: tick() returned None when given "
        "an unwrapped raising tracer (expected boundary-wrap to absorb it)."
    )
    assert new_state.profile.values, (
        "I-TRACE-02 corrigenda C2 violated: tick() returned an empty profile"
    )


@register("I-TRACE-03", status="STRUCTURAL")
def check_I_TRACE_03() -> None:
    """Trace payloads cannot overwrite reserved event-envelope keys."""
    for key in ("type", "timestamp_ns", "tick_id"):
        mem_tracer = MemoryTracer()
        _assert_trace_03_value_error(
            lambda key=key, mem_tracer=mem_tracer: mem_tracer.record(
                "reserved-key-test",
                {key: "payload collision"},
            )
        )
        assert mem_tracer.events == [], (
            f"I-TRACE-03 violated: MemoryTracer recorded reserved key {key!r}"
        )

        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "trace.jsonl"
            file_tracer = FileTracer(file_path)
            try:
                _assert_trace_03_value_error(
                    lambda key=key, file_tracer=file_tracer: file_tracer.record(
                        "reserved-key-test",
                        {key: "payload collision"},
                    )
                )
            finally:
                file_tracer.close()
            assert file_path.read_text(encoding="utf-8") == "", (
                f"I-TRACE-03 violated: FileTracer wrote reserved key {key!r}"
            )

    safe_mem = MemoryTracer()
    SafeTracer(safe_mem).record("reserved-key-test", {"type": "payload collision"})
    assert safe_mem.events == [], (
        "I-TRACE-03 violated: SafeTracer(MemoryTracer) propagated reserved-key "
        "failure or recorded the invalid event"
    )

    with tempfile.TemporaryDirectory() as tmp:
        file_path = Path(tmp) / "trace.jsonl"
        safe_file = SafeTracer(FileTracer(file_path))
        safe_file.record("reserved-key-test", {"tick_id": 123})
        safe_file.close()
        assert file_path.read_text(encoding="utf-8") == "", (
            "I-TRACE-03 violated: SafeTracer(FileTracer) recorded an invalid event"
        )
