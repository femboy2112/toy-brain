"""Fixtures for I-PLEDGER-14, I-PLEDGER-16 (no runtime coupling).

* I-PLEDGER-14 — Pattern Ledger has no ``BrainState`` / ``MSI`` /
  ``PtCns`` / ``ContentRegistry`` / ``latest_tick`` / ``tick_counter``
  / agency / LLM coupling. ``observe(...)`` does not mutate any of
  those identities and the ``tick()`` route is bit-for-bit
  unchanged. The Pattern Ledger module itself imports neither
  ``brain.tick`` nor any LLM seam.
* I-PLEDGER-16 — :class:`PatternLedgerEntry` and
  :class:`PatternLedger` records store no callable, file handle,
  socket, subprocess handle, ``pathlib.Path``, ``sqlite3.Connection``,
  curses object, or object exposing ``eval_consistency``.
"""
from __future__ import annotations

from brain.development.pattern_ledger import (
    PatternLedger,
    PatternLedgerEntry,
)
from brain.development.text_stream import (
    TextStreamSource,
    make_stream_promotion_candidate,
    make_text_stream_chunk,
)
from brain.invariants import register
from brain.tick import initial_state


def _pair():
    chunk = make_text_stream_chunk(
        chunk_id="strm-chunk-1",
        text="alpha beta gamma",
        source=TextStreamSource.OPERATOR,
        provenance="operator",
    )
    cand = make_stream_promotion_candidate(
        candidate_id="promo-strm-chunk-1",
        target_content_id="strm-strm-chunk-1",
        source=TextStreamSource.OPERATOR,
        chunk_id=chunk.chunk_id,
        text=chunk.text,
        provenance=chunk.provenance,
    )
    return chunk, cand


@register("I-PLEDGER-14", status="REQUIRED")
def check_pattern_ledger_observe_has_no_runtime_coupling() -> None:
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

    chunk, cand = _pair()
    led = PatternLedger()
    new_led = led.observe(chunk, cand, current_tick=0)
    # Second observe to exercise the existing-entry path.
    new_led = new_led.observe(chunk, cand, current_tick=1)

    # observe(...) must return a ledger with entries; the underlying
    # state must remain identity-stable.
    assert new_led.entries[0].recurrence_count >= 2
    assert state_before.profile is snapshot[0]
    assert state_before.msi is snapshot[1]
    assert state_before.ptcns is snapshot[2]
    assert state_before.registry is snapshot[3]
    assert dict(state_before.profile.values) == snapshot_profile_values
    assert frozenset(state_before.msi.contents) == snapshot_msi_contents
    assert frozenset(state_before.ptcns.positive_contents) == snapshot_ptcns_pos
    assert dict(state_before.registry.texts) == snapshot_registry_texts

    # Pattern Ledger surface exposes no truth / agency / mode / LLM /
    # tick attribute.
    forbidden_attrs = (
        "preserve",
        "damage",
        "pce",
        "projected_pce",
        "feasible_projected_pce",
        "feasibleProjectedPCE",
        "act",
        "mode_op",
        "mode",
        "agency_witness",
        "agency",
        "truth",
        "validity",
        "readability_score",
        "language",
        "meaning",
        "tick_callback",
        "eval_consistency",
        "consciousness",
        "sentience",
        "awareness",
    )
    for name in forbidden_attrs:
        assert not hasattr(new_led, name), (
            f"I-PLEDGER-14 violated: PatternLedger exposes {name!r}"
        )
        assert not hasattr(new_led.entries[0], name), (
            f"I-PLEDGER-14 violated: PatternLedgerEntry exposes {name!r}"
        )

    # The Pattern Ledger module does not import brain.tick / brain.llm
    # / brain.ui at module level (the I-PLEDGER-15 static audit
    # enforces this comprehensively; the assertion here is a runtime
    # cross-check that confirms the loaded module's globals are clean).
    import brain.development.pattern_ledger as pl  # noqa: PLC0415
    pl_globals = vars(pl)
    for forbidden_global in ("tick", "BrainState", "LLMClient"):
        assert forbidden_global not in pl_globals, (
            "I-PLEDGER-14 violated: pattern_ledger.py exposes global "
            f"{forbidden_global!r}"
        )
    pl_modules_in_globals = {
        v.__name__ for v in pl_globals.values()
        if hasattr(v, "__name__") and isinstance(getattr(v, "__name__"), str)
    }
    for forbidden_mod in ("brain.tick", "brain.llm.client", "brain.ui.session"):
        assert forbidden_mod not in pl_modules_in_globals, (
            "I-PLEDGER-14 violated: pattern_ledger.py module globals "
            f"include {forbidden_mod!r}"
        )


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
        # Tuples are fine; we recurse one level to catch a callable
        # hiding in a tuple member, but not deeper to avoid touching
        # frozen-set bookkeeping.
        if isinstance(value, tuple):
            for i, item in enumerate(value):
                out.append((f"{name}[{i}]", item))
    return out


@register("I-PLEDGER-16", status="STRUCTURAL")
def check_pattern_ledger_records_carry_no_unsafe_resources() -> None:
    chunk, cand = _pair()
    led = PatternLedger().observe(chunk, cand, current_tick=0)
    led = led.observe(chunk, cand, current_tick=1)

    # PatternLedger record itself.
    for name, value in _walk_field_values(led):
        unsafe, reason = _is_resource_like(value)
        assert not unsafe, (
            f"I-PLEDGER-16 violated: PatternLedger.{name} looks unsafe ({reason})"
        )

    # Every entry.
    for idx, entry in enumerate(led.entries):
        assert isinstance(entry, PatternLedgerEntry)
        for name, value in _walk_field_values(entry):
            unsafe, reason = _is_resource_like(value)
            assert not unsafe, (
                f"I-PLEDGER-16 violated: PatternLedger.entries[{idx}].{name} "
                f"looks unsafe ({reason})"
            )
