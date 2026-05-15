# TLICA → `brain/` Invariant Catalog (v0)

This catalog is the spine of the v0 plan. Each row binds a Lean source declaration in `lean-scratch-main/TLICA/` to a Python runtime check in `brain/`, names the owning Python module, and points at the fixture that exercises it. v0's success criterion is: every row marked **REQUIRED** asserts green on its named fixture under the deterministic stubs.

> **Catalog version:** v0.5. Patches over v0.4 (Phase 2 v1.2 baseline hardening): +5 STRUCTURAL rows (I-RT-11 single-event tick, I-RT-12 duplicate content_id, I-TRACE-02 trace fail-open, I-TRACE-03 trace reserved-key rejection, I-CAT-01 catalog↔registry coverage); six correctness patches (P1 SafeTracer, P2 single-event guard, P3 duplicate guard, P4 ambiguous-parse rejection, P5 FutureMSIModel runtime guard, P6 trace envelope reserved-key protection); `SourceKind` schema field inferred by `tools/catalog.py`; auto-generated `brain/_catalog_ids.py`; strict `tools.catalog counts` gate; README synced. No new fixtures; existing fixtures gain new rows.
>
> **Catalog version:** v0.4. Patches over v0.3 (Phase 2 v1.1): togglable `CognitionTracer` Protocol seam in `brain/trace.py`; three backends (`NullTracer`, `MemoryTracer`, `FileTracer`); +1 STRUCTURAL row (I-TRACE-01); +1 fixture (`trace_v1_1.py`). Observation-only — no semantic change to v0.3 invariants.
>
> **Catalog version:** v0.3. Patches over v0.2 (Phase 2 v1): LLM-backed `PtCns.eval` via the new `brain/llm/` seam; new `OBSERVED` Status; +4 REQUIRED rows (I-LLM-01, I-LLM-03, I-RT-08, I-BHV-01); +3 STRUCTURAL rows (I-LLM-04, I-RT-09, I-RT-10); +1 OBSERVED row (I-LLM-02); two new fixtures (`llm_protocol.py`, `scenario_v1.py`).
>
> **Catalog version:** v0.2. Patches over v0.1: numeric representation switched to `Fraction`; `Act` is an `Enum`; `PreservationRanking` stub is cogito-gated; `I-INT-01` uses Lean-exact `< 1`; `I-MSI-05` corrected to ρ/profile; `I-PHI-01` reclassified DEFERRED; trajectory shared-distance rows added; PCE-valence exclusions added; free-will witness rows reclassified NOT-EXERCISED; `I-RT-07` cogito-preservation invariant added; `ProjectMap.natural_dynamics` made an explicit Protocol method; `affect_kernel_collapse.py` fixture added.

## Schema

