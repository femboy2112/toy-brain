# Phase 2 v1.2 Corrigenda — Baseline Hardening Completion

## Purpose

This corrigenda completes the Phase 2 v1.2 baseline-hardening pass.

The v0.5 catalog already introduced the intended hardening surface:

- `I-RT-11` — single-event tick semantics
- `I-RT-12` — duplicate `content_id` rejection
- `I-TRACE-02` — trace fail-open behavior
- `I-CAT-01` — catalog ↔ registry coverage audit

The implementation mostly landed those changes. This corrigenda closes the remaining gaps before the branch is treated as Phase 3-ready.

**No catalog version bump is required.** These are tightening / completion patches against existing v0.5 commitments, not new rows.

## Current target

Catalog target:

```
v0.5
84 REQUIRED
15 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
1 OBSERVED
14 fixtures
```

The branch already includes:

- `brain/_catalog_ids.py`
- `SafeTracer`
- I-CAT-01 runner coverage audit
- single-event tick guard
- duplicate-content tick guard
- ambiguous LLM parse rejection
- `FutureMSIModel` runtime domain guard
- strict `tools.catalog` counts gate

Remaining required fixes:

- **C1.** Harden I-PCE-05 import audit.
- **C2.** Make `SafeTracer` unavoidable at the tick boundary.
- **C3.** Finish README v0.5 synchronization.
- **C4.** Resolve missing `BASELINE_HARDENING_KICKOFF.md` reference.

P1 polish items are deferred (see end of document).

## C1 — Harden I-PCE-05 import audit

### Problem

The existing import audit catches:

```python
import brain.tlica.pce
from brain.tlica.pce import PCE
```

but misses:

```python
from brain.tlica import pce
```

This AST form parses as:

```python
ast.ImportFrom(
    module="brain.tlica",
    names=[ast.alias(name="pce")]
)
```

The audit checks `node.module`, sees `"brain.tlica"`, and fails to inspect `node.names`. This is a real correctness gap in the I-PCE-05 gate that has existed since v0.

### Required patch

**File:** `brain/_import_audit.py`

Refactor the AST-walking logic into a private pure helper, then have the public function call it on the canonical agency.py path. This keeps the public API stable while making the testable unit pure.

```python
import ast
from pathlib import Path

_AGENCY_PATH = Path(__file__).parent / "tlica" / "agency.py"


def _audit_pce_imports(tree: ast.Module, filename: str) -> tuple[bool, str]:
    """Pure AST audit. Tests can call this on a parsed temp file."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = {alias.name for alias in node.names}

            if module == "brain.tlica" and "pce" in names:
                return False, (
                    f"I-PCE-05 violated: {filename} imports pce from brain.tlica. "
                    "Action selection must route through feasibleProjectedPCE, "
                    "not the foundation-default PCE."
                )

            if (
                module == "brain.tlica.pce"
                or module.endswith(".pce")
                or module == "pce"
            ):
                return False, (
                    f"I-PCE-05 violated: {filename} imports {module!r}. "
                    "Action selection must route through feasibleProjectedPCE, "
                    "not the foundation-default PCE."
                )

        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if (
                    name == "brain.tlica.pce"
                    or name.endswith(".pce")
                    or name == "pce"
                ):
                    return False, (
                        f"I-PCE-05 violated: {filename} imports {name!r}. "
                        "Action selection must route through feasibleProjectedPCE, "
                        "not the foundation-default PCE."
                    )

    return True, f"I-PCE-05: {filename} is clean of pce imports."


def audit_agency_no_pce_import() -> tuple[bool, str]:
    """Public entry: audit the canonical agency.py file."""
    if not _AGENCY_PATH.exists():
        return True, (
            f"I-PCE-05: {_AGENCY_PATH.name} does not exist yet (audit skipped)."
        )
    tree = ast.parse(_AGENCY_PATH.read_text(encoding="utf-8"))
    return _audit_pce_imports(tree, _AGENCY_PATH.name)
```

### Required test

Add a negative-case test that would have failed before this patch.

**Location:** `brain/invariants.py`, inside the registered structural check for I-PCE-05:

