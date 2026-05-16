"""Pure Operator TUI renderer.

This module is the deterministic, terminal-agnostic renderer. Given the same
``TuiViewModel`` (or snapshot bundle + active view + width + height) the
public ``render`` function returns equal display rows across repeated calls;
it does not call ``tick()``, does not touch curses, and does not perform
file / network / shell I/O.

Catalog rows driven from here:

* ``I-UI-02`` — pure renderer determinism (REQUIRED).
* ``I-UI-09`` — ``TuiViewModel`` is a small terminal-agnostic data contract
  (STRUCTURAL).

This module deliberately imports only from ``brain.ui.snapshot``; it does not
import ``curses``, ``brain.tick``, ``brain.llm``, or any module from
``brain.tlica``. The renderer never opens a file, a socket, or a subprocess.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from brain.ui.snapshot import (
    ACTIVE_VIEWS,
    EMPTY_DISPLAY,
    BrainSnapshot,
    DevelopmentSnapshot,
    StreamCandidatesSnapshot,
    StreamSummarySnapshot,
)


# ---------------------------------------------------------------------------
# Layout bounds
# ---------------------------------------------------------------------------


DEFAULT_WIDTH = 80
DEFAULT_HEIGHT = 24
MIN_WIDTH = 20
MIN_HEIGHT = 6


# ---------------------------------------------------------------------------
# TuiViewModel — terminal-agnostic data contract
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TuiViewModel:
    """Immutable terminal-agnostic input contract for the pure renderer.

    All fields are bounded primitives, tuples of bounded printable strings,
    or snapshot references. No field is a curses object, file handle,
    socket, real LLM client, callable, or mutable reference into
    ``BrainState`` / developmental histories.

    Drives ``I-UI-09``.
    """

    active_view: str
    width: int
    height: int
    brain: BrainSnapshot
    development: DevelopmentSnapshot
    queued_event_summary: tuple[str, ...] = ()
    status_message: str = ""
    error_message: str = ""
    keyboard_help: tuple[tuple[str, str], ...] = ()
    pane_titles: tuple[str, ...] = ()
    stream_summary: Optional[StreamSummarySnapshot] = None
    stream_candidates: Optional[StreamCandidatesSnapshot] = None

    def __post_init__(self) -> None:
        if not isinstance(self.active_view, str):
            raise TypeError(
                "TuiViewModel.active_view must be str "
                f"(got {type(self.active_view).__name__})"
            )
        if self.active_view not in ACTIVE_VIEWS:
            raise ValueError(
                "I-UI-09 violated: TuiViewModel.active_view "
                f"{self.active_view!r} is not in the closed enumeration "
                f"{ACTIVE_VIEWS!r}"
            )
        if not isinstance(self.width, int) or self.width < MIN_WIDTH:
            raise ValueError(
                "TuiViewModel.width must be an int >= "
                f"{MIN_WIDTH} (got {self.width!r})"
            )
        if not isinstance(self.height, int) or self.height < MIN_HEIGHT:
            raise ValueError(
                "TuiViewModel.height must be an int >= "
                f"{MIN_HEIGHT} (got {self.height!r})"
            )
        if not isinstance(self.brain, BrainSnapshot):
            raise TypeError(
                "TuiViewModel.brain must be a BrainSnapshot "
                f"(got {type(self.brain).__name__})"
            )
        if not isinstance(self.development, DevelopmentSnapshot):
            raise TypeError(
                "TuiViewModel.development must be a DevelopmentSnapshot "
                f"(got {type(self.development).__name__})"
            )
        for label, value in (
            ("queued_event_summary", self.queued_event_summary),
            ("pane_titles", self.pane_titles),
        ):
            if not isinstance(value, tuple):
                raise TypeError(
                    f"TuiViewModel.{label} must be a tuple "
                    f"(got {type(value).__name__})"
                )
            for line in value:
                if not isinstance(line, str) or not line.isprintable():
                    raise ValueError(
                        f"TuiViewModel.{label} entries must be printable "
                        f"strings (got {line!r})"
                    )
        for label, value in (
            ("status_message", self.status_message),
            ("error_message", self.error_message),
        ):
            if not isinstance(value, str):
                raise TypeError(
                    f"TuiViewModel.{label} must be str "
                    f"(got {type(value).__name__})"
                )
            # Empty string is allowed (no status / no error); otherwise the
            # text must be printable so the renderer can place it directly.
            if value and not value.isprintable():
                raise ValueError(
                    f"TuiViewModel.{label} must be printable text "
                    f"(got {value!r})"
                )
        if not isinstance(self.keyboard_help, tuple):
            raise TypeError(
                "TuiViewModel.keyboard_help must be a tuple of "
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
                    "TuiViewModel.keyboard_help entries must be "
                    "(str, str) tuples"
                )
        if self.stream_summary is not None and not isinstance(
            self.stream_summary, StreamSummarySnapshot
        ):
            raise TypeError(
                "TuiViewModel.stream_summary must be a StreamSummarySnapshot "
                "or None"
            )
        if self.stream_candidates is not None and not isinstance(
            self.stream_candidates, StreamCandidatesSnapshot
        ):
            raise TypeError(
                "TuiViewModel.stream_candidates must be a "
                "StreamCandidatesSnapshot or None"
            )


# ---------------------------------------------------------------------------
# View-model construction helpers
# ---------------------------------------------------------------------------


DEFAULT_PANE_TITLES: tuple[str, ...] = (
    "core state",
    "latest tick",
    "output history",
    "worldlet history",
    "repl history",
    "queued event",
    "status / error",
    "help",
)


DEFAULT_KEYBOARD_HELP: tuple[tuple[str, str], ...] = (
    ("s", "inspect kernel state"),
    ("t", "inspect latest tick"),
    ("o", "inspect output history"),
    ("w", "inspect worldlet history"),
    ("r", "inspect repl history"),
    ("p", "inspect queued percept event"),
    ("e", "queue percept event"),
    ("space", "step tick"),
    ("c", "clear status / error"),
    ("?", "help"),
    ("q", "quit"),
)


def build_view_model(
    *,
    active_view: str,
    brain: BrainSnapshot,
    development: DevelopmentSnapshot,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    queued_event_summary: tuple[str, ...] = (),
    status_message: str = "",
    error_message: str = "",
    keyboard_help: Optional[tuple[tuple[str, str], ...]] = None,
    pane_titles: Optional[tuple[str, ...]] = None,
    stream_summary: Optional[StreamSummarySnapshot] = None,
    stream_candidates: Optional[StreamCandidatesSnapshot] = None,
) -> TuiViewModel:
    """Helper: build a ``TuiViewModel`` with the default keyboard help / panes.

    Construction is total: invalid inputs raise via ``TuiViewModel.__post_init__``
    rather than silently producing a partial record.
    """
    return TuiViewModel(
        active_view=active_view,
        width=int(width),
        height=int(height),
        brain=brain,
        development=development,
        queued_event_summary=tuple(queued_event_summary),
        status_message=status_message,
        error_message=error_message,
        keyboard_help=DEFAULT_KEYBOARD_HELP if keyboard_help is None else keyboard_help,
        pane_titles=DEFAULT_PANE_TITLES if pane_titles is None else pane_titles,
        stream_summary=stream_summary,
        stream_candidates=stream_candidates,
    )


# ---------------------------------------------------------------------------
# Pure renderer
# ---------------------------------------------------------------------------


def _truncate(line: str, width: int) -> str:
    """Bound a single line at the supplied width; preserve printability."""
    if len(line) <= width:
        return line
    if width <= 1:
        return line[:width]
    return line[: width - 1] + "…"  # horizontal ellipsis


def _frame_header(title: str, width: int) -> str:
    label = f"[ {title} ]"
    if len(label) >= width:
        return _truncate(label, width)
    pad = "-" * (width - len(label))
    return label + pad


def _format_pairs(pairs: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    if not pairs:
        return (EMPTY_DISPLAY,)
    return tuple(f"{k} = {v}" for k, v in pairs)


def _render_state(view: TuiViewModel) -> tuple[str, ...]:
    b = view.brain
    lines: list[str] = []
    lines.append(_frame_header("core state", view.width))
    lines.append(f"profile domain size : {len(b.profile_domain)}")
    if b.profile_values:
        lines.append("profile values:")
        for cid, value in b.profile_values:
            lines.append(f"  {cid} = {value}")
    else:
        lines.append("profile values: " + EMPTY_DISPLAY)
    lines.append(
        f"msi contents (n={len(b.msi_contents)}): "
        + (", ".join(sorted(b.msi_contents)) or EMPTY_DISPLAY)
    )
    lines.append(f"msi threshold : {b.msi_threshold}")
    lines.append(
        "eval positive : "
        + (", ".join(sorted(b.eval_positive)) or EMPTY_DISPLAY)
    )
    lines.append(
        "eval negative : "
        + (", ".join(sorted(b.eval_negative)) or EMPTY_DISPLAY)
    )
    lines.append(
        "eval neutral  : "
        + (", ".join(sorted(b.eval_neutral)) or EMPTY_DISPLAY)
    )
    lines.append(
        "boundary      : "
        + (", ".join(sorted(b.boundary_contents)) or EMPTY_DISPLAY)
    )
    if b.registry_entries:
        lines.append("registry:")
        for cid, text in b.registry_entries:
            lines.append(f"  {cid} -> {text}")
    else:
        lines.append("registry: " + EMPTY_DISPLAY)
    return tuple(lines)


def _render_tick(view: TuiViewModel) -> tuple[str, ...]:
    b = view.brain
    lines: list[str] = []
    lines.append(_frame_header("latest tick", view.width))
    if b.latest_tick_index is None:
        lines.append(EMPTY_DISPLAY)
        return tuple(lines)
    lines.append(f"tick index    : {b.latest_tick_index}")
    lines.append(
        "mode trace    : "
        + (", ".join(b.latest_mode_trace) or EMPTY_DISPLAY)
    )
    lines.append(
        "triggered mode: "
        + (b.latest_triggered_mode if b.latest_triggered_mode else EMPTY_DISPLAY)
    )
    if b.latest_tick_notes:
        lines.append("notes:")
        for note in b.latest_tick_notes:
            lines.append(f"  {note}")
    else:
        lines.append("notes: " + EMPTY_DISPLAY)
    return tuple(lines)


def _render_output(view: TuiViewModel) -> tuple[str, ...]:
    d = view.development
    lines: list[str] = []
    lines.append(_frame_header("output history", view.width))
    lines.append(f"impulses        : {d.output_impulse_count}")
    lines.append(f"echoes          : {d.output_echo_count}")
    lines.append(f"patterns        : {d.output_pattern_count}")
    lines.append(f"token candidates: {d.output_token_candidate_count}")
    lines.append(f"learned tokens  : {d.learned_output_token_count}")
    return tuple(lines)


def _render_worldlet(view: TuiViewModel) -> tuple[str, ...]:
    d = view.development
    lines: list[str] = []
    lines.append(_frame_header("worldlet history", view.width))
    if d.worldlet_state_id is None:
        lines.append(EMPTY_DISPLAY)
        return tuple(lines)
    lines.append(f"latest state    : {d.worldlet_state_id}")
    lines.append(f"step index      : {d.worldlet_step_index}")
    lines.append(f"attempts        : {d.worldlet_attempt_count}")
    lines.append(f"responses       : {d.worldlet_response_count}")
    lines.append(
        "objects         : "
        + (", ".join(d.worldlet_object_ids) or EMPTY_DISPLAY)
    )
    return tuple(lines)


def _render_repl(view: TuiViewModel) -> tuple[str, ...]:
    d = view.development
    lines: list[str] = []
    lines.append(_frame_header("repl history", view.width))
    lines.append(f"parse results   : {d.repl_parse_count}")
    lines.append(f"commands        : {d.repl_command_count}")
    lines.append(f"executions      : {d.repl_execution_count}")
    lines.append(f"feedback        : {d.repl_feedback_count}")
    if d.repl_emit_counts:
        lines.append("emit counts:")
        for form, count in d.repl_emit_counts:
            lines.append(f"  {form} = {count}")
    else:
        lines.append("emit counts: " + EMPTY_DISPLAY)
    return tuple(lines)


def _render_queue(view: TuiViewModel) -> tuple[str, ...]:
    lines: list[str] = []
    lines.append(_frame_header("queued event", view.width))
    if view.queued_event_summary:
        lines.extend(view.queued_event_summary)
    else:
        lines.append(EMPTY_DISPLAY)
    return tuple(lines)


def _render_status(view: TuiViewModel) -> tuple[str, ...]:
    lines: list[str] = []
    lines.append(_frame_header("status / error", view.width))
    lines.append("status: " + (view.status_message or EMPTY_DISPLAY))
    lines.append("error : " + (view.error_message or EMPTY_DISPLAY))
    return tuple(lines)


def _render_help(view: TuiViewModel) -> tuple[str, ...]:
    lines: list[str] = []
    lines.append(_frame_header("help", view.width))
    if not view.keyboard_help:
        lines.append(EMPTY_DISPLAY)
        return tuple(lines)
    for key, description in view.keyboard_help:
        lines.append(f"  {key:7s} {description}")
    return tuple(lines)


def _render_stream_summary(view: TuiViewModel) -> tuple[str, ...]:
    lines: list[str] = []
    lines.append(_frame_header("stream summary", view.width))
    summary = view.stream_summary
    if summary is None:
        lines.append(EMPTY_DISPLAY)
        return tuple(lines)
    lines.append(
        f"chunks          : {summary.chunk_count} / {summary.history_capacity}"
    )
    lines.append(f"total length    : {summary.total_text_length}")
    lines.append(f"distinct ids    : {summary.distinct_chunk_ids}")
    if summary.source_counts:
        lines.append("by source:")
        for name, count in summary.source_counts:
            lines.append(f"  {name} = {count}")
    else:
        lines.append("by source: " + EMPTY_DISPLAY)
    lines.append(
        "latest chunk    : "
        + (summary.latest_chunk_id if summary.latest_chunk_id else EMPTY_DISPLAY)
    )
    if summary.latest_chunk_text_preview:
        lines.append(f"latest preview  : {summary.latest_chunk_text_preview}")
    return tuple(lines)


def _render_stream_candidates(view: TuiViewModel) -> tuple[str, ...]:
    lines: list[str] = []
    lines.append(_frame_header("stream candidates", view.width))
    candidates = view.stream_candidates
    if candidates is None or not candidates.candidates:
        lines.append(EMPTY_DISPLAY)
        if candidates is not None:
            lines.append(
                f"capacity        : {candidates.candidate_capacity}"
            )
        return tuple(lines)
    lines.append(
        f"candidates      : "
        f"{candidates.candidate_count} / {candidates.candidate_capacity}"
    )
    for snapshot in candidates.candidates:
        lines.append(f"  {snapshot.candidate_id} -> {snapshot.target_content_id}")
        lines.append(f"    source = {snapshot.source}")
        lines.append(f"    chunk  = {snapshot.chunk_id}")
        if snapshot.text_preview:
            lines.append(f"    text   = {snapshot.text_preview}")
    return tuple(lines)


_RENDERERS = {
    "state": _render_state,
    "tick": _render_tick,
    "output": _render_output,
    "worldlet": _render_worldlet,
    "repl": _render_repl,
    "queue": _render_queue,
    "status": _render_status,
    "help": _render_help,
    "stream_summary": _render_stream_summary,
    "stream_candidates": _render_stream_candidates,
}


def render(view: TuiViewModel) -> tuple[str, ...]:
    """Render a ``TuiViewModel`` to a deterministic tuple of display rows.

    The returned rows are bounded by ``view.width`` (long lines are
    truncated with a horizontal-ellipsis suffix). The renderer does not
    touch curses, ``tick()``, files, sockets, or subprocesses.

    Drives ``I-UI-02``.
    """
    if not isinstance(view, TuiViewModel):
        raise TypeError(
            f"render expects a TuiViewModel (got {type(view).__name__})"
        )
    renderer = _RENDERERS.get(view.active_view)
    if renderer is None:
        # Should be unreachable because TuiViewModel.__post_init__ already
        # rejects unknown active_view values; we still guard for clarity.
        raise ValueError(
            f"render: unknown active_view {view.active_view!r}; "
            f"expected one of {ACTIVE_VIEWS!r}"
        )
    body = renderer(view)
    bounded = tuple(_truncate(line, view.width) for line in body)
    # Trim to the available height so the renderer can never overflow the
    # supplied terminal box. The header already guarantees printable text.
    if len(bounded) > view.height:
        bounded = bounded[: view.height]
    return bounded


# ---------------------------------------------------------------------------
# Agent-style layout-aware renderer.
#
# The agent-style renderer composes per-pane bodies into a single tuple of
# rows whose length equals ``view.height`` and whose every line is bounded
# to ``view.width``. It walks an ``AgentLayout`` (a pure function of
# ``(width, height)``) and dispatches a per-pane renderer for each pane. The
# function performs no curses calls, no file/network/shell I/O, and no
# ``tick()`` invocation; it is a pure function of the supplied view model.
#
# Drives ``I-UI-16`` (pane composition matches the layout) and contributes
# to ``I-UI-20`` (the agent-layout view model + per-pane records are
# terminal-agnostic frozen dataclasses).
# ---------------------------------------------------------------------------


def _pad_or_truncate(line: str, width: int) -> str:
    """Truncate over-long lines and right-pad short lines to ``width``."""
    truncated = _truncate(line, width)
    if len(truncated) < width:
        truncated = truncated + " " * (width - len(truncated))
    return truncated


def _legacy_view_for_pane(
    view: "AgentTuiViewModel", active_view: str
) -> TuiViewModel:
    """Reuse the legacy ``TuiViewModel`` body renderers for compatible panes.

    The agent-layout renderer reuses the existing per-pane bodies for the
    ``STATE``, ``INSPECTOR``, ``TRANSCRIPT``-adjacent helpers, and friends.
    Building a temporary legacy view model with the same ``brain`` /
    ``development`` snapshots keeps the body output identical to the
    legacy renderer for the duration of the campaign (decision E retires
    the legacy view model at Step 10).
    """
    # Width is the pane width; height is bounded high enough to keep the
    # body renderer from truncating, with the layout-aware composer doing
    # the final truncation per pane.
    return TuiViewModel(
        active_view=active_view,
        width=max(MIN_WIDTH, view.width),
        height=max(MIN_HEIGHT, view.height),
        brain=view.brain,
        development=view.development,
        queued_event_summary=view.queued_event_summary,
        status_message=view.status_message,
        error_message=view.error_message,
        keyboard_help=view.keyboard_help or DEFAULT_KEYBOARD_HELP,
        pane_titles=view.pane_titles or DEFAULT_PANE_TITLES,
        stream_summary=getattr(view, "stream_summary", None),
        stream_candidates=getattr(view, "stream_candidates", None),
    )


def _render_agent_header(view: "AgentTuiViewModel", pane) -> tuple[str, ...]:
    label = (
        f" toy-brain operator · view={view.active_view} "
        f"· tick={view.tick_counter} · queue={len(view.queued_event_summary)}"
    )
    return (label,)


def _render_agent_state(view: "AgentTuiViewModel", pane) -> tuple[str, ...]:
    legacy = _legacy_view_for_pane(view, "state")
    return _render_state(legacy)


def _render_agent_inspector(view: "AgentTuiViewModel", pane) -> tuple[str, ...]:
    # Pick the renderer matching the active view; ``state`` is already
    # rendered by the left pane so the inspector defaults to ``tick`` when
    # the operator's active view is ``state``.
    active = view.active_view
    if active == "state":
        active = "tick"
    legacy = _legacy_view_for_pane(view, active)
    renderer = _RENDERERS.get(active, _render_tick)
    return renderer(legacy)


def _render_agent_transcript(view: "AgentTuiViewModel", pane) -> tuple[str, ...]:
    lines: list[str] = [_frame_header("transcript", pane.width)]
    entries = view.transcript.entries
    if not entries:
        lines.append(EMPTY_DISPLAY)
        return tuple(lines)
    # Show the newest entries first when there is not enough room for all
    # of them. The layout pane will pad / truncate to the final pane height.
    visible = entries[-(pane.height - 1) :] if pane.height > 1 else ()
    for entry in visible:
        lines.append(f"[{entry.kind}@{entry.tick_at_event}] {entry.text}")
    return tuple(lines)


def _render_agent_composer(view: "AgentTuiViewModel", pane) -> tuple[str, ...]:
    composer = view.composer
    # Place a visible cursor marker. We use ``_`` (underscore) so the
    # cursor renders deterministically on any terminal — the curses
    # wrapper handles the actual cursor positioning at paint time.
    prefix = "> "
    visible_buffer = composer.buffer
    cursor_marker_at = len(prefix) + composer.cursor
    edit_line = prefix + visible_buffer
    if cursor_marker_at >= len(edit_line):
        edit_line = edit_line + "_"
    else:
        edit_line = (
            edit_line[:cursor_marker_at]
            + "|"
            + edit_line[cursor_marker_at + 1 :]
        )
    status_field = composer.status_line or view.status_message
    meta = (
        f"mode={composer.mode}  cursor={composer.cursor}  "
        f"history={composer.history_size}"
    )
    if status_field:
        meta = meta + f"  status={status_field}"
    return (edit_line, meta)


def _render_agent_footer(view: "AgentTuiViewModel", pane) -> tuple[str, ...]:
    if view.error_message:
        hint = f"error: {view.error_message}"
    else:
        hint = (
            "keys: enter submit  ^u clear  ^p prev  ^n next  "
            "/help full keymap"
        )
    return (hint,)


_AGENT_PANE_RENDERERS = {
    "header": _render_agent_header,
    "state": _render_agent_state,
    "inspector": _render_agent_inspector,
    "transcript": _render_agent_transcript,
    "composer": _render_agent_composer,
    "footer": _render_agent_footer,
}


def render_agent(view: "AgentTuiViewModel") -> tuple[str, ...]:
    """Render an :class:`~brain.ui.layout.AgentTuiViewModel` deterministically.

    Returns exactly ``view.height`` rows, each padded or truncated to
    ``view.width``. Pure function: no curses, no clock, no file I/O,
    no network, no ``tick()`` invocation. Reuses the legacy per-pane
    body renderers (``_render_state``, ``_render_tick``, etc.) for
    compatibility with the existing fixtures.

    Drives ``I-UI-16`` (layout composition) and contributes to
    ``I-UI-20`` (terminal-agnostic contract).
    """
    # Local import to avoid a module-level cycle between render.py and
    # layout.py (layout.py imports MIN_WIDTH / MIN_HEIGHT from this module).
    from brain.ui.layout import AgentTuiViewModel  # noqa: PLC0415

    if not isinstance(view, AgentTuiViewModel):
        raise TypeError(
            "render_agent expects an AgentTuiViewModel "
            f"(got {type(view).__name__})"
        )
    layout = view.layout
    # Build a per-row mutable buffer; each row starts blank and panes paste
    # their (padded/truncated) per-cell content over their bounding rect.
    grid: list[list[str]] = [[" "] * view.width for _ in range(view.height)]
    for pane in layout.panes:
        renderer = _AGENT_PANE_RENDERERS.get(pane.renderer)
        if renderer is None:
            raise ValueError(
                "render_agent: unknown pane renderer key "
                f"{pane.renderer!r}"
            )
        body = renderer(view, pane)
        # Pad / truncate body rows to pane height and width.
        padded_rows: list[str] = []
        for i in range(pane.height):
            raw = body[i] if i < len(body) else ""
            padded_rows.append(_pad_or_truncate(raw, pane.width))
        for r_offset, row_text in enumerate(padded_rows):
            r = pane.row + r_offset
            if r < 0 or r >= view.height:
                continue
            chars = list(row_text)
            for c_offset, ch in enumerate(chars):
                c = pane.col + c_offset
                if 0 <= c < view.width:
                    grid[r][c] = ch
    return tuple("".join(row).rstrip() or "" for row in grid)


__all__ = [
    "DEFAULT_WIDTH",
    "DEFAULT_HEIGHT",
    "MIN_WIDTH",
    "MIN_HEIGHT",
    "DEFAULT_PANE_TITLES",
    "DEFAULT_KEYBOARD_HELP",
    "TuiViewModel",
    "build_view_model",
    "render",
    "render_agent",
]
