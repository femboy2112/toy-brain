"""Fixtures for I-GROW-12 and I-GROW-20.

* I-GROW-12 — :class:`GrowthEvent` and :class:`GrowthLedger` records
  store no callable, file handle, socket, subprocess handle,
  ``pathlib.Path``, ``sqlite3.Connection`` / ``Cursor``, curses
  object, LLM client-shaped object, or object exposing
  ``eval_consistency``.
* I-GROW-20 — Growth Ledger integration is structurally one-way:
  ``brain/ui/session.py`` imports
  :mod:`brain.development.growth_ledger`, but the Growth Ledger
  module does not import the session, Pattern Ledger, Coherence
  Monitor, ``brain.tick``, LLM, or UI modules at runtime.
  :meth:`GrowthLedger.observe` does not mutate
  :class:`BrainState`, ``MSI``, ``PtCns``, ``ContentRegistry``,
  ``latest_tick``, ``tick_counter``, ``OperatorSession.event_queue``,
  stream histories, the Pattern Ledger, the Coherence Monitor
  records, the persistence config, or the autosave config.
"""
from __future__ import annotations

import brain.development.growth_ledger as gl
from brain.development.growth_ledger import (
    GrowthEvent,
    GrowthEventSource,
    GrowthEventType,
    GrowthLedger,
)
from brain.invariants import register
from brain.tick import initial_state


def _is_resource_like(value: object) -> tuple[bool, str]:
    """Return ``(is_unsafe, reason)`` mirroring the I-UI-10 audit."""
    if callable(value):
        return True, "callable"
    if hasattr(value, "eval_consistency"):
        return True, "eval_consistency (LLM client)"
    if hasattr(value, "read") and hasattr(value, "write"):
        return True, "read/write (file/socket-like)"
    if hasattr(value, "fileno"):
        return True, "fileno (resource-like)"
    if hasattr(value, "send_signal") or hasattr(value, "communicate"):
        return True, "subprocess handle"
    if hasattr(value, "cursor") and hasattr(value, "commit"):
        return True, "sqlite3.Connection-like"
    return False, ""


def _walk_field_values(record: object) -> list[tuple[str, object]]:
    out: list[tuple[str, object]] = []
    for name in getattr(record, "__slots__", ()):
        value = getattr(record, name)
        out.append((name, value))
        if isinstance(value, tuple):
            for i, item in enumerate(value):
                out.append((f"{name}[{i}]", item))
    return out


def _sample_ledger() -> GrowthLedger:
    led = GrowthLedger()
    led = led.observe(
        event_type=GrowthEventType.STREAM_CHUNK_ACCEPTED,
        tick=1,
        source=GrowthEventSource.STREAM_APPEND,
        references=("strm-chunk-1",),
        provenance="stream_append:_dispatch_stream_append",
    )
    led = led.observe(
        event_type=GrowthEventType.TICK_SUCCEEDED,
        tick=2,
        source=GrowthEventSource.STEP_DISPATCH,
        references=("tick-1",),
        provenance="step_dispatch:_dispatch_step",
    )
    return led


@register("I-GROW-12", status="REQUIRED")
def check_growth_ledger_no_unsafe_resources() -> None:
    led = _sample_ledger()

    # GrowthLedger record itself.
    for name, value in _walk_field_values(led):
        unsafe, reason = _is_resource_like(value)
        assert not unsafe, (
            f"I-GROW-12 violated: GrowthLedger.{name} looks unsafe ({reason})"
        )

    # Every GrowthEvent.
    for idx, event in enumerate(led.events):
        assert isinstance(event, GrowthEvent)
        for name, value in _walk_field_values(event):
            unsafe, reason = _is_resource_like(value)
            assert not unsafe, (
                f"I-GROW-12 violated: GrowthLedger.events[{idx}].{name} "
                f"looks unsafe ({reason})"
            )

    # GrowthEvent / GrowthLedger surface exposes no LLM / kernel /
    # claim attribute.
    forbidden_attrs = (
        "pce",
        "projected_pce",
        "feasible_projected_pce",
        "feasibleProjectedPCE",
        "act",
        "mode_op",
        "mode",
        "agency_witness",
        "validity",
        "readability_score",
        "language",
        "meaning",
        "tick_callback",
        "eval_consistency",
    )
    sample_event = led.events[0]
    for name in forbidden_attrs:
        assert not hasattr(led, name), (
            f"I-GROW-12 violated: GrowthLedger exposes forbidden field "
            f"{name!r}"
        )
        assert not hasattr(sample_event, name), (
            f"I-GROW-12 violated: GrowthEvent exposes forbidden field "
            f"{name!r}"
        )


