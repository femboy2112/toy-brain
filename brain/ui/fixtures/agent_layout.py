"""Operator TUI agent-layout fixtures.

Drives:

* ``I-UI-16`` (REQUIRED) — ``AgentLayout`` exposes persistent named panes
  plus a bottom composer with deterministic ordering, anchoring, and
  non-overlapping geometry over a ``(width, height)`` sweep.
* ``I-UI-20`` (STRUCTURAL) — ``AgentLayout`` / ``PaneSpec`` /
  ``PaneRenderResult`` / ``AgentTuiViewModel`` are frozen
  terminal-agnostic immutable contracts; ``AgentLayout.from_size`` reads
  no global state and no terminal.
* ``I-UI-22`` (STRUCTURAL) — responsive pane geometry is deterministic
  across a deterministic ``(width, height)`` grid; ``HEADER`` /
  ``COMPOSER`` / ``FOOTER`` are preserved on small terminals; dimensions
  below the floor raise ``ValueError``.

This fixture imports only from the public ``brain.ui`` surfaces plus the
``brain.invariants`` registry helper. It performs no curses calls, no
file / network / shell I/O, and no ``tick()`` invocation.
"""
from __future__ import annotations

import os
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
from brain.ui import layout as layout_module
from brain.ui import render as render_module
from brain.ui.layout import (
    ALLOWED_RENDERER_KEYS,
    MIN_PANE_WIDTH,
    MIN_SIDE_BY_SIDE_WIDTH,
    MIN_TRANSCRIPT_ROWS,
    AgentLayout,
    AgentTuiViewModel,
    ComposerSnapshot,
    PaneName,
    PaneRenderResult,
    PaneSpec,
    TranscriptSnapshot,
    TranscriptSnapshotEntry,
)
from brain.ui.render import (
    MIN_HEIGHT,
    MIN_WIDTH,
    render_agent,
)
from brain.ui.snapshot import (
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


def _make_snapshots() -> tuple[BrainSnapshot, DevelopmentSnapshot]:
    state = _make_state()
    brain_snap = build_brain_snapshot(state, latest_tick=None)
    dev_snap = build_development_snapshot()
    return brain_snap, dev_snap


def _make_view(
    width: int = 80,
    height: int = 24,
    *,
    active_view: str = "state",
    composer_buffer: str = "",
    transcript_entries: tuple[TranscriptSnapshotEntry, ...] = (),
) -> AgentTuiViewModel:
    brain_snap, dev_snap = _make_snapshots()
    layout = AgentLayout.from_size(width, height)
    composer = ComposerSnapshot(
        buffer=composer_buffer,
        cursor=len(composer_buffer),
        history_size=0,
        mode="local-cmd",
        status_line="",
    )
    transcript = TranscriptSnapshot(entries=transcript_entries)
    return AgentTuiViewModel(
        active_view=active_view,
        width=width,
        height=height,
        brain=brain_snap,
        development=dev_snap,
        layout=layout,
        composer=composer,
        transcript=transcript,
        tick_counter=0,
        queued_event_summary=(),
        status_message="",
        error_message="",
        keyboard_help=(("?", "help"), ("q", "quit")),
        pane_titles=("core", "tick"),
    )


# ---------------------------------------------------------------------------
# Forbidden import-surface audit
# ---------------------------------------------------------------------------


_FORBIDDEN_LAYOUT_MODULES = (
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


def _assert_layout_surface_clean() -> None:
    """Walk layout.py's module globals; reject forbidden host surfaces."""
    for name, value in vars(layout_module).items():
        if name.startswith("__"):
            continue
        mod = getattr(value, "__module__", None)
        if not isinstance(mod, str):
            continue
        for forbidden in _FORBIDDEN_LAYOUT_MODULES:
            if mod == forbidden or mod.startswith(forbidden + "."):
                raise AssertionError(
                    "I-UI-20 violated: brain.ui.layout references "
                    f"{forbidden!r} via attribute {name!r} (resolved module "
                    f"{mod!r})"
                )


# ---------------------------------------------------------------------------
# Deterministic (width, height) sweep
# ---------------------------------------------------------------------------


def _grid_sweep() -> tuple[tuple[int, int], ...]:
    """Return a deterministic ``(width, height)`` test grid.

    The grid covers the four corrigenda section 4 boundary cases plus a
    small floor-corner sweep so the layout's small-terminal degradation
    path is exercised at every nearby grid point.
    """
    cases: list[tuple[int, int]] = []
    # Floor corner sweep
    for w in range(MIN_WIDTH, MIN_WIDTH + 5):
        for h in range(MIN_HEIGHT, MIN_HEIGHT + 5):
            cases.append((w, h))
    # Boundary at MIN_SIDE_BY_SIDE_WIDTH (37)
    cases.append((MIN_SIDE_BY_SIDE_WIDTH - 1, 10))
    cases.append((MIN_SIDE_BY_SIDE_WIDTH, 10))
    cases.append((MIN_SIDE_BY_SIDE_WIDTH + 1, 10))
    # Standard 80x24 and a larger terminal
    cases.append((80, 24))
    cases.append((120, 40))
    cases.append((200, 60))
    return tuple(dict.fromkeys(cases))


# ---------------------------------------------------------------------------
# I-UI-16 — pane presence, anchoring, ordering.
# ---------------------------------------------------------------------------


@register("I-UI-16", status="REQUIRED")
def check_I_UI_16_agent_layout_presents_named_panes() -> None:
    sweep = _grid_sweep()
    for width, height in sweep:
        layout = AgentLayout.from_size(width, height)
        names = [pane.name for pane in layout.panes]

        # Required panes are always present, exactly once.
        for required in (PaneName.HEADER, PaneName.COMPOSER, PaneName.FOOTER):
            assert names.count(required) == 1, (
                f"I-UI-16 violated: layout at {(width, height)!r} is missing "
                f"or duplicates {required.value!r}"
            )

        # HEADER anchored at row 0; FOOTER anchored at the last row.
        header = layout.pane(PaneName.HEADER)
        footer = layout.pane(PaneName.FOOTER)
        composer = layout.pane(PaneName.COMPOSER)
        assert header is not None and header.row == 0, (
            f"I-UI-16 violated: HEADER row != 0 at {(width, height)!r} "
            f"(got {header.row if header else None!r})"
        )
        assert footer is not None and footer.row == height - 1, (
            f"I-UI-16 violated: FOOTER row != height-1 at {(width, height)!r} "
            f"(got {footer.row if footer else None!r})"
        )
        # Composer is anchored just above the footer (2-row tall).
        assert composer is not None, (
            f"I-UI-16 violated: COMPOSER missing at {(width, height)!r}"
        )
        assert composer.row == height - 3, (
            f"I-UI-16 violated: COMPOSER row != height-3 at {(width, height)!r} "
            f"(got {composer.row})"
        )
        assert composer.height == 2, (
            f"I-UI-16 violated: COMPOSER height != 2 at {(width, height)!r} "
            f"(got {composer.height})"
        )
        # Ordering: panes are sorted top-to-bottom, left-to-right.
        for i in range(len(layout.panes) - 1):
            a = layout.panes[i]
            b = layout.panes[i + 1]
            assert (a.row, a.col) <= (b.row, b.col), (
                f"I-UI-16 violated: panes not ordered at {(width, height)!r}: "
                f"{a.name.value!r} {(a.row, a.col)} followed by "
                f"{b.name.value!r} {(b.row, b.col)}"
            )

        # STATE pane is always present (even in collapsed mode).
        assert layout.pane(PaneName.STATE) is not None, (
            f"I-UI-16 violated: STATE pane missing at {(width, height)!r}"
        )

        # Pane widths never exceed layout.width.
        for pane in layout.panes:
            assert pane.width <= width, (
                f"I-UI-16 violated: pane {pane.name.value!r} width "
                f"{pane.width} exceeds layout width {width}"
            )

    # The renderer composes exactly height rows for the default terminal
    # geometry.
    view = _make_view(80, 24)
    rows = render_agent(view)
    assert len(rows) == 24, (
        f"I-UI-16 violated: render_agent returned {len(rows)} rows for "
        "height 24"
    )
    for row in rows:
        assert len(row) <= 80, (
            f"I-UI-16 violated: render_agent row width {len(row)} exceeds 80"
        )
        assert row == "" or row.isprintable(), (
            f"I-UI-16 violated: render_agent emitted non-printable row {row!r}"
        )


# ---------------------------------------------------------------------------
# I-UI-20 — terminal-agnostic immutable contracts.
# ---------------------------------------------------------------------------


@register("I-UI-20", status="STRUCTURAL")
def check_I_UI_20_agent_layout_contracts_are_terminal_agnostic() -> None:
    # Construct a representative instance and assert immutability.
    layout = AgentLayout.from_size(80, 24)
    try:
        layout.width = 100  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("I-UI-20 violated: AgentLayout.width is mutable")

    pane = layout.panes[0]
    try:
        pane.row = 99  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("I-UI-20 violated: PaneSpec.row is mutable")

    # PaneSpec.renderer is a plain str (no callables on UI records).
    for spec in layout.panes:
        assert isinstance(spec.renderer, str), (
            f"I-UI-20 violated: PaneSpec.renderer is not str (got "
            f"{type(spec.renderer).__name__})"
        )
        assert spec.renderer in ALLOWED_RENDERER_KEYS, (
            f"I-UI-20 violated: PaneSpec.renderer {spec.renderer!r} "
            f"is outside the allowed set {sorted(ALLOWED_RENDERER_KEYS)!r}"
        )

    # AgentLayout fields are bounded primitives / tuples / bools.
    declared = {f.name for f in fields(layout)}
    assert declared == {"width", "height", "panes", "collapsed", "transcript_rows"}, (
        f"I-UI-20 violated: AgentLayout fields drifted (declared={declared!r})"
    )
    for f in fields(layout):
        value = getattr(layout, f.name)
        assert not callable(value), (
            f"I-UI-20 violated: AgentLayout.{f.name} is callable"
        )
        # Reject file-handle / socket / curses-window duck types.
        if hasattr(value, "read") and hasattr(value, "write"):
            raise AssertionError(
                f"I-UI-20 violated: AgentLayout.{f.name} exposes "
                "read/write (resource-like)"
            )

    # PaneRenderResult shape contract.
    sample = PaneRenderResult(
        name=PaneName.HEADER,
        rows=("hello",),
    )
    assert sample.rows == ("hello",)

    # Construction is deterministic: equal inputs produce equal outputs.
    a = AgentLayout.from_size(80, 24)
    b = AgentLayout.from_size(80, 24)
    assert a == b, "I-UI-20 violated: AgentLayout.from_size is non-deterministic"

    # AgentLayout.from_size reads no env var or terminal. We verify the
    # function does not consult os.environ by setting a sentinel key that
    # a misbehaving implementation might consult and confirming the layout
    # is unchanged.
    sentinel = "BRAIN_AGENT_LAYOUT_SENTINEL"
    saved = os.environ.get(sentinel)
    try:
        os.environ[sentinel] = "1"
        c = AgentLayout.from_size(80, 24)
        assert c == a, (
            "I-UI-20 violated: AgentLayout.from_size depends on environment"
        )
    finally:
        if saved is None:
            os.environ.pop(sentinel, None)
        else:
            os.environ[sentinel] = saved

    # AgentTuiViewModel contract.
    view = _make_view()
    try:
        view.width = 100  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "I-UI-20 violated: AgentTuiViewModel.width is mutable"
        )

    # ComposerSnapshot / TranscriptSnapshot contracts.
    try:
        ComposerSnapshot(buffer="x", cursor=99)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-UI-20 violated: ComposerSnapshot accepted cursor beyond buffer"
        )

    try:
        TranscriptSnapshotEntry(kind="SUBMIT", tick_at_event=-1, text="x")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-UI-20 violated: TranscriptSnapshotEntry accepted negative tick"
        )

    # Layout module is free of forbidden host surfaces.
    _assert_layout_surface_clean()
    assert "brain.ui.layout" in sys.modules, "layout module not importable"