| Column | Meaning |
|---|---|
| **ID** | Stable identifier `I-<MOD>-NN` for cross-referencing. |
| **Lean source** | `<file>::<decl>` — the authoritative theorem, definition, or structure field. |
| **Proposition** | Plain statement of what holds. |
| **Python assertion** | Pseudocode for the runtime check. |
| **Owning module** | The `brain/` file that hosts the assertion. |
| **Fixture** | The `brain/fixtures/` file that drives it. |
| **Status** | `REQUIRED` (must assert green in v0) · `STRUCTURAL` (type-enforced at construction or covered by another row's fixture; no per-tick assertion of its own) · `NOT-EXERCISED` (Python surface exists but no v0 fixture drives it) · `DEFERRED` (explicit non-goal per `CLAIM_GUARDRAILS.md` or Lean deferred marker) · `OBSERVED` (recorded in the run summary for inspection; does not fail the runner — used for properties useful to track but not required for correctness). |

## Conventions

- **Numeric core: `Fraction`.** All profile values, distances, ranks, and PCE values inside `brain/tlica/`, `brain/fixtures/`, and `brain/invariants.py` are `fractions.Fraction`. Type alias `Rho = Fraction`. Raw `==` is safe and used throughout the catalog. The constructor `rho(value: int | float | str | Fraction) -> Fraction` normalizes at the I/O boundary and raises if the value is outside `[0, 1]` — never silently clamps. `brain/io_types.PerceptEvent` accepts any of those input types; `TickRecord` may expose float views for display only, never for invariant checks.
- **`Act` is an `enum.Enum`**, not a `typing.Literal`:
  ```python
  class Act(str, Enum):
      NOOP = "noop"
      INTEGRATE = "integrate"
      DIFFERENTIATE = "differentiate"
      ENCAPSULATE = "encapsulate"
  ```
  `isinstance(x, Act)` works at runtime; `proj.no_action is Act.NOOP`.
- **Infinity.** `dInfShared` returns `math.inf` (a float, the single permitted float in the kernel) on empty intersection, matching Lean's `⊤`. All other distance/rank/PCE values are `Fraction`.
- **Distances.** `dInfUnion(f, g)` and `dInfShared(f, g)` are computed over `f.domain | g.domain` and `f.domain & g.domain` respectively — **not** the current content store's keys. Projected profiles have their own domains.
- **Cogito.** `COGITO_ID` is a reserved sentinel that cannot collide with user input. Cogito invariants (I-MSI-01, I-MSI-02, I-PTC-01) are enforced at construction via `brain/tlica/builders.py`, then re-asserted at every tick. v0 deterministic `ProjectMap` stubs are obligated to preserve `COGITO_ID` at value `1` in every projected profile (I-RT-07).
- **PCE vs ProjectedPCE.** Foundation `PCE` (`brain/tlica/pce.py`) is action-constant by Lean theorem (I-PCE-04). Action selection routes through `feasibleProjectedPCE` (`brain/tlica/agency.py` / `brain/tlica/action_projection.py`). The brain **never** uses foundation PCE for action choice (I-PCE-05).
- **Modes vs Actions.** `ModeOp` (A / B / C / neutral) and `Act` (NOOP / INTEGRATE / DIFFERENTIATE / ENCAPSULATE) are disjoint namespaces. Mode B is parallel, not triggered by `PtCns.fromEval`. The mapping from `ModeOp` to default `Act` is a lookup, not an identity.
- **`ProjectMap` exposes `natural_dynamics`.** Because Lean's `identity_action_natural` is an existential, the Python `ProjectMap` Protocol exposes `natural_dynamics(profile) -> ScalarProfile` explicitly so the witness is testable. v0 deterministic stub: `natural_dynamics(P) = P`.
- **Validation helpers live in `brain/validation.py`.** Reusable functions like `profile_equiv`, `is_in_unit_interval`, `assert_subset_rank_le` are owned by `brain/validation.py`, used by both `brain/invariants.py` and the fixtures. Constructors live in `brain/tlica/builders.py`. The catalog runner lives in `brain/invariants.py`. The dependency graph: `builders → validation`, `invariants → fixtures + validation`, `tick → builders + invariants`.

---

## Required v0 invariants

### `brain/tlica/profile.py` — `ScalarProfile`, `zeroExtend`

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-PROF-01 | `Profile.lean::ScalarProfile.toFun_nonneg` | Every profile value is ≥ 0. | `all(v >= 0 for v in profile.values.values())` | `minimal.py` | REQUIRED |
| I-PROF-02 | `Profile.lean::ScalarProfile.toFun_le_one` | Every profile value is ≤ 1. | `all(v <= 1 for v in profile.values.values())` | `minimal.py` | REQUIRED |
| I-PROF-03 | `Profile.lean::zeroExtend_of_mem` | `zero_extend(x) == profile[x]` when `x ∈ domain`. | `profile.zero_extend(x) == profile.values[x]` for `x in profile.domain` | `profile_distance.py` | REQUIRED |
| I-PROF-04 | `Profile.lean::zeroExtend_of_not_mem` | `zero_extend(x) == 0` when `x ∉ domain`. | `profile.zero_extend(x) == Fraction(0)` for `x not in profile.domain` | `profile_distance.py` | REQUIRED |
| I-PROF-05 | `Profile.lean::zeroExtend_nonneg` | Zero-extension is non-negative everywhere. | `all(profile.zero_extend(x) >= 0 for x in universe)` | `profile_distance.py` | REQUIRED |
| I-PROF-06 | `Profile.lean::zeroExtend_le_one` | Zero-extension is ≤ 1 everywhere. | `all(profile.zero_extend(x) <= 1 for x in universe)` | `profile_distance.py` | REQUIRED |
| I-PROF-07 | `Profile.lean::abs_sub_zeroExtend_le_one` | Pointwise zero-extension difference is ≤ 1. | `all(abs(f.zero_extend(x) - g.zero_extend(x)) <= 1 for x in f.domain | g.domain)` | `profile_distance.py` | REQUIRED |

### `brain/tlica/msi.py` — `MSI`

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-MSI-01 | `MSI.lean::MSI.cogito_value` | `profile.toFun cogito = 1`. | `profile.values[COGITO_ID] == 1` | `cogito_invariants.py` | REQUIRED |
| I-MSI-02 | `MSI.lean::MSI.cogito_in` (Axiom 3.3.1) | Cogito is in MSI contents. | `COGITO_ID in msi.contents` | `cogito_invariants.py` | REQUIRED |
| I-MSI-03 | `MSI.lean::MSI.density` (Axiom 3.3.3) | Non-cogito MSI members meet threshold. | `all(profile.values[x] >= msi.threshold for x in msi.contents if x != COGITO_ID)` | `minimal.py` | REQUIRED |
| I-MSI-04 | `MSI.lean::MSI.threshold_pos`, `threshold_lt_one` | `0 < threshold < 1`. | `0 < msi.threshold < 1` | `minimal.py` | REQUIRED |
| I-MSI-05 | `MSI.lean::cogito_is_supremum` | Cogito is the ρ/profile supremum. | `all(profile.values[x] <= profile.values[COGITO_ID] for x in profile.domain)` | `cogito_invariants.py` | REQUIRED |
| I-MSI-06 | `MSI.lean::mem_msi_positive` | Every MSI member has positive profile value. | `all(profile.values[x] > 0 for x in msi.contents)` | `minimal.py` | REQUIRED |

### `brain/tlica/ptcns.py` — `ConsistencyEval`, `PtCns`

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-PTC-01 | `PtCns.lean::PtCns.cogito_invariance` (Axiom 7.3.1) | `eval(cogito) == preserve`. | `ptcns.eval(COGITO_ID) == ConsistencyEval.PRESERVE` | `cogito_invariants.py` | REQUIRED |
| I-PTC-02 | `PtCns.lean::partition_disjoint` | The three eval classes are pairwise disjoint. | `pos & neg == set() and pos & neu == set() and neg & neu == set()` | `minimal.py` | REQUIRED |
| I-PTC-03 | `PtCns.lean::partition_cover` | The three eval classes cover the profile domain. | `pos | neg | neu == set(profile.domain)` | `minimal.py` | REQUIRED |
| I-PTC-04 | `PtCns.lean::cogito_in_positive` | Cogito is in the positive set. | `COGITO_ID in ptcns.positive_contents` | `cogito_invariants.py` | REQUIRED |
| I-PTC-05 | `PtCns.lean::cogito_not_negative`, `cogito_not_neutral` | Cogito is not negative or neutral. | `COGITO_ID not in ptcns.negative_contents and COGITO_ID not in ptcns.neutral_contents` | `cogito_invariants.py` | REQUIRED |

### `brain/tlica/modes.py` — `ModeOp`, `fromEval`

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-MOD-01 | `Modes.lean::ModeOp.fromEval_damage` | `fromEval(damage) == modeA`. | `ModeOp.from_eval(ConsistencyEval.DAMAGE) == ModeOp.MODE_A` | `mode_a_dispatch.py` | REQUIRED |
| I-MOD-02 | `Modes.lean::ModeOp.fromEval_neutral` | `fromEval(neutral) == neutral`. | `ModeOp.from_eval(ConsistencyEval.NEUTRAL) == ModeOp.NEUTRAL` | `neutral_encapsulation.py` | REQUIRED |
| I-MOD-03 | `Modes.lean::ModeOp.fromEval_preserve` | `fromEval(preserve) == modeC`. | `ModeOp.from_eval(ConsistencyEval.PRESERVE) == ModeOp.MODE_C` | `mode_c_dispatch.py` | REQUIRED |
| I-MOD-04 | `Modes.lean::cogito_triggers_modeC` | Cogito eval always fires Mode C. | `ModeOp.from_eval(ptcns.eval(COGITO_ID)) == ModeOp.MODE_C` | `cogito_invariants.py` | REQUIRED |
| I-MOD-05 | (Plan convention, no Lean theorem) | `fromEval` never returns `ModeOp.MODE_B`. | `ModeOp.from_eval(e) != ModeOp.MODE_B` for every `e` in `ConsistencyEval` | `mode_a_dispatch.py` | REQUIRED |

### `brain/tlica/iboundary.py` — `boundary`

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-IBND-01 | `IBoundary.lean::boundary_excludes_neutral` | `boundary ∩ neutralContents == ∅`. | `boundary & ptcns.neutral_contents == set()` | `mode_a_dispatch.py` | REQUIRED |
| I-IBND-02 | `IBoundary.lean::cogito_in_boundary` | Cogito is in the boundary. | `COGITO_ID in boundary(msi, ptcns)` | `cogito_invariants.py` | REQUIRED |
| I-IBND-03 | `IBoundary.lean::mem_boundary_iff` | `x ∈ boundary ↔ eval(x) ∈ {preserve, damage}`. | `x in boundary ⇔ ptcns.eval(x) in {PRESERVE, DAMAGE}` | `mode_a_dispatch.py` | REQUIRED |
| I-IBND-04 | `IBoundary.lean::boundary_not_neutral` | `x ∈ boundary ⇒ eval(x) ≠ neutral`. | Implied by I-IBND-03; tested in same fixture. | `mode_a_dispatch.py` | REQUIRED |
| I-IBND-05 | `IBoundary.lean::contestableBoundary` | Currently aliased to `boundary` (refinement deferred). | Python `contestable_boundary` is an alias; not exercised. | — | DEFERRED |

### `brain/tlica/preservation.py` — `PreservationRanking`

> **v0 stub signature (cogito-gated):**
> ```python
> def rank(S: frozenset[ContentID]) -> Fraction:
>     if COGITO_ID not in S:
>         return Fraction(0)
>     return Fraction(len(S & msi.contents), max(1, len(msi.contents)))
> ```
> This satisfies `rank_nonneg`, `cogito_necessity`, `no_cogito_zero_rank`, `msi_maximality`, and (by construction over the simple stub) `msi_monotonicity`.

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-PRES-01 | `PreservationRanking.lean::PreservationRanking.rank_nonneg` | Every set's rank is non-negative. | `all(pi.rank(S) >= 0 for S in test_sets)` | `minimal.py` | REQUIRED |
| I-PRES-02 | `PreservationRanking.lean::PreservationRanking.cogito_necessity` (Axiom 4.3.1) | Rank > 0 implies cogito in set. | `for S in test_sets: pi.rank(S) > 0 ⇒ COGITO_ID in S` | `minimal.py` | REQUIRED |
| I-PRES-03 | `PreservationRanking.lean::PreservationRanking.msi_maximality` (Axiom 4.3.2) | MSI realizes rank maximum. | `all(pi.rank(S) <= pi.rank(msi.contents) for S in test_sets)` | `minimal.py` | REQUIRED |
| I-PRES-04 | `PreservationRanking.lean::no_cogito_zero_rank` | Sets without cogito have rank 0. | `pi.rank(S) == 0` when `COGITO_ID not in S` | `minimal.py` | REQUIRED |
| I-PRES-05 | `PreservationRanking.lean::PreservationRanking.msi_monotonicity` (Axiom 4.3.3) | Conditional MSI-component monotonicity. | Holds by construction under the cogito-gated stub; covered by `minimal.py` sampling. | `minimal.py` | STRUCTURAL |

### `brain/tlica/project_map.py` — `ProjectMap`

> **Python Protocol exposes `natural_dynamics` explicitly:**
> ```python
> class ProjectMap(Protocol):
>     no_action: Act
>     def project(self, action: Act, profile: ScalarProfile) -> ScalarProfile: ...
>     def natural_dynamics(self, profile: ScalarProfile) -> ScalarProfile: ...
> ```
> v0 deterministic stub: `natural_dynamics(P) = P` (identity); `project(NOOP, P) = natural_dynamics(P)`.

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-PMAP-01 | `ProjectMap.lean::ProjectMap` field `noAction` | The action space has a designated no-action element. | `proj.no_action is Act.NOOP` | `action_selection.py` | STRUCTURAL |
| I-PMAP-02 | `ProjectMap.lean::ProjectMap.identity_action_natural` (Axiom 5.3.1) | `project(noAction, P)` equals natural dynamics. | `profile_equiv(proj.project(proj.no_action, P), proj.natural_dynamics(P))` | `trajectory_step.py` | REQUIRED |
| I-PMAP-03 | `ProjectMap.lean::ProjectMap.noAction_projects` | `project(noAction, P)` is well-defined. | Total function — Python type system enforces. | — | STRUCTURAL |

### `brain/tlica/pce.py` — foundation-default `PCE`

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-PCE-01 | `PCE.lean::PCE.nonneg` | Foundation PCE is non-negative. | `PCE(msi, pi, proj, a) >= 0` | `projected_pce.py` | REQUIRED |
| I-PCE-02 | `PCE.lean::PCE.eq_rank_msi_contents` | Foundation PCE equals `pi.rank(msi.contents)`. | `PCE(msi, pi, proj, a) == pi.rank(msi.contents)` | `projected_pce.py` | REQUIRED |
| I-PCE-03 | `PCE.lean::PCE.bounded_by_msi_max` | Foundation PCE is ≤ `pi.rank(msi.contents)`. | `PCE(...) <= pi.rank(msi.contents)` | `projected_pce.py` | REQUIRED |
| I-PCE-04 | `PCE.lean::PCE.all_actions_equal` | Foundation PCE is action-constant. | `all(PCE(..., a) == PCE(..., b) for a, b in pairs(Act))` | `projected_pce.py` | REQUIRED |
| I-PCE-05 | (Plan rule, no Lean theorem) | Action selection never reads foundation PCE. | Static check: `agency.py` never imports `pce.PCE`. Enforced by import-graph audit in `invariants.run`. | — | STRUCTURAL |

### `brain/tlica/action_projection.py` — `FutureMSIModel`, `GlobalPreservationRanking`, `ProjectedPCE`

> **v0 `GlobalPreservationRanking` stub:** `rank(S) = Fraction(len(S), max(1, |universe|))`. Non-negative and monotone by construction. (No cogito gating — only `PreservationRanking` over an MSI domain carries cogito necessity; the global rank is over universal-domain content sets.)

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-APRJ-01 | `ActionProjection.lean::FutureMSIModel.domain_match` | `(msiOf P).profile.domain = P.domain`. | `fam.msi_of(P).profile.domain == P.domain` for every `P` queried | `projected_pce.py` | REQUIRED |
| I-APRJ-02 | `ActionProjection.lean::GlobalPreservationRanking.rank_nonneg` | Global rank is ≥ 0. | `global_rank.rank(S) >= 0` | `projected_pce.py` | REQUIRED |
| I-APRJ-03 | `ActionProjection.lean::GlobalPreservationRanking.monotone` | `S ⊆ T ⇒ rank(S) ≤ rank(T)`. | `global_rank.rank(S) <= global_rank.rank(T)` for sampled `S ⊆ T` | `projected_pce.py` | REQUIRED |
| I-APRJ-04 | `ActionProjection.lean::ProjectedPCE.nonneg` | Projected PCE is ≥ 0. | `projected_pce(fam, gr, proj, P, a) >= 0` | `projected_pce.py` | REQUIRED |
| I-APRJ-05 | `ActionProjection.lean::ProjectedPCE.eq_of_future_contents_eq` | Equal lifted future contents ⇒ equal projected PCE. | If `future_contents(a) == future_contents(b)` then `projected_pce(a) == projected_pce(b)` | `projected_pce.py` | REQUIRED |
| I-APRJ-06 | `ActionProjection.lean::ProjectedPCE.monotone_of_future_contents_subset` | `future_contents(b) ⊆ future_contents(a) ⇒ projected_pce(b) ≤ projected_pce(a)`. | Compute and assert. | `projected_pce.py` | REQUIRED |

### `brain/tlica/agency.py` — `FeasibilityModel`, selection

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-AGN-01 | `Agency.lean::FeasibilityModel.noAction_feasible` | `noAction ∈ feasible(P)` for every `P`. | `proj.no_action in ctx.feasible(P)` | `action_selection.py` | REQUIRED |
| I-AGN-02 | `Agency.lean::AgencyWitness.selected_feasible` | The selected action is feasible. | `witness.selected in ctx.feasible(P)` | `action_selection.py` | REQUIRED |
| I-AGN-03 | `Agency.lean::AgencyWitness.selected_max` | Selected action maximizes feasible projected PCE. | `all(feasibleProjectedPCE(ctx, P, b) <= feasibleProjectedPCE(ctx, P, witness.selected) for b in ctx.feasible(P))` | `action_selection.py` | REQUIRED |
| I-AGN-04 | `Agency.lean::not_exists_feasible_strictly_higher_of_selects` | No feasible alternative strictly beats the selection. | Derivable from I-AGN-03; tested in same fixture. | `action_selection.py` | REQUIRED |
| I-AGN-05 | `Agency.lean::exists_selectsFeasibleAction_of_finite_feasible` | Finite non-empty feasible set ⇒ a maximizer exists. | Constructor: `select(ctx, P)` succeeds when `len(ctx.feasible(P)) > 0`. | `action_selection.py` | REQUIRED |
| I-AGN-06 | `Agency.lean::feasibleProjectedPCE_eq_projectedPCE` | Agency-context projected PCE equals direct `ProjectedPCE`. | `ctx.feasible_projected_pce(P, a) == projected_pce(ctx.fam, ctx.global_rank, ctx.proj, P, a)` | `action_selection.py` | REQUIRED |

### `brain/tlica/trajectory.py` — `ProfileTrajectory`, `generatedBy`, step distances

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-TRJ-01 | `TemporalTrajectory.lean::generatedBy_step` | `profile_at(n+1) == project(action_at(n), profile_at(n))`. | `profile_equiv(traj.profile_at(n+1), ctx.proj.project(sched.action_at(n), traj.profile_at(n)))` | `trajectory_step.py` | REQUIRED |
| I-TRJ-02 | `TemporalTrajectory.lean::stepUnionDistance_nonneg` | Adjacent union distance ≥ 0. | `step_union_distance(traj, n) >= 0` | `trajectory_step.py` | REQUIRED |
| I-TRJ-03 | `TemporalTrajectory.lean::stepUnionDistance_le_one` | Adjacent union distance ≤ 1. | `step_union_distance(traj, n) <= 1` | `trajectory_step.py` | REQUIRED |
| I-TRJ-04 | `TemporalTrajectory.lean::stepSharedDistance_top_iff` | Empty shared domain ⇔ shared distance is `inf`. | `step_shared_distance(traj, n) == math.inf` iff `domain_n & domain_{n+1} == set()` | `trajectory_step.py` | REQUIRED |
| I-TRJ-08 | `TemporalTrajectory.lean::stepSharedDistance_nonneg` | Adjacent shared distance ≥ 0. | `step_shared_distance(traj, n) >= 0` (treating `math.inf >= 0`) | `trajectory_step.py` | REQUIRED |
| I-TRJ-09 | `TemporalTrajectory.lean::stepSharedDistance_le_one_of_nonempty` | Non-empty shared domain ⇒ shared distance ≤ 1. | If `domain_n & domain_{n+1} != set()`: `step_shared_distance(traj, n) <= 1` | `trajectory_step.py` | REQUIRED |
| I-TRJ-05 | `TemporalTrajectory.lean::stochasticTrajectory_deferred` | Stochastic trajectory is not formalized. | Surface only — no runtime path. | — | DEFERRED |
| I-TRJ-06 | `TemporalTrajectory.lean::phenomenologicalDuration_deferred` | Phenomenological duration is not formalized. | Surface only. | — | DEFERRED |
| I-TRJ-07 | `TemporalTrajectory.lean::temporalContinuityMetric_deferred` | Temporal continuity metric is not formalized. | Surface only. | — | DEFERRED |

### `brain/tlica/comparison/pointwise.py` — `dInfUnion`, `dInfShared`

> **Computable, finite-domain implementations:**
> ```python
> def d_inf_union(f, g):
>     vals = [abs(f.zero_extend(x) - g.zero_extend(x)) for x in f.domain | g.domain]
>     return max(vals) if vals else Fraction(0)
>
> def d_inf_shared(f, g):
>     shared = f.domain & g.domain
>     if not shared:
>         return math.inf
>     return max(abs(f.zero_extend(x) - g.zero_extend(x)) for x in shared)
> ```

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-PWS-01 | `Pointwise.lean::dInfUnion_nonneg` | `dInfUnion(f, g) ≥ 0`. | `d_inf_union(f, g) >= 0` | `profile_distance.py` | REQUIRED |
| I-PWS-02 | `Pointwise.lean::dInfUnion_symm` | `dInfUnion(f, g) == dInfUnion(g, f)`. | `d_inf_union(f, g) == d_inf_union(g, f)` | `profile_distance.py` | REQUIRED |
| I-PWS-03 | `Pointwise.lean::dInfUnion_self` | `dInfUnion(f, f) == 0`. | `d_inf_union(f, f) == 0` | `profile_distance.py` | REQUIRED |
| I-PWS-04 | `Pointwise.lean::dInfUnion_le_one` | `dInfUnion(f, g) ≤ 1`. | `d_inf_union(f, g) <= 1` | `profile_distance.py` | REQUIRED |
| I-PWS-05 | `Pointwise.lean::dInfUnion_triangle` | `dInfUnion(f, h) ≤ dInfUnion(f, g) + dInfUnion(g, h)`. | Triangle inequality across three test profiles. | `profile_distance.py` | REQUIRED |
| I-PWS-06 | `Pointwise.lean::dInfShared_nonneg` | `dInfShared(f, g) ≥ 0`. | `d_inf_shared(f, g) >= 0` (with `math.inf >= 0`) | `profile_distance.py` | REQUIRED |
| I-PWS-07 | `Pointwise.lean::dInfShared_symm` | `dInfShared(f, g) == dInfShared(g, f)`. | `d_inf_shared(f, g) == d_inf_shared(g, f)` | `profile_distance.py` | REQUIRED |
| I-PWS-08 | `Pointwise.lean::dInfShared_self_of_nonempty` | Non-empty domain ⇒ `dInfShared(f, f) == 0`. | If `f.domain != set()`: `d_inf_shared(f, f) == 0` | `profile_distance.py` | REQUIRED |
| I-PWS-09 | `Pointwise.lean::dInfShared_top_iff` | Empty intersection ⇔ `dInfShared(f, g) == ⊤`. | `d_inf_shared(f, g) == math.inf` iff `f.domain & g.domain == set()` | `profile_distance.py` | REQUIRED |
| I-PWS-10 | `Pointwise.lean::dInfShared_le_one_of_nonempty` | Non-empty intersection ⇒ `dInfShared(f, g) ≤ 1`. | If shared non-empty: `d_inf_shared(f, g) <= 1` | `profile_distance.py` | REQUIRED |

### `brain/tlica/integration_graph.py` — strict ρ-bound

> Sample with moderate `C` values. Under `Fraction`, exactness removes float-rounding concerns at the limit.

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-INT-01 | `IntegrationGraph.lean::strict_rho_bound` (Lemma 2.4.2) | `C ≥ 0 ⇒ C/(1+C) < 1`. | For sampled `C` in `[Fraction(0), Fraction(1, 10), Fraction(1), Fraction(10), Fraction(1000)]`: `C / (1 + C) < 1` | `profile_distance.py` | REQUIRED |
| I-INT-02 | `IntegrationGraph.lean::rho_nonneg` | `C/(1+C) ≥ 0` for `C ≥ 0`. | For sampled `C ≥ 0`: `C / (1 + C) >= 0` | `profile_distance.py` | REQUIRED |

### `brain/tlica/phi_coordinate.py` — φ-coordinate

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-PHI-01 | `PhiCoordinate.lean::phiCogito` | `φ(cogito) = 1 - δ`. | Requires non-Archimedean δ; v0 drops δ. Module exposes `phi_cogito()` as docstring reference only. | — | DEFERRED |
| I-PHI-02 | `PhiCoordinate.lean::cogito_unique_phi_supremum` (Proposition 3.3.7) | Cogito is the unique φ-supremum. | Not exercised in v0; φ-coordinate is documentation-level. | — | DEFERRED |
| I-PHI-03 | `PhiCoordinate.lean::two_delta_minus_real_in_DPhi` | `D_φ ⊋ (1-δ-ℝ_{≥0})`. | Requires δ. | — | DEFERRED |

### `brain/tlica/affect.py` — affect kernel

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-AFF-01 | `DifferentiatedAffect.lean::pceValence_trichotomy` | Every (baseline, action) is supportive OR neutral OR defeating. | At least one of the three valence predicates holds. | `projected_pce.py` | REQUIRED |
| I-AFF-02 | `DifferentiatedAffect.lean::pceSupportive_iff` | Supportive ⇔ `baseline < action` in projected PCE. | Per-sample biconditional check. | `projected_pce.py` | REQUIRED |
| I-AFF-03 | `DifferentiatedAffect.lean::pceDefeating_iff` | Defeating ⇔ `action < baseline` in projected PCE. | Per-sample biconditional check. | `projected_pce.py` | REQUIRED |
| I-AFF-04 | `DifferentiatedAffect.lean::pceNeutral_iff` | Neutral ⇔ projected PCE values equal. | Per-sample biconditional check. | `projected_pce.py` | REQUIRED |
| I-AFF-11 | `DifferentiatedAffect.lean::pceSupportive_not_neutral` | Supportive excludes neutral. | `pce_supportive(...) ⇒ not pce_neutral(...)` | `projected_pce.py` | REQUIRED |
| I-AFF-12 | `DifferentiatedAffect.lean::pceSupportive_not_defeating` | Supportive excludes defeating. | `pce_supportive(...) ⇒ not pce_defeating(...)` | `projected_pce.py` | REQUIRED |
| I-AFF-13 | `DifferentiatedAffect.lean::pceDefeating_not_neutral` | Defeating excludes neutral. | `pce_defeating(...) ⇒ not pce_neutral(...)` | `projected_pce.py` | REQUIRED |
| I-AFF-05 | `DifferentiatedAffect.lean::no_affectKernel_of_branch_and_pce_collapse` | Collapsed branch profiles + collapsed PCE ⇒ no affect-kernel witness. | Constructor `AffectKernelWitness(...)` raises when every feasible action pair has equal branch profiles AND equal projected PCE. | `affect_kernel_collapse.py` | REQUIRED |
| I-AFF-06 | `DifferentiatedAffect.lean::temporalAffectIntensity_le_one` | `temporal_affect_intensity(traj, n) ≤ 1`. | `temporal_affect_intensity(traj, n) <= 1` | `trajectory_step.py` | REQUIRED |
| I-AFF-07 | `DifferentiatedAffect.lean::namedAffectTaxonomy_deferred` | Named affect taxonomy is prose-only. | Surface only. | — | DEFERRED |
| I-AFF-08 | `DifferentiatedAffect.lean::loveConstitutiveExtension_deferred` | Love as constitutive extension is prose-only. | Surface only. | — | DEFERRED |
| I-AFF-09 | `DifferentiatedAffect.lean::substrateAffectPathway_deferred` | Substrate affect pathways prose-only. | Surface only. | — | DEFERRED |
| I-AFF-10 | `DifferentiatedAffect.lean::sourceOpacityAffect_deferred` | Source-opacity affect prose-only. | Surface only. | — | DEFERRED |

### `brain/tlica/free_will.py` — branch-sensitive agency witnesses (surface only in v0)

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-FW-01 | `FreeWill.lean::FreeWillWitness` (structure) | A free-will witness carries selected, alternative, agency, live-alt, and branch-distinct fields. | Surface only; type exposed, not constructed in v0. | — | NOT-EXERCISED |
| I-FW-02 | `FreeWill.lean::PCEFreeWillWitness` (structure) | PCE-differentiated free-will witness exists as a stronger form. | Surface only; type exposed, not constructed in v0. | — | NOT-EXERCISED |
| I-FW-03 | `FreeWill.lean::no_freeWillWitness_of_all_branch_contents_equal` | Collapsed branch future contents ⇒ no free-will witness. | Surface only; not exercised in v0. | — | NOT-EXERCISED |
| I-FW-04 | (Per `Agency.lean` docstring) | Free-will branch semantics remain deferred. | No fixture exercises branch dynamics. | — | DEFERRED |

### `brain/tlica/profile_iso.py` — optional coherence relation

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-ISO-01 | `ProfileIso.lean::ProfileIso.refl` | `ProfileIso P P` always holds. | `ProfileIso.refl(P)` returns a valid iso. | — | STRUCTURAL |
| I-ISO-02 | `ProfileIso.lean::ProfileIso.symm` | Iso is symmetric. | `ProfileIso.symm(h)` valid for any iso `h`. | — | STRUCTURAL |
| I-ISO-03 | `ProfileIso.lean::ProfileIso.trans` | Iso is transitive. | `ProfileIso.trans(h1, h2)` valid for compatible `h1, h2`. | — | STRUCTURAL |

### `brain/toce_core.py` — TOCE Boolean classifier layer

| ID | Lean source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-TOCE-01 | `TOCE_Core.lean::classifyContent` | Classification branches only on `available`, `verificationPath`, `retrievable`. | Truth table over 16 `ContentState` cases; `operative` does not affect class. | `content_classification.py` | REQUIRED |
| I-TOCE-02 | `TOCE_Core.lean::available_content_clear_or_fuzzy` | `available=true ⇒ classifyContent ∈ {consciousClear, consciousFuzzy}`. | Truth-table subset check. | `content_classification.py` | REQUIRED |
| I-TOCE-03 | `TOCE_Core.lean::unavailable_content_latent_or_unconscious` | `available=false ⇒ classifyContent ∈ {latentRetrievable, unconsciousOperative}`. | Truth-table subset check. | `content_classification.py` | REQUIRED |
| I-TOCE-04 | `TOCE_Core.lean::clear_requires_availability` | `consciousClear ⇒ available=true`. | Truth-table check. | `content_classification.py` | REQUIRED |
| I-TOCE-05 | `TOCE_Core.lean::fuzzy_requires_availability` | `consciousFuzzy ⇒ available=true`. | Truth-table check. | `content_classification.py` | REQUIRED |

### `brain/llm/` — LLM client seam (Phase 2 v1)

> The LLM-backed `PtCns.eval` layer. Foundation `PtCns` (the v0 dataclass) is unchanged; `LLMBackedPtCns` is a duck-typed alternative that consults an `LLMClient` Protocol.

| ID | Source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-LLM-01 | Plan convention (Phase 2 v1) | `PtCns.eval` returns one of `{PRESERVE, DAMAGE, NEUTRAL}` after retry resolution. Up to 3 attempts; final failure raises and the tick fails. | `LLMBackedPtCns(content)` returns `ConsistencyEval` member; never returns sentinel "invalid"; raises `ValueError` on Nth-attempt failure. | `llm_protocol.py` | REQUIRED |
| I-LLM-02 | Plan convention (Phase 2 v1) | Cached identical prompts produce identical outputs. | Same prompt routed twice through `CachedClient` returns same response without re-calling the inner client. | `llm_protocol.py` | OBSERVED |
| I-LLM-03 | I-PTC-01 (cogito_invariance) | LLM-backed `PtCns.eval(COGITO_ID)` short-circuits to `PRESERVE` without an LLM call. | `LLMBackedPtCns.eval(COGITO_ID) == PRESERVE` and the underlying client is not called. | `llm_protocol.py` | REQUIRED |
| I-LLM-04 | Plan convention (Phase 2 v1) | The LLM-backed implementation honors the `LLMClient` Protocol — `eval_consistency(prompt: str) -> str`. No direct HTTP coupling, no provider lock-in. | `isinstance(client, LLMClient)` and `LLMBackedPtCns` accepts any conforming client. | `llm_protocol.py` | STRUCTURAL |

### `brain/trace.py` — Cognition trace seam (Phase 2 v1.1)

> The togglable observation seam: a `CognitionTracer` Protocol with three backends (`NullTracer`, `MemoryTracer`, `FileTracer`). The tracer is observation-only — `tick()` output must be byte-identical whether a tracer is present or not. Toggle via `BRAIN_TRACE_PATH` env var or `--trace` CLI flag; default is `NullTracer()`.

| ID | Source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-TRACE-01 | Plan convention (Phase 2 v1.1) | The tracer is observation-only. `tick(state, events, client, tracer)` produces identical `(BrainState, TickRecord)` output regardless of which `CognitionTracer` backend is supplied. | Run the first scenario through each of `{NullTracer(), MemoryTracer(), FileTracer(tmp_path)}` with the same MockClient seed; assert all three final `BrainState` values are equal and all three `mode_trace` sequences are identical. | `trace_v1_1.py` | STRUCTURAL |
| I-TRACE-02 | Plan convention (Phase 2 v1.2 baseline hardening) | Tracer record failures do not propagate. `tick()` output is identical whether `tracer.record` raises or not. `SafeTracer` wraps every factory-built tracer and swallows backend exceptions. | Run the scenario through a `_TracerThatAlwaysRaises` wrapped in `SafeTracer`; assert resulting `BrainState` and `mode_trace` equal the `NullTracer` baseline. | `trace_v1_1.py` | STRUCTURAL |
| I-TRACE-03 | Plan convention (trace boundary hardening) | Tracer payloads cannot overwrite reserved event-envelope keys. `MemoryTracer` and `FileTracer` reject payloads containing `type`, `timestamp_ns`, or `tick_id`; `SafeTracer` preserves observation-only behavior by swallowing trace-sink validation failures. | Raw `MemoryTracer` and `FileTracer(tmp_path)` raise `ValueError` naming I-TRACE-03 on reserved keys; `SafeTracer(MemoryTracer())` and `SafeTracer(FileTracer(tmp_path))` swallow the same validation failure without recording an invalid event. | `trace_v1_1.py` | STRUCTURAL |

### Behavioral (Phase 2 v1)

| ID | Source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-BHV-01 | Plan convention (Phase 2 v1, criterion 3) | Given a forced eval sequence (via MockClient seeded from `expected_eval`), the resulting mode trace matches `expected_mode`. Verifies the eval→mode→state-update orchestration; *does not* verify LLM behavior. | After running `scenarios/first_scenario_v1.json`: `actual_modes == [tick["expected_mode"] for tick in scenario.ticks]`. | `scenario_v1.py` | REQUIRED |

> **Note.** I-BHV-01 verifies the brain's deterministic orchestration of eval→mode under controlled MockClient inputs. The actual LLM behavioral check (does the LLM correctly classify the scenario's percepts?) happens in `python -m brain.scenario run …` with a real `AnthropicAPIClient` and is not part of the runner gate.

