# brain — TLICA-constrained Python kernel (catalog v0.5)

This package is the TLICA-constrained Python "brain" kernel. Open it, read this file, then read `INVARIANT_CATALOG.md`, then take direction from whichever current kickoff/corrigenda is in flight.

## What this is

A theorem-constrained Python state machine. The TLICA Lean formalization (snapshot in `lean_reference/`) is the *spec*, not the runtime. `INVARIANT_CATALOG.md` (canonical at the version on disk) binds each Lean theorem we honor — plus the engineering-hypothesis rows added by Phase 2 and beyond — to a Python runtime assertion, names the owning module, and assigns it to a fixture. The kernel is healthy when every REQUIRED row reports green.

This is not a brain in any philosophical sense. It is a runtime object that satisfies the structural prerequisites the TLICA theory says a "conscious I" must have — the constraints the Lean is good at enforcing. Whether the theory is right that those structural features are consciousness is untouched.

## What to do first

1. Read `INVARIANT_CATALOG.md`. That is canonical.
2. Read this README's "Constraints" section below for the pre-coding rules.
3. Build (or modify) according to the current kickoff document's build order.
4. Run `bash tools/check_all.sh` (catalog freshness → counts → citations → import audit → runner).
5. The kernel is healthy when every REQUIRED row reports green and all auxiliary gates pass.

Implement from the current `INVARIANT_CATALOG.md` exactly; the catalog is canonical.

## Package contents

| Path | What it is |
|---|---|
| `README.md` | This file. Read first. |
| `INVARIANT_CATALOG.md` | The current catalog spec (see version banner). The spine. |
| `SPEC_UPDATES.md` | How to consult `github.com/femboy2112/lean-scratch` for future spec evolution. |
| `lean_reference/` | Snapshot of the Lean source the catalog cites. Read-only reference. |
| `lean_reference/TLICA.lean` | Top-level Lean aggregator (lists every module imported). |
| `lean_reference/TLICA/` | Every TLICA module the catalog cites. |
| `lean_reference/TOCE_Core.lean` | The TOCE Boolean classifier layer (separate from TLICA proper). |
| `brain/` | The Python kernel: TLICA layer, LLM seam, trace seam, tick orchestration, fixtures. |
| `scenarios/` | Locked scenario JSON files (e.g. `first_scenario_v1.json`). |
| `tools/` | Catalog parser, citation verifier, import audit, snapshot diff, runner wrappers. |

## Catalog history

- **v0.2** — initial Lean-bound catalog (Phase 1 / v0 implementation).
- **v0.3** — +I-LLM-01/02/03/04, +I-RT-08, +I-BHV-01 (Phase 2 v1 LLM-backed `PtCns`).
- **v0.4** — +I-TRACE-01 (Phase 2 v1.1 cognition trace).
- **v0.5** — +I-RT-11, +I-RT-12, +I-TRACE-02, +I-TRACE-03, +I-CAT-01 (Phase 2 v1.2 baseline hardening plus pre-Phase-3.1 trace boundary hardening).

Companion docs (consult the relevant one when editing the catalog):
- `PLAN_CORRIGENDA.md` (v0 plan corrigenda).
- `PHASE2_v1_KICKOFF.md` / `PHASE2_v1_CORRIGENDA.md` (LLM-backed `PtCns`).
- `PHASE2_v1_1_TRACE_KICKOFF.md` (cognition trace).
- `BASELINE_HARDENING_KICKOFF.md` (Phase 2 v1.2, this round).

## Constraints (pre-coding rules — these are pulled from the catalog)

If any of these is unclear at code time, the catalog is canonical. Do not relax them.

### Catalog version

Use `INVARIANT_CATALOG.md` as shipped. Version banner inside should say **v0.5**. Confirmation numbers: **84 REQUIRED · 16 STRUCTURAL · 3 NOT-EXERCISED · 12 DEFERRED · 1 OBSERVED · 14 fixtures**. Run `python -m tools.catalog counts` to verify; the strict gate fails if banner / actual / expected ever drift. If you see anything that looks like 74 REQUIRED, float+EPS, or `Literal[...]` for `Act`, that is an older draft and is wrong.

### Numeric core

All profile values, distances, ranks, and projected-PCE values inside `brain/tlica/`, `brain/fixtures/`, and `brain/invariants.py` are `fractions.Fraction`. Raw `==` is safe and used throughout. The constructor `rho(value: int | float | str | Fraction) -> Fraction` normalizes at the I/O boundary and **raises** if the value is outside `[0, 1]` — never silently clamp. `math.inf` is the only permitted float, representing Lean's `⊤` for empty-intersection `dInfShared`.

### `Act`

```python
from enum import Enum

class Act(str, Enum):
    NOOP = "noop"
    INTEGRATE = "integrate"
    DIFFERENTIATE = "differentiate"
    ENCAPSULATE = "encapsulate"
```

`isinstance(x, Act)` works at runtime; `proj.no_action is Act.NOOP`.

### `PreservationRanking.rank` (cogito-gated)

