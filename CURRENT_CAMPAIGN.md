# CURRENT_CAMPAIGN.md — Phase 3.2 Output Ladder Campaign

## Purpose

This campaign lets Codex proceed through Phase 3.2 without requiring a new `CURRENT_MISSION.md` for every micro-step.

When the user says `go`, Codex should:

```text
read CURRENT_MISSION.md
read CURRENT_CAMPAIGN.md
run preflight
find the next eligible campaign step
execute only that step's allowed scope
use test results to choose the next branch
commit and push after each completed step
stop only at explicit gates, failures requiring user judgment, or campaign completion
```

This campaign is bounded to **Phase 3.2 Output Ladder** only.

It does not authorize Phase 3.3 Minimal Worldlet, Proto-BASIC REPL, expression/readability, social/language, or Mode B implementation.

---

## Local command rule

Use `python3 -m ...` for every Python module command.

Do **not** use `python -m ...` unless the user explicitly confirms a `python` alias exists.

If copied instructions say `python -m`, silently convert them to `python3 -m` before running.

---

## Accepted inputs

Treat these repo-local files as accepted inputs unless the user explicitly says otherwise:

```text
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
PHASE3_1_OSMOTIC_CHAMBER_CORRIGENDA.md
PHASE3_1_OSMOTIC_CHAMBER_CATALOG_PATCH_PLAN.md
PHASE3_1_OSMOTIC_CHAMBER_AUDIT.md
INVARIANT_CATALOG.md
```

Core bridge principle inherited from Phase 3.1:

```text
PRESERVE should be earned, not labeled.
```

Phase 3.2-specific principle:

```text
Output should become action-like only through echo, recurrence, source-tagged history, and bounded consequence evidence; it is not reflective agency yet.
```

---

## Current baseline

Current baseline should be v0.6 after the Phase 3.1 Osmotic Chamber campaign and promotion-gate tightening.

Expected baseline:

```text
92 REQUIRED
20 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
2 OBSERVED
```

`I-TRACE-03` is present and green. Phase 3.1 source tags, proto-patterns, probes, proto-content, and promotion through `PerceptEvent` + `tick()` are present.

---

## Global hard boundaries

Never modify unless a campaign step explicitly allows it:

```text
brain/tlica/
lean_reference/
traces/first_scenario_real.jsonl
traces/RUN_SUMMARY.md
scenarios/
brain/tick.py
brain/llm/
```

Never implement in this campaign:

```text
Minimal Worldlet
Proto-BASIC REPL
expression layer
readability predictor
social/language harness
Mode B developmental layer
real LLM training behavior
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

- If `PHASE3_2_OUTPUT_LADDER_SYNTHESIS.md` exists, Step 1 may be complete.
- If `PHASE3_2_OUTPUT_LADDER_KICKOFF.md` exists, Step 2 may be complete.
- If `PHASE3_2_OUTPUT_LADDER_CORRIGENDA.md` exists, Step 3 may be complete.
- If `PHASE3_2_OUTPUT_LADDER_CATALOG_PATCH_PLAN.md` exists, Step 4 may be complete.
- If `INVARIANT_CATALOG.md` has v0.7 output-ladder rows and `tools/catalog.py` expected counts match, Step 5 may be complete.
- If `brain/development/output.py` or equivalent output-ladder modules exist with targeted rows green, implementation steps may be complete.
- If `PHASE3_2_OUTPUT_LADDER_AUDIT.md` exists and full gate is green, the campaign may be complete.

When in doubt, inspect files and tests before deciding.

---

# Step 0 — Preflight

## Purpose

Confirm the repo is ready for Phase 3.2 planning.

## Required reads

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_1_OSMOTIC_CHAMBER_AUDIT.md
brain/development/
```

## Commands

```bash
git status --short
git branch --show-current
git log --oneline -10
python3 -m tools.catalog counts
python3 -m brain.invariants run --id I-DEV-05
bash tools/check_all.sh
```

## Branch logic

- If there are uncommitted external changes, stop and report.
- If the full gate fails, do not start Phase 3.2; diagnose within current scope or stop.
- If the promotion-gate tightening is absent, stop and report that Phase 3.1 audit patch is incomplete.
- If preflight is green, proceed to Step 1.

---

# Step 1 — Phase 3.2 synthesis

## Purpose

Draft the bridge document explaining why the Output Ladder follows the Osmotic Chamber.

## Output file

```text
PHASE3_2_OUTPUT_LADDER_SYNTHESIS.md
```

## Allowed files

```text
PHASE3_2_OUTPUT_LADDER_SYNTHESIS.md
```

## Required contents

Include:

```text
v0.6 Phase 3.1 baseline summary
why output follows substrate history
output ladder thesis
non-goals
expected phase ordering
risks
next artifact: PHASE3_2_OUTPUT_LADDER_KICKOFF.md
```

Core thesis:

```text
Output is not language and not reflective action at first; it begins as source-tagged output echo and becomes action-like only after recurrence and consequence history.
```

## Validation

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push after drafting.

---

# Step 2 — Phase 3.2 kickoff

## Purpose

Draft a precise kickoff for the Output Ladder implementation plan.

## Output file

```text
PHASE3_2_OUTPUT_LADDER_KICKOFF.md
```

## Allowed files

```text
PHASE3_2_OUTPUT_LADDER_KICKOFF.md
```

## Required scope

The kickoff should cover only:

```text
OutputImpulse
OutputEchoFrame / output source tagging
OutputPattern / recurrence
OutputTokenCandidate
LearnedOutputToken
ProtoOutputAction
output-history storage
output echo is not agency
stable output token is not language yet
promotion/interaction with existing substrate history
```

