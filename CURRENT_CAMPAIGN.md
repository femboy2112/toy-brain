# CURRENT_CAMPAIGN.md — Phase 3.1 Osmotic Chamber Campaign

## Purpose

This campaign lets Codex proceed through Phase 3.1 without requiring a new `CURRENT_MISSION.md` for every micro-step.

When the user says `go`, Codex should:

```text
read CURRENT_MISSION.md
read CURRENT_CAMPAIGN.md
find the next eligible campaign step
execute it
use test results to choose the next branch
commit and push after each completed step
stop only at explicit gates, failures requiring user judgment, or campaign completion
```

This campaign is bounded to **Phase 3.1 Osmotic Chamber** only.

It does not authorize Phase 3.2+ work.

---

## Local command rule

Use `python3 -m ...` for every Python module command.

Do **not** use `python -m ...` unless the user explicitly confirms a `python` alias exists.

If copied instructions say `python -m`, silently convert them to `python3 -m` before running.

---

## Current accepted inputs

Treat these repo-local files as accepted campaign inputs unless the user explicitly says otherwise:

```text
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md
PHASE3_1_OSMOTIC_CHAMBER_CATALOG_PATCH_PLAN.md
```

The catalog patch plan is accepted as the controlling plan for v0.6 unless direct inspection finds an internal contradiction, stale command, bad arithmetic, or conflict with v0.5 tooling.

Core bridge principle:

```text
PRESERVE should be earned, not labeled.
```

---

## Current baseline

Current baseline is v0.5 plus trace reserved-key hardening:

```text
84 REQUIRED
16 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
1 OBSERVED
```

`I-TRACE-03` is present and green.

The next developmental catalog target from the patch plan is projected v0.6:

```text
92 REQUIRED
20 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
2 OBSERVED
```

---

## Global hard boundaries

Never modify unless a campaign step explicitly allows it:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
```

Never do in this campaign:

```text
Phase 3.2 output ladder
Minimal Worldlet
Proto-BASIC REPL
expression layer
social/language harness
Mode B implementation
real LLM scenario run
prompt-tuning solely to force the four-tick scenario to pass
seeded-MSI scenario shortcut
```

Do not run real LLM commands unless the user explicitly asks.

---

## Git persistence rule

After every successful campaign step:

```text
stage only intended files
commit with a clear message
push to current branch / main as appropriate
report commit SHA
```

If no files changed, report no commit and why.

If tests fail, fix within the step's allowed scope. If the fix requires files outside the allowed scope, stop and report.

---

## Campaign state detection

Codex should infer completed steps from repo state:

- If `PHASE3_1_OSMOTIC_CHAMBER_CATALOG_PATCH_PLAN.md` exists and uses `python3 -m` throughout command examples, the catalog patch plan step is complete.
- If `INVARIANT_CATALOG.md` banner/history includes v0.6 Phase 3.1 rows and `tools/catalog.py` expected counts match projected v0.6 counts, the v0.6 catalog patch step is complete.
- If `brain/development/stream.py` exists and `I-FRAME-*` checks are registered and green, the frame/source-tag step is complete.
- If `brain/development/drives.py`, `history.py`, and metric modules exist with relevant checks green, the metrics/history step is complete.
- If `ProtoPattern`, probes, proto-content, and promotion rows are implemented and all targeted checks pass, the implementation rows are complete.
- If `bash tools/check_all.sh` is green after all Phase 3.1 rows, the campaign is complete.

---

# Step 0 — Preflight

## Purpose

Confirm the current repo state before taking action.

## Required reads

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_1_OSMOTIC_CHAMBER_CATALOG_PATCH_PLAN.md
```

## Commands

```bash
git status --short
git branch --show-current
git log --oneline -5
python3 -m tools.catalog counts
```

## Branch logic

- If there are uncommitted changes not created by Codex for this campaign, stop and report.
- If counts fail before any changes, stop and report.
- If the catalog patch plan is missing, recreate or restore it from the accepted plan only after reporting.
- If the plan exists and is coherent, proceed to Step 1.

---

# Step 1 — Apply accepted v0.6 catalog patch

## Purpose

Apply the accepted Phase 3.1 catalog row plan without implementing runtime behavior yet.

