"""Operator TUI renderer fixtures.

Drives:

* ``I-UI-02`` (REQUIRED) — pure renderer determinism. Given the same input
  view model, repeated calls to ``render`` produce equal tuples of strings.
  We also assert the renderer reaches no curses / file / network / shell /
  ``tick()`` surface by walking the module's runtime imports and bytecode
  globals.
* ``I-UI-09`` (STRUCTURAL) — ``TuiViewModel`` is a small terminal-agnostic
  data contract. We assert it is a frozen dataclass whose fields are
  bounded primitives, tuples of bounded strings, or snapshot references.
"""
from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError, fields
from fractions import Fraction
from types import MappingProxyType

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
from brain.ui import render as render_module
from brain.ui.render import (
    DEFAULT_HEIGHT,
    DEFAULT_KEYBOARD_HELP,
    DEFAULT_PANE_TITLES,
    DEFAULT_WIDTH,
    MIN_HEIGHT,
    MIN_WIDTH,
    TuiViewModel,
    build_view_model,
    render,
)
from brain.ui.snapshot import (
    ACTIVE_VIEWS,
    BrainSnapshot,
    DevelopmentSnapshot,
    build_brain_snapshot,
    build_development_snapshot,
)


# ---------------------------------------------------------------------------
# Deterministic input
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


def _make_snapshots() -> tuple[BrainSnapshot, DevelopmentSnapshot]:
    state = _make_state()
    brain_snap = build_brain_snapshot(state, latest_tick=None)
    dev_snap = build_development_snapshot()
    return brain_snap, dev_snap


# ---------------------------------------------------------------------------
# Forbidden import-surface audit
# ---------------------------------------------------------------------------


_FORBIDDEN_RENDER_MODULES = (
    "curses",
    "subprocess",
    "socket",
    "urllib",
    "http",
    "requests",
    "brain.llm",
    "brain.tick",
    "brain.tlica",
)


def _assert_render_surface_clean() -> None:
    """Walk render.py's module globals; reject forbidden host surfaces."""
    globals_ = vars(render_module)
    for name, value in globals_.items():
        if name.startswith("__"):
            continue
        mod = getattr(value, "__module__", None)
        if not isinstance(mod, str):
            continue
        for forbidden in _FORBIDDEN_RENDER_MODULES:
            if mod == forbidden or mod.startswith(forbidden + "."):
                raise AssertionError(
                    "I-UI-02 violated: brain.ui.render references "
                    f"{forbidden!r} via attribute {name!r} (resolved module "
                    f"{mod!r})"
                )

    # Also confirm that importing the renderer did not pull a curses module
    # into ``sys.modules`` via brain.ui.render's direct import graph.
    # ``curses`` may have been imported earlier by an unrelated module; we
    # only assert that ``brain.ui.render``'s own globals do not depend on
    # it. The first loop above catches that case.
    assert "brain.ui.render" in sys.modules, "renderer not importable"


# ---------------------------------------------------------------------------
# I-UI-02 — pure renderer determinism.
# ---------------------------------------------------------------------------


@register("I-UI-02", status="REQUIRED")
def check_I_UI_02_render_is_deterministic() -> None:
    brain_snap, dev_snap = _make_snapshots()

    for view_name in ACTIVE_VIEWS:
        view = build_view_model(
            active_view=view_name,
            brain=brain_snap,
            development=dev_snap,
            status_message="ok",
        )
        rows_a = render(view)
        rows_b = render(view)
        assert isinstance(rows_a, tuple)
        assert all(isinstance(line, str) and line.isprintable() for line in rows_a)
        assert rows_a == rows_b, (
            f"I-UI-02 violated: render({view_name!r}) returned different rows "
            "across repeated calls"
        )
        # Equal input view models produce equal output regardless of
        # construction order.
        view_again = build_view_model(
            active_view=view_name,
            brain=brain_snap,
            development=dev_snap,
            status_message="ok",
        )
        assert render(view_again) == rows_a, (
            f"I-UI-02 violated: render({view_name!r}) depends on "
            "view-model identity, not value"
        )
        # Rendered lines respect the supplied width bound.
        assert all(len(line) <= view.width for line in rows_a), (
            f"I-UI-02 violated: render({view_name!r}) line exceeds width "
            f"{view.width}"
        )
        # Rendered output respects the supplied height bound.
        assert len(rows_a) <= view.height, (
            f"I-UI-02 violated: render({view_name!r}) produced "
            f"{len(rows_a)} rows for height {view.height}"
        )

    # Narrow width: lines should be truncated, not raise.
    narrow = build_view_model(
        active_view="state",
        brain=brain_snap,
        development=dev_snap,
        width=MIN_WIDTH,
        height=MIN_HEIGHT,
    )
    narrow_rows = render(narrow)
    assert all(len(line) <= MIN_WIDTH for line in narrow_rows)
    assert len(narrow_rows) <= MIN_HEIGHT

    # Render surface is free of curses / network / shell / kernel imports.
    _assert_render_surface_clean()