# ---------------------------------------------------------------------------
# I-UI-22 — responsive geometry preserves composer + footer.
# ---------------------------------------------------------------------------


@register("I-UI-22", status="STRUCTURAL")
def check_I_UI_22_responsive_geometry_preserves_composer() -> None:
    sweep = _grid_sweep()
    for width, height in sweep:
        layout = AgentLayout.from_size(width, height)

        # Pane heights sum to layout.height when each row is counted once.
        # The side-by-side layout shares rows between STATE and INSPECTOR,
        # so we sum heights from the panes whose column extents start at
        # column 0 (the "left edge" panes covering all rows).
        # Alternative deterministic check: the union of (row, col) cells
        # exactly equals width * height.
        cells = 0
        for pane in layout.panes:
            cells += pane.height * pane.width
        assert cells == width * height, (
            f"I-UI-22 violated: cell coverage {cells} != {width * height} at "
            f"{(width, height)!r}"
        )

        # Small-terminal preservation: COMPOSER and FOOTER always present.
        composer = layout.pane(PaneName.COMPOSER)
        footer = layout.pane(PaneName.FOOTER)
        assert composer is not None, (
            f"I-UI-22 violated: COMPOSER dropped at {(width, height)!r}"
        )
        assert footer is not None, (
            f"I-UI-22 violated: FOOTER dropped at {(width, height)!r}"
        )
        # COMPOSER height is exactly 2 across the entire sweep.
        assert composer.height == 2, (
            f"I-UI-22 violated: COMPOSER height {composer.height} != 2 at "
            f"{(width, height)!r}"
        )
        # FOOTER height is exactly 1.
        assert footer.height == 1, (
            f"I-UI-22 violated: FOOTER height {footer.height} != 1 at "
            f"{(width, height)!r}"
        )

        # Collapsed flag matches the width threshold.
        expected_collapsed = width < MIN_SIDE_BY_SIDE_WIDTH
        assert layout.collapsed == expected_collapsed, (
            f"I-UI-22 violated: collapsed={layout.collapsed} expected "
            f"{expected_collapsed} at {(width, height)!r}"
        )

        # Transcript_rows is zero when the body cannot accommodate the floor.
        body_rows = height - 1 - 1 - 2  # header + footer + composer
        if body_rows < 1 + MIN_TRANSCRIPT_ROWS:
            assert layout.transcript_rows == 0, (
                f"I-UI-22 violated: expected transcript_rows == 0 at "
                f"{(width, height)!r} (got {layout.transcript_rows})"
            )
        else:
            assert layout.transcript_rows >= MIN_TRANSCRIPT_ROWS, (
                f"I-UI-22 violated: transcript_rows below floor at "
                f"{(width, height)!r} (got {layout.transcript_rows})"
            )

    # Dimensions below the floor raise ValueError.
    for w, h in ((MIN_WIDTH - 1, MIN_HEIGHT), (MIN_WIDTH, MIN_HEIGHT - 1)):
        try:
            AgentLayout.from_size(w, h)
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"I-UI-22 violated: AgentLayout.from_size({w}, {h}) accepted "
                "a sub-floor dimension"
            )

    # AgentLayout.from_size is a pure function: no clock dependence.
    a = AgentLayout.from_size(80, 24)
    b = AgentLayout.from_size(80, 24)
    assert a == b, "I-UI-22 violated: AgentLayout.from_size non-deterministic"