@register("I-GROW-20", status="STRUCTURAL")
def check_growth_ledger_no_runtime_coupling() -> None:
    state_before = initial_state()
    snapshot = (
        state_before.profile,
        state_before.msi,
        state_before.ptcns,
        state_before.registry,
    )
    snapshot_profile_values = dict(state_before.profile.values)
    snapshot_msi_contents = frozenset(state_before.msi.contents)
    snapshot_ptcns_pos = frozenset(state_before.ptcns.positive_contents)
    snapshot_registry_texts = dict(state_before.registry.texts)

    led = _sample_ledger()
    # An additional observe is a no-op for state identity.
    _ = led.observe(
        event_type=GrowthEventType.STREAM_CHUNK_ACCEPTED,
        tick=4,
        source=GrowthEventSource.STREAM_APPEND,
        references=("strm-chunk-2",),
        provenance="stream_append:_dispatch_stream_append",
    )

    # observe(...) must never reach into the kernel state record.
    assert state_before.profile is snapshot[0]
    assert state_before.msi is snapshot[1]
    assert state_before.ptcns is snapshot[2]
    assert state_before.registry is snapshot[3]
    assert dict(state_before.profile.values) == snapshot_profile_values
    assert frozenset(state_before.msi.contents) == snapshot_msi_contents
    assert (
        frozenset(state_before.ptcns.positive_contents) == snapshot_ptcns_pos
    )
    assert dict(state_before.registry.texts) == snapshot_registry_texts

    # The Growth Ledger module exposes no global binding of the
    # session / kernel / Pattern Ledger / Coherence Monitor / LLM
    # callables. This is a runtime cross-check; I-GROW-10 / I-GROW-11
    # enforce the same property at the static-AST level.
    gl_globals = vars(gl)
    for forbidden_global in (
        "tick",
        "BrainState",
        "LLMClient",
        "OperatorSession",
        "PatternLedger",
        "PatternLedgerEntry",
        "CoherenceReport",
        "CoherenceCheck",
        "TextStreamChunk",
        "TextStreamHistory",
        "save_session",
        "load_session",
        "db_backup",
        "db_verify",
        "maybe_autosave_after_mutation",
        "build_coherence_report",
        "build_full_coherence_report",
    ):
        assert forbidden_global not in gl_globals, (
            "I-GROW-20 violated: growth_ledger.py exposes global "
            f"{forbidden_global!r}"
        )

    # The set of module names visible as loaded module values inside
    # growth_ledger.py must not include session / tick / llm / ui /
    # pattern_ledger / coherence_monitor.
    gl_module_names = {
        v.__name__ for v in gl_globals.values()
        if hasattr(v, "__name__") and isinstance(getattr(v, "__name__"), str)
    }
    for forbidden_mod in (
        "brain.tick",
        "brain.llm.client",
        "brain.ui.session",
        "brain.development.pattern_ledger",
        "brain.development.coherence_monitor",
        "brain.development.text_stream",
    ):
        assert forbidden_mod not in gl_module_names, (
            "I-GROW-20 violated: growth_ledger.py module globals include "
            f"{forbidden_mod!r}"
        )