```python
def rank(S: frozenset[ContentID]) -> Fraction:
    if COGITO_ID not in S:
        return Fraction(0)
    return Fraction(len(S & msi.contents), max(1, len(msi.contents)))
```

This satisfies `rank_nonneg`, `cogito_necessity`, `no_cogito_zero_rank`, `msi_maximality`, and `msi_monotonicity` by construction.

### `GlobalPreservationRanking.rank` (no cogito gating)

```python
def rank(S: frozenset[ContentID]) -> Fraction:
    return Fraction(len(S), max(1, len(universe)))
```

Non-negative and monotone. **No** cogito gating — only `PreservationRanking` over an MSI domain carries cogito necessity.

### `ProjectMap` Protocol

```python
class ProjectMap(Protocol):
    no_action: Act
    def project(self, action: Act, profile: ScalarProfile) -> ScalarProfile: ...
    def natural_dynamics(self, profile: ScalarProfile) -> ScalarProfile: ...
```

v0 deterministic stub: `natural_dynamics(P) = P` (identity); `project(NOOP, P) = natural_dynamics(P)`. Every projected profile **must** preserve `COGITO_ID` at value `1` (I-RT-07).

### `ModeOp` vs `Act` (disjoint namespaces)

`ModeOp` has four members: `MODE_A`, `MODE_B`, `MODE_C`, `NEUTRAL`. `Act` has four: `NOOP`, `INTEGRATE`, `DIFFERENTIATE`, `ENCAPSULATE`. They are not interchangeable. Mode B is parallel — it is **not** triggered by `ModeOp.from_eval`. The mapping from `ModeOp` to default `Act` is a lookup dict, not an identity.

### Action selection routes through `feasibleProjectedPCE` only

`brain/tlica/agency.py` must **never** import `brain.tlica.pce`. Foundation `PCE` is action-constant by Lean theorem (`PCE.all_actions_equal`); using it for action selection would make all actions equivalent. Selection goes through `feasibleProjectedPCE` (which routes through `action_projection.py`). The invariant runner performs an import-graph audit to enforce this (I-PCE-05).

### Free-will branch semantics are deferred

`brain/tlica/free_will.py` exposes surface types (`FreeWillWitness`, `PCEFreeWillWitness`) but no v0 fixture constructs them. Do not add one. Branch semantics are explicitly deferred per `Agency.lean`'s docstring.

### I-AFF-05 is REQUIRED — collapse fixture is mandatory

The `AffectKernelWitness` constructor **must** raise when every feasible action pair has equal branch profiles AND equal projected PCE. This is exercised by `brain/fixtures/affect_kernel_collapse.py`, which is the only fixture driving I-AFF-05.

### Validation file split

```
brain/tlica/builders.py     # construction-time preconditions; raises on invalid input
brain/validation.py         # reusable helpers (profile_equiv, is_in_unit_interval, …)
brain/invariants.py         # catalog registry + runner
```

Dependency graph: `builders → validation`; `invariants → fixtures + validation`; `tick → builders + invariants`. Do not fold validation into builders or builders into invariants.

## Build order

The kernel is already past every v0/v1/v1.1/v1.2 checkpoint. New work
follows the build order in the current kickoff document (see "Catalog
history" above for which is in flight); each kickoff specifies its own
ordering of catalog patch → tooling → modules → fixtures →
verification.

The original v0 eight-file checkpoint and its successor sequencing are
preserved in `ARCHIVE.md` as historical context. Do not use them as
instructions for new work.

## Success criterion

```
bash tools/check_all.sh
```

reports every REQUIRED row green, every STRUCTURAL row green, all
auxiliary gates pass, and OBSERVED rows are reported without gating.

For catalog v0.5, the expected count is:
**84 REQUIRED · 16 STRUCTURAL · 3 NOT-EXERCISED · 12 DEFERRED · 1 OBSERVED**.

The runner also performs the I-PCE-05 import-graph audit (`agency.py`
never imports `pce.py`) and the I-CAT-01 catalog↔registry coverage
audit (every REQUIRED/STRUCTURAL row has a registered check); both must
pass for the runner to claim "all green".

## Spec evolution

The Lean spec on `github.com/femboy2112/lean-scratch` is canonical and will evolve. When it does, the catalog needs to be re-aligned and the code re-validated against the new theorems. See `SPEC_UPDATES.md` for the refresh protocol.

## Things to not do

- Do not implement from stale draft counts or earlier catalog versions. Use the current `INVARIANT_CATALOG.md` exactly.
- Don't introduce modules outside the catalog's module map.
- Don't re-enable a deferred item (RCX, named affect taxonomy, love-as-constitutive-extension, substrate affect pathways, source-opacity affect, stochastic projection, phenomenological duration, temporal continuity metric, contestable-boundary refinement, free-will branch semantics, φ-coordinate / non-Archimedean δ) without an explicit upstream change.
- Don't use `typing.Literal` for `Act`.
- Don't use raw float arithmetic in `brain/tlica/`. Use `Fraction`.
- Don't push to `femboy2112/lean-scratch` — it is read-only from this package's perspective.
