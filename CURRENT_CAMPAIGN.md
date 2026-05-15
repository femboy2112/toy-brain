# CURRENT_CAMPAIGN.md — Phase 3.3 Minimal Worldlet Campaign

## Purpose

This campaign lets Codex proceed through Phase 3.3 without requiring a new `CURRENT_MISSION.md` for every micro-step.

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

This campaign is bounded to **Phase 3.3 Minimal Worldlet** only.

It does not authorize Proto-BASIC REPL, expression/readability, social/language, or Mode B implementation.

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
PHASE3_1_OSMOTIC_CHAMBER_AUDIT.md
PHASE3_2_OUTPUT_LADDER_SYNTHESIS.md
PHASE3_2_OUTPUT_LADDER_KICKOFF.md
PHASE3_2_OUTPUT_LADDER_CORRIGENDA.md
PHASE3_2_OUTPUT_LADDER_CATALOG_PATCH_PLAN.md
PHASE3_2_OUTPUT_LADDER_AUDIT.md
INVARIANT_CATALOG.md
```

Core inherited principle:

```text
PRESERVE should be earned, not labeled.
```

Phase 3.2 boundary inherited into Phase 3.3:

```text
Output readiness is only local history evidence; it is not agency, language, or world consequence.
```

Phase 3.3-specific principle:

```text
A worldlet supplies bounded not-I pushback and consequence evidence, but it is still a deterministic harness, not a real environment and not reflective agency.
```

---

## Current baseline

Current baseline should be v0.7 after the Phase 3.2 Output Ladder campaign.

Expected baseline:

```text
99 REQUIRED
24 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
3 OBSERVED
```

The Phase 3.2 audit reports PASS. `I-OUT-*` rows are green, output echo remains below agency, learned output tokens remain below language, and proto-output-action readiness is OBSERVED only.

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
Proto-BASIC REPL
expression layer
readability predictor
social/language harness
Mode B developmental layer
real LLM training behavior
real host execution
open-ended process execution
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

- If `PHASE3_3_MINIMAL_WORLDLET_SYNTHESIS.md` exists, Step 1 may be complete.
- If `PHASE3_3_MINIMAL_WORLDLET_KICKOFF.md` exists, Step 2 may be complete.
- If `PHASE3_3_MINIMAL_WORLDLET_CORRIGENDA.md` exists, Step 3 may be complete.
- If `PHASE3_3_MINIMAL_WORLDLET_CATALOG_PATCH_PLAN.md` exists, Step 4 may be complete.
- If `INVARIANT_CATALOG.md` has v0.8 Minimal Worldlet rows and `tools/catalog.py` expected counts match, Step 6 may be complete.
- If `brain/development/worldlet.py` or equivalent worldlet modules exist with targeted rows green, implementation steps may be complete.
- If `PHASE3_3_MINIMAL_WORLDLET_AUDIT.md` exists and full gate is green, the campaign may be complete.

When in doubt, inspect files and tests before deciding.

---

# Step 0 — Preflight

## Purpose

Confirm the repo is ready for Phase 3.3 planning.

## Required reads

```text
CURRENT_MISSION.md
CURRENT_CAMPAIGN.md
README.md
INVARIANT_CATALOG.md
PHASE3_2_OUTPUT_LADDER_AUDIT.md
brain/development/output.py
```

## Commands

```bash
git status --short
git branch --show-current
git log --oneline -10
python3 -m tools.catalog counts
python3 -m brain.invariants run --id I-OUT-11
bash tools/check_all.sh
```

## Branch logic

- If there are uncommitted external changes, stop and report.
- If the full gate fails, do not start Phase 3.3; diagnose within current scope or stop.
- If Phase 3.2 audit is absent or not PASS, stop and report.
- If preflight is green, proceed to Step 1.

---

# Step 1 — Phase 3.3 synthesis

## Purpose

Draft the bridge document explaining why the Minimal Worldlet follows the Output Ladder.

## Output file

```text
PHASE3_3_MINIMAL_WORLDLET_SYNTHESIS.md
```

## Allowed files

```text
PHASE3_3_MINIMAL_WORLDLET_SYNTHESIS.md
```

## Required contents

Include:

```text
v0.7 Phase 3.2 baseline summary
why worldlet follows output readiness
minimal worldlet thesis
not-I pushback and bounded consequence evidence
why this is still below agency and Mode B
non-goals
expected phase ordering
risks
next artifact: PHASE3_3_MINIMAL_WORLDLET_KICKOFF.md
```

Core thesis:

```text
The Minimal Worldlet converts local proto-output readiness into bounded consequence-bearing attempts, but only inside a deterministic harness. It supplies not-I pushback; it does not create reflective agency, language, REPL command syntax, or real-world action.
```

## Validation

```bash
git diff --name-only
python3 -m tools.catalog counts
```

Commit/push after drafting.

---

# Step 2 — Phase 3.3 kickoff

## Purpose

Draft a precise kickoff for the Minimal Worldlet implementation plan.

## Output file

```text
PHASE3_3_MINIMAL_WORLDLET_KICKOFF.md
```

## Allowed files

```text
PHASE3_3_MINIMAL_WORLDLET_KICKOFF.md
```

## Required scope

The kickoff should cover only:

```text
WorldletState
WorldletObject / target surface if needed
WorldletAttempt
WorldletResponse
WorldletValence bounded in [-1, 1]
WorldletHistory
not-I pushback
bounded deterministic consequence evidence
connection from ProtoOutputActionReadiness to WorldletAttempt
worldlet response enters local worldlet history, not TLICA state
```

Do not include:

```text
Proto-BASIC grammar
open-ended sandbox execution
real host execution
natural language teacher
expression/readability
social/language harness
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
PHASE3_3_MINIMAL_WORLDLET_CORRIGENDA.md
```

## Allowed files

```text
PHASE3_3_MINIMAL_WORLDLET_CORRIGENDA.md
```

## Required issues to check

At minimum:

```text
worldlet consequence vs agency distinction
whether WorldletAttempt may be constructed from readiness alone or requires learned token support
whether response valence is bounded and source-tagged
whether failed attempts produce negative-but-bounded evidence without fear/avoidance pathology
whether not-I pushback is represented without claiming external reality
whether rows should be REQUIRED / STRUCTURAL / OBSERVED
whether Proto-BASIC / REPL semantics leaked in
whether worldlet evidence can ever enter PerceptEvent/tick in this phase or must remain local
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

