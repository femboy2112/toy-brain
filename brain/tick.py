"""Brain tick orchestrator (Phase 2 v1).

Functional API replacing the v0 ``Brain`` class:

    new_state, record = tick(state, events, client)

Each call:
  1. Validates each event (PerceptEvent.__post_init__ enforces I-RT-01,
     I-RT-09).
  2. Extends the ContentRegistry with each event's text (I-RT-10).
  3. Inserts each new content into the profile at its initial_rho.
  4. Constructs an LLMBackedPtCns over the post-ingest MSI/registry and
     evaluates each *new* content (the cogito and existing MSI members
     are short-circuited from the per-instance cache or evaluated as
     needed).
  5. Dispatches mode for each new content via ModeOp.from_eval; applies
     the v1 mode-operator semantics (MODE_C integrates if rho meets
     threshold; MODE_A/NEUTRAL leave the content in profile but not in
     MSI).
  6. Reconstructs the final MSI/PtCns via builders so I-RT-04 holds
     (ptcns.eval_map keys == profile.domain).
  7. Calls assert_state_invariants(new_state) — I-RT-08.
  8. Returns (new_state, TickRecord).

The dependency graph is preserved: ``tick → builders + io_types + llm``;
``brain/llm/`` does not import ``brain/tlica/agency.py``, so I-PCE-05 is
unaffected.
"""
from __future__ import annotations

import time
import traceback as _traceback
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType

from brain.io_types import ContentRegistry, PerceptEvent, TickRecord
from brain.llm.client import LLMClient
from brain.llm.ptcns_backed import LLMBackedPtCns
from brain.tlica.builders import make_msi, make_ptcns
from brain.tlica.iboundary import boundary
from brain.tlica.modes import ModeOp, from_eval
from brain.tlica.msi import MSI
from brain.tlica.preservation import PreservationRanking
from brain.tlica.profile import COGITO_ID, ContentID, ScalarProfile
from brain.tlica.ptcns import ConsistencyEval, PtCns, PtCnsLike
from brain.trace import CognitionTracer, NullTracer
from brain.validation import assert_partition


@dataclass(frozen=True, slots=True)
class BrainState:
    """Immutable kernel state passed between ticks."""

    profile: ScalarProfile
    msi: MSI
    ptcns: PtCnsLike
    registry: ContentRegistry


def _summarize_state(state: BrainState) -> dict:
    """Compact JSON-safe view of a BrainState for tick.start / tick.end events."""
    return {
        "profile_domain": sorted(state.profile.domain),
        "msi_contents": sorted(state.msi.contents),
        "msi_threshold": str(state.msi.threshold),
        "registry_size": len(state.registry.texts),
        "boundary": sorted(boundary(state.msi, state.ptcns)),
    }


def _profile_delta(
    old: ScalarProfile, new: ScalarProfile
) -> dict:
    """Compute add/modify/remove delta between two profiles."""
    added: dict[str, str] = {}
    modified: dict[str, str] = {}
    for k in new.domain:
        if k not in old.domain:
            added[k] = str(new.values[k])
        elif old.values[k] != new.values[k]:
            modified[k] = str(new.values[k])
    removed = sorted(old.domain - new.domain)
    return {"added": added, "modified": modified, "removed": removed}


def _set_delta(old: frozenset, new: frozenset) -> dict:
    return {
        "added": sorted(new - old),
        "removed": sorted(old - new),
    }