---

## Modules with no v0-required invariants

### `brain/tlica/mode_aggregation.py`, `brain/tlica/dynamics.py`

These cover Proposition 2.5.1 (convergence of the mode-aggregation series) and Proposition 5.7.2 (uniform convergence by M-test). Both reason about genuinely infinite sums; v0 commits to finite-at-each-tick (summation over finite content store). Python equivalents may expose a truncated `finite_mode_aggregation(...)` for fixture use, but no invariant in v0 depends on convergence. Status: **NOT-EXERCISED** in v0; thin module with docstring + truncated computation.

### `brain/tlica/non_reducibility.py`

Covers Theorem 6.5.1 (formal non-reducibility). Requires the non-Archimedean δ that v0 drops. Status: **DEFERRED** in v0; docstring-only.

### `brain/tlica/comparison/shell_refinement.py`, `brain/tlica/comparison/pseudo_emetric.py`

Shell-stratified distance bounds and pseudo-emetric instance. v0 exposes the types so the public surface matches the Lean, but no fixture drives them. Status: **NOT-EXERCISED**.

---

## Cross-cutting / runtime-only invariants

These are not Lean theorems but are needed for the runtime to be coherent. Owned by `brain/invariants.py`, `brain/tlica/builders.py`, and `brain/tick.py`.