```python
@register("I-PCE-05", status="STRUCTURAL")
def check_I_PCE_05() -> None:
    # Positive case: real agency.py is clean.
    ok, msg = audit_agency_no_pce_import()
    if not ok:
        raise AssertionError(f"I-PCE-05 violated: {msg}")

    # Negative case: the previously-slipping import form is now caught.
    import ast
    from brain._import_audit import _audit_pce_imports

    bad_tree = ast.parse(
        "from brain.tlica import pce\n"
        "def f():\n"
        "    return pce\n"
    )
    ok, msg = _audit_pce_imports(bad_tree, "agency.py")
    assert not ok, (
        "I-PCE-05 audit failed to reject `from brain.tlica import pce`"
    )
    assert "I-PCE-05" in msg
```

### Acceptance criterion

```
python -m brain.invariants run --id I-PCE-05
```

must pass. Reverting the audit patch must cause the negative test to fail.

## C2 — Make `SafeTracer` unavoidable at the tick boundary

### Problem

`SafeTracer` exists and `make_tracer_from_env()` wraps by default, but callers can still bypass it by constructing a raw tracer and passing it directly into `tick()`.

Current CLI path:

```python
if args.trace:
    tracer = FileTracer(Path(args.trace))
```

This means explicit `--trace` can still pass a raw `FileTracer` into the runtime. The observation-only guarantee should be enforced at the kernel boundary, not delegated to each caller.

### Required patch

**File:** `brain/tick.py`

Import `SafeTracer`:

```python
from brain.trace import CognitionTracer, NullTracer, SafeTracer
```

At the start of `tick()`, replace:

```python
tracer = tracer if tracer is not None else NullTracer()
```

with:

```python
if tracer is None:
    tracer = SafeTracer(NullTracer())
elif not isinstance(tracer, SafeTracer):
    tracer = SafeTracer(tracer)
```

This makes trace fail-open behavior unavoidable for all callers. The `isinstance` check prevents double-wrapping when the tracer already arrives wrapped (e.g., from `make_tracer_from_env()`).

### Important note

Fixtures that hold a `MemoryTracer` reference still work correctly:

```python
mem_tracer = MemoryTracer()
result = run_scenario(spec, client, tracer=mem_tracer)
assert mem_tracer.events
```

The caller's `mem_tracer` object is preserved. `tick()` wraps it internally in a `SafeTracer`, but `SafeTracer.record()` forwards to the inner tracer's `record()`. The fixture's outer reference (`mem_tracer`) still points to the original `MemoryTracer`, which still accumulates events. No fixture changes are required.

### Required test

Existing I-TRACE-02 already tests that `SafeTracer(_TracerThatAlwaysRaises())` produces the same `BrainState` / `mode_trace` as `NullTracer`.

Add one direct tick-boundary case for the unwrapped path:

```python
# Confirms that an unwrapped raising tracer passed to tick()
# is wrapped at the boundary and does not propagate failures.
state = _initial_state()
events = [_dummy_event("foo")]
client = _mock_client(["PRESERVE"])
raising = _TracerThatAlwaysRaises()  # unwrapped — bypasses make_tracer_from_env

# Must not raise.
new_state, record = tick(state, events, client, tracer=raising)
assert record is not None  # tick completed normally
```

### Acceptance criterion

```
python -m brain.invariants run --id I-TRACE
```

must pass.

## C3 — Finish README v0.5 synchronization

### Problem

The README header and catalog-history section are mostly v0.5-aware, but old v0.2 language remains later in the file:

- `reports every REQUIRED row green (80 of them, distributed across 11 fixtures)`
- `Don't review the plan. Implement v0.2 exactly.`
- Historical build-order instructions still read as if the repo is unimplemented and `tick.py` should not exist yet.

### Required patch

**File:** `README.md`

#### Replace the success criterion

Old:

```
reports every REQUIRED row green (80 of them, distributed across 11 fixtures).
```

New:

```
reports every REQUIRED row green, every STRUCTURAL row green, all auxiliary gates
pass, and OBSERVED rows are reported without gating.

For catalog v0.5, the expected count is:
84 REQUIRED · 15 STRUCTURAL · 3 NOT-EXERCISED · 12 DEFERRED · 1 OBSERVED.
```

#### Replace the stale v0.2 instruction

Old:

```
Don't review the plan. Implement v0.2 exactly.
```

New:

```
Do not implement from stale draft counts or earlier catalog versions.
Use the current INVARIANT_CATALOG.md exactly.
```

#### Remove old build-order instructions from README

The README is the canonical entry point. Historical implementation instructions should not live in its body, even if labeled "historical," because future readers will reasonably assume the README describes the current state of the repo.

**Preferred fix:** move the historical content out of README entirely. Two options:

- **Option 3a:** Delete the section and rely on git history.
- **Option 3b:** Move it into a new `ARCHIVE.md` under a header like `## Historical v0 build order`.

