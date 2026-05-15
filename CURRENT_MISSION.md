# CURRENT_MISSION.md — Codex `go` Entry Point

## One-line instruction

When the user tells Codex **`go`** in this repository, Codex should read this file and execute the current mission below, unless the user gives a more specific instruction.

---

## Current mission

Draft, validate, commit, and push the Phase 3.1 Osmotic Chamber catalog-patch plan:

```text
PHASE3_1_OSMOTIC_CHAMBER_CATALOG_PATCH_PLAN.md
```

This is a **planning artifact only**.

Do **not** edit `INVARIANT_CATALOG.md` yet.
Do **not** implement Phase 3 runtime code.
Do **not** create `brain/development/` yet.

---

## Important local command rule

Use `python3 -m ...` for all Python module commands.

Do **not** use `python -m ...` on this machine unless the user explicitly says a `python` alias exists.

If any copied command says `python -m`, convert it to `python3 -m` before running.

---

## Important persistence clarification

Creating the artifact locally is not sufficient.

Committing and pushing the artifact is part of the mission and does **not** count as an unauthorized edit.

Required final state:

```text
PHASE3_1_OSMOTIC_CHAMBER_CATALOG_PATCH_PLAN.md exists on the pushed branch / main.
```

If the file already exists locally but is uncommitted, do not recreate it. Inspect it, validate it, stage only that file, commit it, push it, and report the commit SHA.

---

## Why this mission exists

The Phase 3.1 kickoff and corrigenda are now drafted:

```text
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md
```

The trace reserved-key micro-hardening is complete and `I-TRACE-03` is green.

The next safe step is to design the exact catalog patch that will later bump the catalog from v0.5 to v0.6 for Phase 3.1 Osmotic Chamber rows.

Because `I-CAT-01` enforces catalog↔registry coverage, do not edit `INVARIANT_CATALOG.md` until the full row set, fixture names, owning modules, and implementation order are accepted.

This mission drafts and persists the catalog-patch plan only.

---

## Required source files to read first

Read these before writing the plan:

```text
CURRENT_MISSION.md
README.md
INVARIANT_CATALOG.md
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md
traces/RUN_SUMMARY.md
brain/trace.py
brain/fixtures/trace_v1_1.py
tools/catalog.py
```

Do not rely on unstated conversation context. The plan must stand on repo-local files.

---

## Required output file

Create or update exactly this artifact:

```text
PHASE3_1_OSMOTIC_CHAMBER_CATALOG_PATCH_PLAN.md
```

Do not edit any other file unless absolutely necessary and explicitly justified.

---

## Required contents

The plan must specify the exact proposed v0.6 catalog patch without applying it yet.

### 1. Purpose

State that this document designs the future v0.6 Phase 3.1 catalog patch for the deterministic Osmotic Chamber substrate layer.

State that it is a planning artifact only.

### 2. Baseline

State that current baseline is:

```text
catalog v0.5
84 REQUIRED
16 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
1 OBSERVED
```

State that `I-TRACE-03` is already present as trace reserved-key hardening.

### 3. Versioning decision

Recommend:

```text
The accepted Phase 3.1 Osmotic Chamber catalog patch should bump the catalog to v0.6.
```

Explain that this is the first developmental-layer catalog expansion and should not be folded into v0.5 trace hardening.

### 4. Source-kind policy

All Phase 3.1 developmental rows should use source wording equivalent to:

```text
Engineering hypothesis (Phase 3.1 Osmotic Chamber). Not a TLICA theorem. Specific formulas and thresholds are parameterized simulation choices; the family of constraints is the commitment, not any single instantiation.
```

Rows that are pure kernel-boundary or trace-envelope rules may use plan-convention wording instead.

### 5. Proposed row families

Define row families:

```text
I-FRAME-*   PhenomenalFrame / FrameSource structure and source coverage
I-DEV-*     recurrence, salience, stability, prediction gain, probes, promotion
I-SBX-*     substrate boundary constraints such as salience-is-not-truth and operator-injection-is-not-knowledge
```

Do not add output-ladder, worldlet, REPL, expression, or social/language rows.

### 6. Proposed rows table

Include a table with at least:

```text
ID
Source
Proposition
Owning module
Fixture
Status
Rationale
```

Use the corrigenda row sketch as the starting point:

```text
I-FRAME-01 exact source coverage
I-FRAME-02 source confidence Fraction in [0, 1]
I-FRAME-03 missing/extra/mismatched source tags raise
I-FRAME-04 active source kinds distinguish ENDOGENOUS / OPERATOR_INJECTION / PROBE_ECHO / EXTERNAL / GENERATED
I-DEV-01 recurring signature creates or updates ProtoPattern
I-DEV-02 unstable one-off noise does not become stable proto-content
I-DEV-03 salience alone does not promote
I-DEV-04 FOCUS_CONTACT updates ProbeUse / policy history and does not promote by itself
I-DEV-05 ProtoContent promotion creates valid PerceptEvent and enters through tick()
I-DEV-06 developmental content cannot produce COGITO_ID
I-DEV-07 focused contact can stabilize under recurrence or remain unpromoted / dissolve without recurrence (OBSERVED)
I-SBX-01 probe output is not knowledge by itself
I-SBX-02 salience drive is not truth and cannot bypass stability or prediction gain
```

