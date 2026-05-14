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
from brain.validation import assert_partition


@dataclass(frozen=True, slots=True)
class BrainState:
    """Immutable kernel state passed between ticks."""

    profile: ScalarProfile
    msi: MSI
    ptcns: PtCnsLike
    registry: ContentRegistry


def tick(
    state: BrainState,
    events: list[PerceptEvent],
    client: LLMClient,
) -> tuple[BrainState, TickRecord]:
    """Process a batch of percepts; return ``(new_state, record)``.

    See module docstring for the per-tick flow. Raises ``ValueError`` on
    any invariant violation; the caller decides whether to halt the
    trajectory or recover.
    """
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
    #    New contents are added to MSI per mode-operator semantics below.
    provisional_msi = make_msi(
        profile=new_profile,
        contents=state.msi.contents,
        threshold=state.msi.threshold,
    )

    # 5. Construct the LLM-backed PtCns and evaluate each new content.
    llm_ptcns = LLMBackedPtCns(
        msi=provisional_msi,
        content_texts=new_registry.texts,
        client=client,
    )
    eval_results: dict[ContentID, ConsistencyEval] = {}
    for event in events:
        eval_results[event.content_id] = llm_ptcns.eval(event.content_id)

    # 6. Apply v1 mode-operator semantics.
    #    MODE_C integrates into MSI iff rho >= threshold; MODE_A and
    #    NEUTRAL leave the content in the profile but exclude from MSI.
    final_contents: set[ContentID] = set(state.msi.contents)
    mode_trace: list[ModeOp] = []
    for event in events:
        eval_value = eval_results[event.content_id]
        mode = from_eval(eval_value)
        mode_trace.append(mode)
        if mode is ModeOp.MODE_C and event.initial_rho >= provisional_msi.threshold:
            final_contents.add(event.content_id)
        # MODE_A / NEUTRAL: content stays in profile only.

    final_msi = make_msi(
        profile=new_profile,
        contents=frozenset(final_contents),
        threshold=state.msi.threshold,
    )

    # 7. Build the final PtCns over the *full* domain.
    full_eval_map: dict[ContentID, ConsistencyEval] = {COGITO_ID: ConsistencyEval.PRESERVE}
    # Carry over existing eval_map entries for any pre-existing domain
    # members (their LLM evaluations were cached at the tick they were
    # introduced and stored in the prior PtCns).
    for cid in state.profile.domain:
        if cid == COGITO_ID:
            continue
        full_eval_map[cid] = state.ptcns.eval(cid)
    for cid, ev in eval_results.items():
        full_eval_map[cid] = ev
    # Sanity: must cover every domain element exactly.
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

    # 8. Re-assert runtime-applicable invariants over the post-tick state.
    assert_state_invariants(new_state)

    triggered = mode_trace[0] if mode_trace else None
    record = TickRecord(
        tick_index=0,  # caller may override; the scenario runner stamps it
        profile_values=MappingProxyType(dict(new_profile.values)),
        msi_contents=final_msi.contents,
        eval_map=MappingProxyType(dict(final_ptcns.eval_map)),
        boundary=boundary(final_msi, final_ptcns),
        mode_trace=tuple(mode_trace),
        triggered_mode=triggered,
        registry=new_registry,
        notes=tuple(
            f"{event.content_id}={eval_results[event.content_id].name}→{from_eval(eval_results[event.content_id]).name}"
            for event in events
        ),
    )
    return new_state, record


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