Either is acceptable. Recommend Option 3b — keeps the content available without polluting the canonical entry point.

### Acceptance criterion

`README.md` must contain no authoritative references to:

- `v0.2 exactly`
- `80 REQUIRED`
- `11 fixtures`
- `do not write tick.py`

unless they are in `ARCHIVE.md` or a clearly non-authoritative historical section outside the main README.

## C4 — Resolve missing `BASELINE_HARDENING_KICKOFF.md` reference

### Problem

`README.md` references `BASELINE_HARDENING_KICKOFF.md`, but the file is not committed to the repo. This creates a broken documentation pointer.

### Required decision

Choose one:

- **Option A.** Commit the kickoff doc.
- **Option B.** Remove the README reference.

### Recommendation

Choose **Option A**. The kickoff doc has historical value and explains why v0.5 exists. It already exists as a planning artifact — commit it as-is.

Recommended contents (already present in the planning artifact):

- Purpose: Phase 2 v1.2 baseline hardening before Phase 3.
- P1 `SafeTracer` / I-TRACE-02.
- P2 single-event tick guard / I-RT-11.
- P3 duplicate `content_id` guard / I-RT-12.
- P4 ambiguous parse rejection / I-LLM-01 hardening.
- P5 `FutureMSIModel` runtime guard / I-APRJ-01 hardening.
- P6 strict catalog count gate.
- P7 generated catalog IDs / I-CAT-01.
- Validation: `bash tools/check_all.sh`.

### Acceptance criterion

No broken README references.

## Deferred P1 polish

These are reasonable but not merge blockers for Phase 2 v1.2.

### P1-A — Extra stale-registration audit

Current I-CAT-01 checks missing REQUIRED/STRUCTURAL registrations. A later pass may also check stale extra registrations: rows in the registry that no longer exist in `brain/_catalog_ids.py`. Useful before Phase 3 row churn, but not required for this corrigenda.

### P1-B — I-CAT-01 reporting UX

Currently coverage failure hard-fails before the normal row table prints. A later pass may convert that into a structured `RunReport` failure so I-CAT-01 appears as a red row in the standard output rather than as a `RuntimeError` before any row is reported. UX choice, not a correctness issue.

### P1-C — Trace reserved-key protection

Current tracer payload logic allows payload keys to overwrite reserved fields (`type`, `timestamp_ns`, `tick_id`). A later pass should either namespace payloads under a `payload` sub-key or reject reserved keys. Not required now, but **should be done before Phase 3.1 trace-heavy work** — Phase 3.1 will generate many source-tagged developmental events and this risk grows with volume.

### P1-D — Executable bit for scripts

If desired: `chmod +x tools/check_all.sh`. README already uses `bash tools/check_all.sh` so this is not a blocker.

## Validation plan

After C1–C4:

```
python -m tools.catalog generate-ids
bash tools/check_all.sh
```

Expected:

```
0/5 generated catalog IDs freshness: pass
1/5 catalog counts strict: pass
2/5 citation verification: pass
3/5 import audit: pass
4/5 invariant runner: pass
```

Then run targeted checks:

```
python -m brain.invariants run --id I-PCE-05
python -m brain.invariants run --id I-TRACE
python -m brain.invariants run --id I-RT-11
python -m brain.invariants run --id I-RT-12
python -m brain.invariants run --id I-CAT-01
```

All must pass.

## Merge readiness

The branch is merge-ready only after:

1. C1 import audit patch lands (with the helper refactor + negative test).
2. C2 `SafeTracer` tick-boundary wrapper lands.
3. C3 README stale text is removed or moved to `ARCHIVE.md`.
4. C4 missing kickoff reference is resolved (recommended: commit the doc).
5. Branch is rebased or merged with `origin/main`.
6. `bash tools/check_all.sh` passes all five stages.

## Phase 3 readiness

Do **not** begin Phase 3.1 until this corrigenda is complete.

After this branch lands:

1. Run real behavioral CLI with trace.
2. Inspect LLM classifications and trace output.
3. Update `PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.1.md` to v0.2 incorporating the corrected baseline state, the worldlet-before-REPL phase-order recommendation, the refined REQUIRED / STRUCTURAL / OBSERVED status mix, and whatever the traced CLI reveals.
4. Write `PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md` with the same plan/corrigenda discipline as v0 and v1.
5. Run a corrigenda pass on Phase 3.1 before any code lands.

The catalog remains at v0.5 throughout this corrigenda.