def tick(
    state: BrainState,
    events: list[PerceptEvent],
    client: LLMClient,
    tracer: CognitionTracer | None = None,
    tick_id: int = 0,
) -> tuple[BrainState, TickRecord]:
    """Process a batch of percepts; return ``(new_state, record)``.

    See module docstring for the per-tick flow. Raises ``ValueError`` on
    any invariant violation; the caller decides whether to halt the
    trajectory or recover.

    Phase 2 v1.1: ``tracer`` records ``tick.start`` / ``tick.end`` and
    fine-grained ``eval.complete`` / ``mode.dispatch`` / ``state.update``
    events. ``tracer`` is observation-only — I-TRACE-01 enforces that
    ``(new_state, record)`` is byte-identical regardless of which
    backend is used. ``tick_id`` is auto-tagged on every event recorded
    during this call (cleared in a ``finally``).
    """
    tracer = tracer if tracer is not None else NullTracer()
    tracer.set_tick(tick_id)
    try:
        start_ns = time.time_ns()
        tracer.record(
            "tick.start",
            {
                "events": [
                    {
                        "content_id": e.content_id,
                        "text": e.text,
                        "content_state": {
                            "available": e.content_state.available,
                            "verification_path": e.content_state.verification_path,
                            "retrievable": e.content_state.retrievable,
                            "operative": e.content_state.operative,
                        },
                        "initial_rho": str(e.initial_rho),
                    }
                    for e in events
                ],
                "state_before": _summarize_state(state),
            },
        )

        # 1. Validation already done by PerceptEvent.__post_init__.

        # 2. Extend the registry with each event's text.
        new_registry = state.registry
        for event in events:
            new_registry = new_registry.with_added(event.content_id, event.text)

        # 3. Insert each new content into the profile at its initial_rho.
        new_values: dict[ContentID, Fraction] = dict(state.profile.values)
        for event in events:
            new_values[event.content_id] = event.initial_rho
        new_profile = ScalarProfile(
            domain=frozenset(new_values.keys()),
            values=MappingProxyType(new_values),
        )

        # 4. Build a provisional MSI carrying over existing MSI members.
        provisional_msi = make_msi(
            profile=new_profile,
            contents=state.msi.contents,
            threshold=state.msi.threshold,
        )

        # 5. Construct the LLM-backed PtCns (tracer plumbs through to the
        #    retry shell) and evaluate each new content.
        llm_ptcns = LLMBackedPtCns(
            msi=provisional_msi,
            content_texts=new_registry.texts,
            client=client,
            tracer=tracer,
        )
        eval_results: dict[ContentID, ConsistencyEval] = {}
        for event in events:
            eval_results[event.content_id] = llm_ptcns.eval(event.content_id)
            tracer.record(
                "eval.complete",
                {
                    "content_id": event.content_id,
                    "result": eval_results[event.content_id].name,
                },
            )

        # 6. Apply v1 mode-operator semantics and emit mode.dispatch.
        final_contents: set[ContentID] = set(state.msi.contents)
        mode_trace: list[ModeOp] = []
        for event in events:
            eval_value = eval_results[event.content_id]
            mode = from_eval(eval_value)
            mode_trace.append(mode)
            tracer.record(
                "mode.dispatch",
                {
                    "content_id": event.content_id,
                    "eval": eval_value.name,
                    "mode": mode.name,
                },
            )
            if mode is ModeOp.MODE_C and event.initial_rho >= provisional_msi.threshold:
                final_contents.add(event.content_id)
            # MODE_A / NEUTRAL: content stays in profile only.

        final_msi = make_msi(
            profile=new_profile,
            contents=frozenset(final_contents),
            threshold=state.msi.threshold,
        )

        # 7. Build the final PtCns over the *full* domain.
        full_eval_map: dict[ContentID, ConsistencyEval] = {
            COGITO_ID: ConsistencyEval.PRESERVE
        }
        for cid in state.profile.domain:
            if cid == COGITO_ID:
                continue
            full_eval_map[cid] = state.ptcns.eval(cid)
        for cid, ev in eval_results.items():
            full_eval_map[cid] = ev
        if set(full_eval_map.keys()) != new_profile.domain:
            missing = new_profile.domain - set(full_eval_map.keys())
            extra = set(full_eval_map.keys()) - new_profile.domain
            raise ValueError(
                "I-RT-04 violated mid-tick: eval_map keys diverged from "
                f"profile.domain (missing={sorted(missing)!r}, extra={sorted(extra)!r})"
            )
        final_ptcns: PtCns = make_ptcns(msi=final_msi, eval_map=full_eval_map)

        new_state = BrainState(
            profile=new_profile,
            msi=final_msi,
            ptcns=final_ptcns,
            registry=new_registry,
        )

        # 7b. Emit state.update per event (v1 has one event per tick,
        #     so the per-event delta equals the per-tick delta).
        old_boundary = boundary(state.msi, state.ptcns)
        new_boundary = boundary(final_msi, final_ptcns)
        for event in events:
            tracer.record(
                "state.update",
                {
                    "content_id": event.content_id,
                    "profile_delta": _profile_delta(state.profile, new_profile),
                    "msi_delta": _set_delta(state.msi.contents, final_msi.contents),
                    "boundary_delta": _set_delta(old_boundary, new_boundary),
                },
            )

        # 8. Re-assert runtime-applicable invariants over the post-tick state.
        try:
            assert_state_invariants(new_state, tracer=tracer)
        except ValueError as exc:
            tracer.record(
                "error",
                {
                    "origin": "brain.tick.assert_state_invariants",
                    "error_type": "ValueError",
                    "message": str(exc),
                    "traceback": _traceback.format_exc(),
                },
            )
            raise

        triggered = mode_trace[0] if mode_trace else None
        record = TickRecord(
            tick_index=0,  # caller may override; the scenario runner stamps it
            profile_values=MappingProxyType(dict(new_profile.values)),
            msi_contents=final_msi.contents,
            eval_map=MappingProxyType(dict(final_ptcns.eval_map)),
            boundary=new_boundary,
            mode_trace=tuple(mode_trace),
            triggered_mode=triggered,
            registry=new_registry,
            notes=tuple(
                f"{event.content_id}={eval_results[event.content_id].name}→{from_eval(eval_results[event.content_id]).name}"
                for event in events
            ),
        )

        duration_ms = (time.time_ns() - start_ns) // 1_000_000
        tracer.record(
            "tick.end",
            {
                "state_after": _summarize_state(new_state),
                "mode_trace": [m.name for m in mode_trace],
                "triggered_mode": triggered.name if triggered is not None else None,
                "duration_ms": duration_ms,
            },
        )
        return new_state, record
    finally:
        tracer.clear_tick()