def assert_state_invariants(state: BrainState) -> None:
    """Re-assert all runtime-applicable v0.2 REQUIRED invariants against
    live ``BrainState``. Called once per tick by ``tick(...)``.

    MAINTENANCE CONTRACT (corrigenda C6): This function mirrors the
    subset of ``INVARIANT_CATALOG.md`` rows whose semantics are "must
    hold over the live runtime state" (as opposed to "enforced by
    construction at builder time"). When a new I-RT-NN or
    runtime-applicable row lands in the catalog, add the corresponding
    assertion here. The runner fixtures check rows against hand-built
    fixture data; this function checks the same rows against post-tick
    state.

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

    Raises ``ValueError`` naming the violated row on failure.
    """
    profile = state.profile
    msi = state.msi
    ptcns = state.ptcns

    # I-PROF-01/02 + I-RT-02: profile values in [0, 1].
    for k, v in profile.values.items():
        if v < 0:
            raise ValueError(
                f"I-PROF-01 / I-RT-02 violated: profile[{k!r}] = {v} < 0"
            )
        if v > 1:
            raise ValueError(
                f"I-PROF-02 / I-RT-02 violated: profile[{k!r}] = {v} > 1"
            )

    # I-MSI-01: cogito at value 1.
    if profile.values.get(COGITO_ID) != Fraction(1):
        raise ValueError(
            f"I-MSI-01 / I-RT-07 violated: profile[COGITO_ID] = "
            f"{profile.values.get(COGITO_ID)!r}, must be 1"
        )

    # I-MSI-02: cogito in MSI.
    if COGITO_ID not in msi.contents:
        raise ValueError(
            f"I-MSI-02 violated: COGITO_ID not in msi.contents {set(msi.contents)!r}"
        )

    # I-MSI-03 + I-RT-03: density on non-cogito members.
    for c in msi.contents:
        if c == COGITO_ID:
            continue
        v = profile.values[c]
        if v < msi.threshold:
            raise ValueError(
                f"I-MSI-03 / I-RT-03 violated: MSI member {c!r} = {v} below "
                f"threshold {msi.threshold}"
            )

    # I-MSI-04: 0 < threshold < 1.
    if not (Fraction(0) < msi.threshold < Fraction(1)):
        raise ValueError(
            f"I-MSI-04 violated: threshold {msi.threshold} not in (0, 1)"
        )

    # I-MSI-05: cogito is the supremum.
    cogito_val = profile.values[COGITO_ID]
    for x in profile.domain:
        if profile.values[x] > cogito_val:
            raise ValueError(
                f"I-MSI-05 violated: profile[{x!r}] = {profile.values[x]} > "
                f"cogito = {cogito_val}"
            )

    # I-MSI-06: every MSI member has positive value.
    for c in msi.contents:
        if profile.values[c] <= 0:
            raise ValueError(
                f"I-MSI-06 violated: MSI member {c!r} has value "
                f"{profile.values[c]}, not strictly positive"
            )

    # I-PTC-01: cogito_invariance.
    if ptcns.eval(COGITO_ID) is not ConsistencyEval.PRESERVE:
        raise ValueError(
            f"I-PTC-01 violated: ptcns.eval(COGITO_ID) = {ptcns.eval(COGITO_ID)!r}"
        )

    # I-RT-04: PtCns total over profile.domain.
    if set(ptcns.eval_map.keys()) != set(profile.domain):
        missing = set(profile.domain) - set(ptcns.eval_map.keys())
        extra = set(ptcns.eval_map.keys()) - set(profile.domain)
        raise ValueError(
            "I-RT-04 violated: ptcns.eval_map keys != profile.domain "
            f"(missing={sorted(missing)!r}, extra={sorted(extra)!r})"
        )

    # I-PTC-02 + I-PTC-03: partition.
    assert_partition(
        pos=ptcns.positive_contents,
        neg=ptcns.negative_contents,
        neu=ptcns.neutral_contents,
        domain=profile.domain,
    )

    # I-PTC-04: cogito in positive.
    if COGITO_ID not in ptcns.positive_contents:
        raise ValueError("I-PTC-04 violated: COGITO_ID not in positive_contents")

    # I-PTC-05: cogito not negative or neutral.
    if COGITO_ID in ptcns.negative_contents or COGITO_ID in ptcns.neutral_contents:
        raise ValueError("I-PTC-05 violated: COGITO_ID classified as non-positive")

    # I-MOD-04: cogito triggers MODE_C.
    if from_eval(ptcns.eval(COGITO_ID)) is not ModeOp.MODE_C:
        raise ValueError(
            f"I-MOD-04 violated: cogito mode = {from_eval(ptcns.eval(COGITO_ID))!r}"
        )

    # I-IBND-01..04: boundary semantics.
    b = boundary(msi, ptcns)
    if b & ptcns.neutral_contents:
        raise ValueError("I-IBND-01 violated: boundary intersects neutral_contents")
    for x in profile.domain:
        in_b = x in b
        eval_in_boundary = ptcns.eval(x) in (
            ConsistencyEval.PRESERVE,
            ConsistencyEval.DAMAGE,
        )
        if in_b != eval_in_boundary:
            raise ValueError(
                f"I-IBND-03 violated: boundary membership for {x!r} "
                f"disagrees with eval class"
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
        if r < 0:
            raise ValueError(f"I-PRES-01 violated: rank({s!r}) = {r} < 0")
        if r > 0 and COGITO_ID not in s:
            raise ValueError(
                f"I-PRES-02 violated: rank({s!r}) = {r} > 0 but cogito missing"
            )
        if r > msi_rank:
            raise ValueError(
                f"I-PRES-03 violated: rank({s!r}) = {r} > MSI rank {msi_rank}"
            )
        if COGITO_ID not in s and r != 0:
            raise ValueError(
                f"I-PRES-04 violated: cogito-less rank({s!r}) = {r} != 0"
            )


__all__ = [
    "BrainState",
    "tick",
    "initial_state",
    "assert_state_invariants",
]