Do not include:

```text
Worldlet consequence rules
Proto-BASIC grammar
natural language teacher
expression/readability
Mode B reflective planning
```

## Validation

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push after drafting.

---

# Step 3 — Kickoff corrigenda

## Purpose

Review and tighten the kickoff before catalog rows or code.

## Output file

```text
PHASE3_2_OUTPUT_LADDER_CORRIGENDA.md
```

## Allowed files

```text
PHASE3_2_OUTPUT_LADDER_CORRIGENDA.md
```

## Required issues to check

At minimum:

```text
output echo vs agency distinction
whether output token candidates require recurrence + echo provenance
whether output source kinds require new enum values or use existing GENERATED / ENDOGENOUS / PROBE_ECHO
whether output action candidates require worldlet evidence or should stay proto-action only
whether rows should be REQUIRED / STRUCTURAL / OBSERVED
whether any Phase 3.3 worldlet semantics leaked in
```

## Validation

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push after drafting.

---

# Step 4 — Catalog patch plan

## Purpose

Design the future v0.7 Phase 3.2 catalog patch without applying it yet.

## Output file

```text
PHASE3_2_OUTPUT_LADDER_CATALOG_PATCH_PLAN.md
```

## Allowed files

```text
PHASE3_2_OUTPUT_LADDER_CATALOG_PATCH_PLAN.md
```

## Required contents

Specify:

```text
proposed row families, likely I-OUT-*
row IDs, statuses, owning modules, fixtures
count impact from current v0.6
fixture roster
owning module map
catalog patch mechanics
strict implementation order
open decisions
stop condition
```

Likely row themes:

```text
output impulses are source-tagged
output echo enters substrate history but is not agency
repeated output pattern creates OutputPattern
token candidate requires recurrence and correction/echo support
learned output token is still not language
proto-output action requires consequence history below Mode B
no direct TLICA state mutation
```

Do not apply the catalog patch in this step.

## Validation

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push after drafting.

---

# Step 5 — Review gate before implementation

## Purpose

Do not automatically apply the v0.7 catalog patch unless the catalog patch plan is coherent and no open decision blocks implementation.

## Branch logic

- If the catalog patch plan contains unresolved blockers, stop and report.
- If the plan is coherent and internally complete, Codex may proceed to Step 6 when the user says `go` again.
- If the user explicitly says the plan is accepted, proceed to Step 6 in the same campaign.

This is an explicit review gate.

---

# Step 6 — Apply accepted v0.7 catalog patch

## Purpose

Apply the accepted Output Ladder catalog rows.

## Allowed files

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
brain/development/fixtures/__init__.py
```

Only create module/fixture placeholders if necessary for registry coherence. Do not implement full output ladder behavior in this step unless the plan explicitly allows it.

## Commands

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

Commit/push when catalog and generated IDs are coherent. If I-CAT-01 requires fixture registration immediately, create minimal intentional fixture registrations only within the accepted plan.

---

# Step 7 — Implement output echo and source-tag rows

## Purpose

Implement the first output-ladder layer.

## Allowed files

```text
brain/development/output.py
brain/development/fixtures/output_echo.py
brain/invariants.py
brain/_catalog_ids.py
```

## Expected behavior

```text
OutputImpulse
OutputEcho
output echo source/provenance
output echo is not agency
output echo does not mutate TLICA state
```

Run targeted rows from the accepted plan and commit/push when green.

---

# Step 8 — Implement output pattern / token candidate rows

## Purpose

Implement recurrence-based output patterns and token candidates.

## Allowed files

```text
brain/development/output.py
brain/development/fixtures/output_pattern.py
brain/development/fixtures/output_token_candidate.py
brain/invariants.py
```

## Expected behavior

```text
repeated output impulse creates output pattern
one-off output noise does not become token
stable token candidate requires recurrence/support
learned output token is not language
```

Commit/push when targeted checks pass.

---

# Step 9 — Implement proto-output action rows if authorized

## Purpose

Only implement proto-output-action behavior if the accepted catalog plan includes it.

## Stop logic

If the accepted plan defers proto-output actions to a later phase, skip this step and proceed to audit.

If included, keep it below Mode B and below worldlet semantics.

Allowed behavior:

```text
proto-output action candidate from recurrence and echo history
not reflective agency
not worldlet causality
not language
```

Commit/push when targeted checks pass.

---

# Step 10 — Full gate

## Purpose

Verify the whole repo after Phase 3.2 rows are implemented.

## Commands

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Commit/push any final sync docs if needed.

---

# Step 11 — Post-completion audit

## Purpose

Audit Phase 3.2 after implementation.

## Output file

```text
PHASE3_2_OUTPUT_LADDER_AUDIT.md
```

## Required verdict

```text
PASS
PASS WITH PATCHES
BLOCKED
```

Audit:

```text
scope creep
row-family registration
output echo vs agency distinction
learned token vs language distinction
kernel boundary
full gate
recommended next mission
```

Commit/push the audit.

---

## Stop conditions requiring user review

Stop and report if:

```text
a fix requires editing brain/tlica/
a fix requires changing tick() semantics
a fix requires changing scenario schema
a fix requires real LLM execution
a test failure suggests the campaign plan itself is wrong
Phase 3.3 worldlet semantics become necessary
Proto-BASIC syntax becomes necessary
there are uncommitted external changes
```

---

## Campaign complete output

When complete, report:

```text
Phase 3.2 Output Ladder campaign complete.
Catalog: <version>
Counts: <actual>
Full gate: pass
Commits: <list>
Remaining deferred work: Phase 3.3 Minimal Worldlet and later phases
```
