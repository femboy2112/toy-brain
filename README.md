# brain v0 kickoff package

This package is everything Claude Code needs to implement the v0 TLICA-constrained Python "brain" kernel. Open it, read this file, then read `INVARIANT_CATALOG.md`, then start coding from the build order at the bottom of this file.

## What this is

A theorem-constrained Python state machine. The TLICA Lean formalization (snapshot in `lean_reference/`) is the *spec*, not the runtime. `INVARIANT_CATALOG.md` v0.2 binds each Lean theorem we honor to a Python runtime assertion, names the owning module, and assigns it to a fixture. v0 is complete when every REQUIRED row in the catalog asserts green.

This is not a brain in any philosophical sense. It is a runtime object that satisfies the structural prerequisites the TLICA theory says a "conscious I" must have — the constraints the Lean is good at enforcing. Whether the theory is right that those structural features are consciousness is untouched.

## What to do first

1. Read `INVARIANT_CATALOG.md`. That is canonical.
2. Read this README's "Constraints" section below for the pre-coding rules.
3. Build the eight files in the "Build order" section below, in order.
4. Run `python -m brain.invariants run`.
5. v0 is done when every REQUIRED row in the catalog reports green.

Do **not** review the plan or re-audit the catalog. The catalog was already audited twice. Implement from v0.2 exactly.

## Package contents

| Path | What it is |
|---|---|
| `README.md` | This file. Read first. |
| `INVARIANT_CATALOG.md` | The v0.2 spec. 80 REQUIRED rows · 7 STRUCTURAL · 3 NOT-EXERCISED · 12 DEFERRED. The spine. |
| `SPEC_UPDATES.md` | How to consult `github.com/femboy2112/lean-scratch` for future spec evolution. |
| `lean_reference/` | Snapshot of the Lean source the catalog cites. Read-only reference. |
| `lean_reference/TLICA.lean` | Top-level Lean aggregator (lists every module imported). |
| `lean_reference/TLICA/` | Every TLICA module the catalog cites. |
| `lean_reference/TOCE_Core.lean` | The TOCE Boolean classifier layer (separate from TLICA proper). |

## Constraints (pre-coding rules — these are pulled from the catalog)

If any of these is unclear at code time, the catalog is canonical. Do not relax them.

### Catalog version

Use `INVARIANT_CATALOG.md` as shipped. Version banner inside should say **v0.2**. Confirmation numbers: **80 REQUIRED · 7 STRUCTURAL · 3 NOT-EXERCISED · 12 DEFERRED · 11 fixtures**. If you see anything that looks like 74 REQUIRED, float+EPS, or `Literal[...]` for `Act`, that is the older draft and is wrong.

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

Do **not** start with `tick.py`. Build in this order:

1. `brain/tlica/profile.py`
2. `brain/tlica/msi.py`
3. `brain/tlica/ptcns.py`
4. `brain/tlica/builders.py`
5. `brain/validation.py`
6. `brain/invariants.py` (catalog registry + runner shell)
7. `brain/fixtures/minimal.py`
8. `brain/fixtures/cogito_invariants.py`

At this point run `python -m brain.invariants run`. The runner should report green on every REQUIRED row owned by those eight files (these fixtures cover I-PROF-01..02, I-MSI-01..06, I-PTC-01..05, I-MOD-04, I-IBND-02, I-PRES-01..05).

Once that gate is green, expand to the remaining modules in the dependency order implied by the import graph:

- `preservation.py` → `project_map.py` → `pce.py` → `action_projection.py` → `agency.py` → `trajectory.py` → `affect.py`
- `comparison/pointwise.py` can be built in parallel with the above
- `iboundary.py` after `ptcns.py`
- `toce_core.py` is independent of `brain/tlica/`

Then add the remaining fixtures: `content_classification.py`, `profile_distance.py`, `mode_a_dispatch.py`, `mode_c_dispatch.py`, `neutral_encapsulation.py`, `action_selection.py`, `projected_pce.py`, `affect_kernel_collapse.py`, `trajectory_step.py`.

Only after every REQUIRED row is green should you implement `brain/tick.py` and `brain/io_types.py`.

## Success criterion

```
python -m brain.invariants run
```

reports every REQUIRED row green (80 of them, distributed across 11 fixtures). The runner also performs an import-graph audit (I-PCE-05) and refuses to start if any STRUCTURAL builder check fails on construction.

## After v0 lands

The Lean spec on `github.com/femboy2112/lean-scratch` is canonical and will evolve. When it does, the catalog needs to be re-aligned and the code re-validated against the new theorems. See `SPEC_UPDATES.md` for the refresh protocol.

## Things to not do

- Don't review the plan. Implement v0.2 exactly.
- Don't introduce modules outside the catalog's module map.
- Don't re-enable a deferred item (RCX, named affect taxonomy, love-as-constitutive-extension, substrate affect pathways, source-opacity affect, stochastic projection, phenomenological duration, temporal continuity metric, contestable-boundary refinement, free-will branch semantics, φ-coordinate / non-Archimedean δ) without an explicit upstream change.
- Don't use `typing.Literal` for `Act`.
- Don't use raw float arithmetic in `brain/tlica/`. Use `Fraction`.
- Don't write `brain/tick.py` until the eight-file checkpoint is green.
- Don't push to `femboy2112/lean-scratch` — it is read-only from this package's perspective.