## Allowed files

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
brain/development/__init__.py
brain/development/fixtures/__init__.py
```

Only create minimal package/fixture package markers if needed to make future imports legal. Do not implement chamber logic in this step.

## Required catalog additions

Add the 13 planned Phase 3.1 rows:

```text
I-FRAME-01
I-FRAME-02
I-FRAME-03
I-FRAME-04
I-DEV-01
I-DEV-02
I-DEV-03
I-DEV-04
I-DEV-05
I-DEV-06
I-DEV-07
I-SBX-01
I-SBX-02
```

Use the planned statuses:

```text
REQUIRED +8
STRUCTURAL +4
OBSERVED +1
```

Update projected counts to:

```text
92 REQUIRED
20 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
2 OBSERVED
```

## Important I-CAT-01 handling

Because I-CAT-01 enforces catalog-to-registry coverage, do **not** leave new REQUIRED/STRUCTURAL rows unregistered.

If a row cannot yet have a real implementation, register an intentional placeholder check that raises an explicit `NotImplementedError` only if the row is not supposed to pass yet. However, preferred campaign behavior is to add row registrations together with minimal implementations in the same step or next immediate step so the gate can move forward.

Safer branch:

- If adding catalog rows alone makes `python3 -m tools.catalog counts` pass but `brain.invariants` fail due missing registration, continue immediately to create placeholder fixture modules and registrations within the allowed scope.
- Do not claim Step 1 complete until catalog counts and registry coverage are coherent.

## Commands

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

Commit/push after counts and generated IDs are coherent. If full invariants are expected to fail because implementations are not present, say so explicitly and proceed to Step 2.

---

# Step 2 — Implement I-FRAME rows

## Purpose

Implement frame/source-tag data model and deterministic source-tag fixture coverage.

## Rows

```text
I-FRAME-01
I-FRAME-02
I-FRAME-03
I-FRAME-04
```

## Allowed files

```text
brain/development/stream.py
brain/development/fixtures/source_tag_audit.py
brain/invariants.py
brain/_catalog_ids.py
```

## Required behavior

Implement:

```text
FrameSourceKind = ENDOGENOUS, OPERATOR_INJECTION, PROBE_ECHO, EXTERNAL, GENERATED
FrameSource
PhenomenalFrame
exact source coverage validation
source confidence Fraction in [0,1]
constructor rejection for missing/extra/mismatched source tags
```

## Commands

```bash
python3 -m brain.invariants run --id I-FRAME-01
python3 -m brain.invariants run --id I-FRAME-02
python3 -m brain.invariants run --id I-FRAME-03
python3 -m brain.invariants run --id I-FRAME-04
python3 -m tools.catalog counts
```

Commit/push when all I-FRAME rows pass.

---

# Step 3 — Implement drives, history, and metric helpers

## Purpose

Add deterministic substrate support used by later rows.

## Allowed files

```text
brain/development/drives.py
brain/development/history.py
brain/development/salience.py
brain/development/stability.py
brain/development/prediction_gain.py
```

## Required behavior

Implement exact-Fraction, deterministic helpers:

```text
SubstrateDrives
SubstrateHistory
salience_v1
stability_v1
prediction_gain_v1 positive-delta formula
```

No row needs to be declared complete unless a row fixture directly depends on it. Commit/push when modules are usable and local checks pass.

## Commands

```bash
python3 -m tools.catalog counts
```

If no targeted rows are available yet, do not run full gate unless useful.

---

# Step 4 — Implement ProtoPattern recurrence rows

## Rows

```text
I-DEV-01
I-DEV-02
```

## Allowed files

```text
brain/development/proto_pattern.py
brain/development/proto_content.py
brain/development/fixtures/recurrence_detection.py
brain/development/fixtures/unstable_noise_rejection.py
brain/invariants.py
```

## Commands

```bash
python3 -m brain.invariants run --id I-DEV-01
python3 -m brain.invariants run --id I-DEV-02
python3 -m tools.catalog counts
```

Commit/push when green.

---

# Step 5 — Implement probes and salience boundary rows

## Rows

```text
I-DEV-03
I-DEV-04
I-DEV-07
I-SBX-01
I-SBX-02
```

## Allowed files

```text
brain/development/probes.py
brain/development/fixtures/salience_is_not_truth.py
brain/development/fixtures/focus_contact_protocol.py
brain/development/fixtures/focus_stabilizes_or_dissolves.py
brain/invariants.py
```

## Commands

```bash
python3 -m brain.invariants run --id I-DEV-03
python3 -m brain.invariants run --id I-DEV-04
python3 -m brain.invariants run --id I-SBX-01
python3 -m brain.invariants run --id I-SBX-02
python3 -m tools.catalog counts
```

`I-DEV-07` is OBSERVED. Run/report it if runner supports doing so without gating, but do not force it as a correctness gate.

Commit/push when REQUIRED/STRUCTURAL rows are green.

---

# Step 6 — Implement ProtoContent promotion rows

## Rows

```text
I-DEV-05
I-DEV-06
```

## Allowed files

```text
brain/development/promotion.py
brain/development/proto_content.py
brain/development/fixtures/proto_content_promotion.py
brain/invariants.py
```

## Required behavior

Promotion must:

```text
create a valid PerceptEvent
reject COGITO_ID
require more than salience alone
preserve existing tick() boundary
feed one PerceptEvent per tick
not mutate BrainState/MSI/PtCns directly
```

## Commands

```bash
python3 -m brain.invariants run --id I-DEV-05
python3 -m brain.invariants run --id I-DEV-06
python3 -m tools.catalog counts
```

Commit/push when green.

---

# Step 7 — Full campaign gate

## Purpose

Verify the whole repo after Phase 3.1 rows are implemented.

## Commands

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

## Completion condition

Campaign complete when:

```text
all REQUIRED rows green
all STRUCTURAL rows green
OBSERVED rows reported but non-gating
bash tools/check_all.sh exits 0
```

Commit/push any final documentation updates, then report completion.

---

## Stop conditions requiring user review

Stop and report if:

```text
a fix requires editing brain/tlica/
a fix requires changing tick() semantics
a fix requires changing scenario schema
a fix requires changing existing v0.5/v0.6 row meaning rather than implementing it
a test failure suggests the catalog patch plan itself is wrong
there are uncommitted external changes
real LLM execution appears necessary
```

---

## Campaign complete output

When complete, report:

```text
Phase 3.1 Osmotic Chamber campaign complete.
Catalog: v0.6
Counts: <actual>
Full gate: pass
Commits: <list>
Remaining deferred work: Phase 3.2 output ladder and later phases
```
