"""Read-only Operator TUI snapshot records.

This module is the read-only display projection of the kernel state and the
optional Phase 3.1-3.4 developmental histories. Construction is pure: it never
mutates ``BrainState``, ``ScalarProfile``, ``MSI``, ``PtCns``,
``ContentRegistry``, ``TickRecord``, ``OutputHistory``, ``WorldletHistory``,
``ProtoBasicHistory``, trace backends, scenario files, or catalog files. All
exact ``Fraction`` values are rendered as strings so the display path can never
introduce float arithmetic into invariant-bearing paths.

Catalog rows driven from here:

* ``I-UI-01`` — snapshot construction is read-only over kernel state.
* ``I-UI-08`` — snapshot records are immutable display values.

This module deliberately does **not** import ``curses``, ``brain.tick``,
``brain.llm``, or any module from ``brain.tlica``. It depends only on
``brain.io_types`` (for ``TickRecord`` / ``ContentRegistry`` typing) and the
public developmental layer surfaces, all of which are pure-data immutable
records.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # pragma: no cover - typing-only imports
    from brain.io_types import ContentRegistry, TickRecord
    from brain.development.output import OutputHistory
    from brain.development.repl import ProtoBasicHistory
    from brain.development.worldlet import WorldletHistory


# ---------------------------------------------------------------------------
# Static description tables
# ---------------------------------------------------------------------------


#: Canonical UI view identifiers. Renderer / router consumers MUST treat this
#: as a closed enumeration; new views require a catalog-aware change.
ACTIVE_VIEWS: tuple[str, ...] = (
    "state",
    "tick",
    "output",
    "worldlet",
    "repl",
    "queue",
    "status",
    "help",
)


#: Sentinel printed for missing histories / records so the renderer can render
#: "no data" panes deterministically.
EMPTY_DISPLAY = "(empty)"


# ---------------------------------------------------------------------------
# BrainSnapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BrainSnapshot:
    """Immutable display projection of the current kernel state.

    All fields are bounded primitives, tuples of strings, or frozensets. No
    mutable kernel container is exposed. Exact ``Fraction`` values are stored
    as strings (e.g. ``"1/2"``) so the UI cannot accidentally introduce float
    arithmetic into invariant-bearing paths.

    Drives ``I-UI-01`` (the constructor reads only) and ``I-UI-08`` (the
    record is frozen, every field is an immutable display value).
    """

    profile_domain: tuple[str, ...]
    profile_values: tuple[tuple[str, str], ...]
    msi_contents: frozenset[str]
    msi_threshold: str
    eval_positive: frozenset[str]
    eval_negative: frozenset[str]
    eval_neutral: frozenset[str]
    boundary_contents: frozenset[str]
    registry_keys: tuple[str, ...]
    registry_entries: tuple[tuple[str, str], ...]
    latest_tick_index: Optional[int]
    latest_mode_trace: tuple[str, ...]
    latest_triggered_mode: Optional[str]
    latest_tick_notes: tuple[str, ...]


def build_brain_snapshot(
    state: "object",
    *,
    latest_tick: Optional["TickRecord"] = None,
) -> BrainSnapshot:
    """Construct a ``BrainSnapshot`` from a ``BrainState`` without mutation.

    ``state`` is typed as ``object`` to avoid importing ``brain.tick`` here:
    the snapshot path must remain free of kernel-orchestrator imports. The
    function only reads attributes (``profile``, ``msi``, ``ptcns``,
    ``registry``) and copies their contents into immutable display values.

    Drives:
      * ``I-UI-01`` — no attribute is reassigned, no container is mutated,
        the kernel objects' identities and ``repr`` remain unchanged before
        and after the call.
      * ``I-UI-08`` — every collection is converted to a tuple / frozenset
        before being placed on the snapshot.
    """
    profile = state.profile  # type: ignore[attr-defined]
    msi = state.msi  # type: ignore[attr-defined]
    ptcns = state.ptcns  # type: ignore[attr-defined]
    registry = state.registry  # type: ignore[attr-defined]

    profile_domain = tuple(sorted(profile.domain))
    profile_values = tuple(
        (cid, str(profile.values[cid])) for cid in profile_domain
    )

    msi_contents = frozenset(msi.contents)
    msi_threshold = str(msi.threshold)

    # ``ptcns`` exposes ``eval_map``; classify keys by the public enum
    # without importing ConsistencyEval (keep this module free of
    # ``brain.tlica`` imports). We rely on each value carrying a stable
    # ``name`` attribute (str Enum), which every ``ConsistencyEval`` does.
    pos: list[str] = []
    neg: list[str] = []
    neu: list[str] = []
    for cid, value in ptcns.eval_map.items():
        name = getattr(value, "name", str(value))
        if name == "PRESERVE":
            pos.append(cid)
        elif name == "DAMAGE":
            neg.append(cid)
        else:
            neu.append(cid)

    eval_positive = frozenset(pos)
    eval_negative = frozenset(neg)
    eval_neutral = frozenset(neu)

    # ``iboundary.boundary`` is the canonical compute; importing it would pull
    # in ``brain.tlica``. We compute the boundary locally from MSI + PtCns to
    # keep ``brain.ui`` free of ``brain.tlica`` imports.
    boundary_contents = frozenset(
        cid for cid in msi.contents
        if getattr(ptcns.eval_map.get(cid), "name", None) != "PRESERVE"
    )

    registry_keys = tuple(sorted(registry.texts.keys()))
    registry_entries = tuple(
        (cid, registry.texts[cid]) for cid in registry_keys
    )

    if latest_tick is None:
        latest_tick_index: Optional[int] = None
        latest_mode_trace: tuple[str, ...] = ()
        latest_triggered_mode: Optional[str] = None
        latest_tick_notes: tuple[str, ...] = ()
    else:
        latest_tick_index = int(latest_tick.tick_index)
        latest_mode_trace = tuple(
            getattr(m, "name", str(m)) for m in latest_tick.mode_trace
        )
        trig = latest_tick.triggered_mode
        latest_triggered_mode = (
            getattr(trig, "name", str(trig)) if trig is not None else None
        )
        latest_tick_notes = tuple(str(n) for n in latest_tick.notes)

    return BrainSnapshot(
        profile_domain=profile_domain,
        profile_values=profile_values,
        msi_contents=msi_contents,
        msi_threshold=msi_threshold,
        eval_positive=eval_positive,
        eval_negative=eval_negative,
        eval_neutral=eval_neutral,
        boundary_contents=boundary_contents,
        registry_keys=registry_keys,
        registry_entries=registry_entries,
        latest_tick_index=latest_tick_index,
        latest_mode_trace=latest_mode_trace,
        latest_triggered_mode=latest_triggered_mode,
        latest_tick_notes=latest_tick_notes,
    )


# ---------------------------------------------------------------------------
# DevelopmentSnapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DevelopmentSnapshot:
    """Immutable display projection of Phase 3.1-3.4 developmental histories.

    Each field is either an integer count or a tuple of bounded printable
    strings. Missing histories are represented by zero counts and empty
    tuples, never by ``None`` from the renderer's point of view.

    Drives ``I-UI-08`` (immutable display values). The renderer references
    this record via ``TuiViewModel`` (``I-UI-09``).
    """

    output_impulse_count: int = 0
    output_echo_count: int = 0
    output_pattern_count: int = 0
    output_token_candidate_count: int = 0
    learned_output_token_count: int = 0
    worldlet_state_id: Optional[str] = None
    worldlet_step_index: Optional[int] = None
    worldlet_attempt_count: int = 0
    worldlet_response_count: int = 0
    worldlet_object_ids: tuple[str, ...] = ()
    repl_parse_count: int = 0
    repl_command_count: int = 0
    repl_execution_count: int = 0
    repl_feedback_count: int = 0
    repl_emit_counts: tuple[tuple[str, int], ...] = ()


def build_development_snapshot(
    *,
    output_history: Optional["OutputHistory"] = None,
    worldlet_history: Optional["WorldletHistory"] = None,
    repl_history: Optional["ProtoBasicHistory"] = None,
) -> DevelopmentSnapshot:
    """Construct a ``DevelopmentSnapshot`` from optional developmental layers.

    Missing histories yield zero counts and empty tuples; the constructor
    does not raise when a history is ``None``. Like ``build_brain_snapshot``
    this function never mutates its inputs.

    Drives ``I-UI-01`` (read-only over the supplied histories) and
    ``I-UI-08`` (output is immutable).
    """
    if output_history is None:
        output_impulse_count = 0
        output_echo_count = 0
        output_pattern_count = 0
        output_token_candidate_count = 0
        learned_output_token_count = 0
    else:
        output_impulse_count = len(output_history.impulses)
        output_echo_count = len(output_history.echoes)
        output_pattern_count = len(output_history.output_patterns or ())
        output_token_candidate_count = len(
            output_history.token_candidates or ()
        )
        learned_output_token_count = len(output_history.learned_tokens or ())

    if worldlet_history is None:
        worldlet_state_id: Optional[str] = None
        worldlet_step_index: Optional[int] = None
        worldlet_attempt_count = 0
        worldlet_response_count = 0
        worldlet_object_ids: tuple[str, ...] = ()
    else:
        latest_state = worldlet_history.latest_state
        worldlet_state_id = str(latest_state.state_id)
        worldlet_step_index = int(latest_state.step_index)
        worldlet_attempt_count = len(worldlet_history.attempts)
        worldlet_response_count = len(worldlet_history.responses)
        worldlet_object_ids = tuple(sorted(latest_state.objects.keys()))

    if repl_history is None:
        repl_parse_count = 0
        repl_command_count = 0
        repl_execution_count = 0
        repl_feedback_count = 0
        repl_emit_counts: tuple[tuple[str, int], ...] = ()
    else:
        repl_parse_count = len(repl_history.parse_results)
        repl_command_count = len(repl_history.commands)
        repl_execution_count = len(repl_history.execution_results)
        repl_feedback_count = len(repl_history.feedback)
        emit_map = dict(repl_history.emit_counts or {})
        repl_emit_counts = tuple(
            (k, int(emit_map[k])) for k in sorted(emit_map.keys())
        )

    return DevelopmentSnapshot(
        output_impulse_count=output_impulse_count,
        output_echo_count=output_echo_count,
        output_pattern_count=output_pattern_count,
        output_token_candidate_count=output_token_candidate_count,
        learned_output_token_count=learned_output_token_count,
        worldlet_state_id=worldlet_state_id,
        worldlet_step_index=worldlet_step_index,
        worldlet_attempt_count=worldlet_attempt_count,
        worldlet_response_count=worldlet_response_count,
        worldlet_object_ids=worldlet_object_ids,
        repl_parse_count=repl_parse_count,
        repl_command_count=repl_command_count,
        repl_execution_count=repl_execution_count,
        repl_feedback_count=repl_feedback_count,
        repl_emit_counts=repl_emit_counts,
    )


__all__ = [
    "ACTIVE_VIEWS",
    "EMPTY_DISPLAY",
    "BrainSnapshot",
    "DevelopmentSnapshot",
    "build_brain_snapshot",
    "build_development_snapshot",
]
