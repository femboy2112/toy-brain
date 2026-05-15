"""Operator TUI snapshot fixtures.

Drives:

* ``I-UI-01`` (REQUIRED) — snapshot construction is read-only over kernel
  state. We build a deterministic ``BrainState`` plus a deterministic
  developmental-history bundle, snapshot them, and assert every input
  container's identity and ``repr`` are unchanged.
* ``I-UI-08`` (STRUCTURAL) — snapshot records are immutable display values.
  We assert ``BrainSnapshot`` and ``DevelopmentSnapshot`` are frozen
  dataclasses, every collection field is a tuple / frozenset, and exact
  ``Fraction`` values appear as strings rather than floats.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from fractions import Fraction
from types import MappingProxyType

from brain.development.output import (
    OutputHistory,
    OutputImpulse,
    OutputProvenance,
)
from brain.development.repl import ProtoBasicHistory
from brain.development.stream import FrameSourceKind
from brain.development.worldlet import (
    WorldletHistory,
    WorldletObject,
    WorldletState,
)
from brain.invariants import register
from brain.io_types import ContentRegistry
from brain.tick import BrainState
from brain.tlica.builders import (
    make_msi,
    make_profile_with_cogito,
    make_ptcns,
)
from brain.tlica.profile import COGITO_ID
from brain.tlica.ptcns import ConsistencyEval
from brain.ui.snapshot import (
    ACTIVE_VIEWS,
    BrainSnapshot,
    DevelopmentSnapshot,
    build_brain_snapshot,
    build_development_snapshot,
)


# ---------------------------------------------------------------------------
# Deterministic fixture builders
# ---------------------------------------------------------------------------


def _make_state() -> BrainState:
    profile = make_profile_with_cogito({
        COGITO_ID: 1,
        "alpha": Fraction(3, 4),
        "beta": Fraction(1, 4),
    })
    msi = make_msi(
        profile,
        contents={COGITO_ID, "alpha"},
        threshold=Fraction(1, 2),
    )
    ptcns = make_ptcns(
        msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "alpha": ConsistencyEval.PRESERVE,
            "beta": ConsistencyEval.NEUTRAL,
        },
    )
    registry = ContentRegistry(
        texts=MappingProxyType({
            "alpha": "alpha text",
            "beta": "beta text",
        })
    )
    return BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)


def _make_output_history() -> OutputHistory:
    provenance = OutputProvenance(
        source_kind=FrameSourceKind.GENERATED,
        confidence=Fraction(4, 5),
        trace_event_ids=("snapshot-fixture:out",),
    )
    impulse = OutputImpulse(
        impulse_id="out-impulse:1",
        text="snapshot fixture impulse",
        provenance=provenance,
    )
    return OutputHistory(impulses=(impulse,))


def _make_worldlet_history() -> WorldletHistory:
    obj = WorldletObject(
        object_id="wld:obj-1",
        label="target",
        available=True,
        accepted_token_ids=(),
    )
    state = WorldletState(
        state_id="wld:state-1",
        objects={obj.object_id: obj},
        step_index=0,
    )
    return WorldletHistory(latest_state=state)


def _make_repl_history() -> ProtoBasicHistory:
    return ProtoBasicHistory()


# ---------------------------------------------------------------------------
# Identity / repr snapshot for the read-only assertion
# ---------------------------------------------------------------------------


def _snapshot_identity(state: BrainState) -> tuple:
    """Capture identity + repr of every kernel container reachable from ``state``."""
    return (
        id(state),
        repr(state),
        id(state.profile),
        repr(state.profile),
        id(state.profile.values),
        id(state.profile.domain),
        id(state.msi),
        repr(state.msi),
        id(state.msi.contents),
        id(state.ptcns),
        repr(state.ptcns),
        id(state.ptcns.eval_map),
        id(state.registry),
        repr(state.registry),
        id(state.registry.texts),
    )


# ---------------------------------------------------------------------------
# I-UI-01 — snapshot construction is read-only over kernel state.
# ---------------------------------------------------------------------------


@register("I-UI-01", status="REQUIRED")
def check_I_UI_01_snapshot_is_read_only_over_kernel_state() -> None:
    state = _make_state()
    out_history = _make_output_history()
    wld_history = _make_worldlet_history()
    repl_history = _make_repl_history()

    state_id_before = _snapshot_identity(state)
    out_repr_before = repr(out_history)
    wld_repr_before = repr(wld_history)
    repl_repr_before = repr(repl_history)
    out_id_before = id(out_history)
    wld_id_before = id(wld_history)
    repl_id_before = id(repl_history)

    brain_snap = build_brain_snapshot(state, latest_tick=None)
    dev_snap = build_development_snapshot(
        output_history=out_history,
        worldlet_history=wld_history,
        repl_history=repl_history,
    )

    assert isinstance(brain_snap, BrainSnapshot)
    assert isinstance(dev_snap, DevelopmentSnapshot)

    state_id_after = _snapshot_identity(state)
    assert state_id_after == state_id_before, (
        "I-UI-01 violated: BrainState identity/repr changed across snapshot"
    )
    assert id(out_history) == out_id_before and repr(out_history) == out_repr_before, (
        "I-UI-01 violated: OutputHistory mutated across snapshot"
    )
    assert id(wld_history) == wld_id_before and repr(wld_history) == wld_repr_before, (
        "I-UI-01 violated: WorldletHistory mutated across snapshot"
    )
    assert id(repl_history) == repl_id_before and repr(repl_history) == repl_repr_before, (
        "I-UI-01 violated: ProtoBasicHistory mutated across snapshot"
    )

    # Snapshotting the same state twice yields equal display values; the
    # underlying kernel objects are still untouched.
    brain_snap_again = build_brain_snapshot(state, latest_tick=None)
    assert brain_snap == brain_snap_again, (
        "I-UI-01 / I-UI-02 violated: repeated snapshot is not equal"
    )

    # Missing histories are tolerated without error: snapshot the same
    # state with ``None`` histories.
    dev_empty = build_development_snapshot()
    assert isinstance(dev_empty, DevelopmentSnapshot)
    assert dev_empty.output_impulse_count == 0
    assert dev_empty.worldlet_state_id is None
    assert dev_empty.repl_parse_count == 0

    # Content comparison: snapshot construction did not perturb the kernel
    # containers' values either.
    assert dict(state.profile.values) == {
        COGITO_ID: Fraction(1),
        "alpha": Fraction(3, 4),
        "beta": Fraction(1, 4),
    }
    assert state.msi.contents == frozenset({COGITO_ID, "alpha"})
    assert dict(state.ptcns.eval_map) == {
        COGITO_ID: ConsistencyEval.PRESERVE,
        "alpha": ConsistencyEval.PRESERVE,
        "beta": ConsistencyEval.NEUTRAL,
    }
    assert dict(state.registry.texts) == {
        "alpha": "alpha text",
        "beta": "beta text",
    }


# ---------------------------------------------------------------------------
# I-UI-08 — snapshot records are immutable display values.
# ---------------------------------------------------------------------------


def _assert_frozen(record: object, *, label: str) -> None:
    # frozen dataclass + slots=True: setattr on a declared field raises
    # FrozenInstanceError; setattr on an undeclared name raises
    # AttributeError because of slots. Either rejection counts as frozen.
    # Use a declared field name so we test the frozen-dataclass guard
    # specifically rather than only the slots guard.
    if hasattr(record, "active_view"):
        target_name = "active_view"
    else:
        target_name = next(iter(record.__dataclass_fields__))  # type: ignore[attr-defined]
    try:
        setattr(record, target_name, "MUTATED")
    except FrozenInstanceError:
        return
    except AttributeError:
        return
    raise AssertionError(
        f"I-UI-08 violated: {label} is not frozen (setattr succeeded)"
    )


@register("I-UI-08", status="STRUCTURAL")
def check_I_UI_08_snapshots_are_immutable_display_values() -> None:
    state = _make_state()
    out_history = _make_output_history()
    wld_history = _make_worldlet_history()
    repl_history = _make_repl_history()

    brain_snap = build_brain_snapshot(state, latest_tick=None)
    dev_snap = build_development_snapshot(
        output_history=out_history,
        worldlet_history=wld_history,
        repl_history=repl_history,
    )

    _assert_frozen(brain_snap, label="BrainSnapshot")
    _assert_frozen(dev_snap, label="DevelopmentSnapshot")

    # Every collection field on BrainSnapshot is an immutable display type.
    assert isinstance(brain_snap.profile_domain, tuple)
    assert all(isinstance(x, str) for x in brain_snap.profile_domain)
    assert isinstance(brain_snap.profile_values, tuple)
    for pair in brain_snap.profile_values:
        assert isinstance(pair, tuple) and len(pair) == 2
        assert isinstance(pair[0], str) and isinstance(pair[1], str)
        # Exact Fraction is rendered as a string, never as a float.
        assert "." not in pair[1] or pair[1] in {"0", "1"}, (
            f"I-UI-08 violated: profile value {pair[1]!r} looks like a float"
        )
    assert isinstance(brain_snap.msi_contents, frozenset)
    assert isinstance(brain_snap.msi_threshold, str)
    assert isinstance(brain_snap.eval_positive, frozenset)
    assert isinstance(brain_snap.eval_negative, frozenset)
    assert isinstance(brain_snap.eval_neutral, frozenset)
    assert isinstance(brain_snap.boundary_contents, frozenset)
    assert isinstance(brain_snap.registry_keys, tuple)
    assert isinstance(brain_snap.registry_entries, tuple)
    assert isinstance(brain_snap.latest_mode_trace, tuple)
    assert isinstance(brain_snap.latest_tick_notes, tuple)

    # Every field on DevelopmentSnapshot is either a bounded primitive or an
    # immutable tuple of bounded primitives.
    for name in (
        "output_impulse_count",
        "output_echo_count",
        "output_pattern_count",
        "output_token_candidate_count",
        "learned_output_token_count",
        "worldlet_attempt_count",
        "worldlet_response_count",
        "repl_parse_count",
        "repl_command_count",
        "repl_execution_count",
        "repl_feedback_count",
    ):
        value = getattr(dev_snap, name)
        assert isinstance(value, int) and value >= 0, (
            f"I-UI-08 violated: {name} must be a non-negative int (got {value!r})"
        )
    assert dev_snap.worldlet_state_id is None or isinstance(
        dev_snap.worldlet_state_id, str
    )
    assert dev_snap.worldlet_step_index is None or isinstance(
        dev_snap.worldlet_step_index, int
    )
    assert isinstance(dev_snap.worldlet_object_ids, tuple)
    assert all(isinstance(x, str) for x in dev_snap.worldlet_object_ids)
    assert isinstance(dev_snap.repl_emit_counts, tuple)
    for entry in dev_snap.repl_emit_counts:
        assert (
            isinstance(entry, tuple)
            and len(entry) == 2
            and isinstance(entry[0], str)
            and isinstance(entry[1], int)
        ), f"I-UI-08 violated: repl emit entry {entry!r} is not (str, int)"

    # ACTIVE_VIEWS is itself an immutable display contract.
    assert isinstance(ACTIVE_VIEWS, tuple)
    assert all(isinstance(name, str) and name for name in ACTIVE_VIEWS)