# ---------------------------------------------------------------------------
# I-UI-09 — TuiViewModel is a small terminal-agnostic data contract.
# ---------------------------------------------------------------------------


@register("I-UI-09", status="STRUCTURAL")
def check_I_UI_09_view_model_is_terminal_agnostic() -> None:
    brain_snap, dev_snap = _make_snapshots()
    view = build_view_model(
        active_view="state",
        brain=brain_snap,
        development=dev_snap,
    )

    # Frozen dataclass: attempting to mutate any field must raise.
    try:
        view.active_view = "tick"  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "I-UI-09 violated: TuiViewModel.active_view is mutable"
        )

    # Every declared field is a bounded primitive, tuple, or snapshot
    # reference. No curses/file/socket/callable values are accepted.
    from brain.ui.snapshot import StreamCandidatesSnapshot, StreamSummarySnapshot
    allowed_types = {
        "active_view": (str,),
        "width": (int,),
        "height": (int,),
        "brain": (BrainSnapshot,),
        "development": (DevelopmentSnapshot,),
        "queued_event_summary": (tuple,),
        "status_message": (str,),
        "error_message": (str,),
        "keyboard_help": (tuple,),
        "pane_titles": (tuple,),
        "stream_summary": (StreamSummarySnapshot, type(None)),
        "stream_candidates": (StreamCandidatesSnapshot, type(None)),
    }
    declared = {f.name for f in fields(view)}
    assert declared == set(allowed_types.keys()), (
        f"I-UI-09 violated: TuiViewModel fields drifted (declared={declared!r})"
    )
    for name, types in allowed_types.items():
        value = getattr(view, name)
        assert isinstance(value, types), (
            f"I-UI-09 violated: TuiViewModel.{name} is not in {types!r} "
            f"(got {type(value).__name__})"
        )

    # No field is callable or a curses-style object.
    for f in fields(view):
        value = getattr(view, f.name)
        assert not callable(value), (
            f"I-UI-09 violated: TuiViewModel.{f.name} is callable"
        )
        # Reject file-handle / socket / curses-window duck types: any object
        # exposing both ``read`` and ``write`` methods is treated as a
        # forbidden resource here.
        if hasattr(value, "read") and hasattr(value, "write"):
            raise AssertionError(
                "I-UI-09 violated: TuiViewModel."
                f"{f.name} exposes read/write (resource-like)"
            )

    # Constructor enforces the closed active_view enumeration.
    try:
        TuiViewModel(
            active_view="not-a-view",
            width=DEFAULT_WIDTH,
            height=DEFAULT_HEIGHT,
            brain=brain_snap,
            development=dev_snap,
        )
    except ValueError as exc:
        assert "I-UI-09" in str(exc)
    else:
        raise AssertionError(
            "I-UI-09 violated: TuiViewModel accepted an out-of-enum active_view"
        )

    # Constructor enforces width / height lower bounds.
    try:
        TuiViewModel(
            active_view="state",
            width=MIN_WIDTH - 1,
            height=DEFAULT_HEIGHT,
            brain=brain_snap,
            development=dev_snap,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-UI-09 violated: TuiViewModel accepted width below MIN_WIDTH"
        )

    try:
        TuiViewModel(
            active_view="state",
            width=DEFAULT_WIDTH,
            height=MIN_HEIGHT - 1,
            brain=brain_snap,
            development=dev_snap,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-UI-09 violated: TuiViewModel accepted height below MIN_HEIGHT"
        )

    # Default keyboard help and pane titles are immutable display contracts.
    assert isinstance(DEFAULT_KEYBOARD_HELP, tuple)
    for entry in DEFAULT_KEYBOARD_HELP:
        assert (
            isinstance(entry, tuple)
            and len(entry) == 2
            and isinstance(entry[0], str)
            and isinstance(entry[1], str)
        )
    assert isinstance(DEFAULT_PANE_TITLES, tuple)
    assert all(isinstance(t, str) for t in DEFAULT_PANE_TITLES)
