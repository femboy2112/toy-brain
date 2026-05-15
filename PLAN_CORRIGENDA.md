# PLAN_CORRIGENDA.md — `brain/` v0 Implementation Plan

Read alongside the implementation plan. This file lists three correctness fixes, three decisions to pin, and four minor notes — ordered by severity. Apply C1–C3 to the plan text before any module is written; pin D4–D6 in the kickoff briefing for the row-implementer subagent; treat M7–M10 as optional.

## Corrections (must apply before coding)

### C1. `__post_init__` policy must be consistent across all dataclasses

**Issue.** The plan describes two different policies. For `ScalarProfile`, `__post_init__` re-asserts that values are in `[0, 1]` and (implicitly) raises. For `MSI`, `__post_init__` re-asserts the axioms "but does not raise on its own — the builder is the official entry point that raises." Inconsistent. If `MSI.__post_init__` doesn't raise, any code that bypasses `make_msi` can construct an invalid MSI, which defeats I-RT-06.

**Fix.** Every dataclass `__post_init__` raises `ValueError` on invariant violation. Builders in `brain/tlica/builders.py` exist to:
- accept friendlier input shapes (e.g., normalize floats via `Fraction(str(v))`);
- combine multiple field-level checks into one atomic operation;
- emit error messages that name the Lean axiom, e.g. `"I-MSI-02 violated: cogito not in contents (Axiom 3.3.1)"`.

The dataclass itself is also a hard gate. There is no "builder-is-the-only-gate" path.

### C2. `tools/` must not be a runtime dependency of `brain/`

**Issue.** The plan has `brain/invariants.py` calling `tools.import_audit.audit()` to enforce I-PCE-05. That makes `tools/` a runtime dependency of `brain/`, not just a developer-helper directory. The catalog's dependency graph (`builders → validation`; `invariants → fixtures + validation`; `tick → builders + invariants`) does not include `tools/`.

**Fix.** Put the AST-based audit logic in `brain/_import_audit.py` (private module, leading underscore). `tools/import_audit.py` becomes a thin CLI wrapper:

```python
# brain/_import_audit.py
import ast
import importlib.util
from pathlib import Path

FORBIDDEN_PAIR = ("brain.tlica.agency", "brain.tlica.pce")

def audit_agency_no_pce_import() -> tuple[bool, str]:
    """Return (passed, message). I-PCE-05."""
    src_path = Path(__file__).parent / "tlica" / "agency.py"
    tree = ast.parse(src_path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "pce" in node.module:
            return False, f"I-PCE-05 violated: agency.py imports {node.module}"
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "pce" in alias.name:
                    return False, f"I-PCE-05 violated: agency.py imports {alias.name}"
    return True, "I-PCE-05: agency.py clean of pce imports."
```

```python
# tools/import_audit.py
from brain._import_audit import audit_agency_no_pce_import

def main() -> int:
    ok, msg = audit_agency_no_pce_import()
    print(msg)
    return 0 if ok else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
```

`brain/invariants.py` imports from `brain._import_audit`, not from `tools/`. `brain/` stays self-contained.

### C3. `msi_of` stub must build a fresh MSI tied to whatever profile it receives

**Issue.** Plan says "Stub `msi_of` returns the same MSI for every projected profile (domain matches by construction since `project(a, P) = P`)." This holds only when every queried `P` is the same object. In `projected_pce.py` and `trajectory_step.py`, fixtures pass multiple distinct profiles. The stub then violates I-APRJ-01: `FutureMSIModel.domain_match : ∀ P, (msiOf P).profile.domain = P.domain`. The Lean is `∀ P` — the stub must work for any input profile, not just one fixed P.

**Fix.** Build a fresh MSI per call, tied to the supplied profile:

```python
# brain/stubs/future_msi_stub.py (or inside the fixture that uses it)
from fractions import Fraction
from brain.tlica.builders import make_msi
from brain.tlica.profile import COGITO_ID, ScalarProfile
from brain.tlica.msi import MSI

def msi_of(P: ScalarProfile) -> MSI:
    threshold = Fraction(1, 2)
    contents = frozenset(
        {COGITO_ID} | {x for x in P.domain if x != COGITO_ID and P.values[x] >= threshold}
    )
    return make_msi(profile=P, contents=contents, threshold=threshold)
```

Domain match is now guaranteed because the MSI's `profile` *is* the input `P`.

## Decisions to pin (clarify in the kickoff briefing)

### D4. `AffectKernelWitness.__post_init__` does a local check, not a global one

The catalog wording for I-AFF-05 ("Constructor raises when every feasible action pair has equal branch profiles AND equal projected PCE") sounds global, but the cleanest Python implementation is local — matching the Lean structure exactly. In Lean, `AffectKernelWitness` requires a witness of `structural_perturbation` as a field; the no-affect-kernel theorem says that field can't be supplied in a collapsed world for *any* pair. In Python:

```python
@dataclass(frozen=True, slots=True)
class AffectKernelWitness:
    ctx: AgencyContext
    P: ScalarProfile
    baseline: Act
    action: Act

    def __post_init__(self) -> None:
        if self.baseline not in self.ctx.feasible(self.P):
            raise ValueError("baseline not feasible")
        if self.action not in self.ctx.feasible(self.P):
            raise ValueError("action not feasible")
        branches_differ = (
            branch_profile(self.ctx, self.P, self.baseline)
            != branch_profile(self.ctx, self.P, self.action)
        )
        pce_differs = (
            self.ctx.feasible_projected_pce(self.P, self.baseline)
            != self.ctx.feasible_projected_pce(self.P, self.action)
        )
        if not (branches_differ or pce_differs):
            raise ValueError(
                "I-AFF-05 violated: structural_perturbation empty "
                "(branch profiles and projected PCE both collapse for this pair)."
            )
```

