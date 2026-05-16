---
name: brain-invariants
description: Orchestrate the TLICA invariant catalog and runner for toy-brain. Use when working on brain/ implementation, debugging a red invariant row, looking up a row by ID, verifying Lean citations, auditing the agency->pce import rule, executing the current mission/campaign, or applying SPEC_UPDATES after upstream Lean evolves.
---

# brain-invariants skill

The `brain/` package is a theorem-constrained Python state machine.
`INVARIANT_CATALOG.md` is the canonical runtime assertion catalog. It binds
Lean theorems plus Phase 2 and Phase 3 engineering-hypothesis rows to Python
checks, owning modules, and fixtures.

Current baseline is catalog v0.8:

- 105 REQUIRED
- 29 STRUCTURAL
- 3 NOT-EXERCISED
- 12 DEFERRED
- 4 OBSERVED

`python3 -m tools.catalog counts` is the strict gate for banner, actual, and
expected count agreement. `python3 -m brain.invariants run` must report every
REQUIRED and STRUCTURAL row green; OBSERVED rows are logged but do not gate.

## When To Use

- Implementing a new fixture or module by catalog row.
- Debugging a red row from the invariant runner.
- Checking catalog hygiene, generated ID freshness, citations, and source-kind
  counts.
- Auditing the I-PCE-05 import rule (`agency.py` must not import `pce.py`).
- Auditing catalog-to-registry coverage (I-CAT-01).
- Working on Phase 3.1 Osmotic Chamber, Phase 3.2 Output Ladder, or Phase 3.3
  Minimal Worldlet rows already present in the catalog.
- Executing `CURRENT_MISSION.md` / `CURRENT_CAMPAIGN.md` when the user says
  `go` or an equivalent mission trigger.
- Applying `SPEC_UPDATES.md` when upstream Lean evolves.

Do not use this skill as permission to start Phase 3.4 or later work. Later
phase planning or implementation requires an explicit mission.

## Mission Entry

When the user says `go`, `run current mission`, `execute current mission`, or
`do the current task`, use `.claude/agents/brain-current-mission.md` and read
`CURRENT_MISSION.md` first. If it references `CURRENT_CAMPAIGN.md`, run the
campaign preflight, detect the next eligible step from repo state, obey that
step's allowed file scope, validate as specified, commit and push successful
step results, and stop at explicit review gates or campaign completion.

Treat references in mission and campaign files to Codex as applying to Claude
Code too.

## Campaign Preflight

The "campaign preflight" referenced by `brain-current-mission.md` step 3 is the
checklist below. It is designed to be issued as a single parallel burst (all
items in one tool-call message) so a `go` invocation completes a full
diagnostic sweep before choosing the next step.

Issue in parallel:

1. **Required reads** — every file the mission's required-read section names,
   one `Read` call per file in the same message.
2. **Gate commands** — run all of these in parallel Bash calls:
   ```bash
   python3 -m tools.catalog counts
   python3 -m tools.citations verify
   python3 -m tools.import_audit
   python3 -m brain.invariants run
   git status
   git log --oneline -10
   git log --merges --oneline origin/main | head -10
   ```
3. **Diagnostic agents** — spawn both in the same message:
   - `brain-campaign-state` (returns `READY`, `STOP`, or `USER-JUDGMENT`
     verdict).
   - `brain-catalog-lint` (returns C1/C2/C3/C4 punch list).

After all three burst results return, synthesize:

- If `brain-campaign-state` returns `STOP` or `USER-JUDGMENT`, surface the
  verdict and stop. Do NOT proceed to step selection.
- If any gate command failed, surface the failure and stop unless the failure
  is exactly the situation the next campaign step is supposed to fix.
- If `brain-catalog-lint` returns FAIL on C1 / C2 / C3 / C4, include the
  finding in the report; treat C1 / C2 as blockers (auto-fix candidates
  before the step), and C3 / C4 as user-judgment items.
- Otherwise proceed to step execution using the verdict from
  `brain-campaign-state` plus the campaign macro sequence.

Step execution itself should also batch independent operations: read all
allowed-scope files in parallel, batch independent edits, batch independent
validation commands.

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

- `brain-current-mission`: executes `CURRENT_MISSION.md` when the user says
  `go` or uses an equivalent mission trigger. Orchestrates preflight in
  parallel via the agents below plus the gate commands.
- `brain-explorer`: read-only navigator.
- `brain-row-implementer`: bounded row implementation.
- `brain-runner-debugger`: red-row diagnosis and minimal fix.
- `brain-spec-refresher`: SPEC_UPDATES and upstream Lean drift workflow.
- `brain-catalog-lint`: read-only drift check between
  INVARIANT_CATALOG.md, `tools/catalog.py` banner, `FIXTURE_MODULES` list,
  README / CURRENT_MISSION / CURRENT_CAMPAIGN version strings, and
  `_PHASE3_*_PENDING_ROWS` docstrings. Auto-fix limited to banner and list
  edits, only on explicit user authorization.
- `brain-campaign-state`: read-only diagnostic that emits `READY` / `STOP` /
  `USER-JUDGMENT` for the next eligible step. Used by `brain-current-mission`
  preflight and by the `/repo-state` command.

## Common Mistakes (history-mined)

Six recurring drift patterns observed across the Phase 3.1–3.8b campaigns. The
first four are auto-detected by `brain-catalog-lint`; the last two are
auto-detected by `brain-campaign-state`.

1. **Catalog banner drift.** `tools/catalog.py` `EXPECTED_COUNTS` dict gets
   bumped, but the prose comment block above it still claims the prior
   version/phase. Caught by C1.
2. **FIXTURE_MODULES list drift.** A new fixture is added under
   `brain/**/fixtures/*.py` but the manual `FIXTURE_MODULES` list in
   `brain/invariants.py` is not updated (silent: the new fixture never runs).
   Caught by C2.
3. **Catalog-version triplet drift.** Mission file, campaign file, and README
   describe a starting catalog version that is no longer current. Caught by
   C3. C3 does NOT auto-fix — mission baselines are sometimes lagged on
   purpose to record the state the campaign started from.
4. **Pending-row docstring staleness.** `_PHASE3_*_PENDING_ROWS` blocks are
   copy-pasted with stale step numbers from a prior phase. Caught by C4.
5. **Merged-PR-vs-stale-mission.** A campaign completes and merges to `main`,
   but `CURRENT_MISSION.md` still describes the now-completed campaign as the
   active mission. Caught by `brain-campaign-state` S1.
6. **Amendment vs campaign-doc drift.** A `*_AMENDMENT.md` is added but
   `CURRENT_CAMPAIGN.md` is not updated to require reading it. Watch for
   amendment commits without a same-PR `CURRENT_CAMPAIGN.md` edit; surface
   under `brain-campaign-state` S3 USER-JUDGMENT.

Two further gates owned by existing tools (not duplicated in any new agent):

- **Generated-IDs freshness** is step 0 of `bash tools/check_all.sh`. If
  catalog rows are added without running `python3 -m tools.catalog generate-ids`,
  `brain/_catalog_ids.py` goes stale.
- **I-PCE-05 import audit** is `python3 -m tools.import_audit`. `agency.py`
  must never import `pce.py`.
