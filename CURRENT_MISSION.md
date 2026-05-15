# CURRENT_MISSION.md — Codex `go` Entry Point

## One-line instruction

When the user tells Codex **`go`** in this repository, Codex should read this file and execute the current mission below, unless the user gives a more specific instruction.

---

## Current mission

Review the Phase 3.1 kickoff and draft its corrigenda document:

```text
PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md
```

This is a **planning/corrigenda artifact only**.

Do **not** implement Phase 3 code.

---

## Why this mission exists

`PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md` is now drafted and pushed. It is good enough to enter a corrigenda pass, but review identified several issues to tighten before any Phase 3.1 implementation begins.

The corrigenda should turn the kickoff into an implementation-ready plan while preserving the project discipline:

```text
plan → corrigenda → code
```

This mission drafts the corrigenda only. It does not authorize runtime implementation.

---

## Required source files to read first

Read these before writing the corrigenda:

```text
CURRENT_MISSION.md
README.md
INVARIANT_CATALOG.md
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
traces/RUN_SUMMARY.md
BASELINE_HARDENING_KICKOFF.md
PHASE2_v1_2_CORRIGENDA.md
```

Do not rely on unstated conversation context. The corrigenda must stand on repo-local files.

---

## Required output file

Create:

```text
PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md
```

Do not edit any other file unless absolutely necessary and explicitly justified.

---

## Required review stance

Treat `PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md` as a strong draft, not as final.

The corrigenda should preserve what is sound:

```text
PRESERVE should be earned, not labeled.
Phase 3.1 is planning-only until kickoff + corrigenda are accepted.
Osmotic Chamber only; no output ladder/worldlet/REPL/expression/social-language implementation.
SubstrateHistory is in scope from day one.
Existing tick() and PerceptEvent remain the only path into TLICA runtime state.
```

The corrigenda should tighten what is underspecified or risky.

---

## Required issues to address

The corrigenda must address at least these issues.

### C1 — FrameSourceKind granularity

The kickoff currently proposes:

```text
EXTERNAL
INTERNAL
PROBE
GENERATED
```

This is probably too coarse.

Corrigenda should recommend a Phase 3.1-appropriate source enum that distinguishes at least:

```text
ENDOGENOUS
OPERATOR_INJECTION
PROBE_ECHO
EXTERNAL
GENERATED
```

It should explicitly defer later-only source kinds like:

```text
WORLDLET_RESPONSE
OUTPUT_ECHO
REPL_FEEDBACK
TEACHER_SIGNAL
```

unless the corrigenda has a strong reason to include them as reserved-but-unused values.

Explain why source granularity matters:

```text
operator-injected content must not be confused with endogenous patterning
probe echo must not be confused with external contact
source confusion would undermine salience/stability/prediction histories
```

### C2 — Avoid `ContentID = str` shadowing

The kickoff sketch currently aliases:

```python
ContentID = str
```

This risks confusion with `brain.tlica.profile.ContentID`.

Corrigenda should recommend one of:

```text
DevContentID = str
```

or:

```text
use existing ContentID only at the promotion boundary
```

The preferred rule:

```text
developmental proto-content IDs are developmental IDs until promotion;
existing TLICA ContentID is used only when producing a PerceptEvent.
```

### C3 — Revisit `prediction_gain_v1`

The kickoff formula uses:

```python
prediction_gain_v1 = clamp_unit(raw_gain - baseline + Fraction(1, 2))
```

This may artificially lift weak/non-predictive patterns to about `1/2`, which is also the proposed promotion threshold.

Corrigenda should recommend a stricter formula, such as:

```python
prediction_gain_v1 = clamp_unit(raw_gain - baseline)
```

or another normalized positive-delta formula that keeps non-predictive patterns low.

Explain why:

```text
promotion should not become easy just because the metric is offset upward
PRESERVE should be earned by real recurrence/stability/predictive structure
```

### C4 — Clarify status of focus behavior row

The kickoff proposes `focus_stabilizes_or_dissolves.py`, but the suggested row `I-DEV-04` is OBSERVED.

Corrigenda should decide:

```text
If the fixture is deterministic and has a crisp pass/fail behavior, make it REQUIRED.
If it is qualitative or trend-like, keep it OBSERVED and rename/scope it accordingly.
```

The recommended path:

```text
make the first focus fixture deterministic and REQUIRED for the narrow claim that FOCUS_CONTACT updates ProbeUse history and does not promote by itself;
leave broader stabilize/dissolve dynamics as OBSERVED.
```

### C5 — Trace reserved-key protection

The kickoff recommends trace reserved-key protection as a pre-Phase-3.1 micro-hardening patch.

Corrigenda should convert that recommendation into a specific decision:

```text
trace reserved-key protection should be the next mission before Phase 3.1 implementation
```

or

```text
trace reserved-key protection should be the first Phase 3.1 catalog row
```

Preferred recommendation:

```text
next mission before Phase 3.1 implementation
```

Rationale:

```text
it is a trace-envelope boundary issue, not a developmental feature
it should be fixed before developmental trace volume increases
```

### C6 — Data model validation details

Corrigenda should sharpen constructor validation expectations for:

```text
Fraction normalized fields in [0, 1]
non-empty printable IDs
source-map exact coverage
non-empty provenance for promotion
COGITO_ID rejection at developmental ID and promotion boundary
```

### C7 — Catalog versioning and row family plan

Corrigenda should recommend whether Phase 3.1 rows bump the catalog from v0.5 directly to v0.6, or whether trace reserved-key protection creates a v0.5.x / v0.6-pre hardening step first.

Preferred recommendation:

```text
trace reserved-key protection gets its own micro-hardening mission without changing Phase 3 semantics;
Phase 3.1 Osmotic Chamber catalog patch should then bump to v0.6.
```

### C8 — Build-order correction

Corrigenda should reaffirm:

```text
no code before accepted catalog patch
no runtime behavior before data model/source-tag constructors
no promotion before source-tag and metric fixtures are green
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
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
```

Allowed file for this mission:

```text
PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md
```

Optional only if needed:

```text
CURRENT_MISSION.md
```

But do not update `CURRENT_MISSION.md` again unless the user asks.

---

## Validation

After drafting the corrigenda:

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
stage only PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md
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
Created/updated:
- PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md

Validation:
- git diff --name-only: ...
- python -m tools.catalog counts: pass / not run with reason

Git:
- commit: <sha or none>
- push: success / not run with reason

Next:
- review corrigenda
- then decide trace reserved-key micro-hardening vs Phase 3.1 implementation planning
```

---

## Stop condition

Stop after drafting `PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md`, validating, committing, pushing, and reporting the result.

Do not proceed into Phase 3.1 code unless the user gives a new explicit instruction.