| ID | Source | Proposition | Python assertion | Owning module |
|---|---|---|---|---|
| I-RT-01 | Plan convention | `COGITO_ID` does not appear in any user-supplied `PerceptEvent`. | At ingest: `event.content_id != COGITO_ID` raises. | `brain/io_types.py` |
| I-RT-02 | Plan convention | Profile values stay in `[0, 1]` across every tick transition. | After each mode operator: re-assert I-PROF-01 and I-PROF-02. | `brain/tick.py` |
| I-RT-03 | Plan convention | MSI density is maintained across transitions. | After each mode operator: re-assert I-MSI-03. | `brain/tick.py` |
| I-RT-04 | Plan convention | PtCns evaluations remain a total function over the current profile domain. | After each tick: assert `set(ptcns.eval_map.keys()) == set(profile.domain)`. | `brain/tick.py` |
| I-RT-05 | Plan convention | The tick log is append-only; no state is mutated retroactively. | `TickRecord` instances are frozen dataclasses. | `brain/io_types.py` |
| I-RT-06 | Plan convention | Builders fail loudly on invalid construction (no silent clamping; out-of-bounds values raise). | `make_profile_with_cogito`, `make_msi`, `make_ptcns` raise `ValueError` on violation. | `brain/tlica/builders.py` |
| I-RT-07 | Plan convention | Every projected profile produced by v0 `ProjectMap` preserves `COGITO_ID` at value `1`. | After every `project(a, P)`: `COGITO_ID in projected.domain and projected.values[COGITO_ID] == 1`. | `brain/tlica/project_map.py` + `brain/tick.py` |

