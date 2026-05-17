---
name: brain-invariants
description: Orchestrate the toy-brain TLICA invariant catalog, runner, Lean citation checks, import audit, current mission/campaign workflow, and SPEC_UPDATES refresh workflow.
---

# brain-invariants

This Codex-readable skill is derived from
`.claude/skills/brain-invariants/SKILL.md`. Keep the Claude file as source
material when refreshing this skill.

The `brain/` package is a theorem-constrained Python state machine.
`INVARIANT_CATALOG.md` is the canonical runtime assertion catalog. It binds
Lean theorems plus Phase 2 and Phase 3 engineering-hypothesis rows to Python
checks, owning modules, and fixtures.

Current baseline is catalog v0.20:

- 214 REQUIRED
- 83 STRUCTURAL
- 9 NOT-EXERCISED
- 12 DEFERRED
- 16 OBSERVED

`python3 -m tools.catalog counts` is the strict gate for banner, actual, and
expected count agreement. `python3 -m brain.invariants run` must report every
REQUIRED and STRUCTURAL row green; OBSERVED rows are logged but do not gate.

## When To Use

Use this skill when:

- implementing or debugging an invariant row
- looking up a catalog row by ID, module, fixture, or status
- verifying Lean citations
- auditing the `agency.py` to `pce.py` import boundary
- checking catalog to registry coverage
- running the invariant tooling
- executing `CURRENT_MISSION.md` / `CURRENT_CAMPAIGN.md` when the user says
  `go` or an equivalent mission trigger
- applying the `SPEC_UPDATES.md` protocol after upstream Lean changes

Do not use this skill as permission to start Phase 3.4 or later work. Later
phase planning or implementation requires an explicit mission.

## Mission Entry

When the user says `go`, `run current mission`, `execute current mission`, or
`do the current task`, read `CURRENT_MISSION.md` first. If it references
`CURRENT_CAMPAIGN.md`, run the campaign preflight, detect the next eligible
step from repo state, obey that step's allowed file scope, validate as
specified, commit and push successful step results, and stop at explicit review
gates or campaign completion.

## Core Commands

Catalog queries:

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog list
python3 -m tools.catalog list --status REQUIRED
python3 -m tools.catalog list --status DEFERRED
python3 -m tools.catalog list --module <module>
python3 -m tools.catalog list --fixture <fixture>
python3 -m tools.catalog list --id-prefix I-XXX
python3 -m tools.catalog list --source-kind LEAN
python3 -m tools.catalog show I-XXX-NN
python3 -m tools.catalog generate-ids
```

Verification and audits:

```bash
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
python3 -m brain.invariants run --id I-XXX-NN
bash tools/check_all.sh
```

Refresh support:

```bash
tools/refresh_snapshot.sh
python3 -m tools.snapshot_diff /tmp/lean-scratch-latest
python3 -m tools.decl_index lean_reference
python3 -m tools.decl_index /tmp/lean-scratch-latest
```

Do not run real traced scenarios or real LLM-backed scenario commands unless
the user explicitly asks.

## Hard Rules

- Use `python3 -m ...` for Python module commands. Convert copied
  `python -m ...` examples to `python3 -m ...` on this machine.
- Use `fractions.Fraction` in `brain/tlica/`, `brain/fixtures/`, and
  `brain/invariants.py`.
- `math.inf` is only for Lean top in `dInfShared` empty-shared-domain cases.
- `rho(value)` normalizes I/O boundary values and raises outside `[0, 1]`;
  it never clamps silently.
- `Act` is `enum.Enum`, not `typing.Literal`.
- `ModeOp` and `Act` are disjoint namespaces.
- `agency.py` must never import `pce.py`.
- Foundation PCE is action-constant.
- Action selection uses `feasibleProjectedPCE`.
- `COGITO_ID` is reserved and never user-created.
- `tick()` is single-event in v1 semantics.
- Trace is observation-only and SafeTracer-wrapped.
- Catalog/registry coverage is enforced by I-CAT-01.
- Do not change catalog status or version to make code pass unless the user
  explicitly requested a spec update.
- Do not implement deferred phase surfaces from this skill.

## Phase 3 Boundaries

- Phase 3.1 Osmotic Chamber records deterministic developmental substrate
  behavior without bypassing promotion gates.
- Phase 3.2 Output Ladder remains below language, reflective agency, Mode B,
  worldlet semantics, and runtime mutation.
- Phase 3.3 Minimal Worldlet is a deterministic local harness only. It can
  record bounded consequence evidence and not-I pushback in local history, but
  it does not claim external reality, language, reflective agency, Mode B, real
  host execution, or `PerceptEvent` / `tick()` promotion.
- Phase 3.4 Proto-BASIC REPL and later surfaces are not authorized unless a new
  mission explicitly says so.

## Row Implementation Workflow

1. Read the row with `python3 -m tools.catalog show I-XXX-NN`.
2. Read nearby rows when needed with
   `python3 -m tools.catalog list --id-prefix I-XXX`.
3. Read the cited Lean source under `lean_reference/`.
4. Read the owning module and fixture.
5. Implement the smallest behavior that satisfies the row.
6. Run the targeted invariant check.
7. Run `bash tools/check_all.sh` when practical.
8. Summarize rows changed, commands run, and remaining risks.

## Red Row Debug Workflow

1. Reproduce the row failure.
2. Read the catalog row, cited Lean declaration, fixture, and owning module.
3. Classify the failure as constructor strictness, fixture invalidity, domain
   mismatch, `Fraction`/float leakage, catalog drift, or import/dependency
   violation.
4. Fix with minimum blast radius.
5. Re-run targeted and full checks.

If the problem is catalog drift, do not silently change code. Surface the drift
and apply `SPEC_UPDATES.md` only when the user asks for a spec refresh.

## SPEC_UPDATES Refresh Protocol

When upstream Lean evolves:

1. Run `tools/refresh_snapshot.sh`.
2. Classify declaration drift.
3. Treat upstream Lean as newer than local `lean_reference/`.
4. Treat local `lean_reference/` as newer than the catalog.
5. Treat the catalog as newer than Python implementation code.
6. Update catalog rows only when justified.
7. Refresh `lean_reference/` only after catalog review.
8. Run `python3 -m tools.catalog counts`.
9. Run `python3 -m tools.citations verify`.
10. Run `bash tools/check_all.sh`.

Never push to the upstream Lean repository.

## Common Failure Modes

- Stale row count expectations from older catalog baselines.
- Raw float arithmetic leaking into TLICA modules or fixtures.
- `Act` modeled as `typing.Literal` instead of `enum.Enum`.
- Mode operations treated as actions.
- `agency.py` importing foundation PCE.
- Fixture inputs weakened to bypass constructor checks.
- Catalog edited to match Python behavior instead of treating the catalog as
  canonical.
- Trace backends changing semantic `(BrainState, TickRecord)` output.
- Output or worldlet surfaces accidentally claiming language, agency,
  external reality, Mode B, or runtime mutation.
- Real scenario commands run during prompt/config work.

## Paired Agent Roles

- `brain_current_mission`: executes `CURRENT_MISSION.md` when the user says
  `go` or uses an equivalent mission trigger.
- `brain_explorer`: read-only navigator.
- `brain_row_implementer`: bounded row implementation.
- `brain_runner_debugger`: red-row diagnosis and minimal fix.
- `brain_spec_refresher`: SPEC_UPDATES and upstream Lean drift workflow.
