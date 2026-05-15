"""Agent-style layout geometry for the Operator TUI.

This module defines the immutable ``AgentLayout`` geometry record, the
``PaneSpec`` per-pane bounding rectangle, the ``PaneName`` closed
enumeration of pane identities, and the ``PaneRenderResult`` /
``AgentTuiViewModel`` records used by the layout-aware pure renderer in
``brain.ui.render``.

The geometry is a **pure function** of ``(width, height)`` and a small set
of module-level constants. It reads no global state, no environment
variable, no terminal, no curses module, and no clock. The records
themselves are frozen dataclasses with slots; their fields are bounded
primitives, tuples of bounded primitives, or references to other frozen
records — no callables, file handles, sockets, real LLM clients, or
mutable references into ``BrainState`` or developmental histories.

Catalog rows driven from here:

* ``I-UI-16`` (REQUIRED) — ``AgentLayout`` exposes persistent named panes
  plus bottom composer.
* ``I-UI-20`` (STRUCTURAL) — ``AgentLayout`` / ``PaneSpec`` /
  ``AgentTuiViewModel`` are terminal-agnostic immutable contracts.
* ``I-UI-22`` (STRUCTURAL) — responsive pane geometry is deterministic
  and preserves a visible bottom composer on small terminals.

This module deliberately imports only from ``brain.ui.render`` (for the
``MIN_WIDTH`` / ``MIN_HEIGHT`` floor constants and the existing
``TuiViewModel`` it extends), ``brain.ui.snapshot`` (for the read-only
display snapshot types), and standard-library typing helpers. It does
not import ``curses``, ``brain.tick``, ``brain.llm``, or any module
from ``brain.tlica``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from brain.ui.render import MIN_HEIGHT, MIN_WIDTH
from brain.ui.snapshot import (
    ACTIVE_VIEWS,
    BrainSnapshot,
    DevelopmentSnapshot,
)


# ---------------------------------------------------------------------------
# Geometry floors and renderer keys
# ---------------------------------------------------------------------------


#: Minimum column count required for a side-by-side ``STATE`` / ``INSPECTOR``
#: layout. Below this threshold the body collapses vertically (single-column
#: stacked panes).
MIN_PANE_WIDTH: int = 18

#: Threshold at which the layout switches between collapsed (stacked) and
#: side-by-side panes. ``2 * MIN_PANE_WIDTH`` columns (no gutter; the current
#: pane geometry uses two contiguous panes whose column extents are
#: disjoint).
MIN_SIDE_BY_SIDE_WIDTH: int = 2 * MIN_PANE_WIDTH + 1

#: Minimum transcript rows preserved when the body has room for a transcript.
#: When the body is too small to hold both the inspector and the transcript
#: floor, the transcript collapses to zero rows but the composer and footer
#: panes remain visible.
MIN_TRANSCRIPT_ROWS: int = 2


class PaneName(str, Enum):
    """Closed enumeration of pane identities.

    The string value of each member is the renderer dispatch key used by
    ``PaneSpec.renderer``. Storing the enum as a ``str`` subclass keeps
    structural equality across the rendered output without coupling the
    renderer to an additional enum import.
    """

    HEADER = "header"
    STATE = "state"
    INSPECTOR = "inspector"
    TRANSCRIPT = "transcript"
    COMPOSER = "composer"
    FOOTER = "footer"


#: The closed set of renderer keys allowed on ``PaneSpec.renderer``. A
#: ``PaneSpec`` constructed with a key outside this set is rejected by
#: ``__post_init__``.
ALLOWED_RENDERER_KEYS: frozenset[str] = frozenset(p.value for p in PaneName)


# ---------------------------------------------------------------------------
# PaneSpec
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PaneSpec:
    """Immutable per-pane bounding rectangle.

    Fields:

    * ``name`` — closed enumeration of pane identities.
    * ``row``, ``col`` — top-left corner of the pane (0-based, inclusive).
    * ``height``, ``width`` — pane row / column counts (both ``>= 1``).
    * ``renderer`` — string key into the renderer dispatch table.

    Drives ``I-UI-20``: the record is frozen, the renderer field is a
    plain ``str`` (not a callable), and every field is a bounded
    primitive.
    """

    name: PaneName
    row: int
    col: int
    height: int
    width: int
    renderer: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, PaneName):
            raise TypeError(
                "PaneSpec.name must be a PaneName "
                f"(got {type(self.name).__name__})"
            )
        for label, value in (
            ("row", self.row),
            ("col", self.col),
            ("height", self.height),
            ("width", self.width),
        ):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(
                    f"PaneSpec.{label} must be int "
                    f"(got {type(value).__name__})"
                )
        if self.row < 0:
            raise ValueError(f"PaneSpec.row must be >= 0 (got {self.row!r})")
        if self.col < 0:
            raise ValueError(f"PaneSpec.col must be >= 0 (got {self.col!r})")
        if self.height < 1:
            raise ValueError(
                f"PaneSpec.height must be >= 1 (got {self.height!r})"
            )
        if self.width < 1:
            raise ValueError(
                f"PaneSpec.width must be >= 1 (got {self.width!r})"
            )
        if not isinstance(self.renderer, str):
            raise TypeError(
                "PaneSpec.renderer must be str "
                f"(got {type(self.renderer).__name__})"
            )
        if self.renderer not in ALLOWED_RENDERER_KEYS:
            raise ValueError(
                "I-UI-20 violated: PaneSpec.renderer "
                f"{self.renderer!r} is not in {sorted(ALLOWED_RENDERER_KEYS)!r}"
            )


# ---------------------------------------------------------------------------
# AgentLayout
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AgentLayout:
    """Immutable terminal-agnostic geometry derived from ``(width, height)``.

    The construction is total: ``AgentLayout.from_size(width, height)``
    raises ``ValueError`` for any ``(width, height) < (MIN_WIDTH,
    MIN_HEIGHT)``. For valid inputs the layout always carries a
    ``HEADER`` row, an inspector / state body region, an optional
    ``TRANSCRIPT`` band, a 2-row ``COMPOSER``, and a ``FOOTER`` row.
    The ``HEADER``, ``COMPOSER``, and ``FOOTER`` panes are always
    present; on small terminals the transcript may collapse to zero
    rows and the state/inspector split may stack vertically, but the
    composer is never dropped.

    Drives ``I-UI-16`` (pane presence) and ``I-UI-22`` (deterministic
    responsive geometry).
    """

    width: int
    height: int
    panes: tuple[PaneSpec, ...]
    collapsed: bool
    transcript_rows: int

    def __post_init__(self) -> None:
        if not isinstance(self.width, int) or self.width < MIN_WIDTH:
            raise ValueError(
                "AgentLayout.width must be an int >= "
                f"{MIN_WIDTH} (got {self.width!r})"
            )
        if not isinstance(self.height, int) or self.height < MIN_HEIGHT:
            raise ValueError(
                "AgentLayout.height must be an int >= "
                f"{MIN_HEIGHT} (got {self.height!r})"
            )
        if not isinstance(self.panes, tuple):
            raise TypeError(
                "AgentLayout.panes must be a tuple "
                f"(got {type(self.panes).__name__})"
            )
        names = []
        for pane in self.panes:
            if not isinstance(pane, PaneSpec):
                raise TypeError(
                    "AgentLayout.panes entries must be PaneSpec "
                    f"(got {type(pane).__name__})"
                )
            if pane.width > self.width:
                raise ValueError(
                    "I-UI-22 violated: PaneSpec.width "
                    f"{pane.width} exceeds layout.width {self.width}"
                )
            names.append(pane.name)
        # HEADER, COMPOSER, FOOTER are mandatory on every valid layout.
        for required in (PaneName.HEADER, PaneName.COMPOSER, PaneName.FOOTER):
            if required not in names:
                raise ValueError(
                    "I-UI-22 violated: AgentLayout missing required pane "
                    f"{required.value!r}"
                )
        if names.count(PaneName.HEADER) != 1:
            raise ValueError(
                "I-UI-22 violated: AgentLayout must contain exactly one HEADER"
            )
        if names.count(PaneName.COMPOSER) != 1:
            raise ValueError(
                "I-UI-22 violated: AgentLayout must contain exactly one COMPOSER"
            )
        if names.count(PaneName.FOOTER) != 1:
            raise ValueError(
                "I-UI-22 violated: AgentLayout must contain exactly one FOOTER"
            )
        # Composer is exactly 2 rows; header and footer are exactly 1 row.
        for pane in self.panes:
            if pane.name is PaneName.HEADER and pane.height != 1:
                raise ValueError(
                    f"I-UI-22 violated: HEADER height must be 1 (got {pane.height})"
                )
            if pane.name is PaneName.FOOTER and pane.height != 1:
                raise ValueError(
                    f"I-UI-22 violated: FOOTER height must be 1 (got {pane.height})"
                )
            if pane.name is PaneName.COMPOSER and pane.height != 2:
                raise ValueError(
                    f"I-UI-22 violated: COMPOSER height must be 2 (got {pane.height})"
                )
        # Pane heights must sum to layout.height. We sum across panes that
        # occupy distinct rows; STATE and INSPECTOR may share rows in the
        # side-by-side layout, so when they do we count their shared rows
        # only once. The structural property the row enforces is that every
        # row of the layout is covered by exactly one pane in any given
        # column.
        row_coverage = _row_coverage_for(self.panes, self.height, self.width)
        if any(c == 0 for c in row_coverage):
            raise ValueError(
                "I-UI-22 violated: AgentLayout leaves uncovered rows "
                f"(row_coverage={row_coverage!r})"
            )
        # Overlap check: every (row, col) cell belongs to exactly one pane.
        _assert_no_overlap(self.panes, self.height, self.width)
        if not isinstance(self.collapsed, bool):
            raise TypeError(
                "AgentLayout.collapsed must be bool "
                f"(got {type(self.collapsed).__name__})"
            )
        if not isinstance(self.transcript_rows, int) or self.transcript_rows < 0:
            raise ValueError(
                "AgentLayout.transcript_rows must be a non-negative int "
                f"(got {self.transcript_rows!r})"
            )

    @classmethod
    def from_size(cls, width: int, height: int) -> "AgentLayout":
        """Construct an :class:`AgentLayout` for a ``(width, height)`` terminal.

        Pure function: reads no global state, no environment variable,
        no terminal. For ``(width, height) < (MIN_WIDTH, MIN_HEIGHT)`` it
        raises ``ValueError`` matching the existing renderer contract.
        """
        if not isinstance(width, int) or isinstance(width, bool):
            raise TypeError(
                f"AgentLayout.from_size width must be int (got {type(width).__name__})"
            )
        if not isinstance(height, int) or isinstance(height, bool):
            raise TypeError(
                f"AgentLayout.from_size height must be int (got {type(height).__name__})"
            )
        if width < MIN_WIDTH:
            raise ValueError(
                f"AgentLayout.from_size: width {width} below floor {MIN_WIDTH}"
            )
        if height < MIN_HEIGHT:
            raise ValueError(
                f"AgentLayout.from_size: height {height} below floor {MIN_HEIGHT}"
            )

        # STEP A: header
        header = PaneSpec(
            name=PaneName.HEADER,
            row=0,
            col=0,
            height=1,
            width=width,
            renderer=PaneName.HEADER.value,
        )
        # STEP B: footer
        footer = PaneSpec(
            name=PaneName.FOOTER,
            row=height - 1,
            col=0,
            height=1,
            width=width,
            renderer=PaneName.FOOTER.value,
        )
        # STEP C: composer (always 2 rows just above the footer).
        composer = PaneSpec(
            name=PaneName.COMPOSER,
            row=height - 3,
            col=0,
            height=2,
            width=width,
            renderer=PaneName.COMPOSER.value,
        )

        # STEP D: body region between header and composer.
        body_top = 1
        body_bottom = height - 3  # exclusive (composer starts here)
        body_rows = body_bottom - body_top  # may be 0 at MIN_HEIGHT (= 6 - 3 - 1 = 2)
        if body_rows < 1:
            # Should be unreachable because height >= MIN_HEIGHT (6) guarantees
            # body_rows >= 2; keep a defensive guard so a future floor change
            # cannot silently produce a zero-row body.
            raise ValueError(
                "AgentLayout.from_size: body region has no rows "
                f"(height={height}, body_rows={body_rows})"
            )

        if body_rows < 1 + MIN_TRANSCRIPT_ROWS:
            # Degenerate: transcript collapses to 0 rows; state/inspector
            # consume the entire body. The composer and footer panes were
            # constructed above and survive this collapse.
            transcript_rows = 0
            inspector_rows = body_rows
        else:
            transcript_rows = max(MIN_TRANSCRIPT_ROWS, body_rows // 3)
            inspector_rows = body_rows - transcript_rows

        # STEP E: inspector split.
        body_panes: list[PaneSpec] = []
        if width >= MIN_SIDE_BY_SIDE_WIDTH:
            collapsed = False
            left_width = width // 2
            right_width = width - left_width
            body_panes.append(
                PaneSpec(
                    name=PaneName.STATE,
                    row=body_top,
                    col=0,
                    height=inspector_rows,
                    width=left_width,
                    renderer=PaneName.STATE.value,
                )
            )
            body_panes.append(
                PaneSpec(
                    name=PaneName.INSPECTOR,
                    row=body_top,
                    col=left_width,
                    height=inspector_rows,
                    width=right_width,
                    renderer=PaneName.INSPECTOR.value,
                )
            )
        else:
            collapsed = True
            # Single-column stacked. Split inspector_rows between STATE and
            # INSPECTOR; at the floor (inspector_rows == 2) each gets 1 row.
            state_rows = max(1, inspector_rows // 2)
            inspector_rows2 = inspector_rows - state_rows
            if inspector_rows2 < 1:
                # Defensive: at inspector_rows == 1 the layout would lose a
                # pane. We bias the floor toward STATE because the INSPECTOR
                # pane is otherwise empty until the operator picks a view.
                state_rows = inspector_rows
                inspector_rows2 = 0
            body_panes.append(
                PaneSpec(
                    name=PaneName.STATE,
                    row=body_top,
                    col=0,
                    height=state_rows,
                    width=width,
                    renderer=PaneName.STATE.value,
                )
            )
            if inspector_rows2 > 0:
                body_panes.append(
                    PaneSpec(
                        name=PaneName.INSPECTOR,
                        row=body_top + state_rows,
                        col=0,
                        height=inspector_rows2,
                        width=width,
                        renderer=PaneName.INSPECTOR.value,
                    )
                )

        # STEP F: transcript pane (only if transcript_rows > 0).
        transcript_pane: Optional[PaneSpec] = None
        if transcript_rows > 0:
            transcript_pane = PaneSpec(
                name=PaneName.TRANSCRIPT,
                row=body_bottom - transcript_rows,
                col=0,
                height=transcript_rows,
                width=width,
                renderer=PaneName.TRANSCRIPT.value,
            )

        ordered: list[PaneSpec] = [header]
        ordered.extend(body_panes)
        if transcript_pane is not None:
            ordered.append(transcript_pane)
        ordered.append(composer)
        ordered.append(footer)

        return cls(
            width=width,
            height=height,
            panes=tuple(ordered),
            collapsed=collapsed,
            transcript_rows=transcript_rows,
        )

    def pane(self, name: PaneName) -> Optional[PaneSpec]:
        """Return the :class:`PaneSpec` matching *name* if present."""
        for spec in self.panes:
            if spec.name is name:
                return spec
        return None


def _row_coverage_for(
    panes: tuple[PaneSpec, ...], height: int, width: int
) -> tuple[int, ...]:
    """Count how many cells of each row are covered by ``panes``.

    A row is "covered" when every column index in ``[0, width)`` belongs
    to at least one pane. We return the per-row coverage count (total
    cells covered on that row). The caller asserts that every row has at
    least one covered cell.
    """
    coverage = [0] * height
    for pane in panes:
        for r in range(pane.row, pane.row + pane.height):
            if 0 <= r < height:
                coverage[r] += pane.width
    return tuple(coverage)


def _assert_no_overlap(
    panes: tuple[PaneSpec, ...], height: int, width: int
) -> None:
    """Assert every ``(row, col)`` cell belongs to at most one pane.

    The check is O(rows * cols * panes) but the layout is bounded
    (``height <= ~200``, ``width <= ~400`` in realistic terminals) and
    the cost is paid only at construction time inside the fixture.
    """
    occupied: dict[tuple[int, int], PaneName] = {}
    for pane in panes:
        for r in range(pane.row, pane.row + pane.height):
            for c in range(pane.col, pane.col + pane.width):
                key = (r, c)
                if key in occupied:
                    raise ValueError(
                        "I-UI-22 violated: overlap at "
                        f"(row={r}, col={c}) between {occupied[key].value!r}"
                        f" and {pane.name.value!r}"
                    )
                occupied[key] = pane.name


# ---------------------------------------------------------------------------
# PaneRenderResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PaneRenderResult:
    """Per-pane renderer output.

    ``rows`` is exactly ``pane.height`` strings, each padded or truncated
    to ``pane.width``. Every row is bounded printable text. Drives
    ``I-UI-20``.
    """

    name: PaneName
    rows: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.name, PaneName):
            raise TypeError(
                "PaneRenderResult.name must be a PaneName "
                f"(got {type(self.name).__name__})"
            )
        if not isinstance(self.rows, tuple):
            raise TypeError(
                "PaneRenderResult.rows must be a tuple "
                f"(got {type(self.rows).__name__})"
            )
        for row in self.rows:
            if not isinstance(row, str):
                raise TypeError(
                    "PaneRenderResult.rows entries must be str "
                    f"(got {type(row).__name__})"
                )
            if row and not row.isprintable():
                raise ValueError(
                    "I-UI-20 violated: PaneRenderResult.rows entry is not "
                    f"printable ({row!r})"
                )


# ---------------------------------------------------------------------------
# ComposerSnapshot and TranscriptSnapshot — typed display projections.
# ---------------------------------------------------------------------------
#
# Steps 8 and 9 of the campaign land the runtime ``ComposerState`` and
# ``OperatorTranscript`` records. Step 7 (this step) introduces only the
# **display projection** that the layout-aware renderer needs so the
# ``AgentTuiViewModel`` contract can be enforced without depending on the
# yet-to-land composer / transcript modules. The snapshots below are pure
# data containers; the runtime composer / transcript will produce equivalent
# projections at frame-build time.


@dataclass(frozen=True, slots=True)
class ComposerSnapshot:
    """Immutable read-only projection of the bottom composer state.

    Fields:

    * ``buffer`` — printable text currently in the editor row.
    * ``cursor`` — column offset within ``buffer`` (``0 <= cursor <= len(buffer)``).
    * ``history_size`` — bounded count of submitted lines.
    * ``mode`` — composer mode tag (only ``"local-cmd"`` in this campaign).
    * ``status_line`` — bounded printable text shown on the composer meta row
      when the session status is empty.
    """

    buffer: str = ""
    cursor: int = 0
    history_size: int = 0
    mode: str = "local-cmd"
    status_line: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.buffer, str):
            raise TypeError(
                "ComposerSnapshot.buffer must be str "
                f"(got {type(self.buffer).__name__})"
            )
        if self.buffer and not self.buffer.isprintable():
            raise ValueError(
                "I-UI-20 violated: ComposerSnapshot.buffer must be printable "
                f"(got {self.buffer!r})"
            )
        if not isinstance(self.cursor, int) or self.cursor < 0:
            raise ValueError(
                "ComposerSnapshot.cursor must be a non-negative int "
                f"(got {self.cursor!r})"
            )
        if self.cursor > len(self.buffer):
            raise ValueError(
                "ComposerSnapshot.cursor exceeds buffer length "
                f"(cursor={self.cursor}, len(buffer)={len(self.buffer)})"
            )
        if not isinstance(self.history_size, int) or self.history_size < 0:
            raise ValueError(
                "ComposerSnapshot.history_size must be a non-negative int "
                f"(got {self.history_size!r})"
            )
        if not isinstance(self.mode, str) or not self.mode:
            raise ValueError(
                "ComposerSnapshot.mode must be a non-empty str "
                f"(got {self.mode!r})"
            )
        if not isinstance(self.status_line, str):
            raise TypeError(
                "ComposerSnapshot.status_line must be str "
                f"(got {type(self.status_line).__name__})"
            )
        if self.status_line and not self.status_line.isprintable():
            raise ValueError(
                "I-UI-20 violated: ComposerSnapshot.status_line must be "
                f"printable (got {self.status_line!r})"
            )


@dataclass(frozen=True, slots=True)
class TranscriptSnapshotEntry:
    """A single bounded transcript line for the agent layout renderer."""

    kind: str
    tick_at_event: int
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, str) or not self.kind:
            raise ValueError(
                "TranscriptSnapshotEntry.kind must be a non-empty str "
                f"(got {self.kind!r})"
            )
        if not isinstance(self.tick_at_event, int) or self.tick_at_event < 0:
            raise ValueError(
                "TranscriptSnapshotEntry.tick_at_event must be a non-negative int "
                f"(got {self.tick_at_event!r})"
            )
        if not isinstance(self.text, str):
            raise TypeError(
                "TranscriptSnapshotEntry.text must be str "
                f"(got {type(self.text).__name__})"
            )
        if self.text and not self.text.isprintable():
            raise ValueError(
                "I-UI-20 violated: TranscriptSnapshotEntry.text must be "
                f"printable (got {self.text!r})"
            )


@dataclass(frozen=True, slots=True)
class TranscriptSnapshot:
    """Immutable read-only projection of the operator transcript ring."""

    entries: tuple[TranscriptSnapshotEntry, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple):
            raise TypeError(
                "TranscriptSnapshot.entries must be a tuple "
                f"(got {type(self.entries).__name__})"
            )
        for entry in self.entries:
            if not isinstance(entry, TranscriptSnapshotEntry):
                raise TypeError(
                    "TranscriptSnapshot.entries items must be "
                    f"TranscriptSnapshotEntry (got {type(entry).__name__})"
                )


# ---------------------------------------------------------------------------
# AgentTuiViewModel
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AgentTuiViewModel:
    """Immutable terminal-agnostic input contract for the agent-style renderer.

    Extends the existing ``TuiViewModel`` shape with the new agent-layout
    fields (``layout``, ``composer``, ``transcript``, ``tick_counter``).
    All fields are bounded primitives, tuples of bounded printable
    strings, or references to other frozen records. No field is a
    curses object, file handle, socket, real LLM client, callable, or
    mutable reference into ``BrainState`` or developmental histories.

    Drives ``I-UI-20``.
    """

    active_view: str
    width: int
    height: int
    brain: BrainSnapshot
    development: DevelopmentSnapshot
    layout: AgentLayout
    composer: ComposerSnapshot
    transcript: TranscriptSnapshot
    tick_counter: int = 0
    queued_event_summary: tuple[str, ...] = ()
    status_message: str = ""
    error_message: str = ""
    keyboard_help: tuple[tuple[str, str], ...] = ()
    pane_titles: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.active_view, str):
            raise TypeError(
                "AgentTuiViewModel.active_view must be str "
                f"(got {type(self.active_view).__name__})"
            )
        if self.active_view not in ACTIVE_VIEWS:
            raise ValueError(
                "I-UI-20 violated: AgentTuiViewModel.active_view "
                f"{self.active_view!r} is not in the closed enumeration "
                f"{ACTIVE_VIEWS!r}"
            )
        if not isinstance(self.width, int) or self.width < MIN_WIDTH:
            raise ValueError(
                "AgentTuiViewModel.width must be an int >= "
                f"{MIN_WIDTH} (got {self.width!r})"
            )
        if not isinstance(self.height, int) or self.height < MIN_HEIGHT:
            raise ValueError(
                "AgentTuiViewModel.height must be an int >= "
                f"{MIN_HEIGHT} (got {self.height!r})"
            )
        if not isinstance(self.brain, BrainSnapshot):
            raise TypeError(
                "AgentTuiViewModel.brain must be a BrainSnapshot "
                f"(got {type(self.brain).__name__})"
            )
        if not isinstance(self.development, DevelopmentSnapshot):
            raise TypeError(
                "AgentTuiViewModel.development must be a DevelopmentSnapshot "
                f"(got {type(self.development).__name__})"
            )
        if not isinstance(self.layout, AgentLayout):
            raise TypeError(
                "AgentTuiViewModel.layout must be an AgentLayout "
                f"(got {type(self.layout).__name__})"
            )
        if self.layout.width != self.width or self.layout.height != self.height:
            raise ValueError(
                "I-UI-20 violated: AgentTuiViewModel.layout size "
                f"({self.layout.width}, {self.layout.height}) does not match "
                f"view size ({self.width}, {self.height})"
            )
        if not isinstance(self.composer, ComposerSnapshot):
            raise TypeError(
                "AgentTuiViewModel.composer must be a ComposerSnapshot "
                f"(got {type(self.composer).__name__})"
            )
        if not isinstance(self.transcript, TranscriptSnapshot):
            raise TypeError(
                "AgentTuiViewModel.transcript must be a TranscriptSnapshot "
                f"(got {type(self.transcript).__name__})"
            )
        if not isinstance(self.tick_counter, int) or self.tick_counter < 0:
            raise ValueError(
                "AgentTuiViewModel.tick_counter must be a non-negative int "
                f"(got {self.tick_counter!r})"
            )
        for label, value in (
            ("queued_event_summary", self.queued_event_summary),
            ("pane_titles", self.pane_titles),
        ):
            if not isinstance(value, tuple):
                raise TypeError(
                    f"AgentTuiViewModel.{label} must be a tuple "
                    f"(got {type(value).__name__})"
                )
            for line in value:
                if not isinstance(line, str) or not line.isprintable():
                    raise ValueError(
                        f"AgentTuiViewModel.{label} entries must be printable "
                        f"strings (got {line!r})"
                    )
        for label, value in (
            ("status_message", self.status_message),
            ("error_message", self.error_message),
        ):
            if not isinstance(value, str):
                raise TypeError(
                    f"AgentTuiViewModel.{label} must be str "
                    f"(got {type(value).__name__})"
                )
            if value and not value.isprintable():
                raise ValueError(
                    f"AgentTuiViewModel.{label} must be printable text "
                    f"(got {value!r})"
                )
        if not isinstance(self.keyboard_help, tuple):
            raise TypeError(
                "AgentTuiViewModel.keyboard_help must be a tuple of "
                "(key, description) pairs"
            )
        for entry in self.keyboard_help:
            if (
                not isinstance(entry, tuple)
                or len(entry) != 2
                or not isinstance(entry[0], str)
                or not isinstance(entry[1], str)
            ):
                raise TypeError(
                    "AgentTuiViewModel.keyboard_help entries must be "
                    "(str, str) tuples"
                )


__all__ = [
    "MIN_PANE_WIDTH",
    "MIN_SIDE_BY_SIDE_WIDTH",
    "MIN_TRANSCRIPT_ROWS",
    "PaneName",
    "ALLOWED_RENDERER_KEYS",
    "PaneSpec",
    "AgentLayout",
    "PaneRenderResult",
    "ComposerSnapshot",
    "TranscriptSnapshotEntry",
    "TranscriptSnapshot",
    "AgentTuiViewModel",
]