`affect_kernel_collapse.py` then builds a globally-collapsed world; *any* chosen pair fails the local check. Same outcome as a global check, simpler code, matches Lean semantics.

### D5. Include `brain/tlica/modes.py` and `brain/tlica/iboundary.py` in the 8-file checkpoint commit

The plan offers two options for handling I-MOD-04 and I-IBND-02 — inline functions inside `cogito_invariants.py`, or thin module files. Pick the module files. They are tiny (~30 lines each):

- `brain/tlica/modes.py`: imports `ConsistencyEval`, defines `ModeOp(str, Enum)` with the four members, and `from_eval(e: ConsistencyEval) -> ModeOp` via a lookup dict `{DAMAGE: MODE_A, PRESERVE: MODE_C, NEUTRAL: NEUTRAL}`. Never returns `MODE_B`.
- `brain/tlica/iboundary.py`: `def boundary(msi, ptcns) -> frozenset[ContentID]: return ptcns.positive_contents | ptcns.negative_contents`.

The "8-file checkpoint" effectively becomes a 10-file checkpoint, but the import graph is correct from day one and the expansion phase only adds *fixtures*, not new modules. The README's stated build order is unaffected — these two files slot in between steps 3 (`ptcns.py`) and 4 (`builders.py`).

### D6. `assert_subset_rank_le` takes explicit pairs; no internal sampling

The plan calls `assert_subset_rank_le` a "sampling helper." Internal randomness would make `python -m brain.invariants run` non-deterministic, breaking the green/red gate. Fix the signature so all randomness lives in the fixture, not the helper:

```python
# brain/validation.py
from collections.abc import Callable
from fractions import Fraction
from typing import TypeVar

T = TypeVar("T")

def assert_subset_rank_le(
    rank_fn: Callable[[frozenset[T]], Fraction],
    pairs: list[tuple[frozenset[T], frozenset[T]]],
) -> None:
    """For each (S, T) with S ⊆ T, assert rank_fn(S) <= rank_fn(T).
    Pairs come from the fixture, not from internal sampling — the runner
    must be deterministic."""
    for S, super_T in pairs:
        if not S <= super_T:
            raise ValueError(f"pair invalid: {S} not subset of {super_T}")
        if not rank_fn(S) <= rank_fn(super_T):
            raise AssertionError(
                f"monotonicity failed: rank({S})={rank_fn(S)} > rank({super_T})={rank_fn(super_T)}"
            )
```

Each fixture passes a hand-built list of `(subset, superset)` pairs that exercise the row's intent.

## Minor notes (optional polish)

### M7. `Fraction(str(value))` for float input — confirmed

The plan correctly normalizes float input via `Fraction(str(value))` rather than `Fraction(value)`, avoiding binary-drift surprises (`Fraction(0.1)` returns the binary representation `Fraction(3602879701896397, 36028797018963968)`, not `1/10`). No change needed; just confirming this should remain the convention in `brain/tlica/builders.py::rho`.

### M8. Add a type-checking gate to `tools/check_all.sh`

The plan's `tools/check_all.sh` runs four checks (catalog counts, citations, import audit, invariant runner). Consider adding `mypy --strict brain/ tools/` (or `pyright`) as a fifth check. With Protocols and `Fraction` everywhere, type checking catches a class of bugs the runner won't (mis-typed `Fraction | float` returns, Protocol method-signature drift, dataclass field reassignment). Not v0-critical, but cheap.

### M9. Drop `tests/` discovery from `pyproject.toml` (or commit to using it)

The plan adds `[tool.pytest.ini_options]` configured to discover under `tests/`, but the fixtures *are* the test harness — the invariant runner orchestrates them. Two options, pick one:

- **Drop `tests/` discovery.** Fixtures suffice; the runner is the harness.
- **Commit to `tests/`** as the home for unit tests on `tools/` and `brain/validation.py` (the helper code that the invariant runner depends on but doesn't itself assert).

Recommendation: drop until there's concrete need. Shipping a half-empty `tests/` directory invites confusion about which is canonical.

### M10. Document that `@register` order doesn't matter

The runner sorts output by row ID. The order in which fixture modules import is irrelevant to logic. Add a one-line docstring in `brain/invariants.py` saying so explicitly, to prevent a future contributor from accidentally introducing load-order coupling.

## Apply order

1. Apply **C1–C3** to the plan text before any module is written.
2. Pin **D4–D6** in the kickoff briefing for the `brain-row-implementer` subagent.
3. Treat **M7–M10** as optional; handle in Phase G or skip.

## What this corrigenda does *not* change

- The build order (8-file gate then expansion, tick + io_types last) is correct.
- The numeric core (`Fraction` everywhere; `math.inf` only for empty-shared `dInfShared`) is correct.
- The `Act` enum shape is correct.
- The cogito-gated `PreservationRanking.rank` stub is correct.
- The `ProjectMap` Protocol with explicit `natural_dynamics` is correct.
- The `tools/` and `.claude/` skill/subagent layout is correct.
- The `SPEC_UPDATES.md` refresh protocol is correct.
- The success criterion (`python -m brain.invariants run` reports 80 REQUIRED rows green) is correct.

If anything in this corrigenda contradicts `INVARIANT_CATALOG.md` v0.2, the catalog wins.