def initial_state(
    msi_threshold: Fraction = Fraction(1, 2),
) -> BrainState:
    """Construct a cogito-only initial BrainState.

    Used by the scenario runner and by fixtures that build from a
    minimal starting world.
    """
    from brain.tlica.builders import make_profile_with_cogito
    profile = make_profile_with_cogito({COGITO_ID: 1})
    msi = make_msi(
        profile=profile,
        contents={COGITO_ID},
        threshold=msi_threshold,
    )
    ptcns = make_ptcns(
        msi=msi,
        eval_map={COGITO_ID: ConsistencyEval.PRESERVE},
    )
    return BrainState(
        profile=profile,
        msi=msi,
        ptcns=ptcns,
        registry=ContentRegistry.empty(),
    )


def assert_state_invariants(
    state: BrainState,
    tracer: CognitionTracer | None = None,
) -> None:
    """Re-assert all runtime-applicable v0.2 REQUIRED invariants against
    live ``BrainState``. Called once per tick by ``tick(...)``.

    MAINTENANCE CONTRACT (corrigenda C6 + v1.1): This function mirrors
    the subset of ``INVARIANT_CATALOG.md`` rows whose semantics are
    "must hold over the live runtime state" (as opposed to "enforced
    by construction at builder time"). When a new I-RT-NN or
    runtime-applicable row lands in the catalog, add the corresponding
    assertion here AND emit ``invariant.check`` for it via the
    ``_check`` helper. The runner fixtures check rows against
    hand-built fixture data; this function checks the same rows
    against post-tick state.

    The current row set covered:
      - I-PROF-01/02 (profile values in [0, 1])
      - I-MSI-01..06 (MSI consistency and cogito membership)
      - I-PTC-01..05 (PtCns total, cogito always PRESERVE, partition)
      - I-MOD-04 (cogito mode is MODE_C)
      - I-IBND-01..04 (boundary = pos ∪ neg, excludes neutral)
      - I-PRES-01..04 (rank non-negative, cogito-necessity, MSI maximum,
        no-cogito → zero rank)
      - I-RT-02 (post-tick profile values in [0, 1])
      - I-RT-03 (MSI density: non-cogito members meet threshold)
      - I-RT-04 (PtCns eval total over profile.domain)
      - I-RT-07 (cogito at value 1 in profile)

    Raises ``ValueError`` naming the violated row on failure. When a
    tracer is supplied, emits one ``invariant.check`` event per row
    (``passed: true``) on success, or one ``invariant.check`` with
    ``passed: false`` plus an ``error`` event before re-raising.
    """
    tracer = tracer if tracer is not None else NullTracer()
    profile = state.profile
    msi = state.msi
    ptcns = state.ptcns

    def _check(row_id: str, predicate: bool, message: str) -> None:
        if predicate:
            tracer.record(
                "invariant.check",
                {"source": "post_tick", "row_id": row_id, "passed": True},
            )
            return
        tracer.record(
            "invariant.check",
            {"source": "post_tick", "row_id": row_id, "passed": False, "error": message},
        )
        tracer.record(
            "error",
            {
                "origin": "brain.tick.assert_state_invariants",
                "error_type": "ValueError",
                "message": message,
                "row_id": row_id,
            },
        )
        raise ValueError(message)

    # I-PROF-01/02 + I-RT-02: profile values in [0, 1].
    for k, v in profile.values.items():
        _check("I-PROF-01", v >= 0, f"I-PROF-01 / I-RT-02 violated: profile[{k!r}] = {v} < 0")
        _check("I-PROF-02", v <= 1, f"I-PROF-02 / I-RT-02 violated: profile[{k!r}] = {v} > 1")

    # I-MSI-01: cogito at value 1.
    _check(
        "I-MSI-01",
        profile.values.get(COGITO_ID) == Fraction(1),
        f"I-MSI-01 / I-RT-07 violated: profile[COGITO_ID] = "
        f"{profile.values.get(COGITO_ID)!r}, must be 1",
    )

    # I-MSI-02: cogito in MSI.
    _check(
        "I-MSI-02",
        COGITO_ID in msi.contents,
        f"I-MSI-02 violated: COGITO_ID not in msi.contents {set(msi.contents)!r}",
    )

    # I-MSI-03 + I-RT-03: density on non-cogito members.
    for c in msi.contents:
        if c == COGITO_ID:
            continue
        v = profile.values[c]
        _check(
            "I-MSI-03",
            v >= msi.threshold,
            f"I-MSI-03 / I-RT-03 violated: MSI member {c!r} = {v} below "
            f"threshold {msi.threshold}",
        )

    # I-MSI-04: 0 < threshold < 1.
    _check(
        "I-MSI-04",
        Fraction(0) < msi.threshold < Fraction(1),
        f"I-MSI-04 violated: threshold {msi.threshold} not in (0, 1)",
    )

    # I-MSI-05: cogito is the supremum.
    cogito_val = profile.values[COGITO_ID]
    for x in profile.domain:
        _check(
            "I-MSI-05",
            profile.values[x] <= cogito_val,
            f"I-MSI-05 violated: profile[{x!r}] = {profile.values[x]} > "
            f"cogito = {cogito_val}",
        )

    # I-MSI-06: every MSI member has positive value.
    for c in msi.contents:
        _check(
            "I-MSI-06",
            profile.values[c] > 0,
            f"I-MSI-06 violated: MSI member {c!r} has value "
            f"{profile.values[c]}, not strictly positive",
        )

    # I-PTC-01: cogito_invariance.
    _check(
        "I-PTC-01",
        ptcns.eval(COGITO_ID) is ConsistencyEval.PRESERVE,
        f"I-PTC-01 violated: ptcns.eval(COGITO_ID) = {ptcns.eval(COGITO_ID)!r}",
    )

    # I-RT-04: PtCns total over profile.domain.
    _check(
        "I-RT-04",
        set(ptcns.eval_map.keys()) == set(profile.domain),
        "I-RT-04 violated: ptcns.eval_map keys != profile.domain",
    )

    # I-PTC-02 + I-PTC-03: partition (delegate to validation helper, then
    # emit a single combined invariant.check on success).
    try:
        assert_partition(
            pos=ptcns.positive_contents,
            neg=ptcns.negative_contents,
            neu=ptcns.neutral_contents,
            domain=profile.domain,
        )
    except AssertionError as exc:
        message = str(exc)
        tracer.record(
            "invariant.check",
            {"source": "post_tick", "row_id": "I-PTC-02", "passed": False, "error": message},
        )
        tracer.record(
            "error",
            {
                "origin": "brain.tick.assert_state_invariants",
                "error_type": "AssertionError",
                "message": message,
                "row_id": "I-PTC-02",
            },
        )
        raise ValueError(message) from exc
    tracer.record("invariant.check", {"source": "post_tick", "row_id": "I-PTC-02", "passed": True})
    tracer.record("invariant.check", {"source": "post_tick", "row_id": "I-PTC-03", "passed": True})

    # I-PTC-04: cogito in positive.
    _check(
        "I-PTC-04",
        COGITO_ID in ptcns.positive_contents,
        "I-PTC-04 violated: COGITO_ID not in positive_contents",
    )

    # I-PTC-05: cogito not negative or neutral.
    _check(
        "I-PTC-05",
        COGITO_ID not in ptcns.negative_contents and COGITO_ID not in ptcns.neutral_contents,
        "I-PTC-05 violated: COGITO_ID classified as non-positive",
    )

    # I-MOD-04: cogito triggers MODE_C.
    _check(
        "I-MOD-04",
        from_eval(ptcns.eval(COGITO_ID)) is ModeOp.MODE_C,
        f"I-MOD-04 violated: cogito mode = {from_eval(ptcns.eval(COGITO_ID))!r}",
    )

    # I-IBND-01..04: boundary semantics.
    b = boundary(msi, ptcns)
    _check(
        "I-IBND-01",
        not (b & ptcns.neutral_contents),
        "I-IBND-01 violated: boundary intersects neutral_contents",
    )
    for x in profile.domain:
        in_b = x in b
        eval_in_boundary = ptcns.eval(x) in (
            ConsistencyEval.PRESERVE,
            ConsistencyEval.DAMAGE,
        )
        _check(
            "I-IBND-03",
            in_b == eval_in_boundary,
            f"I-IBND-03 violated: boundary membership for {x!r} disagrees with eval class",
        )

    # I-PRES-01..04: cogito-gated rank invariants.
    pi = PreservationRanking(msi=msi)
    msi_rank = pi.rank(msi.contents)
    sample_sets: list[frozenset[ContentID]] = [
        frozenset(),
        frozenset({COGITO_ID}),
        msi.contents,
    ]
    for s in sample_sets:
        r = pi.rank(s)
        _check("I-PRES-01", r >= 0, f"I-PRES-01 violated: rank({s!r}) = {r} < 0")
        if r > 0:
            _check(
                "I-PRES-02",
                COGITO_ID in s,
                f"I-PRES-02 violated: rank({s!r}) = {r} > 0 but cogito missing",
            )
        _check(
            "I-PRES-03",
            r <= msi_rank,
            f"I-PRES-03 violated: rank({s!r}) = {r} > MSI rank {msi_rank}",
        )
        if COGITO_ID not in s:
            _check(
                "I-PRES-04",
                r == 0,
                f"I-PRES-04 violated: cogito-less rank({s!r}) = {r} != 0",
            )


__all__ = [
    "BrainState",
    "tick",
    "initial_state",
    "assert_state_invariants",
]