Design the future v0.8 Phase 3.3 catalog patch without applying it yet.

## Output file

```text
PHASE3_3_MINIMAL_WORLDLET_CATALOG_PATCH_PLAN.md
```

## Allowed files

```text
PHASE3_3_MINIMAL_WORLDLET_CATALOG_PATCH_PLAN.md
```

## Required contents

Specify:

```text
proposed row families, likely I-WLD-*
row IDs, statuses, owning modules, fixtures
count impact from current v0.7
fixture roster
owning module map
catalog patch mechanics
strict implementation order
open decisions
stop condition
```

Likely row themes:

```text
worldlet state is finite and deterministic
worldlet attempts are constructed from output readiness / learned token support only
worldlet attempts are not agency and do not select Act
worldlet responses are bounded and source-tagged
valid attempts may change only WorldletHistory, not TLICA runtime state
invalid or unavailable attempts produce bounded negative valence
not-I pushback is recorded as response evidence, not external reality
worldlet consequence evidence is local and below Mode B
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

Do not automatically apply the v0.8 catalog patch unless the catalog patch plan is coherent and no open decision blocks implementation.

## Branch logic

- If the catalog patch plan contains unresolved blockers, stop and report.
- If the plan is coherent and internally complete, Codex may proceed to Step 6 when the user says `go` again.
- If the user explicitly says the plan is accepted, proceed to Step 6 in the same campaign.

This is an explicit review gate.

---

# Step 6 — Apply accepted v0.8 catalog patch

## Purpose

Apply the accepted Minimal Worldlet catalog rows.

## Allowed files

```text
INVARIANT_CATALOG.md
tools/catalog.py
brain/_catalog_ids.py
brain/invariants.py
brain/development/fixtures/__init__.py
```

Only create module/fixture placeholders if necessary for registry coherence. Do not implement full worldlet behavior in this step unless the plan explicitly allows it.

## Commands

```bash
python3 -m tools.catalog counts
python3 -m tools.catalog generate-ids
python3 -m tools.catalog counts
```

Commit/push when catalog and generated IDs are coherent. If I-CAT-01 requires fixture registration immediately, create minimal intentional fixture registrations only within the accepted plan.

---

# Step 7 — Implement worldlet state and response boundary rows

## Purpose

Implement the minimal worldlet state/response surface.

## Allowed files

```text
brain/development/worldlet.py
brain/development/fixtures/worldlet_state.py
brain/development/fixtures/worldlet_response.py
brain/invariants.py
brain/_catalog_ids.py
```

## Expected behavior

```text
finite deterministic WorldletState
WorldletResponse
WorldletValence bounded in [-1, 1]
source/provenance tags
copy-on-write WorldletHistory
no TLICA runtime mutation
```

Run targeted rows from the accepted plan and commit/push when green.

---

# Step 8 — Implement worldlet attempt and consequence rows

## Purpose

Implement consequence-bearing attempts below agency.

## Allowed files

```text
brain/development/worldlet.py
brain/development/fixtures/worldlet_attempt.py
brain/development/fixtures/worldlet_consequence.py
brain/invariants.py
```

## Expected behavior

```text
WorldletAttempt from learned output token / proto-output readiness support
attempt is not Act and not AgencyWitness
valid attempt produces deterministic WorldletResponse
invalid/unavailable attempt produces bounded negative response
response updates WorldletHistory only
```

Commit/push when targeted checks pass.

---

# Step 9 — Implement not-I pushback / local evidence rows if authorized

## Purpose

Represent not-I pushback and local consequence evidence only if the accepted catalog plan includes it.

## Stop logic

If the accepted plan defers not-I pushback to a later phase, skip this step and proceed to full gate.

If included, keep it below external reality claims, below Mode B, and below language.

Allowed behavior:

```text
not-I pushback as deterministic response evidence
bounded valence
local history only
no PerceptEvent promotion unless explicitly authorized by the accepted plan
```

Commit/push when targeted checks pass.

---

# Step 10 — Full gate

## Purpose

Verify the whole repo after Phase 3.3 rows are implemented.

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

Audit Phase 3.3 after implementation.

## Output file

```text
PHASE3_3_MINIMAL_WORLDLET_AUDIT.md
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
worldlet response vs agency distinction
not-I pushback vs external reality distinction
bounded valence
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
Proto-BASIC syntax becomes necessary
open-ended host execution becomes necessary
there are uncommitted external changes
```

---

## Campaign complete output

When complete, report:

```text
Phase 3.3 Minimal Worldlet campaign complete.
Catalog: <version>
Counts: <actual>
Full gate: pass
Commits: <list>
Remaining deferred work: Phase 3.4 Proto-BASIC REPL and later phases
```