You may refine IDs/propositions if justified, but keep the same scope.

### 7. Count impact

Calculate the proposed count impact.

Starting from v0.5:

```text
84 REQUIRED
16 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
1 OBSERVED
```

Show projected v0.6 counts based on the proposed row statuses.

If using the row sketch as-is, expected additions are approximately:

```text
REQUIRED +8
STRUCTURAL +4
OBSERVED +1
```

Check that arithmetic carefully in the plan.

### 8. Fixture roster

List future fixture files:

```text
brain/development/fixtures/source_tag_audit.py
brain/development/fixtures/recurrence_detection.py
brain/development/fixtures/unstable_noise_rejection.py
brain/development/fixtures/salience_is_not_truth.py
brain/development/fixtures/focus_contact_protocol.py
brain/development/fixtures/focus_stabilizes_or_dissolves.py
brain/development/fixtures/proto_content_promotion.py
```

Explain which rows each fixture owns.

### 9. Owning module map

List future owning modules:

```text
brain/development/stream.py
brain/development/drives.py
brain/development/history.py
brain/development/proto_pattern.py
brain/development/proto_content.py
brain/development/salience.py
brain/development/stability.py
brain/development/prediction_gain.py
brain/development/probes.py
brain/development/promotion.py
```

Do not create these files yet.

### 10. Catalog patch mechanics

Specify what the future implementation mission must update:

```text
INVARIANT_CATALOG.md banner/history
INVARIANT_CATALOG.md row table(s)
summary counts
tools/catalog.py EXPECTED_COUNTS
brain/_catalog_ids.py via python3 -m tools.catalog generate-ids
brain/invariants.py FIXTURE_MODULES once fixtures exist
```

Warn that adding rows without registered checks will trip `I-CAT-01`.

### 11. Implementation order after catalog acceptance

Specify strict order:

```text
1. accepted catalog patch to v0.6
2. stream/source tags
3. drives
4. history
5. metrics
6. proto-pattern
7. probes
8. proto-content
9. promotion
10. fixtures
11. runner registration / generated IDs
12. targeted checks
13. full gate
```

### 12. Non-goals

Explicitly prohibit:

```text
no runtime implementation in this mission
no direct catalog edits in this mission
no brain/development files in this mission
no Phase 3.2+ rows
no output ladder/worldlet/REPL/expression/social-language rows
no Mode B rows
no real LLM scenario run
```

### 13. Open decisions for review

Include at least:

```text
whether projected v0.6 counts are acceptable
whether I-DEV-07 should remain OBSERVED
whether I-SBX-* belongs as separate family or folded into I-DEV-*
whether promotion requires at least one ProbeUse in initial v0.6
whether source kinds should be exactly five active values or include reserved future enum members
```

### 14. Stop condition

End by saying:

```text
Do not apply this catalog patch until this plan is reviewed and accepted.
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
tools/catalog.py
```

Allowed file for this mission:

```text
PHASE3_1_OSMOTIC_CHAMBER_CATALOG_PATCH_PLAN.md
```

Git operations are required and are not considered edits to guarded files.

Optional only if needed:

```text
CURRENT_MISSION.md
```

But do not update `CURRENT_MISSION.md` again unless the user asks.

---

## Validation

After drafting the plan:

Run lightweight checks only:

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Do not run:

```bash
bash tools/check_all.sh
python3 -m brain.scenario run ...
```

unless the user explicitly asks.

---

## Git persistence requirement

After validation passes, Codex must commit and push its result.

Rules:

```text
stage only PHASE3_1_OSMOTIC_CHAMBER_CATALOG_PATCH_PLAN.md
commit with a clear message
push to the current branch / main as appropriate
report the commit SHA
```

Committing and pushing the artifact is mandatory if the artifact was created or changed.
This persistence step is part of the mission, not an optional extra.

Do not commit accidental changes to guarded files.

If there are no changes, Codex should report that no commit was made and explain why.

---

## Final report

When done, report:

```text
Created/updated:
- PHASE3_1_OSMOTIC_CHAMBER_CATALOG_PATCH_PLAN.md

Validation:
- git diff --name-only: ...
- python3 -m tools.catalog counts: pass / not run with reason

Git:
- commit: <sha or none>
- push: success / not run with reason

Next:
- review catalog patch plan
- then update mission to apply accepted v0.6 catalog patch
```

---

## Stop condition

Stop after drafting `PHASE3_1_OSMOTIC_CHAMBER_CATALOG_PATCH_PLAN.md`, validating, committing, pushing, and reporting the result.

Do not apply the catalog patch or proceed into Phase 3.1 implementation unless the user gives a new explicit instruction.