### Runtime / tick orchestration (Phase 2 v1 / v1.2)

> *(I-RT-08 is enforced by `brain/tick.py::assert_state_invariants`. New runtime-applicable rows must be added there too — see that function's MAINTENANCE CONTRACT docstring.)*

| ID | Source | Proposition | Python assertion | Owning module | Fixture | Status |
|---|---|---|---|---|---|---|
| I-RT-08 | Plan convention (Phase 2 v1) | The invariant runner is green after every tick in any scenario. The kernel never sees an invalid state mid-trajectory. | After each `tick(state, events, client)` call, `brain/tick.py::assert_state_invariants(new_state)` re-asserts the runtime-applicable v0.2 rows; the scenario fixture asserts no exception escapes the loop. | `brain/tick.py` | `scenario_v1.py` | REQUIRED |
| I-RT-09 | Plan convention (Phase 2 v1) | `PerceptEvent.text` is non-empty and printable. | At ingest: `event.text and event.text.isprintable()`; raises `ValueError` otherwise. | `brain/io_types.py` | `scenario_v1.py` | STRUCTURAL |
| I-RT-10 | Plan convention (Phase 2 v1) | Content registry retains text metadata across ticks for content already integrated into the profile. | `len(registry.texts) >= len(profile.domain) - 1` (one less because cogito has no text). | `brain/io_types.py` | `scenario_v1.py` | STRUCTURAL |
| I-RT-11 | Plan convention (Phase 2 v1.2 baseline hardening) | `tick()` rejects events list with length > 1 in v1 semantics. Multi-event mode aggregation is deferred. | `tick(state, [e1, e2], client)` raises `ValueError` naming I-RT-11. | `brain/tick.py` | `scenario_v1.py` | STRUCTURAL |
| I-RT-12 | Plan convention (Phase 2 v1.2 baseline hardening) | `tick()` rejects `PerceptEvent` whose `content_id` is already in `state.profile.domain`. v1 promotion is one-shot per content. | `tick(state, [event_with_existing_id], client)` raises `ValueError` naming I-RT-12. | `brain/tick.py` | `scenario_v1.py` | STRUCTURAL |

### Meta / runner integrity (Phase 2 v1.2)

> *I-CAT-01 has fixture `_meta` because the check is enforced at runner entry rather than by a fixture function alone. A stub `@register` entry inside `brain/invariants.py` re-runs the audit so the row also satisfies its own registration requirement. See "Validation procedure" below.*

| ID | Source | Proposition | Python assertion | Owning module | Fixture | Status |
|---|---|---|---|---|---|---|
| I-CAT-01 | Plan convention (Phase 2 v1.2 baseline hardening) | Every catalog row with status REQUIRED or STRUCTURAL has a registered check. The runner refuses to claim "all green" if any row is missing registration. | After load + import of `FIXTURE_MODULES`, registered IDs ⊇ catalog's REQUIRED ∪ STRUCTURAL IDs (excluding `_meta`-fixture rows that the runner enforces directly); mismatch raises before any check runs. | `brain/invariants.py` | `_meta` | STRUCTURAL |

---

## Inherited deferrals (from `CLAIM_GUARDRAILS.md` and Lean deferred markers)

| Deferral | Source | Notes |
|---|---|---|
| RCX (religiously charged experience) | `CLAIM_GUARDRAILS.md` + `AGENTS.md` exclusions | Prose-only; not Lean-ready. |
| Named affect taxonomy | `DifferentiatedAffect.lean::namedAffectTaxonomy_deferred` | I-AFF-07. |
| Love as constitutive extension | `DifferentiatedAffect.lean::loveConstitutiveExtension_deferred` | I-AFF-08. |
| Substrate affect pathways | `DifferentiatedAffect.lean::substrateAffectPathway_deferred` | I-AFF-09. |
| Source-opacity affect | `DifferentiatedAffect.lean::sourceOpacityAffect_deferred` | I-AFF-10. |
| Stochastic projection | `TemporalTrajectory.lean::stochasticTrajectory_deferred` | I-TRJ-05. |
| Phenomenological duration | `TemporalTrajectory.lean::phenomenologicalDuration_deferred` | I-TRJ-06. |
| Temporal continuity metric | `TemporalTrajectory.lean::temporalContinuityMetric_deferred` | I-TRJ-07. |
| Contestable-boundary refinement | `IBoundary.lean::contestableBoundary` (aliased to `boundary`) | I-IBND-05. |
| Free-will branch semantics | `Agency.lean` / `FreeWill.lean` docstrings | I-FW-04. |
| Shell-stratified comparison machinery | `ShellRefinement.lean` (not exercised in v0) | Surface only. |
| Pseudo-emetric instance | `PseudoEMetric.lean` (not exercised in v0) | Surface only. |
| φ-coordinate / non-Archimedean δ | Required only by `NonReducibility.lean::formal_non_reducibility` and `PhiCoordinate.lean::phiCogito`. v0 drops δ. | I-PHI-01..03. |
| Compatibility aliases | `GeneralActionProjection.lean`, `DefaultAction`, `UnitDefaultProjectMap` | Not mirrored in Python. |

---

## v0 fixture roster

| Fixture | Drives invariant IDs |
|---|---|
| `minimal.py` | I-PROF-01, I-PROF-02, I-MSI-03, I-MSI-04, I-MSI-06, I-PTC-02, I-PTC-03, I-PRES-01..05 |
| `cogito_invariants.py` | I-MSI-01, I-MSI-02, I-MSI-05, I-PTC-01, I-PTC-04, I-PTC-05, I-MOD-04, I-IBND-02 |
| `content_classification.py` | I-TOCE-01..05 |
| `profile_distance.py` | I-PROF-03..07, I-PWS-01..10, I-INT-01..02 |
| `mode_a_dispatch.py` | I-MOD-01, I-MOD-05, I-IBND-01, I-IBND-03, I-IBND-04 |
| `mode_c_dispatch.py` | I-MOD-03 |
| `neutral_encapsulation.py` | I-MOD-02 |
| `action_selection.py` | I-AGN-01..06, I-PMAP-01 |
| `projected_pce.py` | I-PCE-01..04, I-APRJ-01..06, I-AFF-01..04, I-AFF-11..13 |
| `affect_kernel_collapse.py` | I-AFF-05 |
| `trajectory_step.py` | I-PMAP-02, I-TRJ-01..04, I-TRJ-08, I-TRJ-09, I-AFF-06 |
| `llm_protocol.py` | I-LLM-01, I-LLM-02 (OBSERVED), I-LLM-03, I-LLM-04 |
| `scenario_v1.py` | I-RT-08, I-RT-09, I-RT-10, I-RT-11, I-RT-12, I-BHV-01 |
| `trace_v1_1.py` | I-TRACE-01, I-TRACE-02, I-TRACE-03 |

14 fixtures total. I-CAT-01 is enforced at runner entry; its catalog fixture column is `_meta`.

---

## Validation procedure

`python -m brain.invariants run` walks every `REQUIRED` row, loads each named fixture, and reports a structured pass/fail table. v0 is complete when every row's row-id appears in the green column. The runner refuses to start if any `STRUCTURAL` builder check fails on construction (cogito sentinel, profile bounds, etc.) — those errors fire before any per-tick check. The runner also performs the import-graph audit for I-PCE-05 (`agency.py` never imports `pce.PCE`) and the I-CAT-01 coverage audit (every catalog REQUIRED/STRUCTURAL row has a registered check). Rows whose fixture column is `_meta` are enforced by the runner directly rather than by a fixture file; the runner registers a stub `@register` entry for each so they appear in the run summary.

---

## Pinned decisions

1. **Numeric core = `Fraction`.** `brain/tlica/`, `brain/fixtures/`, `brain/invariants.py` use `fractions.Fraction` throughout. `math.inf` (the single permitted float) represents Lean's `⊤` for empty-intersection `dInfShared`. The `rho()` constructor in `brain/tlica/builders.py` normalizes input at the I/O boundary; `TickRecord` may expose float views for display only.
2. **Three-way split:** `brain/tlica/builders.py` (construction-time preconditions, raises on invalid), `brain/validation.py` (reusable assertion helpers: `profile_equiv`, `is_in_unit_interval`, etc.), `brain/invariants.py` (catalog registry + runner). Dependency graph: `builders → validation`; `invariants → fixtures + validation`; `tick → builders + invariants`.

---

## Summary counts

- **REQUIRED v0 invariants:** 84
- **STRUCTURAL (constructor- or type-enforced, not per-tick asserted):** 16
- **NOT-EXERCISED row-level:** 3 (plus 5 modules covered at module-level in "Modules with no v0-required invariants")
- **DEFERRED row-level:** 12 (plus inherited deferrals table)
- **OBSERVED row-level:** 1 (Phase 2 v1; recorded in run summary, not gating)

Total tabular entries: 116. v0.5 success is gated by the 84 REQUIRED rows + 16 STRUCTURAL rows (the OBSERVED row is logged but does not gate; the new I-CAT-01 runner audit gates separately at startup).

---

## Build order (for Claude Code)

Do not start with `tick.py`. Build the object layer and invariant runner first, in this order:

1. `brain/tlica/profile.py`
2. `brain/tlica/msi.py`
3. `brain/tlica/ptcns.py`
4. `brain/tlica/builders.py`
5. `brain/validation.py`
6. `brain/invariants.py` (catalog registry + runner shell)
7. `brain/fixtures/minimal.py`
8. `brain/fixtures/cogito_invariants.py`

When those eight files pass their assigned invariants under `python -m brain.invariants run`, expand to the remaining modules and fixtures in the dependency order implied by the import graph (`preservation` → `project_map` → `pce` → `action_projection` → `agency` → `trajectory` → `affect`; `comparison/pointwise` parallel to those; `iboundary` after `ptcns`; `toce_core` independent of `brain/tlica/`).
