# CURRENT_MISSION.md — Codex `go` Entry Point

## One-line instruction

When the user tells Codex **`go`** in this repository, Codex should read this file and execute the current mission below, unless the user gives a more specific instruction.

---

## Current mission

Patch the Phase 3 bridge document:

```text
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
```

This is a **planning-artifact patch only**.

Do **not** implement Phase 3 code.

---

## Why this mission exists

`PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md` already captures the main v0.5 → Phase 3 bridge correctly, but review found that it is missing two explicit sections required by this mission protocol:

```text
11. Explicit Non-Goals
12. Next Artifact
```

Your job is to patch only that document so those sections are present and the document ends with the required next-artifact framing.

---

## Required source files to read first

Read these before editing:

```text
CURRENT_MISSION.md
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
README.md
INVARIANT_CATALOG.md
traces/RUN_SUMMARY.md
```

Do not rely on unstated conversation context. The patch must stand on repo-local files.

---

## Required patch

Edit only:

```text
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
```

Add explicit sections near the end of the synthesis, after the ClaudeCLIClient / Phase 3.1 kickoff implications material and before the final closing if needed.

### Add section 11

Use this section title:

```text
## 11. Explicit Non-Goals
```

Include these non-goals:

```text
prompt-tuning solely to force the four-tick scenario to pass
seeded-MSI scenario hacks as the immediate next move
Phase 3 runtime implementation from this synthesis
direct developmental mutation of TLICA state
bypassing PerceptEvent and tick()
implementation of the Osmotic Chamber before a kickoff + corrigenda pass
implementation of the output ladder, worldlet, Proto-BASIC REPL, expression layer, or language harness from this synthesis
```

Also state that the developmental layer must feed the existing kernel through the promotion gate rather than replacing or mutating it directly.

### Add section 12

Use this section title:

```text
## 12. Next Artifact
```

Include this exact next artifact:

```text
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
```

Include this exact sentence:

```text
No Phase 3 code before kickoff + corrigenda.
```

Also say the kickoff must lock:

```text
PhenomenalFrame
FrameSource
SubstrateDrives
SubstrateHistory
ProtoPattern
ProtoContent
salience_v1
stability_v1
prediction_gain_v1
SIMILARITY
FOCUS_CONTACT
ProbeUse
ProbePolicyState
promotion gate to PerceptEvent
source-tag audit
first deterministic chamber fixtures
Phase 3.1 row statuses
trace reserved-key protection decision
```

---

## Guardrails

Do not modify these files during this mission:

```text
brain/
INVARIANT_CATALOG.md
lean_reference/
traces/
scenarios/
```

Allowed file for this mission:

```text
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
```

Do not edit README unless explicitly necessary. It should not be necessary for this mission.

---

## Validation

After patching the synthesis:

Run lightweight checks only:

```bash
git diff --name-only
python -m tools.catalog counts
```

Do not run:

```bash
bash tools/check_all.sh
python -m brain.scenario run ...
```

unless the user explicitly asks.

---

## Git persistence requirement

After validation passes, Codex must commit and push its result.

Rules:

```text
stage only PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
commit with a clear message
push to the current branch / main as appropriate
report the commit SHA
```

Do not commit accidental changes to guarded files.

If there are no changes, Codex should report that no commit was made and explain why.

---

## Final report

When done, report:

```text
Updated:
- PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md

Validation:
- git diff --name-only: ...
- python -m tools.catalog counts: pass / not run with reason

Git:
- commit: <sha or none>
- push: success / not run with reason

Next:
- review patched synthesis
- then draft PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
```

---

## Stop condition

Stop after patching `PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md`, validating, committing, pushing, and reporting the result.

Do not proceed into Phase 3.1 kickoff or code unless the user gives a new explicit instruction.
