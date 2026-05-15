# CURRENT_MISSION.md — Codex `go` Entry Point

## One-line instruction

When the user tells Codex **`go`** in this repository, Codex should read this file and execute the current mission below.

---

## Current mission

Audit the completed Phase 3.1 Osmotic Chamber campaign and write a post-completion audit report:

```text
PHASE3_1_OSMOTIC_CHAMBER_AUDIT.md
```

This is an **audit artifact only**.

Do **not** implement new code.
Do **not** patch the catalog.
Do **not** start Phase 3.2.

---

## Important local command rule

Use `python3 -m ...` for all Python module commands.

Do **not** use `python -m ...` on this machine unless the user explicitly says a `python` alias exists.

If any copied command says `python -m`, convert it to `python3 -m` before running.

---

## Why this mission exists

The Phase 3.1 campaign appears complete. The repo now contains:

```text
catalog v0.6
Phase 3.1 Osmotic Chamber row families
brain/development/ substrate modules
Phase 3.1 fixtures
final gate-sync commit
```

Before moving to any next phase or additional implementation, Codex should audit the completed state.

The audit should answer:

```text
Did Phase 3.1 stay inside scope?
Are v0.6 catalog counts coherent?
Are the I-FRAME / I-DEV / I-SBX rows implemented and registered?
Did the implementation preserve the PerceptEvent + tick() boundary?
Is COGITO_ID protected at developmental and promotion boundaries?
Are OBSERVED rows non-gating?
Did any Phase 3.2+ surfaces accidentally appear?
Are there obvious risks to address before Phase 3.2 planning?
```

---

## Required source files to read first

Read these before writing the audit:

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md
PHASE3_1_OSMOTIC_CHAMBER_CATALOG_PATCH_PLAN.md
traces/RUN_SUMMARY.md
```

Then inspect the implemented Phase 3.1 files:

```text
brain/development/
brain/development/fixtures/
brain/invariants.py
brain/_catalog_ids.py
tools/catalog.py
```

Do not rely on unstated conversation context. The audit must stand on repo-local files and command results.

---

## Required output file

Create:

```text
PHASE3_1_OSMOTIC_CHAMBER_AUDIT.md
```

Allowed file for this mission:

```text
PHASE3_1_OSMOTIC_CHAMBER_AUDIT.md
```

Do not edit implementation files while auditing.

If you discover a defect, document it in the audit. Do not fix it unless the user explicitly asks for a fix mission.

---

## Audit scope

The audit must include these sections or equivalent headings.

### 1. Executive verdict

State whether Phase 3.1 is:

```text
PASS
PASS WITH PATCHES
BLOCKED
```

Define what that means.

### 2. Current counts and gate status

Report current catalog counts.

Expected v0.6 target:

```text
92 REQUIRED
20 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
2 OBSERVED
```

Report whether `python3 -m tools.catalog counts` agrees.

### 3. Full validation status

Run and report:

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

If any command fails, stop after collecting enough output to identify the failure.

Do not run real LLM scenario commands.

### 4. Row-family audit

Audit each row family:

```text
I-FRAME-*
I-DEV-*
I-SBX-*
```

For each family, report:

```text
expected rows
owning modules
fixtures
status split
whether targeted checks pass
any implementation concerns
```

### 5. Scope-creep audit

Check for accidental Phase 3.2+ implementation.

There should be no runtime implementation of:

```text
output ladder
Minimal Worldlet
Proto-BASIC REPL
expression layer
social/language harness
Mode B developmental layer
real LLM training behavior
```

If any related files or code exist, classify whether they are docs-only, stubs, or scope creep.

### 6. Kernel-boundary audit

Verify:

```text
promotion produces PerceptEvent
existing tick() remains the only TLICA runtime state transition path
developmental code does not mutate BrainState / MSI / PtCns / mode state directly
single-event tick semantics are preserved
```

### 7. COGITO_ID audit

Verify:

```text
developmental content cannot produce COGITO_ID
promotion boundary independently rejects COGITO_ID
fixtures exercise this rejection
```

### 8. OBSERVED-row audit

Verify that OBSERVED rows are reported but do not gate success.

In particular, inspect `I-DEV-07`.

### 9. Source-tag / provenance audit

Verify:

```text
FrameSourceKind has exactly the accepted Phase 3.1 active values
source coverage is exact
operator injection / probe echo / endogenous / external / generated are distinguishable
source confusion is prevented at construction
```

### 10. Metric / promotion audit

Review:

```text
salience_v1
stability_v1
prediction_gain_v1
promotion threshold logic
salience-is-not-truth behavior
```

Pay special attention to whether non-predictive patterns can accidentally satisfy promotion.

### 11. Risks and recommended patches

List any needed patches as:

```text
P0 blocker
P1 before Phase 3.2
P2 cleanup
```

Do not implement them.

### 12. Next recommended mission

Recommend the next mission after audit.

Possible outcomes:

```text
If PASS: prepare Phase 3.2 output ladder synthesis/kickoff.
If PASS WITH PATCHES: create a focused patch mission for identified issues.
If BLOCKED: fix blockers before proceeding.
```

---

## Guardrails

Do not modify these files during this audit mission:

```text
brain/
INVARIANT_CATALOG.md
lean_reference/
traces/
scenarios/
tools/catalog.py
CURRENT_CAMPAIGN.md
CURRENT_MISSION.md
.codex/
.agents/
```

The only intended changed file is:

```text
PHASE3_1_OSMOTIC_CHAMBER_AUDIT.md
```

Git operations are required and are not considered edits to guarded files.

---

## Validation and commands

Use `python3`, not `python`.

Run:

```bash
git status --short
git log --oneline -10
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Do not run:

```bash
python3 -m brain.scenario run ...
```

unless the user explicitly asks.

---

## Git persistence requirement

After writing the audit, commit and push it.

Rules:

```text
stage only PHASE3_1_OSMOTIC_CHAMBER_AUDIT.md
commit with a clear message
push to current branch / main as appropriate
report the commit SHA
```

Do not commit accidental changes to guarded files.

If no audit file is created, report why and do not commit.

---

## Final report

When done, report:

```text
Created/updated:
- PHASE3_1_OSMOTIC_CHAMBER_AUDIT.md

Validation:
- command results

Git:
- commit: <sha or none>
- push: success / not run with reason

Verdict:
- PASS / PASS WITH PATCHES / BLOCKED

Next:
- recommended next mission
```

---

## Stop condition

Stop after writing the audit, running validation, committing, pushing, and reporting.

Do not proceed into Phase 3.2 or any patch mission unless the user gives a new explicit instruction.
